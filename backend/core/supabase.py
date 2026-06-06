from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SECRET_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL 또는 SUPABASE_SECRET_KEY가 없습니다. .env 확인하세요.")

supabase: Client = create_client(url, key)
