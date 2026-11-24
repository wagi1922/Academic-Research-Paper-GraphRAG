# PRD Teknis — Academic & Research Paper GraphRAG

**Project:** Capstone GraphRAG  
**Tim:** 3 orang (UIR Teknik Informatika Sem 7)  
**Status:** Finalisasi Minggu 3  
**Updated:** 2026-11-21

---

## 1. Ringkasan Eksekutif

| Parameter | Nilai |
|---|---|
| **Nama Produk** | Academic & Research Paper GraphRAG |
| **Domain** | Literatur ilmiah (CS, ML, Economics) |
| **Core Capability** | Ingestion PDF → Knowledge Graph (Neo4j) → GraphRAG Query + Visualisasi |
| **Arsitektur** | FastAPI + Neo4j 5.18 + OpenRouter LLM/Embeddings + Grobid Parser |
| **Target User** | Mahasiswa, peneliti, dosen — eksplorasi paper via natural language |
| **Timeline** | 10 minggu (14 Nov 2026 – ~19 Jan 2027) |

---

## 2. Arsitektur Sistem

### 2.1 High-Level Diagram

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        UI[Frontend Vue 3 + Cytoscape.js]
        CLI[cURL / Postman]
    end

    subgraph API["API Layer (FastAPI)"]
        GW[API Gateway /router]
        ING[/api/v1/papers/ingest*]
        QRY[/api/v1/query*]
        GRPH[/api/v1/graph*]
        HLTH[/health]
    end

    subgraph Core["Core Pipeline"]
        PAR[PDFParser (Grobid)]
        CHK[Chunker (Fixed/Semantic/Proposition)]
        EXT[EntityExtractor (LLM + Pydantic)]
        GWRT[GraphWriter (Batch Cypher)]
        EMB[EmbeddingService (OpenRouter/Local)]
        VEC[VectorSearch (Neo4j Vector Index)]
        GTT[GraphTraversal (Cypher APOC)]
        CTX[ContextBuilder (Prompt Assembly)]
        SYN[AnswerSynthesizer (LLM + Citations)]
        VAL[CitationValidator (Grounding Check)]
    end

    subgraph Data["Data Layer"]
        N4J[(Neo4j 5.18\nGraph + Vector Index)]
        GRB[Grobid Docker\nlocalhost:8070]
        OR[OpenRouter API\nLLM + Embeddings (FREE ONLY)]
    end

    Client --> API
    API --> Core
    Core --> Data
```

### 2.2 Component Responsibilities

| Komponen | File/Module | Responsibility |
|---|---|---|
| **PDFParser** | `app/ingestion/parser.py` | Grobid REST call, extract full_text + sections + metadata |
| **Chunker** | `app/ingestion/chunker.py` | 4 strategi: fixed_512_50, fixed_1024_100, semantic_nomic, proposition_gpt4o_mini |
| **EntityExtractor** | `app/ingestion/extractor.py` | LLM structured output → Author, Concept, Method, Dataset, Relations |
| **GraphWriter** | `app/ingestion/graph_writer.py` | Batch Cypher MERGE, constraints, vector index upsert |
|| **EmbeddingService** | `app/ingestion/embedding_service.py` | OpenRouter FREE models only (`text-embedding-3-small` fallback, `nomic-embed-text-v1.5:free`, `inclusionai/ling-3.2-flash:free` for embeddings) ||
| **VectorSearch** | `app/retrieval/vector_search.py` | `db.index.vector.queryNodes` paper & chunk level |
| **GraphTraversal** | `app/retrieval/graph_traversal.py` | Multi-hop Cypher from seed papers, configurable depth/relation_types |
| **ContextBuilder** | `app/retrieval/context_builder.py` | Assemble chunks + paths + entities → prompt template |
| **AnswerSynthesizer** | `app/retrieval/synthesizer.py` | LLM call (OpenRouter), streaming support, citation format enforcement |
| **CitationValidator** | `app/retrieval/synthesizer.py::validate_answer_grounding` | Check citations exist in retrieved context, compute grounding_score |

---

## 3. Data Model (Neo4j Schema)

### 3.1 Node Labels & Properties

| Label | Properties | Constraints |
|---|---|---|
| `Paper` | id (PK), title, abstract, year, doi, venue, keywords[], embedding[1536] | `CREATE CONSTRAINT FOR (p:Paper) REQUIRE p.id IS UNIQUE` |
| `Author` | id (PK), name, institution | `CREATE CONSTRAINT FOR (a:Author) REQUIRE a.id IS UNIQUE` |
| `Concept` | id (PK), name, category | `CREATE CONSTRAINT FOR (c:Concept) REQUIRE c.id IS UNIQUE` |
| `Method` | id (PK), name, description | `CREATE CONSTRAINT FOR (m:Method) REQUIRE m.id IS UNIQUE` |
| `Dataset` | id (PK), name, domain | `CREATE CONSTRAINT FOR (d:Dataset) REQUIRE d.id IS UNIQUE` |
| `Chunk` | id (PK), paper_id, text, chunk_index, embedding[1536], metadata{} | `CREATE CONSTRAINT FOR (ck:Chunk) REQUIRE ck.id IS UNIQUE` |

### 3.2 Relationship Types

| Type | Source → Target | Properties |
|---|---|---|
| `WROTE` | Author → Paper | — |
| `CITES` | Paper → Paper | — |
| `ADDRESSES_TOPIC` | Paper → Concept | — |
| `USES_METHOD` | Paper → Method | — |
| `USES_DATASET` | Paper → Dataset | — |
| `HAS_CHUNK` | Paper → Chunk | — |
| `MENTIONS` | Chunk → (Author\|Concept\|Method\|Dataset) | confidence (float) |

### 3.3 Vector Indexes

```cypher
// Paper abstract embeddings (1536 dim)
CREATE VECTOR INDEX paper_abstract_vector_idx
FOR (p:Paper) ON (p.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}

