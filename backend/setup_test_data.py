"""
테스트 데이터 초기 세팅
실행: python setup_test_data.py

Supabase에 테스트 유저 + 관심사를 삽입합니다.
"""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from core.supabase import supabase

TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"

def setup():
    print("테스트 데이터 세팅 중...")

    # 1. 테스트 유저 삽입 (이미 있으면 무시)
    try:
        supabase.table("users").upsert({
            "id": TEMP_USER_ID,
            "email": "test@briefup.com",
            "nickname": "테스터"
        }).execute()
        print("✅ 테스트 유저 생성 완료")
    except Exception as e:
        print(f"유저 생성: {e}")

    # 2. 관심사 삽입
    topics = [
        {"user_id": TEMP_USER_ID, "name": "Agentic AI", "category": "AI/ML"},
        {"user_id": TEMP_USER_ID, "name": "RAG", "category": "AI/ML"},
    ]
    for t in topics:
        try:
            supabase.table("topics").insert(t).execute()
            print(f"✅ 관심사 추가: {t['name']}")
        except Exception as e:
            print(f"관심사 ({t['name']}): {e}")

    # 3. 스트릭 초기화
    try:
        supabase.table("streaks").upsert({
            "user_id": TEMP_USER_ID,
            "current_streak": 0,
            "longest_streak": 0,
        }).execute()
        print("✅ 스트릭 초기화 완료")
    except Exception as e:
        print(f"스트릭: {e}")

    print("\n✅ 세팅 완료! 이제 서버 실행하세요.")
    print("   uvicorn main:app --reload")

if __name__ == "__main__":
    setup()
