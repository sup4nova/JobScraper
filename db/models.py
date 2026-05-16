import aiosqlite
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "jobs.db"


async def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_id TEXT,
                title TEXT NOT NULL,
                company TEXT,
                city TEXT,
                salary TEXT,
                education TEXT,
                contract_type TEXT,
                description TEXT,
                url TEXT NOT NULL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new',
                UNIQUE(source, url)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cv_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER REFERENCES jobs(id),
                output_path TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def upsert_job(job: dict) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            cur = await db.execute("""
                INSERT INTO jobs (source, external_id, title, company, city, salary, education, contract_type, description, url)
                VALUES (:source, :external_id, :title, :company, :city, :salary, :education, :contract_type, :description, :url)
                ON CONFLICT(source, url) DO NOTHING
            """, job)
            await db.commit()
            return cur.lastrowid
        except Exception:
            return None


async def get_jobs(status: str | None = None, search: str | None = None, source: str | None = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        clauses = []
        params = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if source:
            clauses.append("source = ?")
            params.append(source)
        if search:
            clauses.append("(title LIKE ? OR company LIKE ? OR city LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = await db.execute(f"SELECT * FROM jobs {where} ORDER BY scraped_at DESC", params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_job(job_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_job_status(job_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        await db.commit()


async def delete_job(job_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        await db.commit()


async def log_cv_generation(job_id: int, output_path: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO cv_generations (job_id, output_path) VALUES (?, ?)",
            (job_id, output_path)
        )
        await db.commit()
