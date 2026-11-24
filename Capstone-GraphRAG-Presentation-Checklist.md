---
title: "Capstone GraphRAG — Presentation Day Checklist"
tags: [capstone, graphrag, checklist, presentation-day]
updated: 2026-11-23
---

# Capstone GraphRAG — Presentation Day Checklist

**Tanggal Presentasi:** [ISI TANGGAL]
**Waktu:** [ISI WAKTU]
**Ruang:** [ISI RUANG]
**Tim:** 3 Orang (Ketua + 2 Anggota)

---

## 📅 H-1 (Besok Presentasi) — Persiapan Akhir

### Slide Deck & Assets
- [ ] **Marp render ke PDF** — `marp Capstone-GraphRAG-Presentation.marp.md --pdf --allow-local-files`
- [ ] **Marp render ke PPTX** — `marp Capstone-GraphRAG-Presentation.marp.md --pptx --allow-local-files` (backup)
- [ ] **Verifikasi PDF** — buka, cek semua slide, diagram muncul, font rapi, tidak terpotong
- [ ] **Diagram PNG 4 halaman** — sudah embedded di slide 5, 7, 8 (context, container, component, sequence)
- [ ] **Speaker Notes** — print fisik / simpan di tablet (Capstone-GraphRAG-Speaker-Notes.md)
- [ ] **Backup Slides** — 4 slide backup siap (Pydantic schema, contoh output, deployment, QA examples)
- [ ] **One-Pager Handout** — print 3 copies (Capstone-GraphRAG-OnePager.md → PDF)

### Demo Video
- [ ] **Render final** — 1080p, 3-5 menit, audio clear
- [ ] **Test play** — di laptop presentasi, fullscreen, volume OK
- [ ] **Backup copy** — di USB drive + Google Drive link

### Repository & Code
- [ ] **Tag release** — `git tag proposal-v1 && git push origin proposal-v1`
- [ ] **README updated** — setup instructions, architecture overview, run commands
- [ ] **CI passing** — ruff, black, mypy, pytest ≥ 70% (GitHub Actions green)
- [ ] **Demo script ready** — `scripts/demo_ingest_query.sh` untuk live demo jika perlu

### Laptop & Hardware
- [ ] **Laptop primary** — ThinkPad X13 Gen 1 (charger WAJIB bawa)
- [ ] **Laptop backup** — [Nama anggota 2] laptop (jika primary gagal)
- [ ] **HDMI/USB-C adapter** — bawa sendiri, jangan andalkan ruang
- [ ] **Mouse wireless** — untuk navigasi slide nyaman
- [ ] **Clicker/presenter remote** — jika ada
- [ ] **Power bank** — untuk clicker/phone hotspot
- [ ] **Internet backup** — phone hotspot 4G/5G (jika butuh live demo OpenRouter)

### Dokumen Fisik
- [ ] **Surat tugas / undangan** — print jika diperlukan
- [ ] **KTM / ID card** — semua anggota
- [ ] **Notebook + pen** — catat feedback dosen
- [ ] **Air mineral** — 1 botol per orang

---

## 🕐 Hari Presentasi (D-Day)

### Sebelum Masuk Ruang (T-30 menit)
- [ ] **Datang 30 menit sebelum** — setup hardware, test proyektor
- [ ] **Koneksi HDMI** — test display cloning/extend
- [ ] **Audio test** — jika demo video punya suara
- [ ] **Slide mode** — presenter view di laptop, fullscreen di proyektor
- [ ] **Timer set** — HP vibrate 20 menit (warning), 22 menit (wrap up)
- [ ] **Backup laptop ready** — buka PDF slide di laptop backup
- [ ] **Toilet break** — selesai sebelum masuk ruang

### Saat Presentasi
- [ ] **Salam & perkenalan** — 30 detik, kontak mata ke semua dosen
- [ ] **Pacing** — ~1.5 menit per slide teknis, 30 detik slide cover/kesimpulan
- [ ] **Pointer/laser** — gunakan saat explain diagram
- [ ] **Jawaban Q&A** — singkat dulu, detail jika dilanjutkan (lihat Speaker Notes)
- [ ] **Catat feedback** — delegasikan ke Anggota 2/3 saat presenter menjawab
- [ ] **Tutup formal** — "Terima kasih, siap menjawab pertanyaan lebih lanjut"

### Setelah Presentasi
- [ ] **Foto grup** — dengan dosen (jika diperbolehkan)
- [ ] **Kumpulkan handout** — yang belum diterima dosen
- [ ] **Debrief 15 menit** — tim: apa feedback, action items, siapa kerjakan
- [ ] **Update vault/kanban** — catat feedback dosen ke Obsidian
- [ ] **Commit slide final** — ke repo dengan tag `presentation-final`

---

## 🎯 Role Assignment (Tim 3 Orang)

| Role | Orang | Tugas |
|---|---|---|
| **Presenter Utama** | Anggota 1 (Ketua) | Presentasi slide, jawab Q&A teknis arsitektur |
| **Slide Operator** | Anggota 2 | Next/prev slide, pointer, catat feedback dosen |
| **Demo & Backup** | Anggota 3 | Siapin demo video, laptop backup, catat Q&A detail |

### Komunikasi Internal (Durante Presentasi)
- **Signal "butuh waktu"** — Anggota 2 tap bahu Anggota 1
- **Signal "jawab ini"** — Anggota 3 tulis di kertas/HP → tunjuk ke Anggota 1
- **Signal "waktu hampir habis"** — Anggota 2 tunjuk jam/HP

---

## 🚨 Kontingensi (Plan B)

| Skenario | Plan B |
|---|---|
| Laptop primary mati | Switch ke laptop backup (Anggota 2) — PDF sudah terbuka |
| Proyektor tidak keluar gambar | Presentasi tanpa slide (pakai whiteboard + speaker notes), handout sebagai referensi |
| Demo video tidak play | Screenshot demo video di slide backup, explain langkah-langkah |
| Internet mati (live demo) | Skip live demo, pakai screenshot/video offline |
| Dosen tanya di luar scope | "Itu di luar scope capstone 10 minggu, tapi menarik untuk penelitian lanjutan. Kami catat." |
| Waktu melebihi 20 menit | Skip slide non-kritis (tech stack, risk management), lompat ke kesimpulan |

---

## 📋 Post-Presentation Action Items (Template)

| Feedback Dosen | Action Item | PIC | Deadline |
|---|---|---|---|
| [Isi setelah presentasi] | | | |
| | | | |
| | | | |

---

## ✅ Final Verification (T-5 menit sebelum masuk)

```
Presenter (Anggota 1): "Slide ready? Demo ready? Notes ready? Timer ready? Handout ready? Team ready?"
Anggota 2: "Slide OK. Demo OK. Notes OK. Timer OK. Handout 3 copies OK."
Anggota 3: "Laptop backup OK. USB backup OK. Hotspot ready. Notebook pen ready."
Ketua: "GOOD TO GO. Masuk ruang."
```

---

## 📞 Emergency Contacts

| Keperluan | Kontak |
|---|---|
| Koordinator Capstone / Prodi | [Nomor/WA] |
| Dosen Pembimbing (Darurat) | [Nomor/WA] |
| IT Support Kampus (Proyektor) | [Nomor/WA] |
| Anggota Tim (Darurat) | [Nomor WA masing-masing] |

---

**Status: SIAP / BELUM SIAP** — Tandai setiap item

**Disiapkan oleh:** [Nama Ketua Tim]  
**Tanggal:** [Tanggal]  
**Tanda Tangan:** _______________