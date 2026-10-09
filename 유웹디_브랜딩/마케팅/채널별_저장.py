#!/usr/bin/env python3
"""채널별 폴더 자동 정리·검사 (인스타그램·스레드·네이버 블로그·당근마켓)

사용법 (유웹디_브랜딩/마케팅/ 에서):
  python3 채널별_저장.py            # 블로그 이미지를 영상에서 다시 뽑고(영상이 바뀌었을 때 자동 반영), 모든 채널 글을 검사
  python3 채널별_저장.py --render   # 영상·커버부터 다시 만든 뒤 위 작업 (node, playwright, ffmpeg 필요)
  python3 채널별_저장.py --check    # 검사만

하는 일
  1) --render: 영상/릴스_유웹디 의 render.js → 인스타그램 폴더에 mp4, cover.js → 같은 폴더에 커버 PNG
  2) 인스타그램 폴더의 mp4 에서 블로그 이미지(IMG-01~15)를 다시 뽑고 사례 모아보기(IMG-16)를 만들어 네이버블로그/…/이미지 에 저장,
     당근마켓 소식에 쓰는 이미지는 같은 파일을 당근마켓/…/이미지 로 복사
  3) 모든 채널 글 검사: 금지어·미검증 숫자, 글자수(스레드 500자, 캡션 2,200자, 블로그 제목 100자·태그 30개),
     블로그 본문 이미지 파일 존재 여부, 영상 규격
기준은 공통/말해도_되는_사실과_규칙.md 입니다. 문제가 있으면 종료 코드 1 로 끝납니다.
"""
import re, subprocess, sys, hashlib, tempfile, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent                      # 유웹디_브랜딩/마케팅
REELS = ROOT.parent / "영상" / "릴스_유웹디"                 # 영상 소스(reels.html, render.js, cover.js)
IG = ROOT / "인스타그램" / "릴스_대표님이직접운영하는웹사이트"
TH = ROOT / "스레드" / "릴스_대표님이직접운영하는웹사이트"
NB = ROOT / "네이버블로그" / "소상공인홈페이지제작_업체고를때확인할점"
DG = ROOT / "당근마켓" / "동네사장님_홈페이지문구수정"
MP4 = IG / "유웹디_릴스_대표님이직접운영하는웹사이트_9x16.mp4"
IMG_DIR = NB / "이미지"
FPS = 30

# 블로그 이미지: (파일 이름, 영상 속 시각[초]). 장면 시간이 바뀌면 여기만 고칩니다.
FRAMES = [
    ("IMG-01_훅_맡기고_기다림", 5.28), ("IMG-02_코드_어디를_고치죠", 1.62), ("IMG-03_수정예시_빌더_줌", 7.20),
    ("IMG-04_수정예시_사이트_바로반영", 8.10), ("IMG-05_수정예시_배경사진_교체", 9.45), ("IMG-06_1인_웹사이트_제작_스튜디오", 11.80),
    ("IMG-07_이런_대표님께_맞습니다", 15.40), ("IMG-08_반응형_홈페이지", 17.90), ("IMG-09_오픈_뒤에도_혼자_두지_않습니다", 27.60),
    ("IMG-10_사례_기업_THEIC", 29.50), ("IMG-11_사례_쇼핑몰_고재가구소아", 31.00), ("IMG-12_사례_스튜디오_셔터플레이", 32.50),
    ("IMG-13_사례_아카데미_MBC모델센터", 34.10), ("IMG-14_사례_건축인테리어_우버하우스", 35.80), ("IMG-15_상담_원해요", 39.50),
]
CROP = (0, 160, 1080, 1560)          # 1080x1920 프레임에서 내용이 있는 부분(1080x1400)
BANNED = ["압도적", "완벽한", "무조건", "클릭 한 번으로", "코딩 없이", "최고", "1등", "국내 유일", "열 곳", "20년"]


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"실패: {' '.join(map(str, cmd))}\n{r.stderr[-800:]}")
    return r.stdout


def render():
    for js in ("render.js", "cover.js"):
        print(f"[렌더] node {js}")
        sh(["node", js], cwd=REELS)


