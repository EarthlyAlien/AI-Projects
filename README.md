# Why evals

A short silent animation about why a good demo is not a measurement. The pictures are made with [ManimGL](https://github.com/3b1b/manim), the engine Grant Sanderson uses for 3Blue1Brown. The scene is original. It does not use code from [3b1b/videos](https://github.com/3b1b/videos).

The voiceover is in [evals/NARRATION.md](evals/NARRATION.md). The frames follow it: one lit case, the cloud of cases around it, two scores on the same twenty, then the practiced score rising while a held-out set stays put.

## Render

Python 3.10 or newer, [FFmpeg](https://ffmpeg.org/), Pango, and a LaTeX install (`texlive-latex-extra` and `dvisvgm` are enough for the one formula).

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
manimgl evals/why_evals.py WhyEvals -w
```

On a machine with no display, run that last command under `xvfb-run -a`. The file lands at `evals/media/WhyEvals.mp4`.

`-l` renders a small preview. The committed file is 1920×1080 at 30 fps, from [custom_config.yml](custom_config.yml).
