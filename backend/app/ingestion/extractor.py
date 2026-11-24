"""
Entity & Relation Extraction Module
Uses LLM with Instructor for structured output extraction.
"""

import logging
from openai import AsyncOpenAI
from typing import Optional
from pydantic import BaseModel, ValidationError

from app.schemas.entities import (
    ExtractedEntities,
    AuthorEntity,
    ConceptEntity,
    MethodEntity,
    DatasetEntity,
    RelationEntity,
    EntityType,
    RelationType,
)

logger = logging.getLogger(__name__)


# Extraction prompt template
EXTRACTION_PROMPT = """You are an expert at extracting structured information from academic papers.
Extract the following entities and relations from the provided text.

ENTITY TYPES:
1. Author: Researchers who wrote the paper (name, institution)
2. Concept: Key concepts, topics, tasks, domains, metrics (name, category)
3. Method: Algorithms, models, techniques, frameworks used (name, description)
4. Dataset: Datasets used in experiments (name, domain)

RELATION TYPES:
- WROTE: Author -> Paper
- CITES: Paper -> Paper (citations)
- ADDRESSES_TOPIC: Paper -> Concept
- USES_METHOD: Paper -> Method
- USES_DATASET: Paper -> Dataset

EXTRACTION RULES:
- Extract ONLY entities explicitly mentioned in the text
- For authors, include institution if mentioned
- For concepts, categorize as: task, domain, metric, technique, application, theory
- For methods, include brief description if available
- For datasets, include domain/application area
- Relations must connect entities that are both extracted
- Paper entity is implicit (the current paper being processed)
- Return empty lists if no entities of a type found

RELATION SCHEMA (REQUIRED FIELDS - MUST INCLUDE ALL):
{
  "source_type": "Paper",          // Paper | Author | Concept | Method | Dataset
  "source_name": "current paper",  // exact entity name extracted
  "relation": "USES_METHOD",       // WROTE | CITES | ADDRESSES_TOPIC | USES_METHOD | USES_DATASET
  "target_type": "Method",         // Paper | Author | Concept | Method | Dataset  ← REQUIRED
  "target_name": "Transformer"     // exact entity name extracted
}

VALID RELATION EXAMPLES:
- Paper -> Concept:   {"source_type":"Paper","source_name":"current paper","relation":"ADDRESSES_TOPIC","target_type":"Concept","target_name":"Attention Mechanism"}
- Paper -> Method:    {"source_type":"Paper","source_name":"current paper","relation":"USES_METHOD","target_type":"Method","target_name":"BERT"}
- Paper -> Dataset:   {"source_type":"Paper","source_name":"current paper","relation":"USES_DATASET","target_type":"Dataset","target_name":"SQuAD"}
- Author -> Paper:    {"source_type":"Author","source_name":"Vaswani et al.","relation":"WROTE","target_type":"Paper","target_name":"current paper"}
- Paper -> Paper:     {"source_type":"Paper","source_name":"current paper","relation":"CITES","target_type":"Paper","target_name":"Attention Is All You Need"}

TEXT TO ANALYZE:
{text}

Return structured output matching this EXACT JSON schema (all 5 keys required, empty lists if none):
{
  "authors": [{"name": "...", "institution": "..."}],
  "concepts": [{"name": "...", "category": "..."}],
  "methods": [{"name": "...", "description": "..."}],
  "datasets": [{"name": "...", "domain": "..."}],
  "relations": [{"source_type": "Paper", "source_name": "current paper", "relation": "USES_METHOD", "target_type": "Method", "target_name": "..."}]
}
OUTPUT ONLY VALID JSON. NO REASONING. NO MARKDOWN. NO EXTRA TEXT."""


