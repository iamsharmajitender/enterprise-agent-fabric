#!/usr/bin/env python3
"""Generate executive pitch diagrams (HTML source + sibling SVG)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent

PAPER = "#f8fafc"
INK = "#1e293b"
MUTED = "#64748b"
SOFT = "#94a3b8"
ACCENT = "#f97316"
ACCENT_TINT = "rgba(249,115,22,0.10)"
WHITE = "#ffffff"
SANS = "'Geist', system-ui, sans-serif"
SERIF = "'Instrument Serif', serif"
MONO = "'Geist Mono', ui-monospace, monospace"
FONTS = (
    "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1"
    "&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap"
)
FONTS_XML = FONTS.replace("&", "&amp;")


def chrome(slug: str, eyebrow: str, title: str, vb: str, body: str) -> str:
    tw, th = vb.split()[2:]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="{FONTS}" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: {SANS};
      background: {PAPER};
      color: {INK};
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 3rem 2rem;
    }}
    .frame {{ max-width: 1280px; width: 100%; }}
    .eyebrow {{
      font-family: {MONO};
      font-size: 0.66rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: {MUTED};
      margin-bottom: 0.5rem;
    }}
    h1 {{
      font-family: {SERIF};
      font-size: clamp(1.5rem, 2.4vw + 0.75rem, 2rem);
      font-weight: 400;
      letter-spacing: -0.02em;
      line-height: 1.15;
      color: {INK};
      margin-bottom: 1.5rem;
    }}
    svg {{ width: 100%; min-width: {tw}px; display: block; }}
  </style>
</head>
<body>
  <div class="frame">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{title}</h1>
    {body}
  </div>
</body>
</html>
"""


def markers(prefix: str) -> str:
    return f"""
      <marker id="{prefix}-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/>
      </marker>
      <marker id="{prefix}-arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/>
      </marker>"""


def box(x: int, y: int, w: int, h: int, tag: str, name: str, sub: str = "",
        fill: str = WHITE, stroke: str = INK, tag_stroke: str = "rgba(30,41,59,0.40)",
        rx: int = 6, name_size: int = 12) -> str:
    cx = x + w // 2
    cy = y + h // 2
    sub_y = cy + 16 if sub else cy + 4
    name_y = cy - 4 if sub else cy + 4
    return f"""
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{PAPER}"/>
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>
      <rect x="{x + 8}" y="{y + 8}" width="28" height="12" rx="2" fill="transparent" stroke="{tag_stroke}" stroke-width="0.8"/>
      <text x="{x + 22}" y="{y + 17}" fill="{stroke}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.08em">{tag}</text>
      <text x="{cx}" y="{name_y}" fill="{INK}" font-size="{name_size}" font-weight="600" font-family="{SANS}" text-anchor="middle">{name}</text>
      {f'<text x="{cx}" y="{sub_y}" fill="{MUTED}" font-size="9" font-family="{MONO}" text-anchor="middle">{sub}</text>' if sub else ''}"""


