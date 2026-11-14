# Academic & Research Paper GraphRAG - Quick Start

## Prerequisites

- Docker & Docker Compose v2+
- Python 3.11+ (for local development)
- Neo4j 5.18+ (via Docker)
- OpenRouter API key (for LLM/embeddings)

## 1. Environment Setup

```bash
# Clone and navigate
cd /home/guard/Documents/perkuliahan/sem\ 7/Cap

# Copy env template
cp .env.example .env

# Edit .env with your OpenRouter API key
nano .env
```

Required `.env` variables:
```env
OPENROUTER_API_KEY=your_key_here
NEO4J_PASSWORD=your_secure_password
```

## 2. Start Services

```bash
# Start Neo4j and backend
docker compose up -d

# Verify services
docker compose ps
# Should show: neo4j (healthy), backend (healthy)

# Check Neo4j browser
open http://localhost:7474
# Login: neo4j / your_password
```

## 3. Initialize Database Schema

```bash
# Run migrations (creates constraints, indexes, vector indexes)
docker compose exec backend python -m app.core.neo4j_migrate

# Or locally:
python -m app.core.neo4j_migrate
```

## 4. Ingest Papers

### Via API (Recommended)

```bash
# Single paper
curl -X POST "http://localhost:8000/api/v1/papers/ingest" \
  -F "file=@paper.pdf" \
  -F "title=Attention Is All You Need" \
  -F "year=2017" \
  -F "doi=10.48550/arXiv.1706.03762" \
  -F "venue=NeurIPS 2017" \
  -F "keywords=transformer,attention,NLP" \
  -F "chunking_strategy=fixed_512_50"

# Check status
curl "http://localhost:8000/api/v1/papers/ingest/status/{job_id}"
```

### Batch Ingestion

```bash
curl -X POST "http://localhost:8000/api/v1/papers/ingest/batch" \
  -F "files=@paper1.pdf" \
  -F "files=@paper2.pdf" \
  -F "chunking_strategy=fixed_512_50"
```

## 5. Query the GraphRAG

```bash
# Basic query
curl -X POST "http://localhost:8000/api/v1/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Apa metode yang digunakan dalam paper Attention Is All You Need?",
    "top_k": 5,
    "depth": 2
  }'

# Streaming query (SSE)
curl -N "http://localhost:8000/api/v1/query/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "Jelaskan arsitektur Transformer", "top_k": 5, "depth": 2}'
```

## 6. Visualize Graph

```bash
# Get subgraph for paper
curl "http://localhost:8000/api/v1/graph/visualize?paper_id=10.48550/arXiv.1706.03762&depth=2&max_nodes=50"

# Get graph stats
curl "http://localhost:8000/api/v1/graph/stats"

# Papers by concept
curl "http://localhost:8000/api/v1/graph/concept/Transformer/papers?limit=10"

# Papers by method
curl "http://localhost:8000/api/v1/graph/method/Self-Attention/papers?limit=10"
```

## 7. Run Experiments

```bash
# E1: Chunking strategies
python experiments/run_e1_chunking.py

# E2: Embedding models
python experiments/run_e2_embedding.py

# E3: Retrieval params
python experiments/run_e3_retrieval.py

# E4: Ablation study
python experiments/run_e4_ablation.py
```

## 8. Run Tests

```bash
# All tests
docker compose exec backend pytest tests/ -v

# Specific module
docker compose exec backend pytest tests/test_ingestion.py -v
docker compose exec backend pytest tests/test_retrieval.py -v

# With coverage
docker compose exec backend pytest tests/ -v --cov=app --cov-report=html
```

## 9. Development

### Local Development Setup

```bash
# Create venv
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Install dev dependencies
pip install ruff black mypy pytest pytest-asyncio httpx

# Run linters
ruff check backend/
black backend/
mypy backend/

# Run backend locally (needs Neo4j running)
uvicorn app.main:app --reload --port 8000
```

### Code Quality

```bash
# Format
ruff check --fix backend/
black backend/

# Type check
mypy backend/

# Pre-commit (install first: pip install pre-commit)
pre-commit install
pre-commit run --all-files
```

## 10. API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
Cap/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API routes (ingest, query, graph)
│   │   ├── core/                # Config, Neo4j driver, migrations
│   │   ├── ingestion/           # PDF parsing, chunking, entity extraction, graph writing
│   │   ├── retrieval/           # Vector search, graph traversal, context building, synthesis
│   │   ├── schemas/             # Pydantic models
│   │   └── main.py              # FastAPI entry point
│   ├── tests/                   # Unit & integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── experiments/
│   ├── config/                  # YAML configs for E1-E4
│   ├── data/                    # Gold standard queries
│   └── results/                 # Experiment outputs
├── docs/
│   └── quickstart.md
├── docker-compose.yml
└── README.md
```

## Chunking Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `fixed_512_50` | 512 chars, 50 overlap | General purpose, fast |
| `fixed_1024_100` | 1024 chars, 100 overlap | Longer context needed |
| `semantic_nomic` | Semantic boundaries | Better retrieval quality |
| `proposition_gpt4o_mini` | LLM-extracted propositions | Maximum precision |

## GraphRAG Pipeline

```
Query → Embedding → Vector Search (top-k papers)
            ↓
      Graph Traversal (depth hops from seeds)
            ↓
      Context Building (chunks + paths + entities)
            ↓
      LLM Synthesis (with citations)
            ↓
      Citation Validation
            ↓
      Final Answer
```

## Troubleshooting

### Neo4j Connection Failed
```bash
# Check logs
docker compose logs neo4j

# Verify credentials in .env match docker-compose.yml
```

### Ingestion Stuck
```bash
# Check job status
curl http://localhost:8000/api/v1/papers/ingest/status/{job_id}

# Check backend logs
docker compose logs backend
```

### Out of Memory
```bash
# Increase Docker memory limit
# Or reduce chunk_size in chunking strategy
```

## License

Academic use only - Capstone Project, Teknik Informatika UIR 2026/2027