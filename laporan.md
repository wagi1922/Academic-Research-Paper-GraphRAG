---
jenis_dokumen: "FORMAT LAPORAN MAKALAH UIR
Capstone Project"
judul: "Academic & Research Paper GraphRAG: Sistem RAG Tingkat Lanjut dengan Knowledge Graph untuk Literatur Ilmiah"
nama: "Wagi Artono"
nim: "223510011"
prodi: "Teknik Informatika"
fakultas: "Teknik"
universitas: "Universitas Islam Riau"
kota: "Pekanbaru"
tahun: "2026"
heading_case: title
---

<!-- ATURAN UMUM dari berkas format (berlaku untuk seluruh laporan):
  **Berdasarkan:** Buku Panduan Capstone Project UIR + Template.docx MAKALAH UIR
  ---
-->

# PENDAHULUAN

## Latar Belakang
Perkembangan kecerdasan buatan (Artificial Intelligence) dan pembelajaran mesin (Machine Learning) telah mendorong transformasi besar dalam cara peneliti dan praktisi mengakses, memproses, dan mensintesis pengetahuan dari literatur ilmiah. Volume publikasi ilmiah yang tumbuh secara eksponensial — ribuan paper baru diterbitkan setiap minggu di arXiv, IEEE Xplore, ACM Digital Library, dan repository lain — menciptakan tantangan fundamental: bagaimana menemukan, memahami, dan mengkorelasikan informasi lintas dokumen secara efisien.

Retrieval-Augmented Generation (RAG) standar berbasis vector search (semantic search) telah menjadi pendekatan dominan untuk menjawab pertanyaan berbasis dokumen. Namun, RAG vector-only memiliki keterbatasan krusial pada multi-hop query — pertanyaan kompleks yang membutuhkan penalaran lintas beberapa dokumen, seperti "Bandingkan performa LSTM vs Transformer pada dataset inflasi Indonesia" atau "Sebutkan penelitian yang mengusung metode Graph Neural Network untuk deteksi anomaly jaringan". Vector search saja tidak menangkap relasi struktural antar paper: sitasi (citation), metode yang dibagikan (shared methods), dataset yang sama, penulis yang sama, atau topik yang berkaitan.

GraphRAG (Graph-based RAG) menawarkan solusi dengan menggabungkan kekuatan vector search untuk pencarian semantik dengan knowledge graph untuk penalaran relasional. Knowledge graph merepresentasikan entitas (paper, penulis, konsep, metode, dataset) dan relasi antar entitas (CITES, USES_METHOD, USES_DATASET, ADDRESSES_TOPIC, WROTE) secara eksplisit, memungkinkan traversal multi-hop untuk mengumpulkan konteks kaya sebelum sintesis jawaban oleh LLM.

## Rumusan Masalah
Berdasarkan latar belakang di atas, rumusan masalah dalam proposal ini adalah:
1. Bagaimana merancang dan mengimplementasikan pipeline ingestion yang mampu mengekstrak entitas dan relasi dari paper akademik (PDF) secara otomatis dan menginjeksi ke dalam knowledge graph Neo4j?
2. Bagaimana mengembangkan pipeline GraphRAG hybrid yang menggabungkan vector search (semantic similarity) dan graph traversal (multi-hop reasoning) untuk menjawab multi-hop query pada literatur ilmiah?
3. Bagaimana membandingkan performa strategi chunking (fixed-size vs semantic vs proposition-based), model embedding (text-embedding-3-small vs nomic-embed-text vs IndoBERT), dan kedalaman retrieval (top-k dan graph depth) terhadap kualitas jawaban?
4. Bagaimana mengukur keunggulan GraphRAG dibandingkan vector-only RAG (ablation study) pada benchmark multi-hop QA dengan gold standard 30–40 pertanyaan?

