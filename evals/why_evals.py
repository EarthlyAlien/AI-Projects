from manimlib import *
import numpy as np


FONT = "Liberation Serif"
N_CASES = 20
# The demo is case 0. Eight of the twenty are right, including that one.
MODEL_A = {0, 2, 5, 8, 11, 13, 16, 18}
# A second system, clumsy on the demo, right on fifteen of the same cases.
MODEL_B = set(range(N_CASES)) - {3, 7, 12, 15, 19}


def label(text, color=GREY_A, size=32):
    mob = Text(text, font=FONT, font_size=size)
    mob.set_color(color)
    return mob


def sample_dots(correct, radius=0.085):
    dots = VGroup()
    for index in range(N_CASES):
        dot = Dot(radius=radius)
        color = GREEN if index in correct else RED_C
        dot.set_color(color)
        dots.add(dot)
    dots.arrange_in_grid(n_rows=2, n_cols=10, buff=0.32)
    return dots


def score_bar(fraction, color, width=3.4, height=0.32):
    track = Rectangle(width=width, height=height)
    track.set_fill(GREY_E, 1)
    track.set_stroke(GREY_B, 1.5)
    fill = Rectangle(width=max(width * fraction, 0.04), height=height)
    fill.set_fill(color, 1)
    fill.set_stroke(width=0)
    fill.move_to(track, LEFT)
    return VGroup(track, fill)


