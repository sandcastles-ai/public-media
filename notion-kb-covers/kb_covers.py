import html
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')

CX, CY = 1000, 225

BLUE = '#3b82f6'
CLAUDE_ORANGE = '#d97757'

CATEGORY_ACCENT = {
    'General': '#3b82f6',
    'Videos': '#8b5cf6',
    'Ideas': '#ec4899',
    'Scripts': '#10b981',
    'Channels': '#f59e0b',
    'Settings': '#f97316',
    'Billing': '#22c55e',
}

PAGE_ACCENT = {
    '343acc48f1da81f293fdcded23f5aaae': '#0ea5e9',
    '343acc48f1da8167b46ee18bc4762113': '#d946ef',
    '343acc48f1da8125aa5fe07461c7936f': '#f43f5e',
    '3bfacc48f1da817aa758e1630e08bbe5': '#14b8a6',
    '3a3acc48f1da8141a6b7d76aa21c19f3': '#6366f1',
    '35eacc48f1da81b2b297de871e4f1667': '#84cc16',
    '354acc48f1da811aa801de0d5f5c8844': '#06b6d4',
    '343acc48f1da81aebafcea7eabf89de2': '#eab308',
}

PARTNER_ACCENT = {'claude': CLAUDE_ORANGE, 'chatgpt': '#10a37f', 'grok': '#a1a1aa'}

LOGO_TILES = {'sandcastles', 'claude', 'chatgpt', 'grok', 'youtube', 'tiktok', 'instagram'}

