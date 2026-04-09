from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health import router as health_router
from app.routes.parse import router as parse_router
from app.routes.classify import router as classify_router
from app.routes.approval import router as approval_router
from app.routes.enrich import router as enrich_router

app = FastAPI(
    title="YieldStream Qualify",
    version="0.1.0",
    description="Document parsing and financial intelligence API — extract structured data from bank statements, tax returns, and MCA applications.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(parse_router)
app.include_router(classify_router)
app.include_router(approval_router)
app.include_router(enrich_router)
