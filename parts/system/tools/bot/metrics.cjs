// P19 ⑥ 재미 검증 지표 — 무기 × 노드를 봇으로 돌려 표로 낸다 (계약 free-combat §5). `npm run bot:metrics -- [옵션]`
//   --dist <폴더>      이미 빌드한 dist (없으면 vite build 를 임시 폴더로)
//   --weapons a,b      기본 katana,greatsword,dagger,bow (무기마다 브라우저 하나, 동시에)
//   --nodes c1r0,...   기본 c1r0,c3r0,c4r0,c5r0 (전투가 아닌 노드면 같은 열 다른 줄)
//   --out <폴더>       결과 JSON (기본 OS 임시 폴더/lopad-bot)
//   --port <n>         기본 5470
// 합격선은 P19 ⑥ 표 (방 클리어 35~55초 · 동시 활성 5~7/≤12 · 동시 공격 1.2~2.0, 3+ ≤ 10% · 공백 ≤ 1.5초 · 정지 ≤ 15% · 히트스톱 ≤ 8%).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');
const { serve, open, seedMeta, boot, closeMenus } = require('./common.cjs');

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const ROOT = path.resolve(__dirname, '../../../..');
const OUT = path.resolve(arg('out', path.join(os.tmpdir(), 'lopad-bot')));
const PORT = Number(arg('port', 5470));
const WEAPONS = arg('weapons', 'katana,greatsword,dagger,bow').split(',');
const NODES = arg('nodes', 'c1r0,c3r0,c4r0,c5r0').split(',');
const BOT = fs.readFileSync(path.join(__dirname, 'bot.js'), 'utf8');

const PASS = {
  combatMs: (v) => v != null && v >= 35000 && v <= 55000,
  aliveAvg: (v) => v >= 5 && v <= 7,
  aliveMax: (v) => v <= 12,
  attackersAvg: (v) => v >= 1.2 && v <= 2.0,
  attackers3: (v) => v <= 10,
  gapMaxMs: (v) => v <= 1500,
  stillPct: (v) => v <= 15,
  hitstopPct: (v) => v <= 8,
};

async function runWeapon(base, W) {
  const log = (s) => console.log(`[${W}] ${s}`);
  const { browser, page, errors, ev } = await open(base);
  const run = (ms) => page.clock.runFor(ms);
  await seedMeta(page, base);
  await boot(page, ev, `${base}?debug=1&new=1&nobirth&weapon=${W}&seed=p19${W}&notutorial`);
  await page.evaluate(BOT);
  const out = [];
  const opts = { ranged: W === 'bow', reach: W === 'greatsword' ? 34 : W === 'dagger' ? 22 : 28, dashIn: true, drive: true };
  for (const want of NODES) {
    const node = await ev((id) => {
      const nodes = window.__lopad.route().nodes;
      // 전투 노드 + 1열 여정(버려진 길 — 1층 첫 전투)
      const ok = (n) => n && (n.type === 'battle' || (n.type === 'journey' && n.col === 1));
      const n = nodes.find((x) => x.id === id);
      if (ok(n)) return id;
      const col = id.replace(/r\d+$/, '');
      const alt = nodes.find((x) => x.id.startsWith(col + 'r') && ok(x));
      return alt ? alt.id : null;
    }, want);
    if (!node || typeof node !== 'string' || node.startsWith('ERR')) { log(`skip ${want} (전투 노드 아님)`); continue; }
    await ev((id) => window.__lopad.gotoNode(id), node);
    for (let i = 0; i < 80; i++) {
      await run(250);
      const ph = await ev(() => { const g = window.__lopad.sceneObj('Game'); return g && g.sys.settings.status === 5 && g.player && g.director ? (window.__lopad.doors ? window.__lopad.doors().phase : 'x') + ':' + (window.__lopad.route().nodes.find((n) => n.state === 'current') || {}).id : null; });
      if (ph && typeof ph === 'string' && ph.endsWith(':' + node) && !ph.startsWith('walkIn')) break;
    }
    await closeMenus(ev, run);
    await ev(() => { const st = window.__lopad.state; st.hp = st.maxHp = 400; });
    await ev((o) => window.__botInstall(o), { ...opts, node, render: false });
    const t0 = Date.now();
    for (let k = 0; k < 180; k++) {
      await run(1000);
      const s = await ev(() => { const s = window.__botStats; const g = window.__lopad.sceneObj('Game'); return { end: s.combatEnd, frozen: g.frozen, over: window.__lopad.state.gameOver, alive: g.director.debugInfo.alive, wave: g.director.debugInfo.wave, kills: s.kills }; });
      if (typeof s === 'string') { log('ERR ' + s); break; }
      if (process.env.BOT_VERBOSE && k % 10 === 0) log(`  ${k}s ${JSON.stringify(s)}`);
      if (s.frozen) await closeMenus(ev, run);
      if (s.over) { log('died'); break; }
      if (s.end != null) break;
    }
    const sum = await ev(() => window.__botSummary());
    log(`${node} ${((Date.now() - t0) / 1000).toFixed(0)}s real`);
    out.push({ weapon: W, ...sum });
    // 중간에 끊겨도 남게 노드마다 한 줄씩
    fs.appendFileSync(path.join(OUT, 'nodes.jsonl'), JSON.stringify({ weapon: W, ...sum }) + '\n');
    log(table([{ weapon: W, ...sum }]).split('\n')[2]);
    await ev(() => { window.__lopad.killAll(); const g = window.__lopad.sceneObj('Game'); g.sys.game.scene.render = g.sys.game.__origRender; });
    await run(1500);
    await closeMenus(ev, run);
  }
  if (errors.length) log('errors ' + JSON.stringify(errors.slice(0, 5)));
  await browser.close();
  return out;
}

