---
title: "Capstone GraphRAG — Speaker Notes & Q&A Prep"
tags: [capstone, graphrag, presentation, speaker-notes, qa]
updated: 2026-11-23
---

# Capstone GraphRAG — Speaker Notes & Q&A Preparation

**Untuk:** Presenter (Anggota 1 / Ketua Tim)
**Durasi:** 15–20 menit presentasi + 10 menit Q&A
**Audience:** Dosen pembimbing + 2 dosen penguji capstone

---

## Slide-by-Slide Speaker Notes

### Slide 1: Cover (30 detik)
**Script:**
> "Assalamualaikum warahmatullahi wabarakatuh. Selamat pagi/siang Bapak/Ibu dosen pembimbing dan penguji yang berbahagia.
>
> Perkenalkan, saya [Nama] mewakili tim capstone kami beranggotakan 3 orang: [Nama Anggota 1] sebagai Backend Lead, [Nama Anggota 2] sebagai Retrieval Engineer, dan [Nama Anggota 3] sebagai API & Experiment Lead.
>
> Judul proyek kami: **Academic & Research Paper GraphRAG: Sistem RAG Tingkat Lanjut dengan Knowledge Graph untuk Literatur Ilmiah**.
>
> Proyek ini berjalan selama 10 minggu, mulai 14 November 2026, dan hari ini kami mempresentasikan proposal tahap perencanaan yang sudah disetujui dosen pembimbing minggu lalu."

**Tips:**
- Kontak mata ke semua dosen
- Tone percaya diri tapi tidak berlebihan
- Siap jawab "Siapa ketua?" → tunjuk ke slide (Anggota 1)

---

### Slide 2: Latar Belakang & Masalah (1.5 menit)
**Script:**
> "Sebelum ke solusi, mari lihat **masalah nyata** yang kami temukan pada RAG standar — atau yang sering disebut *vector-only RAG*.
>
> Tiga gap fundamental:
> 1. **Single-hop retrieval** — vector search hanya mengembalikan chunk paling mirip secara semantik. Dia tidak bisa 'melompat' antar dokumen.
> 2. **Tidak ada relasi struktural** — sitasi antar paper, metode yang sama, dataset yang sama, penulis yang sama — semuanya hilang saat di-embed jadi vektor.
> 3. **Hallucination risk** — LLM bebas mengarang sitasi karena tidak ada mekanisme validasi against source of truth.
>
> Contoh konkret: query *'Bandungkan performa LSTM vs Transformer pada dataset inflasi Indonesia'*. Vector search akan return paper LSTM terpisah dan paper Transformer terpisah. Tidak ada relasi 'paper A cite paper B' atau 'keduanya pakai dataset sama'. GraphRAG memecahkan ini dengan knowledge graph eksplisit."

**Antisipasi Pertanyaan:**
- *Q: "Kenapa tidak pakai LangChain/LlamaIndex GraphRAG yang sudah jadi?"*
  → A: "Kami *reference* arsitektur mereka tapi build custom untuk: (1) schema domain akademik khusus (CITES, USES_METHOD, dll), (2) zero-cost inference via OpenRouter free + local embedding, (3) eksperimen terukur E1–E4 yang butuh akses penuh ke pipeline."

---

### Slide 3: Rumusan Masalah & Tujuan (1 menit)
**Script:**
> "Dari gap tadi, kami merumuskan 3 rumusan masalah yang *langsung* menjurus ke 3 tujuan penelitian:
>
> 1. **Rumusan 1** → **Tujuan 1**: Bangun pipeline ingestion end-to-end PDF → Knowledge Graph Neo4j → Query API dengan grounding.
> 2. **Rumusan 2** → **Tujuan 2**: 4 eksperimen sistematis — E1 chunking, E2 embedding, E3 retrieval depth, E4 ablation graph vs vector.
> 3. **Rumusan 3** → **Tujuan 3**: Prototype working demo: REST API + visualisasi graf interaktif.
>
> Perbedaan dengan skripsi biasa: **fokus pada eksperimen terukur (measured experiments)** bukan sekadar 'sistem berjalan'."