CSS = '''
  @font-face { font-family: 'InterVariable'; font-weight: 100 900; src: url('../fonts/InterVariable.woff2') format('woff2'); }
  @font-face { font-family: 'JetBrains Mono'; font-weight: 500; src: url('../fonts/JetBrainsMono-500.woff2') format('woff2'); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 2000px; height: 500px; overflow: hidden; }
  body {
    font-family: 'InterVariable', sans-serif;
    font-feature-settings: 'cv11', 'ss01';
    -webkit-font-smoothing: antialiased;
    overflow: hidden; position: relative;
    background: #09090b;
    color: #fff;
  }
  .layer { position: absolute; inset: 0; }
  .glow { position: absolute; border-radius: 50%; filter: blur(10px); mix-blend-mode: screen; }
  .grid {
    background-image: radial-gradient(rgba(255,255,255,0.13) 1px, transparent 1.3px);
    background-size: 24px 24px; background-position: 12px 12px;
    -webkit-mask-image: radial-gradient(ellipse 50% 95% at 50% 45%, transparent 25%, #000 80%);
  }
  .ring { position: absolute; border-radius: 50%; border: 1px solid rgba(255,255,255,0.09); }
  .vignette { background: radial-gradient(ellipse 70% 130% at 50% 45%, transparent 55%, rgba(9,9,11,0.7) 100%); }
  .node { position: absolute; width: 6px; height: 6px; margin: -3px 0 0 -3px; border-radius: 999px; background: #fff; }

  .core { position: absolute; left: 0; right: 0; top: 225px; transform: translateY(-50%); display: flex; align-items: center; justify-content: center; }
  .tile {
    width: 176px; height: 176px; border-radius: 44px; background: #fff;
    display: flex; align-items: center; justify-content: center; position: relative;
  }
  .tile .mark { width: 100px; }
  .tile .spark { width: 106px; }
  .tile .ic { width: 92px; height: 92px; }
  .tile .brand { width: 96px; height: 96px; }
  .tile .png { width: 104px; height: 104px; object-fit: contain; }
  .tile .tbadge {
    position: absolute; top: -16px; right: -16px; width: 64px; height: 64px; border-radius: 999px;
    box-shadow: 0 0 0 5px #09090b, 0 10px 24px -6px rgba(0,0,0,0.7);
  }
  .platforms { display: flex; gap: 28px; }

  .wire { position: relative; width: 236px; height: 176px; display: flex; align-items: center; justify-content: center; }
  .wire .line { position: absolute; left: 8px; right: 8px; top: 50%; height: 3px; margin-top: -1.5px; border-radius: 3px; }
  .wire .dot { position: absolute; top: 50%; width: 14px; height: 14px; margin-top: -7px; border-radius: 999px; background: #fff; }
  .wire .dot.l { left: 0; }
  .wire .dot.r { right: 0; }
  .wire .pill {
    position: relative; background: #fff; color: #09090b;
    font-weight: 700; font-size: 19px; letter-spacing: 0.08em;
    padding: 9px 19px; border-radius: 999px;
  }

  .chip {
    margin-left: 30px; height: 104px; padding: 0 34px; border-radius: 28px;
    display: flex; align-items: center; white-space: nowrap;
    background: rgba(24,24,27,0.82);
    font-weight: 650; letter-spacing: -0.02em; color: #fff;
  }
  .chip.mono { font-family: 'JetBrains Mono', monospace; font-weight: 500; letter-spacing: -0.01em; font-variant-ligatures: none; font-feature-settings: 'calt' 0, 'liga' 0; }

  .side {
    position: absolute; top: 225px; transform: translateY(-50%); width: 380px;
    background: rgba(24,24,27,0.78);
    box-shadow: 0 0 0 1px rgba(255,255,255,0.1) inset, 0 24px 48px -16px rgba(0,0,0,0.7);
    border-radius: 18px; padding: 22px 26px;
  }
  .side.left { left: 40px; }
  .side.right { right: 40px; }
  .eyebrow { font-size: 15px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: #a1a1aa; }
  .head { display: flex; align-items: center; gap: 12px; font-size: 21px; font-weight: 600; letter-spacing: -0.01em; }
  .mini { width: 36px; height: 36px; border-radius: 10px; background: #fff; display: flex; align-items: center; justify-content: center; }
  .mini .mark { width: 21px; }
  .mini .ic { width: 20px; height: 20px; }
  .mini .brand { width: 21px; height: 21px; }
  .badge {
    margin-left: auto; display: inline-flex; align-items: center; gap: 6px;
    background: rgba(34,197,94,0.1); color: #4ade80;
    font-size: 15px; line-height: 24px; font-weight: 500; padding: 1px 10px; border-radius: 7px;
  }
  .badge i { width: 7px; height: 7px; border-radius: 999px; background: #22c55e; display: block; }
  .label { margin-top: 18px; font-size: 16px; color: #a1a1aa; }
  .code {
    margin-top: 8px; display: flex; align-items: center; justify-content: space-between;
    border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); border-radius: 8px; padding: 8px 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 17px; font-weight: 500; color: #fff;
    font-variant-ligatures: none; font-feature-settings: 'calt' 0, 'liga' 0;
  }
  .code .ic { width: 20px; height: 20px; color: #71717a; }
  .steps { list-style: none; margin-top: 16px; display: flex; flex-direction: column; gap: 13px; }
  .steps li { display: flex; align-items: center; gap: 12px; font-size: 19px; font-weight: 500; color: rgba(255,255,255,0.92); }
  .steps b {
    width: 28px; height: 28px; border-radius: 999px; flex: none;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 700; color: #fff;
  }
  .side .arrow { color: #71717a; font-weight: 400; }
  .rows { list-style: none; margin-top: 16px; display: flex; flex-direction: column; gap: 12px; }
  .rows li { display: flex; align-items: center; gap: 12px; font-size: 19px; font-weight: 500; color: rgba(255,255,255,0.92); }
  .rows .ico { width: 32px; height: 32px; border-radius: 9px; flex: none; display: flex; align-items: center; justify-content: center; }
  .rows .ico .ic { width: 19px; height: 19px; }
  .chips { margin-top: 16px; display: flex; flex-wrap: wrap; gap: 9px; }
  .chips span {
    font-size: 17px; font-weight: 500; line-height: 24px; color: rgba(255,255,255,0.92);
    padding: 5px 12px; border-radius: 9px; background: rgba(255,255,255,0.06);
    box-shadow: 0 0 0 1px rgba(255,255,255,0.12) inset;
  }
  .bubble {
    margin-top: 14px; padding: 14px 16px; border-radius: 16px 16px 16px 6px;
    background: rgba(255,255,255,0.07); box-shadow: 0 0 0 1px rgba(255,255,255,0.1) inset;
    font-size: 18px; line-height: 1.45; font-weight: 450; color: rgba(255,255,255,0.94); overflow-wrap: anywhere;
  }
'''

FIT_JS = '''
<script>
  document.fonts.ready.then(() => {
    const chip = document.querySelector('.chip')
    if (chip) {
      let size = 56
      chip.style.fontSize = size + 'px'
      while (chip.getBoundingClientRect().width > 436 && size > 26) {
        size -= 1
        chip.style.fontSize = size + 'px'
      }
    }
    document.body.dataset.ready = '1'
  })
</script>
'''

SC_PATHS = open(os.path.join(HERE, 'logo_paths.txt')).read().split('\n')


def slugify(title):
    s = title.lower().replace('&', ' and ').replace("'", '').replace('’', '')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def esc(s):
    return html.escape(s, quote=True)


def rgba(hex_, a):
    h = hex_.lstrip('#')
    return f'rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})'


def icon(name, cls='ic'):
    ds = open(os.path.join(HERE, 'icons', f'{name}.d')).read().split('|')
    paths = ''.join(f'<path stroke-linecap="round" stroke-linejoin="round" d="{d}"/>' for d in ds)
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">{paths}</svg>'