class EntityExtractor:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "inclusionai/ling-3.2-flash:free",
        max_retries: int = 2,
        timeout: float = 120.0,
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model
        self.max_retries = max_retries

    async def extract(self, text: str, paper_title: str = "") -> ExtractedEntities:
        """Extract entities and relations from text."""
        logger.error(f"[EXTRACT] Called with text length: {len(text)}")
        if not text.strip():
            logger.error("[EXTRACT] Empty text, returning empty")
            return ExtractedEntities()
        logger.error("[EXTRACT] Text not empty, proceeding")

        # Limit text length for token efficiency
        max_chars = 12000
        analysis_text = text[:max_chars]
        if len(text) > max_chars:
            analysis_text += f"\n\n[TRUNCATED - original length: {len(text)} chars]"
        logger.error("[EXTRACT] Text truncated, creating prompt")

        prompt = EXTRACTION_PROMPT.replace("{text}", analysis_text)
        logger.error(f"[EXTRACT] Prompt length: {len(prompt)}")
        logger.error(f"[EXTRACT] Prompt preview: {prompt[:500]}")

        for attempt in range(self.max_retries + 1):
            try:
                logger.error(f"[EXTRACT] Attempt {attempt + 1}/{self.max_retries + 1} calling LLM, model={self.model}")
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an academic information extraction expert. Output ONLY valid JSON matching the schema. No reasoning, no markdown, no extra text."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0,
                )
                content = response.choices[0].message.content
                logger.error(f"[EXTRACT] Raw response (first 1000 chars): {content[:1000]}")
                
                # Parse JSON manually
                import json
                try:
                    data = json.loads(content)
                    result = ExtractedEntities(**data)
                    # CITES is only valid as Paper->Paper; drop placeholder/self citations
                    result.relations = [
                        r for r in result.relations
                        if not (
                            r.relation == RelationType.CITES
                            and (
                                r.source_type != EntityType.PAPER
                                or r.target_type != EntityType.PAPER
                                or r.target_name.strip().lower() in ("current paper", paper_title.strip().lower())
                            )
                        )
                    ]
                    logger.info(f"Extracted: {len(result.authors)} authors, {len(result.concepts)} concepts, "
                               f"{len(result.methods)} methods, {len(result.datasets)} datasets, "
                               f"{len(result.relations)} relations")
                    return result
                except json.JSONDecodeError as je:
                    logger.warning(f"JSON parse error: {je}")
                    if attempt == self.max_retries:
                        logger.error(f"All extraction attempts failed, returning empty entities")
                        return ExtractedEntities()
                except ValidationError as ve:
                    logger.warning(f"Validation error: {ve}")
                    if attempt == self.max_retries:
                        logger.error(f"All extraction attempts failed, returning empty entities")
                        return ExtractedEntities()

            except Exception as e:
                logger.warning(f"Extraction attempt {attempt + 1} failed: {type(e).__name__}: {e}")
                if attempt == self.max_retries:
                    logger.error(f"All extraction attempts failed, returning empty entities")
                    return ExtractedEntities()

        return ExtractedEntities()

    async def extract_from_chunks(self, chunks: list[str], paper_title: str = "") -> ExtractedEntities:
        """Extract from multiple chunks and merge results.

        Budget optimization: chunks are grouped into ~10k-char windows and each
        window costs ONE LLM call (extract() truncates at 12k chars anyway).
        Per-chunk calls would burn ~195 calls on a single GraphRAG paper.
        """
        windows: list[str] = []
        cur: list[str] = []
        n = 0
        for chunk in chunks:
            if n + len(chunk) > 10000 and cur:
                windows.append("\n\n".join(cur))
                cur, n = [], 0
            cur.append(chunk)
            n += len(chunk)
        if cur:
            windows.append("\n\n".join(cur))

        all_entities = ExtractedEntities()
        for i, window in enumerate(windows):
            logger.debug(f"Extracting window {i+1}/{len(windows)}")
            entities = await self.extract(window, paper_title)
            all_entities.authors.extend(entities.authors)
            all_entities.concepts.extend(entities.concepts)
            all_entities.methods.extend(entities.methods)
            all_entities.datasets.extend(entities.datasets)
            all_entities.relations.extend(entities.relations)

        # Deduplicate by name
        all_entities.authors = self._deduplicate_entities(all_entities.authors, "name")
        all_entities.authors = self._split_author_names(all_entities.authors)
        all_entities.concepts = self._deduplicate_entities(all_entities.concepts, "name")
        all_entities.methods = self._deduplicate_entities(all_entities.methods, "name")
        all_entities.datasets = self._deduplicate_entities(all_entities.datasets, "name")
        all_entities.relations = self._deduplicate_relations(all_entities.relations)

        return all_entities

    def _deduplicate_entities(self, entities: list, key_attr: str) -> list:
        seen = set()
        unique = []
        for e in entities:
            key = getattr(e, key_attr, "").lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    def _deduplicate_relations(self, relations: list[RelationEntity]) -> list[RelationEntity]:
        seen = set()
        unique = []
        for r in relations:
            key = (r.source_type, r.source_name.lower(), r.relation, r.target_type, r.target_name.lower())
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    def _split_author_names(self, authors: list) -> list:
        """Split combined author names (e.g., 'A and B', 'A, B') into individual authors."""
        import re
        split_authors = []
        for a in authors:
            name = a.name.strip()
            # Split on common delimiters
            parts = re.split(r'\s+(?:and|&)\s+|,\s*', name)
            for part in parts:
                part = part.strip()
                if part and len(part) > 2:  # Filter initials-only
                    # Create new AuthorEntity with same institution
                    split_authors.append(type(a)(name=part, institution=a.institution))
        return split_authors if split_authors else authors


# Simplified extractor for fallback (no instructor)
class SimpleEntityExtractor:
    """Fallback extractor using basic LLM call without structured output."""

    def __init__(self, llm_client, model: str = "inclusionai/ling-3.2-flash:free"):
        self.llm_client = llm_client
        self.model = model

    async def extract(self, text: str) -> ExtractedEntities:
        prompt = f"""Extract entities from this academic text as JSON:
{{
  "authors": [{{"name": "", "institution": ""}}],
  "concepts": [{{"name": "", "category": ""}}],
  "methods": [{{"name": "", "description": ""}}],
  "datasets": [{{"name": "", "domain": ""}}],
  "relations": [{{"source_type": "", "source_name": "", "relation": "", "target_type": "", "target_name": ""}}]
}}

Text: {text[:8000]}"""

        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"},
            )
            import json
            data = json.loads(response.choices[0].message.content)
            return ExtractedEntities(**data)
        except Exception as e:
            logger.error(f"Simple extraction failed: {e}")
            return ExtractedEntities()