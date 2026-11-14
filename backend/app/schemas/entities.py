from typing import Optional, Literal
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class EntityType(str, Enum):
    PAPER = "Paper"
    AUTHOR = "Author"
    CONCEPT = "Concept"
    METHOD = "Method"
    DATASET = "Dataset"


class RelationType(str, Enum):
    WROTE = "WROTE"
    CITES = "CITES"
    ADDRESSES_TOPIC = "ADDRESSES_TOPIC"
    USES_METHOD = "USES_METHOD"
    USES_DATASET = "USES_DATASET"


# --- Entity Extraction Schemas (for LLM structured output) ---

class AuthorEntity(BaseModel):
    name: str = Field(..., description="Full name of the author")
    institution: Optional[str] = Field(None, description="Affiliation/institution")


class ConceptEntity(BaseModel):
    name: str = Field(..., description="Name of the concept")
    category: str = Field(..., description="Category: task, domain, metric, technique, etc.")


class MethodEntity(BaseModel):
    name: str = Field(..., description="Name of the method/algorithm/model")
    description: Optional[str] = Field(None, description="Brief description of the method")


class DatasetEntity(BaseModel):
    name: str = Field(..., description="Name of the dataset")
    domain: Optional[str] = Field(None, description="Domain/application area")


class RelationEntity(BaseModel):
    source_type: EntityType
    source_name: str
    relation: RelationType
    target_type: EntityType
    target_name: str


class ExtractedEntities(BaseModel):
    authors: list[AuthorEntity] = Field(default_factory=list)
    concepts: list[ConceptEntity] = Field(default_factory=list)
    methods: list[MethodEntity] = Field(default_factory=list)
    datasets: list[DatasetEntity] = Field(default_factory=list)
    relations: list[RelationEntity] = Field(default_factory=list)


# --- API Request/Response Schemas ---

class IngestRequest(BaseModel):
    """For JSON ingestion (DOI/URL)"""
    doi: Optional[str] = None
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None


class IngestResponse(BaseModel):
    paper_id: str
    title: str
    entities_extracted: dict
    chunks_indexed: int
    status: str = "success"


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000, description="Natural language question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of seed papers from vector search")
    depth: int = Field(default=2, ge=1, le=3, description="Graph traversal hops")
    include_chunks: bool = Field(default=True, description="Include vector chunks in context")
    stream: bool = Field(default=False, description="Stream response via SSE")


class SourceCitation(BaseModel):
    paper_id: str
    title: str
    year: Optional[int] = None
    authors: list[str] = Field(default_factory=list)
    relevance_score: Optional[float] = None
    citation_text: Optional[str] = None


class GraphPathElement(BaseModel):
    source: str
    relation: str
    target: str
    source_type: str
    target_type: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceCitation] = Field(default_factory=list)
    graph_path: list[GraphPathElement] = Field(default_factory=list)
    extracted_entities: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class VisualizeRequest(BaseModel):
    paper_id: Optional[str] = None
    concept_id: Optional[str] = None
    method_id: Optional[str] = None
    dataset_id: Optional[str] = None
    max_nodes: int = Field(default=50, ge=10, le=200)


class VisualizeNode(BaseModel):
    id: str
    label: str
    type: str
    properties: dict = Field(default_factory=dict)


class VisualizeEdge(BaseModel):
    source: str
    target: str
    type: str
    properties: dict = Field(default_factory=dict)


class VisualizeResponse(BaseModel):
    nodes: list[VisualizeNode]
    edges: list[VisualizeEdge]


# --- Internal Schemas ---

class PaperCreate(BaseModel):
    id: str
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    embedding: Optional[list[float]] = None


class ChunkCreate(BaseModel):
    id: str
    paper_id: str
    text: str
    chunk_index: int
    embedding: Optional[list[float]] = None
    metadata: dict = Field(default_factory=dict)