def target_state() -> tuple[str, str]:
    slug = "agent-fabric-pitch-target-state"
    w, h = 960, 560
    cx = w // 2
    body = f"""
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img"
         aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">Enterprise Agent Fabric target state</title>
      <desc id="{slug}-desc">Users and applications enter through the Enterprise AI Front Door. A decision layer selects the capability and verifies entitlement. Specialised domain capabilities execute under shared enterprise controls.</desc>
      <defs>{markers("pitch-target")}</defs>
      <rect width="100%" height="100%" fill="{PAPER}"/>

      <line x1="{cx}" y1="88" x2="{cx}" y2="108" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-target-arrow)"/>
      <line x1="{cx}" y1="168" x2="{cx}" y2="188" stroke="{ACCENT}" stroke-width="1.6" marker-end="url(#pitch-target-arrow-accent)"/>
      <path d="M 400 268 L 400 308 L 200 308 L 200 328" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-target-arrow)"/>
      <path d="M {cx} 268 L {cx} 328" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-target-arrow)"/>
      <path d="M 560 268 L 560 308 L 760 308 L 760 328" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-target-arrow)"/>
      <path d="M 200 368 L 200 408" fill="none" stroke="{MUTED}" stroke-width="1.2"/>
      <path d="M {cx} 368 L {cx} 408" fill="none" stroke="{MUTED}" stroke-width="1.2"/>
      <path d="M 760 368 L 760 408" fill="none" stroke="{MUTED}" stroke-width="1.2"/>
      <path d="M 200 408 L 760 408" fill="none" stroke="{MUTED}" stroke-width="1.2"/>
      <line x1="{cx}" y1="408" x2="{cx}" y2="428" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-target-arrow)"/>

      {box(cx - 120, 32, 240, 56, "IN", "Users / applications", fill="rgba(100,116,139,0.10)", stroke=SOFT, tag_stroke="rgba(148,163,184,0.45)", rx=20)}
      {box(cx - 140, 108, 280, 60, "AFD", "Enterprise AI Front Door", fill=ACCENT_TINT, stroke=ACCENT, tag_stroke="rgba(249,115,22,0.45)")}
      {box(cx - 160, 188, 320, 80, "CTL", "Decision / control", "Entitlement · routing · policy", fill=WHITE, stroke=INK)}
      {box(120, 328, 160, 40, "DOM", "Customer AI", fill=WHITE, stroke=INK, name_size=11)}
      {box(cx - 80, 328, 160, 40, "DOM", "Payments AI", fill=WHITE, stroke=INK, name_size=11)}
      {box(680, 328, 160, 40, "DOM", "Legal AI", fill=WHITE, stroke=INK, name_size=11)}
      {box(cx - 180, 428, 360, 72, "GOV", "Enterprise controls", "Data · tools · approval · audit · risk", fill="rgba(30,41,59,0.04)", stroke=MUTED)}

      <text x="{cx}" y="520" fill="{INK}" font-size="14" font-family="{SERIF}" font-style="italic" text-anchor="middle">Not one giant agent — one operating layer around specialised capabilities.</text>

      <line x1="40" y1="536" x2="920" y2="536" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <text x="40" y="552" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.14em">LEGEND</text>
      <rect x="40" y="536" width="20" height="14" rx="2" fill="{ACCENT_TINT}" stroke="{ACCENT}" stroke-width="1"/>
      <text x="68" y="546" fill="{MUTED}" font-size="8" font-family="{SANS}">Front door</text>
      <rect x="140" y="536" width="20" height="14" rx="2" fill="{WHITE}" stroke="{INK}" stroke-width="1"/>
      <text x="168" y="546" fill="{MUTED}" font-size="8" font-family="{SANS}">Domain capability</text>
    </svg>"""
    html = chrome(
        slug,
        "Architecture · Target state",
        "One front door, governed decision, specialised capabilities, shared controls.",
        f"0 0 {w} {h}",
        body,
    )
    return slug, html


