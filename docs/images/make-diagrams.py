#!/usr/bin/env python3
"""Draws the diagrams in docs/SERVER_SETUP.md, each in a light and a dark version.

Usage: python3 docs/images/make-diagrams.py   (writes the SVGs next to this file)

The figures are code rather than drawings so a change (a renamed variable, a new
container) is one edit here, and the light and dark versions can never drift apart.
Brand logos are paths from Simple Icons 16.37.0; brands not in that set get neutral icons.
"""
import sys, os
from xml.sax.saxutils import escape

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

# Simple Icons 16.37.0 paths (24x24 viewBox)
ICON = {
 "docker": "M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 00.186-.186V6.29a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 00.184-.186V6.29a.185.185 0 00-.185-.185H8.1a.185.185 0 00-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 00.185-.186V6.29a.185.185 0 00-.185-.185H5.136a.186.186 0 00-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 00.185-.185V9.006a.185.185 0 00-.184-.186h-2.12a.186.186 0 00-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.430-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 00-.75.748 11.376 11.376 0 00.692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 003.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z",
 "n8n": "M4.8 16.8c.45 0 .6-.15.6-.6V15c0-1.8.6-2.4 2.4-2.4H9c1.8 0 2.4.6 2.4 2.4v1.2c0 .45.15.6.6.6s.6-.15.6-.6V15c0-1.8.6-2.4 2.4-2.4h1.2c1.8 0 2.4.6 2.4 2.4v1.2c0 .45.15.6.6.6s.6-.15.6-.6V15c0-1.8.6-2.4 2.4-2.4h1.2c.45 0 .6-.15.6-.6s-.15-.6-.6-.6h-1.2c-1.8 0-2.4-.6-2.4-2.4V7.8c0-.45-.15-.6-.6-.6s-.6.15-.6.6V9c0 1.8-.6 2.4-2.4 2.4H15c-1.8 0-2.4-.6-2.4-2.4V7.8c0-.45-.15-.6-.6-.6s-.6.15-.6.6V9c0 1.8-.6 2.4-2.4 2.4H7.8c-1.8 0-2.4-.6-2.4-2.4V7.8c0-.45-.15-.6-.6-.6s-.6.15-.6.6V9c0 1.8-.6 2.4-2.4 2.4H.6c-.45 0-.6.15-.6.6s.15.6.6.6h1.2c1.8 0 2.4.6 2.4 2.4v1.2c0 .45.15.6.6.6",
 "ubuntu": "M17.61.455a3.41 3.41 0 0 0-3.41 3.41 3.41 3.41 0 0 0 3.41 3.41 3.41 3.41 0 0 0 3.41-3.41 3.41 3.41 0 0 0-3.41-3.41zM12.92.8C8.923.777 5.137 2.941 3.148 6.451a4.5 4.5 0 0 1 .26-.007 4.920 4.920 0 0 1 2.585.737A8.316 8.316 0 0 1 12.688 3.6 4.944 4.944 0 0 1 13.723.834 11.008 11.008 0 0 0 12.92.8zm9.226 4.994a4.915 4.915 0 0 1-1.918 2.246 8.360 8.360 0 0 1-.273 8.303 4.890 4.890 0 0 1 1.632 2.540 11.156 11.156 0 0 0 .559-13.089zM3.41 7.932A3.41 3.41 0 0 0 0 11.342a3.41 3.41 0 0 0 3.41 3.409 3.41 3.41 0 0 0 3.41-3.41 3.41 3.41 0 0 0-3.41-3.41zm2.027 7.866a4.908 4.908 0 0 1-2.915.358 11.100 11.100 0 0 0 7.991 6.698 11.234 11.234 0 0 0 2.422.249 4.879 4.879 0 0 1-.999-2.850 8.484 8.484 0 0 1-.836-.136 8.304 8.304 0 0 1-5.663-4.320zm11.405.928a3.41 3.41 0 0 0-3.41 3.41 3.41 3.41 0 0 0 3.41 3.41 3.41 3.41 0 0 0 3.41-3.41 3.41 3.41 0 0 0-3.41-3.41z",
 "tailscale": "M24 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0zm-9 9a3 3 0 1 1-6 0 3 3 0 0 1 6 0zm0-9a3 3 0 1 1-6 0 3 3 0 0 1 6 0zm6-6a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0-.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM3 24a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0-.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zm18 .5a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0-.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM6 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0zm9-9a3 3 0 1 1-6 0 3 3 0 0 1 6 0zm-3 2.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM6 3a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM3 5.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
 "cloudflare": "M16.5088 16.8447c.1475-.5068.0908-.9707-.1553-1.3154-.2246-.3164-.6045-.499-1.0615-.5205l-8.6592-.1123a.1559.1559 0 0 1-.1333-.0713c-.0283-.042-.0351-.0986-.021-.1553.0278-.084.1123-.1484.2036-.1562l8.7359-.1123c1.0351-.0489 2.1601-.8868 2.5537-1.9136l.499-1.3013c.0215-.0561.0293-.1128.0147-.168-.5625-2.5463-2.835-4.4453-5.5499-4.4453-2.5039 0-4.6284 1.6177-5.3876 3.8614-.4927-.3658-1.1187-.5625-1.794-.499-1.2026.119-2.1665 1.083-2.2861 2.2856-.0283.31-.0069.6128.0635.894C1.5683 13.171 0 14.7754 0 16.752c0 .1748.0142.3515.0352.5273.0141.083.0844.1475.1689.1475h15.9814c.0909 0 .1758-.0645.2032-.1553l.12-.4268zm2.7568-5.5634c-.0771 0-.1611 0-.2383.0112-.0566 0-.1054.0415-.127.0976l-.3378 1.1744c-.1475.5068-.0918.9707.1543 1.3164.2256.3164.6055.498 1.0625.5195l1.8437.1133c.0557 0 .1055.0263.1329.0703.0283.043.0351.1074.0214.1562-.0283.084-.1132.1485-.204.1553l-1.921.1123c-1.041.0488-2.1582.8867-2.5527 1.914l-.1406.3585c-.0283.0713.0215.1416.0986.1416h6.5977c.0771 0 .1474-.0489.169-.126.1122-.4082.1757-.837.1757-1.2803 0-2.6025-2.125-4.727-4.7344-4.727",
 "shopify": "M15.337 23.979l7.216-1.561s-2.604-17.613-2.625-17.73c-.018-.116-.114-.192-.211-.192s-1.929-.136-1.929-.136-1.275-1.274-1.439-1.411c-.045-.037-.075-.057-.121-.074l-.914 21.104h.023zM11.71 11.305s-.81-.424-1.774-.424c-1.447 0-1.504.906-1.504 1.141 0 1.232 3.24 1.715 3.24 4.629 0 2.295-1.44 3.76-3.406 3.760-2.354 0-3.540-1.465-3.540-1.465l.646-2.086s1.245 1.066 2.280 1.066c.675 0 .975-.545.975-.932 0-1.619-2.654-1.694-2.654-4.359-.034-2.237 1.571-4.416 4.827-4.416 1.257 0 1.875.361 1.875.361l-.945 2.715-.02.01zM11.17.83c.136 0 .271.038.405.135-.984.465-2.064 1.639-2.508 3.992-.656.213-1.293.405-1.889.578C7.697 3.75 8.951.84 11.17.84V.83zm1.235 2.949v.135c-.754.232-1.583.484-2.394.736.466-1.777 1.333-2.645 2.085-2.971.193.501.309 1.176.309 2.1zm.539-2.234c.694.074 1.141.867 1.429 1.755-.349.114-.735.231-1.158.366v-.252c0-.752-.096-1.371-.271-1.871v.002zm2.992 1.289c-.02 0-.06.021-.078.021s-.289.075-.714.21c-.423-1.233-1.176-2.37-2.508-2.37h-.115C12.135.209 11.669 0 11.265 0 8.159 0 6.675 3.877 6.21 5.846c-1.194.365-2.063.636-2.16.674-.675.213-.694.232-.772.87-.075.462-1.83 14.063-1.83 14.063L15.009 24l.927-21.166z",
}

