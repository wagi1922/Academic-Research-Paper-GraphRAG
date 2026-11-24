# Experiment Plan — Academic & Research Paper GraphRAG

**Project:** Capstone GraphRAG  
**Timeline:** Minggu 5–9 (Implementasi) → Minggu 9–10 (Evaluasi)  
**Tim:** 3 orang  
**Updated:** 2026-11-14

---

## 1. Tujuan Eksperimen

Mengevaluasi performa pipeline GraphRAG end-to-end dengan menguji empat variabel utama:
- **E1:** Chunking strategy → kualitas retrieval & answer generation
- **E2:** Embedding model → vector search quality
- **E3:** Retrieval parameters (top_k, depth) → coverage vs precision trade-off
- **E4:** Ablation study → kontribusi komponen graph vs vector-only

---

## 2. Dataset & Gold Standard

| Komponen | Detail |
|---|---|
| **Corpus** | 50 paper akademik (CS, ML, Economics cross-domain) |
| **Format** | PDF (Grobid parsed) + metadata (title, authors, year, DOI, venue, keywords) |
| **Gold QA Pairs** | 30 pertanyaan dengan jawaban referensi + expected citations |
| **Query Types** | Factual lookup, method comparison, concept explanation, multi-hop reasoning |
| **Split** | 20 train (tuning) + 10 test (final evaluation) |

> **Sumber paper:** arXiv (CS.CL, CS.LG, ECON), Semantic Scholar API, manual curation

---

## 3. Metrik Evaluasi

| Kategori | Metrik | Formula / Deskripsi |
|---|---|---|
| **Retrieval** | Precision@k | Relevant chunks in top-k / k |
| | Recall@k | Relevant chunks retrieved / total relevant |
| | MRR | Mean Reciprocal Rank of first relevant |
| **Generation** | Answer F1 | Token-level F1 vs gold answer |
| | Citation Accuracy | % claims backed by correct source |
| | Faithfulness | LLM-evaluated: answer grounded in context |
| **System** | Latency (ms) | End-to-end p50, p95 |
| | Token Cost | Input + output tokens per query |
| | Graph Coverage | % nodes/edges utilized in answer |

---

## 4. Eksperimen Detail

### E1: Chunking Strategy Comparison

| Config | Parameter |
|---|---|
| **Strategies** | `fixed_512_50`, `fixed_1024_100`, `semantic_nomic`, `proposition_gpt4o_mini` |
| **Embedding** | `nomic-embed-text-v1.5:free` (fixed) |
| **Retrieval** | top_k=5, depth=2 (fixed) |
| **LLM** | `inclusionai/ling-3.2-flash:free` (fixed) |
| **Runs** | 3 per strategy (different random seeds for semantic/proposition) |

**Hypothesis:** Semantic/proposition chunking > fixed-size untuk answer quality; fixed-size > semantic untuk latency.

---

### E2: Embedding Model Comparison

| Config | Parameter |
|---|---|
| **Models** | `nomic-embed-text-v1.5:free`, `inclusionai/ling-3.2-flash:free`, `google/gemma-4-31b-it:free`, `nvidia/nemotron-3.5-lightning:free`, `particle-ai/particle-1:free` |
| **Chunking** | Best dari E1 (fixed) |
| **Retrieval** | top_k=5, depth=2 (fixed) |
| **LLM** | `inclusionai/ling-3.2-flash:free` (fixed) |
| **Runs** | 3 per model |

**Hypothesis:** `nomic-embed-text-v1.5:free` competitive; `inclusionai/ling-3.2-flash:free` dual-purpose (LLM + embedding); gemma/nemotron/particle alternatif.

---

### E3: Retrieval Parameter Sweep

| Config | Parameter |
|---|---|
| **top_k** | 3, 5, 10, 15 |
| **depth** | 1, 2, 3 |
| **Chunking** | Best E1 |
| **Embedding** | Best E2 |
| **LLM** | `inclusionai/ling-3.2-flash:free` (fixed) |
| **Runs** | 1 per combo (grid search) |

