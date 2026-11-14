# Why AI evals matter — video content (step 1)

This file is the **source of truth** for the film. Step 2 is animating `evals/why_evals.py` to match this script. Step 3 is re-render and voiceover.

**Audience:** someone who has seen an AI demo in a meeting and wants to know whether the product actually works.

**One story all the way through:** a support team picks between two AI assistants for customer email. The vendor demos one refund question. The buyer still needs a fair way to choose.

**Rule for language:** say what happened in plain words first, then use the term in bold once.

---

## Glossary (use these words consistently)

| Term | Say this on screen | Do not say |
|------|-------------------|------------|
| **Demo** | One example someone **chose to show you** | "Won the demo" as a product name |
| **Test case** | One real situation the AI must handle | "Case" alone without context |
| **Checklist** | The **fixed list** of test cases, written **before** anyone runs the AI | "Dataset" |
| **Pass / Fail** | Right or wrong against **written rules** | "Correct / incorrect" only |
| **Eval** | Run the **whole checklist** and **count passes** | "Benchmark" on first mention |
| **Score** | Passes ÷ total on that checklist | Accuracy % (until after the fraction) |
| **Practice list** | Tickets the team **uses while fixing** the AI | "Tuned set" on first mention |
| **Fresh test** | Tickets **kept aside** — **no fixes** using these | "Held-out set" on first mention (add in parentheses once) |

---

## Story arc (six beats)

1. **Hook** — One great answer is not proof.
2. **Demo** — What a demo is.
3. **Checklist** — From one ticket to many, with rules.
4. **Score** — Same checklist, two products, count passes.
5. **Practice vs fresh** — Fixing on the practice list stops measuring real skill.
6. **Recap** — Demo vs eval vs fresh test.

Target length after animation: **~75–90 seconds** (longer holds than the 43s cut; read speed for business viewers).

---

## Beat 0 — Title / hook

**On screen (large):**

- Title: `Why AI evals matter`
- Line 1: `A demo is one answer.`
- Line 2: `An eval counts passes on a list you fixed first.`

**Narration:**

> In a sales call you see one perfect answer. That is a demo. It is not proof the AI works on your real week of customer mail. An eval is different: you write the situations first, write what counts as wrong, run the AI on all of them, and count passes.

**Visual:** Text only. No chart.

**Hold:** ~4s on the two lines after they appear.

---

## Beat 1 — Demo

**Section label:** `Demo`

**Definition (on screen):**

- `A demo is one example.`
- `Usually the one the seller picked to show you.`

**Concrete example (card):**

- Customer message: `Can I get a partial refund? My box arrived two weeks late.`
- AI reply: `Yes. Our policy allows a partial refund for late delivery.`
- Badge: `Pass` (green) — against the written rule: *refund allowed for late delivery*

**Punch line (yellow):**

- `Right on this message. Still only one message.`

**Narration:**

> Here is the demo. One customer email. The AI answers well. The policy really does allow that refund. Mark it pass. That is still a single test case. The vendor chose this email. You have not seen the other ninety-nine messages from a normal week.

**Visual:** Ticket card + pass badge. No chart.

**Intuition check:** Viewer should think: *“Okay, one good email isn’t enough.”*

---

## Beat 2 — Test case → checklist → eval setup

**Section label:** `Test case`

**Definition:**

- `A test case is one situation the AI must handle.`
- `An eval uses a checklist of test cases.`

**Sub-beat 2a — Rules (small card above the list):**

- `Rules (written before testing):`
  - `Wrong policy or made-up fact → Fail`
  - `Must hand off to a human when the customer asks → Fail`

**Checklist (five rows, stagger in):**

| # | Customer situation | Result |
|---|-------------------|--------|
| 1 | Partial refund, package late (same as demo) | **Pass** |
| 2 | Customer wants to cancel order; AI offers a refund instead | **Fail** |
| 3 | “Where is my tracking?” — email in Spanish | **Pass** |
| 4 | “I need a person.” Third angry email today. | **Fail** |
| 5 | “Where is my order?” — no order number in the thread | **Fail** |

**Footer:**

- `On these 5: 2 pass, 3 fail.`

**Bridge line (before next beat):**

- `Five tickets is a sample. A real eval uses the full checklist — here, 20 tickets — frozen before anyone runs the AI.`

**Narration:**

> A test case is one slice of the job. Before you run the model, you freeze a checklist. You write what counts as fail. Partial refund on a late box: pass. Cancel mix-up: fail. Spanish tracking: pass. Human handoff ignored: fail. Order status with no order ID: fail. Two passes, three fails on five. A real eval runs the full list. Same rules. No adding tickets because the model failed.

