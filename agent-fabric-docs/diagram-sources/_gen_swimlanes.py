#!/usr/bin/env python3
"""Generate Pattern 0–3 swimlane HTML (source of truth) and sibling SVGs."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "static" / "diagrams"

PAPER = "#f8fafc"
INK = "#1e293b"
MUTED = "#64748b"
ACCENT = "#3b82f6"
ACCENT_TINT = "rgba(59,130,246,0.08)"
LINK = "#2563eb"
RULE = "rgba(30,41,59,0.12)"
RULE_SOFT = "rgba(30,41,59,0.08)"
WHITE = "#ffffff"
SANS = "'Geist', system-ui, sans-serif"
SERIF = "'Instrument Serif', serif"
MONO = "'Geist Mono', ui-monospace, monospace"
FONTS = "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap"
# Standalone .svg is XML. Bare & in the font URL is a parse error, so <img> shows nothing.
FONTS_XML = FONTS.replace("&", "&amp;")


def chrome(slug: str, title: str, desc: str, vb: str, body: str, h: int) -> str:
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
    :root {{
      --color-paper: {PAPER};
      --color-ink: {INK};
      --color-muted: {MUTED};
      --color-accent: {ACCENT};
      --font-sans: {SANS};
      --font-serif: {SERIF};
      --font-mono: {MONO};
    }}
    body {{
      font-family: var(--font-sans);
      background: var(--color-paper);
      color: var(--color-ink);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 3rem 2rem;
    }}
    .frame {{ max-width: 1200px; width: 100%; }}
    .eyebrow {{
      font-family: var(--font-mono);
      font-size: 0.66rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 0.5rem;
    }}
    h1 {{
      font-family: var(--font-serif);
      font-size: clamp(1.5rem, 2.4vw + 0.75rem, 2rem);
      font-weight: 400;
      letter-spacing: -0.02em;
      line-height: 1.15;
      color: var(--color-ink);
      margin-bottom: 1.5rem;
    }}
    svg {{ width: 100%; min-width: 900px; display: block; }}
  </style>
</head>
<body>
  <div class="frame">
    <p class="eyebrow">Swimlane · Pattern hook-up</p>
    <h1>{title}</h1>
    <svg viewBox="0 0 {tw} {th}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">{title}</title>
      <desc id="{slug}-desc">{desc}</desc>
      <defs>
        <style>@import url('{FONTS_XML}');</style>
        <marker id="{slug}-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
        <marker id="{slug}-arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
        <marker id="{slug}-arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{LINK}"/></marker>
      </defs>
      <rect width="100%" height="100%" fill="{PAPER}"/>
{body}
    </svg>
  </div>
</body>
</html>
"""


def lanes(slug: str, labels: list[str], top: int, lane_h: int, width: int) -> str:
    n = len(labels)
    y0 = top
    y1 = top + n * lane_h
    x_div = 168
    lines = [
        f'      <line x1="40" y1="{y0}" x2="{width - 40}" y2="{y0}" stroke="{RULE}" stroke-width="1"/>',
        f'      <line x1="40" y1="{y1}" x2="{width - 40}" y2="{y1}" stroke="{RULE}" stroke-width="1"/>',
        f'      <line x1="{x_div}" y1="{y0}" x2="{x_div}" y2="{y1}" stroke="{RULE}" stroke-width="1"/>',
    ]
    for i in range(1, n):
        y = y0 + i * lane_h
        lines.append(
            f'      <line x1="40" y1="{y}" x2="{width - 40}" y2="{y}" stroke="{RULE_SOFT}" stroke-width="1"/>'
        )
    for i, lab in enumerate(labels):
        ty = y0 + i * lane_h + lane_h // 2 + 4
        lines.append(
            f'      <text x="52" y="{ty}" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.14em">{lab}</text>'
        )
    return "\n".join(lines)


def box(x: int, y: int, w: int, h: int, name: str, sub: str, *, focal: bool = False) -> str:
    fill = ACCENT_TINT if focal else WHITE
    stroke = ACCENT if focal else INK
    cx = x + w // 2
    return f"""      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/>
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>
      <text x="{cx}" y="{y + 22}" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">{name}</text>
      <text x="{cx}" y="{y + 36}" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle">{sub}</text>"""


