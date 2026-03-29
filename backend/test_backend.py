import os
import unittest
from services.llm_groq import generate_script_and_scenes

class TestLLMGroq(unittest.TestCase):
    def test_schema_generation(self):
        # Only run if GROQ_API_KEY is available
        if not os.getenv("GROQ_API_KEY"):
            self.skipTest("GROQ_API_KEY not set")
            
        try:
            result = generate_script_and_scenes("A simple test about cats", "manim")
            self.assertIn("title", result)
            self.assertIn("scenes", result)
            self.assertIsInstance(result["scenes"], list)
            if len(result["scenes"]) > 0:
                scene = result["scenes"][0]
                self.assertIn("text", scene)
        except Exception as e:
            self.fail(f"API call failed: {str(e)}")

if __name__ == "__main__":
    unittest.main()
