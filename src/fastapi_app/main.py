from fastapi import FastAPI

app = FastAPI(title="fastapi-app", version="0.1.0")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello, FastAPI!"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
