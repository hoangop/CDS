from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.migration import run_migrations

app = FastAPI(title="CDS Analytics API", version="1.0.0")

# Run migrations on startup
@app.on_event("startup")
async def startup_event():
    run_migrations()

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn (trong dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to CDS Analytics API"}

app.include_router(endpoints.router, prefix="/api/v1")

