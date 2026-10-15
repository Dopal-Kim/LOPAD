// P19 ⑤3 화면 밝기: 형태 틀 7종 + 보스 헤드리스 스크린샷 (가짜 시계) → 평균 휘도 · 거의 검정(L<25) 비율.
//   node parts/system/tools/bot/shots.cjs <dist> <outDir>   (ONLY=plaza_fountain,rampart 처럼 고를 수 있다)
// 휘도 = Rec.709 (0.2126 R + 0.7152 G + 0.0722 B) — 페이지 안 캔버스로 PNG 를 풀어 잰다 (외부 의존 없음).
// 한 형태에 두 장: 입장 직후(<형태>.png) · 주인공을 무대 중심 앞으로(<형태>_center.png — 전투 화면).
const fs = require('fs');
const path = require('path');
const { serve, open, seedMeta, boot, closeMenus } = require('./common.cjs');

const [dist, out] = process.argv.slice(2);
const SHOTS = [
  ['plaza_fountain', 'c3r0'], ['crossroad', 'c3r1'], ['dock_quay', 'c5r0'], ['cellar', 'c5r1'],
  ['distillery', 'c5r0'], ['terrace', 'c3r0'], ['rampart', 'c1r0'], ['banquet_hall', 'c7r0'],
];

async function luma(page, file) {
  const b64 = fs.readFileSync(file).toString('base64');
  return page.evaluate(async (data) => {
    const img = new Image();
    img.src = 'data:image/png;base64,' + data;
    await img.decode();
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const x = c.getContext('2d'); x.drawImage(img, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height).data;
    let sum = 0, dark = 0; const n = d.length / 4;
    for (let i = 0; i < d.length; i += 4) { const L = 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]; sum += L; if (L < 25) dark++; }
    return { mean: +(sum / n).toFixed(1), dark: +((100 * dark) / n).toFixed(1) };
  }, b64);
}

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const PORT = Number(process.env.PORT || 4719);
  const close = await serve(path.resolve(dist), PORT);
  const base = `http://127.0.0.1:${PORT}/`;
  const only = (process.env.ONLY || '').split(',').filter(Boolean);
  const rows = [];
  for (const [shape, node] of SHOTS.filter(([s]) => only.length === 0 || only.includes(s))) {
    const { browser, page, errors, ev } = await open(base);
    try {
      const run = (ms) => page.clock.runFor(ms);
      await seedMeta(page, base);
      await boot(page, ev, `${base}?debug=1&new=1&nobirth&weapon=katana&seed=p19shot&notutorial&shape=${shape}`);
      await ev((id) => window.__lopad.gotoNode(id), node);
      for (let i = 0; i < 120; i++) {
        await run(250);
        const ok = await ev((id) => { const g = window.__lopad.sceneObj('Game'); return Boolean(g && g.sys.settings.status === 5 && g.nodeArena && g.node && g.node.id === id && !g.transitioning && !(window.__lopad.doors && window.__lopad.doors().phase.startsWith('walk'))); }, node);
        if (ok === true) break;
      }
      await run(4000);
      // 조작 안내·보상 메뉴 같은 화면 가운데 판이 밝기를 가리지 않게
      await closeMenus(ev, run);
      // 보스 노드 '싸우는 법' 안내판(UI — 메뉴 목록 밖)은 Enter 로 닫는다
      await page.keyboard.press('Enter');
      await run(500);
      const file = path.join(out, `${shape}.png`);
      await page.screenshot({ path: file });
      await ev(() => { const g = window.__lopad.sceneObj('Game'); const c = g.layout.arena.center; g.player.body.reset((c.x + 0.5) * 16, (c.y + 3.5) * 16); });
      await run(1500);
      const fileC = path.join(out, `${shape}_center.png`);
      await page.screenshot({ path: fileC });
      const row = { shape, node, entry: await luma(page, file), center: await luma(page, fileC), errors: errors.slice(0, 3) };
      rows.push(row);
      console.log(JSON.stringify(row));
    } catch (e) {
      console.log('FAIL ' + shape + ' ' + e.message.split('\n')[0]);
    }
    await browser.close().catch(() => {});
  }
  close();
  console.log('\n| 형태 | 입장 휘도 / L<25 % | 전투 화면 휘도 / L<25 % |\n|---|---|---|');
  for (const r of rows) console.log(`| ${r.shape} | ${r.entry.mean} / ${r.entry.dark} | ${r.center.mean} / ${r.center.dark} |`);
  process.exit(0);
})();