def blog_images():
    if not MP4.exists():
        print("[이미지] 영상이 없어 건너뜀:", MP4.name); return
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    changed = 0
    with tempfile.TemporaryDirectory() as td:
        for name, t in FRAMES:
            n = round(t * FPS)
            png = Path(td) / "f.jpg"
            sh(["ffmpeg", "-v", "error", "-y", "-i", str(MP4), "-vf", f"select='eq(n\\,{n})'", "-vsync", "0", "-q:v", "2", str(png)])
            im = Image.open(png).convert("RGB")
            assert im.size == (1080, 1920), im.size
            out = IMG_DIR / f"{name}.jpg"
            before = hashlib.md5(out.read_bytes()).hexdigest() if out.exists() else None
            im.crop(CROP).save(out, quality=92, optimize=True)
            if hashlib.md5(out.read_bytes()).hexdigest() != before:
                changed += 1
    collage()
    print(f"[이미지] {len(FRAMES)}장 확인, {changed}장 갱신 + 사례 모아보기(IMG-16)")
    daangn_images()


def daangn_images():
    md = DG / "당근마켓_소식_광고문구.md"
    if not md.exists():
        return
    ids = sorted(set(re.findall(r"IMG-\d+", " ".join(re.findall(r"^사진\(순서대로\): (.*)$", md.read_text(encoding="utf-8"), flags=re.M)))))
    out = DG / "이미지"
    out.mkdir(exist_ok=True)
    n = 0
    for i in ids:
        src = next(IMG_DIR.glob(i + "_*.jpg"), None)
        if src and (not (out / src.name).exists() or (out / src.name).read_bytes() != src.read_bytes()):
            shutil.copy2(src, out / src.name); n += 1
    print(f"[당근마켓 이미지] {len(ids)}장 확인, {n}장 복사")


def collage():
    cases = sorted(IMG_DIR.glob("IMG-1[0-4]_*.jpg"))
    if len(cases) != 5:
        return
    W, M, G = 1500, 42, 24
    TW = (W - 2 * M - 2 * G) // 3
    box = (60, 340, 1020, 1200)
    TH_ = round(TW * (box[3] - box[1]) / (box[2] - box[0]))
    top = 130
    sheet = Image.new("RGB", (W, top + TH_ * 2 + G + M), (243, 242, 244))
    d = ImageDraw.Draw(sheet)
    font = None
    for p in ("/root/.fonts/Pretendard-Bold.otf", "/usr/share/fonts/truetype/Pretendard-Bold.otf"):
        if Path(p).exists():
            font = ImageFont.truetype(p, 54); break
    title = "유웹디가 만든 고객사 홈페이지"
    if font:
        d.text(((W - d.textlength(title, font=font)) / 2, 38), title, font=font, fill=(22, 24, 29))

    def tile(p, x, y):
        sheet.paste(Image.open(p).convert("RGB").crop(box).resize((TW, TH_), Image.LANCZOS), (x, y))
    for i, p in enumerate(cases[:3]): tile(p, M + i * (TW + G), top)
    x2 = (W - (2 * TW + G)) // 2
    for i, p in enumerate(cases[3:]): tile(p, x2 + i * (TW + G), top + TH_ + G)
    sheet.save(IMG_DIR / "IMG-16_사례_모아보기.jpg", quality=92, optimize=True)


# ---------------- 검사 ----------------
problems, notes = [], []


def bad(msg): problems.append(msg)


def scan_banned(path, text):
    for w in BANNED:
        if w in text:
            bad(f"{path.relative_to(ROOT)}: 금지어/미검증 표현 「{w}」")


def text_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in (".txt", ".md") and "공통" not in p.parts and p.name != "README.md":
            yield p


def check_instagram():
    cap = IG / "게시글_캡션.txt"
    if cap.exists():
        t = cap.read_text(encoding="utf-8")
        if len(t) > 2200: bad(f"인스타그램 캡션 {len(t)}자 (2,200자 초과)")
        if len(re.findall(r"#\S+", t)) > 30: bad("인스타그램 해시태그 30개 초과")
        n_tags = len(re.findall(r"#\S+", t))
        notes.append(f"인스타그램 캡션 {len(t)}자, 해시태그 {n_tags}개")
    else:
        bad("인스타그램 캡션 파일 없음")
    if MP4.exists():
        out = sh(["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration", "-of", "default=nw=1", str(MP4)])
        w = int(re.search(r"width=(\d+)", out).group(1)); h = int(re.search(r"height=(\d+)", out).group(1))
        dur = float(re.search(r"duration=([\d.]+)", out).group(1))
        if (w, h) != (1080, 1920): bad(f"영상 규격 {w}x{h} (9:16 1080x1920 아님)")
        if not 3 <= dur <= 90: bad(f"릴스 길이 {dur:.1f}초 (3~90초 아님)")
        notes.append(f"영상 {w}x{h}, {dur:.1f}초")
    else:
        bad("영상(mp4) 없음 — python3 채널별_저장.py --render")
    if not list(IG.glob("릴스_커버_*초.png")): bad("릴스 커버 PNG 없음")


