import os
import uuid
from typing import Dict
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.llm_groq import generate_script_and_scenes
from services.engine_manim import render_manim_video
from services.audio_gtts import generate_audio
from services.engine_moviepy import stitch_video_and_audio

os.makedirs("videos", exist_ok=True)

app = FastAPI(title="AI Video Generator SaaS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/videos", StaticFiles(directory="videos"), name="videos")

class GenerationRequest(BaseModel):
    prompt: str
    format: str  # "manim", "3d", "motion"

class JobStatus(BaseModel):
    id: str
    status: str
    video_url: str | None = None
    script_data: dict | None = None
    error: str | None = None

jobs: Dict[str, JobStatus] = {}

def process_video_job(job_id: str, prompt: str, format_type: str):
    try:
        jobs[job_id].status = "generating_script"
        script_data = generate_script_and_scenes(prompt, format_type)
        jobs[job_id].script_data = script_data
        
        jobs[job_id].status = "generating_audio"
        full_text = " ".join([scene.get("text", "") for scene in script_data.get("scenes", []) if scene.get("text")])
        if not full_text:
            full_text = "Welcome to the video."
            
        audio_path = f"videos/tmp_{job_id}.mp3"
        generate_audio(full_text, audio_path)
        
        if format_type == "manim":
            jobs[job_id].status = "rendering_manim"
            manim_code = "\n".join([scene.get("manim_code", "") for scene in script_data.get("scenes", []) if scene.get("manim_code")])
            
            if "from manim import *" not in manim_code:
                manim_code = "from manim import *\nclass ExplainerScene(Scene):\n    def construct(self):\n        t = Text('Render Error').scale(2)\n        self.play(Write(t))\n        self.wait(2)\n" + manim_code
            
            raw_video = f"videos/raw_{job_id}.mp4"
            render_manim_video(manim_code, output_path=raw_video)
            
            jobs[job_id].status = "stitching_final_video"
            final_video = f"videos/final_{job_id}.mp4"
            stitch_video_and_audio(raw_video, audio_path, final_video)
            
            if os.path.exists(raw_video): os.remove(raw_video)
            if os.path.exists(audio_path): os.remove(audio_path)
            
            jobs[job_id].video_url = f"/videos/final_{job_id}.mp4"
            jobs[job_id].status = "completed"
            
        else:
            jobs[job_id].status = "completed"
            if os.path.exists(audio_path):
                final_audio = f"videos/final_{job_id}.mp3"
                os.rename(audio_path, final_audio)
                jobs[job_id].video_url = f"/videos/final_{job_id}.mp3"
                
    except Exception as e:
        jobs[job_id].status = "failed"
        jobs[job_id].error = str(e)

@app.get("/")
def read_root(): return {"status": "Service is running"}

@app.post("/generate", response_model=JobStatus)
def generate_video(req: GenerationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(id=job_id, status="queued")
    background_tasks.add_task(process_video_job, job_id, req.prompt, req.format)
    return jobs[job_id]

@app.get("/status/{job_id}", response_model=JobStatus)
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]
