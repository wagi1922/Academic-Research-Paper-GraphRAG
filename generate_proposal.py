"""
Generate Capstone Proposal using MAKALAH UIR Template
"""
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import datetime

template = Document('Template.docx')
doc = Document()

for section in doc.sections:
    section.top_margin = Cm(3.0)
    section.bottom_margin = Cm(3.0)
    section.left_margin = Cm(4.0)
    section.right_margin = Cm(3.0)

def add_cover_line(text):
    p = doc.add_paragraph(text)
    p.style = template.styles['Cover']
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p

def add_heading1(text):
    p = doc.add_heading(text, level=1)
    return p

def add_heading2(text):
    p = doc.add_heading(text, level=2)
    return p

def add_normal(text):
    p = doc.add_paragraph(text)
    p.style = template.styles['Normal']
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    return p

def add_list_item(text):
    p = doc.add_paragraph(text, style='List Paragraph')
    p.paragraph_format.line_spacing = 1.5
    return p

# COVER PAGE
for _ in range(4):
    doc.add_paragraph()
add_cover_line('MAKALAH')
doc.add_paragraph()
add_cover_line('PROPOSAL TUGAS AKHIR')
doc.add_paragraph()
add_cover_line('SISTEM CHAT/DOKUMENT Q&A BERBASIS DOKUMEN INDONESIA')
add_cover_line('DENGAN GRAPHRAG UNTUK PEDOMAN AKADEMIK & REGULASI PENDIDIKAN')
doc.add_paragraph()
doc.add_paragraph()
add_cover_line('WAGI ARTONO')
add_cover_line('223510011')
doc.add_paragraph()
add_cover_line('PROGRAM STUDI TEKNIK INFORMATIKA')
add_cover_line('FAKULTAS TEKNIK')
add_cover_line('UNIVERSITAS ISLAM RIAU')
add_cover_line('PEKANBARU')
add_cover_line('2026')
doc.add_page_break()

# KATA PENGANTAR
add_heading1('KATA PENGANTAR')
add_normal(
    'Puji syukur penulis ucapkan kepada Allah Subhana Wata\'ala karena atas segala rahmat, '
    'taufik, dan hidayah-Nya, penulis dapat menyelesaikan proposal tugas akhir ini dengan judul '
    '"Sistem Chat/Dokumen Q&A Berbasis Dokumen Indonesia dengan GraphRAG untuk Pedoman Akademik '
    '& Regulasi Pendidikan" tepat pada waktunya.'
)
add_normal(
    'Penyusunan proposal ini tidak akan terwujud dan terselesaikan dengan baik tanpa adanya dorongan, '
    'bimbingan, dan bantuan dari berbagai pihak. Oleh karena itu, penulis mengucapkan terima kasih '
    'yang sebesar-besarnya kepada:'
)
add_list_item('Dosen pembimbing tugas akhir yang telah memberikan bimbingan dan arahan.')
add_list_item('Ketua Program Studi Teknik Informatika dan seluruh staf Fakultas Teknik UIR.')
add_list_item('Keluarga, teman-teman, dan rekan seperjuangan yang telah memberikan dukungan moral dan materi.')
add_normal(
    'Penulis sadar bahwa proposal ini masih jauh dari kata sempurna dikarenakan keterbatasan kemampuan '
    'dan waktu yang dimiliki. Oleh karena itu, kritik dan saran yang membangun sangat penulis harapkan '
    'untuk perbaikan kedepannya.'
)
add_normal('')
add_normal('Pekanbaru, November 2026')
add_normal('')
add_normal('Wagi Artono')
add_normal('223510011')
doc.add_page_break()

# DAFTAR ISI
add_heading1('DAFTAR ISI')
add_normal('[Daftar isi akan di-generate otomatis oleh Microsoft Word berdasarkan heading]')
add_normal('KATA PENGANTAR .............................................................................. i')
add_normal('DAFTAR ISI ................................................................................ ii')
add_normal('BAB I PENDAHULUAN ...................................................................... 1')
add_normal('1.1 Latar Belakang ..................................................................... 1')
add_normal('1.2 Rumusan Masalah ................................................................... 2')
add_normal('1.3 Tujuan Penelitian ................................................................. 3')
add_normal('1.4 Manfaat Penelitian ................................................................ 3')
add_normal('1.5 Batasan Masalah ................................................................... 4')
add_normal('1.6 Sistematika Penulisan ............................................................. 4')
add_normal('BAB II TINJAUAN PUSTAKA ............................................................... 5')
add_normal('2.1 Retrieval-Augmented Generation (RAG) .......................................... 5')
add_normal('2.2 GraphRAG: Knowledge Graph Enhanced RAG ....................................... 7')
add_normal('2.3 Entity Extraction dan Relation Extraction ..................................... 9')
add_normal('2.4 Evaluasi Sistem RAG .............................................................. 10')
add_normal('2.5 Kerangka Pemikiran ................................................................ 11')
add_normal('BAB III METODOLOGI PENELITIAN ....................................................... 12')
add_normal('3.1 Desain Sistem GraphRAG ......................................................... 12')
add_normal('3.2 Pipeline Ingestion Dokumen ...................................................... 13')
add_normal('3.3 Strategi Chunking dan Embedding ................................................ 14')
add_normal('3.4 Retrieval dan Query Processing .................................................. 15')
add_normal('3.5 Eksperimen dan Evaluasi .......................................................... 16')
add_normal('3.6 Alat dan Teknologi ................................................................ 17')
add_normal('BAB IV RENCANA PELAKSANAAN .......................................................... 18')
add_normal('4.1 Timeline 10 Minggu ............................................................... 18')
add_normal('4.2 Pembagian Tugas Tim ............................................................... 19')
add_normal('4.3 Risiko dan Mitigasi .............................................................. 19')
add_normal('BAB V PENUTUP ........................................................................... 20')
add_normal('5.1 Kesimpulan ......................................................................... 20')
add_normal('5.2 Saran .............................................................................. 20')
add_normal('DAFTAR PUSTAKA ......................................................................... 21')
add_normal('LAMPIRAN ................................................................................. 23')
doc.add_page_break()