**Key Point:** Tekankan "measured experiments" — ini differentiator akademik.

---

### Slide 4: Solusi GraphRAG (1.5 menit)
**Script:**
> "Ini arsitektur inti GraphRAG kami — tiga stage berurutan:
>
> **Stage 1: Semantic Vector Search** — input query di-embedding, cari top-k paper paling mirip (seed nodes).
> **Stage 2: Knowledge Graph Traversal** — dari seed nodes, traverse 1–2 hops lewat edges: CITES, USES_METHOD, USES_DATASET, ADDRESSES_TOPIC. Ini yang bikin multi-hop possible.
> **Stage 3: Grounded Synthesis** — LLM generate jawaban *dengan wajib cite paper_id dari subgraph*. Citation validator cek apakah sitasi benar ada di retrieved context. Kalau tidak, ditolak.
>
> Perbandingan cepat: Vector-only RAG gagal di multi-hop, hallucination-prone, explainability rendah. GraphRAG native support multi-hop, grounded citations, graph path visible untuk explainability."

**Visual:** Arahkan pointer ke diagram alur 3 kotak.

---

### Slide 5: Container Diagram (2 menit)
**Script:**
> "Ini Container Diagram (C4 Level 2) — 5 container internal dalam boundary GraphRAG System:
>
> 1. **API Gateway** — FastAPI, handle routing, validation, rate limit, SSE streaming.
> 2. **Ingestion Service** — Pipeline PDF parsing (Grobid), chunking, entity extraction (Instructor+Pydantic), graph injection (batch Cypher APOC), vector indexing.
> 3. **Query/GraphRAG Service** — Hybrid search (vector + graph traversal), context assembly, LLM synthesis, citation validation.
> 4. **Visualization Service** — Extract subgraph, format JSON kompatibel React Flow/D3.js untuk frontend.
> 5. **Embedding Service** — **Kunci cost-saving**: all-MiniLM-L6-v2 384-d jalan lokal via systemd service port 8788. OpenRouter *tidak punya* free embedding model.
>
> External systems: Neo4j (graph + vector index terintegrasi), Grobid (PDF parser), OpenRouter (free LLM), Ollama (fallback)."

**Antisipasi Pertanyaan:**
- *Q: "Kenapa embedding lokal, tidak pakai OpenAI text-embedding-3-small?"*
  → A: "Cost. OpenRouter free tier tidak punya embedding. OpenAI butuh billing. MiniLM 384-d cukup untuk semantic search akademik, latency < 50ms per batch, zero cost."

---

### Slide 6: Data Model Neo4j (1.5 menit)
**Script:**
> "Schema Neo4j dirancang khusus domain literatur ilmiah — 5 node types, 5 relationship types:
>
> **Nodes:** Paper (core), Author, Concept (task/domain/metric), Method, Dataset.
> **Edges:** WROTE, CITES, ADDRESSES_TOPIC, USES_METHOD, USES_DATASET.
>
> Desain ini enable query seperti: *'Paper apa yang cite paper X dan menggunakan method Y?'* — single Cypher query.
>
> Embedding disimpan di node Paper (abstract) dan Chunk (paragraph) untuk vector search dual-granularity."

**Visual:** Tunjuk ke diagram schema (Author→Paper→CITES→Paper→USES_METHOD→Method).

---

### Slide 7: Pipeline Ingestion (2 menit)
**Script:**
> "Pipeline ingestion 6 step, semua modular & swappable:
>
> 1. **Parsing** — Grobid self-hosted primary, LlamaParse fallback. Output: teks terstruktur + metadata (title, authors, references).
> 2. **Chunking** — 3 strategi untuk E1: Fixed (512/1024 token), Semantic (berdasar heading/section), Proposition-based (atomic claims).
> 3. **Entity Extraction** — Instructor + Pydantic v2 enforce structured output. Schema: Author, Concept, Method, Dataset, Relations (CITES, USES_METHOD, dll).
> 4. **Graph Injection** — Batch Cypher async via APOC, idempotent by paper_id (MERGE nodes, CREATE edges).
> 5. **Vector Indexing** — Call local embedding service → upsert ke Neo4j Vector Index (cosine, 384-d).
> 6. **Response** — paper_id, stats (entities, chunks, duration).
>
> Status sekarang: 4 paper GraphRAG corpus sudah ter-ingest, 313 chunks, embeddings 384-d live. CITES edges functional setelah fix Paper.title matcher."