## Tujuan Penulisan
Tujuan dari proposal capstone ini adalah:
1. Membangun pipeline ingestion end-to-end: PDF parsing (Grobid) → entity/relation extraction (LLM + Pydantic schema) → graph injection (Neo4j batch Cypher) → vector indexing (Neo4j Vector Index 1536-dim cosine).
2. Mengimplementasikan GraphRAG query pipeline: intent/entity extraction → hybrid seed node selection (vector + graph) → multi-hop subgraph expansion (1–3 hops) → context assembly → grounded LLM synthesis dengan sitasi valid.
3. Menyediakan REST API (FastAPI) untuk ingestion dan query, serta visualisasi subgraf (React Flow/D3.js ready).
4. Melakukan eksperimen sistematis E1–E4: chunking strategy, embedding model, retrieval depth, dan ablation GraphRAG vs vector-only.
5. Menghasilkan laporan capstone dan presentasi sesuai format MAKALAH UIR dari Template.docx.

# TINJAUAN PUSTAKA

## Landasan Teori / Konsep Dasar
Retrieval-Augmented Generation (RAG) diperkenalkan oleh Lewis et al. (2020) sebagai pendekatan yang mengkombinasikan retriever (dense vector search) dengan generator (LLM) untuk menjawab pertanyaan berbasis pengetahuan eksternal. Variasi RAG standar menggunakan embedding model (seperti text-embedding-3-small, nomic-embed-text) untuk mengubah query dan dokumen ke ruang vektor, kemudian mengambil top-k chunk paling relevan via cosine similarity.

Keterbatasan RAG vector-only: (1) Tidak ada pemahaman relasional eksplisit antar dokumen; (2) Sulit menjawab pertanyaan yang membutuhkan aggregasi informasi dari multiple hops; (3) Tidak ada traceability relasi sitasi/metode/dataset. Penelitian terbaru (Edge et al., 2024; Microsoft GraphRAG) menunjukkan penambahan knowledge graph meningkatkan performa pada multi-hop reasoning.

Knowledge graph akademik merepresentasikan paper, penulis, konsep, metode, dan dataset sebagai node, dengan relasi seperti CITES, WROTE, USES_METHOD, USES_DATASET, ADDRESSES_TOPIC. Semantic Scholar, OpenAlex, dan Microsoft Academic Graph (sebelum ditutup) adalah contoh skala besar. Pada skala proyek, Neo4j dengan APOC dan Vector Index menyediakan platform terpadu untuk graph traversal dan vector search dalam satu query Cypher.

Entity extraction dari paper akademik menggunakan LLM dengan schema terstruktur (Pydantic) memungkinkan ekstraksi konsisten: AuthorEntity, ConceptEntity, MethodEntity, DatasetEntity, dan RelationEntity. Prompt engineering dengan few-shot examples meningkatkan recall dan precision entitas teknis.

## Tinjauan Pustaka / Related Work
Arsitektur GraphRAG standar mengikuti alur: (1) Indexing: dokumen → chunk → entity extraction → graph construction → vector index; (2) Query: user question → intent/entity extraction → hybrid retrieval (vector + graph traversal) → context assembly → LLM synthesis. Microsoft GraphRAG (2024) menggunakan community detection untuk summarization skala besar; proyek ini menggunakan pendekatan multi-hop traversal dari seed nodes yang dipilih via vector similarity.

Evaluasi RAG melibatkan: (1) Retrieval metrics: Recall@k, MRR, nDCG; (2) Generation metrics: Faithfulness (grounding), Answer Relevance, Citation Accuracy; (3) End-to-end: Human evaluation atau LLM-as-judge pada gold QA set. Untuk multi-hop QA, dataset seperti HotpotQA, 2WikiMultihopQA, atau custom gold set diperlukan. Proyek ini membangun custom gold set 30–40 QA dari corpus 50–100 paper.

## Kerangka Pemikiran
Kerangka pemikiran proyek ini mengikuti alur: Input (PDF Paper Akademik) → Ingestion Pipeline (Parsing, Chunking, Entity Extraction, Graph Injection, Vector Indexing) → Knowledge Graph Neo4j (Nodes: Paper, Author, Concept, Method, Dataset; Edges: WROTE, CITES, ADDRESSES_TOPIC, USES_METHOD, USES_DATASET) → Query Pipeline (Intent Extraction, Hybrid Seed Selection, Multi-hop Traversal, Context Assembly, Grounded Synthesis) → Output (Jawaban Naratif + Sitasi + Subgraf Visualisasi). Evaluasi dilakukan melalui eksperimen E1–E4 dengan metrik retrieval (Recall@k, MRR) dan generation (Faithfulness, Answer Relevance, Citation Accuracy).

