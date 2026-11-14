from manimlib import *


FONT = "Liberation Sans"


def T(text, size=32, color=WHITE):
    mob = Text(str(text), font=FONT, font_size=size)
    mob.set_color(color)
    return mob


def lines(rows, size=30, color=GREY_A, buff=0.12):
    group = VGroup(*(T(row, size, color) for row in rows))
    group.arrange(DOWN, buff=buff)
    return group


def pill(word, color):
    text = T(word, 22, color)
    box = RoundedRectangle(
        width=max(text.get_width() + 0.36, 1.45),
        height=0.42,
        corner_radius=0.1,
    )
    box.set_fill(color, 0.18)
    box.set_stroke(color, 2)
    text.move_to(box)
    return VGroup(box, text)


class WhyEvals(InteractiveScene):
    def construct(self):
        self.pieces = []
        self.ask()
        self.show_demo()
        self.show_checklist()
        self.show_score()
        self.show_fresh()
        self.show_answer()

    def keep(self, *mobs):
        self.pieces.extend(mobs)
        return mobs

    def clear(self):
        if not self.pieces:
            return
        self.play(*(FadeOut(mob) for mob in self.pieces), run_time=0.4)
        self.pieces = []

    def ask(self):
        title = T("Why AI evals?", 68, YELLOW)
        subtitle = lines(
            (
                "A demo is one answer.",
                "An eval is a score on the whole job.",
            ),
            size=36,
            color=WHITE,
            buff=0.2,
        )
        block = VGroup(title, subtitle).arrange(DOWN, buff=0.5)
        self.keep(block)
        self.play(FadeIn(title, shift=0.12 * UP), run_time=0.7)
        self.play(FadeIn(subtitle, shift=0.08 * UP), run_time=0.8)
        self.wait(4.5)
        self.clear()

    def show_demo(self):
        head, defin = self.heading(
            "Why? A demo is one example.",
            (
                "A demo is one example.",
                "Often the one someone picked to look good.",
            ),
        )
        card = RoundedRectangle(width=12.2, height=2.05, corner_radius=0.12)
        card.set_fill(GREY_E, 1)
        card.set_stroke(GREY_B, 2)
        question = T("Customer: partial refund? The box was two weeks late.", 28)
        answer = T("AI: Yes. Policy allows a partial refund for late delivery.", 28, GREEN_B)
        words = VGroup(question, answer).arrange(DOWN, buff=0.22)
        for word in words:
            if word.get_width() > 11.2:
                word.set_width(11.2)
        words.move_to(card)
        ticket = VGroup(card, words)
        ticket.next_to(defin, DOWN, buff=0.32)
        mark = pill("Pass", GREEN_B)
        mark.next_to(ticket, DOWN, buff=0.28)
        note = T('One ticket. One pass. Easy to call that "it works."', 30, YELLOW)
        if note.get_width() > 13:
            note.set_width(13)
        note.next_to(mark, DOWN, buff=0.28)

        self.keep(head, defin, ticket, mark, note)
        self.play(FadeIn(head), FadeIn(defin), run_time=0.6)
        self.play(FadeIn(card), FadeIn(question), run_time=0.7)
        self.play(FadeIn(answer, shift=0.08 * UP), run_time=0.5)
        self.play(FadeIn(mark, scale=0.9), run_time=0.4)
        self.play(FadeIn(note, shift=0.08 * UP), run_time=0.45)
        self.wait(5.0)
        self.clear()

    def show_checklist(self):
        head, defin = self.heading(
            "Why? You write the list first.",
            (
                "An eval = frozen checklist + written rules + pass count.",
                "Write the list before you run the AI.",
            ),
            title_size=40,
            body_size=26,
        )
        rules = lines(
            (
                "Rules, frozen first:",
                "Wrong policy or invented fact  →  Fail",
                "Asks for a human, no handoff  →  Fail",
            ),
            size=24,
            color=GREY_A,
            buff=0.06,
        )
        rules.next_to(defin, DOWN, buff=0.18)
        rows = VGroup(*(
            self.case_row(name, ok)
            for name, ok in (
                ("Partial refund, late package", True),
                ("Wanted to cancel; AI offered a refund", False),
                ("Tracking question, in Spanish", True),
                ("I need a person. Third angry email.", False),
                ('"Where is my order?" No order number.', False),
            )
        ))
        rows.arrange(DOWN, buff=0.1)
        rows.next_to(rules, DOWN, buff=0.18)
        tally = T("On these 5: 2 pass, 3 fail.   Full eval: 20 tickets, same rules.", 26, WHITE)
        if tally.get_width() > 13:
            tally.set_width(13)
        tally.next_to(rows, DOWN, buff=0.18)

        self.keep(head, defin, rules, rows, tally)
        self.play(FadeIn(head), FadeIn(defin), FadeIn(rules), run_time=0.7)
        self.play(
            LaggedStart(*(FadeIn(row, shift=0.12 * RIGHT) for row in rows), lag_ratio=0.12),
            run_time=1.8,
        )
        self.play(FadeIn(tally, shift=0.06 * UP), run_time=0.45)
        self.wait(5.5)
        self.clear()

    def show_score(self):
        head, defin = self.heading(
            "Why? The demo hid the score.",
            (
                "Score = passes ÷ tickets on the checklist.",
                "Same AI. The demo tested one ticket. The eval tests twenty.",
            ),
            title_size=42,
            body_size=28,
        )
        chart = self.bar_chart()
        chart.next_to(defin, DOWN, buff=0.28)
        caption = lines(
            (
                'One pass on one ticket is not "the AI works."',
                "Eight passes on twenty is a measurement.",
            ),
            size=30,
            color=YELLOW,
            buff=0.1,
        )
        caption.next_to(chart, DOWN, buff=0.28)

        self.keep(head, defin, chart, caption)
        self.add(chart.bars)
        self.play(FadeIn(head), FadeIn(defin), run_time=0.55)
        self.play(FadeIn(chart.axes_group), FadeIn(chart.y_name), run_time=0.6)
        self.play(
            chart.bars[0].animate.set_height(chart.full_heights[0], about_edge=DOWN, stretch=True),
            chart.bars[1].animate.set_height(chart.full_heights[1], about_edge=DOWN, stretch=True),
            run_time=1.4,
        )
        self.play(FadeIn(chart.value_labels), FadeIn(chart.names), run_time=0.45)
        self.play(FadeIn(caption, shift=0.08 * UP), run_time=0.45)
        self.wait(5.5)
        self.clear()

    def show_fresh(self):
        head, defin = self.heading(
            "Why? Practice scores can lie.",
            (
                "Fix the AI on the practice list only.",
                "A fresh test (a held-out set) is never used while fixing.",
            ),
            title_size=42,
            body_size=28,
        )
        chart = self.line_chart()
        chart.next_to(defin, DOWN, buff=0.16)
        chart.set_x(-1.2)
        legend = VGroup(
            self.legend_item("Practice list", BLUE_D),
            self.legend_item("Fresh test", YELLOW_D),
        ).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        legend.next_to(chart, RIGHT, buff=0.4)
        legend.align_to(chart, UP).shift(0.3 * DOWN)
        caption = T("The practice score rises. New mail does not.", 30, YELLOW)
        caption.to_edge(DOWN, buff=0.28)

        self.keep(head, defin, chart, legend, caption)
        self.add(chart.tuned_lines, chart.held_lines)
        self.play(FadeIn(head), FadeIn(defin), run_time=0.55)
        self.play(FadeIn(chart.axes_group), FadeIn(chart.x_name), FadeIn(legend), run_time=0.6)
        self.play(ShowCreation(chart.tuned_lines), run_time=1.4)
        self.play(FadeIn(chart.tuned_dots, scale=0.6), FadeIn(chart.tuned_labels), run_time=0.4)
        self.play(ShowCreation(chart.held_lines), run_time=1.2)
        self.play(
            FadeIn(chart.held_dots, scale=0.6),
            FadeIn(chart.held_labels),
            FadeIn(caption, shift=0.06 * UP),
            run_time=0.5,
        )
        self.wait(5.5)
        self.clear()

    def show_answer(self):
        title = T("Why AI evals?", 56, YELLOW)
        title.to_edge(UP, buff=0.32)
        answers = lines(
            (
                "To see past one demo.",
                "To score the whole job.",
                "To tell real progress from memorizing the test.",
            ),
            size=32,
            color=WHITE,
            buff=0.14,
        )
        answers.next_to(title, DOWN, buff=0.32)
        cards = VGroup(
            self.term_card("Demo", "One chosen example."),
            self.term_card("Eval", "Frozen checklist, rules, and a score."),
            self.term_card("Fresh test", "Tickets kept aside while you fix."),
        ).arrange(DOWN, buff=0.16)
        cards.next_to(answers, DOWN, buff=0.32)
        close = T("No frozen list and no written rules: you only have a demo.", 28, YELLOW)
        if close.get_width() > 13:
            close.set_width(13)
        close.next_to(cards, DOWN, buff=0.28)

        self.keep(title, answers, cards, close)
        self.play(FadeIn(title), run_time=0.4)
        self.play(
            LaggedStart(*(FadeIn(line, shift=0.08 * UP) for line in answers), lag_ratio=0.2),
            run_time=1.3,
        )
        self.play(
            LaggedStart(*(FadeIn(card, shift=0.08 * UP) for card in cards), lag_ratio=0.15),
            run_time=1.2,
        )
        self.play(FadeIn(close, shift=0.06 * UP), run_time=0.45)
        self.wait(5.5)

    def heading(self, word, defin_rows, title_size=44, body_size=28):
        title = T(word, title_size, YELLOW)
        if title.get_width() > 13:
            title.set_width(13)
        title.to_edge(UP, buff=0.28)
        defin = lines(defin_rows, size=body_size, color=GREY_A, buff=0.08)
        defin.next_to(title, DOWN, buff=0.14)
        return title, defin

    def case_row(self, name, ok):
        background = RoundedRectangle(width=12.6, height=0.52, corner_radius=0.08)
        background.set_fill(GREY_E, 1)
        background.set_stroke(GREY_D, 1.5)
        name_text = T(name, 24, WHITE)
        if name_text.get_width() > 8.6:
            name_text.set_width(8.6)
        badge = pill("Pass" if ok else "Fail", GREEN_B if ok else RED_C)
        name_text.next_to(background.get_left(), RIGHT, buff=0.22)
        badge.next_to(background.get_right(), LEFT, buff=0.16)
        name_text.set_y(background.get_y())
        badge.set_y(background.get_y())
        return VGroup(background, name_text, badge)

    def bar_chart(self):
        axes = Axes(
            x_range=(0, 3, 1),
            y_range=(0, 20, 5),
            height=3.15,
            width=6.4,
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
            tick = T(str(value), 22, GREY_A)
            tick.next_to(axes.c2p(0, value), LEFT, buff=0.14)
            y_labels.add(tick)
        y_name = T("passes", 22, GREY_B)
        y_name.next_to(y_labels, UP, buff=0.08)

        values = (1, 8)
        colors = (BLUE_D, TEAL_D)
        names = ("Demo", "Full eval")
        fractions = ("1 / 1", "8 / 20")
        bars = VGroup()
        full_heights = []
        for index, (value, color) in enumerate(zip(values, colors), start=1):
            left = axes.c2p(index - 0.28, 0)
            right = axes.c2p(index + 0.28, value)
            bar = Rectangle(width=right[0] - left[0], height=max(right[1] - left[1], 0.08))
            bar.set_fill(color, 1)
            bar.set_stroke(width=0)
            bar.move_to(axes.c2p(index, 0), DOWN)
            full_heights.append(bar.get_height())
            bar.set_height(0.05, about_edge=DOWN, stretch=True)
            bars.add(bar)

        value_labels = VGroup()
        name_labels = VGroup()
        for index, (value, color, name, fraction) in enumerate(
            zip(values, colors, names, fractions), start=1
        ):
            value_label = T(fraction, 28, color)
            value_label.next_to(axes.c2p(index, value), UP, buff=0.14)
            name_label = T(name, 26, color)
            name_label.next_to(axes.c2p(index, 0), DOWN, buff=0.2)
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
            height=3.05,
            width=6.2,
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
            tick = T(str(value), 20, GREY_A)
            tick.next_to(axes.c2p(0.5, value), LEFT, buff=0.12)
            y_labels.add(tick)
        y_name = T("passes", 20, GREY_B)
        y_name.next_to(y_labels, UP, buff=0.06)
        week_labels = VGroup()
        for week in range(1, 5):
            tick = T(str(week), 22, GREY_A)
            tick.next_to(axes.c2p(week, 0), DOWN, buff=0.12)
            week_labels.add(tick)
        x_name = T("week", 22, GREY_B)
        x_name.next_to(week_labels, DOWN, buff=0.06)

        tuned_values = (8, 12, 16, 18)
        held_values = (9, 9, 8, 9)
        tuned_lines, tuned_dots = self.series(axes, tuned_values, BLUE_D)
        held_lines, held_dots = self.series(axes, held_values, YELLOW_D)
        tuned_labels = VGroup()
        held_labels = VGroup()
        for index, (tuned, held) in enumerate(zip(tuned_values, held_values), start=1):
            tuned_label = T(str(tuned), 22, BLUE_B)
            held_label = T(str(held), 22, YELLOW)
            if abs(tuned - held) <= 2:
                tuned_label.move_to(axes.c2p(index - 0.28, 12.4))
                held_label.next_to(axes.c2p(index, held), DOWN, buff=0.36)
            else:
                tuned_label.next_to(axes.c2p(index, tuned), UP, buff=0.1)
                held_label.next_to(axes.c2p(index, held), DOWN, buff=0.1)
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
        dots = VGroup(*(Dot(point, radius=0.07, fill_color=color) for point in points))
        return segments, dots

    def legend_item(self, text, color):
        swatch = Square(side_length=0.26)
        swatch.set_fill(color, 1)
        swatch.set_stroke(width=0)
        words = T(text, 24, color)
        words.next_to(swatch, RIGHT, buff=0.14)
        return VGroup(swatch, words)

    def term_card(self, word, meaning):
        name = T(word, 28, YELLOW)
        body = T(meaning, 24, WHITE)
        text = VGroup(name, body).arrange(DOWN, buff=0.08)
        card = RoundedRectangle(
            width=12.2,
            height=text.get_height() + 0.28,
            corner_radius=0.1,
        )
        card.set_fill(GREY_E, 1)
        card.set_stroke(GREY_B, 1.5)
        text.move_to(card)
        return VGroup(card, text)
