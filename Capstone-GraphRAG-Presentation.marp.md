---
marp: true
theme: default
paginate: true
header: "Capstone GraphRAG — Proposal Presentasi"
footer: "Teknik Informatika UIR | 2026"
backgroundColor: #0d1117
color: #e6edf3
style: |
  :root {
    --accent: #58a6ff;
    --accent-dim: #388bfd;
    --muted: #8b949e;
    --success: #3fb950;
    --warning: #d29922;
    --danger: #f85149;
  }
  h1 { color: #58a6ff; font-size: 2.2rem; }
  h2 { color: #58a6ff; font-size: 1.6rem; border-bottom: 1px solid #30363d; padding-bottom: 0.3rem; }
  h3 { color: #e6edf3; font-size: 1.2rem; }
  table { font-size: 0.75rem; width: 100%; }
  th { background: #21262d; color: #58a6ff; }
  td { background: #161b22; }
  code { background: #21262d; color: #a5d6ff; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85rem; }
  pre { background: #161b22; border: 1px solid #30363d; }
  .columns { display: flex; gap: 1rem; }
  .col { flex: 1; }
  .small { font-size: 0.7rem; }
  .highlight { color: #58a6ff; font-weight: bold; }
  .success { color: #3fb950; }
  .warning { color: #d29922; }
  .danger { color: #f85149; }
  .muted { color: #8b949e; font-size: 0.85rem; }
  blockquote { border-left: 3px solid #58a6ff; color: #8b949e; }
  .footnote { font-size: 0.65rem; color: #8b949e; }
---

# Academic & Research Paper GraphRAG
## Sistem RAG Tingkat Lanjut dengan Knowledge Graph untuk Literatur Ilmiah

**Presentasi Proposal Capstone Project**
Teknik Informatika — Fakultas Teknik — Universitas Islam Riau

---

**Tim (3 Orang):**
- **Anggota 1 (Ketua)** — Backend Lead / GraphRAG Core
- **Anggota 2** — Retrieval & Query Engine
- **Anggota 3** — API / Frontend Viz / Eksperimen

**Dosen Pembimbing:** [Nama Dosen], S.Kom., M.Kom.
**Tanggal:** [Isi Tanggal Presentasi]

---

# Latar Belakang & Masalah

## Gap RAG Standar (Vector-Only)

| Masalah | Dampak |
|---|---|
| **Single-hop retrieval** — hanya chunk paling mirip semantik | Tidak bisa jawab query kompleks lintas dokumen |
| **Tidak ada relasi struktural** — sitasi, metode, dataset, penulis | Jawaban tidak *grounded* pada bukti terstruktur |
| **Hallucination risk** — LLM mengarang sitasi | Keandalan rendah untuk riset akademik |

> **Contoh Query Gagal:** *"Bandungkan performa LSTM vs Transformer pada dataset inflasi Indonesia"*
> - Butuh paper yang mengandung keduanya ATAU paper yang sitasi saling terkait
> - Vector search hanya mengembalikan paper terpisah, **tidak relasinya**

---

# Rumusan Masalah & Tujuan

## 3 Rumusan Masalah
1. Bagaimana merancang pipeline ingestion ekstrak entitas & relasi dari paper PDF otomatis?
2. Bagaimana mengimplementasikan hybrid retrieval (vector + graph) untuk query multi-hop?
3. Bagaimana mengevaluasi GraphRAG vs vector-only RAG pada query kompleks multi-hop?

## 3 Tujuan Penelitian
1. **Membangun** sistem GraphRAG end-to-end: PDF → Knowledge Graph Neo4j → Query API dengan grounding
2. **Mengimplementasikan** 4 eksperimen terukur: E1 Chunking, E2 Embedding, E3 Retrieval Depth, E4 Ablation
3. **Menghasilkan** prototype working: REST API + visualisasi graf interaktif untuk eksplorasi literatur

---

# Solusi: GraphRAG

## Arsitektur Inti

```
┌─────────────────────────────────────────────────────────────────┐
│                        GRAPHRAG ARCHITECTURE                      │
│                                                                   │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│   │  SEMANTIC    │     │  KNOWLEDGE   │     │   GROUNDED   │    │
│   │  VECTOR      │────▶│  GRAPH       │────▶│   SYNTHESIS  │    │
│   │  SEARCH      │     │  TRAVERSAL   │     │   + CITATION │    │
│   │  (Seed Nodes)│     │  (Multi-hop) │     │   VALIDATION │    │
│   └──────────────┘     └──────────────┘     └──────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Keunggulan vs RAG Standar

| Aspek | Vector-Only RAG | **GraphRAG (Proposed)** |
|---|---|---|
| Multi-hop query | ❌ Gagal | ✅ Native support |
| Citation grounding | ❌ Hallucination-prone | ✅ Validated against graph |
| Structural relations | ❌ Tidak tertangkap | ✅ Explicit (CITES, USES_METHOD, dll) |
| Explainability | Rendah | **Tinggi** (graph path visible) |

---

# Arsitektur Sistem — Container Diagram

![Container Diagram](Capstone-Drawings-Rapi.drawio.png#page=2)

**5 Container Utama:**
1. **Ingestion Pipeline** — PDF → Entity Extraction → Graph Injection
2. **Query/GraphRAG Pipeline** — Hybrid Search → Traversal → Synthesis
3. **Visualization Service** — React Flow / D3.js compatible JSON
4. **Embedding Service (Local)** — all-MiniLM-L6-v2 (384-d) via `guard-embedding.service` :8788
5. **FastAPI Backend** — Orchestrator, REST API, SSE streaming

**External Systems:**
- **Neo4j 5.18** — Graph DB + Vector Index (APOC)
- **Grobid** — PDF Parser (self-hosted)
- **OpenRouter Free LLM** — Nemotron-3.5-Lightning, Ling-3.2-Flash
- **Ollama Local** — Fallback embedding & LLM

---

# Data Model Neo4j

## Nodes (5 Types)

| Label | Properti Kunci |
|---|---|
| `Paper` | `id`, `title`, `abstract`, `year`, `doi`, `embedding` |
| `Author` | `id`, `name`, `institution` |
| `Concept` | `id`, `name`, `category` (task/domain/metric) |
| `Method` | `id`, `name`, `description` |
| `Dataset` | `id`, `name`, `domain` |

## Edges (5 Relationships)

```
(Author)-[:WROTE]->(Paper)-[:CITES]->(Paper)
    │                    │
    │                    ├──[:ADDRESSES_TOPIC]->(Concept)
    │                    ├──[:USES_METHOD]->(Method)
    │                    └──[:USES_DATASET]->(Dataset)
```

> Schema dirancang untuk query: *"Paper apa yang cite paper X dan pakai metode Y?"*

---

# Pipeline Ingestion (PDF → Knowledge Graph)

![Component Diagram](Capstone-Drawings-Rapi.drawio.png#page=3)

```
User Input (PDF/DOI)
       │
       ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   PARSING   │──▶│  CHUNKING   │──▶│ EXTRACTION  │──▶│  GRAPH      │
│ (Grobid/    │   │ (Fixed/     │   │ (LLM +      │   │  INJECTION  │
│  LlamaParse)│   │  Semantic/  │   │  Pydantic)  │   │ (Batch      │
└─────────────┘   │  Proposition)│   └─────────────┘   │  Cypher)    │
                  └─────────────┘                      └──────┬──────┘
                                                              │
                                              ┌───────────────┴───────────────┐
                                              ▼                               ▼
                                     ┌─────────────────┐            ┌─────────────────┐
                                     │ VECTOR INDEXING │            │   RESPONSE      │
                                     │ (Neo4j Vec Idx) │            │ {paper_id,      │
                                     └─────────────────┘            │  stats}         │
                                                                    └─────────────────┘
```

**Key Tech:**
- **Parsing:** Grobid self-hosted + LlamaParse fallback
- **Chunking:** 3 strategi (E1 variable) — Fixed 512/1024, Semantic, Proposition
- **Extraction:** Instructor + Pydantic v2 → structured output enforcement
- **Graph Injection:** Async batch Cypher via APOC, idempotent by `paper_id`
- **Embedding:** **Local** all-MiniLM-L6-v2 (384-d) — OpenRouter tidak punya free embedding

---

# Pipeline Query / GraphRAG Execution

![Sequence Diagram](Capstone-Drawings-Rapi.drawio.png#page=4)

```
User Query + Params (top_k, depth)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  VECTOR SEARCH (top-k seed papers)  │  GRAPH TRAVERSAL     │
│  (embedding similarity)             │  (depth hops:        │
└────────────────┬────────────────────┘  CITES, USES_METHOD, │
                 │                     USES_DATASET,         │
                 ▼                     ADDRESSES_TOPIC)      │
┌─────────────────────────────────────────────────────────────┐
│                    SUBGRAPH ASSEMBLY                         │
│         Nodes + Edges + Vector Chunks (context)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  CONTEXT BUILDER → PROMPT TEMPLATE → LLM SYNTHESIS          │
│  (Structured: {query, subgraph, chunks}) → Answer + Cites   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  CITATION VALIDATION  →  RESPONSE {answer, sources, graph_path}│
│  (Check citations exist in retrieved subgraph)              │
└─────────────────────────────────────────────────────────────┘
```

**Parameter:** `query` (required), `top_k` (default 5), `depth` (default 2), `stream` (SSE)

---

# Eksperimen & Evaluasi (E1–E4)

| Kode | Fokus | Variabel Independen | Metrik Utama |
|---|---|---|---|
| **E1** | Chunking Strategy | Fixed (512/1024) vs Semantic vs Proposition | Retrieval precision, latency |
| **E2** | Embedding Model | OpenAI 3-small (1536-d) vs nomic-embed (Ollama, 768-d) vs IndoBERT | NDCG@10, multi-lingual retrieval |
| **E3** | Retrieval Depth | top_k ∈ {3,5,10} × depth ∈ {1,2,3} | Grounding score, cite_acc, latency |
| **E4** | **Ablation: Graph vs Vector** | GraphRAG vs Vector-only vs Vector+Graph (no traversal) vs No citation validation | **Citation Accuracy, Grounding Score** |

## Dataset Uji
- **Corpus:** 50–100 paper (arXiv cs.CL, cs.CV, cs.LG, cs.AI + cross-domain)
- **QA Gold:** 30–40 multi-hop pairs (min 2 hops: method comparison, dataset usage, concept evolution, author collaboration)

## Evaluasi Otomatis
- **Grounding Score:** Proporsi klaim supported retrieved chunks (0–1)
- **Citation Accuracy:** Proporsi sitasi `[Paper ID]` valid di subgraph (0–1)
- **Statistical Test:** Paired t-test GraphRAG vs Vector-only (p < 0.05)

---

# Tech Stack & Infrastructure

| Layer | Teknologi | Catatan |
|---|---|---|
| **Language** | Python 3.11 | |
| **API Framework** | FastAPI | Async, Pydantic v2 |
| **Graph DB** | Neo4j 5.18 | Community + APOC + Vector Index |
| **Vector Store** | Neo4j Vector Index | **Integrated** (bukan terpisah) |
| **Extraction** | Instructor + Pydantic | Structured output |
| **Embedding** | **Local** all-MiniLM-L6-v2 (384-d) | `guard-embedding.service` systemd :8788 |
| **LLM** | OpenRouter **Free Only** | `nemotron-3.5-lightning:free`, `ling-3.2-flash:free` |
| **PDF Parser** | Grobid (self-hosted) | + defusedxml fallback |
| **Frontend Viz** | Vue 3 + React Flow / D3.js | Optional, terpisah repo |
| **Container** | Docker Compose | Neo4j + Backend |
| **Testing** | pytest, httpx | Unit + integration |
| **Code Quality** | ruff, black, mypy | CI-ready |

> **Zero-cost inference:** LLM enforce `:free` suffix, embedding lokal, Neo4j integrated vector index

---

# Timeline 10 Minggu & Progress Saat Ini

| Minggu | Tanggal | Fase | Status |
|---|---|---|---|
| **1** | 14–20 Nov | Perencanaan: Proposal, Env Setup, Diagram | ✅ **SELESAI** |
| **2** | 21–27 Nov | Ingestion Pipeline: Parsing, Extraction, Indexing | 🔄 **IN PROGRESS** |
| **3** | 28 Nov–4 Des | Retrieval & Query: Hybrid Search, Traversal, API | ⏳ **PARTIAL** |
| **4** | 5–11 Des | API Lengkap, Synthesis, Grounding, Visualisasi | ⏳ |
| **5** | 12–18 Des | Eksperimen E1–E2: Chunking & Embedding | ⏳ |
| **6** | 19–25 Des | Eksperimen E3–E4: Retrieval Depth & Ablation | ⏳ |
| **7** | 26 Des–1 Jan | Analisis, Optimasi, Perbaikan Pipeline | ⏳ |
| **8** | 2–8 Jan | Dokumentasi Laporan & Slide Final | ⏳ |
| **9** | 9–15 Jan | Simulasi Presentasi, Finalisasi Repo | ⏳ |
| **10** | 16–19 Jan | **DEADLINE: Pengumpulan & Presentasi** | ⏳ |

## Progress Minggu 1–3 (Realita)
- ✅ Proposal approved, konsultasi dosen selesai
- ✅ Docker Compose: Neo4j + Backend running
- ✅ Neo4j schema migration (constraints, indexes, vector index 384-d)
- ✅ Project structure backend lengkap (FastAPI, Pydantic schemas)
- ✅ Diagram arsitektur 4 halaman (.drawio) selesai
- 🔄 **Corpus 4 paper GraphRAG** ter-ingest: 313 chunks, embeddings 384-d (MiniLM lokal)
- 🔄 Retrieval API terverifikasi: vector search + graph traversal + CITES edges functional
- ⏳ Eksperimen E1–E4 menunggu corpus scale-up (target 50+ paper)

---

# Pembagian Tugas & Risk Management

## Peran Tim (3 Orang)

| Anggota | Peran | Fokus Minggu 1–5 |
|---|---|---|
| **Anggota 1 (Ketua)** | Backend Lead / GraphRAG Core | Neo4j schema, ingestion pipeline, entity extraction, graph injection |
| **Anggota 2** | Retrieval & Query Engine | Vector search, hybrid search, graph traversal, context assembly, LLM synthesis |
| **Anggota 3** | API / Frontend Viz / Eksperimen | FastAPI endpoints, React Flow/D3 viz, experiment framework E1–E4 |

> **Kolaborasi:** Semua kontribusi proposal, dokumentasi, presentasi, code review.

## Risk Management

| Risiko | Probabilitas | Mitigasi |
|---|---|---|
| LLM API quota (OpenRouter) | **Tinggi** | Fallback Ollama lokal, batch processing, budget planning |
| Grobid/LlamaParse setup | Sedang | Dual option, test early, Docker image pinned |
| Neo4j Vector Index compat | Rendah | Test versi di Docker Compose sebelum commit |
| Tim beban kerja tidak seimbang | Sedang | Weekly sync 15min, GitHub Projects/Kanban, pair programming |
| Corpus tidak cukup multi-hop | Sedang | Target 50+ paper, citation graph builder, arXiv bulk download |

---

# Deliverables & Kriteria Sukses (KPI)

## Deliverables Akhir
| Deliverable | Format |
|---|---|
| Laporan Capstone | .docx + .pdf (MAKALAH UIR template) |
| Slide Presentasi | .pdf / .pptx (deck ini) |
| Demo Video | .mp4 (3–5 menit) |
| Source Code | GitHub Repo (Private) + README |
| Diagram Arsitektur | .drawio + .png (4 halaman) |

## KPI Terukur

| KPI | Target | Verifikasi |
|---|---|---|
| Ingestion Throughput | ≥ 5 paper/menit | Benchmark script 50 paper |
| Query Latency (P95) | < 10 detik | `top_k=5, depth=2` pada 50 paper |
| **Citation Accuracy (E4)** | **> 0.60** | Evaluasi otomatis 30–40 QA gold |
| **Grounding Score (E4)** | **> 0.75** | Evaluasi otomatis 30–40 QA gold |
| GraphRAG > Vector-Only | Signifikan (p < 0.05) | Paired t-test cite_acc & grounding |
| Code Quality | mypy/ruff clean, pytest ≥ 70% | CI pipeline pass |

---

# Kesimpulan

## 3 Poin Kunci

1. **Novelitas:** GraphRAG untuk literatur ilmiah cross-domain dengan knowledge graph eksplisit (CITES, USES_METHOD, USES_DATASET, ADDRESSES_TOPIC, WROTE) — bukan sekadar vector search

2. **Rigorasitas Evaluasi:** 4 eksperimen terukur (E1–E4) dengan metrik otomatis (grounding, citation accuracy) + statistical significance testing pada corpus 50+ paper & 30–40 multi-hop QA

3. **Production-Ready Stack:** FastAPI + Neo4j (graph + vector terintegrasi) + Local Embedding + Free LLM via OpenRouter — **zero cost inference**, deployable di laptop mahasiswa

---

## Call to Action

> **"Kami meminta persetujuan untuk melanjutkan ke tahap implementasi penuh (Minggu 4–10) dengan target demo working pada Minggu 7 dan laporan final Minggu 10."**

---

# Terima Kasih

## Siap Menjawab Pertanyaan

**Backup Slides Tersedia:**
- Detail schema Pydantic entity extraction
- Contoh output query GraphRAG (answer + sources + graph_path)
- Arsitektur deployment (Docker Compose + systemd)
- Rincian QA gold standard examples

---

# Appendix: Teknis Pembuatan Slide

## Render ke PDF/PPTX (Marp CLI)
```bash
npm install -g @marp-team/marp-cli
marp Capstone-GraphRAG-Presentation.marp.md --pdf --allow-local-files
marp Capstone-GraphRAG-Presentation.marp.md --pptx --allow-local-files
```

## Diagram Draw.io Export
```bash
# Buka draw.io desktop → File → Export → PNG
# Pilih halaman 1-4 → Scale 2x (1920x1080)
# Simpan ke folder slide assets/
```

## Generator Laporan (Konsistensi Format UIR)
```bash
cd /home/guard/Documents/perkuliahan/sem\ 7/Cap/
python make_makalah_capstone.py  # .docx dari Template.docx
soffice --headless --convert-to pdf Proposal-Capstone-GraphRAG.docx
```

## Checklist Persiapan
- [ ] Slide deck final (review typography, contrast)
- [ ] Diagram PNG exported (4 halaman)
- [ ] Speaker notes printed / di device terpisah
- [ ] Demo video recorded (3–5 menit)
- [ ] Backup slides siap
- [ ] Repo GitHub updated (tag `proposal-v1`)
- [ ] Laptop test: HDMI, audio, internet
- [ ] Print 1-pager ringkasan untuk dosen