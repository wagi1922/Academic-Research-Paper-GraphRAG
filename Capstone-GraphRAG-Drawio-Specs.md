---
title: "Capstone GraphRAG — Draw.io Diagram Specifications"
tags: [capstone, graphrag, drawio, diagrams]
updated: 2026-11-23
---

# Capstone GraphRAG — Draw.io Diagram Specifications (4 Halaman)

File target: `/home/guard/Documents/perkuliahan/sem 7/Cap/Capstone-Drawings-Rapi.drawio`

---

## Halaman 1: System Context Diagram (C4 Level 1)

**Tujuan:** Tunjukkan actor, sistem GraphRAG, dan sistem eksternal — big picture untuk dosen non-teknis.

### Elemen (Containers/Actors)

| Elemen | Tipe | Label | Deskripsi |
|---|---|---|---|
| `Researcher/Student` | Person (Actor) | Peneliti / Mahasiswa | Pengguna akhir yang query literatur |
| `GraphRAG System` | Software System | GraphRAG — Academic Paper Knowledge Engine | Sistem utama (FastAPI + Neo4j + LLM) |
| `Neo4j Database` | External System | Neo4j 5.18 (Graph DB + Vector Index) | Penyimpanan knowledge graph & embedding |
| `Grobid Server` | External System | Grobid (Self-hosted PDF Parser) | Ekstrak teks terstruktur dari PDF |
| `OpenRouter API` | External System | OpenRouter (Free LLM: Nemotron, Ling) | Inference LLM untuk extraction & synthesis |
| `Local Embedding Service` | External System | all-MiniLM-L6-v2 (384-d, :8788) | Embedding lokal, zero-cost |
| `Ollama Local` | External System | Ollama (Fallback LLM/Embedding) | Fallback saat quota habis |

### Relasi (Arrows)

| Dari | Ke | Label | Teknologi |
|---|---|---|---|
| Researcher | GraphRAG System | Query / Upload PDF | HTTPS/REST (JSON) |
| GraphRAG System | Neo4j | Read/Write Graph + Vector | Bolt + Cypher |
| GraphRAG System | Grobid | Parse PDF → Text | HTTP REST |
| GraphRAG System | OpenRouter | LLM Inference | HTTPS (OpenAI-compatible) |
| GraphRAG System | Local Embedding | Generate Embeddings | HTTP (OpenAI-compatible :8788) |
| GraphRAG System | Ollama | Fallback Inference | HTTP (localhost:11434) |

### Visual Style (Draw.io)
- **Person:** Stick figure icon, warna `#58a6ff`
- **Software System:** Rounded rectangle, fill `#1f6feb`, border `#58a6ff`, text putih
- **External System:** Rectangle, fill `#21262d`, border `#30363d`, text `#e6edf3`
- **Arrows:** Solid, warna `#8b949e`, label di tengah, font size 10
- **Background:** Dark `#0d1117` (consistent dengan Marp theme)
- **Title:** "System Context Diagram — GraphRAG" di atas kiri, font 16, `#58a6ff`

---

## Halaman 2: Container Diagram (C4 Level 2)

**Tujuan:** Tunjukkan container internal GraphRAG System — untuk dosen teknis & reviewer.

### Container (di dalam boundary "GraphRAG System")

| Container | Teknologi | Deskripsi | Responsibilities |
|---|---|---|---|
| **API Gateway** | FastAPI (Python 3.11) | Entry point REST API | Routing, validation, auth, rate limit, SSE |
| **Ingestion Service** | FastAPI + Grobid Client | Pipeline PDF → Graph | Parse, chunk, extract, inject, index |
| **Query/GraphRAG Service** | FastAPI + Neo4j Driver | Pipeline Query → Answer | Vector search, graph traversal, synthesis |
| **Visualization Service** | FastAPI + JSON Serializer | Graph → React Flow/D3 | Subgraph extraction, format conversion |
| **Embedding Service** | all-MiniLM-L6-v2 (Local) | Generate Vectors | `/v1/embeddings` OpenAI-compatible |

### External Systems (di luar boundary)

| System | Teknologi |
|---|---|
| Neo4j Database | Neo4j 5.18 + APOC + Vector Index |
| Grobid Server | Grobid 0.8.x (Docker) |
| OpenRouter LLM | Nemotron-3.5-Lightning:free, Ling-3.2-Flash:free |
| Ollama Local | Llama-3.1-8B, nomic-embed-text (fallback) |

### Relasi Container → External

