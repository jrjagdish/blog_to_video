from fastapi import FastAPI
from app.api.routes.video_routes import router as video_router

app = FastAPI()

@app.get("/")
def health_check():
    return {"message": "Hello World!"}

app.include_router(video_router, prefix="/api/video", tags=["video"])