**Visual:** Rule card + five rows. No chart yet.

---

## Beat 3 — Score (bar chart)

**Section label:** `Score`

**Definition:**

- `Score = passes ÷ all test cases on the checklist`
- `Same 20 tickets. Same rules. Two products.`

**Chart — bar chart**

- Y-axis label: `Passes (out of 20)`
- Y ticks: `0`, `10`, `20`
- Horizontal guide at 10 (optional, faint)

| Bar position | Bar label (under axis) | Value on bar | Color role |
|--------------|------------------------|--------------|------------|
| Left | `Product from the demo` | `8 / 20` | Blue — the one they showed |
| Right | `The other product` | `15 / 20` | Teal — not shown in the call |

**Caption (yellow):**

- `The product that looked better in the meeting scored lower on the full checklist.`

**Why these labels:** “Won the demo” / “Lost the demo” sounds like sports and hides that both are measured on the **same** checklist. “Product from the demo” vs “The other product” states the comparison directly.

**Narration:**

> Now the score. Twenty frozen tickets. Same pass/fail rules for both assistants. Count passes. The product they demoed: eight out of twenty. The other product: fifteen out of twenty. The one that wowed the room is weaker on the work you care about — because the room only saw one email.

**Animation:** Axes fade in → bars grow from zero → values and labels → caption.

**Intuition check:** Taller bar = more passes = better. No inverted logic.

---

## Beat 4 — Practice list vs fresh test (line chart)

**Section label:** `Fresh test`

**Definition (introduce term once):**

- `Keep some tickets aside. Never use them while fixing the AI.`
- `That is a fresh test (evals call it a held-out set).`

**Chart — line chart**

- X-axis: `Week` — `1`, `2`, `3`, `4`
- Y-axis: `Passes (out of 20)`

| Week | Practice list | Fresh test |
|------|---------------|------------|
| 1 | 8 | 9 |
| 2 | 12 | 9 |
| 3 | 16 | 8 |
| 4 | 18 | 9 |

**Legend:**

- Blue: `Practice list (used while fixing)`
- Yellow: `Fresh test (not used while fixing)`

**Caption:**

- `The practice score rises. The fresh test does not.`

**Narration:**

> The team keeps improving the product against the twenty tickets they already use every day. That score climbs: eight, twelve, sixteen, eighteen. They never train on a separate batch of twenty tickets kept aside from the start. That fresh test stays near nine. The number you optimize becomes a report card for memorizing the practice list. The fresh test is still the honest check.

**Animation:** Draw blue line + point labels, then yellow line + labels, then caption.

**Intuition check:** “Practice” vs “fresh” parallels studying old exam questions vs sitting a new exam.

---

## Beat 5 — Recap

**On screen:**

- Title: `Three ideas`

| Term | One-line meaning |
|------|------------------|
| **Demo** | One example, usually picked to impress you. |
| **Eval** | A frozen checklist, written rules, and a pass count. |
| **Fresh test** | Tickets kept aside so fixes cannot train on them. |

**Close (yellow):**

- `No frozen checklist and no written rules → you do not have an eval. You have a demo.`

**Narration:**

> Three ideas. Demo: one chosen example. Eval: frozen checklist, written rules, pass count. Fresh test: tickets you never use while fixing. Without the checklist frozen first and fail defined in writing, you are still watching demos.

---

## Numbers cheat sheet (do not change without updating both charts)

- Sample rows: **2 pass, 3 fail** on 5
- Full checklist size: **20**
- Product from demo: **8/20**
- Other product: **15/20**
- Practice line: **8 → 12 → 16 → 18**
- Fresh line: **9, 9, 8, 9**

---

## What was wrong in the previous cut (content notes)

1. **“Won the demo” / “Lost the demo”** — Sounds like winners and losers, not *same test, two products*.
2. **“Case”** — Too abstract without “test case” or “customer situation.”
3. **Rules missing on screen** — Fails look arbitrary without *wrong policy / no handoff*.
4. **Held-out first** — Jargon before the idea (*tickets kept aside*).
5. **Pace** — Terms appeared faster than a non-technical viewer could map demo → list → score.

---

## Step 2 checklist (animation — not done in this step)

- [ ] Rename scene beats to match sections above
- [ ] Add rules card in beat 2
- [ ] Relabel bars: `Product from the demo` / `The other product`
- [ ] Relabel held-out beat to `Fresh test` with parenthetical held-out once
- [ ] Lengthen `wait()` times per hold targets
- [ ] Sync `evals/NARRATION.md` line-for-line with this file