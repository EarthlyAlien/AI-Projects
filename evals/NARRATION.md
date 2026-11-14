# Why AI evals matter — voiceover

Read this with the picture. Full storyboard and chart labels: [VIDEO_CONTENT.md](VIDEO_CONTENT.md).

Pace: plain situation first, then the term. Pause on each chart until the numbers are readable.

---

## Title / hook

In a sales call you see one perfect answer. That is a demo. It is not proof the AI works on your real week of customer mail.

An eval is different: you write the situations first, you write what counts as wrong, you run the AI on all of them, and you count passes.

---

## Demo

Here is the demo. One customer email. The box arrived two weeks late. The customer asks for a partial refund.

The AI says yes, and the policy really does allow that refund. Mark it pass.

That is still a single test case. The vendor chose this email. You have not seen the other messages from a normal week.

---

## Test case and checklist

A test case is one situation the AI must handle.

Before you run the model, you freeze a checklist. You write the rules first. Wrong policy or made-up fact: fail. Customer asks for a human and the AI keeps chatting: fail.

Partial refund on a late box: pass. Customer wanted to cancel; the AI offered a refund instead: fail. Tracking question in Spanish: pass. Third angry email, still no human: fail. “Where is my order?” with no order number: fail.

Two passes, three fails on five.

A real eval runs the full list — twenty tickets here — frozen before anyone runs the AI. Same rules. You do not add tickets just because the model failed.

---

## Score

Now the score. Twenty frozen tickets. Same pass/fail rules for both assistants.

The product they showed in the demo: eight passes out of twenty.

The other product: fifteen out of twenty.

The one that looked better in the meeting scored lower on the full checklist, because the meeting only showed one email.

---

## Fresh test

Some tickets stay aside from day one. The team never uses them while fixing the product. That is the fresh test. Evaluation teams call it a held-out set.

Week by week, the score on the practice list climbs: eight, twelve, sixteen, eighteen.

The fresh test stays near nine.

The number you keep improving is a report card for the practice list. The fresh test is still the honest check.

---

## Recap

Demo: one example, usually picked to impress you.

Eval: a frozen checklist, written rules, and a pass count.

Fresh test: tickets you never use while fixing the AI.

Without the checklist frozen first and fail defined in writing, you do not have an eval. You have a demo.