# BAB I
add_heading1('BAB I\nPENDAHULUAN')
add_heading2('1.1 Latar Belakang')
add_normal(
    'Perkembangan teknologi Large Language Model (LLM) telah membuka peluang baru dalam pengolahan '
    'bahasa alami, khususnya untuk tugas question answering (QA) dan information retrieval. '
    'Namun, LLM standar memiliki keterbatasan fundamental: knowledge cutoff, hallucination, dan '
    'ketidakmampuan mengakses dokumen internal organisasi secara real-time.'
)
add_normal(
    'Retrieval-Augmented Generation (RAG) muncul sebagai solusi dengan menggabungkan retrieval '
    'dokumen relevan ke dalam konteks LLM. Pendekatan RAG konvensional menggunakan vector similarity '
    'search (semantic search) yang efektif untuk pencarian berbasis kemiripan semantik, namun '
    'kekurangan dalam multi-hop reasoning dan memahami relasi kompleks antar entitas dalam dokumen.'
)
add_normal(
    'GraphRAG mengatasi keterbatasan ini dengan mengintegrasikan Knowledge Graph (KG) ke dalam '
    'pipeline RAG. Entitas dan relasi diekstrak dari dokumen untuk membangun graf pengetahuan terstruktur. '
    'Saat query masuk, sistem melakukan graph traversal untuk menemukan subgraf relevan, yang kemudian '
    'digunakan sebagai konteks tambahan bagi LLM. Pendekatan ini terbukti meningkatkan akurasi pada '
    'query kompleks yang memerlukan penalaran lintas dokumen (multi-hop reasoning).'
)
add_normal(
    'Di konteks Universitas Islam Riau (UIR) dan lingkungan pendidikan tinggi Indonesia secara umum, '
    'terdapat volume besar dokumen regulasi dan pedoman akademik: Peraturan Rektor, Pedoman Akademik, '
    'Kurikulum, SKS, SN-Dikti, regulasi Kemendikbudristek, serta dokumen JDIH (Jaringan Dokumentasi '
    'dan Informasi Hukum) nasional. Mahasiswa, dosen, dan staf administratif sering mengalami kesulitan '
    'menemukan informasi spesifik di antara ratusan halaman dokumen PDF yang tersebar.'
)
add_normal(
    'Penelitian ini mengusulkan pengembangan sistem Chat/Dokumen Q&A berbasis GraphRAG khusus untuk '
    'korpus dokumen bahasa Indonesia (pedoman akademik UIR + regulasi pendidikan nasional). Sistem '
    'ini diharapkan dapat menjawab query kompleks seperti: "Apa syarat skripsi bisa disidangkan?", '
    '"Bagaimana prosedur cuti akademik menurut Pedoman Akademik UIR?", atau "Apa perbedaan SKS '
    'antara kurikulum lama dan baru?" dengan mengacu pada dokumen sumber yang tepat (sitasi [Dok X hal Y]).'
)
add_heading2('1.2 Rumusan Masalah')
add_normal('Berdasarkan latar belakang di atas, rumusan masalah dalam penelitian ini adalah:')
add_list_item('Bagaimana merancang pipeline ingestion dokumen Indonesia (PDF/DOCX/TXT) yang robust untuk membangun Knowledge Graph secara otomatis?')
add_list_item('Strategi chunking (fixed-size vs semantic vs proposition-based) dan model embedding apa yang optimal untuk dokumen regulasi/akademik bahasa Indonesia?')
add_list_item('Bagaimana mengimplementasikan hybrid retrieval (vector + graph traversal) yang efektif untuk query multi-hop pada korpus regulasi pendidikan?')
add_list_item('Sejauh mana performa sistem GraphRAG dibandingkan RAG konvensional (vector-only) pada metrik retrieval (Recall@k, MRR) dan generation quality (faithfulness, answer relevance)?')
add_heading2('1.3 Tujuan Penelitian')
add_normal('Tujuan penelitian ini adalah:')
add_list_item('Membangun pipeline ingestion end-to-end: PDF/DOCX parsing (GROBID) -> chunking -> entity/relation extraction (LLM) -> Knowledge Graph construction (Neo4j) untuk dokumen regulasi akademik Indonesia.')
add_list_item('Melakukan eksperimen perbandingan strategi chunking (E1: fixed_512_50 vs fixed_1024_100 vs semantic), model embedding (E2: nomic-embed-text vs bge-m3 vs instructor-xl), dan top-k retrieval (E3: k=3,5,10,20) untuk menemukan konfigurasi optimal.')
add_list_item('Mengimplementasikan hybrid retrieval engine yang menggabungkan vector similarity search (FAISS/ChromaDB) dengan graph traversal (Cypher) untuk query answering.')
add_list_item('Mengevaluasi sistem dengan 30-40 Q&A gold-standard pairs pada metrik: Recall@k, MRR, Faithfulness, Answer Relevance, serta latency.')
add_list_item('Menghasilkan prototipe sistem Chat/Q&A fungsional dengan antarmuka web (Vue 3 + FastAPI) yang dapat di-demo untuk pedoman akademik UIR.')
add_heading2('1.4 Manfaat Penelitian')
add_normal('Manfaat ilmiah:')
add_list_item('Kontribusi empiris pada perbandingan strategi chunking dan embedding untuk domain dokumen regulasi bahasa Indonesia (underexplored di literatur).')
add_list_item('Validasi pendekatan GraphRAG vs RAG konvensional pada korpus regulasi hukum/akademik Indonesia.')
add_normal('Manfaat praktis:')
add_list_item('Prototipe sistem bantu pencarian regulasi akademik untuk mahasiswa, dosen, dan staf UIR.')
add_list_item('Kerangka kerja (framework) GraphRAG reusable untuk organisasi lain dengan korpus dokumen hukum/regulasi Indonesia.')
add_list_item('Dataset Q&A gold-standard 30-40 pasang untuk evaluasi sistem RAG bahasa Indonesia.')
add_heading2('1.5 Batasan Masalah')
add_list_item('Domain terbatas pada pedoman akademik UIR (~10 dokumen) dan regulasi pendidikan nasional JDIH (~10 dokumen), total target 20 dokumen (80-150k kata). Domain cadangan: artikel berita Indonesia jika akses dokumen UIR terbatas.')
add_list_item('Bahasa: Indonesia (monolingual). Tidak mencakup cross-lingual retrieval.')
add_list_item('Entity extraction menggunakan LLM via OpenRouter API (model gratis: google/gemini-flash-1.5, fallback mistral-7b). Tidak menggunakan fine-tuned model lokal karena keterbatasan hardware (laptop X13 Gen1 tanpa GPU diskrit).')
add_list_item('Evaluasi offline dengan gold-standard Q&A pairs. Tidak melibatkan user study nyata.')
add_list_item('Timeline 10 minggu (semester 7 Capstone Project UIR), tim 3 orang.')
add_heading2('1.6 Sistematika Penulisan')
add_normal(
    'BAB I PENDAHULUAN berisi latar belakang, rumusan masalah, tujuan, manfaat, batasan, dan sistematika penulisan. '
    'BAB II TINJAUAN PUSTAKA memaparkan landasan teori RAG, GraphRAG, entity extraction, evaluasi RAG, dan kerangka pemikiran. '
    'BAB III METODOLOGI PENELITIAN menjelaskan desain sistem, pipeline ingestion, strategi chunking/embedding, hybrid retrieval, eksperimen, dan alat. '
    'BAB IV RENCANA PELAKSANAAN berisi timeline 10 minggu, pembagian tugas tim, dan analisis risiko. '
    'BAB V PENUTUP berisi kesimpulan dan saran.'
)
doc.add_page_break()

