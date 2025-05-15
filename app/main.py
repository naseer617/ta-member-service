from fastapi import FastAPI
from shared.db.connection import engine
from shared.db.base import Base
from sqlalchemy.exc import OperationalError
import asyncio

from .routes import router as member_router

app = FastAPI(title="Member Service")
app.include_router(member_router)

@app.on_event("startup")
async def startup():
    retries = 10
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database connected and initialized.")
            break
        except OperationalError:
            print(f" DB not ready (attempt {attempt + 1}/10), retrying...")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Database failed to connect after multiple retries.")