**Antisipasi Pertanyaan:**
- *Q: "Grobid accuracy untuk reference extraction?"*
  → A: "~85-90% untuk format standar arXiv/Elsevier. Kami pakai fallback LlamaParse untuk PDF scan/complex layout. Citation graph builder sudah test 110 papers, extract ~2000 references, match 4 internal citations."

---

### Slide 8: Pipeline Query (2 menit)
**Script:**
> "Query pipeline — hybrid search yang bikin GraphRAG beda:
>
> 1. **Vector Search** — query embedding → top-k seed papers (default 5).
> 2. **Graph Traversal** — dari seed, traverse depth hops (default 2) lewat CITES, USES_METHOD, USES_DATASET, ADDRESSES_TOPIC. Pakai APOC `apoc.path.subgraphAll`.
> 3. **Subgraph Assembly** — gabungkan nodes, edges, vector chunks jadi structured context.
> 4. **Context Builder + Prompt Template** — format ke LLM dengan instruksi wajib cite `[Paper ID]`.
> 5. **LLM Synthesis** — OpenRouter free model (Nemotron/Ling) generate answer + citations.
> 6. **Citation Validation** — cek setiap `[Paper ID]` benar ada di subgraph. Grounding score = proporsi klaim supported.
> 7. **Response** — answer, sources, graph_path, grounding_score, latency_ms. Support SSE streaming.
>
> Parameter: `top_k` (3/5/10), `depth` (1/2/3), `stream` (true/false). Target latency P95 < 10 detik."

---

### Slide 9: Eksperimen E1–E4 (2 menit) — **SLIDE PALING KRITIS**
**Script:**
> "Ini **diferensiasi utama** proyek kami — 4 eksperimen terukur dengan metrik otomatis:
>
> **E1: Chunking Strategy** — Fixed vs Semantic vs Proposition. Metrik: retrieval precision, latency. Hypothesis: Proposition-based lebih baik untuk entity extraction tapi lebih lambat.
>
> **E2: Embedding Model** — OpenAI 3-small (1536-d) vs nomic-embed Ollama (768-d) vs IndoBERT. Metrik: NDCG@10, multi-lingual retrieval. Hypothesis: Local model cukup untuk domain akademik Inggris, IndoBERT butuh untuk paper Indonesia.
>
> **E3: Retrieval Depth** — Grid search top_k {3,5,10} × depth {1,2,3}. Metrik: grounding score, citation accuracy, latency, graph path count. Hypothesis: depth=2 sweet spot, depth=3 diminishing returns + latency naik.
>
> **E4: ABLATION — PALING PENTING** — GraphRAG full vs Vector-only vs Vector+Graph (no traversal) vs No citation validation. **Primary metric: Citation Accuracy & Grounding Score**. Statistical test: paired t-test p < 0.05.
>
> Dataset: 50-100 paper arXiv cross-domain, 30-40 QA gold multi-hop (min 2 hops). Evaluasi fully otomatis — grounding score & citation accuracy dihitung script, bukan manual."

**Antisipasi Pertanyaan (SANGAT MUNCUL):**
- *Q: "Berapa sample size QA gold? Cukup untuk statistical significance?"*
  → A: "30-40 pairs. Paired t-test butuh ~20+ untuk power 0.8. Kami target 40. Jika kurang, akan tambah via synthetic generation dari corpus."
- *Q: "Citation accuracy target 0.60 — kenapa tidak lebih tinggi?"*
  → A: "Baseline vector-only ~0.2-0.3. 0.60 sudah 2x improvement. Paper académik citation format bervariasi, LLM free tier punya keterbatasan. Ini target realistis untuk prototype."

