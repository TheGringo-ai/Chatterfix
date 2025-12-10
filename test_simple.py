#!/usr/bin/env python3
"""
Minimal FastAPI test app to verify container startup works
"""
import os
from fastapi import FastAPI

app = FastAPI(title="Test App")

@app.get("/")
def root():
    return {"message": "Container startup SUCCESS!", "port": os.getenv("PORT", "unknown")}

@app.get("/health")
def health():
    return {"status": "healthy", "port": os.getenv("PORT", "unknown")}

@app.get("/test")
def test():
    return {"test": "working", "port": os.getenv("PORT", "unknown")}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)