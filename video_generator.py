"""
video_generator.py
==================
AI-Powered Doodle Explainer Video Generator (Python / Manim)
"""

import os
import sys
import re
import argparse
import subprocess
import tempfile
import textwrap
import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# ── Groq client ──────────────────────────────────────────────────────────
try:
    from groq import Groq
except ImportError:
    print("[ERROR] 'groq' package not found. Run: pip install groq")
    sys.exit(1)


# ── Constants ─────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert Manim (Community Edition v0.18+) animator and educator.
Your job is to generate complete, runnable Manim Python scripts that create
beautiful doodle-style explainer animations for any topic.

RULES:
1. Output ONLY valid Python code — no prose, no markdown fences, no explanations.
2. The script must define exactly ONE Scene class named `ExplainerScene`.
3. Use ManimCE (from manim import *) only. No external assets or fonts required.
4. Style: doodle / whiteboard aesthetic — use WHITE background, dark ink colors.
5. Include: title card → key concept breakdown → visual diagrams/animations → summary.
6. Keep total runtime under 90 seconds (use self.wait() sparingly).
7. Add voiceover-style text as on-screen captions using Text() or Tex().
8. Every animation must be self-contained — no file I/O, no network calls.
9. Use smooth, staggered animations: Write(), FadeIn(), GrowArrow(), etc.
10. Do NOT use deprecated Manim APIs. Use current v0.18 APIs only.

DOODLE STYLE PALETTE:
  background: WHITE
  primary text: BLACK (#1a1a1a)
  accent 1: BLUE (#3B82F6)
  accent 2: "#E84855" (red-pink)
  accent 3: "#10B981" (green)
  highlight: YELLOW_E

OUTPUT: pure Python code only, starting with `from manim import *`
"""


# ── Groq API call ───────────────────────────────────────────────────────────
def generate_manim_script(topic: str, verbose: bool = True) -> str:
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY environment variable not set.\n"
            "Export it: export GROQ_API_KEY='gsk_...'"
        )

    client = Groq(api_key=GROQ_API_KEY)

    user_message = (
        f"Create a complete Manim doodle explainer video script about:\n\n"
        f"TOPIC: {topic}\n\n"
        f"Make it visually engaging with clear step-by-step explanations. "
        f"Include at least 3-5 distinct animation sections. "
        f"Remember: output ONLY the Python code."
    )

    if verbose:
        print(f"[Groq] Generating Manim script for: '{topic}' ...")

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=4096,
    )

    raw = completion.choices[0].message.content.strip()

    raw = re.sub(r"^```python\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"^```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    if not raw.startswith("from manim"):
        idx = raw.find("from manim")
        if idx != -1:
            raw = raw[idx:]

    return raw


# ── Script validation ─────────────────────────────────────────────────────────
def validate_script(script: str) -> bool:
    checks = [
        "from manim import" in script,
        "ExplainerScene" in script,
        "class ExplainerScene" in script,
        "def construct" in script,
    ]
    return all(checks)


# ── Manim renderer ────────────────────────────────────────────────────────────
QUALITY_FLAGS = {
    "low":    ["-ql"],
    "medium": ["-qm"],
    "high":   ["-qh"],
    "4k":     ["-qk"],
}


def render_video(
    script: str,
    output_path: str = "explainer_video.mp4",
    quality: str = "medium",
    verbose: bool = True,
) -> str:

    quality_flag = QUALITY_FLAGS.get(quality, ["-qm"])

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "scene.py"
        script_path.write_text(script, encoding="utf-8")

        cmd = [
            sys.executable, "-m", "manim",
            *quality_flag,
            "--output_file", "ExplainerScene",
            "--media_dir", str(Path(tmpdir) / "media"),
            str(script_path),
            "ExplainerScene",
        ]

        if verbose:
            print(f"[Manim] Rendering video (quality={quality}) ...")
            print(f"[Manim] CMD: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            cwd=tmpdir,
        )

        if result.returncode != 0:
            err = result.stderr if result.stderr else "Unknown error"
            raise RuntimeError(
                f"Manim rendering failed (exit {result.returncode}):\n{err}"
            )

        media_dir = Path(tmpdir) / "media"
        mp4_files = list(media_dir.rglob("*.mp4"))

        if not mp4_files:
            raise FileNotFoundError(
                "Manim ran successfully but no .mp4 file was found.\n"
                "Check media folder for other output formats."
            )

        best = max(mp4_files, key=lambda p: p.stat().st_size)

        import shutil
        out = Path(output_path).resolve()
        shutil.copy2(best, out)

        if verbose:
            print(f"[Done] Video saved to: {out}")

        return str(out)


# ── Retry wrapper ─────────────────────────────────────────────────────────────
def generate_and_render(
    topic: str,
    output_path: str = "explainer_video.mp4",
    quality: str = "medium",
    max_retries: int = 2,
    save_script: bool = True,
    verbose: bool = True,
) -> dict:

    result = {"topic": topic, "script": None, "video": None, "error": None}
    last_error = None

    for attempt in range(1, max_retries + 2):
        try:
            if verbose and attempt > 1:
                print(f"\n[Retry {attempt-1}/{max_retries}] Regenerating script ...")

            script = generate_manim_script(topic, verbose=verbose)

            if not validate_script(script):
                raise ValueError("Generated script failed validation checks.")

            result["script"] = script

            if save_script:
                script_out = Path(output_path).with_suffix(".py")
                script_out.write_text(script, encoding="utf-8")
                if verbose:
                    print(f"[Saved] Script: {script_out}")

            video_path = render_video(
                script,
                output_path=output_path,
                quality=quality,
                verbose=verbose,
            )
            result["video"] = video_path
            return result

        except Exception as e:
            last_error = str(e)
            if verbose:
                print(f"[Error] Attempt {attempt}: {e}")
            if attempt <= max_retries:
                time.sleep(2)

    result["error"] = last_error
    return result


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic")
    parser.add_argument("--output", "-o", default="explainer_video.mp4")
    parser.add_argument("--quality", "-q", default="medium",
                        choices=["low", "medium", "high", "4k"])
    parser.add_argument("--retries", "-r", type=int, default=2)
    parser.add_argument("--save-script", action="store_true")
    parser.add_argument("--script-only", action="store_true")

    args = parser.parse_args()

    print("=" * 60)
    print("  AI DOODLE EXPLAINER VIDEO GENERATOR")
    print("  Powered by Manim + Groq")
    print("=" * 60)
    print(f"  Topic   : {args.topic}")
    print(f"  Quality : {args.quality}")
    print(f"  Output  : {args.output}")
    print("=" * 60 + "\n")

    if args.script_only:
        script = generate_manim_script(args.topic)
        print(script)
        return

    result = generate_and_render(
        topic=args.topic,
        output_path=args.output,
        quality=args.quality,
        max_retries=args.retries,
        save_script=args.save_script,
    )

    print("\n" + "=" * 60)
    if result["video"]:
        print(f"  ✅ SUCCESS")
        print(f"  Video : {result['video']}")
    else:
        print(f"  ❌ FAILED")
        print(f"  Error : {result['error']}")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()