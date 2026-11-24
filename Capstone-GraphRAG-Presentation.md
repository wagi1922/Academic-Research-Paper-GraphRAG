---
title: "Capstone GraphRAG — Presentasi Proposal"
tags: [capstone, graphrag, presentation, proposal]
updated: 2026-11-23
---

# Capstone GraphRAG — Slide Deck Proposal

**Judul:** Academic & Research Paper GraphRAG: Sistem RAG Tingkat Lanjut dengan Knowledge Graph untuk Literatur Ilmiah
**Tim:** 3 Mahasiswa Teknik Informatika UIR
**Dosen Pembimbing:** [Nama Dosen]
**Tanggal Presentasi:** [Isi Tanggal]
**Durasi:** 15–20 menit presentasi + 10 menit Q&A

---

## Struktur Presentasi (14–16 Slide)

| No | Slide | Waktu | Catatan |
|---|---|---|---|
| 1 | **Cover / Title Slide** | 30s | Judul, tim, dosen, tanggal |
| 2 | **Latar Belakang & Masalah** | 1.5m | Gap RAG standar vs kebutuhan multi-hop |
| 3 | **Rumusan Masalah & Tujuan** | 1m | 3 rumusan, 3 tujuan |
| 4 | **Solusi: GraphRAG** | 1.5m | Konsep gabungan Vector + Graph |
| 5 | **Arsitektur Sistem (Container Diagram)** | 2m | Diagram draw.io Hal 2 |
| 6 | **Data Model Neo4j** | 1.5m | Nodes & Edges |
| 7 | **Pipeline Ingestion (PDF → Knowledge Graph)** | 2m | Diagram draw.io Hal 3 (Component) |
| 8 | **Pipeline Query / GraphRAG Execution** | 2m | Diagram draw.io Hal 4 (Sequence) |
| 9 | **Eksperimen & Evaluasi (E1–E4)** | 2m | Tabel eksperimen + metrik |
| 10 | **Tech Stack & Infrastructure** | 1m | Tabel stack lengkap |
| 11 | **Timeline 10 Minggu & Progress Saat Ini** | 1.5m | Gantt chart + status Minggu 1–3 |
| 12 | **Pembagian Tugas Tim & Risk Management** | 1m | Tabel peran + risiko |
| 13 | **Deliverables & Kriteria Sukses** | 1m | Output akhir + KPI |
| 14 | **Kesimpulan & Pertanyaan** | 30s | Ringkasan 3 poin |

---

## Slide 1: Cover / Title Slide

