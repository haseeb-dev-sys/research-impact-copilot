from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Research Impact Co-Pilot (RIC)",
    description="Helps researchers understand and amplify their paper's impact.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
def hello():
    return {
        "status": "RIC hello",
        "version": "0.1",
        "message": "Research Impact Co-Pilot is running! 🔬"
    }

@app.get("/")
def root():
    return {
        "app": "Research Impact Co-Pilot",
        "docs": "/docs",
        "hello": "/hello"
    }