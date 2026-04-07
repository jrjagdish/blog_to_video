import os
import json
import asyncio
import subprocess
from groq import Groq
import edge_tts
from moviepy.editor import AudioFileClip
from dotenv import load_dotenv
load_dotenv()

# --- CONFIG ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Make sure to set this in your environment variables
client = Groq(api_key=GROQ_API_KEY)

# --- 1. THE BRAINS: GROQ AI ---
def generate_course_plan(topic):
    prompt = f"""
    Create a 4-scene educational video script about '{topic}'.
    Return ONLY a JSON object with this structure:
    {{
      "title": "Course Title",
      "scenes": [
        {{
          "title": "Scene Heading",
          "narration": "Script for the AI voice (30 words)",
          "keywords": "3 keywords for image search",
          "color": "#hex_code_for_accent"
        }}
      ]
    }}
    Rules: Professional tone, interesting facts, valid JSON only.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    return json.loads(chat_completion.choices[0].message.content)

# --- 2. THE VOICE: EDGE TTS ---
async def get_voice_and_duration(text, path):
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural") # Premium sounding male voice
    await communicate.save(path)
    # Get exact duration so the video matches the speech perfectly
    return AudioFileClip(path).duration

# --- 3. THE ENGINE: DYNAMIC VIDEO BAKER ---
async def build_automated_video(topic):
    print(f"🧠 AI is planning the course for: {topic}...")
    plan = generate_course_plan(topic)
    
    editly_spec = {
        "width": 1920, "height": 1080, "fps": 30,
        "outPath": f"./{topic.replace(' ', '_')}.mp4",
        "defaults": {"transition": {"name": "fade", "duration": 0.5}},
        "clips": []
    }

    for i, scene in enumerate(plan['scenes']):
        audio_path = f"audio_{i}.mp3"
        print(f"🎙️ Generating voice for Scene {i+1}...")
        
        # Calculate duration based on actual voiceover length
        duration = await get_voice_and_duration(scene['narration'], audio_path)
        
        # Dynamically fetch image from Unsplash Source
        img_query = scene['keywords'].replace(" ", ",")
        img_url = f"https://source.unsplash.com/1600x900/?{img_query}"

        clip = {
            "duration": duration + 1.0, # Add a small buffer
            "layers": [
                # Background Gradient
                {"type": "fill-color", "color": "#1a1a2e"},
                
                # Main Visual (The "Realistic" part)
                {
                    "type": "image",
                    "path": img_url,
                    "resizeMode": "cover",
                    "opacity": 0.6
                },
                
                # Progress Bar (Top)
                {
                    "type": "rect",
                    "color": scene.get('color', '#00d2ff'),
                    "originX": "left", "x": 0, "y": 0,
                    "width": (i + 1) / len(plan['scenes']), "height": 0.02
                },

                # Modern Title Overlay
                {
                    "type": "title",
                    "text": scene['title'],
                    "textColor": "#ffffff",
                    "style": { "fontWeight": "bold" }
                },

                # Subtitle / Narration Text (Helps retention)
                {
                    "type": "subtitle",
                    "text": scene['narration'],
                    "backgroundColor": "rgba(0,0,0,0.5)"
                },
                
                # Audio Layer
                {"type": "audio", "path": audio_path}
            ]
        }
        editly_spec["clips"].append(clip)

    with open("automated_spec.json", "w") as f:
        json.dump(editly_spec, f)
    
    print("🎬 Rendering final course video...")
    subprocess.run(["editly", "automated_spec.json"])

if __name__ == "__main__":
    user_topic = input("Enter the topic you want to learn: ")
    asyncio.run(build_automated_video(user_topic))