# PEMBAHASAN

## Arsitektur Sistem / Metodologi
Knowledge graph menggunakan model property graph dengan node dan relasi sebagai berikut:
- Node Paper: {id, title, abstract, year, doi, venue, keywords, embedding[1536]}
- Node Author: {id, name, institution}
- Node Concept: {id, name, category} (category: cs.LG, cs.CL, cs.CV, ecs.AI, dll)
- Node Method: {id, name, description}
- Node Dataset: {id, name, domain}

Relasi (directed):
- (:Author)-[:WROTE]->(:Paper)
- (:Paper)-[:CITES]->(:Paper)
- (:Paper)-[:ADDRESSES_TOPIC]->(:Concept)
- (:Paper)-[:USES_METHOD]->(:Method)
- (:Paper)-[:USES_DATASET]->(:Dataset)

Index: Vector Index pada Paper.embedding (1536-dim, cosine) dan Chunk.embedding (1536-dim, cosine). Fulltext index pada Paper.title, Paper.abstract, Chunk.text untuk hybrid keyword+vector search.

## Implementasi / Pipeline / Eksperimen
Pipeline ingestion diimplementasikan sebagai async workflow dengan langkah:
1. PDF Parsing: Grobid (container) ekstrak TEI XML dari PDF → title, abstract, authors, body paragraphs, references, DOI, year.
2. Chunking: FixedSizeChunker (chunk_size=512, overlap=50) dan SemanticChunker (langchain-experimental) sebagai alternatif untuk eksperimen E1.
3. Entity & Relation Extraction: LLM (OpenRouter: nvidia/nemotron-3-ultra-550b-a55b:free) dengan structured output Pydantic (ExtractedEntities: authors, concepts, methods, datasets, relations). Prompt few-shot 3 contoh.
4. Graph Injection: Batch Cypher MERGE untuk node dan CREATE untuk relasi, transaksi async batch 50 records.
5. Vector Indexing: Embedding chunk dan paper abstract via text-embedding-3-small (OpenRouter) → upsert ke Neo4j Vector Index.

Pipeline query meliputi:
1. Intent & Entity Extraction: LLM ekstrak kata kunci, entitas, dan tipe pertanyaan (factual, comparative, methodological).
2. Hybrid Seed Selection: Vector search (top-k=5) pada chunk + paper abstract embedding → seed paper IDs.
3. Multi-hop Graph Traversal: Dari seed papers, traverse relasi CITES, USES_METHOD, USES_DATASET, ADDRESSES_TOPIC, WROTE hingga depth=2 (configurable). Kumpulkan subgraph nodes + edges + paths.
4. Context Assembly: Gabungkan vector chunks (top-5) + graph paths (formatted sebagai natural language) + seed paper metadata.
5. Grounded Synthesis: LLM generate jawaban naratif dengan sitasi inline [Paper ID] yang traceable ke source chunks dan graph paths. Output: answer, sources[], graph_path[], extracted_entities, metadata.

REST API (FastAPI) menyediakan endpoint utama:
- POST /api/v1/papers/ingest — multipart upload PDF atau JSON {doi_list} → return job_id, status polling.
- GET /api/v1/papers/ingest/status/{job_id} — progress ingestion (parsed, entities_extracted, graph_injected, indexed).
- POST /api/v1/query — {query, top_k=5, depth=2} → {answer, sources[], graph_path[], extracted_entities, retrieval_metadata}.
- POST /api/v1/query/stream — Server-Sent Events untuk streaming answer.
- GET /api/v1/graph/visualize?paper_id={id}&depth=2 — subgraph JSON untuk React Flow/D3.js.

