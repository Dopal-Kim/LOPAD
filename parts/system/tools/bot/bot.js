// 페이지 안에서 도는 자동 플레이어 + 프레임 계측 (P19 ① 측정 드라이버). window.__botInstall(opts) 로 게임 씬 입력을 가로챈다.
// 봇: 가까운 적에게 다가가 연타(활은 약 7칸 거리), 다가오는 탄·돌진은 옆 대쉬, 먼 적은 대쉬로 붙는다. 패링·시그니처·홀드는 안 쓴다.
// 동시 공격 수: 적의 `attacking`(P19 S3 — 예고·공격 중) 이 있으면 그것, 없으면(옛 빌드) 상태 이름으로 어림.
window.__botInstall = function (opts) {
  const g = window.__lopad.sceneObj('Game');
  const game = g.sys.game;
  if (!game.__origRender) game.__origRender = game.scene.render;
  game.scene.render = opts.render ? game.__origRender : function () {};
  const ranged = opts.ranged;
  const T = 16;
  const st = (window.__botStats = {
    node: opts.node, frames: 0, ms: 0, hitstopFrames: 0, frozenFrames: 0, combatFrames: 0, combatHitstopFrames: 0,
    moveInputFrames: 0, moveBlockedFrames: 0, playerStillFrames: 0,
    attackPresses: 0, dashes: 0, hits: 0, kills: 0, mobHits: {}, mobFirstHit: {}, mobKillAt: {},
    alive: [], activeAttackers: [], waves: [], combatStart: null, combatEnd: null, hpStart: null, hpEnd: null,
    hurtEvents: 0, emptySince: null, gapMax: 0, perKind: {}, timeline: [],
  });
  // P19 ⑤15 환경 상호작용 (벽꽝·볼링·낙하·폭발·점화) · 반응 횟수 — 시스템 EventBus (debug onEvent)
  st.react = {};
  for (const off of window.__botOffs || []) off();
  window.__botOffs = ['enemy:wall-slam', 'enemy:bowled', 'enemy:fell', 'hazard:exploded', 'hazard:ignited', 'enemy:launched', 'enemy:staggered', 'enemy:knocked'].map((ev) =>
    window.__lopad.onEvent(ev, (p) => {
      const s = window.__botStats; if (!s || s.combatEnd != null) return;
      const k = ev === 'enemy:knocked' ? 'knock' + p.tier : ev === 'enemy:staggered' ? p.kind : ev === 'hazard:exploded' ? (p.chain > 0 ? 'chain' : 'exploded') : ev.split(':')[1];
      s.react[k] = (s.react[k] || 0) + 1;
    }),
  );
  let frame = 0;
  let lastWave = -1;
  let lastHp = null;
  const C = g.combat;
  if (!C.__wrapped) {
    const orig = C.hitMob.bind(C);
    C.hitMob = function (mob, dmg, o) {
      const s = window.__botStats;
      const id = mob.__bid || (mob.__bid = (mob.id || mob.spriteId) + '#' + Math.random().toString(36).slice(2, 6));
      const now = g.time.now;
      s.hits++; s.mobHits[id] = (s.mobHits[id] || 0) + 1; if (s.mobFirstHit[id] == null) s.mobFirstHit[id] = now;
      const died = orig(mob, dmg, o);
      if ((died || mob.hp <= 0) && s.mobKillAt[id] == null) { s.kills++; s.mobKillAt[id] = now; }
      return died;
    };
    C.__wrapped = true;
  }
  // 적 근접 휘두르기 예고·판정 횟수 (P19 S3 — 없으면 0)
  st.swingTele = 0; st.swingHits = 0;
  if (!g.telegraph.__w) { const cone = g.telegraph.cone.bind(g.telegraph); g.telegraph.cone = function (...a) { if (window.__botStats) window.__botStats.swingTele++; return cone(...a); }; g.telegraph.__w = true; }
  if (C.meleeHit && !C.__wm) { const mh = C.meleeHit; C.meleeHit = function (...a) { if (window.__botStats) window.__botStats.swingHits++; return mh(...a); }; C.__wm = true; }
  const IS = g.inputSystem;
  if (!IS.__origRead) IS.__origRead = IS.read.bind(IS);
  if (!g.sys.sceneUpdate.__w) {
    const su = g.sys.sceneUpdate;
    g.sys.sceneUpdate = function (time, delta) {
      const s = window.__botStats;
      if (s) {
        s.frames++; s.ms += delta;
        const fighting = s.combatStart != null && s.combatEnd == null;
        if (fighting) s.combatFrames++;
        if (g.frozen) s.frozenFrames++;
        else if (g.hitStop && g.hitStop.active && g.hitStop.active(time)) { s.hitstopFrames++; if (fighting) s.combatHitstopFrames++; }
      }
      return su.call(this, time, delta);
    };
    g.sys.sceneUpdate.__w = true;
  }
  const attackingOf = (m) => {
    if (typeof m.attacking === 'boolean') return m.attacking;
    const bs = m.behaviorState || '';
    return Boolean(m.windingUp) || bs === 'dash' || bs === 'telegraph' || bs === 'aim' || bs === 'windup' || ((bs === 'chase' || bs === 'pack') && Math.hypot(m.x - g.player.x, m.y - g.player.y) < 26);
  };
  // --- 격자 A* (P19 2단계: 형태 틀 전투장의 벽·낙하 구역을 돌아 남은 적에게 간다) ---
  const world = g.world;
  const TW = world.layout.widthTiles, TH = world.layout.heightTiles;
  const walkT = (tx, ty) => tx >= 0 && ty >= 0 && tx < TW && ty < TH && world.isWalkableAt(tx * T + T / 2, ty * T + T / 2);
  // 몸 반폭(약 5px)만큼 옆도 열려 있어야 직선으로 간다
  const clearAt = (x, y) => world.isWalkableAt(x, y) && world.isWalkableAt(x - 5, y) && world.isWalkableAt(x + 5, y) && world.isWalkableAt(x, y - 4) && world.isWalkableAt(x, y + 4);
  const los = (ax, ay, bx, by) => {
    const d = Math.hypot(bx - ax, by - ay); const n = Math.ceil(d / 6);
    for (let i = 1; i < n; i++) { const t = i / n; if (!clearAt(ax + (bx - ax) * t, ay + (by - ay) * t)) return false; }
    return true;
  };
  // 이진 힙 (f 값이 작은 것부터)
  const heap = { a: [], push(n) { const a = this.a; a.push(n); let i = a.length - 1; while (i > 0) { const j = (i - 1) >> 1; if (a[j][0] <= a[i][0]) break; [a[i], a[j]] = [a[j], a[i]]; i = j; } }, pop() { const a = this.a; const top = a[0]; const last = a.pop(); if (a.length) { a[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < a.length && a[l][0] < a[m][0]) m = l; if (r < a.length && a[r][0] < a[m][0]) m = r; if (m === i) break; [a[i], a[m]] = [a[m], a[i]]; i = m; } } return top; } };
  function astar(sx, sy, gx, gy) {
    const key = (x, y) => y * TW + x;
    const H = (x, y) => { const dx = Math.abs(x - gx), dy = Math.abs(y - gy); return dx + dy - 0.59 * Math.min(dx, dy); };
    heap.a = [[H(sx, sy), sx, sy]]; const gs = new Map([[key(sx, sy), 0]]); const from = new Map(); const closed = new Set();
    let it = 0;
    while (heap.a.length && it++ < 40000) {
      const [, x, y] = heap.pop();
      const k = key(x, y); if (closed.has(k)) continue; closed.add(k);
      if (Math.abs(x - gx) <= 1 && Math.abs(y - gy) <= 1) { const path = [[x, y]]; let c = k; while (from.has(c)) { c = from.get(c); path.push([c % TW, Math.floor(c / TW)]); } return path.reverse(); }
      for (const [ox, oy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
        const nx = x + ox, ny = y + oy; if (!walkT(nx, ny)) continue;
        if (ox && oy && (!walkT(x + ox, y) || !walkT(x, y + oy))) continue; // 모서리 자르기 금지
        const ng = gs.get(k) + (ox && oy ? 1.41 : 1); const nk = key(nx, ny);
        if (ng < (gs.get(nk) ?? 1e9)) { gs.set(nk, ng); from.set(nk, k); heap.push([ng + H(nx, ny), nx, ny]); }
      }
    }
    return null;
  }
  // 갈 수 없는 적은 잠시 목표에서 뺀다 (낙하 구역 건너편 등) · 막혀 서 있으면 옆으로 비킨다
  const unreachable = new WeakMap();
  let stuckFrames = 0, sidestepUntil = 0, sidestep = [0, 0];
  const nav = { path: null, goal: null, at: -1e9, target: null };
  st.pathCalls = 0; st.pathFails = 0; st.stillBy = {};
  /** 목표 (wx, wy) 로 갈 방향: 보이면 직선, 아니면 A* 경로의 보이는 가장 먼 칸 */
  function steer(wx, wy) {
    const p = g.player;
    if (los(p.x, p.y, wx, wy)) { nav.path = null; return [wx, wy]; }
    const gt = [Math.floor(wx / T), Math.floor(wy / T)];
    const now = g.time.now;
    if (!nav.path || !nav.goal || Math.abs(nav.goal[0] - gt[0]) + Math.abs(nav.goal[1] - gt[1]) > 1 || now - nav.at > 700) {
      st.pathCalls++;
      nav.path = astar(Math.floor(p.x / T), Math.floor(p.y / T), gt[0], gt[1]); nav.goal = gt; nav.at = now;
      if (!nav.path) { st.pathFails++; if (nav.target) unreachable.set(nav.target, now + 3000); }
    }
    if (!nav.path) return [wx, wy];
    // 이미 지난 칸 버리기 · 보이는 가장 먼 칸으로 (줄 당기기)
    let best = null;
    for (let i = Math.min(nav.path.length - 1, 12); i >= 0; i--) { const [tx, ty] = nav.path[i]; const cx = tx * T + T / 2, cy = ty * T + T / 2; if (los(p.x, p.y, cx, cy)) { best = [cx, cy]; nav.path = nav.path.slice(i); break; } }
    return best || [nav.path[0][0] * T + T / 2, nav.path[0][1] * T + T / 2];
  }
  let attackToggle = false;
  let dodgeCd = 0;
  let strafe = 1;
  let strafeT = 0;
  IS.read = function () {
    const raw = IS.__origRead();
    const s = window.__botStats;
    const p = g.player;
    const now = g.time.now;
    const mobs = g.mobs.getChildren().filter((m) => m.active && m.hp > 0);
    frame++;
    const inCombat = g.director.inCombat;
    const hp = window.__lopad.state.hp;
    if (s.hpStart == null) s.hpStart = hp;
    if (lastHp != null && hp < lastHp) s.hurtEvents++;
    lastHp = hp; s.hpEnd = hp;
    const dbg = g.director.debugInfo;
    if (inCombat && s.combatStart == null) s.combatStart = now;
    if (dbg.wave !== lastWave) { s.waves.push({ wave: dbg.wave, at: Math.round(now) }); lastWave = dbg.wave; }
    if (s.combatStart != null && !inCombat && s.combatEnd == null && mobs.length === 0) s.combatEnd = now;
    let attackers = 0;
    for (const m of mobs) {
      const k = m.id || m.spriteId;
      const pk = s.perKind[k] || (s.perKind[k] = { frames: 0, attack: 0 });
      pk.frames++;
      if (attackingOf(m)) { attackers++; pk.attack++; }
    }
    if (inCombat && s.combatEnd == null) {
      s.alive.push(mobs.length); s.activeAttackers.push(attackers);
      // 공백: 첫 적이 나온 뒤 살아 있는 적 0 인 연속 시간 (첫 웨이브 예고 전 시간은 빼고)
      if (mobs.length === 0 && s.alive.some((n) => n > 0)) { if (s.emptySince == null) s.emptySince = now; s.gapMax = Math.max(s.gapMax, now - s.emptySince); }
      else s.emptySince = null;
    }
    if (frame % 30 === 0) s.timeline.push([Math.round(now), mobs.length, attackers, hp]);
    if (!opts.drive) return raw;
    let tgt = null, best = 1e9;
    for (const m of mobs) { if ((unreachable.get(m) || 0) > now) continue; const d = Math.hypot(m.x - p.x, m.y - p.y); if (d < best) { best = d; tgt = m; } }
    if (!tgt) for (const m of mobs) { const d = Math.hypot(m.x - p.x, m.y - p.y); if (d < best) { best = d; tgt = m; } }
    nav.target = tgt;
    const out = Object.assign({}, raw, { moveX: 0, moveY: 0, attackPressed: false, attackHeld: false, secondaryPressed: false, secondaryHeld: false, secondaryReleased: false, dashPressed: false, sprintHeld: false, interactPressed: false, interactHeld: false });
    if (!tgt) {
      const c = g.world.layout && g.world.layout.arena && g.world.layout.arena.center;
      if (c) { const cx = c.x * T + 8, cy = c.y * T + 8; const [wx, wy] = steer(cx, cy); const dx = wx - p.x, dy = wy - p.y; const l = Math.hypot(dx, dy); if (Math.hypot(cx - p.x, cy - p.y) > 24 && l > 0) { out.moveX = dx / l; out.moveY = dy / l; } }
      return out;
    }
    const dx = tgt.x - p.x, dy = tgt.y - p.y;
    const l = Math.hypot(dx, dy) || 1;
    // 다가갈 방향 (벽·낙하 구역이 가로막으면 A* 경로)
    const [sx, sy] = steer(tgt.x, tgt.y);
    const sl = Math.hypot(sx - p.x, sy - p.y) || 1;
    const ax = (sx - p.x) / sl, ay = (sy - p.y) / sl;
    out.aimX = tgt.x; out.aimY = tgt.y;
    let threat = null;
    for (const pr of g.projectiles.getChildren()) { if (!pr.active) continue; const rx = p.x - pr.x, ry = p.y - pr.y; const rd = Math.hypot(rx, ry); const vx = pr.body.velocity.x, vy = pr.body.velocity.y; if (rd < 56 && rx * vx + ry * vy > 0) { threat = { vx, vy }; break; } }
    if (!threat) for (const m of mobs) { if (m.behaviorState === 'dash' && Math.hypot(m.x - p.x, m.y - p.y) < 72) { threat = { vx: m.body.velocity.x, vy: m.body.velocity.y }; break; } }
    const dashReady = p.action === 'normal' && now >= dodgeCd;
    if (threat && dashReady && opts.dodge !== false) {
      const tl = Math.hypot(threat.vx, threat.vy) || 1;
      out.moveX = (-threat.vy / tl) * strafe; out.moveY = (threat.vx / tl) * strafe; out.dashPressed = true; dodgeCd = now + 650; s.dashes++; strafe = -strafe;
      return out;
    }
    if (ranged) {
      const want = 110;
      if (l < want - 30) { out.moveX = -dx / l; out.moveY = -dy / l; }
      else if (l > want + 50 || nav.path) { out.moveX = ax; out.moveY = ay; }
      else { if (now > strafeT) { strafe = -strafe; strafeT = now + 1200; } out.moveX = (-dy / l) * strafe * 0.7; out.moveY = (dx / l) * strafe * 0.7; }
      attackToggle = !attackToggle; out.attackPressed = attackToggle; if (out.attackPressed) s.attackPresses++;
    } else {
      const reach = opts.reach || 28;
      if (l > reach || nav.path) {
        out.moveX = ax; out.moveY = ay;
        if (opts.dashIn && !nav.path && l > 70 && l < 120 && dashReady) { out.dashPressed = true; dodgeCd = now + 650; s.dashes++; }
      } else {
        out.moveX = (dx / l) * 0.3; out.moveY = (dy / l) * 0.3;
        attackToggle = !attackToggle; out.attackPressed = attackToggle; if (out.attackPressed) s.attackPresses++;
      }
    }
    // 막힘 탈출: 이동 입력 중 20프레임 넘게 거의 못 움직이면 0.3초 옆으로 (봇 한계 — 지표의 정지 % 와 별개로 센다)
    const vv = Math.hypot(p.body.velocity.x, p.body.velocity.y);
    if (now < sidestepUntil) { out.moveX = sidestep[0]; out.moveY = sidestep[1]; }
    else if (Math.abs(out.moveX) + Math.abs(out.moveY) > 0.5 && p.action === 'normal' && vv < (p.speedPx || 96) * 0.1) {
      if (++stuckFrames > 20) { stuckFrames = 0; s.sidesteps = (s.sidesteps || 0) + 1; sidestep = [-out.moveY * strafe, out.moveX * strafe]; strafe = -strafe; sidestepUntil = now + 300; }
    } else stuckFrames = 0;
    if (Math.abs(out.moveX) + Math.abs(out.moveY) > 0.5) {
      s.moveInputFrames++;
      const v = Math.hypot(p.body.velocity.x, p.body.velocity.y);
      if (v < (p.speedPx || 96) * 0.1) {
        s.moveBlockedFrames++;
        // 정지 원인 (디버그): 주인공 동작 · 경로 따라가는 중
        const why = (p.action || '?') + (nav.path ? ':path' : '') + (p.combo && p.combo.active ? ':combo' : '');
        s.stillBy[why] = (s.stillBy[why] || 0) + 1;
      }
    }
    if (Math.hypot(p.body.velocity.x, p.body.velocity.y) < 5) s.playerStillFrames++;
    return out;
  };
  return { ok: true, mobs: g.mobs.getChildren().length };
};

