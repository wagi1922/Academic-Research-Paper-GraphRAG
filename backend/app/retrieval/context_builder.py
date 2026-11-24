"""
Context Builder Module
Assembles vector chunks and graph paths into structured prompt context.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from app.schemas.entities import ExtractedEntities, SourceCitation, GraphPathElement

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    vector_chunks: list[dict]
    graph_paths: list[dict]
    extracted_entities: ExtractedEntities
    seed_papers: list[dict]


class ContextBuilder:
    def __init__(
        self,
        max_vector_chunks: int = 8,
        max_graph_paths: int = 5,
        max_chunk_chars: int = 2000,
    ):
        self.max_vector_chunks = max_vector_chunks
        self.max_graph_paths = max_graph_paths
        self.max_chunk_chars = max_chunk_chars

    def build(self, context: RetrievalContext) -> dict:
        """Build structured context for LLM prompt."""
        return {
            "vector_chunks": self._format_vector_chunks(context.vector_chunks),
            "graph_paths": self._format_graph_paths(context.graph_paths),
            "extracted_entities": self._format_entities(context.extracted_entities),
            "seed_papers": self._format_seed_papers(context.seed_papers),
        }

    def _format_vector_chunks(self, chunks: list[dict]) -> str:
        if not chunks:
            return "Tidak ada chunk vektor yang relevan ditemukan."

        formatted = []
        for i, chunk in enumerate(chunks[:self.max_vector_chunks]):
            paper_id = chunk.get("paper_id", "unknown")
            text = chunk.get("text", chunk.get("abstract", ""))
            score = chunk.get("score", chunk.get("hybrid_score", 0))
            title = chunk.get("title", "")

            # Truncate if too long
            if len(text) > self.max_chunk_chars:
                text = text[:self.max_chunk_chars] + "..."

            formatted.append(
                f"[Chunk {i+1} | Paper ID: {paper_id} | Title: {title} | Score: {score:.3f}]\n{text}"
            )

        return "\n\n---\n\n".join(formatted)

    def _format_graph_paths(self, paths: list[dict]) -> str:
        if not paths:
            return "Tidak ada jalur graf yang relevan ditemukan."

        formatted = []
        for i, path in enumerate(paths[:self.max_graph_paths]):
            path_type = path.get("type", "unknown")
            nodes = path.get("nodes", [])
            relationships = path.get("relationships", [])

            path_str = f"[Graph Path {i+1} | Type: {path_type}]\n"

            # Build readable path
            if nodes and relationships:
                node_map = {n["id"]: n for n in nodes}
                for rel in relationships:
                    source = node_map.get(rel["source"], {})
                    target = node_map.get(rel["target"], {})
                    source_label = source.get("name", source.get("title", rel["source"]))
                    target_label = target.get("name", target.get("title", rel["target"]))
                    path_str += f"  {source_label} --[{rel['type']}]--> {target_label}\n"
            elif nodes:
                for n in nodes:
                    label = n.get("name", n.get("title", n.get("id", "unknown")))
                    path_str += f"  • {label} ({', '.join(n.get('labels', []))})\n"

            formatted.append(path_str.strip())

        return "\n\n---\n\n".join(formatted)

    def _format_entities(self, entities: Optional[ExtractedEntities]) -> str:
        if not entities:
            return "Tidak ada entitas teridentifikasi."
        
        parts = []
        if entities.authors:
            authors = ", ".join([f"{a.name} ({a.institution})" if a.institution else a.name for a in entities.authors[:10]])
            parts.append(f"Penulis: {authors}")
        if entities.concepts:
            concepts = ", ".join([f"{c.name} [{c.category}]" for c in entities.concepts[:15]])
            parts.append(f"Konsep: {concepts}")
        if entities.methods:
            methods = ", ".join([f"{m.name}" + (f" - {m.description[:50]}" if m.description else "") for m in entities.methods[:10]])
            parts.append(f"Metode: {methods}")
        if entities.datasets:
            datasets = ", ".join([f"{d.name}" + (f" ({d.domain})" if d.domain else "") for d in entities.datasets[:10]])
            parts.append(f"Dataset: {datasets}")
        if entities.relations:
            rels = []
            for r in entities.relations[:10]:
                rels.append(f"{r.source_name} --[{r.relation}]--> {r.target_name}")
            parts.append(f"Relasi: {'; '.join(rels)}")

        return "\n".join(parts) if parts else "Tidak ada entitas teridentifikasi."

    def _format_seed_papers(self, papers: list[dict]) -> str:
        if not papers:
            return "Tidak ada paper seed."

        formatted = []
        for p in papers[:5]:
            title = p.get("title", "Untitled")
            year = p.get("year", "")
            doi = p.get("doi", "")
            paper_id = p.get("paper_id", p.get("id", doi or "unknown"))
            score = p.get("score", p.get("hybrid_score", 0))
            year_str = f" ({year})" if year else ""
            doi_str = f" [DOI: {doi}]" if doi else ""
            id_str = f" [ID: {paper_id}]"
            formatted.append(f"• {title}{year_str}{doi_str}{id_str} (score: {score:.3f})")

        return "\n".join(formatted)


# Prompt Templates
SYSTEM_PROMPT = """Anda adalah research assistant yang menjawab pertanyaan berdasarkan KONTEKS yang diberikan.
Aturan:
1. Jawab HANYA berdasarkan informasi dalam KONTEKS.
2. Sertakan sitasi [Paper ID] untuk setiap klaim/fakta yang Anda sebutkan.
3. Gunakan Paper ID yang tepat seperti yang tertera di konteks (contoh: [10.48550/arXiv.2501.14050v4] atau [2406.06086v2]).
4. JANGAN gunakan angka urut [1], [2], [3] — gunakan Paper ID yang sebenarnya.
5. Jika informasi tidak ada dalam konteks, nyatakan: "Informasi tidak ditemukan dalam konteks yang diberikan."
6. Gunakan bahasa Indonesia yang formal dan akademik.
7. Jawab secara naratif, terstruktur, dan komprehensif.
8. Jika ada data kuantitatif, sebutkan angkanya dengan sitasi.

