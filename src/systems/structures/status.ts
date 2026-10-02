/**
 * 구조물 층 상태 → HUD 상태 줄 (계약 §9.2): 빚 · 취기 · 판돈 · 불씨 · 불붙은 무기 · 투견 링 · 룰렛 규칙 · 숙성 · 전당.
 */
import { gameState } from '../../core/GameState';
import type { UiStatus } from '../../contract/ui';
import { num, structureDef, txt } from './data';
import { agingProgress, drunkMods } from './rules';
import type { StructureCore } from './core';

const ORDER: readonly UiStatus['id'][] = [
  'debt',
  'drunk',
  'stakes',
  'embers',
  'fireWeapon',
  'ring',
  'roulette',
  'aging',
  'pawn',
];

/** 숙성 진행 한 줄 */
function agingStatus(at: number, def: ReturnType<typeof structureDef>): UiStatus {
  const need = num(def, 'trialsNeeded');
  const g = agingProgress(at, gameState.trialsCleared, need);
  return {
    id: 'aging',
    kind: 'progress',
    label: txt(def, 'statusLabel'),
    value: g.ready ? txt(def, 'statusDone') : `${g.done}/${need}`,
    amount: g.done,
    max: need,
    detail: txt(def, 'statusDetail', { n: need }),
  };
}

export function structureStatuses(c: StructureCore): UiStatus[] {
  const out: UiStatus[] = [];
  const now = c.now;
  const ledger = structureDef('ledger');
  if (c.debt > 0)
    out.push({
      id: 'debt',
      kind: 'debuff',
      label: txt(ledger, 'statusLabel'),
      value: `${c.debt}G`,
      amount: c.debt,
      detail: txt(ledger, 'statusDetail', { pct: Math.round(num(ledger, 'repayRatio') * 100) }),
    });
  if (c.drunk > 0) {
    const counter = structureDef('counter');
    const P = c.drunkParams;
    const m = drunkMods(c.drunk, P);
    out.push({
      id: 'drunk',
      kind: 'buff',
      label: txt(counter, 'statusLabel'),
      value: `${c.drunk}단`,
      amount: c.drunk,
      max: P.maxLevel,
      detail: txt(counter, 'statusDetail', {
        atk: Math.round((m.attackMult - 1) * 100),
        def: m.defense,
        deg: m.swayDeg,
      }),
    });
  }
  if (c.stakeRings > 0) {
    const b = structureDef('stakeBell');
    const m = c.stakes;
    out.push({
      id: 'stakes',
      kind: 'debuff',
      label: txt(b, 'statusLabel'),
      value: `×${m.goldMult.toFixed(1)}`,
      amount: c.stakeRings,
      max: num(b, 'maxRings'),
      detail: txt(b, 'statusDetail', {
        hp: Math.round((m.hpMult - 1) * 100),
        extra: m.extra,
        gold: m.goldMult.toFixed(1),
        pers: m.personalityMult.toFixed(1),
      }),
    });
  }
  const fire = c.find('campfire');
  if (fire && c.embers > 0)
    out.push({
      id: 'embers',
      kind: 'resource',
      label: txt(fire.def, 'statusLabel'),
      value: String(c.embers),
      amount: c.embers,
      max: num(fire.def, 'maxEmbers'),
      detail: txt(fire.def, 'statusDetail', { pct: Math.round(num(fire.def, 'healPerEmber') * 100) }),
    });
  const still = c.stillDef;
  if (still && c.fireActive)
    out.push({
      id: 'fireWeapon',
      kind: 'buff',
      label: txt(still, 'statusLabel'),
      value: txt(still, 'statusValue'),
      remainMs: Math.max(0, c.fireWeaponUntil - now),
      durationMs: num(still, 'fireMs'),
      detail: txt(still, 'statusDetail'),
    });
  if (c.ring) {
    const d = c.ring.inst.def;
    const killed = Math.max(0, c.ring.max - c.host.director.debugInfo.alive);
    out.push({
      id: 'ring',
      kind: 'timer',
      label: txt(d, 'statusLabel'),
      value: `${killed}/${c.ring.max}`,
      amount: killed,
      max: c.ring.max,
      remainMs: Math.max(0, c.ring.until - now),
      durationMs: num(d, 'timeLimitMs'),
    });
  }
  if (c.roulette) {
    const rule = c.ruleAt(c.roulette.ruleIndex);
    if (rule)
      out.push({
        id: 'roulette',
        kind: 'rule',
        label: txt(c.roulette.inst.def, 'statusLabel'),
        value: String(rule.name),
        detail: String(rule.detail),
      });
  }
  for (const s of c.list) {
    if (s.kind !== 'agingBarrel' || s.agingAt === null || s.state === 'used') continue;
    out.push(agingStatus(s.agingAt, s.def));
  }
  if (c.agingCarry.length > 0) {
    const ad = structureDef('agingBarrel');
    for (const at of c.agingCarry) out.push(agingStatus(at, ad));
  }
  if (c.pawned.length > 0) {
    const p = structureDef('pawn');
    out.push({
      id: 'pawn',
      kind: 'resource',
      label: txt(p, 'statusLabel'),
      value: String(c.pawned.length),
      amount: c.pawned.length,
      detail: txt(p, 'statusDetail'),
    });
  }
  return out.sort((a, b) => ORDER.indexOf(a.id) - ORDER.indexOf(b.id));
}
