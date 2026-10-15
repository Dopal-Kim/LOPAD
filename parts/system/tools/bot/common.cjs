// P19 봇 드라이버 공용 (scratchpad a64/drv 에서 옮김): 정적 서버 · 헤드리스 브라우저 · 메타 심기 · 부팅 (가짜 시계)
// 환경 변수: PW_MODULE(playwright 모듈 경로) · PW_CHROME(크로미움 실행 파일). 기본값은 클라우드 작업 환경 경로.
const fs = require('fs');
const http = require('http');
const path = require('path');

const PW_MODULE = process.env.PW_MODULE || '/opt/node-tools/node_modules/playwright';
const PW_CHROME = process.env.PW_CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.css': 'text/css', '.ogg': 'audio/ogg', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.webp': 'image/webp' };

/** dist 폴더를 127.0.0.1:port 로 낸다. 닫는 함수를 돌려준다 */
function serve(dir, port) {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent((req.url || '/').split('?')[0]);
    let file = path.join(dir, url === '/' ? 'index.html' : url);
    if (!file.startsWith(dir) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(dir, 'index.html');
    res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((ok) => server.listen(port, '127.0.0.1', () => ok(() => server.close())));
}

async function open(base) {
  const { chromium } = require(PW_MODULE);
  const browser = await chromium.launch({ executablePath: PW_CHROME, args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text().slice(0, 200)); });
  await page.clock.install();
  const ev = async (fn, arg) => { try { return await page.evaluate(fn, arg); } catch (e) { return 'ERR ' + e.message.split('\n')[0]; } };
  return { browser, page, errors, ev, base };
}

async function seedMeta(page, base) {
  await page.goto(base + '?debug=1&notitle', { waitUntil: 'load' });
  await page.evaluate(() => {
    const m = { version: 1, souls: 0, totalSouls: 0, runs: 3, clears: 0, bestFloor: 1, upgrades: {}, codex: {}, diary: { lives: 3, deaths: 2, lastName: '도영', pastLives: [{ name: '도영', weapon: 'katana', floor: 1, kills: 8, cleared: false, bosses: [] }], clues: [], guides: ['trait', 'awaken1', 'awaken2'], training: { offered: true } } };
    localStorage.setItem('lopad.meta', JSON.stringify(m)); localStorage.removeItem('lopad.save');
  });
}

// 로딩 동안은 시계를 흘리고, 게임이 뜨면 멈춘다
async function boot(page, ev, url) {
  await page.goto(url, { waitUntil: 'load' });
  for (let i = 0; i < 600; i++) {
    const ok = await ev(() => Boolean(window.__lopad && window.__lopad.player && window.__lopad.sceneObj && window.__lopad.sceneObj('Game') && window.__lopad.ui && window.__lopad.ui().scenes().some((s) => s.startsWith('UiHud'))));
    if (ok === true) break;
    await page.clock.runFor(100); await page.waitForTimeout(50);
  }
  for (let i = 0; i < 10; i++) { try { const now = await page.evaluate(() => Date.now()); await page.clock.pauseAt(now + 3000); break; } catch (e) { /* 다시 */ } }
}

/** 열린 메뉴(성장·보상)를 첫 선택지로 닫는다 */
async function closeMenus(ev, run, log) {
  for (let i = 0; i < 6; i++) {
    const m = await ev(() => { const s = window.__lopad.ui().snapshot(); const m = s.menu; return m ? { id: m.id, lines: m.lines.map((l) => [l.key, l.label, l.enabled]) } : null; });
    if (!m || typeof m === 'string') return;
    const line = m.lines.find((l) => l[2] !== false);
    if (log) log('  menu ' + m.id + ' -> ' + (line && line[1]));
    await run(500);
    if (line) await ev((a) => window.__lopad.ui().select(a[0], a[1]), [m.id, line[0]]);
    await run(800);
  }
}

module.exports = { serve, open, seedMeta, boot, closeMenus };
