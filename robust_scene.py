from manim import Scene, Text, Circle, Square, Triangle, Rectangle, Star

class GeneratedScene(Scene):
    def construct(self):
        circle = Circle(color=RED)
        circle.shift(2 * LEFT)
        self.play(Create(circle))

        square = Square(color=YELLOW)
        square.shift(2 * RIGHT)
        self.play(Create(square))

        triangle = Triangle(color=GREEN)
        triangle.shift(2 * UP)
        self.play(Create(triangle))

        rectangle = Rectangle(color=BLUE)
        rectangle.shift(2 * DOWN)
        self.play(Create(rectangle))

        star = Star(color=WHITE)
        star.shift(ORIGIN)
        self.play(Create(star))

        text1 = Text("Circle").set_color(RED).next_to(circle, DOWN)
        self.play(Write(text1))

        text2 = Text("Square").set_color(YELLOW).next_to(square, DOWN)
        self.play(Write(text2))

        text3 = Text("Triangle").set_color(GREEN).next_to(triangle, DOWN)
        self.play(Write(text3))

        text4 = Text("Rectangle").set_color(BLUE).next_to(rectangle, UP)
        self.play(Write(text4))

        text5 = Text("Star").set_color(WHITE).next_to(star, DOWN)
        self.play(Write(text5))
        self.wait(2)