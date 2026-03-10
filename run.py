import asyncio
import edge_tts
import numpy as np
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, ColorClip, ImageClip

# 1. SETUP
TEXT_CONTENT = "Mathematics is the language of the universe."
VIDEO_SIZE = (1280, 720)

async def generate_voice():
    communicate = edge_tts.Communicate(TEXT_CONTENT, "en-US-AriaNeural")
    await communicate.save("voice.mp3")

asyncio.run(generate_voice())

# 2. TIMING
audio = AudioFileClip("voice.mp3")
total_duration = audio.duration + 0.5
writing_duration = audio.duration 

# 3. ADVANCED MOTION LOGIC
def get_writing_progress(t):
    """Creates a 'staircase' effect so it reveals letter by letter"""
    progress = min(t / writing_duration, 1.0)
    # The '15' here represents the 'jitter' of writing individual letters
    return (np.floor(progress * 40) / 40) 

# 4. BACKGROUND & TEXT
bg = ColorClip(size=VIDEO_SIZE, color=(252, 252, 252)).with_duration(total_duration)

text_clip = (
    TextClip(
        text=TEXT_CONTENT,
        font="C:/Windows/Fonts/comic.ttf", 
        font_size=65,
        color=(30, 30, 30)
    )
    .with_duration(total_duration)
    .with_position("center")
)

# 5. IMPROVED REVEAL MASK
def reveal_pos(t):
    # This reveals the text in small 'chunks' rather than a smooth slide
    x_pos = get_writing_progress(t) * 950 - 320
    return (x_pos, 0)

reveal_mask = (
    ColorClip(size=VIDEO_SIZE, color=(252, 252, 252))
    .with_duration(total_duration)
    .with_position(reveal_pos)
)

# 6. THE "HUMANIZED" HAND
try:
    hand = (
        ImageClip("hand.png")
        .resized(height=280)
        .with_duration(writing_duration)
        .with_position(lambda t: (
            # Horizontal: Follows the chunked reveal
            get_writing_progress(t) * 950 + 220, 
            # Vertical: Circular 'looping' motion to simulate writing letters
            360 + 20 * np.sin(40 * t) + 10 * np.cos(10 * t)
        ))
    )
except:
    hand = None

# 7. ASSEMBLE
clips = [bg, text_clip, reveal_mask]
if hand: clips.append(hand)

video = CompositeVideoClip(clips).with_audio(audio)
# 60 FPS makes the 'writing' jitter look high-quality
video.write_videofile("math_doodle_v2.mp4", fps=60)