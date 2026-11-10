"""Zostaví 'Social Manager.app' (Mac ikonka) a zabalí ho do zipu. Spúšťa sa pri vydaní novej verzie."""
import shutil
import stat
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist"
APP = OUT / "Social Manager.app"
CODE_ITEMS = ["app", "static", "mac", "requirements.txt", "VERSION", "NAVOD.md"]

PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>Social Manager</string>
<key>CFBundleDisplayName</key><string>Social Manager</string>
<key>CFBundleIdentifier</key><string>sk.socialmanager.app</string>
<key>CFBundleVersion</key><string>{v}</string>
<key>CFBundleShortVersionString</key><string>{v}</string>
<key>CFBundleExecutable</key><string>SocialManager</string>
<key>CFBundleIconFile</key><string>AppIcon</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>10.15</string>
<key>LSUIElement</key><true/>
</dict></plist>
"""


def icon(path):
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = 90
    d.rounded_rectangle([m, m, S - m, S - m], radius=200, fill=(10, 10, 10, 255))
    d.rounded_rectangle([m + 70, m + 70, S - m - 70, S - m - 70], radius=150, fill=(255, 107, 0, 255))
    c = S // 2
    d.polygon([(c - 130, c - 190), (c - 130, c + 190), (c + 200, c)], fill=(255, 255, 255, 255))
    img.save(path, sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)])


def build():
    if APP.exists():
        shutil.rmtree(APP)
    (APP / "Contents/MacOS").mkdir(parents=True)
    res = APP / "Contents/Resources"
    (res / "social-manager").mkdir(parents=True)
    v = (ROOT / "VERSION").read_text().strip()
    (APP / "Contents/Info.plist").write_text(PLIST.format(v=v))
    exe = APP / "Contents/MacOS/SocialManager"
    shutil.copy(ROOT / "mac/launcher.sh", exe)
    exe.chmod(0o755)
    icon(res / "AppIcon.icns")
    for it in CODE_ITEMS:
        src = ROOT / it
        if src.is_dir():
            shutil.copytree(src, res / "social-manager" / it, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy(src, res / "social-manager" / it)
    z = OUT / "Social-Manager-Mac.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in [APP] + sorted(APP.rglob("*")):
            arc = f.relative_to(OUT).as_posix()
            info = zipfile.ZipInfo(arc + ("/" if f.is_dir() else ""), date_time=__import__("time").localtime()[:6])
            mode = f.stat().st_mode
            info.external_attr = ((stat.S_IFDIR if f.is_dir() else stat.S_IFREG) | (mode & 0o777)) << 16
            if f.is_dir():
                info.external_attr |= 0x10
                zf.writestr(info, b"")
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, f.read_bytes())
    print(z)


if __name__ == "__main__":
    build()