Stack teknologi utama:
- Backend: Python 3.11, FastAPI, Pydantic v2, asyncpg/asyncneo4j.
- Database: Neo4j 5.x (Community), APOC, Vector Index (native).
- PDF Parser: Grobid 0.8.x (Docker).
- LLM & Embedding: OpenRouter API (nvidia/nemotron-3-ultra-550b-a55b:free, text-embedding-3-small).
- Orchestration: Docker Compose (neo4j, backend, grobid).
- Testing: pytest (unit + integration), smoke tests parser/chunker/schema.
- Visualisasi: React Flow / D3.js untuk frontend demo (opsional).
- Eksperimen tracking: MLflow atau manual logging ke CSV/JSON.

## Rencana Eksperimen & Evaluasi
Proyek ini mengusulkan empat eksperimen sistematis (E1–E4) untuk mengevaluasi kontribusi setiap komponen GraphRAG terhadap kualitas jawaban multi-hop. Setiap eksperimen mengisolasi satu variabel independen sambil mempertahankan variabel kontrol konstan.

### E1: Chunking Strategy Comparison
Membandingkan tiga strategi chunking pada retrieval quality:
- Fixed-Size: chunk_size=512 tokens, overlap=50 (baseline).
- Semantic Chunker: langchain_experimental.SemanticChunker dengan embedding similarity threshold.
- Proposition-based: LLM ekstrak proposisi atomik per paragraf (mengikuti Chen et al., 2024).
Metrik: Retrieval Recall@5, Answer Faithfulness, Citation Accuracy pada gold set.

### E2: Embedding Model Comparison
Membandingkan model embedding pada vector search quality:
- text-embedding-3-small (OpenAI via OpenRouter, 1536-dim) — baseline produksi.
- nomic-embed-text-v1.5:free (OpenRouter free, 768-dim) — cost-free, online.
- inclusionai/ling-3.2-flash:free (OpenRouter free, 1024-dim) — cost-free, online.
Catatan: Dimension mismatch (1536 vs 768/1024) memerlukan index terpisah. Metrik: Retrieval Recall@5, MRR, latency.

### E3: Retrieval Depth Ablation
Variasi parameter retrieval:
- top-k vector: 3, 5, 10
- Graph depth: 1 hop, 2 hops, 3 hops
- Kombinasi: 3×3 = 9 konfigurasi
Metrik: Answer Relevance, Grounding Score, token usage, latency.

### E4: GraphRAG vs Vector-Only RAG (Ablation Study)
Perbandingan end-to-end pada 30–40 multi-hop QA gold standard:
- GraphRAG (full pipeline: vector + graph traversal + grounded synthesis).
- Vector-Only RAG: vector search chunks → LLM synthesis (tanpa graph traversal).
Metric utama: Faithfulness, Answer Correctness (LLM-as-judge), Citation Validity, Multi-hop Reasoning Score.
Gold set dibangun manual dari corpus: pertanyaan comparative, methodological, causal, dan temporal reasoning.

## Hasil Eksperimen / Analisis (opsional untuk proposal)
Proposal ini merupakan tahap perencanaan (Minggu 1-2). Hasil eksperimen akan diisi setelah pelaksanaan eksperimen E1–E4 pada Minggu 6-7. Rencana analisis meliputi: perbandingan metrik retrieval dan generation antar variasi eksperimen, analisis statistik signifikansi perbedaan, visualisasi hasil (chart, tabel), dan interpretasi temuan terhadap hipoteses penelitian.

# PENUTUP

## Kesimpulan
Proposal ini mengusulkan pengembangan Academic & Research Paper GraphRAG — sistem RAG tingkat lanjut yang menggabungkan vector search dan knowledge graph untuk menjawab multi-hop query pada literatur ilmiah. Sistem dirancang dengan arsitektur modular: ingestion pipeline (PDF → entities → graph → vector index), GraphRAG query pipeline (hybrid retrieval + multi-hop traversal + grounded synthesis), dan REST API untuk integrasi. Eksperimen E1–E4 dirancang untuk mengukur kontribusi setiap komponen (chunking, embedding, retrieval depth, graph vs vector) terhadap kualitas jawaban secara kuantitatif.

