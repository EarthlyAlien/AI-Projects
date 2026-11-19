# Why AI evals in enterprise?

Personal projects live on **vibe checks**. Enterprise products need **evals** once real users, policy, and Legal enter the chat.

The deliverable is an **article + image series**, not a film-first piece.

## Read this

- **Article:** [evals/ARTICLE.md](evals/ARTICLE.md) — witty take with real examples (Hamel Husain on vibe checks → evals, Ankur Goyal’s three stages, Air Canada / Moffatt chatbot refund case)
- **Images:** [evals/article/](evals/article/) — six 16:9 panels for the piece

Cinematic stills (one story moment each, captions in the article, shared warm-lamp / cold-tower grade):

| Image | Beat |
|-------|------|
| `01-hero.jpg` | Kitchen desk vs corporate tower |
| `02-personal-vibe.jpg` | Late-night vibe check smile |
| `03-enterprise-blast.jpg` | Ticket storm vs empty chair |
| `04-chatbot-policy.jpg` | Traveler trusts a chatbot |
| `05-ladder.jpg` | Stairs: thumbs-up → notebook → rack |
| `06-fresh-vs-practice.jpg` | Treadmill practice vs rainy road |

Prompt craft notes: [`evals/IMAGE_PROMPTS.md`](evals/IMAGE_PROMPTS.md).

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
