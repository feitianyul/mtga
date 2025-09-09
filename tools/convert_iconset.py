#!/usr/bin/env python3
"""
生成 macOS icon.iconset 并在 macOS 上用 iconutil 打包为 .icns。
用法:
  python tools/convert_iconset.py --src icons/f0bb32_bg-black.svg --out icons/f0bb32_bg-black.icns

会生成 build/icon.iconset，若在 macOS 上会尝试运行 iconutil 打包为 .icns。
依赖 (在 CI 的 mac runner 上安装):
  pip install pillow cairosvg imageio
或通过 brew 安装 imagemagick（可选，脚本中不依赖 magick）
"""
from pathlib import Path
import argparse
import sys

try:
    from PIL import Image
except Exception:
    print("请先安装 pillow: pip install pillow")
    sys.exit(2)

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

# iconset 所需文件映射 (filename, size_to_render)
ICON_ENTRIES = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]

def rasterize_svg_to_image(src: Path, size=1024):
    try:
        import cairosvg
    except Exception:
        raise RuntimeError("缺少 cairosvg，安装: pip install cairosvg")
    png_bytes = cairosvg.svg2png(url=str(src), output_width=size, output_height=size)
    from io import BytesIO
    return Image.open(BytesIO(png_bytes)).convert("RGBA")

def load_raster_image(src: Path):
    img = Image.open(src)
    # 对 ICO，Pillow 会返回第一帧/最大尺寸，转换为 RGBA
    return img.convert("RGBA")

def generate_iconset(src: Path, iconset_dir: Path):
    ensure_dir(iconset_dir)
    # 若是 svg，先把大尺寸 rasterize
    suffix = src.suffix.lower()
    if suffix == ".svg":
        base_img = rasterize_svg_to_image(src, size=1024)
    else:
        base_img = load_raster_image(src)

    for fname, target in ICON_ENTRIES:
        out = iconset_dir / fname
        img = base_img.copy()
        img = img.resize((target, target), Image.LANCZOS)
        img.save(out, format="PNG")
        print("生成", out)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="源图标（svg/png/ico）路径，例如 icons/f0bb32_bg-black.svg")
    parser.add_argument("--out", required=True, help="目标 icns 路径，例如 icons/f0bb32_bg-black.icns")
    args = parser.parse_args()

    src = Path(args.src)
    out_icns = Path(args.out)
    iconset_dir = Path("build/icon.iconset")

    if not src.exists():
        print("未找到源文件:", src)
        sys.exit(3)

    # 清理旧的 iconset
    if iconset_dir.exists():
        import shutil
        shutil.rmtree(iconset_dir)

    generate_iconset(src, iconset_dir)

    # 如果在 macOS 上，尝试打包为 icns
    if sys.platform == "darwin":
        print("在 macOS 上，尝试使用 iconutil 打包为 .icns ->", out_icns)
        import subprocess
        out_icns.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(out_icns)]
        subprocess.check_call(cmd)
        print("已生成", out_icns)
    else:
        print("非 macOS 系统：已生成 icon.iconset，请在 macOS 上运行:")
        print("  iconutil -c icns build/icon.iconset -o", out_icns)

if __name__ == "__main__":
    main()