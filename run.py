import os
import re
import numpy as np
import asyncio
import time
import random
import base64
from groq import Groq
import edge_tts
from moviepy import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import io

load_dotenv()

# Initialize Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Custom function to convert matplotlib figure to numpy array
def mplfig_to_npimage(fig):
    """Convert matplotlib figure to numpy array reliably"""
    # Draw the figure
    fig.canvas.draw()
    
    # Get the dimensions
    width, height = fig.canvas.get_width_height()
    
    # Get the buffer as ARGB and convert to RGB
    buffer = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
    image = buffer.reshape((height, width, 4))
    
    # Convert RGBA to RGB (remove alpha channel)
    image = image[:, :, :3]
    
    plt.close(fig)
    return image

async def generate_enhanced_script(blog_text):
    """Use AI to generate a rich video script with scene descriptions"""
    
    prompt = f"""
    Create an engaging 20-second video script from this blog: "{blog_text}"
    
    Return a Python list of dictionaries with these exact keys:
    - 'text': The spoken narration for this scene (1 sentence)
    - 'visual': What to show (be descriptive, include colors, movements)
    - 'animation_type': One of ['slide_in', 'fade_in', 'bounce', 'zoom', 'rotate']
    - 'duration': seconds for this scene (between 2-4)
    
    Make it dynamic and visually interesting!
    Format: [{{"text": "...", "visual": "...", "animation_type": "...", "duration": 3}}, ...]
    """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.8
    )
    
    response_content = chat_completion.choices[0].message.content
    print(f"🎬 AI Generated Script: {response_content}")
    
    # Parse the response
    list_match = re.search(r'(\[.*\])', response_content, re.DOTALL)
    if list_match:
        try:
            scenes = eval(list_match.group())
            return scenes
        except:
            pass
    
    # Fallback creative scenes
    return [
        {"text": "Python revolutionizes backend development", 
         "visual": "Futuristic code flowing through digital space", 
         "animation_type": "slide_in", "duration": 3},
        {"text": "FastAPI makes building APIs lightning fast", 
         "visual": "Rocket launching with code trails", 
         "animation_type": "zoom", "duration": 3},
        {"text": "Build production-ready APIs in minutes", 
         "visual": "Factory assembly line with code pieces", 
         "animation_type": "bounce", "duration": 3},
        {"text": "Join the future of web development", 
         "visual": "Connected world map with glowing nodes", 
         "animation_type": "fade_in", "duration": 3}
    ]

