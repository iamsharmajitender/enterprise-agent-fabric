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


DOMAIN_TINT = "rgba(59,130,246,0.08)"
DOMAIN_STROKE = "#3b82f6"
DOMAIN_TAG = "rgba(59,130,246,0.45)"
EMPLOYEE_TINT = "rgba(99,102,241,0.14)"
EMPLOYEE_STROKE = "#6366f1"
CUSTOMER_TINT = "rgba(16,185,129,0.14)"
CUSTOMER_STROKE = "#10b981"
PARTNER_TINT = "rgba(245,158,11,0.16)"
PARTNER_STROKE = "#f59e0b"
RISK_TINT = "rgba(239,68,68,0.10)"
RISK_STROKE = "#ef4444"


def ai_cap_colored(x: int, y: int, w: int, h: int, name: str, fill: str, stroke: str) -> str:
    cx = x + w // 2
    return f"""
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>
      <text x="{cx}" y="{y + 24}" fill="{INK}" font-size="11" font-weight="600" font-family="{SANS}" text-anchor="middle">{name}</text>
      <text x="{cx}" y="{y + 40}" fill="{RISK_STROKE}" font-size="7" font-family="{MONO}" text-anchor="middle">own auth · audit · ops</text>"""


def executive_fragmented_today() -> tuple[str, str]:
    slug = "agent-fabric-executive-problem"
    w, h = 1080, 540
    body = f"""
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img"
         aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">Fragmented enterprise AI today</title>
      <desc id="{slug}-desc">Employees, customers, and partners each reach separate AI assistants. Every capability rebuilds authentication, audit, and operations independently.</desc>
      <defs>
        {markers("exec-prob")}
        <marker id="exec-prob-arrow-indigo" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="{EMPLOYEE_STROKE}"/>
        </marker>
        <marker id="exec-prob-arrow-green" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="{CUSTOMER_STROKE}"/>
        </marker>
        <marker id="exec-prob-arrow-amber" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="{PARTNER_STROKE}"/>
        </marker>
      </defs>
      <rect width="100%" height="100%" fill="{PAPER}"/>

      <!-- employee band -->
      <rect x="248" y="36" width="792" height="118" rx="12" fill="{EMPLOYEE_TINT}" stroke="{EMPLOYEE_STROKE}" stroke-width="1.2"/>
      <text x="268" y="58" fill="{EMPLOYEE_STROKE}" font-size="9" font-weight="600" font-family="{MONO}" letter-spacing="0.14em">EMPLOYEE ASSISTANTS</text>

      <!-- customer band -->
      <rect x="248" y="174" width="792" height="118" rx="12" fill="{CUSTOMER_TINT}" stroke="{CUSTOMER_STROKE}" stroke-width="1.2"/>
      <text x="268" y="196" fill="{CUSTOMER_STROKE}" font-size="9" font-weight="600" font-family="{MONO}" letter-spacing="0.14em">CUSTOMER AI</text>

      <!-- partner band -->
      <rect x="248" y="312" width="792" height="118" rx="12" fill="{PARTNER_TINT}" stroke="{PARTNER_STROKE}" stroke-width="1.2"/>
      <text x="268" y="334" fill="{PARTNER_STROKE}" font-size="9" font-weight="600" font-family="{MONO}" letter-spacing="0.14em">PARTNER AI</text>

      <!-- audience pills -->
      <rect x="40" y="68" width="168" height="54" rx="27" fill="{EMPLOYEE_TINT}" stroke="{EMPLOYEE_STROKE}" stroke-width="1.4"/>
      <text x="124" y="100" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">Employee</text>

      <rect x="40" y="206" width="168" height="54" rx="27" fill="{CUSTOMER_TINT}" stroke="{CUSTOMER_STROKE}" stroke-width="1.4"/>
      <text x="124" y="238" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">Customer</text>

      <rect x="40" y="344" width="168" height="54" rx="27" fill="{PARTNER_TINT}" stroke="{PARTNER_STROKE}" stroke-width="1.4"/>
      <text x="124" y="376" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">Partner</text>

      <!-- arrows -->
      <line x1="208" y1="95" x2="248" y2="95" stroke="{EMPLOYEE_STROKE}" stroke-width="1.6" marker-end="url(#exec-prob-arrow-indigo)"/>
      <path d="M 208 233 L 248 210" fill="none" stroke="{CUSTOMER_STROKE}" stroke-width="1.6" marker-end="url(#exec-prob-arrow-green)"/>
      <path d="M 208 371 L 248 390" fill="none" stroke="{PARTNER_STROKE}" stroke-width="1.6" marker-end="url(#exec-prob-arrow-amber)"/>

      <!-- capabilities -->
      {ai_cap_colored(280, 78, 132, 52, "Finance", EMPLOYEE_TINT, EMPLOYEE_STROKE)}
      {ai_cap_colored(432, 78, 132, 52, "HR", EMPLOYEE_TINT, EMPLOYEE_STROKE)}
      {ai_cap_colored(584, 78, 132, 52, "Legal", EMPLOYEE_TINT, EMPLOYEE_STROKE)}
      {ai_cap_colored(736, 78, 132, 52, "Technology", EMPLOYEE_TINT, EMPLOYEE_STROKE)}

      {ai_cap_colored(360, 216, 148, 52, "Customer service", CUSTOMER_TINT, CUSTOMER_STROKE)}
      {ai_cap_colored(536, 216, 148, 52, "Claims", CUSTOMER_TINT, CUSTOMER_STROKE)}

      {ai_cap_colored(360, 354, 148, 52, "Payments", PARTNER_TINT, PARTNER_STROKE)}
      {ai_cap_colored(536, 354, 148, 52, "KYC", PARTNER_TINT, PARTNER_STROKE)}

      <!-- fragmentation chaos lines between stacks -->
      <path d="M 412 130 Q 500 150 588 130" fill="none" stroke="{RISK_STROKE}" stroke-width="1" stroke-dasharray="4 3" opacity="0.45"/>
      <path d="M 564 130 Q 652 155 740 130" fill="none" stroke="{RISK_STROKE}" stroke-width="1" stroke-dasharray="4 3" opacity="0.45"/>
      <text x="880" y="108" fill="{RISK_STROKE}" font-size="8" font-family="{MONO}" letter-spacing="0.08em">NO SHARED MODEL</text>

      <!-- risk banner -->
      <rect x="40" y="448" width="1000" height="56" rx="10" fill="{RISK_TINT}" stroke="{RISK_STROKE}" stroke-width="1.2"/>
      <text x="540" y="472" fill="{RISK_STROKE}" font-size="9" font-weight="600" font-family="{MONO}" text-anchor="middle" letter-spacing="0.12em">THE ORGANISATION CANNOT CONSISTENTLY ANSWER</text>
      <text x="540" y="492" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">Who may use this? · What may it do? · Why was it selected?</text>

      <line x1="40" y1="516" x2="1040" y2="516" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <rect x="40" y="522" width="16" height="12" rx="6" fill="{EMPLOYEE_TINT}" stroke="{EMPLOYEE_STROKE}" stroke-width="1"/>
      <text x="62" y="531" fill="{MUTED}" font-size="8" font-family="{SANS}">Employee</text>
      <rect x="130" y="522" width="16" height="12" rx="6" fill="{CUSTOMER_TINT}" stroke="{CUSTOMER_STROKE}" stroke-width="1"/>
      <text x="152" y="531" fill="{MUTED}" font-size="8" font-family="{SANS}">Customer</text>
      <rect x="220" y="522" width="16" height="12" rx="6" fill="{PARTNER_TINT}" stroke="{PARTNER_STROKE}" stroke-width="1"/>
      <text x="242" y="531" fill="{MUTED}" font-size="8" font-family="{SANS}">Partner</text>
      <rect x="310" y="522" width="16" height="12" rx="2" fill="{RISK_TINT}" stroke="{RISK_STROKE}" stroke-width="1"/>
      <text x="332" y="531" fill="{MUTED}" font-size="8" font-family="{SANS}">Duplicated controls per capability</text>
    </svg>"""
    html = chrome(
        slug,
        "Executive brief · The problem",
        "Many audiences, many assistants, no shared control model.",
        f"0 0 {w} {h}",
        body,
    )
    return slug, html


