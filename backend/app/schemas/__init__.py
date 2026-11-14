from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


# Re-export from entities
from app.schemas.entities import (
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceCitation,
    GraphPathElement,
    VisualizeRequest,
    VisualizeResponse,
    VisualizeNode,
    VisualizeEdge,
    ExtractedEntities,
    AuthorEntity,
    ConceptEntity,
    MethodEntity,
    DatasetEntity,
    RelationEntity,
    EntityType,
    RelationType,
)

__all__ = [
    "IngestRequest",
    "IngestResponse",
    "QueryRequest",
    "QueryResponse",
    "SourceCitation",
    "GraphPathElement",
    "VisualizeRequest",
    "VisualizeResponse",
    "VisualizeNode",
    "VisualizeEdge",
    "ExtractedEntities",
    "AuthorEntity",
    "ConceptEntity",
    "MethodEntity",
    "DatasetEntity",
    "RelationEntity",
    "EntityType",
    "RelationType",
]