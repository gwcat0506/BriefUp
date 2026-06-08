"""
curriculum_catalog.py의 데이터를 topic_curricula DB에 upsert.
기존 데이터도 최신 catalog 내용으로 덮어씀 (재실행 안전).

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


def seed():
    upserted = 0

    for track_id, track in CURRICULUM_CATALOG.items():
        # search_hints는 catalog 챕터에 이미 내장되어 있음
        chapters = track["chapters"]

        supabase.table("topic_curricula").upsert({
            "topic_key":     track_id,
            "topic_name":    track["title"],
            "category":      track.get("topic_names", [track["title"]])[0],
            "topic_aliases": track.get("topic_names", []),
            "emoji":         track.get("emoji", "📚"),
            "color":         track.get("color", "#6366F1"),
            "description":   track.get("description", ""),
            "chapters":      chapters,
        }, on_conflict="topic_key").execute()

        print(f"  [UPSERT] {track_id} — {len(chapters)}개 챕터")
        upserted += 1

    print(f"\n완료: {upserted}개 upsert")


if __name__ == "__main__":
    seed()
