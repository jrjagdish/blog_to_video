import os
import re
import subprocess
import shutil
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are a Manim expert.
CRITICAL RULES:
1. ALWAYS use 'from manim import *'.
2. POSITIONING: Always call .next_to() or .shift() on the OBJECT, not the animation.
   - WRONG: self.play(Write(Text("Hi")).next_to(obj))
   - RIGHT: self.play(Write(Text("Hi").next_to(obj)))
3. Animations: Use Create(shape), Write(text), FadeIn(obj), Transform(obj1, obj2).
4. Colors: RED, BLUE, GREEN, YELLOW, WHITE, PURPLE, ORANGE.
5. Content: Explain the topic using multiple shapes and labels.
6. Return ONLY raw Python code.
"""

def pre_clean_code(code):
    """Fix common AI syntax hallucinations before rendering."""
    # Fix the .next_to() outside of play() animation call
    # Matches: self.play(Write(Text("...")).next_to(...))
    # Changes to: self.play(Write(Text("...").next_to(...)))
    pattern = r"(self\.play\(Write\((.*?)\)\)\.next_to\((.*?)\))"
    fixed_code = re.sub(pattern, r"self.play(Write(\2.next_to(\3)))", code)
    
    # Ensure Star import is present
    if "from manim import *" not in fixed_code:
        fixed_code = "from manim import *\n" + fixed_code
        
    return fixed_code

def get_ai_response(prompt, error_log=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if error_log:
        messages.append({"role": "user", "content": f"ERROR: {error_log}\nFix the syntax. Remember: .next_to() goes inside the animation call, e.g., self.play(Write(Text('...').next_to(obj)))"})
    else:
        messages.append({"role": "user", "content": f"Visualize: {prompt}. Use colorful shapes and text."})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    
    content = completion.choices[0].message.content
    content = re.sub(r"```python|```", "", content).strip()
    return pre_clean_code(content)

def render_video(code, attempt=1):
    file_name = "syntax_fixed_scene.py"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"\n--- 🎥 Rendering Attempt {attempt} ---")
    
    result = subprocess.run(
        ["manim", "-ql", "--media_dir", ".", file_name, "GeneratedScene"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        source_path = "videos/syntax_fixed_scene/480p15/GeneratedScene.mp4"
        output_name = "final_explainer.mp4"
        if os.path.exists(source_path):
            shutil.copy(source_path, output_name)
            print(f"✅ SUCCESS! Final video: {os.path.abspath(output_name)}")
        return True
    else:
        print(f"❌ Attempt {attempt} failed.")
        # Extract the specific line and error for the AI
        error_lines = result.stderr.splitlines()
        clean_error = "\n".join(error_lines[-8:]) 
        
        if attempt < 2:
            print(f"Retrying with error context...")
            new_code = get_ai_response(None, error_log=clean_error)
            return render_video(new_code, attempt + 1)
        else:
            print("Traceback:\n", result.stderr)
            return False

if __name__ == "__main__":
    topic = input("Topic for visual animation: ")
    initial_code = get_ai_response(topic)
    render_video(initial_code)