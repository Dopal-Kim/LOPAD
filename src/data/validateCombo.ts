/**
 * 48·55라운드 연격 데이터 검사 (data/index.ts 에서 분리 — 55라운드 6-1). 형식은 `comboTypes.ts`.
 */
import type { ComboDef, ComboFollowUpDef, ComboHitDef, HitShapeSpec } from './comboTypes';
import { num } from './validateUtil';

function optNum(v: unknown, path: string): void {
  if (v !== undefined) num(v, path);
}

function positive(v: unknown, path: string): void {
  num(v, path);
  if (!((v as number) > 0)) throw new Error(`[data] ${path} 는 0 보다 커야 합니다`);
}

function ratio(v: unknown, path: string): void {
  if (v === undefined) return;
  num(v, path);
  if ((v as number) < 0 || (v as number) >= 1) throw new Error(`[data] ${path} 는 0 이상 1 미만`);
}

/** 55라운드 §17 판정 모양 */
export function validateHitShape(s: HitShapeSpec, path: string): void {
  switch (s?.kind) {
    case 'arc':
      num(s.fromDeg, `${path}.fromDeg`);
      num(s.toDeg, `${path}.toDeg`);
      if (s.fromDeg === s.toDeg) throw new Error(`[data] ${path}: fromDeg 와 toDeg 가 같다`);
      if (Math.abs(s.toDeg - s.fromDeg) > 360) throw new Error(`[data] ${path}: 호는 360° 이하`);
      ratio(s.innerRatio, `${path}.innerRatio`);
      if (s.radiusMult !== undefined) positive(s.radiusMult, `${path}.radiusMult`);
      return;
    case 'wedge':
      positive(s.widthDeg, `${path}.widthDeg`);
      positive(s.lengthMult, `${path}.lengthMult`);
      optNum(s.angleDeg, `${path}.angleDeg`);
      if (s.impactCircle) {
        positive(s.impactCircle.radiusRatio, `${path}.impactCircle.radiusRatio`);
        optNum(s.impactCircle.atMult, `${path}.impactCircle.atMult`);
      }
      return;
    case 'rect':
      positive(s.lengthMult, `${path}.lengthMult`);
      positive(s.widthMult, `${path}.widthMult`);
      optNum(s.angleDeg, `${path}.angleDeg`);
      optNum(s.fromMult, `${path}.fromMult`);
      return;
    case 'ring':
      positive(s.radiusMult, `${path}.radiusMult`);
      ratio(s.innerRatio, `${path}.innerRatio`);
      optNum(s.atMult, `${path}.atMult`);
      return;
    default:
      throw new Error(`[data] ${path}.kind 는 arc|wedge|rect|ring`);
  }
}

function validateFollowUps(list: ComboFollowUpDef[] | undefined, path: string): void {
  if (list === undefined) return;
  if (!Array.isArray(list)) throw new Error(`[data] ${path} 는 배열`);
  list.forEach((f, i) => {
    const p = `${path}[${i}]`;
    if (typeof f.id !== 'string' || !f.id) throw new Error(`[data] ${p}.id 없음`);
    num(f.delayMs, `${p}.delayMs`);
    if (f.delayMs < 0) throw new Error(`[data] ${p}.delayMs 는 0 이상`);
    num(f.damageMult, `${p}.damageMult`);
    if (f.hitShape) validateHitShape(f.hitShape, `${p}.hitShape`);
    if (f.at !== undefined && f.at !== 'origin' && f.at !== 'impact')
      throw new Error(`[data] ${p}.at 는 origin|impact`);
    optNum(f.activeMs, `${p}.activeMs`);
  });
}

export function validateHit(h: ComboHitDef, path: string, art: Record<string, unknown> | undefined): void {
  for (const k of ['damageMult', 'sizeMult', 'durationMs', 'cancelFromMs', 'activeMs'] as const)
    num(h[k], `${path}.${k}`);
  if (h.cancelFromMs > h.durationMs) throw new Error(`[data] ${path}.cancelFromMs 는 durationMs 이하`);
  if (h.hitAtMs !== undefined && !(h.hitAtMs > 0 && h.hitAtMs < h.durationMs))
    throw new Error(`[data] ${path}.hitAtMs 는 0 과 durationMs 사이`);
  if (h.hitShape) validateHitShape(h.hitShape, `${path}.hitShape`);
  if (h.step) {
    num(h.step.px, `${path}.step.px`);
    positive(h.step.ms, `${path}.step.ms`);
  }
  if (h.art !== undefined && !(art && h.art in art))
    throw new Error(`[data] ${path}.art '${h.art}' 이 combo.art 표에 없음`);
  validateFollowUps(h.followUps, `${path}.followUps`);
  for (const f of h.followUps ?? [])
    if (f.art !== undefined && !(art && f.art in art)) throw new Error(`[data] ${path}.followUps.art '${f.art}' 없음`);
}

