---
title: "Capstone GraphRAG — 1-Pager Ringkasan untuk Dosen Penguji"
tags: [capstone, graphrag, handout, one-pager]
updated: 2026-11-23
---

# Academic & Research Paper GraphRAG
**Capstone Project Proposal — Teknik Informatika UIR 2026/2027**

---

## 📋 Identitas Proyek

| Item | Detail |
|---|---|
| **Judul** | Academic & Research Paper GraphRAG: Sistem RAG Tingkat Lanjut dengan Knowledge Graph untuk Literatur Ilmiah |
| **Tim** | 3 Mahasiswa TI UIR (Backend Lead, Retrieval Engineer, API/Viz/Experiment Lead) |
| **Dosen Pembimbing** | [Nama Dosen], S.Kom., M.Kom. |
| **Durasi** | 10 Minggu (14 Nov 2026 – 19 Jan 2027) |
| **Status** | Minggu 1-3 Selesai → Proposal Approved, Env Ready, Ingestion 4 Paper Live |

---

## 🎯 Masalah & Solusi

### Masalah: Keterbatasan RAG Standar (Vector-Only)
- ❌ **Single-hop retrieval** — tidak bisa jawab query kompleks lintas dokumen
- ❌ **Tidak ada relasi struktural** — sitasi, metode, dataset, penulis hilang saat di-embed
- ❌ **Hallucination risk** — LLM mengarang sitasi tanpa validasi

### Solusi: GraphRAG (Vector Search + Graph Traversal + Grounded Synthesis)
```
Query → Vector Search (seed papers) → Graph Traversal (1-2 hops: CITES, USES_METHOD, USES_DATASET, ADDRESSES_TOPIC)
                                              → Subgraph Assembly → LLM Synthesis + Citation Validation
                                              → Answer + Validated Sources + Graph Paths
```

**Keunggulan:** Native multi-hop, grounded citations, explainable via graph paths.

---

## 🏗️ Arsitektur Sistem (Tech Stack Zero-Cost)

| Layer | Teknologi | Cost |
|---|---|---|
| **API Framework** | FastAPI + Pydantic v2 | Free |
| **Graph DB + Vector Index** | Neo4j 5.18 + APOC (integrated) | Free (Community) |
| **LLM Inference** | OpenRouter Free Tier (Nemotron, Ling) | **$0** |
| **Embedding** | Local all-MiniLM-L6-v2 (384-d, systemd :8788) | **$0** |
| **PDF Parsing** | Grobid Self-Hosted (Docker) | Free |
| **Deployment** | Docker Compose + systemd (Laptop 16GB RAM) | Free |

> **Total Inference Cost: $0** — deployable di laptop mahasiswa tanpa GPU.

---

## 🔬 Eksperimen & Evaluasi (4 Eksperimen Terukur)

| Kode | Fokus | Variabel | Metrik Utama |
|---|---|---|---|
| **E1** | Chunking Strategy | Fixed / Semantic / Proposition | Retrieval Precision, Latency |
| **E2** | Embedding Model | OpenAI 3-small / nomic-embed / IndoBERT | NDCG@10, Multi-lingual |
| **E3** | Retrieval Depth | top_k {3,5,10} × depth {1,2,3} | Grounding Score, Cite_Acc, Latency |
| **E4** | **Ablation: Graph vs Vector** | GraphRAG / Vector-only / Vector+Graph / No Validation | **Citation Accuracy, Grounding Score (p < 0.05)** |

**Dataset:** 50-100 paper arXiv cross-domain, **30-40 QA Gold Multi-Hop (min 2 hops)**
**Evaluasi:** Fully otomatis (grounding score, citation accuracy) + statistical significance testing.

---

## 📊 Progress Saat Ini (Minggu 3)

