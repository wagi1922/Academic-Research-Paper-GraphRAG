"""
Smoke test for Capstone GraphRAG backend (no Docker needed).
Uses only system deps: fastapi, httpx, defusedxml, pydantic.
Tests:
  - PDFParser instantiation & _parse_tei_basic fallback
  - FixedSizeChunker chunking
  - ExtractedEntities schema construction
Run: python3 /home/guard/Documents/perkuliahan/sem 7/Cap/backend/tests_smoke.py
"""

from app.ingestion.parser import PDFParser
from app.ingestion.chunker import FixedSizeChunker
from app.schemas.entities import ExtractedEntities, AuthorEntity, ConceptEntity

parser = PDFParser()
print("PDFParser instantiated OK")

TEI_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<tei:document xmlns:tei="http://www.tei-c.org/ns/1.0">
  <tei:titleStmt>
    <tei:title>Test Title Paper</tei:title>
  </tei:titleStmt>
  <tei:profileDesc>
    <tei:abstract><tei:p>Test abstract paragraph.</tei:p></tei:abstract>
  </tei:profileDesc>
  <tei:author>
    <tei:persName><tei:forename>John</tei:forename>
                <tei:surname>Doe</tei:surname></tei:persName>
  </tei:author>
  <tei:idno type="DOI"><doi>10.48550/arXiv.2504.02112v2</doi></tei:idno>
  <tei:publicationStmt>
    <tei:date when="2025">2025</tei:date>
  </tei:publicationStmt>
  <tei:body>
    <tei:p>First paragraph text.</tei:p>
    <tei:p>Second paragraph text.</tei:p>
  </tei:body>
</tei:document>
"""

result = parser._parse_tei_basic(TEI_SAMPLE.encode())
print("_parse_tei_basic result keys:", list(result.keys()))
print("  title:", result.get("title"))
print("  abstract:", result.get("abstract"))
print("  authors:", result.get("authors"))
print("  doi:", result.get("doi"))
print("  year:", result.get("year"))

chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
text = "This test sentence. " * 10
chunks = chunker.chunk(text, {"source": "test"})
print(f"\nFixedSizeChunker chunks count: {len(chunks)}")
assert len(chunks) > 1
sources = [c.metadata.get("source") for c in chunks]
assert all(s == "test" for s in sources), f"source mismatch: {sources}"
print("Chunk sources all 'test':", sources)

assert chunker.chunk("") == []
assert chunker.chunk(" \n\n ") == []
print("Empty/whitespace chunking OK")

entities = ExtractedEntities(
    authors=[AuthorEntity(name="John Doe")],
    concepts=[ConceptEntity(name="Transformer", category="cs.LG")],
)
print("ExtractedEntities created OK:", entities.authors, entities.concepts)

print("\n=== ALL SMOKE TESTS PASSED ===")