---

### Slide 10: Tech Stack (1 menit)
**Script:**
> "Stack modern, production-ready, tapi **zero-cost untuk mahasiswa**:
>
> - **Python 3.11 + FastAPI + Pydantic v2** — type-safe, async, auto-docs.
> - **Neo4j 5.18 + APOC + Vector Index** — graph DB + vector index *terintegrasi*, tidak butuh Pinecone/Weaviate terpisah.
> - **Instructor + Pydantic** — structured LLM output enforcement.
> - **Local Embedding** — all-MiniLM-L6-v2 384-d via systemd service. **Kunci cost-saving**.
> - **OpenRouter Free Only** — enforce `:free` suffix di config & code. Nemotron untuk extraction, Ling untuk synthesis.
> - **Grobid self-hosted** — PDF parser terbaik untuk akademik.
> - **Docker Compose + systemd** — deployment laptop-friendly.
> - **CI-ready** — ruff, black, mypy, pytest ≥ 70% coverage."

**Key Message:** "Zero-cost inference" — ulang 2x.

---

### Slide 11: Timeline & Progress (1.5 menit)
**Script:**
> "Timeline 10 minggu standar capstone UIR. Saat ini **Minggu 3** (21-27 Nov), progress solid:
>
> **✅ Minggu 1 SELESAI:** Proposal approved, konsultasi dosen, Docker Compose running, Neo4j schema migration, project structure, diagram 4 halaman.
>
> **🔄 Minggu 2-3 IN PROGRESS:** Corpus 4 paper GraphRAG ter-ingest (313 chunks, 384-d embeddings). Retrieval API terverifikasi: vector search + graph traversal + CITES edges functional. Blocker: LLM quota OpenRouter reset harian ~07:00 WIB memperlambat entity extraction batch. Solusi: lokal embedding sudah live, batch processing dioptimasi.
>
> **⏳ Minggu 4 Target:** Query pipeline end-to-end working + visualisasi graf.
>
> **Risiko utama:** Corpus scale-up ke 50+ paper untuk eksperimen E1–E4. Sudah siap script download arXiv bulk + citation graph builder."

**Visual:** Tunjuk ke tabel Gantt, highlight Minggu 1-3 biru, Minggu 4 hijau.

---

### Slide 12: Pembagian Tugas & Risk (1 menit)
**Script:**
> "Pembagian peran jelas tapi kolaboratif:
>
> - **Anggota 1 (Ketua):** Backend Lead — Neo4j schema, ingestion pipeline, entity extraction, graph injection, Cypher optimization.
> - **Anggota 2:** Retrieval Engineer — Vector search, hybrid search, graph traversal APOC, context assembly, LLM synthesis, grounding validation.
> - **Anggota 3:** API/Viz/Experiment — FastAPI endpoints, React Flow/D3 visualisasi, experiment framework E1-E4, evaluasi metrik.
>
> **Risk Management realistis:**
> 1. **LLM quota** (Tinggi) → Fallback Ollama, batch processing, budget planning.
> 2. **Grobid setup** (Sedang) → Dual option, test early, Docker pinned.
> 3. **Workload balance** (Sedang) → Weekly sync 15min, GitHub Projects, pair programming.
> 4. **Corpus size** (Sedang) → Target 50+ paper, citation graph builder, arXiv bulk download ready."

---

### Slide 13: Deliverables & KPI (1 menit)
**Script:**
> "Deliverables konkret & verifiable:
>
> 1. Laporan Capstone .docx/.pdf (format MAKALAH UIR via Template.docx + generator script)
> 2. Slide presentasi (file ini)
> 3. Demo video 3-5 menit (ingest → query → visualize)
> 4. Source code GitHub private repo + README lengkap
> 5. Diagram arsitektur .drawio + .png 4 halaman
>
> **KPI Terukur (Otomatis):**
> - Ingestion throughput ≥ 5 paper/menit
> - Query latency P95 < 10 detik
> - **Citation Accuracy > 0.60** (E4 primary metric)
> - **Grounding Score > 0.75** (E4 primary metric)
> - **GraphRAG > Vector-Only signifikan p < 0.05** (paired t-test)
> - Code quality: mypy/ruff clean, pytest ≥ 70% coverage (CI gate)"