| Milestone | Status | Bukti |
|---|---|---|
| Proposal & Konsultasi Dosen | ✅ Selesai | Approved Minggu 1 |
| Docker Compose (Neo4j + Backend) | ✅ Running | `docker compose up -d` |
| Neo4j Schema Migration | ✅ Done | Constraints, Indexes, Vector Index 384-d |
| Diagram Arsitektur (4 halaman) | ✅ Done | `.drawio` + PNG exported |
| Corpus Ingestion (4 Paper GraphRAG) | ✅ Live | 313 Chunks, 384-d Embeddings |
| Retrieval API Verified | ✅ Functional | Vector Search + Graph Traversal + CITES Edges |
| **Blocker** | 🔄 Managed | LLM Quota OpenRouter (batch + fallback Ollama) |

---

## 🎯 Deliverables & KPI (Terukur Otomatis)

### Deliverables Akhir
1. **Laporan Capstone** — .docx/.pdf (Format MAKALAH UIR via Template.docx + generator script)
2. **Slide Presentasi** — Deck 14 slide (file ini)
3. **Demo Video** — 3-5 menit (Ingest → Query → Visualize)
4. **Source Code** — GitHub Private Repo + README + CI
5. **Diagram Arsitektur** — .drawio + .png (4 halaman)

### KPI Target
| KPI | Target | Verifikasi |
|---|---|---|
| Ingestion Throughput | ≥ 5 paper/menit | Benchmark script 50 paper |
| Query Latency (P95) | < 10 detik | `top_k=5, depth=2` |
| **Citation Accuracy (E4)** | **> 0.60** | Auto-eval 30-40 QA Gold |
| **Grounding Score (E4)** | **> 0.75** | Auto-eval 30-40 QA Gold |
| **GraphRAG > Vector-Only** | **Signifikan (p < 0.05)** | Paired t-test |
| Code Quality | mypy/ruff clean, pytest ≥ 70% | CI Pipeline Pass |

---

## ⚠️ Risk Management (Realistis)

| Risiko | Probabilitas | Mitigasi Konkret |
|---|---|---|
| LLM API Quota (OpenRouter) | Tinggi | Fallback Ollama Local, Batch Processing, Budget Planning |
| Grobid/LlamaParse Setup | Sedang | Dual Option, Test Early, Docker Image Pinned |
| Corpus Tidak Cukup Multi-Hop | Sedang | Target 50+ Paper, Citation Graph Builder, arXiv Bulk Download Ready |
| Workload Tim Tidak Seimbang | Sedang | Weekly Sync 15min, GitHub Projects, Pair Programming |

---

## 📅 Timeline 10 Minggu (Target)

| Minggu | Tanggal | Fokus |
|---|---|---|
| 1 | 14-20 Nov | ✅ Perencanaan, Env Setup, Diagram |
| 2 | 21-27 Nov | 🔄 Ingestion Pipeline Scale-up |
| 3 | 28 Nov-4 Des | 🔄 Retrieval & Query Pipeline |
| 4 | 5-11 Des | ⏳ API Lengkap, Synthesis, Visualisasi |
| 5 | 12-18 Des | ⏳ Eksperimen E1-E2 (Chunking, Embedding) |
| 6 | 19-25 Des | ⏳ Eksperimen E3-E4 (Depth, Ablation) |
| 7 | 26 Des-1 Jan | ⏳ Analisis, Optimasi |
| 8 | 2-8 Jan | ⏳ Dokumentasi Laporan & Slide |
| 9 | 9-15 Jan | ⏳ Simulasi Presentasi, Finalisasi |
| 10 | 16-19 Jan | **DEADLINE: Pengumpulan & Presentasi Final** |

---

## 🤝 Permintaan Persetujuan

> **Kami meminta persetujuan dosen pembimbing & penguji untuk melanjutkan ke tahap implementasi penuh (Minggu 4-10) dengan target demo working Minggu 7 dan laporan final Minggu 10.**

**Kontak Tim:** [Email/WA Ketua Tim] | **Repo:** [GitHub URL] | **Demo Video:** [Link/QR Code]

---

*Disusun oleh Tim Capstone GraphRAG — Teknik Informatika UIR — November 2026*