def alabel(x: int, y: int, w: int, text: str, *, accent: bool = False, link: bool = False) -> str:
    fill = ACCENT if accent else (LINK if link else MUTED)
    return f"""      <rect x="{x}" y="{y}" width="{w}" height="12" rx="2" fill="{PAPER}"/>
      <text x="{x + w // 2}" y="{y + 10}" fill="{fill}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.08em">{text}</text>"""


def legend(y: int, width: int, items_extra: str) -> str:
    return f"""      <line x1="40" y1="{y}" x2="{width - 40}" y2="{y}" stroke="{RULE_SOFT}" stroke-width="0.8"/>
      <text x="40" y="{y + 16}" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.14em">LEGEND</text>
      <rect x="40" y="{y + 28}" width="14" height="10" rx="2" fill="{WHITE}" stroke="{INK}" stroke-width="1"/>
      <text x="60" y="{y + 36}" fill="{MUTED}" font-size="8" font-family="{SANS}">Step</text>
      <rect x="132" y="{y + 28}" width="14" height="10" rx="2" fill="{ACCENT_TINT}" stroke="{ACCENT}" stroke-width="1"/>
      <text x="152" y="{y + 36}" fill="{MUTED}" font-size="8" font-family="{SANS}">LLM call</text>
      <line x1="268" y1="{y + 33}" x2="296" y2="{y + 33}" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#p0-arrow)"/>
      <text x="304" y="{y + 36}" fill="{MUTED}" font-size="8" font-family="{SANS}">Handoff</text>
      <line x1="404" y1="{y + 33}" x2="432" y2="{y + 33}" stroke="{LINK}" stroke-width="1.2" marker-end="url(#p0-arrow-link)"/>
      <text x="440" y="{y + 36}" fill="{MUTED}" font-size="8" font-family="{SANS}">Catalogue GET</text>
{items_extra}"""


def p0() -> tuple[str, str]:
    slug = "p0"
    w, h = 1080, 500
    body = "\n".join(
        [
            lanes(slug, ["FRONT DOOR", "RUNTIME", "DATA PLANE", "LLM"], 64, 80, w),
            # arrows first
            f'      <path d="M 312,104 H 328 Q 336,104 336,112 V 176 Q 336,184 344,184 H 360" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(312, 132, 48, "PIN"),
            f'      <path d="M 496,184 H 512 Q 520,184 520,192 V 256 Q 520,264 528,264 H 544" fill="none" stroke="{LINK}" stroke-width="1.2" marker-end="url(#{slug}-arrow-link)"/>',
            alabel(496, 212, 48, "GET", link=True),
            f'      <path d="M 680,264 H 696 Q 704,264 704,272 V 336 Q 704,344 712,344 H 728" fill="none" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>',
            alabel(680, 292, 64, "COMPLETE", accent=True),
            f'      <path d="M 864,344 H 972 Q 980,344 980,336 V 128" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(984, 220, 56, "RESULT"),
            box(176, 80, 136, 48, "Start run", "POST /v1/runs"),
            box(360, 160, 136, 48, "Pin", "route + goal"),
            box(544, 240, 136, 48, "Prompt pack", "host only"),
            box(728, 320, 136, 48, "One complete", "synthesis", focal=True),
            box(912, 80, 136, 48, "Return", "result + notes"),
            legend(
                416,
                w,
                f'      <line x1="560" y1="449" x2="588" y2="449" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>\n      <text x="596" y="452" fill="{MUTED}" font-size="8" font-family="{SANS}">The one LLM call</text>',
            ).replace("p0-arrow", f"{slug}-arrow"),
        ]
    )
    # fix legend markers to p0
    html = chrome(
        slug,
        "Pattern 0 — pin, one synthesis, return",
        "Front Door starts the run. Runtime pins the route. Data Plane returns the prompt pack. Runtime makes one synthesis LLM call and returns.",
        f"0 0 {w} {h}",
        body,
        h,
    )
    return slug, html


