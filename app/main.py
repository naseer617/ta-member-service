from fastapi import FastAPI
from shared.db.connection import engine
from shared.db.base import Base
from sqlalchemy.exc import OperationalError
import asyncio
from contextlib import asynccontextmanager

from .routes import router as member_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
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

    yield

    # Shutdown
    # Add any cleanup code here if needed

app = FastAPI(title="Member Service", lifespan=lifespan)
app.include_router(member_router)
