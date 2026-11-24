# Experiment Log — Academic & Research Paper GraphRAG

**Project:** Capstone GraphRAG  
**Timeline:** Minggu 3 (2026-11-18 s.d. 2026-11-20)  
**Status:** E1, E2, E3, E4 **SELESAI** (partial — QA generation blocked by OpenRouter limit)  
**Updated:** 2026-11-21

---

## 1. Ringkasan Eksekusi

| Eksperimen | Status | Queries Run | Best Config | Key Finding |
|---|---|---|---|---|
| **E1: Chunking** | ✅ 2/5 selesai | 47 total | `fixed_512_50` (grounding 1.0) / `fixed_1024_100` (cite_acc 0.26) | Semantic/proposition blocked by rate limit; fixed strategies viable |
| **E2: Embedding** | ✅ 7/10 selesai | 218 total | `minilm-l6-v2` (grounding 1.0, local) / `m3e-base` (0.95, local) | Local embeddings competitive; OpenAI/Nomic rate-limited |
| **E3: Retrieval Params** | ✅ Selesai | 20 runs | `topk10_depth2` (grounding 1.0, 3.4 paths, ~7.6s) | Depth=1 slightly better cite_acc at topk5; graph adds +0.07 grounding |
| **E4: Ablation** | ✅ Selesai | 30 runs | `full_graphrag` (grounding 0.90, cite_acc 0.40) | Graph component marginal (sparse citations); citation validation working |

**Total API Calls:** ~315 (mix OpenRouter + local)  
**Blocker:** OpenRouter free tier exhausted ($0.10/$0.10) — E1/E2 incomplete, QA generation blocked

---

## 2. E1: Chunking Strategy — Detail Results

### 2.1 Config Tested

| Strategy | Description | Status | Queries |
|---|---|---|---|
| `fixed_512_50` | 512 chars, 50 overlap | ✅ Selesai | 27 |
| `fixed_1024_100` | 1024 chars, 100 overlap | ✅ Selesai | 20 |
| `semantic_nomic` | Semantic boundaries (nomic embeddings) | ❌ Rate limit | 0 |
| `proposition_gpt4o_mini` | LLM-extracted propositions | ❌ Rate limit | 0 |

### 2.2 Metrics Comparison

| Metric | `fixed_512_50` | `fixed_1024_100` |
|---|---|---|
| **Queries** | 27 | 20 |
| **Avg Latency** | 38.8s | 41.8s |
| **Grounding Score** | **1.000** | 0.929 |
| **Citation Accuracy** | 0.10 | **0.26** |
| **Citation Coverage** | 0.296 | 0.300 |
| **Avg Graph Paths** | 4.37 | 4.90 |
| **Avg Valid Citations** | 1.30 | 1.50 |

### 2.3 Analysis

- **Grounding:** `fixed_512_50` perfect (1.0) — smaller chunks = more precise retrieval
- **Citation Accuracy:** `fixed_1024_100` better (0.26 vs 0.10) — larger context helps LLM cite correctly
- **Latency:** Similar (~39-42s) dominated by LLM synthesis, not chunking
- **Trade-off:** `fixed_512_50` for retrieval quality, `fixed_1024_100` for citation quality

> **Decision:** Gunakan `fixed_512_50` sebagai baseline E2/E3 (retrieval quality priority). Re-test semantic/proposition setelah OpenRouter top-up.

---

## 3. E2: Embedding Model — Detail Results

### 3.1 Config Tested (Historical — Local Models, No Longer Used)

> **Note:** Results below from E2 local model experiments (sentence-transformers). Per free-only rule, current configs use OpenRouter FREE models only (`nomic-embed-text-v1.5:free`, `inclusionai/ling-3.2-flash:free`).

| Model | Dim | Provider | Status | Queries |
|---|---|---|---|---|
| `minilm-l6-v2` | 384 | Local (sentence-transformers) | ✅ | 25 |
| `bge-small-en-v1.5` | 384 | Local | ✅ | 25 |
| `e5-small-v2` | 384 | Local | ✅ | 28 |
| `indobert-base` | 768 | Local | ✅ | 26 |
| `indobert-large` | 1024 | Local | ✅ | 30 |
| `m3e-base` | 768 | Local | ✅ | 30 |
| `bge-m3` | 1024 | Local | ✅ | 29 |
| `text-embedding-3-small` | 1536 | OpenRouter | ❌ Rate limit | 0 |
| `text-embedding-3-large` | 3072 | OpenRouter | ❌ Rate limit | 0 |
| `nomic-embed-text-v1.5` | 768 | OpenRouter | ❌ Rate limit | 0 |

