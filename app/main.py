from fastapi import FastAPI
from app.api.routes import router
from app.database import startup, shutdown

app = FastAPI()

app.include_router(router)

@app.on_event("startup")
async def start_conn():
    await startup(app)

@app.on_event("shutdown")
async def close_conn():
    await shutdown(app)
