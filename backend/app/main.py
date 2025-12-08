from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints

app = FastAPI(title="CDS Analytics API", version="1.0.0")

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

