# database.py
from sqlalchemy import create_engine, MetaData, Table, Column, String
from databases import Database
import asyncio

# Use the K8s service name `postgres` instead of localhost
DATABASE_URL = "postgresql+asyncpg://adarsh:Admin%40123@postgres:5432/adarsh"
database = Database(DATABASE_URL)
metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("username", String, primary_key=True),
    Column("password", String),
)

# Use the sync driver by replacing asyncpg with psycopg2 for create_engine
engine = create_engine(DATABASE_URL.replace("asyncpg", "psycopg2"))
metadata.create_all(engine)

async def test_connection():
    try:
        await database.connect()
        result = await database.fetch_one("SELECT 1")
        print("Database connected successfully! Result:", result)
        await database.disconnect()
    except Exception as e:
        print(f"Failed to connect to database: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())