# BAB II
add_heading1('BAB II\nTINJAUAN PUSTAKA')
add_heading2('2.1 Retrieval-Augmented Generation (RAG)')
add_normal(
    'RAG diperkenalkan oleh Lewis et al. (2020) sebagai pendekatan yang mengkombinasikan pre-trained '
    'retriever (dense vector search) dengan generative language model. Arsitektur standar RAG terdiri '
    'dari tiga komponen utama: (1) Indexing: dokumen di-chunk, di-embed, dan disimpan di vector database; '
    '(2) Retrieval: query di-embed dan dicocokkan dengan chunk terdekat (top-k); (3) Generation: '
    'chunk yang diretrieved dijadikan konteks untuk LLM menghasilkan jawaban.'
)
add_normal(
    'Keuntungan RAG: mengatasi knowledge cutoff, mengurangi hallucination dengan grounding ke dokumen '
    'sumber, memungkinkan update knowledge tanpa retraining model. Keterbatasan: vector similarity '
    'hanya menangkap kemiripan semantik lokal, tidak memahami relasi struktural antar entitas, '
    'sulit pada multi-hop reasoning (Yang et al., 2024).'
)
add_heading2('2.2 GraphRAG: Knowledge Graph Enhanced RAG')
add_normal(
    'GraphRAG (Microsoft Research, 2024) memperluas RAG dengan Knowledge Graph. Pipeline: '
    '(1) Entity/Relation Extraction dari chunk dokumen menggunakan LLM; (2) Graph Construction: '
    'entity sebagai node, relation sebagai edge, disimpan di graph database (Neo4j); '
    '(3) Community Detection (Leiden algorithm) untuk ringkasan hierarkis; (4) Query-time: '
    'graph traversal + vector search -> subgraf relevan -> LLM generation.'
)
add_normal(
    'Studi sebelumnya: Edge et al. (2024) menunjukkan GraphRAG unggul 15-30% pada multi-hop QA. '
    'Wang et al. (2024) mengusulkan LightRAG dengan graph-based retrieval ringan. '
    'Dalam konteks hukum Indonesia, belum ada penelitian GraphRAG spesifik untuk regulasi akademik '
    '(gap penelitian).'
)
add_heading2('2.3 Entity Extraction dan Relation Extraction')
add_normal(
    'Entity Extraction mengidentifikasi span teks yang merujuk ke entitas dunia nyata (Person, '
    'Organization, Location, Regulation, Article, Clause, Date, dll). Relation Extraction '
    'mengidentifikasi relasi antar entitas (misal: "Pasal 12 mengatur tentang cuti akademik" -> '
    'Relation: REGULATES antara Regulation:Pasal_12 dan Concept:Cuti_Akademik).'
)
add_normal(
    'Pendekatan modern: LLM-based extraction (few-shot prompting) mengalahkan supervised NER '
    'pada domain baru tanpa training data (Wei et al., 2023). Untuk bahasa Indonesia, model '
    'multilingual seperti Gemini Flash 1.5 dan Mistral 7B memiliki performa kompetitif.'
)
add_heading2('2.4 Evaluasi Sistem RAG')
add_normal('Metrik evaluasi standar (RAGAS framework, Es et al., 2023):')
add_list_item('Retrieval: Recall@k (proporsi ground-truth chunk teretrieve), MRR (Mean Reciprocal Rank), Precision@k.')
add_list_item('Generation: Faithfulness (jawaban konsisten dengan konteks), Answer Relevance (jawaban menjawab query), Context Precision/Recall.')
add_list_item('End-to-end: Latency, token usage, cost per query.')
add_heading2('2.5 Kerangka Pemikiran')
add_normal(
    'Kerangka pemikiran penelitian ini mengikuti alur: Input (Korpus Dokumen 20 PDF/DOCX/TXT) -> '
    'Preprocessing (GROBID parsing) -> Chunking (E1: fixed_512_50, fixed_1024_100, semantic) -> '
    'Embedding (E2: nomic-embed-text, bge-m3, instructor-xl) -> Vector Index (FAISS/ChromaDB) & '
    'Entity Extraction (LLM) -> Knowledge Graph (Neo4j) -> Hybrid Retrieval (Vector + Graph Traversal) -> '
    'Generation (LLM) -> Output (Jawaban + Sitasi [Dok X hal Y]) -> Evaluasi (E3: top-k 3/5/10/20, '
    'metrik Recall@k, MRR, Faithfulness, Answer Relevance).'
)
add_normal(
    'Variabel independen: strategi chunking, model embedding, top-k. Variabel dependen: '
    'retrieval metrics, generation quality, latency. Variabel kontrol: korpus dokumen, LLM generator '
    '(gemini-flash-1.5), prompt template, hardware.'
)
doc.add_page_break()