def control_chip(x: int, y: int, w: int, h: int, label: str, icon: str) -> str:
    cx = x + w // 2
    return f"""
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{WHITE}" stroke="{ACCENT}" stroke-width="1.2"/>
      <text x="{cx}" y="{y + 28}" fill="{ACCENT}" font-size="16" font-family="{SANS}" text-anchor="middle">{icon}</text>
      <text x="{cx}" y="{y + 48}" fill="{INK}" font-size="10" font-weight="600" font-family="{SANS}" text-anchor="middle">{label}</text>"""


def domain_cap(x: int, y: int, w: int, h: int, name: str) -> str:
    cx = x + w // 2
    return f"""
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{DOMAIN_TINT}" stroke="{DOMAIN_STROKE}" stroke-width="1"/>
      <text x="{cx}" y="{y + 30}" fill="{INK}" font-size="11" font-weight="600" font-family="{SANS}" text-anchor="middle">{name}</text>
      <text x="{cx}" y="{y + 46}" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle">domain-owned</text>"""


def executive_proposition() -> tuple[str, str]:
    slug = "agent-fabric-executive-proposition"
    w, h = 1080, 520
    cx = w // 2
    actor_fill = "rgba(100,116,139,0.10)"
    chips = []
    chip_w, chip_h, gap = 148, 58, 16
    labels = [
        ("Security", "◆"),
        ("Governance", "◇"),
        ("Audit", "▣"),
        ("Observability", "◎"),
        ("Evaluation", "✓"),
    ]
    total_w = len(labels) * chip_w + (len(labels) - 1) * gap
    start_x = cx - total_w // 2
    for i, (label, icon) in enumerate(labels):
        chips.append(control_chip(start_x + i * (chip_w + gap), 196, chip_w, chip_h, label, icon))

    domains = []
    dom_arrows = []
    dom_w, dom_h, dom_gap = 148, 58, 18
    dom_names = ["Finance AI", "HR AI", "Legal AI", "Claims AI", "Payments AI"]
    dom_total = len(dom_names) * dom_w + (len(dom_names) - 1) * dom_gap
    dom_start = cx - dom_total // 2
    for i, name in enumerate(dom_names):
        x = dom_start + i * (dom_w + dom_gap)
        domains.append(domain_cap(x, 372, dom_w, dom_h, name))
        dom_arrows.append(
            f'<line x1="{x + dom_w // 2}" y1="300" x2="{x + dom_w // 2}" y2="368" '
            f'stroke="{MUTED}" stroke-width="1.2" marker-end="url(#exec-prop-arrow)"/>'
        )

    body = f"""
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img"
         aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">Enterprise Agent Fabric proposition</title>
      <desc id="{slug}-desc">Users enter through one front door. The Fabric centralises security, governance, audit, observability, and evaluation. Specialised domain AI capabilities remain independently owned below.</desc>
      <defs>
        {markers("exec-prop")}
        <linearGradient id="fabric-grad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="rgba(249,115,22,0.16)"/>
          <stop offset="50%" stop-color="rgba(249,115,22,0.28)"/>
          <stop offset="100%" stop-color="rgba(249,115,22,0.16)"/>
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="{PAPER}"/>

      {box(200, 28, 148, 44, "USR", "Employees", fill=actor_fill, stroke=SOFT, tag_stroke="rgba(148,163,184,0.45)", rx=22, name_size=11)}
      {box(cx - 74, 28, 148, 44, "USR", "Customers", fill=actor_fill, stroke=SOFT, tag_stroke="rgba(148,163,184,0.45)", rx=22, name_size=11)}
      {box(732, 28, 148, 44, "USR", "Applications", fill=actor_fill, stroke=SOFT, tag_stroke="rgba(148,163,184,0.45)", rx=22, name_size=11)}

      <path d="M 274 72 L {cx} 92" fill="none" stroke="{MUTED}" stroke-width="1.4" marker-end="url(#exec-prop-arrow)"/>
      <path d="M {cx} 72 L {cx} 92" fill="none" stroke="{ACCENT}" stroke-width="1.8" marker-end="url(#exec-prop-arrow-accent)"/>
      <path d="M 806 72 L {cx} 92" fill="none" stroke="{MUTED}" stroke-width="1.4" marker-end="url(#exec-prop-arrow)"/>

      <rect x="{cx - 132}" y="92" width="264" height="40" rx="20" fill="{ACCENT}" stroke="{ACCENT}" stroke-width="1"/>
      <text x="{cx}" y="117" fill="{WHITE}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">One governed front door</text>

      <line x1="{cx}" y1="132" x2="{cx}" y2="152" stroke="{ACCENT}" stroke-width="2" marker-end="url(#exec-prop-arrow-accent)"/>

      <rect x="48" y="152" width="984" height="148" rx="14" fill="url(#fabric-grad)" stroke="{ACCENT}" stroke-width="1.6"/>
      <text x="{cx}" y="178" fill="{INK}" font-size="15" font-weight="600" font-family="{SANS}" text-anchor="middle">Enterprise Agent Fabric</text>
      <text x="{cx}" y="194" fill="{MUTED}" font-size="9" font-family="{MONO}" text-anchor="middle" letter-spacing="0.14em">CENTRAL ENTERPRISE CONTROLS — BUILT ONCE, APPLIED EVERYWHERE</text>
      {"".join(chips)}

      <path d="M 64 318 Q 64 340 88 340 L 992 340 Q 1016 340 1016 318" fill="none" stroke="{ACCENT}" stroke-width="1.2" stroke-dasharray="6 4" opacity="0.55"/>
      <text x="72" y="334" fill="{ACCENT}" font-size="8" font-family="{MONO}" letter-spacing="0.1em">ENTERPRISE STANDARD</text>
      <text x="900" y="334" fill="{DOMAIN_STROKE}" font-size="8" font-family="{MONO}" letter-spacing="0.1em">DOMAIN-OWNED</text>

      {"".join(dom_arrows)}

      {"".join(domains)}

      <text x="{cx}" y="468" fill="{INK}" font-size="15" font-family="{SERIF}" font-style="italic" text-anchor="middle">Centralise the controls. Keep the intelligence in the domains.</text>

      <line x1="40" y1="488" x2="1040" y2="488" stroke="rgba(30,41,59,0.10)" stroke-width="0.8"/>
      <rect x="40" y="496" width="24" height="14" rx="7" fill="{ACCENT}"/>
      <text x="72" y="506" fill="{MUTED}" font-size="8" font-family="{SANS}">Enterprise Fabric</text>
      <rect x="180" y="496" width="20" height="14" rx="2" fill="{DOMAIN_TINT}" stroke="{DOMAIN_STROKE}" stroke-width="1"/>
      <text x="208" y="506" fill="{MUTED}" font-size="8" font-family="{SANS}">Specialised capability</text>
    </svg>"""
    html = chrome(
        slug,
        "Executive brief · Proposition",
        "One front door. Central controls. Many domain-owned capabilities.",
        f"0 0 {w} {h}",
        body,
    )
    return slug, html


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


