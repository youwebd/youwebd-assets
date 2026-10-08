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
CROP = (170, 90, 840, 508)               # 670x418 (받침대 조각 제외)
for slug, ext in [("theic","jpg"),("uberhouse","jpg"),("seokyung","jpg"),("aline","jpg"),("luxenova","jpg")]:
    im = Image.open(R/f"kit/{slug}.{ext}").convert("RGB").crop(CROP)
    if slug == "theic":                  # 초록 플로팅 위젯(고객사 대표번호): 블러 + 어두운 틴트 + 페더
        box = (540, 254, 630, 404)
        reg = im.crop(box).filter(ImageFilter.GaussianBlur(14))
        reg = Image.blend(reg, Image.new("RGB", reg.size, (14, 38, 46)), 0.62)
        m = Image.new("L", reg.size, 0); ImageDraw.Draw(m).rounded_rectangle((8, 8, reg.size[0]-9, reg.size[1]-9), 14, fill=255)
        im.paste(reg, box[:2], m.filter(ImageFilter.GaussianBlur(5)))
    im.resize((906, 565), Image.LANCZOS).save(A/f"case_{slug}.jpg", quality=92)

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
    # 깜빡임 보정: 둘째 줄·블러 패치·버튼 영역(0,184,330,354)을 안정된 프레임에서 복사
    REG = (0, 184, 330, 354)
    for tgt, src in [(18,21),(19,21),(20,21),(30,21),(31,21),(53,54)]:
        t = Image.open(od/f"f{tgt:03d}.jpg"); s_ = Image.open(od/f"f{src:03d}.jpg")
        t.paste(s_.crop(REG), REG[:2]); t.save(od/f"f{tgt:03d}.jpg", quality=92)
    # 렌즈용 썸네일: 바뀌기 전/후 사이트 히어로 (사이트 영역 0~755)
    for name, n in [("old", 168), ("new", 248)]:
        th = Image.open(f"{td}/f{n:03d}.png").convert("RGB").crop((0, 74, 755, 428))
        blur_box(th, (0, 242, 224, 290), radius=8, tint=(255, 255, 255, 0.15))
        th.resize((336, 158), Image.LANCZOS).save(A/f"lens_{name}.jpg", quality=92)
print("ok", len(USE), "frames")