def sc_mark(fill, cls):
    inner = ''.join(f'<path d="{p}" fill="{fill}"/>' for p in SC_PATHS)
    return f'<svg class="{cls}" viewBox="0 0 224.582 181.97">{inner}</svg>'


def claude_mark(fill, cls):
    d = open(os.path.join(HERE, 'icons', 'claude.d')).read()
    return f'<svg class="{cls}" viewBox="0 0 24 24"><path d="{d}" fill="{fill}"/></svg>'


def path_svg(name, fill, cls='brand'):
    d = open(os.path.join(HERE, 'icons', f'{name}.d')).read()
    return f'<svg class="{cls}" viewBox="0 0 24 24"><path fill-rule="evenodd" d="{d}" fill="{fill}"/></svg>'


def logo(name, cls_mark='mark', cls_brand='brand'):
    if name == 'sandcastles':
        return sc_mark(BLUE, cls_mark)
    if name == 'claude':
        return claude_mark(CLAUDE_ORANGE, 'spark' if cls_mark == 'mark' else cls_brand)
    if name == 'chatgpt':
        return path_svg('lh-openai', '#0d0d0d', cls_brand)
    if name == 'grok':
        return path_svg('lh-grok', '#0d0d0d', cls_brand)
    if name in ('youtube', 'tiktok', 'instagram'):
        return f'<img class="png" src="../assets/{name}.png">'
    return None


def glow(x, y, rx, ry, color, a):
    return (
        f'<div class="glow" style="left:{x - rx}px;top:{y - ry}px;width:{rx * 2}px;height:{ry * 2}px;'
        f'background:radial-gradient(closest-side, {rgba(color, a)}, {rgba(color, a * 0.35)} 55%, {rgba(color, 0)} 100%)"></div>'
    )


def rings():
    out = []
    for i, r in enumerate([190, 290, 390, 490, 590, 690, 790]):
        a = max(0.035, 0.12 - i * 0.014)
        out.append(
            f'<div class="ring" style="left:{CX - r}px;top:{CY - r}px;width:{r * 2}px;height:{r * 2}px;border-color:rgba(255,255,255,{a:.3f})"></div>'
        )
    return ''.join(out)


def nodes(items):
    out = []
    for r, deg, color in items:
        x = CX + r * math.cos(math.radians(deg))
        y = CY + r * math.sin(math.radians(deg))
        out.append(f'<div class="node" style="left:{x:.0f}px;top:{y:.0f}px;box-shadow:0 0 0 4px {rgba(color, 0.25)}, 0 0 14px {rgba(color, 0.9)}"></div>')
    return ''.join(out)


def tile(inner, color, cls='tile', badge=None):
    shadow = f'0 0 0 8px {rgba(color, 0.2)}, 0 0 100px {rgba(color, 0.6)}, 0 28px 56px -14px rgba(0,0,0,0.75)'
    extra = '<img class="tbadge" src="../assets/logo-icon.png">' if badge == 'sandcastles' else ''
    return f'<div class="{cls}" style="box-shadow:{shadow}">{inner}{extra}</div>'


def tile_inner(name, accent):
    found = logo(name)
    if found:
        return found
    return icon(name).replace('class="ic"', f'class="ic" style="color:{accent}"')


def accent_for(spec):
    core = spec['core']
    if spec['page_id'] in PAGE_ACCENT:
        return PAGE_ACCENT[spec['page_id']]
    if core['type'] == 'pair':
        return PARTNER_ACCENT[core['right']]
    if core.get('tile') in PARTNER_ACCENT:
        return PARTNER_ACCENT[core['tile']]
    return CATEGORY_ACCENT.get(spec['category'], BLUE)