// Chunk embeddings (1536 dim)
CREATE VECTOR INDEX chunk_vector_idx
FOR (c:Chunk) ON (c.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}
```

---

## 4. API Contract (OpenAPI v3.1)

### 4.1 Base Configuration

```
Base URL: http://localhost:8000/api/v1
Content-Type: application/json (except multipart upload)
Auth: OpenRouter API key via .env (server-side)
```

### 4.2 Endpoints Summary

| Method | Path | Tag | Description |
|---|---|---|---|
| `GET` | `/` | root | API info |
| `GET` | `/health` | health | Health check (Neo4j connectivity) |
| `POST` | `/papers/ingest` | ingestion | Single PDF upload + async processing |
| `GET` | `/papers/ingest/status/{job_id}` | ingestion | Job status polling |
| `POST` | `/papers/ingest/batch` | ingestion | Multiple PDFs (max 20) |
| `POST` | `/query/` | query | Main GraphRAG query |
| `POST` | `/query/stream` | query | SSE streaming query |
| `GET` | `/query/suggestions` | query | Autocomplete suggestions |
| `GET` | `/graph/visualize` | graph | Subgraph for visualization |
| `GET` | `/graph/paper/{paper_id}/subgraph` | graph | Paper-centered citation network |
| `GET` | `/graph/concept/{concept_name}/papers` | graph | Papers by concept |
| `GET` | `/graph/method/{method_name}/papers` | graph | Papers by method |
| `GET` | `/graph/dataset/{dataset_name}/papers` | graph | Papers by dataset |
| `GET` | `/graph/stats` | graph | Global graph statistics |

### 4.3 Request/Response Schemas

#### Health Check
```json
GET /health
Response 200:
{
  "status": "healthy|degraded",
  "neo4j": "connected|error: ...",
  "version": "0.1.0"
}
```

#### Ingest Single Paper
```json
POST /papers/ingest
Content-Type: multipart/form-data

Fields:
- file: PDF (required)
- title: string (required)
- year: integer (optional)
- doi: string (optional)
- venue: string (optional)
- keywords: string (comma-separated, optional)
- chunking_strategy: enum[fixed_512_50, fixed_1024_100, semantic_nomic, proposition_gpt4o_mini] (default: fixed_512_50)