def p1() -> tuple[str, str]:
    slug = "p1"
    w, h = 1080, 600
    body = "\n".join(
        [
            lanes(slug, ["FRONT DOOR", "RUNTIME", "CATALOGUE", "LLM", "DOMAIN HTTP"], 64, 80, w),
            f'      <path d="M 312,104 H 328 Q 336,104 336,112 V 176 Q 336,184 344,184 H 360" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(312, 132, 48, "PIN"),
            f'      <path d="M 496,184 H 512 Q 520,184 520,192 V 256 Q 520,264 528,264 H 544" fill="none" stroke="{LINK}" stroke-width="1.2" marker-end="url(#{slug}-arrow-link)"/>',
            alabel(496, 212, 56, "HYDRATE", link=True),
            f'      <path d="M 680,264 H 696 Q 704,264 704,272 V 336 Q 704,344 712,344 H 728" fill="none" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>',
            alabel(680, 292, 56, "DECIDE", accent=True),
            f'      <line x1="796" y1="368" x2="796" y2="400" fill="none" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>',
            alabel(804, 376, 40, "CALL", accent=True),
            f'      <path d="M 728,424 H 700 Q 692,424 692,416 V 360 Q 692,352 700,352 H 728" fill="none" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#{slug}-arrow)"/>',
            alabel(640, 380, 48, "NOTES"),
            f'      <path d="M 864,344 H 880 Q 888,344 888,336 V 192 Q 888,184 896,184 H 912" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(852, 252, 40, "DONE"),
            box(176, 80, 136, 48, "Start run", "POST /v1/runs"),
            box(360, 160, 136, 48, "Pin", "no workflow"),
            box(544, 240, 136, 48, "Manifest", "invoke.url frozen"),
            box(728, 320, 136, 48, "CALL or DONE", "host every turn", focal=True),
            box(728, 400, 136, 48, "Tool HTTP", "dict(goal)"),
            box(912, 160, 136, 48, "Return", "result"),
            legend(
                512,
                w,
                f'      <line x1="560" y1="545" x2="588" y2="545" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>\n      <text x="596" y="548" fill="{MUTED}" font-size="8" font-family="{SANS}">Decide</text>\n      <line x1="680" y1="545" x2="708" y2="545" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#{slug}-arrow)"/>\n      <text x="716" y="548" fill="{MUTED}" font-size="8" font-family="{SANS}">Observe, loop</text>',
            ).replace("p0-arrow", f"{slug}-arrow"),
        ]
    )
    html = chrome(
        slug,
        "Pattern 1 — pin, hydrate, CALL / DONE loop",
        "Front Door starts the run. Runtime pins with no workflow. Catalogue hydrates the manifest. The LLM decides CALL or DONE. CALL hits domain HTTP; notes return to the next decide until DONE.",
        f"0 0 {w} {h}",
        body,
        h,
    )
    return slug, html


def p2() -> tuple[str, str]:
    slug = "p2"
    w, h = 1080, 600
    body = "\n".join(
        [
            lanes(slug, ["FRONT DOOR", "RUNTIME", "CATALOGUE", "LLM", "DOMAIN HTTP"], 64, 80, w),
            f'      <path d="M 312,104 H 328 Q 336,104 336,112 V 176 Q 336,184 344,184 H 360" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(312, 132, 48, "PIN"),
            f'      <path d="M 496,184 H 512 Q 520,184 520,192 V 256 Q 520,264 528,264 H 544" fill="none" stroke="{LINK}" stroke-width="1.2" marker-end="url(#{slug}-arrow-link)"/>',
            alabel(496, 212, 56, "HYDRATE", link=True),
            f'      <path d="M 680,264 H 696 Q 704,264 704,272 V 200 Q 704,192 712,192 H 728" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(708, 220, 48, "GRAPH"),
            f'      <line x1="760" y1="208" x2="760" y2="320" fill="none" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>',
            alabel(768, 252, 72, "COMPLETE", accent=True),
            f'      <line x1="832" y1="208" x2="832" y2="400" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(840, 288, 40, "HTTP"),
            f'      <path d="M 864,184 H 912" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            box(176, 80, 136, 48, "Start run", "POST /v1/runs"),
            box(360, 160, 136, 48, "Pin", "workflow_id"),
            box(544, 240, 136, 48, "Workflow + pack", "stamp llm_role"),
            box(728, 160, 136, 48, "Linear graph", "_run_stage"),
            box(728, 320, 136, 48, "complete", "classify / synthesis", focal=True),
            box(728, 400, 136, 48, "Tool HTTP", "none / query"),
            box(912, 160, 136, 48, "Return", "respond if needed"),
            legend(
                512,
                w,
                f'      <line x1="560" y1="545" x2="588" y2="545" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>\n      <text x="596" y="548" fill="{MUTED}" font-size="8" font-family="{SANS}">LLM stage</text>\n      <line x1="700" y1="545" x2="728" y2="545" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>\n      <text x="736" y="548" fill="{MUTED}" font-size="8" font-family="{SANS}">HTTP stage</text>',
            ).replace("p0-arrow", f"{slug}-arrow"),
        ]
    )
    html = chrome(
        slug,
        "Pattern 2 — pin, stamp roles, linear stages",
        "Front Door starts the run. Runtime pins a workflow. Catalogue stamps llm_role onto stages. Runtime walks a linear graph. Each stage either completes with the LLM or calls domain HTTP.",
        f"0 0 {w} {h}",
        body,
        h,
    )
    return slug, html