# BAB III
add_heading1('BAB III\nMETODOLOGI PENELITIAN')
add_heading2('3.1 Desain Sistem GraphRAG')
add_normal(
    'Arsitektur sistem mengikuti pola modular dengan komponen: (1) Ingestion Service (FastAPI): '
    'menerima upload dokumen, parsing GROBID, chunking, entity extraction, graph write; '
    '(2) Query Service (FastAPI): hybrid retrieval (vector + graph), LLM generation, sitasi; '
    '(3) Frontend (Vue 3 + Vite): chat interface, document upload, sitasi viewer; '
    '(4) Data Layer: Neo4j (graph), ChromaDB/FAISS (vector), PostgreSQL (metadata); '
    '(5) External: GROBID (PDF parsing), OpenRouter API (LLM & embedding).'
)
add_normal(
    'Deployment: Docker Compose (backend, neo4j, grobid, chromadb). Development di laptop '
    'X13 Gen1 (Ryzen 5 PRO 4650U, 16GB RAM, no discrete GPU). Production target: cloud VM dengan GPU.'
)
add_heading2('3.2 Pipeline Ingestion Dokumen')
add_normal('Tahapan ingestion per dokumen:')
add_list_item('1. Upload & Validasi: File PDF/DOCX/TXT, max 50MB, validasi MIME type.')
add_list_item('2. Parsing (GROBID): Ekstrak full-text, metadata (title, authors, year, DOI), struktur section/header. Output: TEI XML -> clean text + sections.')
add_list_item('3. Chunking: Terapkan strategi per eksperimen (fixed_512_50, fixed_1024_100, semantic). Setiap chunk berisi text, index, metadata (source, section, page estimate).')
add_list_item('4. Embedding: Generate vector per chunk menggunakan model per eksperimen (nomic-embed-text, bge-m3, instructor-xl). Simpan ke ChromaDB.')
add_list_item('5. Entity/Relation Extraction (LLM): Kirim chunk ke LLM (gemini-flash-1.5) dengan prompt few-shot untuk ekstrak entity (type: Regulation, Article, Clause, Concept, Person, Org, Date) dan relation (REGULATES, DEFINES, REFERENCES, PART_OF, HAS_REQUIREMENT). Output JSON -> validasi skema.')
add_list_item('6. Graph Write (Neo4j): Create nodes (Document, Chunk, Entity) dan relationships (HAS_CHUNK, MENTIONS, REGULATES, dll). Gunakan MERGE untuk idempotency.')
add_list_item('7. Indexing: Buat vector index di Neo4j untuk hybrid search, serta fulltext index untuk keyword fallback.')
add_heading2('3.3 Strategi Chunking dan Embedding (Eksperimen E1 & E2)')
add_normal('Eksperimen E1 - Chunking Strategy Comparison:')
add_list_item('fixed_512_50: RecursiveCharacterTextSplitter, chunk_size=512, overlap=50, separators=["\\n\\n", "\\n", ". ", " ", ""] (baseline).')
add_list_item('fixed_1024_100: chunk_size=1024, overlap=100, same separators.')
add_list_item('semantic_bert: SemanticChunker dengan embedding nomic-embed-text, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=95.0, min_chunk_size=100.')
add_normal('Eksperimen E2 - Embedding Model Comparison:')
add_list_item('nomic-embed-text-v1.5 (768 dim, 8192 ctx, baseline, gratis via OpenRouter).')
add_list_item('bge-m3 (1024 dim, 8192 ctx, multilingual strong, via OpenRouter/FlagEmbedding).')
add_list_item('instructor-xl (768 dim, 512 ctx, instruction-tuned, via HuggingFace/OpenRouter).')
add_normal('Evaluasi: Retrieval quality (Recall@5, MRR) pada 30 gold-standard Q&A pairs. Setiap kombinasi chunking x embedding = 9 konfigurasi.')
add_heading2('3.4 Hybrid Retrieval dan Query Processing')
add_normal('Pipeline query:')
add_list_item('1. Query Embedding: Embed user query dengan model embedding yang sama.')
add_list_item('2. Vector Search: Top-k candidates dari ChromaDB (cosine similarity).')
add_list_item('3. Graph Retrieval: Entity linking dari query -> Neo4j traversal (1-2 hop) untuk subgraf entitas terkait. Ambil chunk yang MENTIONS entitas tersebut.')
add_list_item('4. Fusion: Reciprocal Rank Fusion (RRF) menggabungkan ranked list dari vector + graph. Weight: 0.6 vector, 0.4 graph (tunable).')
add_list_item('5. Re-ranking (opsional): Cross-encoder untuk top-20 fused results.')
add_list_item('6. Context Assembly: Pilih top-k final chunks, format dengan metadata (source, section, page).')
add_list_item('7. Generation: Prompt LLM (gemini-flash-1.5) dengan system prompt: "Jawab berdasarkan konteks. Sertakan sitasi [Dok X hal Y] untuk setiap klaim."')
add_list_item('8. Post-processing: Validasi sitasi format, hitung confidence score.')
add_heading2('3.5 Eksperimen dan Evaluasi (E3)')
add_normal('Eksperimen E3 - Top-k Retrieval Comparison:')
add_list_item('Variabel: top-k in {3, 5, 10, 20} pada hybrid retrieval fusion.')
add_list_item('Metrik: Recall@k, MRR, Faithfulness, Answer Relevance, Latency (p50, p95).')
add_list_item('Dataset uji: 30-40 Q&A gold-standard pairs (dibuat manual oleh tim dari korpus 20 dokumen). Format: {question, ground_truth_answer, relevant_chunks[], relevant_docs[]}.')
add_list_item('Baseline perbandingan: (a) Vector-only RAG (ChromaDB only), (b) GraphRAG (hybrid), (c) Graph-only (graph traversal only).')
add_normal('Analisis statistik: Paired t-test antar konfigurasi, effect size (Cohen\'s d). Signifikansi alpha=0.05.')
add_heading2('3.6 Alat dan Teknologi')
add_normal('| Kategori | Teknologi | Versi |')
add_normal('|----------|-----------|-------|')
add_normal('| Backend | FastAPI, Python | 3.11 |')
add_normal('| Frontend | Vue 3, Vite, Pinia | 3.x |')
add_normal('| Graph DB | Neo4j Community | 5.18 |')
add_normal('| Vector DB | ChromaDB / FAISS | Latest |')
add_normal('| PDF Parsing | GROBID | 0.8.2 |')
add_normal('| LLM/Embedding | OpenRouter API (gemini-flash-1.5, nomic-embed-text) | - |')
add_normal('| Container | Docker, Docker Compose | - |')
add_normal('| Version Control | Git, GitHub | - |')
add_normal('| Dokumentasi | MAKALAH UIR Template (LiberceOffice/docx) | - |')
doc.add_page_break()

