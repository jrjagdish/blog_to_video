"""
AI Explainer Video Generator — Single File
==========================================
Pipeline:
  Topic → Groq LLM (scene plan) → gTTS (per-scene audio) → Manim (animations) → MoviePy (composite) → MP4

Requirements:
    pip install groq gtts python-dotenv moviepy manim

System:
    ffmpeg must be in PATH
    LaTeX optional (improves Manim text quality)

Usage:
    python ai_explainer.py "How does photosynthesis work?"
    python ai_explainer.py "Explain quicksort" -o sort.mp4 -q high
    python ai_explainer.py "What is DNA?" --quality low --retries 3
"""

import os, sys, re, json, time, shutil, argparse, tempfile, textwrap, subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR LOGGING
# ─────────────────────────────────────────────────────────────────────────────
def clr(c, s):
    codes = {"red":"\033[91m","green":"\033[92m","yellow":"\033[93m",
             "cyan":"\033[96m","magenta":"\033[95m","bold":"\033[1m","reset":"\033[0m"}
    return f"{codes.get(c,'')}{s}{codes['reset']}"

def log(step, msg, c="cyan"):
    print(clr(c, f"  [{step}] {msg}"))

def banner(title):
    w = 62
    print("\n" + clr("bold", "═"*w))
    print(clr("bold", f"  {title}"))
    print(clr("bold", "═"*w))

# ─────────────────────────────────────────────────────────────────────────────
# DEPENDENCY CHECKS
# ─────────────────────────────────────────────────────────────────────────────
def check_deps():
    missing = []
    try:    import groq
    except: missing.append("groq")
    try:    import gtts
    except: missing.append("gtts")
    try:    import moviepy
    except: missing.append("moviepy")
    if missing:
        print(clr("red", f"\n[ERROR] Missing packages: {', '.join(missing)}"))
        print(clr("yellow", f"  Run: pip install {' '.join(missing)}"))
        sys.exit(1)
    if not shutil.which("ffmpeg"):
        print(clr("red", "\n[ERROR] ffmpeg not found in PATH"))
        print(clr("yellow", "  Install: https://ffmpeg.org/download.html"))
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# GROQ — SCENE PLAN GENERATION
# ─────────────────────────────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"

PLAN_PROMPT = """You are an expert educational video producer.
Return ONLY valid JSON — no markdown fences, no prose, no extra text.

JSON schema:
{
  "title": "short video title",
  "subtitle": "one-line description",
  "color_scheme": {
    "bg": "#hex",
    "primary": "#hex",
    "accent": "#hex",
    "text": "#hex"
  },
  "scenes": [
    {
      "id": 1,
      "scene_type": "intro|bullet_list|diagram|timeline|comparison|summary",
      "scene_title": "Scene heading",
      "caption": "1-2 sentence on-screen text",
      "narration": "2-3 sentence voiceover (conversational, no jargon)",
      "bullets": ["point 1", "point 2", "point 3"],
      "duration": 8
    }
  ]
}

Rules:
- Exactly 7 scenes. Scene 1 = intro, Scene 7 = summary.
- scene_type drives animation: intro=animated title, bullet_list=staggered bullets,
  diagram=nodes+arrows, timeline=horizontal steps, comparison=two columns, summary=checkmarks.
- color_scheme: vivid palette fitting the topic mood (dark bg preferred).
- duration: 6-10 seconds per scene.
- bullets: 3-5 short items.
- narration: friendly, engaging, short sentences.
"""

