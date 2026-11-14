"""
Entity & Relation Extraction Module
Uses LLM with Instructor for structured output extraction.
"""

import logging
import instructor
from openai import AsyncOpenAI
from typing import Optional
from pydantic import BaseModel

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

TEXT TO ANALYZE:
{text}

Return structured output matching the ExtractedEntities schema."""


class EntityExtractor:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openrouter/gpt-4o-mini",
        max_retries: int = 2,
    ):
        self.client = instructor.from_openai(
            AsyncOpenAI(api_key=api_key, base_url=base_url),
            mode=instructor.Mode.JSON,
        )
        self.model = model
        self.max_retries = max_retries

    async def extract(self, text: str, paper_title: str = "") -> ExtractedEntities:
        """Extract entities and relations from text."""
        if not text.strip():
            return ExtractedEntities()

        # Limit text length for token efficiency
        max_chars = 12000
        analysis_text = text[:max_chars]
        if len(text) > max_chars:
            analysis_text += f"\n\n[TRUNCATED - original length: {len(text)} chars]"

        prompt = EXTRACTION_PROMPT.format(text=analysis_text)

        for attempt in range(self.max_retries + 1):
            try:
                result = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an academic information extraction expert."},
                        {"role": "user", "content": prompt},
                    ],
                    response_model=ExtractedEntities,
                    temperature=0,
                    max_retries=0,  # We handle retries manually
                )
                logger.info(f"Extracted: {len(result.authors)} authors, {len(result.concepts)} concepts, "
                           f"{len(result.methods)} methods, {len(result.datasets)} datasets, "
                           f"{len(result.relations)} relations")
                return result

            except Exception as e:
                logger.warning(f"Extraction attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    logger.error(f"All extraction attempts failed, returning empty")
                    return ExtractedEntities()

        return ExtractedEntities()

    async def extract_from_chunks(self, chunks: list[str], paper_title: str = "") -> ExtractedEntities:
        """Extract from multiple chunks and merge results."""
        all_entities = ExtractedEntities()

        for i, chunk in enumerate(chunks):
            logger.debug(f"Extracting from chunk {i+1}/{len(chunks)}")
            entities = await self.extract(chunk, paper_title)
            all_entities.authors.extend(entities.authors)
            all_entities.concepts.extend(entities.concepts)
            all_entities.methods.extend(entities.methods)
            all_entities.datasets.extend(entities.datasets)
            all_entities.relations.extend(entities.relations)

        # Deduplicate by name
        all_entities.authors = self._deduplicate_entities(all_entities.authors, "name")
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


# Simplified extractor for fallback (no instructor)
class SimpleEntityExtractor:
    """Fallback extractor using basic LLM call without structured output."""

    def __init__(self, llm_client, model: str = "gpt-4o-mini"):
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