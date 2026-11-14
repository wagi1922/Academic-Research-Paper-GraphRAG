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
        self.client = httpx.AsyncClient(timeout=120.0)

    async def parse_pdf_grobid(self, file_path: str) -> dict:
        """Parse PDF using Grobid, return structured TEI XML parsed to dict."""
        try:
            with open(file_path, "rb") as f:
                files = {"input": (Path(file_path).name, f, "application/pdf")}
                data = {
                    "consolidateHeader": "1",
                    "consolidateCitations": "1",
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
                "consolidateHeader": "1",
                "consolidateCitations": "1",
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

            # Title
            title_elem = root.find(".//tei:titleStmt/tei:title", ns)
            title = title_elem.text.strip() if title_elem is not None else ""

            # Abstract
            abstract_elem = root.find(".//tei:profileDesc/tei:abstract/tei:p", ns)
            abstract = abstract_elem.text.strip() if abstract_elem is not None else ""

            # Authors
            authors = []
            for author_elem in root.findall(".//tei:author", ns):
                pers_name = author_elem.find(".//tei:persName", ns)
                if pers_name is not None:
                    forename = pers_name.find("tei:forename", ns)
                    surname = pers_name.find("tei:surname", ns)
                    name_parts = []
                    if forename is not None:
                        name_parts.append(forename.text)
                    if surname is not None:
                        name_parts.append(surname.text)
                    if name_parts:
                        authors.append(" ".join(name_parts))

                affiliation = author_elem.find(".//tei:affiliation/tei:orgName", ns)
                if affiliation is not None:
                    # Could store affiliation separately
                    pass

            # DOI
            doi_elem = root.find(".//tei:idno[@type='DOI']", ns)
            doi = doi_elem.text.strip() if doi_elem is not None else None

            # Year
            date_elem = root.find(".//tei:publicationStmt/tei:date", ns)
            year = None
            if date_elem is not None and date_elem.get("when"):
                try:
                    year = int(date_elem.get("when")[:4])
                except ValueError:
                    pass

            # Full text paragraphs
            paragraphs = []
            for p in root.findall(".//tei:body//tei:p", ns):
                text = "".join(p.itertext()).strip()
                if text:
                    paragraphs.append(text)

            return {
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "doi": doi,
                "year": year,
                "paragraphs": paragraphs,
                "full_text": "\n\n".join(paragraphs),
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