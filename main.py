from fastapi import FastAPI

app = FastAPI(title="Travel Planner API")

@app.get("/health")
def health():
    return {"status": "ok"}