import os
import sys
import tempfile
import subprocess
from pathlib import Path

def render_manim_video(
    script: str,
    output_path: str = "manim_output.mp4",
    quality: str = "medium",
    class_name: str = "ExplainerScene"
) -> str:
    """
    Renders a Manim scene given raw python script contents.
    Requires Manim to be installed in the environment.
    """
    QUALITY_FLAGS = {
        "low": "-ql",
        "medium": "-qm",
        "high": "-qh",
        "4k": "-qk"
    }
    
    q_flag = QUALITY_FLAGS.get(quality, "-qm")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "scene.py"
        script_path.write_text(script, encoding="utf-8")
        
        cmd = [
            sys.executable, "-m", "manim",
            q_flag,
            "--output_file", class_name,
            "--media_dir", str(Path(tmpdir) / "media"),
            str(script_path),
            class_name, 
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Manim rendering failed:\n{result.stderr}\n\nSTDOUT:\n{result.stdout}")
            
        media_dir = Path(tmpdir) / "media"
        mp4_files = list(media_dir.rglob("*.mp4"))
        
        if not mp4_files:
            raise FileNotFoundError("Manim ran successfully but no .mp4 file was found.")
            
        best = max(mp4_files, key=lambda p: p.stat().st_size)
        
        import shutil
        out = Path(output_path).resolve()
        shutil.copy2(best, out)
        
        return str(out)