def p3() -> tuple[str, str]:
    slug = "p3"
    w, h = 1080, 600
    body = "\n".join(
        [
            lanes(slug, ["FRONT DOOR", "RUNTIME", "CATALOGUE", "LLM", "DOMAIN HTTP"], 64, 80, w),
            f'      <path d="M 312,104 H 328 Q 336,104 336,112 V 176 Q 336,184 344,184 H 360" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(312, 132, 48, "PIN"),
            f'      <path d="M 496,184 H 512 Q 520,184 520,192 V 256 Q 520,264 528,264 H 544" fill="none" stroke="{LINK}" stroke-width="1.2" marker-end="url(#{slug}-arrow-link)"/>',
            alabel(496, 212, 56, "HYDRATE", link=True),
            f'      <path d="M 680,264 H 696 Q 704,264 704,272 V 200 Q 704,192 712,192 H 728" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            alabel(700, 220, 56, "OUTER"),
            f'      <path d="M 760,208 V 312 Q 760,320 768,320 H 728" fill="none" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>',
            alabel(768, 252, 56, "INNER", accent=True),
            f'      <line x1="796" y1="368" x2="796" y2="400" fill="none" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>',
            alabel(804, 376, 40, "CALL", accent=True),
            f'      <path d="M 728,424 H 700 Q 692,424 692,416 V 360 Q 692,352 700,352 H 728" fill="none" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#{slug}-arrow)"/>',
            alabel(640, 380, 48, "NOTES"),
            f'      <path d="M 864,184 H 912" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#{slug}-arrow)"/>',
            box(176, 80, 136, 48, "Start run", "POST /v1/runs"),
            box(360, 160, 136, 48, "Pin", "workflow + manifest"),
            box(544, 240, 136, 48, "Allowlists", "per-stage ids"),
            box(728, 160, 136, 48, "Outer stages", "designer order"),
            box(728, 320, 136, 48, "Inner CALL/DONE", "allowlist only", focal=True),
            box(728, 400, 136, 48, "Tool HTTP", "max_tool_calls"),
            box(912, 160, 136, 48, "Return", "then next stage"),
            legend(
                500,
                w,
                f'      <line x1="560" y1="533" x2="588" y2="533" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#{slug}-arrow-accent)"/>\n      <text x="596" y="536" fill="{MUTED}" font-size="8" font-family="{SANS}">Intended inner loop</text>',
            ).replace("p0-arrow", f"{slug}-arrow"),
            f'      <text x="176" y="580" fill="{MUTED}" font-size="13" font-family="{SERIF}" font-style="italic">This Runtime still walks Pattern 2 linear — inner loop is catalogue-only.</text>',
        ]
    )
    html = chrome(
        slug,
        "Pattern 3 — outer stages, inner allowlist loop",
        "Front Door starts the run. Runtime pins workflow and manifest. Catalogue stamps allowlists. The designer owns outer stage order. Inside an allowlisted stage the LLM CALLs tools until DONE. This Runtime still runs the linear Pattern 2 graph.",
        f"0 0 {w} {h}",
        body,
        h,
    )
    return slug, html


def extract_svg(html: str) -> str:
    start = html.index("<svg ")
    end = html.index("</svg>") + len("</svg>")
    svg = html[start:end]
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + svg



def main() -> None:
    builders = [
        ("pattern-0-swimlane", p0),
        ("pattern-1-swimlane", p1),
        ("pattern-2-swimlane", p2),
        ("pattern-3-swimlane", p3),
    ]
    for name, fn in builders:
        result = fn()
        html = result[1]
        (OUT / f"{name}.html").write_text(html)
        (OUT / f"{name}.svg").write_text(extract_svg(html))
        print("wrote", name)


if __name__ == "__main__":
    main()