Response 202:
{
  "paper_id": "job_id_temp",
  "title": "...",
  "status": "processing",
  "message": "Ingestion started. Check /papers/ingest/status/{job_id} for progress.",
  "chunks_indexed": 0,
  "entities_extracted": {}
}
```

#### Ingest Status
```json
GET /papers/ingest/status/{job_id}
Response 200:
{
  "job_id": "...",
  "status": "pending|processing|completed|failed",
  "progress": 0-100,
  "message": "...",
  "result": { IngestResponse } | null,
  "error": string | null
}
```

#### Batch Ingest
```json
POST /papers/ingest/batch
Content-Type: multipart/form-data
Fields: files[] (max 20), titles[], years[], dois[], venues[], chunking_strategy

Response 202:
{ "job_id": "...", "status": "processing", "total_files": N }
```

#### Query GraphRAG
```json
POST /query/
Request:
{
  "query": "string (3-2000 chars)",
  "top_k": 5 (1-20),
  "depth": 2 (1-3),
  "include_chunks": true,
  "stream": false,
  "retrieval_only": false
}

Response 200:
{
  "answer": "string",
  "sources": [
    { "paper_id": "...", "title": "...", "year": 2024, "authors": [...], "relevance_score": 0.85, "citation_text": "..." }
  ],
  "graph_path": [
    { "source": "...", "relation": "USES_METHOD", "target": "...", "source_type": "Paper", "target_type": "Method" }
  ],
  "extracted_entities": { "concepts": [...], "methods": [...], "datasets": [...] },
  "retrieval_metadata": {
    "vector_results": 5,
    "chunk_results": 12,
    "graph_paths": 8,
    "seed_papers": [...],
    "grounding_score": 0.87,
    "valid_citations": 3,
    "total_citations": 4,
    "latency_ms": 6200
  }
}
```

#### Streaming Query (SSE)
```json
POST /query/stream
Request: same as /query/
Response: text/event-stream
data: token1
data: token2
...
data: [DONE]
```

#### Graph Visualization
```json
GET /graph/visualize?paper_id=...&depth=2&max_nodes=100&relation_types=CITES,USES_METHOD
Response 200:
{
  "nodes": [
    { "id": "...", "label": "Attention Is All You Need", "type": "paper", "properties": {...}, "classes": "paper" }
  ],
  "edges": [
    { "id": "...", "source": "paper1", "target": "method1", "label": "USES_METHOD", "type": "uses_method", "properties": {} }
  ],
  "metadata": { "type": "paper_traversal", "seed_paper_id": "...", "depth": 2, "node_count": 45, "edge_count": 67 }
}
```

#### Graph Stats
```json
GET /graph/stats
Response 200:
{
  "papers": 200,
  "authors": 1500,
  "concepts": 800,
  "methods": 400,
  "datasets": 150,
  "relations": 12000
}
```

---

## 5. Ingestion Pipeline Detail

### 5.1 Flow

```
PDF Upload
    ↓
Grobid Parse (localhost:8070) → full_text, sections, metadata
    ↓
Chunker (strategy configurable)
    ├─ fixed_512_50: char-based, 512/50 overlap
    ├─ fixed_1024_100: char-based, 1024/100 overlap
    ├─ semantic_nomic: semantic boundaries via embedding similarity
    └─ proposition_gpt4o_mini: LLM extracts atomic propositions
    ↓
EntityExtractor (LLM + Pydantic) — requires OpenRouter key
    → Authors, Concepts, Methods, Datasets, Relations
    ↓
GraphWriter (batch Cypher MERGE)
    → Paper, Author, Concept, Method, Dataset, Chunk nodes
    → WROTE, CITES, ADDRESSES_TOPIC, USES_METHOD, USES_DATASET, HAS_CHUNK, MENTIONS edges
    ↓
EmbeddingService (per chunk + paper abstract)
    → Neo4j Vector Index upsert
```

### 5.2 Error Handling & Retry

| Step | Retry | Fallback |
|---|---|---|
| Grobid Parse | 3x exp backoff | LlamaParse API |
| Entity Extraction | 2x (JSON parse fail) | Simplified schema, retry |
| Graph Injection | 3x (transient Neo4j) | Queue for manual replay |
| Vector Index | 3x | Re-index batch job |

### 5.3 Chunking Strategies Comparison

| Strategy | Speed | Quality | Use Case |
|---|---|---|---|
| `fixed_512_50` | ⚡⚡⚡ Fast | Baseline | Default, high throughput |
| `fixed_1024_100` | ⚡⚡ Medium | Better context | Long papers, method descriptions |
| `semantic_nomic` | ⚡ Slow | Higher precision | When retrieval quality critical |
| `proposition_gpt4o_mini` | 🐢 Slowest | Maximum precision | Gold-standard experiments |

---

## 6. GraphRAG Query Pipeline Detail

### 6.1 Flow

```
User Query
    ↓
