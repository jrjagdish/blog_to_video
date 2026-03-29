import os
import json
from groq import Groq
from pydantic import BaseModel
from typing import List, Optional, Dict

class Scene(BaseModel):
    id: int
    text: str # Narrator voiceover
    duration: float # estimated duration
    manim_code: Optional[str] = None # if format is manim
    threejs_props: Optional[Dict] = None # if format is 3d
    overlay_instruction: Optional[str] = None # for moviepy handanim

class VideoScript(BaseModel):
    title: str
    scenes: List[Scene]

def generate_script_and_scenes(prompt: str, format_type: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set. Please set it in .env")
    
    client = Groq(api_key=api_key)
    
    system_prompt = f"""You are an AI video producer. 
Based on the prompt, generate a JSON object representing a video script.
The video format requested is: {format_type}.
Return ONLY valid JSON matching this schema:
{{
  "title": "Video Title",
  "scenes": [
     {{
       "id": 1,
       "text": "The spoken voiceover text",
       "duration": 5.0,
       "manim_code": "if manim format, pure python manim code defining class Scene1(Scene): ...",
       "threejs_props": {{"text": "Headline", "color": "#ffffff"}},
       "overlay_instruction": "hand drawing a circle"
     }}
  ]
}}"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )
    
    content = completion.choices[0].message.content
    return json.loads(content)