class WhyEvals(InteractiveScene):
    def construct(self):
        self.show_demo()
        self.show_the_cloud()
        self.show_the_ruler()
        self.show_the_split()
        self.show_the_claim()

    def show_demo(self):
        card = RoundedRectangle(width=7.4, height=2.35, corner_radius=0.16)
        card.set_fill(GREY_E, 1)
        card.set_stroke(GREY_B, 2)

        question = label("Late shipment. Partial refund?", WHITE, 36)
        answer = label("Yes. The policy allows it.", GREEN_B, 34)
        words = VGroup(question, answer).arrange(DOWN, buff=0.32)
        words.move_to(card)
        self.demo_card = VGroup(card, words)
        self.demo_card.move_to(0.45 * UP)

        self.demo_dot = Dot(radius=0.15, fill_color=GREEN)
        self.demo_dot.next_to(self.demo_card, DOWN, buff=0.65)
        self.demo_label = label("demo", GREY_A, 30)
        self.demo_label.next_to(self.demo_dot, DOWN, buff=0.18)

        self.play(FadeIn(card, scale=0.98), run_time=0.8)
        self.play(Write(question), run_time=1.2)
        self.wait(0.4)
        self.play(FadeIn(answer, shift=0.15 * UP), run_time=0.8)
        self.wait(0.7)
        self.play(GrowFromCenter(self.demo_dot), run_time=0.7)
        self.play(FadeIn(self.demo_label, shift=0.1 * UP), run_time=0.6)
        self.wait(5.5)

    def show_the_cloud(self):
        mark = VGroup(self.demo_dot, self.demo_label)
        self.play(
            self.demo_card.animate.scale(0.58).to_edge(UP, buff=0.28),
            mark.animate.move_to(0.35 * DOWN),
            run_time=1.5,
        )

        self.cloud = self.get_cloud(self.demo_dot.get_center(), 46)
        self.play(
            LaggedStartMap(FadeIn, self.cloud, lag_ratio=0.03, scale=0.4),
            run_time=3.6,
        )
        caption = label("every other case", GREY_B, 30)
        caption.to_edge(DOWN, buff=0.38)
        self.cloud_caption = caption
        self.play(FadeIn(caption, shift=0.12 * UP), run_time=0.7)
        self.wait(5.6)

    def show_the_ruler(self):
        dots = sample_dots(set())
        for dot in dots:
            dot.set_color(GREY_B)
        dots.move_to(1.35 * UP)

        self.play(
            FadeOut(self.demo_card),
            FadeOut(self.cloud),
            FadeOut(self.cloud_caption),
            FadeOut(self.demo_label),
            FadeOut(self.demo_dot),
            LaggedStartMap(FadeIn, dots, lag_ratio=0.03, scale=0.5),
            run_time=1.4,
        )

        self.play(self.recolor(dots, MODEL_A), run_time=2.6)
        bar_a = self.labeled_bar("A", 8 / N_CASES, BLUE_D, "8 / 20")
        bar_b = self.labeled_bar("B", 15 / N_CASES, TEAL_D, "15 / 20")
        bars = VGroup(bar_a, bar_b).arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        bars.next_to(dots, DOWN, buff=0.7)
        # Start the fills collapsed, then grow them from the left.
        for group, fraction in ((bar_a, 8 / N_CASES), (bar_b, 15 / N_CASES)):
            fill = group[1][1]
            fill.stretch_to_fit_width(0.05, about_edge=LEFT)
            fill.set_opacity(0)

        formula = Tex(R"\frac{\text{correct}}{N}", font_size=46)
        formula.set_color(WHITE)
        formula.next_to(bars, RIGHT, buff=0.7)

        self.play(FadeIn(bar_a[0]), FadeIn(bar_a[1][0]), run_time=0.4)
        self.play(self.grow_fill(bar_a, 8 / N_CASES), FadeIn(bar_a[3]), run_time=1.1)
        self.play(Write(formula), run_time=1.2)
        self.wait(2.2)

        self.play(self.recolor(dots, MODEL_B), run_time=2.4)
        self.play(FadeIn(bar_b[0]), FadeIn(bar_b[1][0]), run_time=0.4)
        self.play(self.grow_fill(bar_b, 15 / N_CASES), FadeIn(bar_b[3]), run_time=1.4)
        self.wait(5.2)

        self.sample = dots
        self.bars = bars
        self.formula = formula
        self.bar_a = bar_a
        self.bar_b = bar_b

    def show_the_split(self):
        tuned_count = self.bar_a[3]
        held = self.held_out_cluster()
        held.move_to(3.55 * RIGHT + 0.15 * UP)

        self.play(
            FadeOut(self.sample),
            FadeOut(self.formula),
            FadeOut(self.bar_b),
            self.bar_a.animate.move_to(3.5 * LEFT + 0.15 * DOWN),
            run_time=1.2,
        )
        tuned_word = label("tuned", BLUE_B, 32)
        tuned_word.next_to(self.bar_a, UP, buff=0.35)
        self.play(FadeIn(tuned_word, shift=0.1 * UP), FadeIn(held), run_time=0.8)

        wider = self.bar_a[1][0].get_width() * (18 / N_CASES)
        later = label("18 / 20", BLUE_B, 28)
        later.move_to(tuned_count)
        self.play(
            self.bar_a[1][1].animate.stretch_to_fit_width(wider, about_edge=LEFT).set_opacity(1),
            Transform(tuned_count, later),
            run_time=3.6,
        )
        self.wait(5.6)
        self.tuned_word = tuned_word
        self.held = held

    def show_the_claim(self):
        one = Dot(radius=0.16, fill_color=GREEN)
        one_label = label("a demo", GREY_A, 30)
        one_label.next_to(one, DOWN, buff=0.25)
        demo_side = VGroup(one, one_label)
        demo_side.move_to(3.4 * LEFT + 0.9 * UP)

        cloud = self.get_cloud(ORIGIN, 28, radius=1.15, color=YELLOW_D, opacity=0.9, hole=0.18)
        cloud_label = label("an eval", YELLOW, 30)
        cloud_label.next_to(cloud, DOWN, buff=0.3)
        eval_side = VGroup(cloud, cloud_label)
        eval_side.move_to(3.1 * RIGHT + 0.85 * UP)

        line_one = label("An eval is the work you did not tune,", WHITE, 32)
        line_two = label("scored the way the job is scored.", WHITE, 32)
        lines = VGroup(line_one, line_two).arrange(DOWN, buff=0.18)
        lines.to_edge(DOWN, buff=0.55)

        self.play(
            FadeOut(self.bar_a),
            FadeOut(self.tuned_word),
            FadeOut(self.held),
            run_time=0.8,
        )
        self.play(
            FadeIn(demo_side, scale=0.9),
            LaggedStartMap(FadeIn, cloud, lag_ratio=0.02, scale=0.5),
            FadeIn(cloud_label, shift=0.1 * UP),
            run_time=1.8,
        )
        self.play(FadeIn(lines, shift=0.15 * UP), run_time=1.0)
        self.wait(6.0)

    def get_cloud(self, center, count, radius=2.55, color=GREY_B, opacity=0.5, hole=0.7):
        rng = np.random.default_rng(7)
        cloud = VGroup()
        center = np.array(center, dtype=float)
        for _ in range(count):
            placed = center
            for _try in range(40):
                angle = rng.uniform(0, TAU)
                rad = rng.uniform(hole, radius)
                placed = center + np.array([
                    rad * 1.25 * np.cos(angle),
                    rad * 0.72 * np.sin(angle),
                    0,
                ])
                if np.linalg.norm(placed - center) > hole:
                    break
            dot = Dot(
                placed,
                radius=float(rng.uniform(0.045, 0.08)),
                fill_color=color,
                fill_opacity=opacity,
                stroke_width=0,
            )
            cloud.add(dot)
        return cloud

    def labeled_bar(self, name, fraction, color, count_text):
        name_label = label(name, color, 34)
        bar = score_bar(fraction, color)
        count = label(count_text, color, 28)
        count.next_to(bar, RIGHT, buff=0.22)
        name_label.next_to(bar, LEFT, buff=0.28)
        group = VGroup(name_label, bar, name_label, count)
        # name_label is referenced twice so the group stays a stable 4-tuple:
        # 0 name, 1 bar (track, fill), 2 spacer unused, 3 count.
        # Rebuild without the duplicate.
        return VGroup(name_label, bar, VectorizedPoint(), count)

    def recolor(self, dots, correct):
        animations = []
        for index, dot in enumerate(dots):
            color = GREEN if index in correct else RED_C
            animations.append(dot.animate.set_color(color))
        return LaggedStart(*animations, lag_ratio=0.05)

    def grow_fill(self, group, fraction):
        track = group[1][0]
        fill = group[1][1]
        width = track.get_width() * fraction
        return AnimationGroup(
            fill.animate.set_opacity(1).stretch_to_fit_width(width, about_edge=LEFT),
        )

    def held_out_cluster(self):
        dots = self.get_cloud(ORIGIN, 18, radius=0.95, color=YELLOW_D, opacity=0.95, hole=0.15)
        bar = score_bar(9 / N_CASES, YELLOW_D, width=2.6, height=0.28)
        count = label("9 / 20", YELLOW, 26)
        count.next_to(bar, RIGHT, buff=0.18)
        word = label("held out", YELLOW, 32)
        body = VGroup(dots, bar)
        body.arrange(DOWN, buff=0.35)
        word.next_to(body, UP, buff=0.22)
        count.next_to(bar, RIGHT, buff=0.18)
        return VGroup(word, dots, bar, count)