def check_threads():
    f = TH / "스레드_게시글.txt"
    if not f.exists():
        bad("스레드 글 없음"); return
    t = f.read_text(encoding="utf-8")
    body = t.split("────────────────────────", 1)[1]
    main, single = body.split("════════════════════════")
    posts = [p.strip() for p in main.split("────────────────────────") if p.strip()]
    posts.append(single.strip())
    for i, p in enumerate(posts, 1):
        txt = "\n".join(p.split("\n")[1:]).strip()
        if len(txt) > 500: bad(f"스레드 {i}번 글 {len(txt)}자 (500자 초과)")
        if len(re.findall(r"#\S+", txt)) > 1: bad(f"스레드 {i}번 글 주제 태그 1개 초과")
    notes.append(f"스레드 글 {len(posts)}개(연결 글 + 한 편 버전) 모두 500자 이내")


def check_blog():
    f = NB / "네이버블로그_게시글.md"
    if not f.exists():
        bad("네이버 블로그 글 없음"); return
    md = f.read_text(encoding="utf-8")
    title = re.search(r"^\| 제목 \| (.*) \|$", md, flags=re.M).group(1)
    tags = re.search(r"^\| 태그\(\d+개\) \| (.*) \|$", md, flags=re.M).group(1).split()
    body = md.split("<!-- 본문 시작 -->")[1].split("<!-- 본문 끝 -->")[0]
    if len(title) > 100: bad(f"블로그 제목 {len(title)}자 (100자 초과)")
    if len(tags) > 30: bad("블로그 태그 30개 초과")
    if any(" " in x for x in tags): bad("블로그 태그에 공백")
    plain = re.sub(r"!\[[^\]]*\]\(IMG-\d+\)", "", body).strip()
    for i in sorted(set(re.findall(r"\]\((IMG-\d+)\)", body))):
        if not list(IMG_DIR.glob(i + "_*.jpg")): bad(f"블로그 본문 이미지 {i} 파일 없음")
    n_img = len(set(re.findall(r"IMG-\d+", body)))
    notes.append(f"블로그 제목 {len(title)}자, 본문 {len(plain)}자, 태그 {len(tags)}개, 이미지 {n_img}장 사용")


def check_daangn():
    md = DG / "당근마켓_소식_광고문구.md"
    if not md.exists():
        bad("당근마켓 글 없음"); return
    t = md.read_text(encoding="utf-8")
    blocks = re.findall(r"```\n(.*?)\n```", t, flags=re.S)
    for i, b in enumerate(blocks, 1):
        if len(b) > 500: bad(f"당근 소식 {i}번 {len(b)}자 (500자 초과)")
    titles = re.findall(r"^제목: (.*)$", t, flags=re.M); bodies = re.findall(r"^본문: (.*)$", t, flags=re.M)
    for i, (a, b) in enumerate(zip(titles, bodies), 1):
        if len(a) > 20: bad(f"당근 광고 후보 {i} 제목 {len(a)}자 (20자 초과)")
        if len(b) > 60: bad(f"당근 광고 후보 {i} 본문 {len(b)}자 (60자 초과)")
    for i in sorted(set(re.findall(r"IMG-\d+", " ".join(re.findall(r"^사진\(순서대로\): (.*)$", t, flags=re.M))))):
        if not list((DG / "이미지").glob(i + "_*.jpg")): bad(f"당근 소식 이미지 {i} 파일 없음")
    notes.append(f"당근마켓 소식 {len(blocks)}편({', '.join(str(len(b)) + '자' for b in blocks)}), 광고 문구 {len(titles)}개")


def check():
    check_instagram(); check_threads(); check_blog(); check_daangn()
    for p in text_files():
        scan_banned(p, p.read_text(encoding="utf-8"))
    print("\n[검사 결과]")
    for n in notes: print("  ·", n)
    if problems:
        print("\n문제", len(problems), "건")
        for x in problems: print("  ✗", x)
        return 1
    print("  문제 없음")
    return 0


if __name__ == "__main__":
    args = set(sys.argv[1:])
    if "--check" not in args:
        if "--render" in args: render()
        blog_images()
    sys.exit(check())