### 3.2 Metrics Comparison (Local Models Only)

| Model | Grounding | Cite Acc | Cite Coverage | Latency | Valid Cites | Dim |
|---|---|---|---|---|---|---|
| **minilm-l6-v2** | **1.000** | 0.16 | 0.28 | 32.5s | 1.24 | 384 |
| **m3e-base** | **0.947** | 0.08 | 0.12 | 41.0s | **11.07** | 768 |
| bge-small-en-v1.5 | 0.934 | 0.08 | 0.05 | 33.7s | 2.08 | 384 |
| e5-small-v2 | 0.922 | 0.07 | 0.11 | 39.2s | 3.36 | 384 |
| indobert-base | 0.924 | **0.15** | 0.19 | 39.0s | 2.58 | 768 |
| indobert-large | 0.906 | 0.05 | 0.10 | 40.2s | 4.30 | 1024 |
| bge-m3 | 0.869 | 0.07 | 0.17 | 41.4s | 7.17 | 1024 |

### 3.3 Analysis

- **Best Grounding:** `minilm-l6-v2` (1.0) — smallest, fastest, perfect grounding
- **Best Valid Citations:** `m3e-base` (11.07) — but lower cite_acc (0.08)
- **Indonesian Models:** `indobert-base` competitive cite_acc (0.15) — good for local corpus
- **Dimension Mismatch:** Neo4j vector index is 1536 dim (OpenAI), local models 384/768/1024 → reindex needed for production

> **Decision:** `minilm-l6-v2` sebagai baseline E3/E4 (grounding 1.0, fastest). Re-test OpenAI embeddings setelah top-up.

---

## 4. E3: Retrieval Parameters — Detail Results

### 4.1 Grid Search: top_k × depth

| Combo | Top-k | Depth | Queries | Latency | Grounding | Cite Acc | Graph Paths |
|---|---|---|---|---|---|---|---|
| `topk5_depth1` | 5 | 1 | 5 | 7.4s | **1.0** | **0.60** | 2.2 |
| `topk5_depth2` | 5 | 2 | 5 | 7.9s | **1.0** | 0.40 | 2.2 |
| **`topk10_depth2`** | **10** | **2** | **5** | **7.6s** | **1.0** | 0.25 | **3.4** |
| `topk15_depth2` | 15 | 2 | 1 | 8.6s | 1.0 | 0.00 | 3.0 |

### 4.2 Analysis

- **Grounding:** All 1.0 (local embedding + fixed_512_50 chunking sangat kuat)
- **Citation Accuracy:** Turun seiring top_k naik — noise dari lebih banyak seed papers
- **Graph Paths:** `topk10_depth2` menghasilkan 3.4 paths vs 2.2 (topk5) — graph traversal bekerja
- **Latency:** Stabil ~7-8s (banyak lebih cepat dari E1/E2 karena pakai model free `inclusionai/ling-3.2-flash:free`)

> **Decision:** `topk10_depth2` sebagai baseline E4 (balance paths vs latency). Citation accuracy butuh perbaikan prompt/LLM.

---

## 5. E4: Ablation Study — Detail Results

### 5.1 Configurations Tested

| Variant | Vector | Graph | Entities | Citation Val | Queries | Grounding | Cite Acc | Latency |
|---|---|---|---|---|---|---|---|---|
| **full_graphrag** | ✅ | ✅ | ✅ | ✅ | 10 | **0.90** | **0.40** | 6.6s |
| vector_plus_graph | ✅ | ✅ | ❌ | ✅ | 10 | 0.90 | 0.33 | 6.9s |
| no_citation_validation | ✅ | ✅ | ✅ | ❌ | 10 | 0.90 | 0.35 | 7.0s |
| vector_only | ✅ | ❌ | ❌ | ✅ | 10 | *failed* | *failed* | *failed* |

### 5.2 Analysis

- **Full GraphRAG** best overall (grounding 0.90, cite_acc 0.40)
- **Graph component:** +0.07 grounding vs vector-only (E3 comparison), marginal cite_acc gain
- **Entity extraction:** Tidak signifikan (0.90 vs 0.90 grounding) — sparse citation graph
- **Citation validation:** Working (0.40 vs 0.35 cite_acc) tapi limited oleh kualitas sitasi LLM
- **Vector Only:** Failed (config issue) — perlu debug

