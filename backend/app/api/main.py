from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.graph import router as graph_router

app = FastAPI(
    title="AI Literature Review Backend",
    version="0.1.0",
    description="FastAPI interface for LangGraph-based literature review workflow."
)

# Allow local frontend (Next dev server) to call the API
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph_router)


# 健康检查
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "AI Literature Review backend is running"}