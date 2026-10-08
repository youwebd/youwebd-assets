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

def desc_placeholder(im, box=(0, 242, 224, 290)):
    """사이트 설명문(숫자 포함)을 지우고 반투명 흰 줄 두 개로 대체"""
    x0, y0, x1, y1 = box
    pad = 18
    big = im.crop((max(0, x0 - pad), y0 - pad, x1 + pad, y1 + pad)).filter(ImageFilter.GaussianBlur(26))
    m = Image.new("L", big.size, 0); ImageDraw.Draw(m).rounded_rectangle((pad // 2, pad // 2, big.size[0] - pad // 2, big.size[1] - pad // 2), 12, fill=255)
    im.paste(big, (max(0, x0 - pad), y0 - pad), m.filter(ImageFilter.GaussianBlur(7)))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle((x0 + 8, y0 + 12, x0 + 196, y0 + 21), 5, fill=(255, 255, 255, 120))
    d.rounded_rectangle((x0 + 8, y0 + 29, x0 + 146, y0 + 38), 5, fill=(255, 255, 255, 120))
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))

def pink_to_blue(im, box=(0, 296, 150, 346), blue=(81, 98, 169)):
    """사진 단계 프레임의 분홍 버튼을 문구 단계와 같은 파랑으로"""
    reg = im.crop(box); px = reg.load(); bl = 0.299*blue[0] + 0.587*blue[1] + 0.114*blue[2]
    for y in range(reg.size[1]):
        for x in range(reg.size[0]):
            r, g, b = px[x, y]
            if r - g > 40 and r > 100:
                w = min(1.0, (r - g - 40) / 50); lum = 0.299*r + 0.587*g + 0.114*b; k = lum / 119.0
                tgt = [min(255, c * k * (119.0 / bl) * (bl / 119.0)) for c in blue]
                px[x, y] = tuple(int(round(c*(1-w) + t*w)) for c, t in zip((r, g, b), tgt))
    im.paste(reg, box[:2])

# 1) 사례 카드: 고객사 5곳, PC·모바일 목업(메인 화면 영상의 깨끗한 프레임)
def hero_frame(slug, t=None):
    if t is None:
        return Image.open(R/f"hero/{slug}.png").convert("RGB")
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",str(R/f"hero/{slug}.mp4"),"-frames:v","1",f"{td}/f.png"], check=True)
        return Image.open(f"{td}/f.png").convert("RGB")
for slug, t in [("theic",None),("gojegagusoa",None),("shutterplay",None),("mbcmodel",None),("uberhouse",None)]:
    hero_frame(slug, t).resize((1032, 735), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2)).save(A/f"case_{slug}.jpg", quality=93)

# 2) '무엇을' 장면: 서경파츠 반응형 화면
hero_frame("seokyung").resize((902, 643), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2)).save(A/"what_seokyung.jpg", quality=92)

# 3) '누가' 장면: 신공간디자인연구소 메인 → 스크롤 영상 프레임
sd = A/"sgg"; sd.mkdir(exist_ok=True)
for f in sd.glob("*.jpg"): f.unlink()
subprocess.run(["ffmpeg","-v","error","-i",str(R/"hero/shingonggan.mp4"),"-vsync","0","-q:v","3",str(sd/"f%03d.jpg")], check=True)

# 이전 버전 자산 정리
for old in ["case_aline.jpg","case_luxenova.jpg","case_seokyung.jpg","what_gojegagusoa.jpg","rep_jang.jpg"]:
    (A/old).unlink(missing_ok=True)

# 4) 수정 시연 프레임: 필요한 프레임만, 크롭(y74~428) + 설명문 블러 + 패널 하단 흰 페이드
USE = list(range(18,22)) + [30,31] + list(range(53,71)) + list(range(165,171)) + list(range(225,249))
with tempfile.TemporaryDirectory() as td:
    subprocess.run(["ffmpeg","-v","error","-i",str(R/"demo/ondam-edit.mp4"),"-vsync","0",f"{td}/f%03d.png"], check=True)
    od = A/"ondam"; od.mkdir(exist_ok=True)
    for n in USE:
        im = Image.open(f"{td}/f{n:03d}.png").convert("RGB").crop((0, 74, 960, 428))   # 960x354
        desc_placeholder(im)                                                           # 사이트 설명문('20년' 포함) 제거
        if n >= 165: pink_to_blue(im)                                                  # 사진 단계 버튼 색을 문구 단계와 맞춤
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
        desc_placeholder(th); pink_to_blue(th)
        th.resize((336, 158), Image.LANCZOS).save(A/f"lens_{name}.jpg", quality=92)
print("ok", len(USE), "frames")
