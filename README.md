# Academic & Research Paper GraphRAG

> **Capstone Project** — Teknik Informatika, Fakultas Teknik, Universitas Islam Riau (UIR)  
> **Tim:** 3 Mahasiswa | **Durasi:** 10 Minggu (14 Nov 2026 – ~19 Jan 2027)

Sistem RAG tingkat lanjut dengan Knowledge Graph untuk literasi ilmiah cross-domain. Menggabungkan vector search + graph traversal untuk retrieval yang kaya konteks dan jawaban ter-grounded dengan sitasi otomatis.

---

## 🎯 Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **Hybrid Retrieval** | Vector search (top-k) + Graph traversal (depth hops) |
| **Entity Extraction** | LLM + Pydantic → Concept, Method, Dataset, Metric + Relations |
| **Knowledge Graph** | Neo4j 5.18 + APOC + GDS + Vector Index |
| **Multi-Strategy Chunking** | Fixed, Semantic, Proposition-based |
| **Citation-Grounded Answers** | Setiap klaim disertai sitasi [Paper ID] |
| **Graph Visualization** | React Flow / D3.js untuk eksplorasi subgraph |
| **Experiment Framework** | E1–E4: Chunking, Embedding, Retrieval, Ablation |
| **Fallback Local LLM** | Ollama (nomic-embed-text, Llama-3.1-8B) saat quota habis |

---

## 🏗️ Arsitektur

### System Context
![System Context](Capstone-Drawings-Rapi.drawio#page-1)

### Container Diagram
![Container](Capstone-Drawings-Rapi.drawio#page-2)

### Component Diagram
![Component](Capstone-Drawings-Rapi.drawio#page-3)

### Sequence Diagram
![Sequence](Capstone-Drawings-Rapi.drawio#page-4)

> **Buka di [draw.io](https://app.diagrams.net/)** → File → Open Device → Pilih `Capstone-Drawings-Rapi.drawio`

---

## 🚀 Quick Start

```bash
# 1. Clone & setup
cd /home/guard/Documents/perkuliahan/sem\ 7/Cap
cp .env.example .env
# Edit .env: isi OPENROUTER_API_KEY & NEO4J_PASSWORD

# 2. Start services
docker compose up -d

# 3. Initialize database schema
docker compose exec backend python -m app.core.neo4j_migrate

# 4. Ingest paper (contoh)
curl -X POST "http://localhost:8000/api/v1/papers/ingest" \
  -F "file=@paper.pdf" \
  -F "title=Attention Is All You Need" \
  -F "year=2017" \
  -F "doi=10.48550/arXiv.1706.03762" \
  -F "chunking_strategy=fixed_512_50"

# 5. Query
curl -X POST "http://localhost:8000/api/v1/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "Apa metode di paper Attention Is All You Need?", "top_k": 5, "depth": 2}'

# 6. Visualisasi graph
curl "http://localhost:8000/api/v1/graph/visualize?paper_id=10.48550/arXiv.1706.03762&depth=2"
```

**Docs lengkap:** [`docs/quickstart.md`](docs/quickstart.md)  
**API Docs:** http://localhost:8000/docs (Swagger) / http://localhost:8000/redoc (ReDoc)

---

## 🧪 Eksperimen

| Eksperimen | Deskripsi | Config |
|------------|-----------|--------|
| **E1** | Chunking Strategy Comparison | `experiments/config/e1_chunking.yaml` |
| **E2** | Embedding Model Comparison | `experiments/config/e2_embedding.yaml` |
| **E3** | Retrieval Parameter Sweep | `experiments/config/e3_retrieval_params.yaml` |
| **E4** | Ablation Study | `experiments/config/e4_ablation.yaml` |

```bash
# Jalankan semua (butuh OpenRouter API key)
python experiments/run_e1_chunking.py
python experiments/run_e2_embedding.py
python experiments/run_e3_retrieval.py
python experiments/run_e4_ablation.py
```

**Rencana detail:** [`docs/experiment_plan.md`](docs/experiment_plan.md)

---

## 📁 Struktur Project

```
Cap/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # ingest, query, graph
│   │   ├── core/                # config, neo4j_driver, neo4j_migrate
│   │   ├── ingestion/           # parser, chunker, extractor, graph_writer
│   │   ├── retrieval/           # vector_search, graph_traversal, context_builder, synthesizer
│   │   ├── schemas/             # Pydantic models (entities)
│   │   └── main.py              # FastAPI entry point
│   ├── tests/                   # Unit & integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── experiments/
│   ├── config/                  # YAML configs E1–E4
│   ├── data/                    # Gold standard QA pairs
│   └── results/                 # Experiment outputs (gitignored)
├── docs/
│   ├── quickstart.md
│   └── experiment_plan.md
├── .github/workflows/ci.yml     # CI/CD pipeline
├── docker-compose.yml
├── Capstone-Drawings-Rapi.drawio
└── README.md
```

---

## 🛠️ Development

```bash
# Local dev setup
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install ruff black mypy pytest pytest-asyncio httpx

# Lint & format
ruff check --fix backend/
black backend/
mypy backend/

# Run tests
docker compose up -d neo4j
pytest backend/tests/ -v --cov=app

# Run backend locally
uvicorn app.main:app --reload --port 8000
```

**Commit Convention:** Conventional Commits (`feat:`, `fix:`, `exp:`, `docs:`, `chore:`, `refactor:`, `test:`)

---

## 📊 Metrik Target (Definition of Done)

| Metrik | Target |
|--------|--------|
| Answer F1 (test set) | ≥ 0.70 |
| Citation Accuracy | ≥ 0.85 |
| Latency p95 | ≤ 8 detik |
| Token Cost / query | ≤ $0.05 |
| Ablation Gap (Full vs Vector Only) | ≥ 10% F1 |

---

## 📚 Referensi

- [PRD Teknis](https://github.com/your-org/graphrag/blob/main/docs/prd.md) (internal)
- [Experiment Plan](docs/experiment_plan.md)
- [Workflow & Alur Kerja](docs/workflow.md)
- Buku Panduan Capstone Project UIR 2024

---

## 👥 Tim

| Peran | Tanggung Jawab |
|-------|----------------|
| **Backend Lead / GraphRAG Core** | Neo4j schema, ingestion pipeline, entity extraction, graph injection |
| **Retrieval & Query Engine** | Vector search, hybrid search, graph traversal, context assembly, LLM synthesis |
| **API / Frontend Viz / Eksperimen** | FastAPI endpoints, visualization (React Flow/D3), experiment framework, evaluasi |

---

## 📄 Lisensi

Academic use only — Capstone Project, Teknik Informatika UIR 2026/2027