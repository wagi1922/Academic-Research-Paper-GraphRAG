#!/usr/bin/env python3
"""
Generate additional QA pairs from corpus using LLM.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Load OpenRouter key from backend .env
sys.path.insert(0, '/home/guard/Documents/perkuliahan/sem 7/Cap/backend')
from app.core.config import settings

import httpx


async def generate_qa_from_paper(paper_title: str, paper_abstract: str, categories: list) -> list:
    """Generate QA pairs for a paper using LLM via OpenRouter."""
    
    prompt = f"""Generate 3 diverse question-answer pairs from this academic paper.

Title: {paper_title}
Abstract: {paper_abstract}
Categories: {', '.join(categories)}

Create questions at different difficulty levels (easy, medium, hard) and categories:
- factoid (specific factual questions)
- methodology (how methods work)
- comparison (compare with other approaches)
- concept_explanation (explain a concept)

Output as JSON array with fields: question, answer, category, difficulty.
Answers should be concise, accurate, and grounded in the paper content."""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1500
                },
                timeout=60.0
            )
            
            print(f"  API Status: {response.status_code}")
            if response.status_code != 200:
                print(f"  API Error: {response.text}")
                return []
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"  Response preview: {content[:200]}")
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                qa_pairs = json.loads(json_match.group())
                for qa in qa_pairs:
                    qa["paper_titles"] = [paper_title]
                return qa_pairs
            else:
                print(f"  No JSON found in response")
    except Exception as e:
        print(f"  Error generating QA for {paper_title}: {e}")
        import traceback
        traceback.print_exc()
    
    return []


async def main():
    # Change to backend directory for imports
    os.chdir('/home/guard/Documents/perkuliahan/sem 7/Cap/backend')
    
    # Load existing QA pairs
    qa_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/qa_pairs.json")
    with open(qa_path) as f:
        existing_qa = json.load(f)
    
    print(f"Existing QA pairs: {len(existing_qa)}")
    
    # Load metadata
    meta_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/data/corpus/metadata.json")
    with open(meta_path) as f:
        metadata = json.load(f)
    
    # Get papers not yet covered
    covered_titles = set()
    for qa in existing_qa:
        for title in qa.get("paper_titles", []):
            covered_titles.add(title)
    
    # Select papers to generate QA for (not covered, prioritize diverse categories)
    papers_to_process = []
    for paper in metadata:
        if paper.get("title") not in covered_titles:
            papers_to_process.append(paper)
    
    print(f"Papers available for QA generation: {len(papers_to_process)}")
    
    # Process first 5 papers to get ~15 more QA pairs
    new_qa = []
    for i, paper in enumerate(papers_to_process[:5]):
        print(f"\nGenerating QA for paper {i+1}/5: {paper['title'][:60]}...")
        qa_pairs = await generate_qa_from_paper(
            paper["title"],
            paper.get("abstract", "")[:2000],
            paper.get("categories", [])
        )
        if qa_pairs:
            new_qa.extend(qa_pairs)
            print(f"  Generated {len(qa_pairs)} QA pairs")
        else:
            print(f"  Failed to generate QA")
        
        await asyncio.sleep(2)  # Rate limiting
    
    # Combine and save
    all_qa = existing_qa + new_qa
    print(f"\nTotal QA pairs: {len(all_qa)}")
    
    with open(qa_path, "w") as f:
        json.dump(all_qa, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to {qa_path}")


if __name__ == "__main__":
    asyncio.run(main())