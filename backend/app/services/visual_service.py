
import os
import uuid
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from app.config import settings

OUT_DIR = os.path.join(settings.VIDEO_DIR, "visuals")
os.makedirs(OUT_DIR, exist_ok=True)


def _out_path(ext="png") -> str:
    return os.path.join(OUT_DIR, f"{uuid.uuid4().hex}.{ext}")


def _blank_canvas(title: str, subtitle: str = "") -> Image.Image:
    img = Image.new("RGB", (1000, 600), color="#F7FAFC")
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.load_default(size=34)
        font_small = ImageFont.load_default(size=20)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()
    draw.rectangle([0, 0, 1000, 90], fill="#3B82F6")
    draw.text((30, 25), title, fill="white", font=font_big)
    if subtitle:
        draw.text((30, 110), subtitle, fill="#1E3A8A", font=font_small)
    return img


def render_graph(concept: str, title: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 5))
    x = list(range(0, 11))
    y = [v * v * 0.5 for v in x]
    ax.plot(x, y, color="#3B82F6", linewidth=3)
    ax.set_title(title or concept, fontsize=14)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(alpha=0.3)
    fig.patch.set_facecolor("#F7FAFC")
    path = _out_path()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def render_equation(concept: str, title: str) -> str:
    img = _blank_canvas(title or "Equation", concept)
    path = _out_path()
    img.save(path)
    return path


def render_force_diagram(concept: str, title: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.add_patch(plt.Rectangle((4, 4), 2, 2, color="#3B82F6"))
    ax.annotate("", xy=(8, 5), xytext=(6, 5),
                arrowprops=dict(arrowstyle="->", color="#EF4444", lw=3))
    ax.annotate("", xy=(4, 5), xytext=(2, 5),
                arrowprops=dict(arrowstyle="->", color="#10B981", lw=3))
    ax.text(6.2, 5.3, "Force", color="#EF4444")
    ax.text(2.2, 5.3, "Reaction", color="#10B981")
    ax.set_title(title or concept)
    ax.axis("off")
    fig.patch.set_facecolor("#F7FAFC")
    path = _out_path()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def render_labeled_diagram(concept: str, title: str) -> str:
    img = _blank_canvas(title or "Diagram", f"Labeled structure: {concept}")
    draw = ImageDraw.Draw(img)
    draw.ellipse([300, 200, 700, 450], outline="#3B82F6", width=4)
    draw.line([500, 200, 500, 130], fill="#374151", width=2)
    draw.text((460, 100), concept, fill="#374151")
    path = _out_path()
    img.save(path)
    return path


def render_timeline(concept: str, title: str) -> str:
    fig, ax = plt.subplots(figsize=(9, 3))
    events = ["Start", "Event A", "Event B", "Event C", "Now"]
    xs = list(range(len(events)))
    ax.plot(xs, [0] * len(xs), color="#3B82F6", linewidth=3, zorder=1)
    ax.scatter(xs, [0] * len(xs), color="#1E3A8A", zorder=2, s=80)
    for x, label in zip(xs, events):
        ax.text(x, 0.05, label, ha="center", fontsize=9)
    ax.set_title(title or concept)
    ax.set_ylim(-0.5, 0.5)
    ax.axis("off")
    fig.patch.set_facecolor("#F7FAFC")
    path = _out_path()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def render_map(concept: str, title: str) -> str:
    img = _blank_canvas(title or "Map", concept)
    path = _out_path()
    img.save(path)
    return path


def render_code_flow(concept: str, title: str) -> str:
    img = _blank_canvas(title or "Execution Flow", concept)
    draw = ImageDraw.Draw(img)
    steps = ["Input", "Process", "Decision", "Output"]
    x = 60
    for s in steps:
        draw.rectangle([x, 250, x + 180, 320], outline="#3B82F6", width=3)
        draw.text((x + 20, 275), s, fill="#1E3A8A")
        x += 220
    path = _out_path()
    img.save(path)
    return path


def render_architecture(concept: str, title: str) -> str:
    return render_code_flow(concept, title)


def render_flowchart(concept: str, title: str) -> str:
    return render_code_flow(concept, title)


def render_plain(concept: str, title: str) -> str:
    img = _blank_canvas(title or concept, concept)
    path = _out_path()
    img.save(path)
    return path


RENDERERS = {
    "graph": render_graph,
    "equation": render_equation,
    "force_diagram": render_force_diagram,
    "labeled_diagram": render_labeled_diagram,
    "timeline": render_timeline,
    "map": render_map,
    "code_flow": render_code_flow,
    "architecture_diagram": render_architecture,
    "flowchart": render_flowchart,
    "plain_illustration": render_plain,
}


def render_visual(visual_spec: dict) -> str:
    vtype = visual_spec.get("visual_type", "plain_illustration")
    concept = visual_spec.get("concept", "")
    title = visual_spec.get("title", concept)
    renderer = RENDERERS.get(vtype, render_plain)
    return renderer(concept, title)
