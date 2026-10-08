#!/usr/bin/env python3
"""릴스용 자산 준비 (원본은 수정하지 않음). 사용법: python3 prep_assets.py"""
import subprocess, tempfile, os
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
R = HERE.parents[2]                      # youwebd-assets
A = HERE / "assets"; A.mkdir(exist_ok=True)

def blur_box(im, box, radius=10, tint=None):
    reg = im.crop(box).filter(ImageFilter.GaussianBlur(radius))
    if tint:
        ov = Image.new("RGB", reg.size, tint[:3]); reg = Image.blend(reg, ov, tint[3])
    im.paste(reg, box[:2])

# 1) 사례 kit: 같은 목업 틀이므로 동일 크롭 → Lanczos 업스케일
CROP = (170, 90, 840, 530)               # 670x440
for slug, ext in [("theic","jpg"),("uberhouse","jpg"),("seokyung","jpg"),("aline","jpg"),("luxenova","jpg")]:
    im = Image.open(R/f"kit/{slug}.{ext}").convert("RGB").crop(CROP)
    if slug == "theic":                  # 초록 플로팅 위젯(고객사 대표번호) 블러
        blur_box(im, (548, 262, 622, 396), radius=12, tint=(58, 74, 80, 0.20))
    im.resize((894, 587), Image.LANCZOS).save(A/f"case_{slug}.jpg", quality=92)

# 2) 고재가구소아 반응형 정지 화면 (hero png)
Image.open(R/"hero/gojegagusoa.png").convert("RGB").resize((902, 643), Image.LANCZOS).save(A/"what_gojegagusoa.jpg", quality=92)

# 3) 대표 사진: 크롭 + 흑백
ph = Image.open(R/"장영주.jpg").convert("RGB").crop((40, 300, 810, 1019))
ImageOps.grayscale(ph).convert("RGB").save(A/"rep_jang.jpg", quality=92)

# 4) 수정 시연 프레임: 필요한 프레임만, 크롭(y74~428) + 설명문 블러 + 패널 하단 흰 페이드
USE = list(range(18,22)) + [30,31] + list(range(53,71)) + list(range(165,171)) + list(range(225,249))
with tempfile.TemporaryDirectory() as td:
    subprocess.run(["ffmpeg","-v","error","-i",str(R/"demo/ondam-edit.mp4"),"-vsync","0",f"{td}/f%03d.png"], check=True)
    od = A/"ondam"; od.mkdir(exist_ok=True)
    for n in USE:
        im = Image.open(f"{td}/f{n:03d}.png").convert("RGB").crop((0, 74, 960, 428))   # 960x354
        blur_box(im, (0, 242, 224, 290), radius=8, tint=(255, 255, 255, 0.15))        # 사이트 설명문('20년' 포함)
        # 패널 하단 잘린 줄 → 흰색 페이드
        g = Image.new("L", (200, 24)); dr = ImageDraw.Draw(g)
        for y in range(24): dr.line([(0,y),(200,y)], fill=int(255*y/23))
        im.paste(Image.new("RGB",(200,24),(255,255,255)), (760, 330), g)
        im.save(od/f"f{n:03d}.jpg", quality=92)
print("ok", len(USE), "frames")
