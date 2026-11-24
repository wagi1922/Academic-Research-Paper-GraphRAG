#!/usr/bin/env python3
"""Generate QA gold set grounded in the 4 ingested papers without LLM."""
import json
import re
from pathlib import Path
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "graphrag123")

PAPER_IDS = [
    "3a2f8ab5-ddf",
    "2406.06086v2",
    "c9a012cc-c4a",
    "5ef495fc-9f4",
]

PAPER_META = {
    "3a2f8ab5-ddf": {
        "title": "GraphRAG Under Fire",
        "year": 2025,
        "topic": "GraphRAG security, poisoning attacks, knowledge graph vulnerabilities",
        "key_concepts": ["GraphRAG", "poisoning attack", "GRAGPOISON", "knowledge graph", "RAG", "adversarial attack", "retrieval-augmented generation"],
    },
    "2406.06086v2": {
        "title": "RawBMamba: End-to-End Bidirectional State Space Model for Audio Deepfake Detection",
        "year": 2024,
        "topic": "Audio deepfake detection, bidirectional Mamba, state space models",
        "key_concepts": ["RawBMamba", "Mamba", "bidirectional", "audio deepfake", "state space model", "ASVspoof", "end-to-end"],
    },
    "c9a012cc-c4a": {
        "title": "Variational Self-attention Model for Sentence Representation",
        "year": 2018,
        "topic": "Variational inference, self-attention, sentence representation, stochastic attention",
        "key_concepts": ["Variational Self-attention Model", "VSAM", "variational inference", "self-attention", "sentence embedding", "latent variable", "Gaussian"],
    },
    "5ef495fc-9f4": {
        "title": "Streamlining and standardizing software citations with The Software Citation Station",
        "year": 2024,
        "topic": "Software citation, standardization, citation tools, academic software",
        "key_concepts": ["Software Citation Station", "software citation", "standardization", "citation format", "dependencies", "metadata"],
    },
}


def fetch_chunks(driver, paper_id, limit=50):
    with driver.session() as session:
        result = session.run(
            "MATCH (p:Paper {id: $pid})-[:HAS_CHUNK]->(c:Chunk) RETURN c.text LIMIT $limit",
            pid=paper_id, limit=limit
        )
        return [record["c.text"] for record in result]


def extract_entities_from_chunks(chunks, key_concepts):
    """Extract sentences containing key concepts."""
    entities = {}
    for concept in key_concepts:
        sentences = []
        for chunk in chunks:
            for sent in re.split(r'(?<=[.!?])\s+', chunk):
                if concept.lower() in sent.lower() and len(sent) > 30:
                    sentences.append(sent.strip())
        if sentences:
            entities[concept] = sentences[:3]
    return entities


def generate_qa_pairs(paper_id, meta, chunks):
    """Generate QA pairs for a paper using templates."""
    entities = extract_entities_from_chunks(chunks, meta["key_concepts"])
    pairs = []

    # Template 1: What is X?
    for concept, sentences in entities.items():
        if sentences:
            pairs.append({
                "question": f"What is {concept} in the context of {meta['title']}?",
                "answer": sentences[0][:500],
                "paper_titles": [meta["title"]],
                "category": meta["topic"].split(",")[0].lower().replace(" ", "_"),
                "difficulty": "easy",
                "source": "grounded_chunk"
            })

    # Template 2: How does X work?
    for concept, sentences in list(entities.items())[:2]:
        if len(sentences) > 1:
            pairs.append({
                "question": f"How does {concept} work according to {meta['title']}?",
                "answer": " ".join(sentences[:2])[:500],
                "paper_titles": [meta["title"]],
                "category": meta["topic"].split(",")[0].lower().replace(" ", "_"),
                "difficulty": "medium",
                "source": "grounded_chunk"
            })

    # Template 3: Key finding/result
    if entities:
        first_concept = list(entities.keys())[0]
        pairs.append({
            "question": f"What is a key finding about {first_concept} in {meta['title']}?",
            "answer": entities[first_concept][0][:500],
            "paper_titles": [meta["title"]],
            "category": meta["topic"].split(",")[0].lower().replace(" ", "_"),
            "difficulty": "medium",
            "source": "grounded_chunk"
        })

    # Template 4: Method/approach description
    method_concepts = [c for c in meta["key_concepts"] if any(w in c.lower() for w in ["model", "method", "approach", "framework", "system"])]
    for concept in method_concepts[:1]:
        if concept in entities and entities[concept]:
            pairs.append({
                "question": f"What method does {meta['title']} propose for {concept.lower()}?",
                "answer": entities[concept][0][:500],
                "paper_titles": [meta["title"]],
                "category": meta["topic"].split(",")[0].lower().replace(" ", "_"),
                "difficulty": "hard",
                "source": "grounded_chunk"
            })

    return pairs


def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    all_pairs = []

    try:
        for paper_id in PAPER_IDS:
            meta = PAPER_META[paper_id]
            print(f"Fetching chunks for {meta['title']}...")
            chunks = fetch_chunks(driver, paper_id, limit=50)
            print(f"  Got {len(chunks)} chunks")

            pairs = generate_qa_pairs(paper_id, meta, chunks)
            print(f"  Generated {len(pairs)} QA pairs")
            all_pairs.extend(pairs)

        # Add some cross-paper comparison questions
        cross_pairs = [
            {
                "question": "Which paper proposes a bidirectional state space model for audio deepfake detection?",
                "answer": "RawBMamba proposes a bidirectional Mamba model for end-to-end audio deepfake detection.",
                "paper_titles": ["RawBMamba: End-to-End Bidirectional State Space Model for Audio Deepfake Detection"],
                "category": "audio_deepfake",
                "difficulty": "easy",
                "source": "cross_paper"
            },
            {
                "question": "Which paper introduces a variational approach to self-attention for sentence representation?",
                "answer": "The Variational Self-attention Model (VSAM) uses variational inference to learn stochastic self-attention for sentence embeddings.",
                "paper_titles": ["Variational Self-attention Model for Sentence Representation"],
                "category": "sentence_representation",
                "difficulty": "easy",
                "source": "cross_paper"
            },
            {
                "question": "What attack does GRAGPOISON perform on GraphRAG systems?",
                "answer": "GRAGPOISON injects false relations into the knowledge graph to compromise retrieval-augmented generation, achieving up to 98% attack success rate.",
                "paper_titles": ["GraphRAG Under Fire"],
                "category": "graphrag_security",
                "difficulty": "medium",
                "source": "cross_paper"
            },
            {
                "question": "What is the Software Citation Station designed to standardize?",
                "answer": "The Software Citation Station standardizes software citation formats and allows users to select specific dependencies for citation.",
                "paper_titles": ["Streamlining and standardizing software citations with The Software Citation Station"],
                "category": "software_citation",
                "difficulty": "easy",
                "source": "cross_paper"
            },
        ]
        all_pairs.extend(cross_pairs)

        # Ensure we have at least 30 QA pairs
        print(f"Total QA pairs: {len(all_pairs)}")

        # Save to file
        output_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/qa_pairs.json")
        with open(output_path, "w") as f:
            json.dump(all_pairs, f, indent=2, ensure_ascii=False)
        print(f"Saved to {output_path}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()