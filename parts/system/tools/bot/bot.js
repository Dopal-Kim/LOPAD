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
    for (const m of mobs) { const d = Math.hypot(m.x - p.x, m.y - p.y); if (d < best) { best = d; tgt = m; } }
    const out = Object.assign({}, raw, { moveX: 0, moveY: 0, attackPressed: false, attackHeld: false, secondaryPressed: false, secondaryHeld: false, secondaryReleased: false, dashPressed: false, sprintHeld: false, interactPressed: false, interactHeld: false });
    if (!tgt) {
      const c = g.world.layout && g.world.layout.arena && g.world.layout.arena.center;
      if (c) { const cx = c.x * T + 8, cy = c.y * T + 8; const dx = cx - p.x, dy = cy - p.y; const l = Math.hypot(dx, dy); if (l > 24) { out.moveX = dx / l; out.moveY = dy / l; } }
      return out;
    }
    const dx = tgt.x - p.x, dy = tgt.y - p.y;
    const l = Math.hypot(dx, dy) || 1;
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
      else if (l > want + 50) { out.moveX = dx / l; out.moveY = dy / l; }
      else { if (now > strafeT) { strafe = -strafe; strafeT = now + 1200; } out.moveX = (-dy / l) * strafe * 0.7; out.moveY = (dx / l) * strafe * 0.7; }
      attackToggle = !attackToggle; out.attackPressed = attackToggle; if (out.attackPressed) s.attackPresses++;
    } else {
      const reach = opts.reach || 28;
      if (l > reach) {
        out.moveX = dx / l; out.moveY = dy / l;
        if (opts.dashIn && l > 70 && l < 120 && dashReady) { out.dashPressed = true; dodgeCd = now + 650; s.dashes++; }
      } else {
        out.moveX = (dx / l) * 0.3; out.moveY = (dy / l) * 0.3;
        attackToggle = !attackToggle; out.attackPressed = attackToggle; if (out.attackPressed) s.attackPresses++;
      }
    }
    if (Math.abs(out.moveX) + Math.abs(out.moveY) > 0.5) {
      s.moveInputFrames++;
      const v = Math.hypot(p.body.velocity.x, p.body.velocity.y);
      if (v < (p.speedPx || 96) * 0.1) s.moveBlockedFrames++;
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
    swings: [s.swingTele, s.swingHits],
    perKindAttackPct: perKindAttack,
    ttk: ttkMed,
  };
};