// 측정 끝: 요약 (P19 ⑥ 지표)
window.__botSummary = function () {
  const s = window.__botStats;
  const avg = (a) => (a.length ? +(a.reduce((x, y) => x + y, 0) / a.length).toFixed(2) : 0);
  const hist = { 0: 0, 1: 0, 2: 0, '3+': 0 };
  for (const v of s.activeAttackers) hist[v >= 3 ? '3+' : v]++;
  const n = Math.max(1, s.activeAttackers.length);
  for (const k in hist) hist[k] = +((100 * hist[k]) / n).toFixed(1);
  const ttk = {};
  for (const id in s.mobKillAt) { const k = id.split('#')[0]; (ttk[k] = ttk[k] || []).push([Math.round(s.mobKillAt[id] - s.mobFirstHit[id]), s.mobHits[id]]); }
  const med = (a) => { const b = [...a].sort((x, y) => x - y); return b.length ? b[Math.floor(b.length / 2)] : null; };
  const ttkMed = {};
  for (const k in ttk) ttkMed[k] = { ms: med(ttk[k].map((x) => x[0])), hits: med(ttk[k].map((x) => x[1])), n: ttk[k].length };
  const perKindAttack = {};
  for (const k in s.perKind) perKindAttack[k] = +((100 * s.perKind[k].attack) / Math.max(1, s.perKind[k].frames)).toFixed(1);
  return {
    node: s.node,
    combatMs: s.combatEnd != null ? Math.round(s.combatEnd - s.combatStart) : null,
    waves: Math.max(0, ...s.waves.map((w) => w.wave)) + 1,
    kills: s.kills,
    aliveAvg: avg(s.alive),
    aliveMax: Math.max(0, ...s.alive),
    attackersAvg: avg(s.activeAttackers),
    attackersHist: hist,
    gapMaxMs: Math.round(s.gapMax),
    stillPct: +((100 * s.moveBlockedFrames) / Math.max(1, s.moveInputFrames)).toFixed(1),
    hitstopPct: +((100 * s.combatHitstopFrames) / Math.max(1, s.combatFrames)).toFixed(1),
    hp: [s.hpStart, s.hpEnd],
    hurtEvents: s.hurtEvents,
    dashes: s.dashes,
    path: [s.pathCalls, s.pathFails],
    react: s.react,
    stillBy: s.stillBy,
    sidesteps: s.sidesteps || 0,
    env: ['wall-slam', 'bowled', 'fell', 'exploded', 'chain', 'ignited'].reduce((a, k) => a + (s.react[k] || 0), 0),
    swings: [s.swingTele, s.swingHits],
    perKindAttackPct: perKindAttack,
    ttk: ttkMed,
  };
};
