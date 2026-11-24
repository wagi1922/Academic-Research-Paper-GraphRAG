#!/usr/bin/env python3
"""
Build Citation Graph from Ingested Papers
Extracts references from PDFs via Grobid, matches to papers in Neo4j, creates CITES relationships.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher

from app.ingestion.parser import PDFParser
from app.core.neo4j_driver import get_neo4j_session
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CitationGraphBuilder:
    def __init__(self, grobid_url: str = "http://localhost:8070/api/processFulltextDocument"):
        self.parser = PDFParser(grobid_url=grobid_url)
        self.metadata_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/data/corpus/metadata.json")
        self.pdf_dir = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/data/corpus/pdfs")

    async def load_metadata(self) -> dict:
        """Load paper metadata from JSON."""
        with open(self.metadata_path) as f:
            return json.load(f)

    async def get_db_papers(self) -> dict:
        """Get all papers from Neo4j, indexed by title/DOI/arXiv for matching."""
        papers_by_title = {}
        papers_by_doi = {}
        papers_by_arxiv = {}

        async for session in get_neo4j_session():
            result = await session.run("""
                MATCH (p:Paper)
                RETURN p.id as id, p.title as title, p.doi as doi, p.year as year
            """)
            async for record in result:
                title = record["title"] or ""
                doi = record["doi"] or ""
                pid = record["id"]
                year = record["year"]

                # Index by normalized title (lowercase, stripped)
                norm_title = self._normalize_title(title)
                if norm_title:
                    papers_by_title[norm_title] = {"id": pid, "title": title, "doi": doi, "year": year}

                if doi:
                    papers_by_doi[doi.lower()] = {"id": pid, "title": title, "doi": doi, "year": year}

                # Also index by ID (which may be arXiv ID)
                if pid:
                    papers_by_arxiv[pid.lower()] = {"id": pid, "title": title, "doi": doi, "year": year}

        logger.info(f"Loaded {len(papers_by_title)} papers from DB for matching")
        return {"by_title": papers_by_title, "by_doi": papers_by_doi, "by_arxiv": papers_by_arxiv}

    def _normalize_title(self, title: str) -> str:
        """Normalize title for fuzzy matching."""
        return title.lower().strip().replace(":", "").replace("-", " ").replace(".", "").replace(",", "")

    def _match_reference(self, ref: dict, db_index: dict) -> Optional[dict]:
        """Match a reference to a paper in the database."""
        # Try DOI match first (most reliable)
        if ref.get("doi"):
            doi = ref["doi"].lower()
            if doi in db_index["by_doi"]:
                return db_index["by_doi"][doi]

        # Try arXiv ID match (convert to DOI format for Neo4j)
        if ref.get("arxiv_id"):
            arxiv = ref["arxiv_id"].lower()
            doi_format = f"10.48550/arxiv.{arxiv}"
            if doi_format in db_index["by_arxiv"]:
                return db_index["by_arxiv"][doi_format]
            # Also try exact match in case DB has raw arXiv ID
            if arxiv in db_index["by_arxiv"]:
                return db_index["by_arxiv"][arxiv]

        # Try fuzzy title match
        if ref.get("title"):
            norm_ref_title = self._normalize_title(ref["title"])
            if norm_ref_title in db_index["by_title"]:
                return db_index["by_title"][norm_ref_title]

            # Fuzzy match with threshold
            best_match = None
            best_score = 0.0
            for db_title, paper in db_index["by_title"].items():
                score = SequenceMatcher(None, norm_ref_title, db_title).ratio()
                if score > best_score and score > 0.85:  # 85% similarity threshold
                    best_score = score
                    best_match = paper

            if best_match:
                logger.debug(f"Fuzzy match: '{ref['title'][:60]}' -> '{best_match['title'][:60]}' ({best_score:.2f})")
                return best_match

        return None

    async def process_paper(self, pdf_path: Path, paper_meta: dict, db_index: dict) -> list[tuple]:
        """Process a single paper: extract references, match to DB, return (citing_id, cited_id) pairs."""
        # Use the same ID format as stored in Neo4j (raw arXiv ID or DOI)
        paper_id = paper_meta.get("id") or paper_meta.get("arxiv_id") or paper_meta.get("doi") or pdf_path.stem
        title = paper_meta.get("title", pdf_path.stem)

        logger.info(f"Processing: {title[:80]}")

        try:
            parse_result = await self.parser.parse_pdf_grobid(str(pdf_path))
            references = self.parser._extract_references(parse_result["raw_tei"])
            logger.info(f"  Extracted {len(references)} references")

            citations = []
            for ref in references:
                match = self._match_reference(ref, db_index)
                if match:
                    citations.append((paper_id, match["id"], ref))
                else:
                    # Log unmatched references for debugging
                    logger.debug(f"  Unmatched: {ref.get('title', 'N/A')[:60]} (DOI: {ref.get('doi', 'N/A')})")

            return citations

        except Exception as e:
            logger.error(f"  Failed to process {pdf_path.name}: {e}")
            return []

    async def build_citation_graph(self):
        """Main entry point: build citation graph for all papers."""
        # Load metadata
        metadata = await self.load_metadata()
        logger.info(f"Loaded metadata for {len(metadata)} papers")

        # Get DB papers for matching
        db_index = await self.get_db_papers()

        all_citations = []
        processed = 0

        for paper_meta in metadata:
            # Find PDF file
            pdf_name = paper_meta.get("filename") or f"{paper_meta.get('arxiv_id', '').replace('/', '_')}.pdf"
            pdf_path = self.pdf_dir / pdf_name

            if not pdf_path.exists():
                # Try to find by arxiv_id in filename
                arxiv_id = paper_meta.get("arxiv_id", "")
                if arxiv_id:
                    # Search for file containing arxiv_id
                    matches = list(self.pdf_dir.glob(f"*{arxiv_id.replace('/', '_')}*.pdf"))
                    if matches:
                        pdf_path = matches[0]
                    else:
                        logger.warning(f"PDF not found for {paper_meta.get('title', 'unknown')}")
                        continue
                else:
                    logger.warning(f"PDF not found for {paper_meta.get('title', 'unknown')}")
                    continue

            citations = await self.process_paper(pdf_path, paper_meta, db_index)
            all_citations.extend(citations)
            processed += 1

            if processed % 10 == 0:
                logger.info(f"Progress: {processed}/{len(metadata)} papers processed, {len(all_citations)} citations found")

        logger.info(f"Total citations found: {len(all_citations)} from {processed} papers")

        # Write to Neo4j
        await self.write_citations(all_citations)

    async def write_citations(self, citations: list[tuple]):
        """Write CITES relationships to Neo4j."""
        if not citations:
            logger.warning("No citations to write")
            return

        async for session in get_neo4j_session():
            writer = GraphWriter(session)

            # Batch write
            batch_size = 100
            for i in range(0, len(citations), batch_size):
                batch = citations[i:i+batch_size]
                for citing_id, cited_id, ref in batch:
                    try:
                        await session.run("""
                            MATCH (citing:Paper {id: $citing_id})
                            MATCH (cited:Paper {id: $cited_id})
                            MERGE (citing)-[r:CITES]->(cited)
                            SET r.reference_title = $ref_title,
                                r.reference_year = $ref_year,
                                r.reference_doi = $ref_doi
                        """, {
                            "citing_id": citing_id,
                            "cited_id": cited_id,
                            "ref_title": ref.get("title", ""),
                            "ref_year": ref.get("year"),
                            "ref_doi": ref.get("doi", "")
                        })
                    except Exception as e:
                        logger.error(f"Failed to create CITES: {citing_id} -> {cited_id}: {e}")

                logger.info(f"Written batch {i//batch_size + 1}/{(len(citations)-1)//batch_size + 1}")

        logger.info(f"Citation graph build complete: {len(citations)} CITES relationships created")


# Need to import GraphWriter or write direct Cypher
from app.ingestion.graph_writer import GraphWriter


async def main():
    builder = CitationGraphBuilder()
    await builder.build_citation_graph()
    await builder.parser.close()


if __name__ == "__main__":
    asyncio.run(main())