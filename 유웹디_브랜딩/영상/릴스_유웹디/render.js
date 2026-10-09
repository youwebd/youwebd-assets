/* reels.html → MP4 (프레임 단위 캡처 + ffmpeg)
 * 사용법: node render.js [출력.mp4] [fps=30]
 * 기본 저장 위치: 유웹디_브랜딩/마케팅/인스타그램/릴스_대표님이직접운영하는웹사이트/ (채널별 폴더)
 * 필요: playwright, ffmpeg. 크롬 경로는 CHROME_PATH 로 지정 가능. 자산은 먼저 python3 prep_assets.py */
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const CHANNEL_DIR = path.join(__dirname, '..', '..', '마케팅', '인스타그램', '릴스_대표님이직접운영하는웹사이트');
const out = path.resolve(process.argv[2] || path.join(CHANNEL_DIR, '유웹디_릴스_대표님이직접운영하는웹사이트_9x16.mp4'));
const FPS = +process.argv[3] || 30;
const url = 'file://' + encodeURI(path.join(__dirname, 'reels.html'));
(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'reels-'));
  const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => { console.error('페이지 오류:', e.message); process.exit(1); });
  await p.goto(url); await p.waitForFunction('window.__ready===true', null, { timeout: 30000 });
  const N = Math.round(await p.evaluate(() => window.DUR) * FPS);
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    await p.evaluate(t => seek(t), i / FPS);
    await p.screenshot({ path: path.join(dir, `f_${String(i).padStart(5, '0')}.png`) });
    if (i % 150 === 149) console.log(`${i + 1}/${N} 프레임 (${((Date.now() - t0) / 1000).toFixed(0)}초)`);
  }
  await b.close();
  fs.mkdirSync(path.dirname(out), { recursive: true });
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(dir, 'f_%05d.png'),
    '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', '-an', out], { stdio: 'inherit' });
  fs.rmSync(dir, { recursive: true, force: true });
  console.log('완료:', out, N, '프레임');
})();
