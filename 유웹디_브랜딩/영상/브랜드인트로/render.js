/* intro.html → MP4 (프레임 단위 캡처 + ffmpeg)
 * 사용법: node render.js [출력.mp4] [fps=30] [초=15]
 * 필요: playwright, ffmpeg.  크롬 경로는 CHROME_PATH 로 지정 가능 */
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const out = path.resolve(process.argv[2] || path.join(__dirname, '유웹디_브랜드인트로_9x16_15s.mp4'));
const FPS = +process.argv[3] || 30, SEC = +process.argv[4] || 15, N = FPS * SEC;
const url = 'file://' + encodeURI(path.join(__dirname, 'intro.html'));
(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'intro-'));
  const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => { console.error('페이지 오류:', e.message); process.exit(1); });
  await p.goto(url); await p.waitForFunction('window.__ready===true', null, { timeout: 20000 });
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    await p.evaluate(t => seek(t), i / FPS);
    await p.screenshot({ path: path.join(dir, `f_${String(i).padStart(4, '0')}.png`) });
    if (i % 60 === 59) console.log(`${i + 1}/${N} 프레임 (${((Date.now() - t0) / 1000).toFixed(0)}초)`);
  }
  await b.close();
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(dir, 'f_%04d.png'),
    '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '14',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', '-an', out], { stdio: 'inherit' });
  fs.rmSync(dir, { recursive: true, force: true });
  console.log('완료:', out);
})();