Hasil yang diharapkan: (1) Pipeline ingestion berfungsi end-to-end untuk 50–100 paper akademik; (2) GraphRAG query pipeline menjawab multi-hop query dengan grounding dan sitasi valid; (3) Temuan eksperimen menunjukkan keunggulan GraphRAG pada multi-hop reasoning dibanding vector-only RAG; (4) Laporan capstone dan presentasi lengkap sesuai standar UIR.

## Saran
1. Pengembangan lanjutan: Integrasi dengan Semantic Scholar / OpenAlex API untuk enrich metadata paper (citation count, venue rank, author h-index).
2. Skalabilitas: Evaluasi performa pada corpus 10.000+ paper dengan community detection (Leiden/Louvain) untuk hierarchical summarization (Microsoft GraphRAG style).
3. Domain adaptation: Fine-tuning embedding model pada corpus akademik Indonesia (IndoBERT-based) untuk meningkatkan retrieval pada paper berbahasa Indonesia.
4. Evaluasi human-in-the-loop: Rekrut dosen/mahasiswa untuk human evaluation pada gold set, melengkapi LLM-as-judge.

# DAFTAR PUSTAKA
Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. Advances in Neural Information Processing Systems, 33, 9459-9474.

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mochocki, M., ... & Wang, J. (2024). From Local to Global: A GraphRAG Approach to Query-Focused Summarization. arXiv preprint arXiv:2404.16130.

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention Is All You Need. Advances in Neural Information Processing Systems, 30.

Yang, Z., Qi, P., Zhang, S., Bengio, Y., Cohen, W., Salakhutdinov, R., & Manning, C. D. (2018). HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering. Proceedings of EMNLP 2018, 2369-2380.

Ho, X., Nguyen, A. K., Sugawara, S., & Aizawa, A. (2020). Constructing A Multi-hop QA Dataset for Comprehensive Evaluation of Reasoning Steps. Proceedings of COLING 2020, 6609-6625.

Chen, J., Lin, H., Han, X., & Sun, L. (2024). Proposition-based Chunking for Retrieval-Augmented Generation. arXiv preprint arXiv:2402.XXXX.

Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., ... & Stoyanov, V. (2019). RoBERTa: A Robustly Optimized BERT Pretraining Approach. arXiv preprint arXiv:1907.11692.

Wilie, B., Vincentio, K., Winata, G. I., Cahyawijaya, S., Li, X., Lin, Z., ... & Fung, P. (2020). IndoNLU: Benchmark and Resources for Evaluating Indonesian Natural Language Understanding. Proceedings of the 1st Conference of the Asia-Pacific Chapter of the Association for Computational Linguistics and the 10th International Joint Conference on Natural Language Processing, 843-857.

Klicpera, J., Bojchevski, A., & Günnemann, S. (2019). Predict then Propagate: Graph Neural Networks meet Personalized PageRank. Proceedings of ICLR 2019.

Neo4j Documentation. (2024). Vector Search and Graph Algorithms. Neo4j Developer Guide.

OpenAI. (2024). text-embedding-3-small Model Card. OpenAI Platform Documentation.

Nomic AI. (2024). nomic-embed-text: Long-context Embedding Model. Nomic AI Blog.

Fakultas Teknik, Universitas Islam Riau. (2023). Buku Pedoman Penulisan Tugas Akhir. Pekanbaru: UIR Press.

Fakultas Teknik, Universitas Islam Riau. (2024). Buku Panduan Capstone Project. Pekanbaru: UIR Press.

# LAMPIRAN
Lampiran A: System Blueprint — Academic & Research Paper GraphRAG (PDF teknis lengkap)
Lampiran B: Buku Panduan Capstone Project UIR (pedoman format, rubrik, struktur bab)
Lampiran C: Capstone-Drawings-Rapi.drawio (diagram arsitektur 4 halaman)
Lampiran D: Kode sumber backend (FastAPI, ingestion, query, retrieval modules)
Lampiran E: Docker Compose configuration (Neo4j, Backend, Grobid)
Lampiran F: Eksperimen plan detail (E1–E4 parameter grid, metrik, gold set template)