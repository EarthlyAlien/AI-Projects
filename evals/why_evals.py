from manimlib import *


FONT = "Liberation Sans"


def T(text, size=32, color=WHITE):
    mob = Text(str(text), font=FONT, font_size=size)
    mob.set_color(color)
    return mob


def lines(rows, size=30, color=GREY_A, buff=0.14):
    group = VGroup(*(T(row, size, color) for row in rows))
    group.arrange(DOWN, buff=buff)
    return group


def pill(word, color):
    text = T(word, 24, color)
    box = RoundedRectangle(
        width=max(text.get_width() + 0.4, 1.7),
        height=0.5,
        corner_radius=0.1,
    )
    box.set_fill(color, 0.18)
    box.set_stroke(color, 2)
    text.move_to(box)
    return VGroup(box, text)


class WhyEvals(InteractiveScene):
    def construct(self):
        self.pieces = []
        self.show_title()
        self.show_demo()
        self.show_cases()
        self.show_score()
        self.show_held_out()
        self.show_terms()

    def keep(self, *mobs):
        self.pieces.extend(mobs)
        return mobs

    def clear(self):
        if not self.pieces:
            return
        self.play(*(FadeOut(mob) for mob in self.pieces), run_time=0.45)
        self.pieces = []

    def show_title(self):
        title = T("Why AI evals matter", 64)
        subtitle = lines(
            (
                "A demo is one answer.",
                "An eval is a score on work you fixed in advance.",
            ),
            size=34,
            color=GREY_A,
            buff=0.22,
        )
        block = VGroup(title, subtitle).arrange(DOWN, buff=0.55)
        self.keep(block)
        self.play(FadeIn(title, shift=0.15 * UP), run_time=0.7)
        self.play(FadeIn(subtitle, shift=0.1 * UP), run_time=0.8)
        self.wait(3.0)
        self.clear()

    def show_demo(self):
        head, defin = self.heading(
            "Demo",
            (
                "A demo is one example,",
                "usually the one someone chose to show you.",
            ),
        )
        card = RoundedRectangle(width=9.2, height=2.15, corner_radius=0.14)
        card.set_fill(GREY_E, 1)
        card.set_stroke(GREY_B, 2)
        question = T("Customer: partial refund on a late shipment?", 30)
        answer = T("Model: Yes. The policy allows it.", 30, GREEN_B)
        words = VGroup(question, answer).arrange(DOWN, buff=0.28)
        words.move_to(card)
        ticket = VGroup(card, words)
        ticket.next_to(defin, DOWN, buff=0.45)

        mark = pill("Correct", GREEN_B)
        mark.next_to(ticket, DOWN, buff=0.35)
        note = T("True. And it is still one case.", 32, YELLOW)
        note.next_to(mark, DOWN, buff=0.35)

        self.keep(head, defin, ticket, mark, note)
        self.play(FadeIn(head), FadeIn(defin), run_time=0.7)
        self.play(FadeIn(card), Write(question), run_time=0.9)
        self.play(FadeIn(answer, shift=0.12 * UP), run_time=0.6)
        self.play(FadeIn(mark, scale=0.9), run_time=0.45)
        self.play(FadeIn(note, shift=0.1 * UP), run_time=0.5)
        self.wait(3.2)
        self.clear()

    def show_cases(self):
        head, defin = self.heading(
            "Case",
            (
                "A case is one real piece of the job.",
                "An eval is a list of cases, written down before you look.",
            ),
        )
        rows = VGroup(*(
            self.case_row(name, ok)
            for name, ok in (
                ("Partial refund on a late shipment", True),
                ("Angry caller, third time today", False),
                ("Tracking question, asked in Spanish", True),
                ("This customer should reach a person", False),
                ('"Where is my order?" and no order number', False),
            )
        ))
        rows.arrange(DOWN, buff=0.16)
        rows.next_to(defin, DOWN, buff=0.38)
        rows.set_x(0)

        tally = T("On these 5 cases: 2 right, 3 wrong.", 30, WHITE)
        tally.next_to(rows, DOWN, buff=0.32)

        self.keep(head, defin, rows, tally)
        self.play(FadeIn(head), FadeIn(defin), run_time=0.6)
        self.play(
            LaggedStart(*(FadeIn(row, shift=0.15 * RIGHT) for row in rows), lag_ratio=0.15),
            run_time=2.2,
        )
        self.play(FadeIn(tally, shift=0.1 * UP), run_time=0.5)
        self.wait(3.6)
        self.clear()

    def show_score(self):
        head, defin = self.heading(
            "Score",
            (
                "Score = correct cases / all cases.",
                "Same 20 cases. Same meaning of wrong. Both systems.",
            ),
        )
        chart = self.bar_chart()
        chart.next_to(defin, DOWN, buff=0.3)
        chart.set_x(-0.2)

        caption = T("The system that won the demo scored worse.", 32, YELLOW)
        caption.next_to(chart, DOWN, buff=0.28)

        self.keep(head, defin, chart, caption)
        self.add(chart.bars)
        self.play(FadeIn(head), FadeIn(defin), run_time=0.6)
        self.play(FadeIn(chart.axes_group), FadeIn(chart.y_name), run_time=0.7)
        self.play(
            chart.bars[0].animate.set_height(chart.full_heights[0], about_edge=DOWN, stretch=True),
            chart.bars[1].animate.set_height(chart.full_heights[1], about_edge=DOWN, stretch=True),
            run_time=1.4,
        )
        self.play(FadeIn(chart.value_labels), FadeIn(chart.names), run_time=0.5)
        self.play(FadeIn(caption, shift=0.1 * UP), run_time=0.45)
        self.wait(3.6)
        self.clear()

    def show_held_out(self):
        head, defin = self.heading(
            "Held-out set",
            (
                "Cases nobody is allowed to practice on.",
                "Once you tune on a score, that score stops measuring.",
            ),
        )
        chart = self.line_chart()
        chart.next_to(defin, DOWN, buff=0.22)
        chart.set_x(-1.15)

        legend = VGroup(
            self.legend_item("Tuned set: you practice on this", BLUE_D),
            self.legend_item("Held-out set: you do not", YELLOW_D),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        legend.next_to(chart, RIGHT, buff=0.45)
        legend.align_to(chart, UP).shift(0.35 * DOWN)

        caption = T("Blue climbs. Yellow, the real measurement, does not.", 30, WHITE)
        caption.to_edge(DOWN, buff=0.32)

        self.keep(head, defin, chart, legend, caption)
        self.add(chart.tuned_lines, chart.held_lines)
        self.play(FadeIn(head), FadeIn(defin), run_time=0.55)
        self.play(FadeIn(chart.axes_group), FadeIn(chart.x_name), FadeIn(legend), run_time=0.7)
        self.play(ShowCreation(chart.tuned_lines), run_time=1.6)
        self.play(FadeIn(chart.tuned_dots, scale=0.6), FadeIn(chart.tuned_labels), run_time=0.45)
        self.play(ShowCreation(chart.held_lines), run_time=1.3)
        self.play(
            FadeIn(chart.held_dots, scale=0.6),
            FadeIn(chart.held_labels),
            FadeIn(caption, shift=0.08 * UP),
            run_time=0.55,
        )
        self.wait(4.0)
        self.clear()

    def show_terms(self):
        title = T("The three words", 48)
        title.to_edge(UP, buff=0.38)
        cards = VGroup(
            self.term_card("Demo", "One example. Often the one picked to impress you."),
            self.term_card("Eval", "A fixed list of cases, and a written meaning of wrong."),
            self.term_card("Held-out set", "The cases nobody is allowed to practice on."),
        ).arrange(DOWN, buff=0.28)
        cards.next_to(title, DOWN, buff=0.4)
        close = T("No fixed list, no written meaning of wrong: you do not have an eval.", 28, YELLOW)
        close.next_to(cards, DOWN, buff=0.38)
        if close.get_width() > 13:
            close.set_width(13)

        self.keep(title, cards, close)
        self.play(FadeIn(title), run_time=0.4)
        self.play(
            LaggedStart(*(FadeIn(card, shift=0.12 * UP) for card in cards), lag_ratio=0.2),
            run_time=1.6,
        )
        self.play(FadeIn(close, shift=0.08 * UP), run_time=0.5)
        self.wait(4.2)

    def heading(self, word, defin_rows):
        title = T(word, 52, YELLOW)
        title.to_edge(UP, buff=0.28)
        defin = lines(defin_rows, size=30, color=GREY_A, buff=0.1)
        defin.next_to(title, DOWN, buff=0.16)
        return title, defin

    def case_row(self, name, ok):
        background = RoundedRectangle(width=12.4, height=0.68, corner_radius=0.1)
        background.set_fill(GREY_E, 1)
        background.set_stroke(GREY_D, 1.5)
        name_text = T(name, 28, WHITE)
        if name_text.get_width() > 8.4:
            name_text.set_width(8.4)
        badge = pill("Right" if ok else "Wrong", GREEN_B if ok else RED_C)
        name_text.next_to(background.get_left(), RIGHT, buff=0.28)
        badge.next_to(background.get_right(), LEFT, buff=0.22)
        name_text.set_y(background.get_y())
        badge.set_y(background.get_y())
        return VGroup(background, name_text, badge)

    def bar_chart(self):
        axes = Axes(
            x_range=(0, 3, 1),
            y_range=(0, 20, 5),
            height=3.7,
            width=6.2,
            axis_config=dict(
                stroke_color=GREY_B,
                stroke_width=2.5,
                include_tip=False,
                include_ticks=False,
                include_numbers=False,
            ),
        )
        guide = Line(axes.c2p(0.15, 10), axes.c2p(2.85, 10), stroke_color=GREY_C, stroke_width=1.5)
        guide.set_stroke(opacity=0.55)
        y_labels = VGroup()
        for value in (0, 10, 20):
            tick = T(str(value), 24, GREY_A)
            tick.next_to(axes.c2p(0, value), LEFT, buff=0.16)
            y_labels.add(tick)
        y_name = T("correct cases", 24, GREY_B)
        y_name.next_to(y_labels, UP, buff=0.12)

        values = (8, 15)
        colors = (BLUE_D, TEAL_D)
        names = ("Won the demo", "Lost the demo")
        bars = VGroup()
        full_heights = []
        for index, (value, color) in enumerate(zip(values, colors), start=1):
            left = axes.c2p(index - 0.28, 0)
            right = axes.c2p(index + 0.28, value)
            bar = Rectangle(width=right[0] - left[0], height=right[1] - left[1])
            bar.set_fill(color, 1)
            bar.set_stroke(width=0)
            bar.move_to(axes.c2p(index, 0), DOWN)
            full_heights.append(bar.get_height())
            bar.set_height(0.06, about_edge=DOWN, stretch=True)
            bars.add(bar)

        value_labels = VGroup()
        name_labels = VGroup()
        for index, (value, color, name) in enumerate(zip(values, colors, names), start=1):
            value_label = T(f"{value} / 20", 28, color)
            value_label.next_to(axes.c2p(index, value), UP, buff=0.12)
            name_label = T(name, 24, color)
            name_label.next_to(axes.c2p(index, 0), DOWN, buff=0.22)
            value_labels.add(value_label)
            name_labels.add(name_label)

        chart = VGroup(axes, guide, y_labels, y_name, bars, value_labels, name_labels)
        chart.axes_group = VGroup(axes, guide, y_labels)
        chart.y_name = y_name
        chart.bars = bars
        chart.full_heights = full_heights
        chart.value_labels = value_labels
        chart.names = name_labels
        return chart

    def line_chart(self):
        axes = Axes(
            x_range=(0.5, 4.6, 1),
            y_range=(0, 20, 5),
            height=3.35,
            width=6.4,
            axis_config=dict(
                stroke_color=GREY_B,
                stroke_width=2.5,
                include_tip=False,
                include_ticks=False,
                include_numbers=False,
            ),
        )
        guide = Line(axes.c2p(0.7, 10), axes.c2p(4.4, 10), stroke_color=GREY_C, stroke_width=1.5)
        guide.set_stroke(opacity=0.55)
        y_labels = VGroup()
        for value in (0, 10, 20):
            tick = T(str(value), 22, GREY_A)
            tick.next_to(axes.c2p(0.5, value), LEFT, buff=0.14)
            y_labels.add(tick)
        y_name = T("correct cases", 22, GREY_B)
        y_name.next_to(y_labels, UP, buff=0.1)
        week_labels = VGroup()
        for week in range(1, 5):
            tick = T(str(week), 24, GREY_A)
            tick.next_to(axes.c2p(week, 0), DOWN, buff=0.16)
            week_labels.add(tick)
        x_name = T("week", 24, GREY_B)
        x_name.next_to(week_labels, DOWN, buff=0.1)

        tuned_values = (8, 12, 16, 18)
        held_values = (9, 9, 8, 9)
        tuned_lines, tuned_dots = self.series(axes, tuned_values, BLUE_D)
        held_lines, held_dots = self.series(axes, held_values, YELLOW_D)
        tuned_labels = VGroup()
        held_labels = VGroup()
        for index, (tuned, held) in enumerate(zip(tuned_values, held_values), start=1):
            tuned_label = T(str(tuned), 24, BLUE_B)
            held_label = T(str(held), 24, YELLOW)
            if abs(tuned - held) <= 2:
                tuned_label.move_to(axes.c2p(index - 0.28, 12.4))
                held_label.next_to(axes.c2p(index, held), DOWN, buff=0.42)
            else:
                tuned_label.next_to(axes.c2p(index, tuned), UP, buff=0.12)
                held_label.next_to(axes.c2p(index, held), DOWN, buff=0.12)
            tuned_labels.add(tuned_label)
            held_labels.add(held_label)

        chart = VGroup(
            axes, guide, y_labels, y_name, week_labels, x_name,
            tuned_lines, tuned_dots, tuned_labels,
            held_lines, held_dots, held_labels,
        )
        chart.axes_group = VGroup(axes, guide, y_labels, y_name, week_labels)
        chart.x_name = x_name
        chart.tuned_lines = tuned_lines
        chart.tuned_dots = tuned_dots
        chart.tuned_labels = tuned_labels
        chart.held_lines = held_lines
        chart.held_dots = held_dots
        chart.held_labels = held_labels
        return chart

    def series(self, axes, values, color):
        points = [axes.c2p(index, value) for index, value in enumerate(values, start=1)]
        segments = VGroup(*(
            Line(start, end, stroke_color=color, stroke_width=7)
            for start, end in zip(points, points[1:])
        ))
        dots = VGroup(*(Dot(point, radius=0.075, fill_color=color) for point in points))
        return segments, dots

    def legend_item(self, text, color):
        swatch = Square(side_length=0.28)
        swatch.set_fill(color, 1)
        swatch.set_stroke(width=0)
        words = T(text, 24, color)
        if words.get_width() > 4.3:
            words.set_width(4.3)
        words.next_to(swatch, RIGHT, buff=0.16)
        return VGroup(swatch, words)

    def term_card(self, word, meaning):
        name = T(word, 34, YELLOW)
        body = T(meaning, 28, WHITE)
        if body.get_width() > 10.2:
            body.set_width(10.2)
        text = VGroup(name, body).arrange(DOWN, buff=0.12)
        card = RoundedRectangle(
            width=12.2,
            height=text.get_height() + 0.42,
            corner_radius=0.12,
        )
        card.set_fill(GREY_E, 1)
        card.set_stroke(GREY_B, 1.5)
        text.move_to(card)
        return VGroup(card, text)
