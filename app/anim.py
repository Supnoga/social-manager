"""Animácie v štýle Claude (čisté, moderné grafiky): počítadlo, stĺpce, zoznam, porovnanie, kinetický text.

Šablóny sú HTML/CSS + JS funkcia renderAt(t), takže každá snímka je presná. Renderuje ich Chromium (Playwright)
s priehľadným pozadím, aby išli aj cez záber. Výsledok sa ukladá podľa hashu – to isté sa nerenderuje dvakrát.
Chromium si appka stiahne sama na pozadí (raz, cca 150 MB). Kým nie je, videá idú bez animácií.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from . import db

CACHE = db.MEDIA_DIR / "anim"
CACHE.mkdir(parents=True, exist_ok=True)
TYPES = ("counter", "bars", "list", "compare", "kinetic")
STATE = {"installing": False, "error": ""}

BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;background:transparent;overflow:hidden;font-family:-apple-system,'SF Pro Display','Inter','Helvetica Neue',Arial,sans-serif;color:#fff}
.stage{position:absolute;left:70px;right:180px;top:430px;height:700px;display:flex;flex-direction:column;justify-content:center;align-items:center}
.card{background:rgba(12,12,12,.82);border:2px solid rgba(255,255,255,.12);border-radius:44px;padding:48px 52px;width:100%;box-shadow:0 30px 80px rgba(0,0,0,.45)}
.acc{color:var(--acc)}
"""