**Hypothesis:** top_k=10, depth=2 optimal balance; depth=3 diminishing returns + latency spike.

---

### E4: Ablation Study

| Variant | Components Active |
|---|---|
| **Full GraphRAG** | Vector + Graph Traversal + Entities + Chunks |
| **Vector Only** | Vector Search + Chunks (no graph) |
| **Graph Only** | Graph Traversal + Entities (no vector chunks) |
| **No Entities** | Vector + Graph (no entity extraction in context) |
| **No Citations** | Full pipeline, citation validation disabled |

**Hypothesis:** Full > Vector Only > Graph Only; Entities critical untuk multi-hop; Citations improve faithfulness 15-20%.

---

## 5. Experiment Execution Order

| Urutan | Eksperimen | Dependensi | Estimasi Waktu | Output |
|---|---|---|---|---|
| 1 | **E1: Chunking** | Ingestion pipeline ready | 2 hari | `experiments/results/E1/` |
| 2 | **E2: Embedding** | E1 best chunking strategy | 2 hari | `experiments/results/E2/` |
| 3 | **E3: Retrieval** | E1+E2 best config | 2 hari | `experiments/results/E3/` |
| 4 | **E4: Ablation** | Full pipeline working | 3 hari | `experiments/results/E4/` |

**Total:** ~9 hari (Minggu 5–9)

---

## 6. Runner Scripts

Semua script di `experiments/`:
- `run_e1_chunking.py` — loads `config/e1_chunking.yaml`
- `run_e2_embedding.py` — loads `config/e2_embedding.yaml`
- `run_e3_retrieval.py` — loads `config/e3_retrieval_params.yaml`
- `run_e4_ablation.py` — loads `config/e4_ablation.yaml`

**Output per run:**
- CSV: `results/{exp_id}/metrics.csv` (per-query metrics)
- JSON: `results/{exp_id}/summary.json` (aggregated stats)
- Plots: `results/{exp_id}/plots/` (auto-generated via analysis notebook)

---

## 7. Analysis & Reporting

| Deliverable | Format | Location |
|---|---|---|
| **Experiment Log** | Markdown table per E1–E4 | `docs/experiment_log.md` |
| **Results Table** | Combined metrics table | `docs/results_summary.md` |
| **Statistical Tests** | Paired t-test / Wilcoxon | Analysis notebook |
| **Visualizations** | Bar charts, latency curves, ablation radar | `experiments/results/*/plots/` |
| **Laporan Akhir Section** | BAB IV Hasil & Pembahasan | `Capstone-GraphRAG-Report.md` → .docx |

---

## 8. Risk & Mitigation

| Risiko | Mitigasi |
|---|---|
| OpenRouter quota habis | **Swap ke alternate free model** (particle-ai/particle-1:free, nvidia/nemotron-3.5-lightning:free, google/gemma-4-31b-it:free), top-up $10 |
| Grobid parsing gagal pada paper tertentu | Skip paper, log warning, pakai LlamaParse API sebagai backup |
| Neo4j vector index lambat | Pre-warm index, gunakan `CALL db.index.vector.queryNodes` dengan parameter optimal |
| Gold QA pairs tidak representatif | Iterate dengan dosen pembimbing Minggu 2–3, tambah 10 pairs jika perlu |

---

## 9. Success Criteria (Definition of Done)

| Kriteria | Target |
|---|---|
| **Answer F1** | ≥ 0.70 pada test set |
| **Citation Accuracy** | ≥ 0.85 |
| **Latency p95** | ≤ 8 detik |
| **Token Cost/query** | ≤ $0.05 (OpenRouter pricing) |
| **Ablation gap** | Full GraphRAG > Vector Only minimal 10% F1 |

---

## 10. Referensi Konfigurasi

- `experiments/config/e1_chunking.yaml`
- `experiments/config/e2_embedding.yaml`
- `experiments/config/e3_retrieval_params.yaml`
- `experiments/config/e4_ablation.yaml`
- `docs/quickstart.md` (section 7 & 16)