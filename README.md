# Why AI evals in enterprise?

Personal projects live on **vibe checks**. Enterprise products need **evals** once real users, policy, and Legal enter the chat.

The deliverable is an **article + image series**, not a film-first piece.

## Read this

- **Article (repo):** [evals/ARTICLE.md](evals/ARTICLE.md)
- **Substack paste file:** [evals/SUBSTACK.md](evals/SUBSTACK.md) — copy from PASTE START, upload images where marked
- **Images:** [evals/article/](evals/article/) — six 16:9 AI editorial panels
- **Image recipe:** [evals/IMAGE_PROMPTS.md](evals/IMAGE_PROMPTS.md)

| Image | Beat |
|-------|------|
| `00-cover-vibe-evals.jpg` | Substack cover: Yes / No |
| `01-hero-aligned.jpg` | Personal sticky note vs enterprise checklist |
| `02-personal-vibe-aligned.jpg` | Read three. Nod. Ship. |
| `03-enterprise-blast-aligned.jpg` | Without evals vs with evals |
| `04-chatbot-policy-aligned.jpg` | Invented refund ≠ real policy |
| `05-ladder-aligned.jpg` | Vibe → 10–20 → prod traces |
| `06-fresh-vs-practice-aligned.jpg` | Practice climbs; fresh stays flat |

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
