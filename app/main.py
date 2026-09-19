from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "DocRAG API is running!"}