def executive_story() -> tuple[str, str]:
    slug = "agent-fabric-v1-story"
    w, h = 1280, 320
    steps = [
        ("01", "AI is fragmenting", "more capabilities", "rgba(100,116,139,0.10)", SOFT, True),
        ("02", "Enterprise risk", "duplicated controls", WHITE, INK, False),
        ("03", "One operating model", "Agent Fabric", ACCENT_TINT, ACCENT, False),
        ("04", "Domain autonomy", "teams own outcomes", WHITE, INK, False),
        ("05", "Scale with control", "portfolio growth", WHITE, INK, True),
    ]
    boxes = []
    xs = [40, 280, 520, 760, 1000]
    widths = [200, 200, 200, 200, 200]
    for i, (tag, name, sub, fill, stroke, rounded) in enumerate(steps):
        rx = 20 if rounded else 6
        accent = i == 2
        boxes.append(
            box(xs[i], 56, widths[i], 96, tag, name, sub, fill=fill, stroke=stroke,
                tag_stroke=f"rgba({('249,115,22' if accent else '30,41,59')},0.45)",
                rx=rx, name_size=14 if len(name) < 18 else 12)
        )
    arrows = ""
    for i in range(4):
        x1 = xs[i] + widths[i]
        x2 = xs[i + 1]
        accent = i == 1
        sw = "1.8" if accent else "1.2"
        col = ACCENT if accent else MUTED
        mk = "-accent" if accent else ""
        arrows += f'<line x1="{x1}" y1="104" x2="{x2}" y2="104" stroke="{col}" stroke-width="{sw}" marker-end="url(#eaf-v1-story-arrow{mk})"/>\n'

    body = f"""
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img"
         aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">The Enterprise Agent Fabric executive story</title>
      <desc id="{slug}-desc">Five beats from fragmented AI and enterprise risk, through one operating model and domain autonomy, to scale with control.</desc>
      <defs>{markers("eaf-v1-story")}</defs>
      <rect width="100%" height="100%" fill="{PAPER}"/>
      {arrows}
      {"".join(boxes)}
      <text x="640" y="188" fill="{INK}" font-size="16" font-family="{SERIF}" font-style="italic" text-anchor="middle">One front door. Many specialised capabilities. One control model.</text>
      <line x1="40" y1="216" x2="1240" y2="216" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <text x="40" y="240" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.18em">LEGEND</text>
      <rect x="40" y="256" width="24" height="14" rx="7" fill="rgba(100,116,139,0.10)" stroke="{SOFT}" stroke-width="1"/>
      <text x="72" y="266" fill="{MUTED}" font-size="8" font-family="{SANS}">Challenge</text>
      <rect x="236" y="256" width="20" height="14" rx="2" fill="{ACCENT_TINT}" stroke="{ACCENT}" stroke-width="1"/>
      <text x="264" y="266" fill="{MUTED}" font-size="8" font-family="{SANS}">Fabric focal</text>
      <rect x="360" y="256" width="20" height="14" rx="2" fill="{WHITE}" stroke="{INK}" stroke-width="1"/>
      <text x="388" y="266" fill="{MUTED}" font-size="8" font-family="{SANS}">Outcome</text>
    </svg>"""
    html = chrome(
        slug,
        "Process · Executive story",
        "From fragmented AI to scale with control.",
        f"0 0 {w} {h}",
        body,
    )
    return slug, html


def fragmented_problem() -> tuple[str, str]:
    slug = "agent-fabric-pitch-problem"
    w, h = 960, 520
    actor_fill = "rgba(100,116,139,0.10)"
    actor_stroke = SOFT
    actor_tag = "rgba(148,163,184,0.45)"
    body = f"""
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img"
         aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">Fragmented enterprise AI today</title>
      <desc id="{slug}-desc">Employees, customers, and partners each reach separate assistants and endpoints. Each domain rebuilds authentication, routing, and controls independently.</desc>
      <defs>{markers("pitch-problem")}</defs>
      <rect width="100%" height="100%" fill="{PAPER}"/>

      <rect x="280" y="32" width="640" height="112" rx="8" fill="rgba(30,41,59,0.02)" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <text x="600" y="52" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.12em">EMPLOYEE ASSISTANTS</text>
      <rect x="280" y="160" width="640" height="112" rx="8" fill="rgba(30,41,59,0.02)" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <text x="600" y="180" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.12em">CUSTOMER AI</text>
      <rect x="280" y="288" width="640" height="112" rx="8" fill="rgba(30,41,59,0.02)" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <text x="600" y="308" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.12em">PARTNER AI</text>

      <line x1="200" y1="88" x2="280" y2="88" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-problem-arrow)"/>
      <line x1="200" y1="216" x2="280" y2="216" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-problem-arrow)"/>
      <line x1="200" y1="344" x2="280" y2="344" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-problem-arrow)"/>

      {box(40, 60, 160, 56, "EMP", "Employee", fill=actor_fill, stroke=actor_stroke, tag_stroke=actor_tag, rx=20)}
      {box(40, 188, 160, 56, "CUS", "Customer", fill=actor_fill, stroke=actor_stroke, tag_stroke=actor_tag, rx=20)}
      {box(40, 316, 160, 56, "PRT", "Partner", fill=actor_fill, stroke=actor_stroke, tag_stroke=actor_tag, rx=20)}

      {box(300, 68, 128, 56, "AI", "Finance", name_size=11)}
      {box(448, 68, 128, 56, "AI", "HR", name_size=11)}
      {box(596, 68, 128, 56, "AI", "Legal", name_size=11)}
      {box(744, 68, 128, 56, "AI", "Technology", name_size=11)}

      {box(372, 196, 160, 56, "AI", "Customer svc", name_size=11)}
      {box(588, 196, 160, 56, "AI", "Claims", name_size=11)}

      {box(372, 324, 160, 56, "AI", "Payments", name_size=11)}
      {box(588, 324, 160, 56, "AI", "KYC", name_size=11)}

      <text x="480" y="440" fill="{INK}" font-size="14" font-family="{SERIF}" font-style="italic" text-anchor="middle">Who may use this? What may it do? Why was it selected?</text>
      <line x1="40" y1="464" x2="920" y2="464" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <text x="40" y="484" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.14em">LEGEND</text>
      <rect x="40" y="492" width="24" height="14" rx="7" fill="{actor_fill}" stroke="{actor_stroke}" stroke-width="1"/>
      <text x="72" y="502" fill="{MUTED}" font-size="8" font-family="{SANS}">Audience</text>
      <rect x="160" y="492" width="20" height="14" rx="2" fill="{WHITE}" stroke="{INK}" stroke-width="1"/>
      <text x="188" y="502" fill="{MUTED}" font-size="8" font-family="{SANS}">Isolated capability</text>
    </svg>"""
    html = chrome(
        slug,
        "Architecture · The problem",
        "Many audiences. Many assistants. No single answer.",
        f"0 0 {w} {h}",
        body,
    )
    return slug, html


