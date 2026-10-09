#!/usr/bin/env python3
"""유웹디 견적서 HTML 생성기.

사용법:  python3 build.py 견적데이터.json [--out 출력폴더]
- 기본값.json (유웹디 정보·계좌·호스팅 요금·비고)에 견적데이터.json 을 덮어써서 만듭니다.
- 결과: <출력폴더>/견적서_<고객명>.html  (폰트·로고 내장, 외부 파일 필요 없음)
"""
import argparse, base64, html, json, sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAX_ITEMS = 6


def won(n):
    return f"{int(n):,}"


def esc(s):
    return html.escape(str(s), quote=False)


def deep_merge(base, over):
    out = dict(base)
    for k, v in over.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def font_css():
    parts = []
    for w in (400, 600, 700):
        b = base64.b64encode((HERE / "fonts" / f"Pretendard-{w}.subset.woff2").read_bytes()).decode()
        parts.append(
            f'@font-face{{font-family:"Pretendard";font-weight:{w};font-style:normal;font-display:block;'
            f'src:url(data:font/woff2;base64,{b}) format("woff2")}}'
        )
    return "\n".join(parts)


def build(d):
    items = d["items"]
    if not 1 <= len(items) <= MAX_ITEMS:
        sys.exit(f"항목은 1~{MAX_ITEMS}개만 한 장(1페이지)에 들어갑니다. 현재 {len(items)}개")
    supply = sum(int(i["amount"]) for i in items)
    vat = int(round(supply * float(d["vatRate"]) + 1e-9))
    total = supply + vat
    sup = d["supplier"]
    cl = d["client"]
    sample = bool(d.get("sample"))
    quote_no = d.get("quoteNo") or f"YWD-{date.today():%Y%m%d}-001"
    if not sample and "SAMPLE" in quote_no.upper():
        print(f"경고: 실제 견적서(sample=false)인데 견적번호에 SAMPLE 이 들어 있습니다 → {quote_no}", file=sys.stderr)
    logo_path = (HERE / d["logo"]).resolve()
    logo = base64.b64encode(logo_path.read_bytes()).decode()
    brand = f'<div class="brand"><img src="data:image/png;base64,{logo}" alt="유웹디 로고"><b>{esc(sup["name"])}</b></div>'
    badge = '<div class="sample">SAMPLE</div>' if sample else ""
    foot_r = lambda n: f'{"본 문서는 샘플입니다. · " if sample else ""}{n} / 2'
    foot = lambda n: (f'<div class="pgfoot"><span>{esc(sup["name"])} · {esc(sup["email"])}</span>'
                      f'<span>{foot_r(n)}</span></div>')

    rows = "\n".join(
        f'      <tr><td>{n}</td><td>{esc(i["title"])}<small>{esc(i.get("sub",""))}</small></td>'
        f'<td class="num">{esc(i.get("qty","1식"))}</td><td class="num">{won(i["amount"])}</td></tr>'
        for n, i in enumerate(items, 1))
    compact = ' class="compact"' if len(items) >= 6 else ""

    p1 = f'''<section class="page" id="p1">
  {badge}
  <header>
    {brand}
    <h1>견 적 서</h1>
    <p>{esc(d.get("subtitle","홈페이지 제작 견적"))} · 견적번호 {esc(quote_no)}</p>
  </header>

  <section class="meta">
    <div class="box">
      <h2>수신</h2>
      <dl>
        <dt>상호</dt><dd><strong>{esc(cl["name"])}</strong> 귀하</dd>
        <dt>프로젝트</dt><dd>{esc(cl["project"])}</dd>
        <dt>견적일</dt><dd>{esc(d["date"])}</dd>
        <dt>유효기간</dt><dd>{esc(d["validity"])}</dd>
      </dl>
    </div>
    <div class="box">
      <h2>공급자</h2>
      <dl>
        <dt>상호</dt><dd><strong>{esc(sup["name"])}</strong></dd>
        <dt>대표</dt><dd>{esc(sup["rep"])}</dd>
        <dt>이메일</dt><dd>{esc(sup["email"])}</dd>
        <dt>사업자번호</dt><dd>{esc(sup["bizNo"])}</dd>
      </dl>
    </div>
  </section>

  <div class="total">
    <span>총 견적금액 (VAT 포함)</span>
    <strong>₩{won(total)}<small>공급가액 {won(supply)} + 부가세 {won(vat)}</small></strong>
  </div>

  <table{compact}>
    <thead><tr><th style="width:5%">No</th><th>항목</th><th class="num" style="width:10%">수량</th><th class="num" style="width:20%">금액(원)</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>

  <div class="sum">
    <div><span>공급가액</span><span class="num">{won(supply)}원</span></div>
    <div><span>부가세 ({int(float(d["vatRate"])*100)}%)</span><span class="num">{won(vat)}원</span></div>
    <div class="grand"><span>합계</span><span class="num">{won(total)}원</span></div>
  </div>

  {foot(1)}
</section>'''

    # ---- 2페이지 ----
    blocks = []
    h = d.get("hosting")
    if h:
        plans = "\n".join(
            f'''      <div class="card">
        <h4>{esc(p["name"])}</h4>
''' + "\n".join(
                f'        <label class="opt"><input type="checkbox"><span>{esc(o[0])}</span><b>{esc(o[1])}</b></label>'
                for o in p["options"]) + "\n      </div>" for p in h["plans"])
        common = "\n".join(f'      <div class="row"><span>{esc(r[0])}</span><b>{esc(r[1])}</b></div>' for r in h["common"])
        blocks.append(f'''  <section class="host" style="margin-top:0">
    <h3>{esc(h["title"])}</h3>
    <p>{esc(h["intro"])}</p>
    <div class="plat">
{plans}
    </div>
    <div class="common">
      <h4>{esc(h["commonTitle"])}</h4>
{common}
    </div>
    <p class="fine">{esc(h["fine"])}</p>
  </section>''')
    a = d.get("account")
    if a:
        blocks.append(f'''  <section class="common" style="margin-top:{28 if h else 0}px">
    <h4>입금 계좌</h4>
    <div class="row"><span>은행</span><b>{esc(a["bank"])}</b></div>
    <div class="row"><span>계좌번호</span><b>{esc(a["number"])}</b></div>
    <div class="row"><span>예금주</span><b>{esc(a["holder"])}</b></div>
  </section>''')
    def fill(n):
        n = n.replace('{total}', won(total)).replace('{supply}', won(supply)).replace('{vat}', won(vat))
        return n if h else n.replace("(위 안내 참조)", "")
    notes = "\n".join(f"      <li>{fill(n)}</li>" for n in d["notes"])
    blocks.append(f'''  <section class="notes">
    <h3>비고</h3>
    <ul>
{notes}
    </ul>
  </section>''')

    p2 = f'''<section class="page" id="p2">
  {badge}
  <div class="p2top">
    {brand}
    <p class="ref"{'' if sample else ' style="padding-right:0"'}>견적번호 {esc(quote_no)} · {esc(cl["name"])}</p>
  </div>

''' + "\n\n".join(blocks) + f"\n\n  {foot(2)}\n</section>"

    css = (HERE / "template.css").read_text(encoding="utf-8").replace("/*FONTS*/", font_css())
    printbtn = '<button class="printbtn" type="button" onclick="window.print()">인쇄 / PDF 저장</button>'
    doc = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(cl["name"])} 견적서{" (샘플)" if sample else ""}</title>
<style>
{css}
</style>
</head>
<body>
<main>

{p1}

{p2}

</main>
{printbtn}
</body>
</html>
'''
    return doc, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out", default=str(HERE / "output"))
    ap.add_argument("--defaults", default=str(HERE / "기본값.json"))
    a = ap.parse_args()
    d = deep_merge(json.loads(Path(a.defaults).read_text(encoding="utf-8")),
                   json.loads(Path(a.data).read_text(encoding="utf-8")))
    for k in ("hosting", "account"):
        if d.get(k) is False:
            d[k] = None
    doc, total = build(d)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    f = out / f'견적서_{d["client"]["name"]}.html'
    f.write_text(doc, encoding="utf-8")
    print(f"{f}  (합계 {won(total)}원)")


if __name__ == "__main__":
    main()