**Key Point:** "Semua KPI terukur otomatis via script — bukan manual feel."

---

### Slide 14: Kesimpulan (30 detik)
**Script:**
> "Ringkasan 3 poin kunci:
>
> 1. **Novelitas:** GraphRAG untuk literatur ilmiah cross-domain dengan knowledge graph eksplisit — bukan sekadar vector search.
> 2. **Rigorasitas:** 4 eksperimen terukur dengan metrik otomatis + statistical significance testing.
> 3. **Production-Ready Zero-Cost:** FastAPI + Neo4j integrated vector + Local Embedding + Free LLM — deployable di laptop mahasiswa.
>
> **Permintaan:** Kami meminta persetujuan lanjut ke tahap implementasi penuh (Minggu 4-10), target demo working Minggu 7, laporan final Minggu 10.
>
> Terima kasih. Siap menjawab pertanyaan Bapak/Ibu dosen."

---

## Q&A Preparation — Pertanyaan Paling Mungkin

### Kategori 1: Teknis Arsitektur

| Pertanyaan | Jawaban Singkat | Detail Jika Dilanjutkan |
|---|---|---|
| "Kenapa Neo4j, bukan PostgreSQL + pgvector?" | Graph traversal native (APOC), CITES/USES_METHOD butuh variable-length path. pgvector hanya vector search. | Neo4J `apoc.path.subgraphAll` handle variable-depth traversal single query. Postgres butuh recursive CTE kompleks. |
| "Vector index Neo4j vs Pinecone/Weaviate?" | Integrated, zero extra infra, ACID transaction graph+vector atomic. Cukup untuk 10k-100k nodes. | Pinecone better untuk scale >1M vectors. Capstone scope 50-100 paper, Neo4J integrated sufficient. |
| "Citation validation beneran prevent hallucination?" | Ya — LLM wajib cite `[Paper ID]`, validator cek ID ada di subgraph. Grounding score quantifies support. | Bukan 100% foolproof — LLM bisa cite ID yang *ada* tapi konteksnya salah. Grounding score catch ini. |
| "Kenapa tidak pakai LangGraph/LlamaIndex workflow?" | Butuh custom schema (CITES, USES_METHOD), full control pipeline untuk eksperimen E1-E4, zero-cost constraint. | LangGraph/LlamaIndex bagus untuk production cepat. Riset butuh akses granular ke setiap stage untuk ablation. |

### Kategori 2: Eksperimen & Evaluasi

| Pertanyaan | Jawaban Singkat | Detail Jika Dilanjutkan |
|---|---|---|
| "QA gold 30-40 pairs — cukup untuk statistical significance?" | Ya, paired t-test butuh ~20+ untuk power 0.8. Target 40. | Jika reviewer minta lebih: "Kami siap generate synthetic QA dari corpus via LLM + manual verify." |
| "Citation accuracy target 0.60 — kenapa rendah?" | Baseline vector-only ~0.2-0.3. 0.60 = 2x improvement. Realistis untuk free LLM. | "Target stretch: 0.75. Jika E4 hasil >0.75, kami update laporan. 0.60 adalah minimum viable." |
| "Evaluasi otomatis vs human evaluation?" | Otomatis (grounding, cite_acc) untuk scale & reproducibility. Human eval untuk kualitas jawaban (subset). | "30-40 QA auto-eval + 10 QA human eval (blind) untuk validasi korelasi auto vs human." |
| "E1 chunking — proposition-based apa bedanya semantic?" | Proposition = atomic claims per sentence. Semantic = by heading/section. Proposition lebih granular untuk entity extraction. | "Proposition-based butuh LLM call lebih banyak (cost/latency). E1 akan quantify trade-off." |

