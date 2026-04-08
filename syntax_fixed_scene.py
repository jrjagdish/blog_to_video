from manim import *

class PythonExplainer(Scene):
    def construct(self):
        # Introduction
        intro_text = Text("Python Explainer", font_size=40, color=BLUE)
        self.play(Write(intro_text))
        self.wait(0.5)
        self.play(FadeOut(intro_text))

        # Basic Syntax
        basic_syntax_text = Text("Basic Syntax", font_size=30, color=GREEN)
        self.play(Write(basic_syntax_text))
        self.wait(0.5)

        syntax_example = Text("print('Hello World')", font_size=24, color=YELLOW)
        syntax_example.next_to(basic_syntax_text, DOWN)
        self.play(Write(syntax_example))
        self.wait(0.5)

        # Variables
        variables_text = Text("Variables", font_size=30, color=RED)
        variables_text.next_to(basic_syntax_text, DOWN * 2)
        self.play(Write(variables_text))

        variable_example = Text("x = 5", font_size=24, color=YELLOW)
        variable_example.next_to(variables_text, DOWN)
        self.play(Write(variable_example))
        self.wait(0.5)

        # Data Types
        data_types_text = Text("Data Types", font_size=30, color=PURPLE)
        data_types_text.next_to(variables_text, DOWN * 2)
        self.play(Write(data_types_text))

        data_types_list = Text("Int, Float, String, List, Dictionary", font_size=24, color=YELLOW)
        data_types_list.next_to(data_types_text, DOWN)
        self.play(Write(data_types_list))
        self.wait(0.5)

        # Control Structures
        control_structures_text = Text("Control Structures", font_size=30, color=ORANGE)
        control_structures_text.next_to(data_types_text, DOWN * 2)
        self.play(Write(control_structures_text))

        # Conditional Statements
        conditional_statements_text = Text("If-Else Statements", font_size=24, color=YELLOW)
        conditional_statements_text.next_to(control_structures_text, DOWN)
        self.play(Write(conditional_statements_text))

        conditional_example = Text("if x > 5: print('x is greater than 5')", font_size=18, color=YELLOW)
        conditional_example.next_to(conditional_statements_text, DOWN)
        self.play(Write(conditional_example))
        self.wait(0.5)

        # Loops
        loops_text = Text("Loops", font_size=30, color=WHITE)
        loops_text.next_to(conditional_statements_text, DOWN * 2)
        self.play(Write(loops_text))

        for_loop_text = Text("For Loop", font_size=24, color=YELLOW)
        for_loop_text.next_to(loops_text, DOWN)
        self.play(Write(for_loop_text))

        for_loop_example = Text("for i in range(5): print(i)", font_size=18, color=YELLOW)
        for_loop_example.next_to(for_loop_text, DOWN)
        self.play(Write(for_loop_example))
        self.wait(0.5)

        while_loop_text = Text("While Loop", font_size=24, color=YELLOW)
        while_loop_text.next_to(for_loop_text, DOWN)
        self.play(Write(while_loop_text))

        while_loop_example = Text("i = 0; while i < 5: print(i); i += 1", font_size=18, color=YELLOW)
        while_loop_example.next_to(while_loop_text, DOWN)
        self.play(Write(while_loop_example))
        self.wait(1)