/** 48라운드 연격: 모양·버퍼·타별 수치 · 55라운드 타별 판정 모양·내딛기·후속 판정·순환·관성·차지·그림 이름 표 */
export function validateCombo(c: ComboDef, path: string): ComboDef {
  if (c.shape !== 'arc' && c.shape !== 'thrust') throw new Error(`[data] ${path}.shape 는 arc|thrust`);
  if (c.shape === 'arc') num(c.arcDeg, `${path}.arcDeg`);
  optNum(c.radiusPx, `${path}.radiusPx`);
  if (c.shape === 'thrust') {
    num(c.thrust?.lengthPx, `${path}.thrust.lengthPx`);
    num(c.thrust?.widthPx, `${path}.thrust.widthPx`);
  }
  for (const k of ['bufferMs', 'resetMs', 'finisherRecoverMs'] as const) num(c[k], `${path}.${k}`);
  if (!Array.isArray(c.hits) || c.hits.length === 0) throw new Error(`[data] ${path}.hits 비어 있음`);
  if (c.leftTransform !== undefined && c.leftTransform !== 'mirror' && c.leftTransform !== 'rotate')
    throw new Error(`[data] ${path}.leftTransform 는 mirror|rotate`);
  if (c.art) {
    for (const [k, e] of Object.entries(c.art)) {
      for (const f of ['body', 'fx', 'impactFx', 'flashFx'] as const) {
        const v = e[f];
        if (v !== undefined && !(Array.isArray(v) && v.every((x) => typeof x === 'string' && x.length > 0)))
          throw new Error(`[data] ${path}.art.${k}.${f} 는 이름 배열`);
      }
      optNum(e.holdColumn, `${path}.art.${k}.holdColumn`);
    }
  }
  c.hits.forEach((h, i) => validateHit(h, `${path}.hits[${i}]`, c.art));
  if (c.momentum) {
    const m = c.momentum;
    for (const k of ['perHit', 'max', 'idleResetMs', 'maxImpactMult'] as const) num(m[k], `${path}.momentum.${k}`);
    if (m.perHit < 0 || m.max < 0) throw new Error(`[data] ${path}.momentum 는 0 이상`);
  }
  if (c.charge) {
    const ch = c.charge;
    positive(ch.holdMs, `${path}.charge.holdMs`);
    num(ch.moveMult, `${path}.charge.moveMult`);
    if (!Array.isArray(ch.stages) || ch.stages.length === 0) throw new Error(`[data] ${path}.charge.stages 비어 있음`);
    ch.stages.forEach((s, i) => {
      const p = `${path}.charge.stages[${i}]`;
      positive(s.atMs, `${p}.atMs`);
      positive(s.lengthMult, `${p}.lengthMult`);
      num(s.damageMult, `${p}.damageMult`);
      if (i > 0 && s.atMs <= ch.stages[i - 1].atMs) throw new Error(`[data] ${p}.atMs 는 오름차순`);
      validateFollowUps(s.followUps, `${p}.followUps`);
      if (s.art !== undefined && !(c.art && s.art in c.art)) throw new Error(`[data] ${p}.art '${s.art}' 없음`);
      if (s.impactMult !== undefined) positive(s.impactMult, `${p}.impactMult`);
    });
    if (ch.stages[0].atMs < ch.holdMs) throw new Error(`[data] ${path}.charge.stages[0].atMs 는 holdMs 이상`);
    validateHit(ch.hit, `${path}.charge.hit`, c.art);
    if (ch.hit.hitShape?.kind !== 'wedge') throw new Error(`[data] ${path}.charge.hit.hitShape 는 wedge`);
    if (ch.holdArt !== undefined && !(c.art && ch.holdArt in c.art))
      throw new Error(`[data] ${path}.charge.holdArt '${ch.holdArt}' 없음`);
    const cl = ch.crackLine;
    if (cl) {
      const cp = `${path}.charge.crackLine`;
      if (!(c.art && cl.art in c.art)) throw new Error(`[data] ${cp}.art '${cl.art}' 이 combo.art 표에 없음`);
      if (!Array.isArray(cl.tilesByStage) || cl.tilesByStage.length !== ch.stages.length)
        throw new Error(`[data] ${cp}.tilesByStage 는 차지 단계 수만큼`);
      cl.tilesByStage.forEach((v, i) => positive(v, `${cp}.tilesByStage[${i}]`));
      for (const k of ['tilePx', 'halfWidthPx', 'msPerTile', 'tileCrackScale'] as const) positive(cl[k], `${cp}.${k}`);
      num(cl.damageMult, `${cp}.damageMult`);
    }
  }
  return c;
}
