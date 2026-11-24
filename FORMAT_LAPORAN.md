# FORMAT LAPORAN MAKALAH UIR — Capstone Project

**Berdasarkan:** Buku Panduan Capstone Project UIR + Template.docx MAKALAH UIR

---

# BAB I PENDAHULUAN

## 1.1 Latar Belakang
Penjelasan latar belakang masalah yang mendasari pemilihan topik capstone. Mengapa topik ini penting, relevan dengan perkembangan teknologi, dan permasalahan yang ingin diselesaikan.

## 1.2 Rumusan Masalah
Daftar pertanyaan/permasalahan spesifik yang akan dijawab/diselesaikan dalam capstone ini. Ditulis sebagai poin-poin terstruktur.

## 1.3 Tujuan Penulisan
Tujuan konkret yang ingin dicapai. Diformulasikan sebagai "Tujuan penulisan ini adalah..." dan mencakup aspek kompetensi, metode, dan target.

# BAB II TINJAUAN PUSTAKA

## 2.1 Landasan Teori / Konsep Dasar
Penjelasan teori-teori, konsep, dan metode yang relevan dengan topik capstone. Termasuk definisi istilah kunci.

## 2.2 Tinjauan Pustaka / Related Work
Studi literatur dari paper/jurnal/penelitian terdahulu yang relevan. Perbandingan dengan pekerjaan yang sudah ada, gap yang diidentifikasi.

## 2.3 Kerangka Pemikiran
Diagram atau deskripsi konseptual yang menggambarkan hubungan variabel, alur proses, atau arsitektur sistem yang diusulkan.

# BAB III PEMBAHASAN

## 3.1 Arsitektur Sistem / Metodologi
Deskripsi detail arsitektur sistem, data model, pipeline, dan algoritma yang digunakan. Termasuk diagram arsitektur.

## 3.2 Implementasi / Pipeline / Eksperimen
Detail implementasi teknis: teknologi, tools, konfigurasi, langkah-langkah pipeline, parameter eksperimen.

## 3.3 Rencana Eksperimen & Evaluasi
Desain eksperimen: variabel independen/dependen, metrik evaluasi, baseline, prosedur pengujian.

### E1: Chunking Strategy Comparison
Perbandingan strategi chunking: fixed-size vs semantic vs proposition-based. Metrik: Recall@k, Faithfulness, Citation Accuracy.

### E2: Embedding Model Comparison
Perbandingan model embedding: text-embedding-3-small vs nomic-embed-text vs IndoBERT. Metrik: Recall@k, MRR, latency.

### E3: Retrieval Depth Ablation
Variasi top-k vector (3/5/10) dan graph depth (1/2/3 hops). Metrik: Answer Relevance, Grounding Score, latency.

### E4: GraphRAG vs Vector-Only RAG (Ablation Study)
Perbandingan end-to-end GraphRAG vs Vector-only pada multi-hop QA gold standard. Metrik: Faithfulness, Answer Correctness, Citation Validity.

## 3.4 Hasil Eksperimen / Analisis (opsional untuk proposal)
Jika sudah ada hasil awal, sertakan di sini. Untuk proposal, bagian ini bisa berisi rencana analisis.

# BAB IV PENUTUP

## 4.1 Kesimpulan
Ringkasan temuan utama, menjawab rumusan masalah, kontribusi capstone.

## 4.2 Saran
Saran untuk pengembangan lebih lanjut, keterbatasan, dan rekomendasi penelitian masa depan.

# DAFTAR PUSTAKA
Entri referensi dalam format APA (author, year). Daftar terurut alfabetis.

# LAMPIRAN
Lampiran A, B, C... (kode sumber lengkap, data mentah, output eksperimen tambahan, dll.)