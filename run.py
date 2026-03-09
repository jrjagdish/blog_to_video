from PIL import Image, ImageDraw, ImageFont

text = "AI is transforming software development"

img = Image.new("RGB", (1280, 720), color=(30,30,30))
draw = ImageDraw.Draw(img)

font = ImageFont.truetype("arial.ttf", 50)

draw.text((100,300), text, fill="white", font=font)

img.save("slide1.png")
import edge_tts
import asyncio

async def generate_voice():
    communicate = edge_tts.Communicate(
        "AI is transforming software development",
        "en-US-AriaNeural"
    )
    await communicate.save("voice.mp3")

asyncio.run(generate_voice())

from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx import FadeIn, FadeOut

slide = (
    ImageClip("slide1.png")
    .with_duration(5)
    .resized(lambda t: 1 + 0.05 * t)
    .with_effects([FadeIn(1), FadeOut(1)])
)

audio = AudioFileClip("voice.mp3")

text = (
    TextClip(
        text="AI is changing development",
        font="C:/Windows/Fonts/arial.ttf",   # full path
        font_size=70,
        color="white"
    )
    .with_duration(5)
    .with_position("center")
    .with_effects([FadeIn(1), FadeOut(1)])
)



video = CompositeVideoClip([slide, text]).with_audio(audio)

video.write_videofile("video.mp4", fps=24)