from fastapi import FastAPI
from app.api.v1.graph import router as graph_router

app = FastAPI(
    title="AI Literature Review Backend",
    version="0.1.0",
    description="FastAPI interface for LangGraph-based literature review workflow."
)

app.include_router(graph_router)

# 健康检查
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "AI Literature Review backend is running"}