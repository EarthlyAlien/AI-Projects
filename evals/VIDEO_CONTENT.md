# Why AI evals? — video content (step 1)

This file is the **source of truth** for the film. Step 2 is animating `evals/why_evals.py` to match this script. Step 3 is re-render and voiceover.

**Theme (on-screen title, every time):** `Why AI evals?`

The film **asks that question, then answers it** with one support AI. Each beat is one answer, labeled on screen:

1. Because a demo is not a measurement.
2. Because you need a frozen list and written rules.
3. Because the score shows the gap the demo hid.
4. Because a rising practice score can still be fake progress.
5. The short answer, restated.

**What this video is not:** a tool comparison. One AI the whole time.

**Audience:** a lead, PM, or engineer who has seen a glowing demo and asks *“Why would we run evals?”*

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

## Story arc — answers to “Why AI evals?”

1. **Ask the question.**
2. **Answer 1** — A demo is one chosen example.
3. **Answer 2** — An eval is a frozen checklist plus written rules.
4. **Answer 3** — The score shows what the demo hid (1/1 vs 8/20, same AI).
5. **Answer 4** — A fresh test shows whether you improved or memorized.
6. **The short answer** — three reasons, then stop.

Target length after animation: **~75–90 seconds**.

---

## Beat 0 — Ask the question

**On screen (large, stays the theme):**

- Title: `Why AI evals?`
- Line 1: `A demo is one answer.`
- Line 2: `An eval is a score on the whole job.`

**Narration:**

> Why AI evals? Because a demo is one answer someone chose to show. An eval is a score on the whole job: a list you froze first, rules for pass and fail, and a count of passes. The rest of this film is that answer, on one support assistant.

**Visual:** Text only.

**Hold:** ~4s.

---

## Beat 1 — Answer 1: a demo is not enough

**Section label:** `Why? A demo is one example.`

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

## Beat 2 — Answer 2: an eval is a frozen checklist

**Section label:** `Why? You write the list first.`

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

## Beat 3 — Answer 3: the score shows the gap (bar chart)

**Section label:** `Why? The demo hid the score.`

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

## Beat 4 — Answer 4: a fresh test keeps the score honest (line chart)

**Section label:** `Why? Practice scores can lie.`

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

> Evals are not a one-time score. The team keeps fixing the assistant. If every fix is judged on the same tickets they edit against, the practice score climbs — eight, twelve, sixteen, eighteen. Hold twenty tickets aside from day one. Never fix toward them. That fresh test stays near nine. The headline number you optimized was practice memory. The fresh test is whether customer mail actually got better. That is another reason you run evals: so “we improved” means something.

---

## Beat 5 — The short answer

**Title (same theme):** `Why AI evals?`

**Three lines, large:**

1. `To see past one demo.`
2. `To score the whole job.`
3. `To tell real progress from memorizing the test.`

**Three terms (smaller cards under the answers):**

| **Demo** | One chosen example. |
| **Eval** | Frozen checklist + rules + score. |
| **Fresh test** | Tickets kept aside while you fix. |

**Close (yellow):**

- `No frozen list and no written rules: you only have a demo.`

**Narration:**

> So: why AI evals? To see past one demo. To score the whole job. To tell real progress from memorizing the test. Demo is one chosen example. An eval is a frozen list, written rules, and a score. A fresh test is the tickets you keep aside while you fix. Without the list and the rules, you only have a demo.

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

- [x] Single AI; bar chart = `Demo` (1/1) vs `Full eval` (8/20)
- [x] Rules on the checklist beat
- [x] Fresh test section + practice/fresh line chart
- [x] Title card and closing card both read `Why AI evals?`
- [x] Match `evals/NARRATION.md`
- [x] Re-render 1080p