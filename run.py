from manim import *
import numpy as np
import asyncio
import edge_tts
import os
import shutil # For auto-deleting files

# ==========================================
# 1. LLM & ASSET SETUP
# ==========================================
# Imagine this comes from your API Key logic:
TEXT_FROM_LLM = "The sun is a star at the center of the Solar System." 
VOICE_FILE = "voice.mp3"
HAND_FILE = "hand.png"

# Optional: Add a path to a custom font (.ttf file)
# If you don't have one, Manim uses system fonts.
CUSTOM_FONT = "Arial" 

async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    await communicate.save(VOICE_FILE)

# ==========================================
# 2. THE ANIMATION ENGINE
# ==========================================
class AIShowcase(Scene):
    def construct(self):
        asyncio.run(generate_voice(TEXT_FROM_LLM))
        self.camera.background_color = "#FCFCFC"

        # --- A. CREATE DYNAMIC TEXT ---
        # scale_to_fit_width ensures long LLM text stays on screen
        text = Text(TEXT_FROM_LLM, color="#1E1E1E", font=CUSTOM_FONT, font_size=40)
        text.scale_to_fit_width(config.frame_width - 2)

        # --- B. HAND TRACKER ---
        tracker = Dot(radius=0).move_to(text.get_left())
        try:
            hand = ImageMobject(HAND_FILE).set_height(2.0)
            hand.rotate(335 * DEGREES) 
            hand.add_updater(lambda m: m.move_to(tracker.get_center() + RIGHT * 0.5 + DOWN * 0.2))
            self.add(hand)
        except:
            hand = None

        # --- C. ANIMATION: WRITING ---
        self.add_sound(VOICE_FILE)
        duration = len(TEXT_FROM_LLM) / 13.0
        
        self.play(
            Write(text),
            tracker.animate.move_to(text.get_right()),
            run_time=duration,
            rate_func=linear
        )
        if hand: self.remove(hand)
        self.wait(1)

        # --- D. EXPLAINING WITH IMAGES ---
        # Move text up to make room for an "explanation image"
        self.play(text.animate.shift(UP * 2.5))

        # Let's say we want to show a "Star" because the LLM mentioned 'Sun'
        explanation_graphic = Star(color=YELLOW, fill_opacity=1).scale(1.5)
        explanation_label = Text("Solar Center", color=GREY, font_size=24).next_to(explanation_graphic, DOWN)
        
        self.play(
            FadeIn(explanation_graphic, shift=UP),
            Write(explanation_label)
        )
        self.play(Indicate(explanation_graphic)) # Makes it pop/flash
        self.wait(3)

# ==========================================
# 3. RUN & AUTO-CLEANUP
# ==========================================
if __name__ == "__main__":
    # Run the render
    os.system("python -m manim run.py AIShowcase -pql")

    # Cleanup: Delete the 'partial_movie_files' to save space
    # The final video stays in media/videos/run/480p15/AIShowcase.mp4
    partial_path = os.path.join("media", "videos", "run", "480p15", "partial_movie_files")
    if os.path.exists(partial_path):
        shutil.rmtree(partial_path)
        print("--- Temporary files deleted. Final video saved! ---")