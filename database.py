import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def get_connection():
    conn = await asyncpg.connect(DATABASE_URL)

    # Set default schema
    await conn.execute("SET search_path TO capstone")
    return conn