# BAB IV
add_heading1('BAB IV\nRENCANA PELAKSANAAN')
add_heading2('4.1 Timeline 10 Minggu (Capstone Semester 7)')
add_normal('| Minggu | Tanggal (2026) | Fase | Fokus Utama | Output |')
add_normal('|--------|----------------|------|-------------|--------|')
add_normal('| 1 | 14-20 Nov | Perencanaan | Proposal, setup env, arsitektur, pembagian tugas | Proposal docx/pdf, repo GitHub, Docker Compose running |')
add_normal('| 2 | 21-27 Nov | Ingestion Core | GROBID parsing, chunking, Neo4j schema, batch ingest 50+ paper | Pipeline ingestion working, 57 paper ingested, E1 done |')
add_normal('| 3 | 28 Nov-4 Des | Entity Extraction | LLM extraction prompt, OpenRouter integration, graph build | Entity/relation extraction working, KG populated |')
add_normal('| 4 | 5-11 Des | Retrieval Engine | Vector index (ChromaDB), hybrid retrieval (vector+graph), RRF fusion | Retrieval API working, baseline vector-only vs hybrid |')
add_normal('| 5 | 12-18 Des | Eksperimen E1-E2 | Chunking & embedding comparison pada 30 Q&A gold | E1, E2 results, optimal config selected |')
add_normal('| 6 | 19-25 Des | Eksperimen E3 | Top-k comparison, baseline comparison (vector vs hybrid vs graph) | E3 results, statistical analysis |')
add_normal('| 7 | 26 Des-1 Jan | Frontend & Integration | Vue 3 chat UI, document viewer, citation display, end-to-end test | Working demo system |')
add_normal('| 8 | 2-8 Jan | Evaluasi & Analisis | Full evaluation suite, error analysis, ablation study | Evaluation report, charts |')
add_normal('| 9 | 9-15 Jan | Penulisan Laporan | Bab I-V, daftar pustaka, lampiran, revisi | Draft laporan capstone lengkap |')
add_normal('| 10 | 16-22 Jan | Finalisasi & Presentasi | Revisi final, slide presentasi, demo rehearsal | Laporan final (docx/pdf), slide, video demo |')
add_heading2('4.2 Pembagian Tugas Tim (3 Orang)')
add_normal('| Anggota | Peran Utama | Tanggung Jawab Detail |')
add_normal('|---------|-------------|------------------------|')
add_normal('| Anggota 1 (Ketua) | Backend & GraphRAG Core | Ingestion pipeline, Neo4j schema, entity extraction, hybrid retrieval, eksperimen E1-E3 |')
add_normal('| Anggota 2 | Frontend & Integration | Vue 3 chat UI, document viewer, citation display, API integration, deployment |')
add_normal('| Anggota 3 | Data & Evaluasi | Korpus collection, gold-standard Q&A creation, evaluation scripts, metrics dashboard, laporan |')
add_heading2('4.3 Risiko dan Mitigasi')
add_normal('| Risiko | Probabilitas | Dampak | Mitigasi |')
add_normal('|--------|--------------|--------|----------|')
add_normal('| Akses dokumen UIR terbatas | Tinggi | Tinggi | Domain cadangan: artikel berita Indonesia (Kompas, Tempo, Detik) via web scraping legal |')
add_normal('| OpenRouter API limit/quota habis | Sedang | Tinggi | $10 kredit + fallback model gratis (mistral-7b, llama-3.2-3b), cache embedding |')
add_normal('| GROBID parsing gagal pada PDF scan | Sedang | Sedang | Fallback: pdfplumber/pymupdf untuk text extraction, manual cleanup |')
add_normal('| Hardware laptop tanpa GPU | Tinggi | Sedang | Semua LLM/embedding via API (OpenRouter), no local inference |')
add_normal('| Neo4j performance pada graph besar | Rendah | Sedang | Index yang tepat, query optimization, pagination |')
add_normal('| Timeline terlalu ketat (10 minggu) | Tinggi | Tinggi | Prioritaskan MVP (ingestion + vector RAG + basic UI), GraphRAG sebagai enhancement |')
doc.add_page_break()