EmbeddingService.embed_text(query) → query_embedding[1536]
    ↓
VectorSearch.search_papers(query_embedding, top_k, min_score=0.3)
    → seed_papers[] (paper_id, title, score)
    ↓
GraphTraversal.traverse_from_papers(seed_paper_ids, depth, max_nodes_per_hop)
    → nodes[], edges[], paths[]
    ↓
VectorSearch.search_chunks(query_embedding, top_k*2, paper_ids=seed_paper_ids)
    → chunk_results[]
    ↓
ContextBuilder.build(RetrievalContext)
    → prompt_context { vector_chunks, graph_paths, seed_papers, extracted_entities }
    ↓
AnswerSynthesizer.synthesize(query, prompt_context)
    → LLM answer with [Paper ID] citations
    ↓
CitationValidator.validate_answer_grounding(answer, context)
    → grounding_score, valid_citations, total_citations
    ↓
Final Response (QueryResponseExtended)
```

### 6.2 Prompt Template (Context Assembly)

```
SYSTEM: Anda adalah research assistant. Jawab berdasarkan KONTEKS yang diberikan.
Sertakan sitasi [Paper ID] untuk setiap klaim. Jika info tidak ada, nyatakan "Tidak ditemukan dalam konteks."

KONTEKS VECTOR CHUNKS:
{vector_chunks}  // List of: [Paper ID] Title (Year) - Chunk text...

KONTEKS GRAPH PATHS:
{graph_paths}    // List of: Paper A --[RELATION]--> Entity B

ENTITAS TERIDENTIFIKASI:
{extracted_entities}  // {concepts: [...], methods: [...], datasets: [...]}

PERTANYAAN: {user_query}

JAWABAN:
```

### 6.3 Query Parameters & Defaults

| Parameter | Default | Range | Description |
|---|---|---|---|
| `top_k` | 5 | 3–20 | Seed papers from vector search |
| `depth` | 2 | 1–3 | Graph traversal hops |
| `include_chunks` | true | bool | Include vector chunks in context |
| `stream` | false | bool | SSE streaming response |
| `retrieval_only` | false | bool | Skip LLM synthesis, return retrieval results |

---

## 7. Experiment Design (E1–E4)

### 7.1 Experiment Matrix

|| Exp | Variable | Values Tested | Fixed Config | Metrics ||
||---|---|---|---|---|---|
|| **E1** | Chunking Strategy | fixed_512_50, fixed_1024_100, semantic_nomic, proposition_gpt4o_mini | Embedding: nomic-embed-text-v1.5:free, top_k=5, depth=2, LLM: inclusionai/ling-3.2-flash:free | Precision@5, Recall@5, Answer F1, Citation Acc, Latency ||
|| **E2** | Embedding Model | nomic-embed-text-v1.5:free, inclusionai/ling-3.2-flash:free, google/gemma-4-31b-it:free, nvidia/nemotron-3.5-lightning:free, particle-ai/particle-1:free | Chunking: best E1, top_k=5, depth=2, LLM: inclusionai/ling-3.2-flash:free | Precision@5, Recall@5, MRR, Latency, Token Cost ||
|| **E3** | Retrieval Params | top_k: 3,5,10,15 × depth: 1,2,3 | Chunking: best E1, Embedding: best E2, LLM: inclusionai/ling-3.2-flash:free | Grounding, Citation Acc, Graph Paths, Latency ||
|| **E4** | Ablation | Full GraphRAG, Vector Only, Graph Only, No Entities, No Citations | Best E1+E2+E3 config | Grounding delta, Citation Acc delta, Latency delta ||

### 7.2 Gold Standard

- **Corpus:** 50 paper akademik (CS.CL, CS.LG, ECON) — arXiv + manual curation
- **QA Pairs:** 30 pertanyaan (20 train + 10 test)
- **Query Types:** Factual lookup, Method comparison, Concept explanation, Multi-hop reasoning
- **Expected:** Reference answer + expected citations per query

### 7.3 Success Criteria

| Metric | Target |
|---|---|
| Answer F1 (test set) | ≥ 0.70 |
| Citation Accuracy | ≥ 0.85 |
| Latency p95 | ≤ 8 detik |
| Token Cost/query | ≤ $0.05 |
| Ablation Gap (Full vs Vector Only) | ≥ 10% F1 improvement |

---

## 8. Configuration Management

### 8.1 Environment Variables (`.env`)

```env
# OpenRouter — FREE MODELS ONLY (no paid, no local)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=inclusionai/ling-3.2-flash:free
EMBEDDING_MODEL=nomic-embed-text-v1.5:free
# Fallback free models (uncomment to swap):
# LLM_MODEL=particle-ai/particle-1:free
# LLM_MODEL=nvidia/nemotron-3.5-lightning:free
# LLM_MODEL=google/gemma-4-31b-it:free
# EMBEDDING_MODEL=inclusionai/ling-3.2-flash:free
# EMBEDDING_MODEL=particle-ai/particle-1:free

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure_password