### Kategori 3: Implementasi & Feasibility

| Pertanyaan | Jawaban Singkat | Detail Jika Dilanjutkan |
|---|---|---|
| "Progress Minggu 3 — apakah on track?" | Ya. Minggu 1-2 deliverables done. Minggu 3 ingestion 4 paper done, retrieval API verified. Blocker LLM quota managed. | "Minggu 4 target: query pipeline end-to-end + visualisasi. Corpus scale-up parallel." |
| "Free LLM OpenRouter — reliable untuk capstone?" | Ya, enforce `:free` suffix. Nemotron-3.5-Lightning & Ling-3.2-Flash stable. Fallback Ollama ready. | "Rate limit ~20 req/min handled dengan retry+exponential backoff. Batch processing di ingestion." |
| "Deployment target — laptop mahasiswa?" | Ya. Docker Compose + systemd embedding service. RAM 16GB cukup (Neo4j ~4GB, embedding ~1GB, backend ~500MB). | "Tested di ThinkPad X13 Gen 1 (Ryzen 5 PRO 4650U, 16GB). Tidak butuh GPU." |
| "Batasan proyek — apa yang TIDAK dikerjakan?" | Frontend full (hanya viz JSON), multi-user auth, production hardening, paper Indonesia NLP (IndoBERT optional E2). | "Scope terbatas: core GraphRAG pipeline + eksperimen. Frontend viz hanya React Flow JSON output." |

### Kategori 4: Akademik & Metodologi

| Pertanyaan | Jawaban Singkat | Detail Jika Dilanjutkan |
|---|---|---|
| "Contribution vs existing GraphRAG papers?" | Domain-specific schema (academic), zero-cost stack, systematic E1-E4 ablation, Indonesian context. | "Existing: Microsoft GraphRAG (general), Neo4j GraphRAG (demo). Kami: academic domain + rigorous eval + zero-cost." |
| "Baseline vector-only — fair comparison?" | Ya, same corpus, same LLM, same prompt template — hanya disable graph traversal & citation validation. | "Ablation E4 isolates graph component. Vector-only = same pipeline tapi skip GraphTraversal & CitationValidator." |
| "Generalizability ke domain lain?" | Schema extensible (add node/edge types). Pipeline modular (swap parser, chunker, embedder). | "Demo: academic papers. Bisa adapt ke legal docs (add CASE_CITES, STATUTE), medical (add TREATS, DIAGNOSES)." |

---

## Backup Slides Content (Siap Jika Ditanya)

### Backup 1: Pydantic Schema Entity Extraction
```python
class ExtractedEntities(BaseModel):
    authors: list[AuthorEntity]
    concepts: list[ConceptEntity]
    methods: list[MethodEntity]
    datasets: list[DatasetEntity]
    relations: list[RelationEntity]

class RelationEntity(BaseModel):
    source_type: Literal["Paper", "Author", "Concept", "Method", "Dataset"]
    source_name: str
    relation: Literal["WROTE", "CITES", "ADDRESSES_TOPIC", "USES_METHOD", "USES_DATASET"]
    target_type: Literal["Paper", "Author", "Concept", "Method", "Dataset"]
    target_name: str
```

### Backup 2: Contoh Output Query GraphRAG
```json
{
  "answer": "Paper 'GraphRAG Under Fire' (2025) mengusulkan hybrid retrieval...",
  "sources": [
    {"paper_id": "3a2f8ab5", "title": "GraphRAG Under Fire", "year": 2025},
    {"paper_id": "5ef495fc", "title": "Streamlining Software Citations", "year": 2024}
  ],
  "graph_path": [
    ["3a2f8ab5", "CITES", "5ef495fc"],
    ["3a2f8ab5", "USES_METHOD", "GraphRAG"],
    ["5ef495fc", "ADDRESSES_TOPIC", "Citation Analysis"]
  ],
  "grounding_score": 0.92,
  "latency_ms": 6420
}
```