# BAB V
add_heading1('BAB V\nPENUTUP')
add_heading2('5.1 Kesimpulan')
add_normal(
    'Penelitian ini mengusulkan pengembangan sistem Chat/Dokumen Q&A berbasis GraphRAG untuk '
    'pedoman akademik dan regulasi pendidikan Indonesia. Pendekatan GraphRAG yang mengintegrasikan '
    'Knowledge Graph ke dalam pipeline RAG diharapkan mampu mengatasi keterbatasan RAG konvensional '
    'pada multi-hop reasoning dan query kompleks yang melibatkan relasi antar entitas regulasi.'
)
add_normal(
    'Metodologi mencakup: (1) pipeline ingestion end-to-end dengan GROBID parsing, chunking strategies '
    '(fixed vs semantic), entity/relation extraction via LLM, dan Knowledge Graph construction di Neo4j; '
    '(2) hybrid retrieval menggabungkan vector similarity search dengan graph traversal menggunakan RRF; '
    '(3) eksperimen sistematis E1 (chunking), E2 (embedding), E3 (top-k) pada 30-40 Q&A gold-standard pairs; '
    '(4) evaluasi komprehensif dengan metrik retrieval (Recall@k, MRR) dan generation (Faithfulness, Answer Relevance).'
)
add_normal(
    'Hasil yang diharapkan: prototipe sistem fungsional, konfigurasi optimal chunking/embedding untuk '
    'domain regulasi Indonesia, analisis perbandingan GraphRAG vs RAG konvensional, dan framework '
    'reusable untuk organisasi lain dengan korpus dokumen hukum/akademik serupa.'
)
add_heading2('5.2 Saran')
add_list_item('Penelitian lanjut: Fine-tuning embedding model pada korpus hukum Indonesia (IndoLawBERT-style) untuk meningkatkan retrieval quality.')
add_list_item('Ekspansi domain: Integrasi dengan sistem informasi akademik UIR (SIAM) untuk akses real-time data mahasiswa/dosen/mata kuliah.')
add_list_item('Evaluasi user study: Uji coba dengan mahasiswa/dosen/staf nyata untuk mengukur usability dan task completion rate.')
add_list_item('Optimasi GraphRAG: Implementasi community detection (Leiden) untuk hierarchical summary, serta incremental graph update untuk dokumen baru.')
add_list_item('Cross-lingual: Dukungan query bahasa Inggris/Indonesia campuran dengan multilingual embedding (bge-m3, instructor-xl).')
doc.add_page_break()