# Neutral stroke icons (24x24), drawn here; brands without an allowed logo get these
STROKE = {
 "laptop": "M4 5h16v10H4z M2 19h20 M2 19l2-4 M22 19l-2-4",
 "key": "M15 3a6 6 0 1 1-5.6 8.2L3 17.6V21h3.4v-2.4h2.4v-2.4h2.4l.6-.6A6 6 0 0 1 15 3z M17 7.5a.5.5 0 1 0 0 .01",
 "chat": "M4 4h16v12H9l-5 4z M8 9h8 M8 12h5",
 "vm": "M3 4h18v14H3z M3 8h18 M6 6h.01 M8.5 6h.01 M8 21h8 M12 18v3",
 "shield": "M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z",
 "clock": "M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18z M12 7v5l3 2",
 "file": "M6 2h8l5 5v15H6z M14 2v5h5 M9 13h7 M9 17h5",
 "db": "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6 M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
 "terminal": "M3 4h18v16H3z M7 9l3 3-3 3 M12 15h5",
 "script": "M5 3h11l3 3v15H5z M8 9l2 2-2 2 M12 13h4",
}

THEMES = {
 "light": dict(bg="#ffffff", text="#1f2328", muted="#59636e", card="#f6f8fa", stroke="#d1d9e0",
               box="#ffffff", box2="#f6f8fa", web="#bc4c00", admin="#0969da", out="#1a7f37", bad="#cf222e",
               badge="#1f2328", badgetext="#ffffff", n8n="#EA4B71", ts="#242424", wall="#fff1e5"),
 "dark":  dict(bg="#0d1117", text="#e6edf3", muted="#9198a1", card="#151b23", stroke="#3d444d",
               box="#0d1117", box2="#151b23", web="#f0883e", admin="#4493f8", out="#3fb950", bad="#f85149",
               badge="#e6edf3", badgetext="#0d1117", n8n="#FF91AC", ts="#e6edf3", wall="#2d1b10"),
}
BRAND = {"docker": "#2496ED", "ubuntu": "#E95420", "cloudflare": "#F38020", "shopify": "#7AB55C"}
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"