function table(rows) {
  const mark = (ok, v) => (ok ? '' : '✗') + v;
  const lines = ['| 무기 | 노드 | 클리어 s | 웨이브 | 처치 | 활성 평균/최대 | 동시 공격 평균 | 3+ % | 공백 최대 s | 정지 % | 히트스톱 % |', '|---|---|---|---|---|---|---|---|---|---|---|'];
  for (const r of rows) {
    lines.push(`| ${r.weapon} | ${r.node} | ${mark(PASS.combatMs(r.combatMs), r.combatMs == null ? '-' : (r.combatMs / 1000).toFixed(1))} | ${r.waves} | ${r.kills} | ${mark(PASS.aliveAvg(r.aliveAvg), r.aliveAvg)}/${mark(PASS.aliveMax(r.aliveMax), r.aliveMax)} | ${mark(PASS.attackersAvg(r.attackersAvg), r.attackersAvg)} | ${mark(PASS.attackers3(r.attackersHist['3+']), r.attackersHist['3+'])} | ${mark(PASS.gapMaxMs(r.gapMaxMs), (r.gapMaxMs / 1000).toFixed(2))} | ${mark(PASS.stillPct(r.stillPct), r.stillPct)} | ${mark(PASS.hitstopPct(r.hitstopPct), r.hitstopPct)} |`);
  }
  return lines.join('\n');
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  let dist = arg('dist', null);
  if (!dist) {
    dist = path.join(OUT, 'dist');
    console.log('vite build →', dist);
    execSync(`npx vite build --outDir "${dist}" --emptyOutDir`, { cwd: ROOT, stdio: 'ignore' });
  }
  const close = await serve(path.resolve(dist), PORT);
  const base = `http://127.0.0.1:${PORT}/`;
  const rows = (await Promise.all(WEAPONS.map((w) => runWeapon(base, w)))).flat();
  close();
  const file = path.join(OUT, `metrics_${Date.now()}.json`);
  fs.writeFileSync(file, JSON.stringify(rows, null, 1));
  console.log('\n' + table(rows) + '\n');
  console.log('✗ = P19 ⑥ 합격선 밖 · 원자료', file);
  process.exit(0);
})();
