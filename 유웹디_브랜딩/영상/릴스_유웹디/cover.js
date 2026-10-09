/* reels.html 의 한 장면 → 릴스 커버 PNG (무손실)
 * 사용법: node cover.js [초=5.28] [출력.png]
 * 기본 저장 위치: 유웹디_브랜딩/마케팅/인스타그램/릴스_대표님이직접운영하는웹사이트/릴스_커버_<초>초.png
 * 5.28초 = 훅 장면(「업체에 맡기고 며칠 기다리셨나요?」+ 답장 기다린 지 3일째). 장면 시간이 바뀌면 이 값도 바꿉니다. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const T = +process.argv[2] || 5.28;
const out = path.resolve(process.argv[3] || path.join(__dirname, '..', '..', '마케팅', '인스타그램', '릴스_대표님이직접운영하는웹사이트', `릴스_커버_${T}초.png`));
const url = 'file://' + encodeURI(path.join(__dirname, 'reels.html'));
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => { console.error('페이지 오류:', e.message); process.exit(1); });
  await p.goto(url); await p.waitForFunction('window.__ready===true', null, { timeout: 30000 });
  await p.evaluate(t => seek(t), T);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await p.screenshot({ path: out });
  await b.close();
  console.log('완료:', out);
})();
