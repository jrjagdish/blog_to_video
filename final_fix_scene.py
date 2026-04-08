from manim import *

class GeneratedScene(Scene):
    def construct(self):
        circle = Circle(color=RED)
        square = Square(color=BLUE).next_to(circle, RIGHT)
        triangle = Triangle(color=GREEN).next_to(square, RIGHT)
        rectangle = Rectangle(color=YELLOW).next_to(triangle, RIGHT)
        star = Star(color=PURPLE).next_to(rectangle, RIGHT)

        self.play(Create(circle))
        self.play(Write(Text("Circle")))
        self.play(FadeIn(square))
        self.play(Write(Text("Square")).next_to(square, DOWN))
        self.play(FadeIn(triangle))
        self.play(Write(Text("Triangle")).next_to(triangle, DOWN))
        self.play(FadeIn(rectangle))
        self.play(Write(Text("Rectangle")).next_to(rectangle, DOWN))
        self.play(FadeIn(star))
        self.play(Write(Text("Star")).next_to(star, DOWN))

        self.play(Transform(circle, square), Transform(triangle, rectangle), Transform(star, circle))