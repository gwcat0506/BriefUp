"""
curriculum_catalog.py의 기존 하드코딩 데이터를 topic_curricula DB에 seed.
최초 1회 실행. 이미 있는 topic_key는 건너뜀.

실행:
  cd backend && source .venv/bin/activate && python seed_curricula.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from core.supabase import supabase
from agent.curriculum_catalog import CURRICULUM_CATALOG

# 각 챕터에 search_hints 추가 — 기존 catalog에는 없으므로 챕터 제목 기반으로 채움
SEARCH_HINTS: dict[str, list[dict]] = {
    "rag": [
        {"arxiv_query": "information retrieval dense retrieval 2024", "web_query": "keyword search vs semantic search explained"},
        {"arxiv_query": "text embeddings vector similarity search", "web_query": "text embeddings vector database beginner guide"},
        {"arxiv_query": "document chunking strategy retrieval augmented generation", "web_query": "RAG chunking strategies overlap explained"},
        {"arxiv_query": "HyDE hypothetical document embeddings reranking RAG", "web_query": "advanced RAG techniques HyDE reranking 2024"},
        {"arxiv_query": "retrieval augmented generation pipeline evaluation", "web_query": "build RAG pipeline from scratch tutorial"},
    ],
    "agent": [
        {"arxiv_query": "LLM agent ReAct reasoning acting framework", "web_query": "what is AI agent ReAct pattern explained"},
        {"arxiv_query": "LLM tool use function calling", "web_query": "LLM function calling tool use examples"},
        {"arxiv_query": "multi-agent systems LLM collaboration", "web_query": "multi-agent AI systems orchestration explained"},
        {"arxiv_query": "LLM agent memory long-term context management", "web_query": "AI agent memory management vector store"},
        {"arxiv_query": "LLM agent deployment production monitoring", "web_query": "deploy AI agent production best practices"},
    ],
    "llm": [
        {"arxiv_query": "transformer architecture self-attention mechanism", "web_query": "how transformer works GPT explained simply"},
        {"arxiv_query": "prompt engineering chain of thought few shot", "web_query": "prompt engineering techniques chain of thought"},
        {"arxiv_query": "fine-tuning LoRA vs retrieval augmented generation comparison", "web_query": "fine-tuning vs RAG when to use which"},
        {"arxiv_query": "LLM evaluation benchmark MMLU HumanEval", "web_query": "how to evaluate LLM performance benchmarks"},
    ],
    "quantum": [
        {"arxiv_query": "quantum mechanics superposition entanglement introduction", "web_query": "quantum mechanics superposition entanglement explained beginners"},
        {"arxiv_query": "qubit quantum gate circuit implementation", "web_query": "what is qubit quantum gate explained simply"},
        {"arxiv_query": "Shor algorithm Grover algorithm quantum speedup", "web_query": "Shor Grover quantum algorithm explained"},
        {"arxiv_query": "NISQ quantum error correction noise 2024", "web_query": "IBM Google quantum computer current status 2024"},
        {"arxiv_query": "quantum computing applications cryptography drug discovery", "web_query": "quantum computing future applications cryptography AI"},
    ],
    "invest": [
        {"arxiv_query": None, "web_query": "what is stock market share ownership explained"},
        {"arxiv_query": "financial statement analysis PER PBR ROE", "web_query": "how to read financial statements PER PBR ROE explained"},
        {"arxiv_query": "value investing growth investing returns comparison", "web_query": "value investing vs growth investing Warren Buffett"},
        {"arxiv_query": "ETF passive investing diversification portfolio", "web_query": "ETF investing diversification beginners guide"},
        {"arxiv_query": "behavioral finance loss aversion investor psychology", "web_query": "investment psychology fear greed behavioral economics"},
    ],
    "psych": [
        {"arxiv_query": "cognitive bias confirmation bias availability heuristic", "web_query": "cognitive biases list explained examples"},
        {"arxiv_query": "behavioral economics nudge loss aversion", "web_query": "behavioral economics nudge theory loss aversion"},
        {"arxiv_query": "Big Five personality traits personality psychology", "web_query": "Big Five personality traits OCEAN model explained"},
        {"arxiv_query": "social psychology conformity obedience Milgram", "web_query": "Milgram experiment conformity social psychology"},
        {"arxiv_query": "positive psychology PERMA wellbeing happiness", "web_query": "positive psychology PERMA model happiness science"},
    ],
    "philosophy": [
        {"arxiv_query": None, "web_query": "Socratic method maieutics philosophy explained"},
        {"arxiv_query": None, "web_query": "utilitarianism deontology virtue ethics comparison"},
        {"arxiv_query": None, "web_query": "existentialism Sartre Heidegger explained simply"},
        {"arxiv_query": None, "web_query": "epistemology Descartes Hume rationalism empiricism"},
        {"arxiv_query": "AI consciousness free will philosophical implications", "web_query": "AI consciousness Turing test Chinese room argument"},
    ],
    "startup": [
        {"arxiv_query": None, "web_query": "startup vs traditional business scalability explained"},
        {"arxiv_query": "product market fit measurement startup", "web_query": "product market fit how to find PMF startup"},
        {"arxiv_query": None, "web_query": "lean startup MVP build measure learn Eric Ries"},
        {"arxiv_query": "venture capital startup funding valuation", "web_query": "startup funding seed series A venture capital explained"},
        {"arxiv_query": "viral growth product growth hacking retention", "web_query": "growth hacking viral loop retention startup"},
    ],
    "health": [
        {"arxiv_query": "muscle hypertrophy progressive overload resistance training", "web_query": "how muscle grows progressive overload explained"},
        {"arxiv_query": "protein intake muscle synthesis nutrition", "web_query": "protein carbs fat nutrition guide for exercise"},
        {"arxiv_query": "aerobic anaerobic exercise heart rate zone", "web_query": "cardio vs strength training which is better"},
        {"arxiv_query": "sleep recovery cortisol overtraining athlete", "web_query": "sleep importance muscle recovery exercise science"},
        {"arxiv_query": "habit formation behavior change exercise adherence", "web_query": "how to build exercise habit behavior design"},
    ],
    "history": [
        {"arxiv_query": None, "web_query": "how history is made primary sources interpretation"},
        {"arxiv_query": None, "web_query": "why great empires fall Rome Ottoman collapse reasons"},
        {"arxiv_query": "industrial revolution steam engine social change", "web_query": "industrial revolution causes effects society"},
        {"arxiv_query": None, "web_query": "20th century world wars cold war economic growth"},
        {"arxiv_query": None, "web_query": "South Korea compressed growth modernization history"},
    ],
}


def seed():
    inserted = 0
    skipped = 0

    for track_id, track in CURRICULUM_CATALOG.items():
        # 이미 존재하면 스킵
        existing = supabase.table("topic_curricula").select("id").eq("topic_key", track_id).execute()
        if existing.data:
            print(f"  [SKIP] {track_id} — 이미 존재")
            skipped += 1
            continue

        # search_hints 주입
        hints = SEARCH_HINTS.get(track_id, [])
        chapters = []
        for i, ch in enumerate(track["chapters"]):
            ch_copy = dict(ch)
            if i < len(hints):
                ch_copy["search_hints"] = hints[i]
            else:
                ch_copy["search_hints"] = {"arxiv_query": None, "web_query": ch["title"]}
            chapters.append(ch_copy)

        supabase.table("topic_curricula").insert({
            "topic_key":    track_id,
            "topic_name":   track["title"],
            "category":     track.get("topic_names", [track["title"]])[0],
            "topic_aliases": track.get("topic_names", []),
            "emoji":        track.get("emoji", "📚"),
            "color":        track.get("color", "#6366F1"),
            "description":  track.get("description", ""),
            "chapters":     chapters,
        }).execute()

        print(f"  [INSERT] {track_id} — {len(chapters)}개 챕터")
        inserted += 1

    print(f"\n완료: {inserted}개 삽입, {skipped}개 스킵")


if __name__ == "__main__":
    seed()
