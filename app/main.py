from fastapi import FastAPI
from app.routers import auth, events

app = FastAPI()

@app.get("/")
def root():
    return {"message": "EventEase API is running 🚀"}

# Register routers
app.include_router(auth.router)
app.include_router(events.router)