def swim_step(x: int, y: int, w: int, h: int, title: str, sub: str = "",
              fill: str = WHITE, stroke: str = INK, accent: bool = False) -> str:
    cx = x + w // 2
    if accent:
        fill = ACCENT_TINT
        stroke = ACCENT
    sub_y = y + h - 12 if sub else y + h // 2 + 4
    title_y = y + 22 if sub else y + h // 2 + 4
    return f"""
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>
      <text x="{cx}" y="{title_y}" fill="{INK}" font-size="10" font-weight="600" font-family="{SANS}" text-anchor="middle">{title}</text>
      {f'<text x="{cx}" y="{sub_y}" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle">{sub}</text>' if sub else ''}"""


def executive_swimlane_automated() -> tuple[str, str]:
    slug = "agent-fabric-executive-swimlane-jobs"
    w, h = 1080, 440
    lane_x, lane_w = 148, 900
    steps = [220, 400, 580, 760, 940]
    body = f"""
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img"
         aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">Automated AI request swimlane</title>
      <desc id="{slug}-desc">A claims system or batch job triggers AI through the Enterprise Fabric: verify and entitle, route and pin, execute under policy, record evidence alongside, return outcome.</desc>
      <defs>{markers("exec-sw")}</defs>
      <rect width="100%" height="100%" fill="{PAPER}"/>

      <!-- lane bands -->
      <rect x="{lane_x}" y="44" width="{lane_w}" height="76" fill="rgba(100,116,139,0.06)" rx="4"/>
      <rect x="{lane_x}" y="132" width="{lane_w}" height="92" fill="{ACCENT_TINT}" rx="4"/>
      <rect x="{lane_x}" y="236" width="{lane_w}" height="76" fill="{DOMAIN_TINT}" rx="4"/>
      <rect x="{lane_x}" y="328" width="{lane_w}" height="76" fill="rgba(30,41,59,0.04)" rx="4"/>

      <!-- lane dividers -->
      <line x1="{lane_x}" y1="44" x2="{lane_x + lane_w}" y2="44" stroke="rgba(30,41,59,0.12)" stroke-width="1"/>
      <line x1="{lane_x}" y1="128" x2="{lane_x + lane_w}" y2="128" stroke="rgba(30,41,59,0.08)" stroke-width="1"/>
      <line x1="{lane_x}" y1="224" x2="{lane_x + lane_w}" y2="224" stroke="rgba(30,41,59,0.08)" stroke-width="1"/>
      <line x1="{lane_x}" y1="328" x2="{lane_x + lane_w}" y2="328" stroke="rgba(30,41,59,0.08)" stroke-width="1"/>
      <line x1="{lane_x}" y1="404" x2="{lane_x + lane_w}" y2="404" stroke="rgba(30,41,59,0.12)" stroke-width="1"/>
      <line x1="{lane_x}" y1="44" x2="{lane_x}" y2="404" stroke="rgba(30,41,59,0.12)" stroke-width="1"/>

      <!-- lane labels -->
      <text x="24" y="88" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.12em">APPLICATION</text>
      <text x="24" y="98" fill="{INK}" font-size="9" font-weight="600" font-family="{SANS}">Claims system</text>
      <text x="24" y="110" fill="{MUTED}" font-size="8" font-family="{SANS}">or batch job</text>

      <text x="24" y="176" fill="{ACCENT}" font-size="8" font-family="{MONO}" letter-spacing="0.12em">ENTERPRISE</text>
      <text x="24" y="188" fill="{INK}" font-size="9" font-weight="600" font-family="{SANS}">Agent Fabric</text>

      <text x="24" y="272" fill="{DOMAIN_STROKE}" font-size="8" font-family="{MONO}" letter-spacing="0.12em">DOMAIN</text>
      <text x="24" y="284" fill="{INK}" font-size="9" font-weight="600" font-family="{SANS}">Claims AI</text>

      <text x="24" y="360" fill="{MUTED}" font-size="8" font-family="{MONO}" letter-spacing="0.12em">ALONGSIDE</text>
      <text x="24" y="372" fill="{INK}" font-size="9" font-weight="600" font-family="{SANS}">Audit &amp; ops</text>

      <!-- steps -->
      {swim_step(steps[0] - 56, 60, 112, 44, "Trigger job", "route case")}
      {swim_step(steps[1] - 64, 148, 128, 52, "Verify", "identity &amp; entitle", accent=True)}
      {swim_step(steps[2] - 64, 148, 128, 52, "Route &amp; pin", "select capability", accent=True)}
      {swim_step(steps[3] - 64, 248, 128, 52, "Execute", "under policy", fill=DOMAIN_TINT, stroke=DOMAIN_STROKE)}
      {swim_step(steps[4] - 56, 60, 112, 44, "Outcome", "202 / result")}
      {swim_step(steps[1] - 48, 344, 96, 40, "Record", fill="rgba(30,41,59,0.02)", stroke=MUTED)}
      {swim_step(steps[2] - 48, 344, 96, 40, "Record", fill="rgba(30,41,59,0.02)", stroke=MUTED)}
      {swim_step(steps[3] - 48, 344, 96, 40, "Record", fill="rgba(30,41,59,0.02)", stroke=MUTED)}
      {swim_step(steps[4] - 48, 344, 96, 40, "Record", fill="rgba(30,41,59,0.02)", stroke=MUTED)}

      <!-- optional control callout -->
      <rect x="{steps[3] - 20}" y="196" width="88" height="22" rx="4" fill="{WHITE}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 3"/>
      <text x="{steps[3] + 24}" y="211" fill="{MUTED}" font-size="8" font-family="{SANS}" text-anchor="middle">approval if required</text>

      <!-- flow arrows -->
      <line x1="{steps[0] + 56}" y1="82" x2="{steps[1] - 64}" y2="148" stroke="{MUTED}" stroke-width="1.3" marker-end="url(#exec-sw-arrow)"/>
      <line x1="{steps[1] + 64}" y1="174" x2="{steps[2] - 64}" y2="174" stroke="{ACCENT}" stroke-width="1.5" marker-end="url(#exec-sw-arrow-accent)"/>
      <line x1="{steps[2] + 64}" y1="174" x2="{steps[3] - 64}" y2="248" stroke="{MUTED}" stroke-width="1.3" marker-end="url(#exec-sw-arrow)"/>
      <line x1="{steps[3] + 64}" y1="274" x2="{steps[4] - 56}" y2="82" stroke="{MUTED}" stroke-width="1.3" marker-end="url(#exec-sw-arrow)"/>

      <!-- alongside track -->
      <line x1="{steps[1]}" y1="364" x2="{steps[4]}" y2="364" stroke="{MUTED}" stroke-width="1" stroke-dasharray="5 4" opacity="0.7"/>
      <text x="{lane_x + lane_w - 8}" y="358" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="end">runs alongside — does not block unless approval required</text>

      <!-- column headers -->
      <text x="{steps[0]}" y="28" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.1em">START</text>
      <text x="{steps[1]}" y="28" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.1em">VERIFY</text>
      <text x="{steps[2]}" y="28" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.1em">ROUTE</text>
      <text x="{steps[3]}" y="28" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.1em">EXECUTE</text>
      <text x="{steps[4]}" y="28" fill="{MUTED}" font-size="8" font-family="{MONO}" text-anchor="middle" letter-spacing="0.1em">COMPLETE</text>

      <text x="540" y="428" fill="{INK}" font-size="13" font-family="{SERIF}" font-style="italic" text-anchor="middle">Same governed path for chat and automated jobs — verify → route → execute → evidence → outcome</text>
    </svg>"""
    html = chrome(
        slug,
        "Swimlane · Automated work",
        "Claims system triggers AI: verify, route, execute, evidence alongside, outcome returned.",
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
    for fn in (executive_proposition, executive_swimlane_automated, executive_fragmented_today, target_state, executive_story, fragmented_problem, lifecycle_proof):
        slug, html = fn()
        (OUT / f"{slug}.html").write_text(html)
        (OUT / f"{slug}.svg").write_text(extract_svg(html))
        print("wrote", slug)


if __name__ == "__main__":
    main()