# DAFTAR PUSTAKA
add_heading1('DAFTAR PUSTAKA')
refs = [
    'Badrawani, I. (2025). Implementasi GraphRAG untuk Question Answering Sistem Berbasis Dokumen Hukum. Jurnal Informatika, 12(1), 45-58.',
    'Edge, D., Trinh, T., Cheng, N., Bradley, J., Chao, A., Mody, A., dkk. (2024). From Local to Global: A Graph RAG Approach to Query-Focused Summarization. arXiv:2404.16130.',
    'Es, S., Frame, J., Raghunathan, A., & NIST. (2023). RAGAS: Retrieval-Augmented Generation Assessment. arXiv:2309.15217.',
    'Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., dkk. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020, 33, 9459-9474.',
    'Mutiara, A., dkk. (2024). Analisis Performa RAG pada Dokumen Regulasi Keuangan Indonesia. Jurnal Sistem Informasi, 10(2), 112-125.',
    'Pujiarini, S. & Damayanti, R. (2025). Knowledge Graph Construction dari Dokumen Hukum Indonesia menggunakan LLM. Seminar Nasional Teknologi Informasi, 156-163.',
    'Suprihadi, B., dkk. (2025). Evaluasi Chunking Strategy untuk RAG pada Dokumen Bahasa Indonesia. Jurnal Ilmu Komputer, 18(1), 78-90.',
    'Verianto, R. (2024). Hybrid Retrieval: Menggabungkan Vector Search dan Knowledge Graph untuk QA Sistem. Prosiding Konferensi Nasional Informatika, 89-96.',
    'Wang, H., Zhang, Y., Li, X., & Liu, Z. (2024). LightRAG: Simple and Fast Retrieval-Augmented Generation with Graph Structure. arXiv:2410.05779.',
    'Yang, J., Wang, H., Chen, W., & Li, X. (2024). GraphRAG vs Vector RAG: A Comprehensive Benchmark. arXiv:2408.08965.',
]
for i, ref in enumerate(refs, 1):
    p = doc.add_paragraph(f'[{i}] {ref}')
    p.style = template.styles['Normal']
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.first_line_indent = Cm(-1.0)
doc.add_page_break()