| Container | External | Protocol |
|---|---|---|
| Ingestion Service | Grobid | HTTP REST |
| Ingestion Service | Neo4j | Bolt (Cypher batch) |
| Ingestion Service | Embedding Service | HTTP :8788 |
| Query Service | Neo4j | Bolt (Vector + Graph) |
| Query Service | OpenRouter | HTTPS (LLM) |
| Query Service | Embedding Service | HTTP :8788 (query embedding) |
| Visualization Service | Neo4j | Bolt (Subgraph query) |
| API Gateway | All Services | Internal HTTP (Docker network) |

### Visual Style
- **Boundary "GraphRAG System":** Dashed rounded rect, stroke `#58a6ff`, label top-left
- **Containers:** Rounded rect, fill `#161b22`, border `#30363d`, icon gear/server
- **External Systems:** Rect, fill `#21262d`, border `#30363d`, icon database/cloud
- **Arrows:** Solid untuk sync, dashed untuk async, label protocol
- **Legend:** Bottom-right: Container, External System, Sync, Async

---

## Halaman 3: Component Diagram — Ingestion Pipeline

**Tujuan:** Detail teknis pipeline ingestion — untuk demonstrasi kedalaman implementasi.

### Components (di dalam Ingestion Service)

| Component | Class/Module | Responsibility |
|---|---|---|
| `PDFParser` | `app/ingestion/parser.py` | Grobid/LlamaParse wrapper, return raw text + metadata |
| `Chunker` | `app/ingestion/chunker.py` | 3 strategi: Fixed, Semantic, Proposition (configurable) |
| `EntityExtractor` | `app/ingestion/extractor.py` | Instructor + Pydantic → structured entities & relations |
| `GraphWriter` | `app/ingestion/graph_writer.py` | Batch Cypher async (APOC), idempotent by paper_id |
| `EmbeddingIndexer` | `app/ingestion/embedding_indexer.py` | Call embedding service → upsert Neo4j vector index |
| `IngestionOrchestrator` | `app/ingestion/orchestrator.py` | Coordinate flow, progress tracking, error handling |

### Data Flow (Sequence)

```
1. POST /api/v1/papers/ingest (multipart PDF)
         │
         ▼
2. IngestionOrchestrator.start_job(paper_id)
         │
         ├─▶ PDFParser.parse(pdf_bytes) → raw_text, metadata
         │
         ├─▶ Chunker.chunk(raw_text, strategy) → List[Chunk]
         │
         ├─▶ EntityExtractor.extract(chunks) → ExtractedEntities
         │       (Pydantic: Author, Concept, Method, Dataset, Relations)
         │
         ├─▶ GraphWriter.inject(paper_id, entities, relations)
         │       → Batch Cypher: MERGE nodes, CREATE edges
         │
         ├─▶ EmbeddingIndexer.index(paper_id, chunks)
         │       → embedding_service.embed(chunks) → vectors
         │       → Neo4j Vector Index upsert
         │
         ▼
3. Response: {paper_id, entities_count, chunks_indexed, duration_ms}
```

### Visual Style
- **Components:** Rounded rect, fill `#1f6feb20`, border `#1f6feb`, icon component
- **Data Flow Arrows:** Numbered circles (1, 2, 3...), solid `#58a6ff`
- **Pydantic Schema Box:** Side note dengan schema `ExtractedEntities` (collapsed)
- **Async Indicator:** Lightning bolt icon pada GraphWriter → Neo4j arrow
- **Config Box:** "Chunking Strategy: Fixed / Semantic / Proposition (E1 variable)"

---

## Halaman 4: Sequence Diagram — Query / GraphRAG Pipeline

**Tujuan:** Alur query end-to-end dengan detail timings — untuk slide teknis & Q&A.

### Participants (Lifelines)

| Participant | Type | Label |
|---|---|---|
| `User` | Actor | Peneliti |
| `API Gateway` | Boundary | FastAPI `/api/v1/query` |
| `QueryOrchestrator` | Control | `app/query/orchestrator.py` |
| `VectorSearch` | Entity | `app/query/vector_search.py` |
| `GraphTraversal` | Entity | `app/query/graph_traversal.py` |
| `ContextBuilder` | Entity | `app/query/context_builder.py` |
| `LLMSynthesizer` | Entity | `app/query/synthesizer.py` (Instructor + OpenRouter) |
| `CitationValidator` | Entity | `app/query/validator.py` |
| `Neo4j` | Database | Graph DB + Vector Index |

### Sequence (Messages)

