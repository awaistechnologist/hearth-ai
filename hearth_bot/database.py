import aiosqlite
import logging

DB_NAME = "/app/hearth_data/hearth.db"

async def init_db():
    import os
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    async with aiosqlite.connect(DB_NAME) as db:
        # Family Config Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS family_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Family Members Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                birthdate TEXT
            )
        """)
        # Users Table (Mapping Telegram ID to Family Member)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'guest',
                approved BOOLEAN DEFAULT 0
            )
        """)
        await db.commit()
    logging.info("Database initialized.")

async def get_config(key: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT value FROM family_config WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_config(key: str, value: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO family_config (key, value) VALUES (?, ?)", (key, value))
        await db.commit()

async def is_user_allowed(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT approved FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False

async def approve_user(telegram_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO users (telegram_id, role, approved) VALUES (?, 'admin', 1)", (telegram_id,))
        await db.commit()