def core_html(spec, accent):
    core = spec['core']
    if core['type'] == 'pair':
        right = core['right']
        rc = PARTNER_ACCENT[right]
        right_inner = claude_mark(CLAUDE_ORANGE, 'spark') if right == 'claude' else logo(right)
        return f'''
    <div class="core">
      {tile(sc_mark(BLUE, 'mark'), BLUE)}
      <div class="wire">
        <span class="line" style="background:linear-gradient(90deg,{BLUE},{rc});box-shadow:0 0 18px {rgba('#ffffff', 0.35)}"></span>
        <span class="dot l" style="box-shadow:0 0 0 6px {rgba(BLUE, 0.35)}"></span>
        <span class="pill" style="box-shadow:0 0 0 6px rgba(255,255,255,0.12), 0 12px 28px -8px rgba(0,0,0,0.7)">{esc(core['pill'])}</span>
        <span class="dot r" style="box-shadow:0 0 0 6px {rgba(rc, 0.35)}"></span>
      </div>
      {tile(right_inner, rc)}
    </div>'''
    if core['type'] == 'platforms':
        tiles = ''.join(tile(logo(p), accent, 'tile sm') for p in core['items'])
        return f'<div class="core"><div class="platforms">{tiles}</div></div>'
    text = esc(core['chip'])
    if core.get('mono') and text.startswith('/'):
        text = f'<span style="color:{accent}">/</span>{text[1:]}'
    cls = 'chip mono' if core.get('mono') else 'chip'
    chip_shadow = f'0 0 0 1px rgba(255,255,255,0.14) inset, 0 0 0 6px {rgba(accent, 0.14)}, 0 24px 48px -16px rgba(0,0,0,0.75)'
    tile_color = PARTNER_ACCENT.get(core['tile'], BLUE if core['tile'] == 'sandcastles' else accent)
    return f'''
    <div class="core">
      {tile(tile_inner(core['tile'], accent), tile_color, badge=core.get('badge'))}
      <div class="{cls}" style="box-shadow:{chip_shadow}">{text}</div>
    </div>'''


def with_arrows(text):
    return esc(text).replace('→', '<span class="arrow">→</span>')


def card_html(card, side, accent):
    t = card['type']
    if t == 'steps':
        items = ''.join(f'<li><b style="background:{accent}">{i + 1}</b>{with_arrows(s)}</li>' for i, s in enumerate(card['items']))
        body = f'<div class="eyebrow">{esc(card["eyebrow"])}</div><ol class="steps">{items}</ol>'
    elif t == 'list':
        items = ''.join(
            f'<li><span class="ico" style="background:{rgba(accent, 0.16)};color:{accent}">{icon(it["icon"])}</span>{with_arrows(it["text"])}</li>'
            for it in card['items']
        )
        body = f'<div class="eyebrow">{esc(card["eyebrow"])}</div><ul class="rows">{items}</ul>'
    elif t == 'chips':
        items = ''.join(f'<span>{esc(s)}</span>' for s in card['items'])
        body = f'<div class="eyebrow">{esc(card["eyebrow"])}</div><div class="chips">{items}</div>'
    elif t == 'prompt':
        body = f'<div class="eyebrow">{esc(card["eyebrow"])}</div><div class="bubble">{esc(card["text"])}</div>'
    elif t == 'code':
        mark = card['mark']
        found = logo(mark) if mark in LOGO_TILES else None
        if mark == 'claude':
            found = claude_mark(CLAUDE_ORANGE, 'brand')
        mini = found or icon(mark).replace('class="ic"', f'class="ic" style="color:{accent}"')
        badge = f'<span class="badge"><i></i>{esc(card["badge"])}</span>' if card.get('badge') else ''
        body = (
            f'<div class="head"><span class="mini">{mini}</span>{esc(card["title"])}{badge}</div>'
            f'<div class="label">{esc(card["label"])}</div>'
            f'<div class="code">{esc(card["code"])}{icon("square-2-stack")}</div>'
        )
    else:
        raise ValueError(t)
    return f'<div class="side {side}">{body}</div>'


def glows_for(spec, accent):
    core = spec['core']
    if core['type'] == 'pair':
        return [glow(790, CY, 560, 400, BLUE, 0.85), glow(1210, CY, 560, 400, PARTNER_ACCENT[core['right']], 0.85)]
    return [glow(CX, CY, 640, 420, accent, 0.9)]


def nodes_for(spec, accent):
    core = spec['core']
    right = PARTNER_ACCENT[core['right']] if core['type'] == 'pair' else accent
    left = BLUE if core['type'] == 'pair' else accent
    return [(290, -135, left), (390, 150, left), (590, -165, left), (290, 45, right), (390, -30, right), (590, 15, right)]


def cover(spec):
    accent = accent_for(spec)
    body = (
        ''.join(glows_for(spec, accent))
        + '<div class="layer grid"></div>'
        + rings()
        + '<div class="layer vignette"></div>'
        + nodes(nodes_for(spec, accent))
        + core_html(spec, accent)
        + card_html(spec['left'], 'left', accent)
        + card_html(spec['right'], 'right', accent)
    )
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{body}{FIT_JS}</body></html>
'''


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    specs = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'specs.json')))
    only = set(sys.argv[2:])
    manifest = []
    for spec in specs:
        slug = slugify(spec['title'])
        if only and slug not in only and spec['page_id'] not in only:
            continue
        open(os.path.join(OUT, slug + '.html'), 'w').write(cover(spec))
        manifest.append({'page_id': spec['page_id'], 'title': spec['title'], 'category': spec['category'], 'slug': slug})
    json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
    print(len(manifest), 'covers built')