TEMPLATES = {
    "counter": ("""<div class="stage"><div class="card" id="c" style="text-align:center">
<div id="num" style="font-size:230px;font-weight:800;letter-spacing:-6px;line-height:1"></div>
<div id="lab" style="font-size:58px;font-weight:600;margin-top:22px;opacity:.9"></div></div></div>""",
                """const D=DATA;document.getElementById('lab').textContent=D.label||'';
function renderAt(t){const c=document.getElementById('c');const k=E(cl(t/0.45));c.style.transform=`scale(${0.85+0.15*k})`;c.style.opacity=k;
const p=E(cl((t-0.2)/1.2));const v=(+D.value||0)*p;const dec=String(D.value).includes('.')||String(D.value).includes(',')?(String(D.value).split(/[.,]/)[1]||'').length:0;
document.getElementById('num').innerHTML=(D.prefix||'')+'<span class="acc">'+v.toFixed(dec).replace('.',D.comma?',':'.')+'</span>'+(D.suffix||'');
const l=document.getElementById('lab');l.style.opacity=E(cl((t-0.9)/0.4));l.style.transform=`translateY(${(1-E(cl((t-0.9)/0.4)))*30}px)`}"""),
    "bars": ("""<div class="stage"><div class="card" id="c"><div id="ti" style="font-size:54px;font-weight:700;margin-bottom:30px"></div><div id="rows"></div></div></div>""",
             """const D=DATA;document.getElementById('ti').textContent=D.title||'';const max=Math.max(...D.items.map(i=>+i.value||0))||1;
document.getElementById('rows').innerHTML=D.items.slice(0,5).map((it,i)=>`<div style="margin:0 0 26px"><div style="display:flex;justify-content:space-between;font-size:44px;font-weight:600;margin-bottom:10px"><span>${it.label}</span><span class="acc" id="v${i}"></span></div><div style="height:30px;background:rgba(255,255,255,.1);border-radius:15px;overflow:hidden"><div id="b${i}" style="height:100%;background:var(--acc);border-radius:15px;width:0"></div></div></div>`).join('');
function renderAt(t){const c=document.getElementById('c');const k=E(cl(t/0.4));c.style.opacity=k;c.style.transform=`translateY(${(1-k)*40}px)`;
D.items.slice(0,5).forEach((it,i)=>{const p=E(cl((t-0.3-i*0.22)/0.8));document.getElementById('b'+i).style.width=(p*(+it.value||0)/max*100)+'%';
const dec=String(it.value).includes('.')?(String(it.value).split('.')[1]||'').length:0;document.getElementById('v'+i).textContent=(D.prefix||'')+((+it.value||0)*p).toFixed(dec).replace('.',D.comma?',':'.')+(D.suffix||'')})}"""),
    "list": ("""<div class="stage"><div class="card" id="c"><div id="ti" style="font-size:60px;font-weight:800;margin-bottom:34px"></div><div id="rows"></div></div></div>""",
             """const D=DATA;document.getElementById('ti').textContent=D.title||'';
document.getElementById('rows').innerHTML=D.items.slice(0,5).map((it,i)=>`<div id="r${i}" style="display:flex;align-items:center;gap:28px;margin-bottom:26px;font-size:48px;font-weight:600"><div style="flex:none;width:84px;height:84px;border-radius:42px;background:var(--acc);color:#000;display:flex;align-items:center;justify-content:center;font-weight:800">${i+1}</div><div>${it}</div></div>`).join('');
function renderAt(t){const c=document.getElementById('c');const k=E(cl(t/0.4));c.style.opacity=k;c.style.transform=`translateY(${(1-k)*40}px)`;
D.items.slice(0,5).forEach((it,i)=>{const p=E(cl((t-0.35-i*0.35)/0.45));const r=document.getElementById('r'+i);r.style.opacity=p;r.style.transform=`translateX(${(1-p)*-60}px)`})}"""),
    "compare": ("""<div class="stage"><div style="display:flex;gap:34px;width:100%">
<div class="card" id="l" style="text-align:center;opacity:.75"><div id="ll" style="font-size:46px;font-weight:600"></div><div id="lv" style="font-size:120px;font-weight:800;margin-top:16px"></div></div>
<div class="card" id="r" style="text-align:center;border-color:var(--acc)"><div id="rl" style="font-size:46px;font-weight:600"></div><div id="rv" class="acc" style="font-size:120px;font-weight:800;margin-top:16px"></div></div></div>
<div id="vs" style="position:absolute;font-size:52px;font-weight:800;background:#fff;color:#000;border-radius:40px;padding:10px 26px">VS</div></div>""",
                """const D=DATA;['l','r'].forEach(s=>{const o=D[s==='l'?'left':'right']||{};document.getElementById(s+'l').textContent=o.label||'';document.getElementById(s+'v').textContent=o.value||''});
function renderAt(t){const a=E(cl(t/0.5)),b=E(cl((t-0.35)/0.5)),v=E(cl((t-0.7)/0.3));const l=document.getElementById('l'),r=document.getElementById('r');
l.style.transform=`translateX(${(1-a)*-120}px)`;l.style.opacity=0.75*a;r.style.transform=`translateX(${(1-b)*120}px) scale(${1+0.04*E(cl((t-1.2)/0.3))})`;r.style.opacity=b;
const vs=document.getElementById('vs');vs.style.opacity=v;vs.style.transform=`scale(${0.5+0.5*v})`}"""),
    "kinetic": ("""<div class="stage" id="s" style="text-align:center"></div>""",
                """const D=DATA;const W=(D.words||[]).slice(0,6);document.getElementById('s').innerHTML=W.map((w,i)=>`<div id="w${i}" style="font-size:${W.length>4?120:150}px;font-weight:900;line-height:1.05;letter-spacing:-3px;text-transform:uppercase;${i===W.length-1?'color:var(--acc)':''};text-shadow:0 8px 40px rgba(0,0,0,.6)">${w}</div>`).join('');
function renderAt(t){W.forEach((w,i)=>{const p=cl((t-i*0.28)/0.3);const e=1+Math.sin(p*Math.PI)*0.12;const el=document.getElementById('w'+i);el.style.opacity=p>0?1:0;el.style.transform=`scale(${p>0?E(p)*e:0})`})}"""),
}

HELPERS = "function cl(x){return Math.max(0,Math.min(1,x))}function E(x){return 1-Math.pow(1-x,3)}"


def html(kind, data, accent="#FF6B00", font=None):
    body, js = TEMPLATES[kind]
    fcss = ""
    if font and Path(font).exists():
        import base64
        b64 = base64.b64encode(Path(font).read_bytes()).decode()
        fcss = (f"@font-face{{font-family:BrandF;src:url(data:font/{Path(font).suffix.lstrip('.').lower()};base64,{b64})}}"
                "html,body{font-family:BrandF,-apple-system,'SF Pro Display','Inter','Helvetica Neue',Arial,sans-serif}")
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>:root{{--acc:{accent}}}{BASE_CSS}{fcss}</style></head>"
            f"<body>{body}<script>const DATA={json.dumps(data, ensure_ascii=False)};{HELPERS}{js}</script></body></html>")


