# Why AI evals in enterprise?

Personal projects live on **vibe checks**. Enterprise products need **evals** once real users, policy, and Legal enter the chat.

The deliverable is an **article + image series**, not a film-first piece.

## Read this

- **Article:** [evals/ARTICLE.md](evals/ARTICLE.md) — witty take with real examples (Hamel Husain on vibe checks → evals, Ankur Goyal’s three stages, Air Canada / Moffatt chatbot refund case)
- **Images:** [evals/article/](evals/article/) — six 16:9 panels for the piece

| Image | Beat |
|-------|------|
| `01-hero.jpg` | Why enterprise evals when personal projects vibe-check? |
| `02-personal-vibe.jpg` | Side-project blast radius |
| `03-enterprise-blast.jpg` | Same joke, company stakes |
| `04-chatbot-policy.jpg` | Invented policy vs a screenshot |
| `05-ladder.jpg` | Vibe → scenarios → production traces |
| `06-fresh-vs-practice.jpg` | Rehearsed score vs fresh tickets |

## Optional Manim short

An older silent animation still lives under `evals/` (`why_evals.py`, `VIDEO_CONTENT.md`, `media/WhyEvals.mp4`) if you want motion later. The article is the source of truth for this theme.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
manimgl evals/why_evals.py WhyEvals -w
```

On a machine with no display, run that under `xvfb-run -a`.

The Manim scene uses stock [ManimGL](https://github.com/3b1b/manim) only. It does not use code from [3b1b/videos](https://github.com/3b1b/videos).