```
User ->> API Gateway: POST /api/v1/query {query, top_k=5, depth=2, stream=false}
API Gateway ->> QueryOrchestrator: execute(query, params)

QueryOrchestrator ->> VectorSearch: search(query_embedding, top_k)
VectorSearch ->> Neo4j: CALL db.index.vector.queryNodes('chunk_vector_idx', $top_k, $embedding)
Neo4j -->> VectorSearch: List[Paper] (seed papers + scores)
VectorSearch -->> QueryOrchestrator: seed_papers

QueryOrchestrator ->> GraphTraversal: traverse(seed_paper_ids, depth)
GraphTraversal ->> Neo4j: CALL apoc.path.subgraphAll(seeds, {maxLevel: $depth, relationshipFilter: "CITES|USES_METHOD|USES_DATASET|ADDRESSES_TOPIC"})
Neo4j -->> GraphTraversal: Subgraph (nodes + edges)
GraphTraversal -->> QueryOrchestrator: subgraph

QueryOrchestrator ->> ContextBuilder: build(query, seed_papers, subgraph)
ContextBuilder -->> QueryOrchestrator: prompt_context {system_prompt, user_prompt, chunks, graph_paths}

QueryOrchestrator ->> LLMSynthesizer: synthesize(prompt_context)
LLMSynthesizer ->> OpenRouter: POST /v1/chat/completions (Nemotron/Ling free)
OpenRouter -->> LLMSynthesizer: Answer + [Paper ID] citations
LLMSynthesizer -->> QueryOrchestrator: raw_answer, citations

QueryOrchestrator ->> CitationValidator: validate(citations, subgraph)
CitationValidator -->> QueryOrchestrator: validated_citations, grounding_score

QueryOrchestrator -->> API Gateway: {answer, sources: [...], graph_path: [...], grounding_score, latency_ms}
API Gateway -->> User: 200 OK JSON (atau SSE stream)
```

### Timing Annotations (Optional)
- Vector Search: ~50–150ms
- Graph Traversal: ~100–300ms (depth=2)
- LLM Synthesis: ~2–8s (dominant)
- Validation: ~50ms
- **Total Target P95: < 10s**

### Visual Style (Draw.io Sequence)
- **Lifelines:** Dashed vertical lines, participant boxes top
- **Messages:** Solid arrows (sync), open arrows (return), numbered
- **Activation Bars:** Thin rect pada lifeline saat active
- **Alt/Loop Frames:** Untuk retry logic (LLM JSON parse retry 2x)
- **Color Coding:**
  - User/API: `#58a6ff`
  - Orchestrator: `#a371f7`
  - Search/Traversal: `#3fb950`
  - LLM/External: `#d29922`
  - Database: `#f85149`
- **Notes:** Sticky notes untuk key decisions (e.g., "Citation validation prevents hallucination")

---

## Export Settings

### PNG Export (untuk slide Marp/PPTX)
- **File:** `Capstone-Drawings-Rapi-page-{1,2,3,4}.png`
- **Resolution:** 1920x1080 (2x scale) atau 3840x2160 (4x untuk print)
- **Background:** Transparent (atau `#0d1117` untuk dark theme)
- **Crop:** Tight ke content

### Draw.io File Management
- **Source:** `/home/guard/Documents/perkuliahan/sem 7/Cap/Capstone-Drawings-Rapi.drawio`
- **Version Control:** Commit ke Git repo bersama slide
- **Update Protocol:** Edit draw.io → Export PNG → Replace di slide assets → Commit

### Color Palette (Consistent dengan Marp Theme)
| Role | Hex | Usage |
|---|---|---|
| Primary/Accent | `#58a6ff` | Borders, arrows, highlights |
| Background Dark | `#0d1117` | Slide bg, diagram bg |
| Surface | `#161b22` | Container fill |
| Border | `#30363d` | Container borders |
| Text Primary | `#e6edf3` | Labels, titles |
| Text Muted | `#8b949e` | Descriptions, legends |
| Success | `#3fb950` | Graph traversal, success paths |
| Warning | `#d29922` | LLM external calls |
| Danger | `#f85149` | Database, critical paths |
| Purple | `#a371f7` | Orchestrator/control |

---

## Checklist Diagram Completeness

- [ ] **Hal 1:** System Context — Actor, System, 5 External Systems, 6 relasi
- [ ] **Hal 2:** Container — 5 Container internal, 4 External, relasi protocol
- [ ] **Hal 3:** Component Ingestion — 6 Components, numbered data flow, Pydantic schema note
- [ ] **Hal 4:** Sequence Query — 9 Participants, full sequence, timing annotations, alt frames
- [ ] **Export PNG** semua 4 halaman ke folder slide assets
- [ ] **Embed di Marp/PPTX** slide 5, 7, 8
- [ ] **Commit drawio + PNG** ke Git repo