**Konten Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│     Academic & Research Paper GraphRAG                      │
│     Sistem RAG Tingkat Lanjut dengan Knowledge Graph        │
│     untuk Literatur Ilmiah                                  │
│                                                             │
│     ─────────────────────────────────────────               │
│                                                             │
│     Presentasi Proposal Capstone Project                    │
│     Teknik Informatika — Fakultas Teknik — UIR              │
│                                                             │
│     Tim:                                                    │
│     • [Nama Anggota 1] (NIM) — Backend Lead / GraphRAG Core │
│     • [Nama Anggota 2] (NIM) — Retrieval & Query Engine     │
│     • [Nama Anggota 3] (NIM) — API / Frontend Viz / Eksperimen │
│                                                             │
│     Dosen Pembimbing: [Nama Dosen], S.Kom., M.Kom.          │
│                                                             │
│     [Tanggal Presentasi]                                    │
└─────────────────────────────────────────────────────────────┘
```

**Speaker Notes:**
- Sapa dosen penguji dan hadirin
- Perkenalkan tim singkat (nama + peran)
- Sebutkan ini proposal capstone project semester 7, durasi 10 minggu

---

## Slide 2: Latar Belakang & Masalah

**Konten Visual:**

| Masalah RAG Standar (Vector-Only) | Dampak |
|---|---|
| **Single-hop retrieval** — hanya mencari chunk paling mirip secara semantik | Tidak bisa menjawab query kompleks lintas dokumen |
| **Tidak ada relasi struktural** — sitasi, metode bersama, dataset sama, penulis sama | Jawaban tidak *grounded* pada bukti terstruktur |
| **Hallucination risk** — LLM mengarang sitasi yang tidak ada di corpus | Keandalan rendah untuk riset akademik |

**Contoh Query yang Gagal di Vector-Only RAG:**
> *"Bandungkan performa LSTM vs Transformer pada dataset inflasi Indonesia"*
> - Butuh temukan paper yang **mengandung keduanya** ATAU paper yang **sitasi saling terkait**
> - Vector search hanya mengembalikan paper terpisah, tidak relasinya

**Speaker Notes:**
- RAG standar (vector-only) sudah matang untuk Q&A sederhana
- Gap muncul saat query butuh *multi-hop reasoning*: bandingkan metode, telusui evolusi konsep, cari kolaborasi penulis
- GraphRAG hadir untuk mengisi gap ini dengan knowledge graph

---

## Slide 3: Rumusan Masalah & Tujuan

**Rumusan Masalah:**
1. Bagaimana merancang pipeline ingestion yang mengekstrak entitas (Author, Concept, Method, Dataset) dan relasi (CITES, USES_METHOD, dll) dari paper akademik PDF secara otomatis?
2. Bagaimana mengimplementasikan hybrid retrieval yang menggabungkan vector search dan graph traversal untuk menjawab query multi-hop?
3. Bagaimana mengevaluasi performa GraphRAG dibandingkan vector-only RAG pada query kompleks multi-hop?

**Tujuan Penelitian:**
1. **Membangun** sistem GraphRAG end-to-end: ingestion PDF → knowledge graph Neo4j → query API dengan grounding
2. **Mengimplementasikan** 4 eksperimen terukur: chunking strategy (E1), embedding model (E2), retrieval depth (E3), ablation graph vs vector (E4)
3. **Menghasilkan** prototype working demo: REST API + visualisasi graf interaktif untuk eksplorasi literatur

**Speaker Notes:**
- 3 rumusan masalah → 3 tujuan yang sejalan
- Fokus pada *working prototype* bukan sekadar teori
- Eksperimen E1–E4 adalah diferensiasi utama vs proyek RAG biasa

---

## Slide 4: Solusi — GraphRAG

**Konsep Inti:**

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
│        │                     │                     │              │
│        ▼                     ▼                     ▼              │
│   Top-k papers          1–2 hops:           Answer +            │
│   by embedding          CITES,                valid citations   │
│   similarity            USES_METHOD,          from graph paths  │
│                         USES_DATASET,         (no hallucination)│
│                         ADDRESSES_TOPIC                        │
└─────────────────────────────────────────────────────────────────┘
```

**Keunggulan vs RAG Standar:**
| Aspek | Vector-Only RAG | GraphRAG (Proposed) |
|---|---|---|
| Multi-hop query | ❌ Gagal | ✅ Native support |
| Citation grounding | ❌ Hallucination-prone | ✅ Validated against graph |
| Structural relations | ❌ Tidak tertangkap | ✅ Explicit (CITES, USES_METHOD, dll) |
| Explainability | Rendah | Tinggi (graph path visible) |

**Speaker Notes:**
- GraphRAG = Vector Search + Graph Traversal + Grounded Synthesis
- Seed nodes dari vector search, lalu expand via graph edges (1–2 hops)
- LLM synthesize dengan sitasi yang divalidasi against subgraph
- Ini yang membedakan dari RAG biasa

---

## Slide 5: Arsitektur Sistem — Container Diagram

**Rujuk Diagram:** `Capstone-Drawings-Rapi.drawio` → **Halaman 2: Container Diagram**