def lifecycle_proof() -> tuple[str, str]:
    slug = "agent-fabric-pitch-lifecycle"
    w, h = 1280, 240
    labels = [
        ("IN", "Message"),
        ("DEC", "Classify"),
        ("DEC", "Entitle"),
        ("PIN", "Pin"),
        ("HYD", "Hydrate"),
        ("RUN", "Execute"),
        ("OUT", "Response"),
    ]
    xs = [40, 200, 360, 520, 680, 840, 1000]
    boxes = []
    for i, (tag, name) in enumerate(labels):
        accent = i == 3
        fill = ACCENT_TINT if accent else WHITE
        stroke = ACCENT if accent else INK
        boxes.append(box(xs[i], 72, 128, 56, tag, name, fill=fill, stroke=stroke,
                           tag_stroke="rgba(249,115,22,0.45)" if accent else "rgba(30,41,59,0.40)",
                           name_size=11))
    arrows = ""
    for i in range(6):
        x1 = xs[i] + 128
        x2 = xs[i + 1]
        arrows += f'<line x1="{x1}" y1="100" x2="{x2}" y2="100" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#pitch-life-arrow)"/>\n'

    body = f"""
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img"
         aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">V1 reference lifecycle</title>
      <desc id="{slug}-desc">The working V1 path from inbound message through classify, entitlement, pin, hydrate, execute, and response.</desc>
      <defs>{markers("pitch-life")}</defs>
      <rect width="100%" height="100%" fill="{PAPER}"/>
      {arrows}
      {"".join(boxes)}
      <text x="640" y="168" fill="{INK}" font-size="14" font-family="{SERIF}" font-style="italic" text-anchor="middle">Same contract for chat and jobs ingress.</text>
      <line x1="40" y1="192" x2="1240" y2="192" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <text x="40" y="208" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.14em">LEGEND</text>
      <rect x="40" y="212" width="20" height="14" rx="2" fill="{ACCENT_TINT}" stroke="{ACCENT}" stroke-width="1"/>
      <text x="68" y="222" fill="{MUTED}" font-size="8" font-family="{SANS}">Durable pin</text>
    </svg>"""
    html = chrome(
        slug,
        "Process · V1 proof point",
        "Message in → governed response out.",
        f"0 0 {w} {h}",
        body,
    )
    return slug, html


def extract_svg(html: str) -> str:
    start = html.index("<svg ")
    end = html.index("</svg>") + len("</svg>")
    svg = html[start:end]
    # Standalone SVG needs escaped ampersands in @import if present
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + svg.replace(FONTS, FONTS_XML)


def main() -> None:
    for fn in (target_state, executive_story, fragmented_problem, lifecycle_proof):
        slug, html = fn()
        (OUT / f"{slug}.html").write_text(html)
        (OUT / f"{slug}.svg").write_text(extract_svg(html))
        print("wrote", slug)


if __name__ == "__main__":
    main()
