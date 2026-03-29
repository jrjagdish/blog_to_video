import os
from moviepy import VideoFileClip, AudioFileClip

def stitch_video_and_audio(
    video_path: str,
    audio_path: str,
    output_path: str = "final_output.mp4"
) -> str:
    """
    Combines a silent Manim/Remotion video with the gTTS generated audio.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")
        
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    
    final_clip = video_clip.set_audio(audio_clip)
    
    final_clip.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac",
        fps=30,
        preset="ultrafast"
    )
    
    try:
        video_clip.close()
        audio_clip.close()
        final_clip.close()
    except Exception:
        pass
        
    return output_path