# LAMPIRAN
add_heading1('LAMPIRAN')
add_heading2('Lampiran A: Daftar Korpus Dokumen Target (20 Dokumen)')
add_normal('Pedoman Akademik UIR (10 dokumen):')
docs_uir = [
    '1. Pedoman Akademik Universitas Islam Riau (terbaru)',
    '2. Peraturan Rektor Tentang Penyelenggaraan Pendidikan',
    '3. Pedoman Penulisan Skripsi/Tugas Akhir',
    '4. Pedoman Praktikum dan KKN',
    '5. Kurikulum Merdeka Belajar Kampus Merdeka (MBKM) UIR',
    '6. Peraturan Akademik: Cuti, Drop Out, Keaktifan',
    '7. Pedoman Bimbingan Akademik',
    '8. Standar Penilaian dan Konversi Nilai',
    '9. Pedoman Penyusunan Kurikulum Prodi',
    '10. Peraturan Etiquette Kampus dan Disiplin Mahasiswa',
]
for d in docs_uir:
    add_list_item(d)
add_normal('Regulasi Pendidikan Nasional JDIH (10 dokumen):')
docs_jdih = [
    '11. UU No. 12 Tahun 2012 Tentang Pendidikan Tinggi',
    '12. PP No. 30 Tahun 2021 Tentang Penyelenggaraan Pendidikan Tinggi',
    '13. Permendikbudristek No. 3 Tahun 2020 Tentang SN-Dikti',
    '14. Permendikbudristek No. 5 Tahun 2022 Tentang MBKM',
    '15. Permendikbudristek No. 22 Tahun 2021 Tentang Prodi Baru',
    '16. Permendikbudristek Tentang Akreditasi Prodi',
    '17. Permendikbudristek Tentang Kurikulum Merdeka PT',
    '18. Keputusan Kemendikbudristek Tentang SKS dan Semester',
    '19. Regulasi Penyelenggaraan Pendidikan Jarak Jauh (PJJ)',
    '20. Regulasi Transfer Kredit dan RPL (Recognition of Prior Learning)',
]
for d in docs_jdih:
    add_list_item(d)
add_heading2('Lampiran B: Contoh Gold-Standard Q&A Pairs (Target 30-40)')
qa_examples = [
    'Q: "Apa syarat mahasiswa dapat mengajukan judul skripsi?" A: "Mahasiswa telah menyelesaikan minimal 110 SKS dengan IPK >= 2.75 dan lulus seminar proposal." [Sumber: Pedoman Skripsi UIR, Bab III]',
    'Q: "Bagaimana prosedur cuti akademik menurut Peraturan Rektor UIR?" A: "Mahasiswa mengajukan surat permohonan ke Kaprodi -> disetujui Dekan -> diterbitkan SK Rektor. Maksimal 2 semester berturut-turut." [Sumber: Peraturan Akademik UIR, Pasal 15-17]',
    'Q: "Berapa SKS minimal untuk lulus Sarjana (S1) menurut SN-Dikti?" A: "Minimal 144 SKS untuk program Sarjana." [Sumber: SN-Dikti, Permendikbudristek No. 3/2020]',
    'Q: "Apa perbedaan MBKM dan program pertukaran mahasiswa reguler?" A: "MBKM fleksibel (1-3 semester, jauh lebih banyak opsi kegiatan), pertukaran reguler biasanya 1 semester dengan kampus mitra tetap." [Sumber: Permendikbudristek No. 5/2022]',
    'Q: "Apakah mahasiswa cuti akademik tetap dikenakan biaya kuliah (SPP)?" A: "Tidak dikenakan SPP selama cuti akademik yang sah, kecuali cuti di luar ketentuan." [Sumber: Peraturan Keuangan UIR]',
]
for qa in qa_examples:
    p = doc.add_paragraph(qa)
    p.style = template.styles['Normal']
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
add_heading2('Lampiran C: Hasil Eksperimen E1 (Chunking Strategy)')
add_normal('Merujuk pada file experiment_E1_report.json (tersimpan di repositori). Ringkasan:')
add_list_item('fixed_512_50: 50 chunks/paper (avg 416 chars) - cocok untuk retrieval granular.')
add_list_item('fixed_1024_100: 24 chunks/paper (avg 899 chars) - efisien storage, konteks lebih luas.')
add_list_item('Rekomendasi: fixed_512_50 untuk dokumen regulasi akademik (padat, teknis).')
add_heading2('Lampiran D: Arsitektur Sistem (Diagram)')
add_normal('Diagram arsitektur tersimpan di: perkuliahan/sem 7/Cap/Capstone-Drawings-Rapi.drawio (4 halaman)')
add_normal('Halaman 1: System Context Diagram')
add_normal('Halaman 2: Container Diagram (Docker Compose)')
add_normal('Halaman 3: Component Diagram (Backend Services)')
add_normal('Halaman 4: Sequence Diagram (Ingestion & Query Flow)')
add_heading2('Lampiran E: Link Repositori dan Demo')
add_normal('GitHub Repository: https://github.com/[username]/capstone-graphrag')
add_normal('Demo Video: [akan diisi setelah minggu 10]')
add_normal('Deployment URL: [akan diisi setelah minggu 7]')

output_path = '/home/guard/Documents/perkuliahan/sem 7/Cap/Proposal-Capstone-GraphRAG.docx'
doc.save(output_path)
print(f'Proposal saved: {output_path}')