**Konten Visual (Deskripsi untuk Draw.io):**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM CONTEXT — CONTAINER DIAGRAM                    │
│                                                                              │
│  ┌─────────────┐                                                             │
│  │  Researcher │  (Actor)                                                    │
│  │  / Student  │                                                             │
│  └──────┬──────┘                                                             │
│         │ HTTPS/REST                                                         │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    GRAPHRAG SYSTEM (FastAPI Backend)                  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ Ingestion   │  │   Query /   │  │ Visualization│  │  Embedding  │  │    │
│  │  │ Pipeline    │  │  GraphRAG   │  │   Service   │  │  Service    │  │    │
│  │  │  (Service)  │  │  Pipeline   │  │  (React Flow│  │  (Local     │  │    │
│  │  └──────┬──────┘  └──────┬──────┘  │   / D3.js)  │  │   MiniLM)   │  │    │
│  └─────────┼────────────────┼─────────┴──────┬────────┴──────┬───────┘    │
│           │                │                │               │             │
│           ▼                ▼                ▼               ▼             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │    Neo4j     │ │   Grobid     │ │   OpenRouter │ │  Local LLM   │    │
│  │  (Graph DB + │ │  (PDF Parser)│ │  (Free LLM:  │ │  (Ollama     │    │
│  │   Vector Idx)│ │              │ │   Nemotron,  │ │   Fallback)  │    │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                                              │
│  Legend: ◄── Container boundary    ▄▄▄ External system    ███ Database      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Speaker Notes:**
- 5 container utama: Ingestion, Query/GraphRAG, Visualization, Embedding Service (lokal), FastAPI sebagai orchestrator
- Neo4j dual role: graph DB + vector index terintegrasi
- Embedding service lokal (all-MiniLM-L6-v2) karena OpenRouter tidak punya embedding gratis
- LLM via OpenRouter free tier dengan fallback Ollama lokal

---

## Slide 6: Data Model Neo4j

**Nodes:**
| Label | Properti Kunci | Deskripsi |
|---|---|---|
| `Paper` | `id`, `title`, `abstract`, `year`, `doi`, `embedding` | Unit dokumen utama |
| `Author` | `id`, `name`, `institution` | Penulis paper |
| `Concept` | `id`, `name`, `category` | Topik/domain/metrik (task, domain, metric) |
| `Method` | `id`, `name`, `description` | Metode/algoritma (LSTM, Transformer, BERT, dll) |
| `Dataset` | `id`, `name`, `domain` | Dataset yang digunakan (GLUE, SQuAD, data inflasi, dll) |

**Edges (Relationships):**
| Edge | Source → Target | Arti |
|---|---|---|
| `WROTE` | `Author` → `Paper` | Penulisan |
| `CITES` | `Paper` → `Paper` | Sitasi antar paper |
| `ADDRESSES_TOPIC` | `Paper` → `Concept` | Paper membahas konsep |
| `USES_METHOD` | `Paper` → `Method` | Paper menggunakan metode |
| `USES_DATASET` | `Paper` → `Dataset` | Paper menggunakan dataset |

**Visualisasi Skema (untuk slide):**
```
(Author)-[:WROTE]->(Paper)-[:CITES]->(Paper)
    │                    │
    │                    ├──[:ADDRESSES_TOPIC]->(Concept)
    │                    ├──[:USES_METHOD]->(Method)
    │                    └──[:USES_DATASET]->(Dataset)
```

**Speaker Notes:**
- 5 node types, 5 relationship types — cukup ekspresif untuk literatur ilmiah
- Embedding disimpan di node `Paper` (abstract) dan `Chunk` (paragraf)
- Schema dirancang untuk mendukung query: "paper apa yang cite paper X dan pakai metode Y?"

---

## Slide 7: Pipeline Ingestion (PDF → Knowledge Graph)

**Rujuk Diagram:** `Capstone-Drawings-Rapi.drawio` → **Halaman 3: Component Diagram**

**Flow Ingestion:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE                                     │
│                                                                              │
│  User Input                                                                  │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   INPUT     │───▶│   PARSING   │───▶│  CHUNKING   │───▶│ EXTRACTION  │  │
│  │  (PDF/DOI)  │    │ (Grobid/    │    │ (Fixed /    │    │ (LLM +      │  │
│  └─────────────┘    │  LlamaParse)│    │  Semantic /  │    │  Pydantic)  │  │
│                     └─────────────┘    │  Proposition)│    └──────┬──────┘  │
│                                         └─────────────┘           │         │
│                                                                   ▼         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  RESPONSE   │◀───│  VECTOR     │◀───│  GRAPH      │◀───│  ENTITIES   │  │
│  │ {paper_id,  │    │  INDEXING   │    │  INJECTION  │    │  & RELATIONS│  │
│  │  stats}     │    │ (Neo4j Vec  │    │ (Batch      │    │  (Author,   │  │
│  └─────────────┘    │  Index)     │    │  Cypher)    │    │   Concept,  │  │
│                     └─────────────┘    └─────────────┘    │   Method,   │  │
│                                                          │   Dataset,  │  │
│                                                          │   CITES,    │  │
│                                                          │   USES_*)   │  │
│                                                          └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Implementation Details:**
- **Parsing:** Grobid self-hosted (primary) + LlamaParse fallback
- **Chunking:** 3 strategi — Fixed (512/1024 token), Semantic, Proposition-based (E1)
- **Extraction:** Instructor + Pydantic v2 → structured output enforcement
- **Graph Injection:** Async batch Cypher via APOC, idempotent by paper_id
- **Embedding:** Local all-MiniLM-L6-v2 (384-d) via `guard-embedding.service` :8788

**Speaker Notes:**
- Pipeline modular: setiap step bisa di-swap (parser, chunker, embedder)
- Pydantic schema memastikan LLM output valid JSON sesuai schema Neo4j
- Batch Cypher + APOC untuk performa injection massal
- Embedding lokal menghindari dependency OpenRouter (tidak ada free embedding)

---

## Slide 8: Pipeline Query / GraphRAG Execution

**Rujuk Diagram:** `Capstone-Drawings-Rapi.drawio` → **Halaman 4: Sequence Diagram**

**Flow Query:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GRAPHRAG QUERY PIPELINE                                 │
│                                                                              │
│  User Query + Params (top_k, depth)                                          │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────┐                                                         │
│  │ INTENT & ENTITY │  (Placeholder: vector search sebagai seed selection)   │
│  │ EXTRACTION      │                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                                │
│  │ VECTOR SEARCH   │     │ GRAPH TRAVERSAL │                                │
│  │ (top-k seed     │     │ (depth hops     │                                │
│  │  papers by      │     │  from seeds:    │                                │
│  │  embedding)     │     │  CITES,         │                                │
│  └────────┬────────┘     │  USES_METHOD,   │                                │
│           │              │  USES_DATASET,  │                                │
│           │              │  ADDRESSES_     │                                │
│           ▼              │  TOPIC)         │                                │
│  ┌─────────────────────────────────────────┐                               │
│  │        SUBGRAPH ASSEMBLY                 │                               │
│  │  Nodes + Edges + Vector Chunks (context) │                               │
│  └────────────────────┬────────────────────┘                               │
│                       │                                                    │
│                       ▼                                                    │
│  ┌─────────────────────────────────────────┐                               │
│  │      CONTEXT BUILDER → PROMPT TEMPLATE  │                               │
│  │  Structured: {query, subgraph, chunks}  │                               │
│  └────────────────────┬────────────────────┘                               │
│                       │                                                    │
│                       ▼                                                    │
│  ┌─────────────────┐     ┌─────────────────┐                              │
│  │ LLM SYNTHESIS   │────▶│ CITATION        │                              │
│  │ (Answer +       │     │ VALIDATION      │                              │
│  │  paper_id cite) │     │ (Check sources  │                              │
│  └─────────────────┘     │  in subgraph)   │                              │
│                          └────────┬────────┘                              │
│                                   │                                       │
│                                   ▼                                       │
│                    ┌─────────────────────────┐                            │
│                    │ RESPONSE: {answer,      │                            │
│                    │  sources: [...],        │                            │
│                    │  graph_path: [...]}     │                            │
│                    └─────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Parameter Query:**
| Parameter | Default | Deskripsi |
|---|---|---|
| `query` | required | Natural language question |
| `top_k` | 5 | Jumlah seed papers dari vector search |
| `depth` | 2 | Hops graph traversal (1–3) |
| `stream` | false | Server-Sent Events untuk UX |

**Speaker Notes:**
- Hybrid search: vector search dulu untuk seed, lalu graph traversal untuk konteks kaya
- Depth 1–2 sudah cukup untuk multi-hop (cite → cite, method → paper yang pakai method)
- Citation validation mencegah hallucination: LLM wajib cite paper_id yang ada di subgraph
- Streaming response (SSE) untuk UX real-time

---

## Slide 9: Eksperimen & Evaluasi (E1–E4)

**Desain Eksperimen:**

| Kode | Fokus | Variabel Independen | Metrik Evaluasi | Baseline |
|---|---|---|---|---|
| **E1** | Chunking Strategy | Fixed (512/1024) vs Semantic vs Proposition | Retrieval precision, chunk coherence, latency | Fixed 512 |
| **E2** | Embedding Model | text-embedding-3-small (1536-d) vs nomic-embed-text (Ollama, 768-d) vs IndoBERT | Semantic search quality (NDCG@10), multi-lingual retrieval | OpenAI 3-small |
| **E3** | Retrieval Depth | top_k ∈ {3,5,10} × depth ∈ {1,2,3} | Grounding score, citation accuracy, latency, graph path count | top_k=5, depth=2 |
| **E4** | Ablation: Graph vs Vector | GraphRAG (full) vs Vector-only vs Vector+Graph (no traversal) vs No citation validation | **Primary:** Citation Accuracy, Grounding Score **Secondary:** Latency, Answer completeness | GraphRAG full |

**Dataset Uji:**
- **Corpus:** 50–100 paper akademik (arXiv cs.CL, cs.CV, cs.LG, cs.AI + cross-domain)
- **QA Gold Standard:** 30–40 multi-hop QA pairs (min 2 hops)
  - Method comparison, Dataset usage, Concept evolution, Author collaboration

**Evaluasi Otomatis:**
- **Grounding Score:** Proporsi klaim yang supported oleh retrieved chunks (0–1)
- **Citation Accuracy:** Proporsi sitasi `[Paper ID]` yang valid di subgraph (0–1)
- **Latency:** End-to-end query time (target < 10s)

**Speaker Notes:**
- 4 eksperimen sistematis, bukan ad-hoc
- E4 adalah yang paling kritis: buktikan GraphRAG > Vector-only pada multi-hop
- Metrik otomatis (grounding, cite_acc) + manual review untuk kualitas jawaban
- Corpus 50+ paper, QA 30–40 pairs — cukup untuk statistical significance

---

## Slide 10: Tech Stack & Infrastructure

| Layer | Teknologi | Versi / Catatan |
|---|---|---|
| **Language** | Python | 3.11 |
| **API Framework** | FastAPI | Async, Pydantic v2 validation |
| **Graph DB** | Neo4j | 5.18 Community + APOC + Vector Index Plugin |
| **Vector Store** | Neo4j Vector Index | Integrated (bukan terpisah) |
| **Extraction** | Instructor + Pydantic | Structured output enforcement |
| **Embedding** | **Local** all-MiniLM-L6-v2 (384-d) | `guard-embedding.service` systemd, OpenAI-compatible :8788 |
| **LLM** | OpenRouter Free Only | `nvidia/nemotron-3.5-lightning:free` (extraction), `inclusionai/ling-3.2-flash:free` (synthesis) |
| **PDF Parser** | Grobid (self-hosted) + defusedxml | Primary + fallback |
| **Frontend Viz** | Vue 3 + React Flow / D3.js | Optional, terpisah repo |
| **Container** | Docker Compose | Neo4j, Backend |
| **Testing** | pytest, httpx (async) | Unit + integration |
| **Code Quality** | ruff, black, mypy | CI-ready |

**Infrastructure:**
- **Host:** Lenovo ThinkPad X13 Gen 1 (Ryzen 5 PRO 4650U, 16 GB RAM, NVMe 238 GB)
- **OS:** Arch Linux (Hyprland/i3)
- **Deployment:** Docker Compose (dev), systemd services untuk embedding service
- **Version Control:** Git + GitHub (private repo), GitFlow ringan

**Speaker Notes:**
- Stack modern, production-ready, tapi gratis/low-cost untuk mahasiswa
- Embedding lokal krusial: OpenRouter tidak punya free embedding model
- LLM enforce `:free` suffix di config & code — zero cost inference
- Neo4j vector index terintegrasi: tidak butuh Pinecone/Weaviate terpisah

---

## Slide 11: Timeline 10 Minggu & Progress Saat Ini

**Gantt Chart (10 Minggu):**

| Minggu | Tanggal | Fase | Kegiatan Utama | Status |
|---|---|---|---|---|
| **1** | 14–20 Nov | Perencanaan | Proposal final, setup env (Neo4j, FastAPI, repo Git), diagram arsitektur | ✅ **SELESAI** |
| **2** | 21–27 Nov | Desain & Ingestion | Ingestion pipeline: PDF parsing, entity extraction, graph injection, vector indexing | 🔄 **IN PROGRESS** |
| **3** | 28 Nov–4 Des | Desain & Retrieval | Hybrid search, graph traversal, context assembly, query API | ⏳ **PARTIAL** |
| **4** | 5–11 Des | Implementasi | API endpoints lengkap, LLM synthesis & grounding, visualisasi graf | ⏳ |
| **5** | 12–18 Des | Implementasi | Eksperimen E1–E2: Chunking & Embedding comparison | ⏳ |
| **6** | 19–25 Des | Implementasi | Eksperimen E3–E4: Retrieval depth & Ablation study | ⏳ |
| **7** | 26 Des–1 Jan | Pengujian | Analisis hasil, perbaikan pipeline, optimasi | ⏳ |
| **8** | 2–8 Jan | Dokumentasi | Laporan akhir (MAKALAH UIR), slide presentasi final | ⏳ |
| **9** | 9–15 Jan | Dokumentasi | Simulasi presentasi, finalisasi repo | ⏳ |
| **10** | 16–19 Jan | **DEADLINE** | Pengumpulan laporak & presentasi capstone | ⏳ |

**Progress Minggu 1–3 (Saat Ini):**
- ✅ Proposal approved, konsultasi dosen selesai
- ✅ Docker Compose: Neo4j + Backend running
- ✅ Neo4j schema migration (constraints, indexes, vector index)
- ✅ Project structure backend lengkap (FastAPI, Pydantic schemas)
- ✅ Diagram arsitektur 4 halaman (.drawio) selesai
- 🔄 Ingestion: 4 paper GraphRAG corpus ter-ingest, 313 chunks, 384-d embeddings (MiniLM lokal)
- 🔄 Retrieval API terverifikasi: vector search + graph traversal + CITES edges functional
- ⏳ Eksperimen E1–E4: menunggu corpus scale-up (target 50+ paper)

**Speaker Notes:**
- Minggu 1–3 sudah berjalan, progress solid
- Blocker utama: LLM quota OpenRouter (reset harian ~07:00 WIB) memperlambat entity extraction
- Solusi: batch processing + lokal embedding sudah live
- Target Minggu 4: query pipeline end-to-end working + visualisasi

---

## Slide 12: Pembagian Tugas Tim & Risk Management

**Pembagian Peran (3 Orang):**

| Anggota | Peran Utama | Tanggung Jawab Minggu 1–5 |
|---|---|---|
| **Anggota 1 (Ketua)** | Backend Lead / GraphRAG Core | Neo4j schema, ingestion pipeline, entity extraction, graph injection, Cypher optimization |
| **Anggota 2** | Retrieval & Query Engine | Vector search, hybrid search, graph traversal (APOC), context assembly, LLM synthesis, grounding validation |
| **Anggota 3** | API / Frontend Viz / Eksperimen | FastAPI endpoints, React Flow/D3 visualisasi, experiment framework (E1–E4), evaluasi metrik |

> **Kolaborasi:** Semua anggota kontribusi pada proposal, dokumentasi, presentasi, code review.

**Risk Management:**

| Risiko | Probabilitas | Dampak | Mitigasi |
|---|---|---|---|
| LLM API quota / cost (OpenRouter) | Tinggi | Gagal eksperimen E1–E4 | Fallback Ollama lokal (nomic-embed-text, Llama-3.1-8B), budget planning, batch processing |
| Grobid/LlamaParse setup kompleks | Sedang | Delay ingestion pipeline | Siapkan kedua opsi, test early, Docker image pinned |
| Neo4j Vector Index kompatibilitas | Rendah | Gagal vector search | Test versi Neo4j + plugin di Docker Compose sebelum commit |
| Tim tidak seimbang beban kerja | Sedang | Burnout / kualitas turun | Weekly sync 15 menit, GitHub Projects/Kanban, pair programming untuk critical path |
| Corpus tidak cukup untuk multi-hop QA | Sedang | E4 tidak signifikan | Target 50+ paper, citation graph builder, fallback ke arXiv bulk download |

**Speaker Notes:**
- Pembagian peran jelas tapi ada overlap pada kolaborasi
- Risk management realistis: quota LLM adalah risiko #1, sudah ada mitigasi konkret
- Weekly sync singkat (15 menit) — standup style, tidak meeting panjang

---

## Slide 13: Deliverables & Kriteria Sukses

**Deliverables Akhir:**

| Deliverable | Format | Deskripsi |
|---|---|---|
| **Laporan Capstone** | .docx + .pdf | Format MAKALAH UIR (Template.docx → `make_makalah_capstone.py` → `soffice --headless --convert-to pdf`) |
| **Slide Presentasi** | .pdf / .pptx | Deck 14–16 slide (file ini) |
| **Demo Video** | .mp4 (3–5 menit) | Walkthrough: ingest paper → query multi-hop → visualisasi graf |
| **Source Code** | GitHub Repo (Private) | Backend + experiment scripts + docs, README lengkap |
| **Diagram Arsitektur** | .drawio + .png | 4 halaman: Context, Container, Component, Sequence |

**Kriteria Sukses (KPI):**

| KPI | Target | Cara Verifikasi |
|---|---|---|
| **Ingestion Throughput** | ≥ 5 paper/menit | Benchmark script pada 50 paper |
| **Query Latency (P95)** | < 10 detik | `top_k=5, depth=2` pada 50 paper corpus |
| **Citation Accuracy (E4)** | > 0.60 | Evaluasi otomatis pada 30–40 QA gold |
| **Grounding Score (E4)** | > 0.75 | Evaluasi otomatis pada 30–40 QA gold |
| **GraphRAG > Vector-Only** | Signifikan (p < 0.05) | Paired t-test pada citation accuracy & grounding |
| **Code Quality** | mypy clean, ruff clean, pytest ≥ 70% coverage | CI pipeline pass |
| **Dokumentasi Lengkap** | 100% | Checklist: README, API spec, experiment log, architecture docs |

**Speaker Notes:**
- Deliverables concrete & verifiable — bukan vague "sistem berjalan"
- KPI terukur otomatis via script evaluasi (bukan manual feel)
- Statistical significance test (paired t-test) untuk claim GraphRAG > Vector-only
- Code quality gates di CI: mypy, ruff, pytest coverage

---

## Slide 14: Kesimpulan & Pertanyaan

**Ringkasan 3 Poin Kunci:**

1. **Novelitas:** GraphRAG untuk literatur ilmiah cross-domain dengan knowledge graph eksplisit (CITES, USES_METHOD, USES_DATASET, ADDRESSES_TOPIC, WROTE) — bukan sekadar vector search
2. **Rigorasitas Evaluasi:** 4 eksperimen terukur (E1–E4) dengan metrik otomatis (grounding, citation accuracy) + statistical significance testing pada corpus 50+ paper & 30–40 multi-hop QA
3. **Production-Ready Stack:** FastAPI + Neo4j (graph + vector terintegrasi) + Local Embedding + Free LLM via OpenRouter — zero cost inference, deployable di laptop mahasiswa

**Call to Action:**
> "Kami meminta persetujuan untuk melanjutkan ke tahap implementasi penuh (Minggu 4–10) dengan target demo working pada Minggu 7 dan laporan final Minggu 10."

**Backup Slides (Jika Diperlukan):**
- Slide tambahan: Detail schema Pydantic extraction
- Slide tambahan: Contoh output query GraphRAG (answer + sources + graph_path)
- Slide tambahan: Arsitektur deployment (Docker Compose + systemd)
- Slide tambahan: Rincian QA gold standard examples

---

**Terima Kasih — Siap Menjawab Pertanyaan**

---

## Catatan Teknis untuk Pembuatan Slide

### Opsi Tools:
1. **Marp (Markdown → PDF/HTML/PPTX)** — Recommended: write once, export multi-format
   ```bash
   npm install -g @marp-team/marp-cli
   marp Capstone-GraphRAG-Presentation.md --pdf --allow-local-files
   ```
2. **Reveal.js** — HTML presentation, interactive
3. **LibreOffice Impress / PowerPoint** — Manual, gunakan outline di atas
4. **Canva / Figma** — Visual-heavy, import outline

### Diagram Draw.io:
File utama: `/home/guard/Documents/perkuliahan/sem 7/Cap/Capstone-Drawings-Rapi.drawio` (4 halaman)
- Hal 1: System Context Diagram → Slide 5 (Context)
- Hal 2: Container Diagram → Slide 5 (Container)
- Hal 3: Component Diagram (Ingestion Pipeline) → Slide 7
- Hal 4: Sequence Diagram (Query Pipeline) → Slide 8

**Export PNG untuk slide:**
- Buka draw.io desktop → File → Export → PNG → pilih halaman → 1920x1080 atau 2x scale

### Generator Laporan (untuk konsistensi):
```bash
cd /home/guard/Documents/perkuliahan/sem 7/Cap/
python make_makalah_capstone.py  # generate .docx dari Template.docx
soffice --headless --convert-to pdf Proposal-Capstone-GraphRAG.docx
```

---

## Checklist Persiapan Presentasi

- [ ] Slide deck final (Marp/Reveal.js/PPTX) — review typography, contrast, animation minimal
- [ ] Diagram PNG exported dari draw.io (4 halaman) — embed di slide 5, 7, 8
- [ ] Speaker notes printed / di device terpisah
- [ ] Demo video recorded (3–5 menit) — ingest → query → visualize
- [ ] Backup slides siap (schema Pydantic, contoh output, deployment)
- [ ] Repo GitHub updated dengan latest code (tag `proposal-v1`)
- [ ] Laptop test: projector/HDMI, audio, internet (untuk live demo jika perlu)
- [ ] Print 1 halaman ringkasan (1-pager) untuk dosen penguji