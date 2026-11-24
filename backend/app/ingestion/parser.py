"""
PDF Parser Module
Supports Grobid (self-hosted) and LlamaParse (API) for PDF text extraction.
"""

import httpx
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFParser:
    def __init__(self, grobid_url: str = "http://localhost:8070/api/processFulltextDocument"):
        self.grobid_url = grobid_url
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(1800.0, connect=30.0, read=1800.0, write=60.0, pool=60.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def parse_pdf_grobid(self, file_path: str) -> dict:
        """Parse PDF using Grobid, return structured TEI XML parsed to dict."""
        try:
            with open(file_path, "rb") as f:
                files = {"input": (Path(file_path).name, f, "application/pdf")}
                data = {
                    "consolidateHeader": "0",
                    "consolidateCitations": "0",
                    "includeRawCitations": "1",
                    "includeRawAffiliations": "1",
                    "teiCoordinates": "0",
                }
                response = await self.client.post(self.grobid_url, files=files, data=data)
                response.raise_for_status()
                return self._parse_tei_xml(response.text)
        except Exception as e:
            logger.error(f"Grobid parsing failed for {file_path}: {e}")
            raise

    async def parse_pdf_grobid_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> dict:
        """Parse PDF from bytes using Grobid."""
        try:
            files = {"input": (filename, pdf_bytes, "application/pdf")}
            data = {
                "consolidateHeader": "0",
                "consolidateCitations": "0",
                "includeRawCitations": "1",
                "includeRawAffiliations": "1",
            }
            response = await self.client.post(self.grobid_url, files=files, data=data)
            response.raise_for_status()
            return self._parse_tei_xml(response.text)
        except Exception as e:
            logger.error(f"Grobid parsing failed for {filename}: {e}")
            raise

    def _parse_tei_xml(self, tei_xml: str) -> dict:
        """Extract key fields from Grobid TEI XML."""
        try:
            from lxml import etree
        except ImportError:
            logger.warning("lxml not installed, using basic XML parsing")
            return self._parse_tei_basic(tei_xml)

        try:
            root = etree.fromstring(tei_xml.encode())
            ns = {"tei": "http://www.tei-c.org/ns/1.0"}

            # Title - try multiple locations
            title = ""
            # 1. Try titleStmt/title (may be empty)
            title_elem = root.find(".//tei:titleStmt/tei:title", ns)
            if title_elem is not None and title_elem.text:
                title = title_elem.text.strip()
            
            # 2. Try analytic/title (main title from biblStruct)
            if not title:
                title_elem = root.find(".//tei:analytic/tei:title", ns)
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
            
            # 3. Try monogr/title (journal/book title)
            if not title:
                title_elem = root.find(".//tei:monogr/tei:title", ns)
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()

            # Abstract
            abstract_elem = root.find(".//tei:profileDesc/tei:abstract//tei:p", ns)
            abstract = "".join(abstract_elem.itertext()).strip() if abstract_elem is not None else ""

            # Authors - from analytic/author (biblStruct authors)
            authors = []
            for author_elem in root.findall(".//tei:analytic/tei:author", ns):
                pers_name = author_elem.find(".//tei:persName", ns)
                if pers_name is not None:
                    forename = pers_name.find("tei:forename", ns)
                    surname = pers_name.find("tei:surname", ns)
                    name_parts = []
                    if forename is not None:
                        # Collect all forenames (first, middle)
                        for fn in pers_name.findall("tei:forename", ns):
                            if fn.text:
                                name_parts.append(fn.text)
                    if surname is not None and surname.text:
                        name_parts.append(surname.text)
                    if name_parts:
                        authors.append(" ".join(name_parts))

            # DOI
            doi_elem = root.find(".//tei:idno[@type='DOI']", ns)
            doi = doi_elem.text.strip() if doi_elem is not None else None

            # Year - from publicationStmt/date or imprint/date
            year = None
            for date_elem in root.findall(".//tei:publicationStmt/tei:date", ns):
                if date_elem.get("when"):
                    try:
                        year = int(date_elem.get("when")[:4])
                        break
                    except ValueError:
                        pass
            if year is None:
                for date_elem in root.findall(".//tei:imprint/tei:date", ns):
                    if date_elem.get("when"):
                        try:
                            year = int(date_elem.get("when")[:4])
                            break
                        except ValueError:
                            pass

            # Full text paragraphs - from text/body/div/p
            paragraphs = []
            for p in root.findall(".//tei:body//tei:p", ns):
                text = "".join(p.itertext()).strip()
                if text:
                    paragraphs.append(text)

            # Sections - from text/body/div with head
            sections = []
            for div in root.findall(".//tei:body/tei:div", ns):
                head_elem = div.find("tei:head", ns)
                head_text = "".join(head_elem.itertext()).strip() if head_elem is not None else ""
                div_paragraphs = []
                for p in div.findall(".//tei:p", ns):
                    text = "".join(p.itertext()).strip()
                    if text:
                        div_paragraphs.append(text)
                if div_paragraphs:
                    sections.append({
                        "heading": head_text,
                        "text": "\n\n".join(div_paragraphs)
                    })

            return {
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "doi": doi,
                "year": year,
                "paragraphs": paragraphs,
                "full_text": "\n\n".join(paragraphs),
                "sections": sections,
                "raw_tei": tei_xml,
            }
        except Exception as e:
            logger.error(f"TEI XML parsing failed: {e}")
            return self._parse_tei_basic(tei_xml)

    def _parse_tei_basic(self, tei_xml: str) -> dict:
        """Fallback basic XML parsing without lxml."""
        try:
            import defusedxml.ElementTree as ET
        except ImportError:
            # Fallback to stdlib with safe parser settings
            import xml.etree.ElementTree as ET
            # Disable external entities
            parser = ET.XMLParser(resolve_entities=False)
            root = ET.fromstring(tei_xml, parser=parser)
        else:
            root = ET.fromstring(tei_xml)

        # Simple extraction - namespace aware
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}

        title = ""
        title_elem = root.find(".//tei:titleStmt/tei:title", ns)
        if title_elem is not None:
            title = title_elem.text or ""

        abstract = ""
        abstract_elem = root.find(".//tei:profileDesc/tei:abstract/tei:p", ns)
        if abstract_elem is not None:
            abstract = abstract_elem.text or ""

        return {
            "title": title.strip(),
            "abstract": abstract.strip(),
            "authors": [],
            "doi": None,
            "year": None,
            "paragraphs": [],
            "full_text": "",
            "raw_tei": tei_xml,
        }

    def _extract_references(self, tei_xml: str) -> list[dict]:
        """Extract references from Grobid TEI XML listBibl section."""
        try:
            from lxml import etree
        except ImportError:
            logger.warning("lxml not installed, cannot extract references")
            return []

        try:
            root = etree.fromstring(tei_xml.encode())
            ns = {"tei": "http://www.tei-c.org/ns/1.0"}

            references = []

            # Find all biblStruct in listBibl
            for bibl in root.findall(".//tei:listBibl/tei:biblStruct", ns):
                ref = {}

                # Get xml:id
                xml_id = bibl.get("{http://www.w3.org/XML/1998/namespace}id") or bibl.get("id")
                if xml_id:
                    ref["xml_id"] = xml_id

                # Title (analytic/title)
                title_elem = bibl.find(".//tei:analytic/tei:title", ns)
                if title_elem is not None and title_elem.text:
                    ref["title"] = title_elem.text.strip()

                # Authors
                authors = []
                for author_elem in bibl.findall(".//tei:analytic/tei:author", ns):
                    pers_name = author_elem.find(".//tei:persName", ns)
                    if pers_name is not None:
                        name_parts = []
                        for fn in pers_name.findall("tei:forename", ns):
                            if fn.text:
                                name_parts.append(fn.text)
                        sn = pers_name.find("tei:surname", ns)
                        if sn is not None and sn.text:
                            name_parts.append(sn.text)
                        if name_parts:
                            authors.append(" ".join(name_parts))
                if authors:
                    ref["authors"] = authors

                # Year - from monogr/imprint/date
                year = None
                for date_elem in bibl.findall(".//tei:monogr/tei:imprint/tei:date", ns):
                    if date_elem.get("when"):
                        try:
                            year = int(date_elem.get("when")[:4])
                            break
                        except (ValueError, TypeError):
                            pass
                if year is None:
                    # Try imprint/date directly
                    for date_elem in bibl.findall(".//tei:imprint/tei:date", ns):
                        if date_elem.get("when"):
                            try:
                                year = int(date_elem.get("when")[:4])
                                break
                            except (ValueError, TypeError):
                                pass
                if year:
                    ref["year"] = year

                # DOI
                doi_elem = bibl.find(".//tei:idno[@type='DOI']", ns)
                if doi_elem is not None and doi_elem.text:
                    ref["doi"] = doi_elem.text.strip()

                # arXiv ID
                arxiv_elem = bibl.find(".//tei:idno[@type='arXiv']", ns)
                if arxiv_elem is not None and arxiv_elem.text:
                    ref["arxiv_id"] = arxiv_elem.text.strip()

                # Venue/Journal title
                venue_elem = bibl.find(".//tei:monogr/tei:title", ns)
                if venue_elem is not None and venue_elem.text:
                    ref["venue"] = venue_elem.text.strip()

                # Only add if we have at least a title
                if ref.get("title"):
                    references.append(ref)

            return references

        except Exception as e:
            logger.error(f"Reference extraction failed: {e}")
            return []

    async def close(self):
        await self.client.aclose()


# LlamaParse integration (optional)
class LlamaParseClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.cloud.llamaindex.ai/api/parsing"
        self.client = httpx.AsyncClient(timeout=120.0, headers={"Authorization": f"Bearer {api_key}"})

    async def parse_pdf(self, file_path: str) -> dict:
        """Submit PDF to LlamaParse and get parsed result."""
        # Implementation would follow LlamaParse API
        # This is a placeholder for the actual implementation
        raise NotImplementedError("LlamaParse integration not yet implemented")

    async def close(self):
        await self.client.aclose()