# Grobid
GROBID_URL=http://localhost:8070

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# App
LOG_LEVEL=INFO
```

### 8.2 Docker Compose Services

```yaml
services:
  neo4j:
    image: neo4j:5.18
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: "neo4j/${NEO4J_PASSWORD}"
      NEO4J_PLUGINS: '["apoc"]'
    volumes: [neo4j_data:/data, neo4j_logs:/logs]

  grobid:
    image: lfoppiano/grobid:0.8.0
    ports: ["8070:8070"]
    deploy:
      resources:
        limits: {memory: 4G}

  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [neo4j, grobid]
    volumes: [./backend:/app]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 9. Development Workflow

### 9.1 Git Branching (GitFlow Ringan)

```
main ← release/v1.0 ← develop ← feature/*
                    ↑
              hotfix/*
```

| Branch | Purpose | Merge Via |
|---|---|---|
| `main` | Production-ready, tagged | PR from `release/*` |
| `develop` | Integration branch | PR from `feature/*`, `hotfix/*` |
| `feature/<name>` | Single feature/experiment | PR to `develop` (1 reviewer) |
| `release/vX.Y` | Stabilisasi demo | PR to `main` |
| `hotfix/<issue>` | Critical bug on main | PR to `main` + `develop` |

### 9.2 Commit Convention (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | Example |
|---|---|
| `feat` | `feat(ingestion): add Grobid parser integration` |
| `fix` | `fix(query): handle empty graph traversal result` |
| `refactor` | `refactor(schemas): unify entity extraction output` |
| `test` | `test(retrieval): add vector search unit tests` |
| `docs` | `docs(api): update OpenAPI spec for /query endpoint` |
| `chore` | `chore(docker): update Neo4j version to 5.18` |
| `exp` | `exp(E1): add semantic chunking experiment script` |

### 9.3 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
stages:
  - lint:
      - ruff check .
      - black --check .
      - mypy app/
  - test:
      - pytest tests/ -v --cov=app --cov-fail-under=70
  - build:
      - docker build -t graphrag-backend .
  - experiment:  # manual trigger
      - python experiments/run_e1_chunking.py
      - python experiments/run_e2_embedding.py
