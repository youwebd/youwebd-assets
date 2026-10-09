/* cards.json → 당근마켓 이미지 카드(1080x1080 JPG)
 * 사용법: NODE_PATH=/opt/node22/lib/node_modules node render_cards.js
 * 필요: playwright(크롬). 글꼴은 견적서_생성기/fonts 의 Pretendard 부분 글꼴을 씁니다.
 * 카드 문구는 cards.json 에서만 고칩니다. 점 항목이 「라벨: 값」 모양이면 안내 줄, 아니면 번호 줄로 그립니다. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const HERE = __dirname;
const OUT = path.join(HERE, '..', '이미지');
const BRAND = path.join(HERE, '..', '..', '..', '..');           // 유웹디_브랜딩
const FONT = n => 'file://' + encodeURI(path.join(BRAND, '견적서_생성기', 'fonts', `Pretendard-${n}.subset.woff2`));
const LOGO = 'file://' + encodeURI(path.join(BRAND, 'youwebd-logo.png'));
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function headlineHTML(c) {
  const lines = c.headline.split('\n');
  return lines.map((ln, i) => {
    let h = esc(ln);
    for (const w of (c.highlight || [])) h = h.split(esc(w)).join(`<em>${esc(w)}</em>`);
    return `<span class="hl${lines.length > 1 && i === 0 ? ' dim' : ''}">${h}</span>`;
  }).join('');
}
function pointsHTML(c) {
  return c.points.map((p, i) => {
    const m = p.match(/^(.{1,6}?)\s*[:：]\s*(.+)$/);
    if (m) return `<div class="row fact"><b class="lab">${esc(m[1])}</b><span class="val">${esc(m[2])}</span></div>`;
    return `<div class="row"><i class="no">${i + 1}</i><span class="val">${esc(p)}</span></div>`;
  }).join('');
}
function html(c) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:P;font-weight:400;src:url(${FONT(400)}) format("woff2")}
@font-face{font-family:P;font-weight:600;src:url(${FONT(600)}) format("woff2")}
@font-face{font-family:P;font-weight:700;src:url(${FONT(700)}) format("woff2")}
*{box-sizing:border-box;margin:0}
body{width:1080px;height:1080px;background:#fff;font-family:P,"Apple SD Gothic Neo",sans-serif;color:#16181d;-webkit-font-smoothing:antialiased;position:relative;overflow:hidden}
.wrap{position:absolute;left:72px;right:72px;top:64px;bottom:64px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;gap:16px}
.top img{width:64px;height:64px}
.top .nm{font-size:34px;font-weight:700;letter-spacing:-.02em}
.top .kick{margin-left:auto;border:3px solid #c82828;color:#c82828;border-radius:999px;padding:8px 24px;font-size:28px;font-weight:700}
.main{margin-top:52px}
h1{font-weight:700;font-size:70px;line-height:1.2;letter-spacing:-.035em;display:flex;flex-direction:column}
h1 .dim{color:#5b6270}
h1 em{font-style:normal;color:#c82828;text-decoration:underline;text-decoration-thickness:7px;text-underline-offset:9px}
.pts{margin-top:46px;display:flex;flex-direction:column;gap:20px}
.row{background:#f6f5f7;border-radius:30px;padding:24px 32px 24px 26px;display:flex;align-items:center;gap:26px;position:relative}
.row .no{flex:none;width:64px;height:64px;border-radius:50%;background:#c82828;color:#fff;font-style:normal;font-weight:700;font-size:34px;display:flex;align-items:center;justify-content:center}
.row .val{font-size:38px;font-weight:700;line-height:1.3;letter-spacing:-.025em}
.row.fact{gap:24px;padding-left:34px}
.row.fact .lab{flex:none;width:128px;color:#c82828;font-size:32px;font-weight:700;letter-spacing:-.02em}
.foot{position:absolute;left:0;right:0;bottom:0;background:#16181d;color:#fff;border-radius:30px;padding:26px 34px;font-size:34px;font-weight:700;letter-spacing:-.02em;display:flex;align-items:center;gap:18px}
.foot:before{content:"";flex:none;width:16px;height:16px;border-radius:50%;background:#ff5a5a}
</style></head><body><div class="wrap">
<div class="top"><img src="${LOGO}"><span class="nm">유웹디</span>${c.kicker ? `<span class="kick">${esc(c.kicker)}</span>` : ''}</div>
<div class="main"><h1>${headlineHTML(c)}</h1><div class="pts">${pointsHTML(c)}</div></div>
${c.footer ? `<div class="foot">${esc(c.footer)}</div>` : ''}
</div></body></html>`;
}

(async () => {
  const cards = JSON.parse(fs.readFileSync(path.join(HERE, 'cards.json'), 'utf8'));
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1080 } });
  let bad = 0;
  for (const c of cards) {
    const tmp = path.join(HERE, `.tmp_${c.id}.html`);
    fs.writeFileSync(tmp, html(c));
    await p.goto('file://' + encodeURI(tmp));
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(150);
    const m = await p.evaluate(() => {
      const main = document.querySelector('.main').getBoundingClientRect();
      const foot = document.querySelector('.foot');
      const lim = foot ? foot.getBoundingClientRect().top : 1080 - 64;
      return { bottom: Math.round(main.bottom), limit: Math.round(lim) };
    });
    if (m.bottom > m.limit - 24) { console.error(`넘침: ${c.id} 본문 아래 ${m.bottom}px > 허용 ${m.limit - 24}px`); bad++; }
    const file = path.join(OUT, `${c.id}_${c.file}.jpg`);
    await p.screenshot({ path: file, type: 'jpeg', quality: 93 });
    fs.rmSync(tmp, { force: true });
    console.log('저장', path.relative(HERE, file), `(본문 아래 ${m.bottom}/${m.limit - 24})`);
  }
  await b.close();
  if (bad) process.exit(1);
})();