class SVG:
    def __init__(s, w, h, t, title, desc):
        s.w, s.h, s.t = w, h, t
        s.o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t d" font-family="{FONT}">',
               f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>',
               '<defs>' + ''.join(
                   f'<marker id="a-{k}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{t[k]}"/></marker>'
                   for k in ("web", "admin", "out", "bad")) + '</defs>',
               f'<rect width="{w}" height="{h}" rx="16" fill="{t["bg"]}"/>']

    def add(s, x): s.o.append(x)

    def text(s, x, y, txt, size=15, color=None, weight=400, anchor="start", mono=False, italic=False):
        c = color or s.t["text"]
        ff = f' font-family="{MONO}"' if mono else ''
        st = ' font-style="italic"' if italic else ''
        s.add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" font-weight="{weight}" text-anchor="{anchor}"{ff}{st}>{escape(txt)}</text>')

    def rect(s, x, y, w, h, fill=None, stroke=None, rx=12, dash=None, sw=1.5):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill or s.t["card"]}" stroke="{stroke or s.t["stroke"]}" stroke-width="{sw}"{d}/>')

    def icon(s, name, x, y, size=24, color=None):
        k = size / 24
        if name in ICON:
            c = color or BRAND.get(name) or (s.t["n8n"] if name == "n8n" else s.t["ts"] if name == "tailscale" else s.t["text"])
            s.add(f'<g transform="translate({x} {y}) scale({k:.4f})"><path d="{ICON[name]}" fill="{c}"/></g>')
        else:
            c = color or s.t["text"]
            s.add(f'<g transform="translate({x} {y}) scale({k:.4f})" fill="none" stroke="{c}" stroke-width="{1.8 / k:.2f}" stroke-linecap="round" stroke-linejoin="round"><path d="{STROKE[name]}"/></g>')

    def badge(s, x, y, n):
        s.add(f'<circle cx="{x}" cy="{y}" r="11" fill="{s.t["badge"]}"/>')
        s.text(x, y + 4.5, str(n), size=12.5, color=s.t["badgetext"], weight=700, anchor="middle")

    def card(s, x, y, w, h, icon, title, lines=(), badges=(), mono_lines=(), fill=None, stroke=None):
        s.rect(x, y, w, h, fill=fill, stroke=stroke)
        s.icon(icon, x + 14, y + 13, 24)
        s.text(x + 48, y + 31, title, size=16, weight=650)
        yy = y + 54
        for ln in lines:
            mono = ln in mono_lines
            s.text(x + 16, yy, ln, size=13.5 if not mono else 13, color=s.t["muted"], mono=mono)
            yy += 19
        bx = x + w - 18
        for b in reversed(badges):
            s.badge(bx, y + 25, b)
            bx -= 26

    def line(s, pts, kind, dash=None, sw=2.6, start=False, end=True):
        d = "M" + " L".join(f"{a} {b}" for a, b in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ''
        ms = f' marker-start="url(#a-{kind})"' if start else ''
        me = f' marker-end="url(#a-{kind})"' if end else ''
        s.add(f'<path d="{d}" fill="none" stroke="{s.t[kind]}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"{da}{ms}{me}/>')

    def pill(s, x, y, txt, kind, anchor="middle", size=12.5, mono=False):
        # label sitting on a road, with a background so it stays readable over lines
        w = len(txt) * (7.6 if mono else 6.9) + 18
        x0 = x - w / 2 if anchor == "middle" else x if anchor == "start" else x - w
        s.add(f'<rect x="{x0:.1f}" y="{y - 15}" width="{w:.1f}" height="22" rx="11" fill="{s.t["bg"]}" stroke="{s.t[kind]}" stroke-width="1.3"/>')
        s.text(x0 + w / 2, y + 0.5, txt, size=size, color=s.t[kind], weight=600, anchor="middle", mono=mono)

    def save(s, path):
        s.o.append('</svg>')
        open(path, "w").write("\n".join(s.o) + "\n")


def network(t):
    s = SVG(1240, 900, t, "How the server is wired",
            "Shopify webhooks reach n8n through Cloudflare and a tunnel the server opens outward. "
            "The owner reaches SSH and the n8n editor only over Tailscale. n8n calls Slack and Shopify outward. "
            "The firewall drops everything else.")
    s.text(40, 52, "How the server is wired", size=26, weight=700)
    s.text(40, 80, "The rehearsal VM on the laptop (step 1.13). The cloud server at 1.14 is the same picture without the laptop around it.",
           size=14.5, color=t["muted"])

    # ---- outside world
    s.text(40, 128, "INTERNET", size=12.5, color=t["muted"], weight=700)
    s.card(40, 142, 230, 92, "shopify", "Shopify", ["dev store: sends a webhook", "when stock changes"])
    s.card(40, 392, 230, 112, "cloudflare", "Cloudflare", ["hooks.mjesar.dpdns.org", "lets through only /webhook/", "and /healthz, else 404"], badges=[6])
    s.card(40, 690, 230, 92, "chat", "Slack", ["the alert lands here,", "on the owner's phone"])

    # ---- laptop
    s.rect(320, 112, 880, 712, fill=t["box"], stroke=t["stroke"], rx=18, sw=2)
    s.icon("laptop", 338, 124, 26)
    s.text(374, 144, "Your laptop", size=17, weight=700)
    s.card(345, 172, 225, 122, "terminal", "You", ["terminal: SSH key id_ed25519", "browser: 127.0.0.1:5680,", "the SSH tunnel's near end"], badges=[4])
    s.card(345, 336, 225, 92, "tailscale", "Tailscale", ["private address 100.x", "only your own devices"], badges=[5])
    s.rect(345, 590, 225, 88, fill=t["card"], stroke=t["bad"], dash="6 5")
    s.text(361, 618, "Multipass network", size=15, weight=650)
    s.text(361, 640, "the VM's own address 10.97.0.x,", size=13.5, color=t["muted"])
    s.text(361, 659, "or any other way in", size=13.5, color=t["muted"])

    # ---- VM
    s.rect(608, 160, 572, 646, fill=t["box2"], stroke=t["stroke"], rx=16, sw=1.8)
    s.icon("ubuntu", 624, 174, 24)
    s.text(658, 193, "Multipass VM  ·  Ubuntu 26.04 LTS", size=16, weight=700)
    s.badge(1160, 186, 1)
    # firewall wall along the VM's left side
    s.rect(620, 216, 34, 576, fill=t["wall"], stroke=t["web"], rx=8, sw=1.3)
    s.add(f'<text transform="translate(643 606) rotate(-90)" font-size="13.5" font-weight="700" fill="{t["web"]}">ufw: deny in, allow out</text>')
    s.badge(637, 232, 8)

    s.card(672, 336, 196, 92, "tailscale", "Tailscale", ["address 100.x", "key expiry off"], badges=[5])
    s.card(672, 216, 196, 92, "key", "SSH :22", ["keys only, root off"], badges=[8])
    s.text(688, 292, "tunnel → n8n :5678", size=13.5, color=t["admin"], weight=650)
    s.card(672, 690, 196, 92, "clock", "Auto updates", ["security fixes daily,", "reboot 04:00 if needed"], badges=[7])
    s.card(672, 560, 196, 100, "file", "Repo + .env", ["git clone of the repo,", ".env copied, chmod 600"], badges=[3])

    # docker box
    s.rect(892, 216, 270, 444, fill=t["box"], stroke=BRAND["docker"], rx=14, sw=1.8)
    s.icon("docker", 906, 228, 28)
    s.text(944, 249, "Docker Compose", size=16, weight=700)
    s.badge(1142, 240, 2)
    s.card(908, 270, 238, 128, "n8n", "n8n 2.47.4", ["runs the workflows", "published on 127.0.0.1:5678", "only, never 0.0.0.0", "restart: unless-stopped"], badges=[9])
    s.card(908, 440, 238, 92, "cloudflare", "cloudflared", ["dials out to Cloudflare,", "nothing listens for it"], badges=[6])
    s.card(908, 570, 238, 74, "db", "n8n_data volume", ["database, credentials (encrypted)"])

    # ---- roads
    # 1. webhook: Shopify -> Cloudflare -> tunnel -> cloudflared -> n8n
    s.line([(130, 234), (130, 392)], "web")
    s.pill(130, 318, "HTTPS POST", "web")
    s.line([(908, 486), (270, 486)], "web", start=True, end=False)
    s.pill(440, 487, "tunnel, opened from inside", "web")
    s.line([(1027, 440), (1027, 398)], "web")
    s.pill(1027, 420, ":5678", "web", mono=True)

    # 2. admin: laptop -> tailnet -> VM tailscale -> ssh -> tunnel to n8n
    s.line([(457, 294), (457, 336)], "admin")
    s.line([(570, 382), (672, 382)], "admin")
    s.add(f'<circle cx="637" cy="382" r="13" fill="{t["bg"]}" stroke="{t["out"]}" stroke-width="2"/>')
    s.add(f'<path d="M631 382l4.5 4.5 7.5-8.5" fill="none" stroke="{t["out"]}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')
    s.line([(770, 336), (770, 308)], "admin")
    s.line([(868, 262), (930, 262), (930, 270)], "admin")
    s.pill(500, 452, "SSH only on tailscale0", "admin")

    # 3. outbound: n8n -> Slack, n8n -> Shopify Admin API
    s.line([(1146, 334), (1186, 334), (1186, 846), (155, 846), (155, 782)], "out")
    s.pill(700, 846, "alert: Slack API (outbound)", "out")
    s.line([(1100, 270), (1100, 100), (300, 100), (300, 188), (270, 188)], "out")
    s.pill(700, 100, "token + product lookup: Shopify Admin API (outbound)", "out")

    # 4. blocked
    s.line([(570, 634), (618, 634)], "bad", dash="5 5")
    s.add(f'<g stroke="{t["bad"]}" stroke-width="3" stroke-linecap="round"><path d="M629 625l16 18M645 625l-16 18"/></g>')
    s.text(458, 700, "SSH and :5678 time out", size=13.5, color=t["bad"], weight=650, anchor="middle")

    # ---- legend
    lx, ly = 40, 548
    s.text(lx, ly - 18, "ROADS", size=12.5, color=t["muted"], weight=700)
    for i, (k, lbl) in enumerate([("web", "webhook, public"), ("admin", "you, over Tailscale"), ("out", "calls going out"), ("bad", "blocked")]):
        yy = ly + i * 26
        s.line([(lx, yy), (lx + 34, yy)], k, dash="5 5" if k == "bad" else None, end=False)
        s.text(lx + 46, yy + 5, lbl, size=13.5)
    s.badge(lx + 11, ly + 110, "1")
    s.text(lx + 30, ly + 115, "= part of SERVER_SETUP.md", size=13.5, color=t["muted"])
    return s


def secrets(t):
    s = SVG(1240, 640, t, "Where the secrets live",
            ".env on the server holds nine values. Docker Compose hands each container only the names listed for it: "
            "n8n gets four, cloudflared gets the tunnel token. The Shopify values are read by a script on the host. "
            "The Slack token and the Shopify secret n8n uses are pasted into n8n credentials, stored encrypted in its volume.")
    s.text(40, 52, "Where the secrets live", size=26, weight=700)
    s.text(40, 80, "Each container gets only the values it uses (D19, D31). Nothing here is ever committed to git.", size=14.5, color=t["muted"])

    # .env
    s.rect(40, 112, 360, 380, fill=t["card"])
    s.icon("file", 56, 126, 26)
    s.text(92, 146, ".env on the server", size=17, weight=700)
    s.text(56, 170, "copied from the laptop, chmod 600", size=13.5, color=t["muted"])
    s.badge(380, 138, 3)
    groups = [
        (192, "out", ["N8N_ENCRYPTION_KEY", "N8N_WEBHOOK_URL", "N8N_PROXY_HOPS", "N8N_EDITOR_BASE_URL"]),
        (318, "web", ["TUNNEL_TOKEN"]),
        (382, "admin", ["SHOPIFY_STORE", "SHOPIFY_CLIENT_ID", "SHOPIFY_CLIENT_SECRET"]),
    ]
    for y0, k, names in groups:
        h = 22 * len(names) + 14
        s.add(f'<rect x="56" y="{y0}" width="5" height="{h}" rx="2.5" fill="{t[k]}"/>')
        for i, n in enumerate(names):
            s.text(74, y0 + 22 + i * 22, n, size=13.5, mono=True)

    # compose in the middle
    s.rect(470, 200, 250, 210, fill=t["box"], stroke=BRAND["docker"], sw=1.8)
    s.icon("docker", 486, 214, 28)
    s.text(524, 236, "docker-compose.yml", size=16, weight=700)
    s.text(486, 266, "fills each ${NAME} from .env,", size=13.5, color=t["muted"])
    s.text(486, 286, "but passes a container only", size=13.5, color=t["muted"])
    s.text(486, 306, "the names it lists:", size=13.5, color=t["muted"])
    s.text(486, 340, "environment:", size=13, mono=True)
    s.text(502, 360, "N8N_WEBHOOK_URL: ${…}", size=13, mono=True, color=t["muted"])
    s.text(502, 380, "…", size=13, mono=True, color=t["muted"])

    # targets
    s.card(800, 112, 400, 120, "n8n", "n8n container", ["sees 4 values: the N8N_* group", "no Shopify secret, no tunnel token", "$env in nodes blocked too (n8n default)"], badges=[6])
    s.card(800, 262, 400, 96, "cloudflare", "cloudflared container", ["sees 1 value: TUNNEL_TOKEN,", "which tunnel to serve and the key to it"], badges=[6])
    s.card(800, 388, 400, 104, "script", "subscribe-webhook.sh (host)", ["reads SHOPIFY_* and the webhook URL itself,", "not via Docker, to subscribe the store once"])

    # arrows env -> compose -> targets
    s.line([(400, 236), (470, 270)], "out")
    s.line([(400, 336), (470, 320)], "web")
    s.line([(720, 280), (800, 172)], "out")
    s.line([(720, 330), (800, 310)], "web")
    s.line([(400, 436), (800, 440)], "admin")
    s.pill(600, 438, "not through Docker", "admin")

    # pasted credentials row
    s.rect(40, 524, 1160, 92, fill=t["card"], stroke=t["stroke"], dash="6 5")
    s.icon("key", 56, 540, 26)
    s.text(92, 560, "Pasted into n8n's editor, not .env:", size=16, weight=700)
    s.text(92, 584, "Slack bot token, Shopify webhook signing secret, Shopify client credentials. Stored in the n8n_data volume,",
           size=13.5, color=t["muted"])
    s.text(92, 603, "encrypted with N8N_ENCRYPTION_KEY. The repo holds only secret-free stubs (D28).", size=13.5, color=t["muted"])
    s.badge(1180, 552, 6)
    return s


os.makedirs(OUT, exist_ok=True)
for name, th in THEMES.items():
    network(th).save(f"{OUT}/server-setup-network-{name}.svg")
    secrets(th).save(f"{OUT}/server-setup-secrets-{name}.svg")
print("written")