def create_animated_text(text, animation_type, duration, size=(640, 480)):
    """Create animated text using PIL and numpy (no matplotlib issues)"""
    
    def make_text_frame(t):
        # Create a blank image
        img = Image.new('RGB', size, color='black')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position based on animation type
        progress = min(t / duration, 1.0)
        
        if animation_type == 'slide_in':
            x = int((size[0] - text_width) * progress)
            y = (size[1] - text_height) // 2
        elif animation_type == 'bounce':
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2 + 20 * np.sin(5 * t)
        elif animation_type == 'zoom':
            scale = 0.5 + 0.5 * progress
            new_width = int(text_width * scale)
            new_height = int(text_height * scale)
            x = (size[0] - new_width) // 2
            y = (size[1] - new_height) // 2
        elif animation_type == 'rotate':
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
        else:  # fade_in
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
        
        # Draw text
        color = (255, 255, 255)  # White
        if animation_type == 'rotate':
            # Create rotated text
            text_img = Image.new('RGBA', (text_width + 50, text_height + 50), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((25, 25), text, fill=(255, 255, 255, 255), font=font)
            
            # Rotate
            angle = 5 * np.sin(2 * t)
            rotated = text_img.rotate(angle, expand=1)
            
            # Paste onto main image
            rotated = rotated.convert('RGB')
            img.paste(rotated, (x, y))
        else:
            draw.text((x, y), text, fill=color, font=font)
        
        return np.array(img)
    
    return VideoClip(make_text_frame, duration=duration)

def create_animated_background(style, duration, size=(640, 480)):
    """Create animated backgrounds using numpy (no matplotlib)"""
    
    def make_bg_frame(t):
        # Create base image
        img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        
        if style == 'particles':
            # Create particle effect
            for i in range(50):
                x = int((i * 10 + t * 50) % size[0])
                y = int((i * 20 + t * 30) % size[1])
                brightness = int(100 + 100 * np.sin(t + i))
                cv2.circle(img, (x, y), 3, (brightness, brightness, 255), -1)
        
        elif style == 'gradient':
            # Create moving gradient
            shift = int(t * 50) % size[0]
            for x in range(size[0]):
                color_val = int(255 * ((x + shift) % size[0]) / size[0])
                img[:, x] = [color_val, color_val // 2, 255 - color_val]
        
        else:  # waves
            for x in range(size[0]):
                y = int(size[1]//2 + 100 * np.sin(2*np.pi*x/100 + 3*t))
                if 0 <= y < size[1]:
                    cv2.circle(img, (x, y), 2, (0, 255, 255), -1)
        
        return img
    
    return VideoClip(make_bg_frame, duration=duration)

def create_visual_element(description, duration, size=(640, 480)):
    """Create visual effects based on description"""
    
    def make_element_frame(t):
        img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        
        # Parse description for keywords
        desc_lower = description.lower()
        
        # Moving circle
        if 'circle' in desc_lower or 'sphere' in desc_lower:
            x = int(size[0]//2 + 150 * np.sin(2 * t))
            y = int(size[1]//2 + 100 * np.cos(3 * t))
            cv2.circle(img, (x, y), 30, (255, 215, 0), -1)  # Gold circle
        
        # Rocket/upward movement
        elif 'rocket' in desc_lower or 'launch' in desc_lower:
            y = int(size[1] - 100 * t)
            if y > 0:
                # Draw rocket shape
                cv2.rectangle(img, (size[0]//2-20, y-40), (size[0]//2+20, y), (255, 100, 100), -1)
                cv2.circle(img, (size[0]//2, y-50), 10, (200, 200, 200), -1)
        
        # Connected nodes
        elif 'connected' in desc_lower or 'network' in desc_lower:
            nodes = [(200, 200), (440, 200), (320, 320), (200, 320), (440, 320)]
            # Draw connections
            for i, (x1, y1) in enumerate(nodes):
                for x2, y2 in nodes[i+1:]:
                    cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
                cv2.circle(img, (x1, y1), 8, (0, 255, 255), -1)
        
        # Default: floating particles
        else:
            for i in range(10):
                x = int(100 + i * 50 + 30 * np.sin(2*t + i))
                y = int(100 + i * 30 + 20 * np.cos(3*t + i))
                cv2.circle(img, (x, y), 5, (255, 100, 255), -1)
        
        return img
    
    return VideoClip(make_element_frame, duration=duration)

async def generate_voiceover(text, output_file):
    """Generate voiceover using edge-tts"""
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
    await communicate.save(output_file)

def generate_video_from_blog(blog_text):
    print("🎬 Starting AI Video Generation...")
    
    # Try to import cv2 for additional effects
    try:
        global cv2
        import cv2
        print("✅ OpenCV available for enhanced effects")
    except ImportError:
        print("⚠️ OpenCV not installed, using basic effects")
        # Create a dummy cv2 module with basic functionality
        class DummyCV2:
            @staticmethod
            def circle(img, center, radius, color, thickness):
                pass
            @staticmethod
            def line(img, pt1, pt2, color, thickness):
                pass
            @staticmethod
            def rectangle(img, pt1, pt2, color, thickness):
                pass
        cv2 = DummyCV2()
    
    # STEP 1: Generate enhanced script with AI
    print("🤖 AI is creating an engaging video script...")
    scenes = asyncio.run(generate_enhanced_script(blog_text))
    
    # STEP 2: Generate voiceover
    print("🎙️ Generating professional voiceover...")
    full_text = " ".join([s['text'] for s in scenes])
    audio_file = "temp_voice.mp3"
    asyncio.run(generate_voiceover(full_text, audio_file))
    
    if not os.path.exists(audio_file):
        print("❌ Voiceover failed!")
        return
    
    audio = AudioFileClip(audio_file)
    print(f"✅ Voiceover ready: {audio.duration:.2f} seconds")
    
    # Adjust scene durations to match audio
    total_duration = audio.duration
    scene_duration = total_duration / len(scenes)
    for scene in scenes:
        scene['duration'] = scene_duration
    
    # STEP 3: Create video clips
    print("🎨 Creating animated scenes...")
    all_clips = []
    current_time = 0
    
    for i, scene in enumerate(scenes):
        print(f"  Scene {i+1}: {scene['animation_type']} animation - '{scene['text'][:30]}...'")
        
        # Create animated background
        bg_style = random.choice(['particles', 'gradient', 'waves'])
        bg_clip = create_animated_background(bg_style, scene['duration'])
        bg_clip = bg_clip.with_start(current_time)
        all_clips.append(bg_clip)
        
        # Create animated text
        txt_clip = create_animated_text(
            scene['text'],
            scene['animation_type'],
            scene['duration']
        ).with_start(current_time)
        all_clips.append(txt_clip)
        
        # Create visual elements
        if 'visual' in scene:
            element_clip = create_visual_element(
                scene['visual'], 
                scene['duration']
            ).with_start(current_time)
            all_clips.append(element_clip)
        
        current_time += scene['duration']
    
    # STEP 4: Compose final video
    print("🎬 Composing final video with all effects...")
    final_video = CompositeVideoClip(
        all_clips,
        size=(640, 480)
    ).with_duration(current_time)
    
    # Add audio
    final_video = final_video.with_audio(audio)
    
    # STEP 5: Export
    output_file = "ai_generated_video.mp4"
    print(f"💾 Exporting video to {output_file}...")
    
    final_video.write_videofile(
        output_file,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )
    
    # Cleanup
    audio.close()
    if os.path.exists(audio_file):
        try:
            os.remove(audio_file)
        except:
            pass
    
    print(f"✅ Video created successfully! Check out {output_file}")
    print(f"📊 Video stats: {current_time:.2f} seconds, {len(scenes)} scenes")

if __name__ == "__main__":
    blog_input = """
    Python has revolutionized backend development with its simplicity and power.
    FastAPI takes it to the next level by providing automatic API documentation,
    validation, and incredible performance. It's the perfect choice for building
    modern web applications and microservices.
    """
    generate_video_from_blog(blog_input)