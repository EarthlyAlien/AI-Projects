# Why AI evals?

A short silent animation that asks **Why AI evals?** and answers it with one support AI: a demo, a frozen checklist, a real score, and a practice-versus-fresh check. Pictures are made with [ManimGL](https://github.com/3b1b/manim) (3Blue1Brown’s engine). The scene is original and does not use code from [3b1b/videos](https://github.com/3b1b/videos).

The **content script** (story, on-screen copy, chart numbers, terminology) is in [evals/VIDEO_CONTENT.md](evals/VIDEO_CONTENT.md). The voiceover is in [evals/NARRATION.md](evals/NARRATION.md), aligned to that script.

`evals/why_evals.py` follows that script: one support AI, title `Why AI evals?`, then the demo, the frozen checklist, the 1/1 versus 8/20 score, and the practice-versus-fresh chart.

## Render

Python 3.10 or newer, [FFmpeg](https://ffmpeg.org/), and Pango. This scene is drawn with text, so rendering it does not need LaTeX.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
manimgl evals/why_evals.py WhyEvals -w
```

On a machine with no display, run that last command under `xvfb-run -a`. The file lands at `evals/media/WhyEvals.mp4`.

`-l` renders a small preview. The committed file is 1920×1080 at 30 fps, from [custom_config.yml](custom_config.yml).
