# Why AI evals matter — video content (step 1)

This file is the **source of truth** for the film. Step 2 is animating `evals/why_evals.py` to match this script. Step 3 is re-render and voiceover.

**What this video is for:** explain **why evals matter** when you build or ship AI — so you are not fooled by a good demo, you know how the system does on real work, and you can tell improvement from memorizing the test.

**What this video is not:** a comparison between two tools or vendors. There is **one** support AI the whole time. The story is **demo → proper eval → honest improvement**.

**Audience:** a lead, PM, or engineer who has seen a glowing demo and needs to decide *“How do we actually know if this works?”*

**Setting:** customer-email support for a shipping company. Same AI throughout.

**Rule for language:** say what happened in plain words first, then use the term once in bold.

---

## Glossary (use these words consistently)

| Term | Say this on screen | Do not say |
|------|-------------------|------------|
| **Demo** | One example someone **chose to show** | Tool A vs tool B |
| **Test case** | One real situation the AI must handle | “Case” without context |
| **Checklist** | The **fixed list** of test cases, frozen **before** testing | “Dataset” on first mention |
| **Pass / Fail** | Meets **written rules** or not | Vibes, “seemed fine” |
| **Eval** | Run the **whole checklist** and **count passes** | “Benchmark” first |
| **Score** | Passes ÷ total tickets on that checklist | Lead with accuracy % |
| **Practice list** | Tickets the team **uses while fixing** | “Training set” first |
| **Fresh test** | Tickets **kept aside** — never used while fixing | “Held-out” first (add once in parentheses) |

---

## Story arc (six beats)

1. **Hook** — Demos feel like proof; they are not measurement.
2. **Demo** — One ticket, one pass, looks like success.
3. **Checklist** — Real eval: frozen list + written rules.
4. **The gap** — Same AI: 1/1 on the demo vs 8/20 on the full eval.
5. **Honest improvement** — Practice score rises; fresh test does not → why eval design matters.
6. **Recap** — What evals give you (truth, progress, trust).

Target length after animation: **~75–90 seconds**.

---

## Beat 0 — Title / hook

**On screen:**

- Title: `Why AI evals matter`
- Line 1: `A demo shows one answer.`
- Line 2: `An eval measures the job.`

**Narration:**

> Teams ship AI on demos. One answer looks perfect in the room. That is not measurement. It does not tell you how the system does on a normal week, whether you are improving, or whether you are ready to roll out. Evals exist for that: a fixed list of real situations, rules for pass and fail, and a score you can track.

**Visual:** Text only.

**Hold:** ~4s.

---

## Beat 1 — Demo

**Section label:** `Demo`

**Definition:**

- `A demo is one example.`
- `Often the one someone picked to look good.`

**Card:**

- Customer: `Can I get a partial refund? My box arrived two weeks late.`
- AI: `Yes. Our policy allows a partial refund for late delivery.`
- Badge: `Pass`

**Punch line (yellow):**

- `One ticket. One pass. Easy to mistake that for “it works.”`

**Narration:**

> Here is the demo. One email. The AI answers well. Mark it pass. Stakeholders nod. If you stop here, you only know how the AI did on **one** message someone selected. You do not know how it does on the rest of the job.

---

## Beat 2 — Test cases, rules, checklist

**Section label:** `Eval`

**Definition:**

- `An eval = frozen checklist + written rules + pass count.`
- `Write the list before you run the AI.`

**Rules card:**

- `Rules (frozen before testing):`
  - `Wrong policy or invented fact → Fail`
  - `Customer asks for a human → must hand off → Fail`

**Five rows (sample of the full list):**

| Customer situation | Result |
|-------------------|--------|
| Partial refund, late package (same as demo) | **Pass** |
| Customer wanted to cancel; AI offered a refund | **Fail** |
| Tracking question in Spanish | **Pass** |
| “I need a person” — third angry email | **Fail** |
| “Where is my order?” — no order number | **Fail** |

**Footer:** `On these 5: 2 pass, 3 fail.`

**Bridge:** `Full eval here: 20 tickets, same rules, list frozen before anyone runs the model.`

**Narration:**

