# Why evals

A short silent animation about why a good demo is not a measurement. The pictures are made with [ManimGL](https://github.com/3b1b/manim), the engine Grant Sanderson uses for 3Blue1Brown. The scene is original. It does not use code from [3b1b/videos](https://github.com/3b1b/videos).

The **content script** (story, on-screen copy, chart numbers, terminology) is in [evals/VIDEO_CONTENT.md](evals/VIDEO_CONTENT.md). The voiceover is in [evals/NARRATION.md](evals/NARRATION.md), aligned to that script.

The current animation is step 2 and may still use older labels until it is rebuilt against `VIDEO_CONTENT.md`.

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
