#!/usr/bin/env python3
"""Render B2B/tech blog storytelling diagrams for ARTICLE.md.

Technique stack (see IMAGE_PROMPTS.md):
- Semrush: diagrams for process / comparison beats
- Patrick Wings: one sentence message, one job per graphic
- Ilir Ivezaj: lock style; overlay text programmatically (no AI typography)
- CapCut tech blogs: brief → fixed palette → export 16:9
- Floniks / BrandGene: conceptual metaphors, not stock laptop photos
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (241, 243, 246)
NAVY = (26, 43, 74)
AMBER = (232, 140, 36)
SOFT = (210, 216, 224)
WHITE = (255, 255, 255)
MUTED = (110, 122, 140)

OUT = Path(__file__).resolve().parent / "article"
ART = Path("/opt/cursor/artifacts/article")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def save(img: Image.Image, stem: str) -> None:
    """Write cache-busted filenames (*-diagrams.jpg) to repo + artifacts."""
    name = f"{stem}-diagrams.jpg"
    OUT.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    for folder in (OUT, ART):
        path = folder / name
        img.save(path, "JPEG", quality=92, optimize=True)
        print(path)


def rounded(draw: ImageDraw.ImageDraw, box, fill, radius=28) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def caption(draw: ImageDraw.ImageDraw, title: str, sub: str) -> None:
    draw.text((96, 72), title, font=font(54, True), fill=NAVY)
    draw.text((96, 148), sub, font=font(30), fill=MUTED)


def panel(draw: ImageDraw.ImageDraw, box, title: str) -> None:
    rounded(draw, box, WHITE, 32)
    draw.rounded_rectangle(box, radius=32, outline=SOFT, width=3)
    draw.text((box[0] + 36, box[1] + 28), title, font=font(28, True), fill=AMBER)


def sticky(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 140) -> None:
    draw.rectangle((x, y, x + size, y + size), fill=AMBER)
    draw.polygon(
        [(x + size - 36, y + size), (x + size, y + size - 36), (x + size, y + size)],
        fill=(196, 110, 20),
    )


def shield(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0) -> None:
    w, h = int(220 * scale), int(260 * scale)
    x0, y0 = cx - w // 2, cy - h // 2
    pts = [
        (cx, y0),
        (x0 + w, y0 + int(50 * scale)),
        (x0 + w, y0 + int(150 * scale)),
        (cx, y0 + h),
        (x0, y0 + int(150 * scale)),
        (x0, y0 + int(50 * scale)),
    ]
    draw.polygon(pts, fill=NAVY)
    for i, checked in enumerate((True, True, True, False)):
        yy = y0 + int(70 * scale) + i * int(36 * scale)
        xx = x0 + int(55 * scale)
        draw.rectangle((xx, yy, xx + int(110 * scale), yy + int(18 * scale)), fill=SOFT)
        if checked:
            draw.line(
                (xx + 8, yy + 9, xx + 18, yy + 16, xx + 34, yy + 4),
                fill=AMBER,
                width=5,
            )


def render_01() -> None:
    img, d = new_canvas()
    caption(d, "Same model. Different blast radius.", "Personal vibe check vs enterprise eval")
    left = (96, 260, 900, 980)
    right = (1020, 260, 1824, 980)
    panel(d, left, "PERSONAL")
    panel(d, right, "ENTERPRISE")
    sticky(d, 430, 480, 180)
    d.text((330, 720), "3 prompts. Looks fine.", font=font(34), fill=MUTED)
    d.text((360, 780), "Ship it.", font=font(40, True), fill=NAVY)
    shield(d, 1420, 560, 1.35)
    d.text((1180, 820), "Frozen cases. Written fail rules.", font=font(34), fill=MUTED)
    d.text((1280, 880), "Score the whole job.", font=font(40, True), fill=NAVY)
    save(img, "01-hero")


def render_02() -> None:
    img, d = new_canvas()
    caption(d, "Vibe checks are a feature…", "…when the only stakeholder is dinner.")
    rounded(d, (420, 300, 1500, 940), WHITE, 40)
    d.rounded_rectangle((420, 300, 1500, 940), radius=40, outline=SOFT, width=3)
    # laptop body + screen + base
    rounded(d, (680, 400, 1240, 720), NAVY, 20)
    rounded(d, (710, 430, 1210, 680), (40, 60, 96), 10)
    d.rectangle((640, 720, 1280, 760), fill=(20, 34, 58))
    sticky(d, 1160, 360, 130)
    d.text((760, 500), "looks fine", font=font(44, True), fill=AMBER)
    d.text((760, 570), "to me", font=font(44, True), fill=WHITE)
    d.text((560, 820), "Read three outputs. Nod. Ship.", font=font(36), fill=MUTED)
    save(img, "02-personal-vibe")


def render_03() -> None:
    img, d = new_canvas()
    caption(d, "Enterprise surface area breaks vibes.", "When tickets outrun the hero on-call.")
    # left: alone with vibes
    panel(d, (96, 280, 780, 980), "WITHOUT EVALS")
    for i, (x, y) in enumerate([(180, 420), (320, 400), (460, 430), (220, 520), (380, 540), (540, 500)]):
        rounded(d, (x, y, x + 140, y + 70), NAVY if i % 2 else (45, 70, 110), 12)
    d.text((180, 680), "Tickets pile up.", font=font(34), fill=MUTED)
    d.text((180, 760), "Someone vibes harder.", font=font(36, True), fill=NAVY)
    d.text((180, 840), "Regressions hide.", font=font(34), fill=MUTED)

    # right: with evals
    panel(d, (900, 280, 1824, 980), "WITH EVALS")
    for i, (x, y) in enumerate([(1020, 400), (1180, 390), (1340, 410), (1500, 395)]):
        rounded(d, (x, y, x + 120, y + 60), (45, 70, 110), 10)
    d.polygon([(1100, 500), (1640, 500), (1480, 680), (1260, 680)], fill=NAVY)
    shield(d, 1370, 820, 0.95)
    d.text((1080, 900), "Frozen rules catch costly misses.", font=font(32, True), fill=NAVY)
    save(img, "03-enterprise-blast")


def render_04() -> None:
    img, d = new_canvas()
    caption(d, "One invented policy sentence is enough.", "Vibes do not survive a screenshot.")
    # bot bubble
    rounded(d, (180, 340, 820, 700), NAVY, 36)
    d.polygon([(420, 700), (520, 700), (470, 760)], fill=NAVY)
    d.text((250, 420), "Chatbot says:", font=font(28), fill=SOFT)
    d.text((250, 490), "“Sure — refund\nwithin 90 days.”", font=font(42, True), fill=WHITE)
    # vs
    d.ellipse((900, 500, 1020, 620), fill=AMBER)
    d.text((930, 530), "≠", font=font(56, True), fill=WHITE)
    # official doc
    rounded(d, (1120, 340, 1760, 820), WHITE, 28)
    d.rounded_rectangle((1120, 340, 1760, 820), radius=28, outline=NAVY, width=4)
    d.text((1180, 390), "Real policy", font=font(28, True), fill=AMBER)
    for i in range(5):
        y = 470 + i * 50
        d.rectangle((1180, y, 1680, y + 22), fill=SOFT)
    d.text((1180, 740), "No retroactive refund.", font=font(34, True), fill=NAVY)
    save(img, "04-chatbot-policy")


def render_05() -> None:
    img, d = new_canvas()
    caption(d, "The ladder everyone climbs", "Vibe → scenarios → production traces")
    stages = [
        (180, "1. Vibe check", "Loop until it\nfeels good", AMBER),
        (720, "2. Write 10–20", "Handwrite cases.\nScore them.", NAVY),
        (1260, "3. Prod traces", "Feed live failures\ninto the same tests.", NAVY),
    ]
    for x, title, body, color in stages:
        rounded(d, (x, 360, x + 480, 820), WHITE, 32)
        d.rounded_rectangle((x, 360, x + 480, 820), radius=32, outline=SOFT, width=3)
        d.ellipse((x + 190, 420, x + 290, 520), fill=color)
        d.text((x + 40, 560), title, font=font(36, True), fill=NAVY)
        d.multiline_text((x + 40, 630), body, font=font(30), fill=MUTED, spacing=8)
    # arrows
    for x in (640, 1180):
        d.polygon([(x, 560), (x + 50, 590), (x, 620)], fill=AMBER)
    save(img, "05-ladder")


def render_06() -> None:
    img, d = new_canvas()
    caption(d, "The score you rehearse is not the score that measures.", "Practice list vs fresh tickets")
    # left gauge climbing
    rounded(d, (160, 300, 900, 960), WHITE, 36)
    d.rounded_rectangle((160, 300, 900, 960), radius=36, outline=SOFT, width=3)
    d.text((250, 340), "PRACTICE LIST", font=font(32, True), fill=AMBER)
    pts = [(240, 820), (340, 700), (440, 640), (540, 520), (640, 420), (780, 360)]
    d.line(pts, fill=AMBER, width=12)
    for x, y in pts:
        d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=NAVY)
    d.text((280, 880), "Dashboard parties", font=font(34, True), fill=NAVY)

    # right gauge flat
    rounded(d, (1020, 300, 1760, 960), WHITE, 36)
    d.rounded_rectangle((1020, 300, 1760, 960), radius=36, outline=SOFT, width=3)
    d.text((1160, 340), "FRESH TICKETS", font=font(32, True), fill=NAVY)
    pts2 = [(1100, 700), (1220, 690), (1340, 710), (1460, 680), (1580, 700), (1680, 690)]
    d.line(pts2, fill=NAVY, width=12)
    for x, y in pts2:
        d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=AMBER)
    d.text((1180, 880), "Customers unchanged", font=font(34, True), fill=NAVY)
    save(img, "06-fresh-vs-practice")


def main() -> None:
    render_01()
    render_02()
    render_03()
    render_04()
    render_05()
    render_06()


if __name__ == "__main__":
    main()
