"""
MongoDB connection manager using motor (async driver)
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from config import settings

_client: AsyncIOMotorClient | None = None


def get_db():
    """Return the database instance. Call after connect_db()."""
    return _client[settings.mongo_db]


async def connect_db():
    global _client
    _client = AsyncIOMotorClient(settings.mongo_uri)
    db = get_db()

    # Create indexes
    await db.users.create_indexes([
        IndexModel([("email", ASCENDING)], unique=True),
    ])
    await db.cases.create_indexes([
        IndexModel([("owner_id", ASCENDING)]),
        IndexModel([("created_at", ASCENDING)]),
    ])
    await db.documents.create_indexes([
        IndexModel([("case_id", ASCENDING)]),
    ])
    print("✅ Connected to MongoDB")


async def close_db():
    global _client
    if _client:
        _client.close()
        print("🔌 Disconnected from MongoDB")