CONTOH FORMAT SITASI YANG BENAR:
Konteks berisi Paper ID: [10.48550/arXiv.2501.14050v4] (title: "GraphRAG for Academic Literature")
Paper ID: [2406.06086v2] (title: "Hybrid LSTM-Attention for Inflation Forecasting")

Pertanyaan: "Apa metode yang digunakan dalam paper GraphRAG?"
JAWABAN BENAR: "Paper [10.48550/arXiv.2501.14050v4] menggunakan pendekatan GraphRAG yang menggabungkan vector search dengan knowledge graph traversal untuk retrieval literaturr ilmiah."

Pertanyaan: "Berapa akurasi prediksi inflasi pada model hybrid?"
JAWABAN BENAR: "Model hybrid LSTM-Attention mencapai MSE 0.023 pada prediksi inflasi Indonesia [2406.06086v2]."

FORMAT SALAH (JANGAN LAKUKAN):
- [1], [2], [3] — angka urut tidak diizinkan
- [GraphRAG paper] — nama paper bukan Paper ID
- Tanpa sitasi — setiap klaim harus memiliki [Paper ID]"""

QUERY_PROMPT_TEMPLATE = """{system_prompt}

KONTEKS VECTOR CHUNKS:
{vector_chunks}

KONTEKS GRAPH PATHS:
{graph_paths}

ENTITAS TERIDENTIFIKASI:
{extracted_entities}

PAPER SEED (dari vector search):
{seed_papers}

PERTANYAAN: {user_query}

JAWABAN:"""


def build_prompt(context_dict: dict, user_query: str) -> str:
    """Build final prompt from context dictionary."""
    return QUERY_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        vector_chunks=context_dict.get("vector_chunks", ""),
        graph_paths=context_dict.get("graph_paths", ""),
        extracted_entities=context_dict.get("extracted_entities", ""),
        seed_papers=context_dict.get("seed_papers", ""),
        user_query=user_query,
    )


def build_prompt_with_citations(context_dict: dict, user_query: str, citation_style: str = "bracket") -> str:
    """Build prompt with explicit citation instructions."""
    base = build_prompt(context_dict, user_query)

    if citation_style == "bracket":
        citation_instruction = """

FORMAT SITASI WAJIB: Gunakan [Paper ID] di akhir SETIAP KALIMAT yang mengandung klaim/fakta dari paper. Paper ID harus PERSIS seperti di konteks (contoh: [10.48550/arXiv.2501.14050v4], [2406.06086v2]). LARANG: [1], [2], [3] atau nama paper.

CATATAN: Setiap kalimat jawaban WAJIB diakhiri [Paper ID]. Jika satu kalimat merujuk multiple paper, gunakan [ID1; ID2]. Jika tidak ada referensi untuk kalimat tersebut, JANGAN buat kalimat tersebut."""
    elif citation_style == "numbered":
        citation_instruction = "\n\nFORMAT SITASI: Gunakan nomor urut [1], [2], dll. sesuai urutan paper di daftar referensi."
    else:
        citation_instruction = ""

    return base + citation_instruction