def generate_plan(topic: str) -> dict:
    from groq import Groq
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set. Add it to .env or export it.")

    client = Groq(api_key=key)
    log("Groq", f"Generating scene plan for: {topic!r}")

    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": PLAN_PROMPT},
            {"role": "user",   "content": f"Topic: {topic}"},
        ],
        temperature=0.65,
        max_tokens=4096,
    )
    raw = resp.choices[0].message.content.strip()

    # strip accidental markdown fences
    raw = re.sub(r"^```[a-z]*\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"^```\s*$",      "", raw, flags=re.MULTILINE)

    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError(f"Could not parse JSON from Groq response:\n{raw[:500]}")

    plan = json.loads(m.group(0))
    log("Groq", f"Plan ready — {len(plan['scenes'])} scenes, title: {plan['title']!r}", "green")
    return plan

# ─────────────────────────────────────────────────────────────────────────────
# gTTS — PER-SCENE VOICEOVER
# ─────────────────────────────────────────────────────────────────────────────
def make_voiceover(text: str, out: Path):
    from gtts import gTTS
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(str(out))

# ─────────────────────────────────────────────────────────────────────────────
# MANIM SCENE SCRIPT BUILDER
# Each scene_type gets a distinct, visually rich Manim animation
# ─────────────────────────────────────────────────────────────────────────────
QUALITY_MAP = {"low": "-ql", "medium": "-qm", "high": "-qh", "4k": "-qk"}

def _mc(hex_color: str) -> str:
    """Convert '#RRGGBB' to a Manim-safe color string."""
    h = hex_color.strip().lstrip("#").upper()
    return f'"#{h}"'

def _trunc(s: str, n: int = 52) -> str:
    return s[:n] + "…" if len(s) > n else s

def build_manim_script(scene: dict, cs: dict, idx: int) -> str:
    """Generate a complete Manim Scene Python script for one scene."""

    bg      = cs.get("bg",      "#0F172A")
    primary = cs.get("primary", "#38BDF8")
    accent  = cs.get("accent",  "#F472B6")
    txt_col = cs.get("text",    "#F8FAFC")

    stype   = scene.get("scene_type", "bullet_list")
    stitle  = _trunc(scene.get("scene_title", ""), 48).replace('"', '\\"')
    caption = _trunc(scene.get("caption", ""),      60).replace('"', '\\"')
    bullets = [_trunc(b, 52).replace('"', '\\"') for b in scene.get("bullets", [])[:6]]
    dur     = max(5, int(scene.get("duration", 8)))
    cname   = f"Scene{idx:02d}"

    # ── INTRO ────────────────────────────────────────────────────────────────
    if stype == "intro":
        body = f"""
        # background
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                        fill_color={_mc(bg)}, fill_opacity=1, stroke_width=0)
        self.add(bg)

        # animated corner accents
        corners = VGroup()
        for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
            sq = Square(side_length=0.9, color={_mc(accent)}, stroke_width=3, fill_opacity=0)
            sq.move_to([dx*6.0, dy*3.2, 0])
            corners.add(sq)

        # gradient bar top
        bar_top = Rectangle(width=config.frame_width, height=0.15,
                             fill_color={_mc(primary)}, fill_opacity=1, stroke_width=0)
        bar_top.to_edge(UP, buff=0)

        # gradient bar bottom
        bar_bot = Rectangle(width=config.frame_width, height=0.15,
                             fill_color={_mc(accent)}, fill_opacity=1, stroke_width=0)
        bar_bot.to_edge(DOWN, buff=0)

        # title
        title = Text("{stitle}", font_size=72, color={_mc(primary)}, weight=BOLD)
        title.move_to(UP * 0.6)

        # subtitle / caption
        sub = Text("{caption}", font_size=30, color={_mc(txt_col)})
        sub.next_to(title, DOWN, buff=0.55)

        # decorative horizontal rule
        rule = Line(LEFT*4.5, RIGHT*4.5, color={_mc(accent)}, stroke_width=2)
        rule.next_to(title, DOWN, buff=0.25)

        self.play(FadeIn(bar_top), FadeIn(bar_bot), run_time=0.4)
        self.play(Write(title), run_time=1.2)
        self.play(Create(rule), run_time=0.5)
        self.play(FadeIn(sub, shift=UP*0.25), run_time=0.7)
        self.play(LaggedStart(*[DrawBorderThenFill(c) for c in corners],
                               lag_ratio=0.2), run_time=0.8)
        self.wait({dur - 4})
        self.play(FadeOut(VGroup(title, sub, rule, corners, bar_top, bar_bot)))
"""

    # ── BULLET LIST ──────────────────────────────────────────────────────────
    elif stype == "bullet_list":
        item_wait = max(1, (dur - 2) // max(len(bullets), 1))
        items_code = "\n".join(
            f'        item_group.add(Text("▸  {b}", font_size=31, color={_mc(txt_col)}))'
            for b in bullets
        )
        body = f"""
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                        fill_color={_mc(bg)}, fill_opacity=1, stroke_width=0)
        self.add(bg)

        # header bar
        hbar = Rectangle(width=config.frame_width, height=0.9,
                          fill_color={_mc(primary)}, fill_opacity=0.18, stroke_width=0)
        hbar.to_edge(UP, buff=0)

        heading = Text("{stitle}", font_size=44, color={_mc(primary)}, weight=BOLD)
        heading.to_edge(UP, buff=0.22)

        accent_line = Line(LEFT*6.5, RIGHT*6.5, color={_mc(accent)}, stroke_width=2.5)
        accent_line.next_to(heading, DOWN, buff=0.08)

        item_group = VGroup()
{items_code}
        item_group.arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        item_group.next_to(accent_line, DOWN, buff=0.42)
        item_group.to_edge(LEFT, buff=0.85)

        self.play(FadeIn(hbar), Write(heading), run_time=0.7)
        self.play(Create(accent_line), run_time=0.4)
        for item in item_group:
            self.play(FadeIn(item, shift=RIGHT*0.5), run_time=0.38)
            self.wait({item_wait})
        self.wait(1)
        self.play(FadeOut(VGroup(hbar, heading, accent_line, item_group)))
"""

    # ── DIAGRAM ──────────────────────────────────────────────────────────────
    elif stype == "diagram":
        node_labels = bullets[:5] if bullets else [caption[:30]]
        nodes_code  = "\n".join(
            f'        node_labels.append("{b}")'
            for b in node_labels
        )
        body = f"""
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                        fill_color={_mc(bg)}, fill_opacity=1, stroke_width=0)
        self.add(bg)

        heading = Text("{stitle}", font_size=44, color={_mc(primary)}, weight=BOLD)
        heading.to_edge(UP, buff=0.35)
        self.play(Write(heading), run_time=0.6)

        node_labels = []
{nodes_code}

        nodes  = VGroup()
        labels = VGroup()
        for lbl in node_labels:
            box = RoundedRectangle(corner_radius=0.25, width=3.0, height=0.85,
                                   fill_color={_mc(primary)}, fill_opacity=0.22,
                                   stroke_color={_mc(primary)}, stroke_width=2.5)
            t = Text(lbl, font_size=24, color={_mc(txt_col)})
            t.move_to(box)
            nodes.add(box)
            labels.add(t)

        arrange_dir = RIGHT if len(node_labels) <= 3 else DOWN
        nodes.arrange(arrange_dir, buff=0.65)
        for i, (box, lbl) in enumerate(zip(nodes, labels)):
            lbl.move_to(box)

        all_nodes = VGroup(*[VGroup(b, l) for b, l in zip(nodes, labels)])
        all_nodes.move_to(ORIGIN + DOWN*0.2)

        arrows = VGroup()
        for i in range(len(nodes)-1):
            if arrange_dir == RIGHT:
                arr = Arrow(nodes[i].get_right(), nodes[i+1].get_left(),
                             buff=0.06, color={_mc(accent)}, stroke_width=3)
            else:
                arr = Arrow(nodes[i].get_bottom(), nodes[i+1].get_top(),
                             buff=0.06, color={_mc(accent)}, stroke_width=3)
            arrows.add(arr)

        for i in range(len(nodes)):
            self.play(FadeIn(nodes[i], scale=0.8), Write(labels[i]), run_time=0.45)
            if i < len(arrows):
                self.play(GrowArrow(arrows[i]), run_time=0.4)

        cap = Text("{caption}", font_size=26, color={_mc(txt_col)})
        cap.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(cap))
        self.wait({max(2, dur - 4)})
        self.play(FadeOut(VGroup(heading, all_nodes, arrows, cap)))
"""

    # ── TIMELINE ─────────────────────────────────────────────────────────────
    elif stype == "timeline":
        tl_items = bullets[:5] if bullets else [caption[:28]]
        n = len(tl_items)
        tl_code = "\n".join(
            f'        tl_items.append("{b}")'
            for b in tl_items
        )
        body = f"""
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                        fill_color={_mc(bg)}, fill_opacity=1, stroke_width=0)
        self.add(bg)

        heading = Text("{stitle}", font_size=44, color={_mc(primary)}, weight=BOLD)
        heading.to_edge(UP, buff=0.35)
        self.play(Write(heading))

        # main timeline axis
        axis = Line(LEFT*5.8, RIGHT*5.8, color={_mc(primary)}, stroke_width=3)
        axis.move_to(ORIGIN + DOWN*0.2)
        self.play(Create(axis), run_time=0.7)

        tl_items = []
{tl_code}
        n = len(tl_items)
        span = 11.0
        xs = [-5.5 + i * (span / max(n-1, 1)) for i in range(n)]

        for i, (label, x) in enumerate(zip(tl_items, xs)):
            dot = Dot(point=[x, -0.2, 0], radius=0.16, color={_mc(accent)})
            tick = Line([x,-0.05,0], [x,0.05,0], color={_mc(primary)}, stroke_width=3)
            lbl  = Text(label, font_size=21, color={_mc(txt_col)})
            lbl.next_to(dot, UP if i % 2 == 0 else DOWN, buff=0.25)
            num  = Text(str(i+1), font_size=16, color={_mc(bg)}, weight=BOLD)
            num.move_to(dot)
            self.play(FadeIn(dot), Write(lbl), run_time=0.45)
            self.add(num)
        self.wait({max(2, dur - 3)})
        self.play(FadeOut(*self.mobjects))
"""

    # ── COMPARISON ───────────────────────────────────────────────────────────
    elif stype == "comparison":
        left_items  = bullets[:3] if bullets else ["Option A"]
        right_items = bullets[3:6] if len(bullets) > 3 else ["Option B"]
        left_code   = "\n".join(f'        left_pts.append("{b}")' for b in left_items)
        right_code  = "\n".join(f'        right_pts.append("{b}")' for b in right_items)
        body = f"""
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                        fill_color={_mc(bg)}, fill_opacity=1, stroke_width=0)
        self.add(bg)

        heading = Text("{stitle}", font_size=42, color={_mc(primary)}, weight=BOLD)
        heading.to_edge(UP, buff=0.35)
        self.play(Write(heading))

        # divider
        div = DashedLine(UP*3.0, DOWN*3.0, color={_mc(primary)},
                          stroke_width=2, dash_length=0.15)
        div.move_to(ORIGIN)
        self.play(Create(div), run_time=0.5)

        # left column header
        lh = Text("◀  " + ("{stitle}".split(" vs ")[0] if " vs " in "{stitle}" else "Side A"),
                   font_size=28, color={_mc(primary)}, weight=BOLD)
        lh.move_to(LEFT*3.5 + UP*2.3)

        # right column header
        rh = Text(("{stitle}".split(" vs ")[1] if " vs " in "{stitle}" else "Side B") + "  ▶",
                   font_size=28, color={_mc(accent)}, weight=BOLD)
        rh.move_to(RIGHT*1.8 + UP*2.3)
        self.play(FadeIn(lh), FadeIn(rh))

        left_pts = []
{left_code}
        right_pts = []
{right_code}

        for i, pt in enumerate(left_pts):
            t = Text("• " + pt, font_size=27, color={_mc(txt_col)})
            t.move_to(LEFT*3.6 + DOWN*(0.2 + i*0.82))
            t.to_edge(LEFT, buff=0.55)
            self.play(FadeIn(t, shift=RIGHT*0.4), run_time=0.38)

        for i, pt in enumerate(right_pts):
            t = Text("• " + pt, font_size=27, color={_mc(txt_col)})
            t.move_to(RIGHT*1.0 + DOWN*(0.2 + i*0.82))
            self.play(FadeIn(t, shift=LEFT*0.4), run_time=0.38)

        self.wait({max(2, dur - 4)})
        self.play(FadeOut(*self.mobjects))
"""

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    elif stype == "summary":
        sum_items = bullets[:5] if bullets else [caption]
        items_code = "\n".join(
            f'        check_items.append("{b}")'
            for b in sum_items
        )
        body = f"""
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                        fill_color={_mc(bg)}, fill_opacity=1, stroke_width=0)
        self.add(bg)

        # accent top bar
        top_bar = Rectangle(width=config.frame_width, height=0.18,
                             fill_color={_mc(accent)}, fill_opacity=1, stroke_width=0)
        top_bar.to_edge(UP, buff=0)
        self.add(top_bar)

        # "Summary" heading
        heading = Text("Summary", font_size=60, color={_mc(primary)}, weight=BOLD)
        heading.to_edge(UP, buff=0.28)
        self.play(Write(heading), run_time=0.8)

        check_items = []
{items_code}

        grp = VGroup()
        for pt in check_items:
            row = VGroup(
                Text("✓", font_size=32, color={_mc(accent)}, weight=BOLD),
                Text("  " + pt, font_size=30, color={_mc(txt_col)})
            )
            row.arrange(RIGHT, aligned_edge=UP, buff=0.18)
            grp.add(row)

        grp.arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        grp.next_to(heading, DOWN, buff=0.48)
        grp.to_edge(LEFT, buff=0.9)

        for row in grp:
            self.play(FadeIn(row, shift=RIGHT*0.4), run_time=0.38)
            self.wait(0.45)

        # CTA
        cta_bg = Rectangle(width=7, height=0.72,
                            fill_color={_mc(accent)}, fill_opacity=0.22, stroke_width=0)
        cta_bg.to_edge(DOWN, buff=0.55)
        cta = Text("👍 Like   🔔 Subscribe   🔗 Share", font_size=28, color={_mc(accent)})
        cta.move_to(cta_bg)
        self.play(FadeIn(cta_bg), FadeIn(cta))
        self.wait({max(2, dur - 4)})
        self.play(FadeOut(*self.mobjects))
"""

    # ── FALLBACK ─────────────────────────────────────────────────────────────
    else:
        body = f"""
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                        fill_color={_mc(bg)}, fill_opacity=1, stroke_width=0)
        self.add(bg)
        heading = Text("{stitle}", font_size=52, color={_mc(primary)}, weight=BOLD)
        cap     = Text("{caption}", font_size=30, color={_mc(txt_col)})
        cap.next_to(heading, DOWN, buff=0.55)
        VGroup(heading, cap).move_to(ORIGIN)
        self.play(Write(heading), run_time=1.0)
        self.play(FadeIn(cap, shift=UP*0.25), run_time=0.7)
        self.wait({max(2, dur - 3)})
        self.play(FadeOut(heading), FadeOut(cap))
"""

    # ── wrap in complete Scene class ─────────────────────────────────────────
    return textwrap.dedent(f"""\
from manim import *

config.pixel_height = 1080
config.pixel_width  = 1920
config.frame_rate   = 30

class {cname}(Scene):
    def construct(self):
{textwrap.indent(body, '        ')}
""")


def render_manim_scene(script: str, cname: str, tmp: Path, quality: str = "medium") -> Path:
    """Write script to disk, run Manim, return path to rendered MP4."""
    qflag = QUALITY_MAP.get(quality, "-qm")
    script_file = tmp / f"{cname}.py"
    script_file.write_text(script, encoding="utf-8")
    media_dir = tmp / "media"

    cmd = [
        sys.executable, "-m", "manim",
        qflag,
        "--output_file", cname,
        "--media_dir", str(media_dir),
        str(script_file),
        cname,
    ]
    result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Manim failed for {cname}:\n{result.stderr[-1200:]}"
        )

    mp4s = list(media_dir.rglob("*.mp4"))
    if not mp4s:
        raise FileNotFoundError(f"No MP4 found after rendering {cname}")
    return max(mp4s, key=lambda p: p.stat().st_size)


# ─────────────────────────────────────────────────────────────────────────────
# MOVIEPY — COMPOSITE FINAL VIDEO
# ─────────────────────────────────────────────────────────────────────────────
def _detect_moviepy_version():
    """
    Returns 1 or 2 depending on installed MoviePy major version.
    MoviePy v1 uses moviepy.editor; MoviePy v2 uses moviepy directly.
    """
    try:
        import moviepy
        ver = getattr(moviepy, "__version__", "1.0.0")
        return 2 if int(ver.split(".")[0]) >= 2 else 1
    except Exception:
        return None


def composite_video(scene_mp4s: list, audio_mp3s: list, out_path: Path):
    """
    Stitch per-scene videos + per-scene audio with fade transitions.
    Compatible with both MoviePy v1.x and v2.x.
    """
    ver = _detect_moviepy_version()
    if ver is None:
        log("MoviePy", "Not installed — falling back to plain ffmpeg concat", "yellow")
        _ffmpeg_concat_only(scene_mp4s, out_path)
        return

    # ── MoviePy v2.x (new API) ────────────────────────────────────────────
    if ver >= 2:
        try:
            from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
            from moviepy.audio.fx import AudioLoop

            clips = []
            for vp, ap in zip(scene_mp4s, audio_mp3s):
                clip  = VideoFileClip(str(vp))
                audio = AudioFileClip(str(ap))

                vlen = clip.duration
                alen = audio.duration

                # loop or trim audio to fit video length
                if alen < vlen:
                    loops = int(vlen / alen) + 2
                    audio = AudioLoop(nloops=loops).apply(audio).subclipped(0, vlen)
                else:
                    audio = audio.subclipped(0, vlen)

                # fade in/out using v2 API
                clip = clip.with_effects([
                    __import__("moviepy.video.fx", fromlist=["FadeIn"]).FadeIn(0.30),
                    __import__("moviepy.video.fx", fromlist=["FadeOut"]).FadeOut(0.30),
                ])
                clip = clip.with_audio(audio)
                clips.append(clip)

            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(
                str(out_path), codec="libx264", audio_codec="aac", fps=30, logger=None
            )
            for c in clips:
                c.close()
            final.close()
            return

        except Exception as e:
            log("MoviePy v2", f"Composite failed ({e}) — trying ffmpeg fallback", "yellow")
            _ffmpeg_concat_with_audio(scene_mp4s, audio_mp3s, out_path)
            return

    # ── MoviePy v1.x (legacy API) ─────────────────────────────────────────
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
        import moviepy.audio.fx.all as afx

        # fadein / fadeout — import gracefully
        try:
            from moviepy.video.fx.fadein  import fadein
            from moviepy.video.fx.fadeout import fadeout
            has_fade = True
        except ImportError:
            has_fade = False

        clips = []
        for vp, ap in zip(scene_mp4s, audio_mp3s):
            clip  = VideoFileClip(str(vp))
            audio = AudioFileClip(str(ap))

            vlen = clip.duration
            alen = audio.duration

            if alen < vlen:
                audio = afx.audio_loop(audio, nloops=int(vlen / alen) + 2).subclip(0, vlen)
            else:
                audio = audio.subclip(0, vlen)

            if has_fade:
                clip = fadein(clip, 0.30).fx(fadeout, 0.30)
            clip = clip.set_audio(audio)
            clips.append(clip)

        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            str(out_path), codec="libx264", audio_codec="aac", fps=30, logger=None
        )
        for c in clips:
            c.close()
        final.close()

    except Exception as e:
        log("MoviePy v1", f"Composite failed ({e}) — using ffmpeg fallback", "yellow")
        _ffmpeg_concat_with_audio(scene_mp4s, audio_mp3s, out_path)


def _ffmpeg_concat_only(clips: list, out_path: Path):
    """Fallback: concat mp4s without audio using ffmpeg concat demuxer."""
    ffmpeg = shutil.which("ffmpeg")
    list_file = out_path.parent / "_concat_list.txt"
    list_file.write_text("\n".join(f"file '{Path(p).resolve()}'" for p in clips))
    subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(out_path)],
        check=True
    )
    list_file.unlink(missing_ok=True)


def _ffmpeg_concat_with_audio(video_paths: list, audio_paths: list, out_path: Path):
    """
    Pure ffmpeg fallback: merge each video+audio pair, then concatenate all.
    Works with any MoviePy version (or none at all).
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise EnvironmentError("ffmpeg not found in PATH")

    tmp_dir = out_path.parent / "_ffmpeg_tmp"
    tmp_dir.mkdir(exist_ok=True)
    merged_clips = []

    for i, (vp, ap) in enumerate(zip(video_paths, audio_paths)):
        merged = tmp_dir / f"merged_{i:02d}.mp4"
        subprocess.run(
            [ffmpeg, "-y",
             "-i", str(vp),
             "-i", str(ap),
             "-c:v", "copy",
             "-c:a", "aac",
             "-shortest",
             str(merged)],
            check=True, capture_output=True
        )
        merged_clips.append(merged)

    # concat all merged clips
    list_file = tmp_dir / "concat_list.txt"
    list_file.write_text("\n".join(f"file \'{p.resolve()}\'" for p in merged_clips))
    subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(out_path)],
        check=True
    )
    shutil.rmtree(tmp_dir, ignore_errors=True)
    log("ffmpeg", f"Final video: {out_path}", "green")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def create_video(topic: str, output: str = "explainer.mp4",
                 quality: str = "medium", retries: int = 2,
                 save_plan: bool = False):

    check_deps()

    out_path = Path(output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    banner("AI EXPLAINER VIDEO GENERATOR")
    print(f"  Topic   : {topic}")
    print(f"  Quality : {quality}")
    print(f"  Output  : {out_path}")
    print()

    # ── Step 1: generate scene plan ──────────────────────────────────────────
    log("1/5", "Generating scene plan via Groq …")
    plan = generate_plan(topic)
    cs   = plan.get("color_scheme",
                    {"bg":"#0F172A","primary":"#38BDF8","accent":"#F472B6","text":"#F8FAFC"})

    if save_plan:
        plan_path = out_path.with_suffix(".plan.json")
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        log("Plan", f"Saved to {plan_path}", "green")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        scene_mp4s = []
        audio_mp3s = []
        total = len(plan["scenes"])

        for idx, scene in enumerate(plan["scenes"]):
            snum  = idx + 1
            stype = scene.get("scene_type", "?")
            stitle = scene.get("scene_title", "")
            log(f"Scene {snum}/{total}", f"[{stype}] {stitle}")

            # ── Step 2: voiceover ─────────────────────────────────────────
            narr     = scene.get("narration") or scene.get("caption", "")
            mp3_path = tmp / f"audio_{idx:02d}.mp3"
            log(f"  2", "Voiceover (gTTS) …")
            try:
                make_voiceover(narr, mp3_path)
            except Exception as e:
                log("WARN", f"gTTS failed: {e} — creating silent audio", "yellow")
                # 1-second silence fallback
                subprocess.run(
                    [shutil.which("ffmpeg"), "-y", "-f", "lavfi",
                     "-i", "anullsrc=r=22050:cl=mono",
                     "-t", str(scene.get("duration", 8)),
                     str(mp3_path)], check=True, capture_output=True
                )

            # ── Step 3 & 4: build + render Manim scene ────────────────────
            cname  = f"Scene{idx:02d}"
            script = build_manim_script(scene, cs, idx)

            rendered = None
            for attempt in range(1, retries + 2):
                try:
                    log(f"  3", f"Rendering {cname} (attempt {attempt}) …")
                    rendered = render_manim_scene(script, cname, tmp, quality)
                    log(f"  ✓", f"{cname} rendered: {rendered.name}", "green")
                    break
                except Exception as e:
                    log("WARN", f"Attempt {attempt} failed: {str(e)[:120]}", "yellow")
                    if attempt <= retries:
                        time.sleep(1)

            if rendered is None:
                log("SKIP", f"Scene {snum} could not be rendered — skipping", "red")
                continue

            scene_mp4s.append(rendered)
            audio_mp3s.append(mp3_path)

        if not scene_mp4s:
            raise RuntimeError("Every scene failed to render. Check Manim installation.")

        # ── Step 5: composite ─────────────────────────────────────────────
        log("5/5", f"Compositing {len(scene_mp4s)} scenes with MoviePy …")
        composite_video(scene_mp4s, audio_mp3s, out_path)

    banner("DONE")
    print(clr("green", f"  ✅  {out_path}"))
    print()
    return str(out_path)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="AI Explainer Video Generator (Groq + Manim + MoviePy)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python ai_explainer.py "How does photosynthesis work?"
          python ai_explainer.py "Explain quicksort" -q high -o sort.mp4
          python ai_explainer.py "What is DNA?" --quality low --retries 3 --save-plan
        """),
    )
    ap.add_argument("topic",       help="Topic for the explainer video")
    ap.add_argument("-o", "--output",   default="explainer.mp4",
                    help="Output MP4 filename  (default: explainer.mp4)")
    ap.add_argument("-q", "--quality",  default="medium",
                    choices=["low","medium","high","4k"],
                    help="Render quality       (default: medium)")
    ap.add_argument("--retries",        type=int, default=2,
                    help="Retry count per scene (default: 2)")
    ap.add_argument("--save-plan",      action="store_true",
                    help="Save the JSON scene plan alongside the video")
    args = ap.parse_args()

    create_video(
        topic     = args.topic,
        output    = args.output,
        quality   = args.quality,
        retries   = args.retries,
        save_plan = args.save_plan,
    )