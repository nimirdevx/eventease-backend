from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "EventEase API is running 🚀"}
