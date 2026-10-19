// P21 아트 A — 실기 전장 캡처(헤드리스 Chromium). 사용: NODE_PATH=$(npm root -g) node capture.cjs <baseUrl> <outDir>
// 게임 코드는 읽지 않는다 — 공개 URL 파라미터(?weapon·?nobirth·?seed, decisions review-2026-10-05)만 쓴다.
const { chromium } = require('playwright');
(async () => {
const [base, out] = process.argv.slice(2);
const shots = [
  ['waste_birth', '?weapon=greatsword&nobirth&seed=22'],
  ['boss_katana', '?weapon=katana&boss&seed=11'],
  ['boss_dagger', '?weapon=dagger&boss&seed=5'],
];
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on('pageerror', e => console.log('pageerror', e.message));
for (const [name, q] of shots) {
  await page.goto(base + '/' + q, { waitUntil: 'load' });
  await page.waitForTimeout(12000);
  for (let i = 0; i < 3; i++) { await page.mouse.click(960, 540); await page.waitForTimeout(2500); }   // 첫 실행 안내 카드 닫기(클릭)
  // 몇 걸음 움직여 적을 화면에 들인다
  for (const k of ['KeyD', 'KeyW', 'KeyA', 'KeyS']) { await page.keyboard.down(k); await page.waitForTimeout(500); await page.keyboard.up(k); }
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `${out}/${name}.png` });
  console.log('shot', name);
}
await browser.close();
})();