```

---

## 10. Current Status & Next Steps (Minggu 3→4)

### 10.1 Completed (Minggu 1–3)

- ✅ Proposal final & konsultasi dosen
- ✅ Docker Compose (Neo4j, Grobid, Backend)
- ✅ Ingestion Pipeline E2E (Grobid → Chunk → Entity → Neo4j → Vector Index)
- ✅ 271 paper processed, 200 success (~12k chunks), citation graph rebuilt
- ✅ GraphRAG Query Pipeline (Vector + Graph + Context + Synthesis + Validation)
- ✅ E1 Chunking Experiment COMPLETE (2/5 strategies successful)
- ✅ E2 Embedding Experiment COMPLETE (7/10 **free** models successful)
- ✅ E3 Retrieval Params COMPLETE (best: topk10_depth2)
- ✅ E4 Ablation Study COMPLETE (best: full_graphrag)
- ✅ OpenRouter direct API migration (portable, no 9router)
- ✅ **Free model policy applied**: `inclusionai/ling-3.2-flash:free` (LLM), `nomic-embed-text-v1.5:free` (embedding)
- ✅ API server stable on localhost:8000

### 10.2 Blockers

- ❌ **OpenRouter key limit hit** ($0.10/$0.10 used) — QA generation blocked
  - 5 chunking × 30 QA, 8 embedding × 30 QA, QA regen from 200 papers → 403
  - **Free model swap ready**: particle-ai/particle-1:free, nvidia/nemotron-3.5-lightning:free

### 10.3 Next Actions (Minggu 4–5: Fase 2 Desain)

| Priority | Task | Owner | Target |
|---|---|---|---|
| 1 | **Top up OpenRouter $10** / swap key | All | Immediate |
| 2 | Finalize **PRD Teknis** (this doc) → commit | Lead | Hari ini |
| 3 | Generate **OpenAPI spec** (auto from FastAPI) | Backend | Hari ini |
| 4 | Formalize **Experiment Plan** (update docs/experiment_plan.md) | Research | Hari ini |
| 5 | Start **MAKALAH UIR** draft (BAB I–III) via `make_makalah_capstone.py` | Writer | Minggu 4 |
| 6 | Scaffold **Frontend Vue 3 + Cytoscape.js** | Frontend | Minggu 4–5 |
| 7 | Reindex vector dimension (1536 vs 384 local) | Backend | Minggu 4 |

---

## 11. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OpenRouter quota exhausted | High | Blocks LLM calls | Top up $10, **swap to alternate free model** (particle-ai/particle-1:free, nvidia/nemotron-3.5-lightning:free, google/gemma-4-31b-it:free) |
| Grobid parsing fails on specific PDFs | Medium | Incomplete ingestion | Skip + log warning, LlamaParse API backup |
| Neo4j vector index slow at scale | Low | Query latency | Pre-warm index, optimize `db.index.vector.queryNodes` params |
| Gold QA pairs not representative | Medium | Invalid evaluation | Iterate with dosen Minggu 2–3, add 10 pairs if needed |
| Frontend visualization performance | Medium | Demo UX | Limit max_nodes=100, lazy load edges, Web Workers |

---

## 12. Appendix

### 12.1 File Structure

```
Cap/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # ingest.py, query.py, graph.py
│   │   ├── core/                # config.py, neo4j_driver.py, neo4j_migrate.py
│   │   ├── ingestion/           # parser.py, chunker.py, extractor.py, graph_writer.py, embedding_service.py
│   │   ├── retrieval/           # vector_search.py, graph_traversal.py, context_builder.py, synthesizer.py
│   │   ├── schemas/             # entities.py
│   │   └── main.py              # FastAPI entry
│   ├── tests/                   # test_ingestion.py, test_retrieval.py, tests_smoke.py
│   ├── requirements.txt
│   └── Dockerfile
├── experiments/
│   ├── config/                  # e1_chunking.yaml, e2_embedding.yaml, e3_retrieval_params.yaml, e4_ablation.yaml
│   ├── data/                    # gold_qa.json
│   └── results/                 # E1/E2/E3/E4 outputs
├── docs/
│   ├── prd_teknis.md            # THIS FILE
│   ├── experiment_plan.md
│   └── quickstart.md
├── docker-compose.yml
├── .env / .env.example
├── Template.docx                # MAKALAH UIR template
├── make_makalah_capstone.py     # Docx generator
├── Capstone-Drawings-Rapi.drawio
└── README.md
```

### 12.2 Key Scripts

| Script | Purpose |
|---|---|
| `python -m app.core.neo4j_migrate` | Create constraints, indexes, vector indexes |
| `python experiments/run_e1_chunking.py` | Run E1 experiment |
| `python experiments/run_e2_embedding.py` | Run E2 experiment |
| `python experiments/run_e3_retrieval.py` | Run E3 experiment |
| `python experiments/run_e4_ablation.py` | Run E4 experiment |
| `python make_makalah_capstone.py` | Generate MAKALAH UIR .docx from Template.docx |
| `./start_api.sh` | Start backend with PYTHONPATH |

---

*End of PRD Teknis — Academic & Research Paper GraphRAG*