> An eval starts before you click run. Freeze the checklist. Write what fail means. Same refund ticket: pass. Cancel confused with refund: fail. Spanish tracking: pass. No human when they asked: fail. Order status with no ID: fail. Two of five pass on this slice. The real eval runs twenty tickets like these — not one cherry-picked email.

---

## Beat 3 — Why the demo misled you (bar chart)

**Section label:** `Score`

**Definition:**

- `Score = passes ÷ tickets on the checklist`
- `Same AI. Different size of test.`

**Chart — two bars, one AI, same y-axis 0–20**

| Bar label (under axis) | Height (passes) | Label on bar | Meaning |
|------------------------|-----------------|--------------|---------|
| `Demo` | **1** | `1 / 1` | Only this ticket was tested |
| `Full eval` | **8** | `8 / 20` | Whole frozen checklist |

**Caption (yellow):**

- `One pass on one ticket is not “the AI works.” Eight passes on twenty is a measurement.`

**Narration:**

> Count passes. On the demo you effectively tested one ticket: one pass out of one. On the full eval, the **same** assistant gets eight passes out of twenty. The demo was not lying — that answer was fine. It was **incomplete**. Without the eval you would roll out on a highlight reel. With it you see the real gap.

**Intuition check:** No second product. Viewer sees *breadth of testing* as the lesson.

**Animation:** Grow both bars; hold on `1/1` vs `8/20`.

---

## Beat 4 — Why eval *design* matters (line chart)

**Section label:** `Fresh test`

**Definition:**

- `Split the checklist: practice tickets vs fresh tickets.`
- `Fix the AI using practice only. Fresh test = held-out set.`

**Setup line (on screen):**

- `The team fixes failures on the practice list every week.`

**Line chart**

- X: `Week` 1–4
- Y: `Passes (out of 20)`

| Week | Practice tickets (fix using these) | Fresh tickets (never used while fixing) |
|------|-------------------------------------|----------------------------------------|
| 1 | 8 | 9 |
| 2 | 12 | 9 |
| 3 | 16 | 8 |
| 4 | 18 | 9 |

**Legend:**

- Blue: `Practice list`
- Yellow: `Fresh test`

**Caption:**

- `You can raise the practice score and still not improve on new mail.`

**Narration:**

> Evals are not a one-time score. The team keeps fixing the assistant. If every fix is judged on the same tickets they edit against, the practice score climbs — eight, twelve, sixteen, eighteen. Hold twenty tickets aside from day one. Never fix toward them. That fresh test stays near nine. The headline number you optimized was practice memory. The fresh test is whether customer mail actually got better. That is why eval design matters.

---

## Beat 5 — Recap (why evals matter)

**Title:** `Why bother with evals?`

**Three bullets (on screen):**

1. **See past the demo** — know pass rate on real situations, not one highlight.
2. **Track real progress** — separate “we memorized the test” from “we improved.”
3. **Ship with evidence** — rollout, pause, or fix based on a score, not a meeting.

**Three terms (compact cards):**

| **Demo** | One chosen example. |
| **Eval** | Frozen checklist + rules + score. |
| **Fresh test** | Tickets kept aside while you fix. |

**Close (yellow):**

- `No frozen checklist and no written rules → you only have demos.`

**Narration:**

> Why evals matter. They show what one good answer hid. They give you a number while you build. They stop you from claiming victory because the practice test got easier. Demo: one example. Eval: frozen list, rules, score. Fresh test: honest check while you improve. Without those, you are guessing.

---

## Numbers cheat sheet

- Five-ticket sample: **2 pass, 3 fail**
- Full checklist: **20 tickets**
- Demo measurement: **1 / 1**
- Full eval (same AI): **8 / 20**
- Practice line: **8 → 12 → 16 → 18**
- Fresh line: **9, 9, 8, 9**

---

## Retired ideas (do not bring back)

- Two products, “won the demo,” vendor bake-off, 8 vs 15 as a **comparison** story.
- Any bar chart that implies picking between tools.

---

## Step 2 checklist (animation)

- [ ] Single AI; bar chart = `Demo` (1/1) vs `Full eval` (8/20)
- [ ] Rules card on checklist beat
- [ ] `Fresh test` section + practice/fresh line chart
- [ ] Recap beat: *why evals matter* bullets + three terms
- [ ] Match `evals/NARRATION.md`
- [ ] Re-render 1080p