# ---------- Chromium ----------
def available():
    try:
        from playwright.sync_api import sync_playwright  # noqa
    except Exception:
        return False
    marker = db.DATA_DIR / ".chromium_ok"
    return marker.exists()


def ensure_installed():
    """Na pozadí raz stiahne Chromium (zadarmo). Nič nezdržuje."""
    if available() or STATE["installing"]:
        return

    def go():
        STATE["installing"] = True
        try:
            py = sys.executable
            subprocess.run([py, "-m", "pip", "install", "-q", "playwright>=1.45"], capture_output=True,
                           stdin=subprocess.DEVNULL, start_new_session=True, timeout=900)
            r = subprocess.run([py, "-m", "playwright", "install", "chromium"], capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, start_new_session=True, timeout=1800)
            if r.returncode == 0:
                (db.DATA_DIR / ".chromium_ok").write_text("ok")
                STATE["error"] = ""
            else:
                STATE["error"] = (r.stderr or r.stdout)[-300:]
        except Exception as e:
            STATE["error"] = str(e)[:300]
        finally:
            STATE["installing"] = False
    threading.Thread(target=go, daemon=True).start()


def status():
    return {"ready": available(), "installing": STATE["installing"], "error": STATE["error"]}


_render_lock = threading.Lock()


def render(kind, data, accent="#FF6B00", dur=3.0, fps=30, font=None):
    """Vyrenderuje animáciu ako priehľadné video (.mov). Vráti cestu alebo None."""
    if kind not in TEMPLATES or not available():
        return None
    from . import media
    h = hashlib.sha1(json.dumps([kind, data, accent, round(dur, 2), fps] + ([font] if font else []), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    out = CACHE / f"{kind}_{h}.mov"
    if out.exists():
        return str(out)
    from playwright.sync_api import sync_playwright
    with _render_lock, tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        import os
        exe = os.environ.get("SM_CHROMIUM")
        b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        try:
            pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
            pg.set_content(html(kind, data, accent, font))
            n = max(1, int(dur * fps))
            for i in range(n):
                pg.evaluate(f"renderAt({i / fps})")
                pg.screenshot(path=f"{tmp}/f{i:04d}.png", omit_background=True)
        finally:
            b.close()
        media._run_ff([media.ffmpeg(), "-y", "-framerate", str(fps), "-i", f"{tmp}/f%04d.png", "-c:v", "png",
                       "-pix_fmt", "rgba", str(out)])
    return str(out)


def texts(a):
    """Texty animácie na preklad (čísla ostávajú)."""
    d = (a or {}).get("d") or {}
    k = (a or {}).get("t")
    if k == "counter":
        return [d.get("label", "")]
    if k == "bars":
        return [d.get("title", "")] + [i.get("label", "") for i in d.get("items", [])]
    if k == "list":
        return [d.get("title", "")] + list(d.get("items", []))
    if k == "compare":
        return [(d.get("left") or {}).get("label", ""), (d.get("right") or {}).get("label", "")]
    if k == "kinetic":
        return [" ".join(d.get("words", []))]
    return []


def with_texts(a, tr):
    """Vráti kópiu animácie s preloženými textami (v rovnakom poradí ako texts())."""
    a = json.loads(json.dumps(a))
    d, k, it = a.get("d") or {}, a.get("t"), iter(tr)
    if k == "counter":
        d["label"] = next(it, d.get("label", ""))
    elif k == "bars":
        d["title"] = next(it, d.get("title", ""))
        for x in d.get("items", []):
            x["label"] = next(it, x.get("label", ""))
    elif k == "list":
        d["title"] = next(it, d.get("title", ""))
        d["items"] = [next(it, x) for x in d.get("items", [])]
    elif k == "compare":
        (d.setdefault("left", {}))["label"] = next(it, "")
        (d.setdefault("right", {}))["label"] = next(it, "")
    elif k == "kinetic":
        d["words"] = next(it, " ".join(d.get("words", []))).split()
    a["d"] = d
    return a
