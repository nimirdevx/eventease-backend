from fastapi import FastAPI
from app.routers import auth, events
from fastapi.staticfiles import StaticFiles
import os


app = FastAPI()

@app.get("/")
def root():
    return {"message": "EventEase API is running 🚀"}

os.makedirs("tickets", exist_ok=True)

# Serve static files from the "tickets" folder
app.mount("/tickets", StaticFiles(directory="tickets"), name="tickets")

# Register routers
app.include_router(auth.router)
app.include_router(events.router)