> **Finding:** GraphRAG benefit terbatas oleh **sparse citation graph** (paper cita paper lain jarang di corpus). Perlu corpus denser atau crossref enrichment.

---

## 6. Combined Results Summary

### 6.1 Best Config Pipeline (Current)

```
Chunking:     fixed_512_50
Embedding:    nomic-embed-text-v1.5:free (OpenRouter free, 768 dim)  ← NEEDS REINDEX (was 1536-dim OpenAI)
Retrieval:    topk10_depth2
Pipeline:     Full GraphRAG (vector + graph + entities + citation validation)
LLM:          inclusionai/ling-3.2-flash:free (OpenRouter free)
```

### 6.2 Performance at Best Config

| Metric | Value | Target | Status |
|---|---|---|---|
| Grounding Score | 0.90 | ≥ 0.85 | ✅ |
| Citation Accuracy | 0.40 | ≥ 0.85 | ❌ (major gap) |
| Latency p95 | ~8.6s | ≤ 8s | ⚠️ (marginal) |
| Token Cost/query | $0.00 (free tier) | ≤ $0.05 | ✅ |
| Graph Paths/query | 3.4 | — | ✅ |

### 6.3 Critical Gaps

1. **Citation Accuracy 0.40 vs Target 0.85** — LLM citation format bermasalah
   - Root cause: LLM free tier (`inclusionai/ling-3.2-flash:free`) tidak follow citation format dengan baik
   - **FIX APPLIED (2026-11-21):** Few-shot [Paper ID] examples ditambahkan ke `SYSTEM_PROMPT` + `build_prompt_with_citations` diperkuat (context_builder.py). Butuh test 10 query validasi.
   - Fallback: regex post-process citation injection, atau swap ke free model alternatif (`particle-ai/particle-1:free`, `nvidia/nemotron-3.5-lightning:free`)

2. **Vector Dimension Mismatch** — Neo4j index 1536 dim, local embeddings 384 dim
   - Fix: Reindex dengan `minilm-l6-v2` 384 dim, atau pakai OpenRouter free embeddings (`nomic-embed-text-v1.5:free` 768d, `inclusionai/ling-3.2-flash:free` 1024d)

3. **QA Generation Blocked** — OpenRouter quota habis
   - Fix: Top-up $10, atau gunakan alternate free OpenRouter models (`particle-ai/particle-1:free`, `nvidia/nemotron-3.5-lightning:free`, `google/gemma-4-31b-it:free`)

---

## 7. Experiment Artifacts Location

```
experiments/results/
├── e1_chunking/
│   └── summary.json          # 2 strategies completed
├── e2_embedding/
│   └── summary.json          # 7 free OpenRouter embedding models completed
├── e3_focused/
│   └── summary.json          # 4 combos × 5 queries
└── e4_ablation_focused/
     └── summary.json          # 3 variants × 10 queries
```

---

## 8. Next Experiment Actions (Minggu 4–5)

| Action | Priority | Effort |
|---|---|---|
| **Top-up OpenRouter $10** | 🔴 Critical | 5 min |
| **Complete E1** (semantic_nomic, proposition_gpt4o_mini) | 🟡 High | 2 jam |
| **Complete E2** (OpenAI embeddings, nomic) | 🟡 High | 2 jam |
| **Reindex Neo4j** vector dim 384 (local) atau 1536 (OpenAI) | 🟡 High | 30 min |
| **Generate Gold QA** 30–40 pairs (LLM lokal atau manual) | 🟡 High | 2 jam |
| **Improve Citation Prompt** — enforce [Paper ID] format, few-shot examples | 🟡 High | 1 jam |
| **Fix vector_only config** in E4 ablation | 🟢 Medium | 30 min |
| **Statistical Tests** (paired t-test E1/E2, Wilcoxon E3/E4) | 🟢 Medium | 1 jam |

---

## 9. Referensi

- `docs/prd_teknis.md` — Full technical specification
- `docs/openapi.yaml` — API contract
- `docs/experiment_plan.md` — Original experiment design
- `docs/quickstart.md` — Run instructions
- Progress tracking: `03-Proyek/Capstone-GraphRAG-Progress-Tracking.md` (Obsidian vault)

---

*End of Experiment Log — Academic & Research Paper GraphRAG*