### Backup 3: Deployment Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    LAPTOP MAHASISWA (16GB RAM)                │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Neo4j     │  │  Backend    │  │  Embedding Service  │  │
│  │  (Docker)   │  │  (Docker)   │  │  (systemd :8788)    │  │
│  │  ~4 GB      │  │  ~500 MB    │  │  ~1 GB (MiniLM)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │               │                   │                │
│         └───────────────┼───────────────────┘                │
│                         ▼                                     │
│              ┌─────────────────────┐                          │
│              │   Ollama (Optional) │                          │
│              │   Fallback LLM      │                          │
│              │   ~2-4 GB           │                          │
│              └─────────────────────┘                          │
│                                                               │
│  Total RAM ~6-10 GB (aman di 16 GB)                          │
└─────────────────────────────────────────────────────────────┘
```

### Backup 4: QA Gold Standard Examples
| Type | Question | Min Hops | Evidence Path |
|---|---|---|---|
| Method Comparison | "Paper mana yang compare BERT vs GPT untuk NER?" | 2 | Paper A → CITES → Paper B |
| Dataset Usage | "Dataset apa yang dipakai paper yang cite BERT?" | 2 | Paper X → CITES → BERT paper → USES_DATASET → Dataset |
| Concept Evolution | "Bagaimana konsep 'attention' evolusi 2017-2023?" | 3+ | 2017 paper → CITES → 2019 paper → CITES → 2023 paper |
| Author Collaboration | "Siapa co-author network dari author X?" | 2 | Author X → WROTE → Paper → WROTE → Author Y |

---

## Tips Presentasi Teknis

### Do's ✅
- **Pakai pointer/laser** ke diagram saat explain flow
- **Jawab singkat dulu**, baru detail jika ditanya lanjut
- **Akui keterbatasan** jujur: "Free LLM punya keterbatasan, itu sebabnya kami target citation accuracy 0.60 realistis"
- **Rujuk ke bukti**: "Seperti terlihat di progress log Minggu 3, retrieval API sudah terverifikasi..."
- **Tone kolaboratif**: "Kami berdiskusi dengan dosen pembimbing minggu lalu dan..."

### Don'ts ❌
- Jangan over-promise: "Sistem ini akan mengalahkan Google Scholar"
- Jangan defensive saat pertanyaan kritis: "Itu bukan masalah karena..."
- Jangan terlalu detail implementasi low-level kecuali ditanya
- Jangan baca slide — slide untuk audience, notes untuk Anda

### Handling "Tidak Tahu"
> "Itu pertanyaan bagus. Saat ini kami belum mengeksplorasi aspek itu secara mendalam. Rencana kami adalah [X] di Minggu [Y]. Bapak/Ibu punya saran arah yang lebih baik?"

---

## Checklist Hari Presentasi

### Sebelum Presentasi (H-1)
- [ ] Slide deck final render PDF/PPTX (test di laptop presentasi)
- [ ] Diagram PNG 4 halaman embedded benar
- [ ] Demo video render 1080p, test play
- [ ] Speaker notes print / di tablet
- [ ] Backup slides ready (4 slides di atas)
- [ ] Repo GitHub updated, tag `proposal-v1`
- [ ] Laptop test: HDMI, audio, battery full, charger bawa
- [ ] 1-pager ringkasan print 3 copies (dosen pembimbing + 2 penguji)

### Saat Presentasi
- [ ] Datang 15 menit awal setup
- [ ] Test microphone/proyektor
- [ ] Bawa air putih
- [ ] Timer di HP (vibrate) untuk pacing 20 menit

### Setelah Presentasi
- [ ] Catat feedback dosen (bawa notebook)
- [ ] Update action items ke vault/kanban
- [ ] Commit slide final ke repo
- [ ] Mulai Minggu 4 implementation per feedback

---

## Closing Note

> **"Persiapan teknis sudah solid (code running, metrics defined, risks mitigated). Yang perlu ditampilkan: kepercayaan diri, kejujuran atas keterbatasan, dan keteguhan pada metodologi eksperimen yang ketat. Dosen menghargai rigor over hype."**

**Good luck! 🚀**