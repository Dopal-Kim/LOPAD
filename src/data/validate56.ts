/**
 * 56라운드 무기 데이터 검증 (gauge · issen · plunge · draw · 기력 groggyMs · 2단계 moves) — data/index.ts validateWeaponExtras 가 부른다.
 */
import type { WeaponDef } from './types';
import { validateMoves } from './validateMoves';

function num(v: unknown, path: string): void {
  if (typeof v !== 'number' || !Number.isFinite(v)) throw new Error(`[data] ${path} 는 숫자여야 합니다`);
}

function str(v: unknown, path: string): void {
  if (typeof v !== 'string' || !v) throw new Error(`[data] ${path} 는 문자열이어야 합니다`);
}

function nums(o: object, keys: readonly string[], path: string): void {
  for (const k of keys) num((o as Record<string, unknown>)[k], `${path}.${k}`);
}

const GAUGE_NUMERIC: Record<string, readonly string[]> = {
  kenki: ['stages', 'perStage', 'gainPerHit', 'parryGainStages', 'issenDamagePerStage', 'cloneAtStages'],
  grudge: ['max', 'blockGainMult', 'perfectMult', 'groggyMult', 'slamDamageBonus', 'slamRangeBonus'],
  brand: [
    'max',
    'perHit',
    'backGain',
    'backAngleDeg',
    'heatGainPerStage',
    'burstDamagePerMark',
    'overheatBurstRadiusTiles',
    'coolingSpeedMult',
    'coolingMoveMult',
    'lifeMs',
  ],
  breath: ['max', 'perfectGain', 'focusMs', 'focusTimeScale', 'focusPerfectWindowMult'],
};

export function validateWeapon56(w: WeaponDef, path: string): void {
  const r = w.resource;
  if (r?.kind === 'stamina' && r.groggyMs !== undefined) num(r.groggyMs, `${path}.resource.groggyMs`);
  const g = w.gauge;
  if (g) {
    const keys = GAUGE_NUMERIC[g.kind];
    if (!keys) throw new Error(`[data] ${path}.gauge.kind 알 수 없음`);
    str(g.label, `${path}.gauge.label`);
    nums(g, keys, `${path}.gauge`);
  }
  const i = w.issen;
  if (i) {
    nums(
      i,
      [
        'dashStartMs',
        'dashEndMs',
        'distancePx',
        'tilePx',
        'hitFromMs',
        'hitToMs',
        'hitBackPx',
        'hitExtraPx',
        'hitWidthPx',
      ],
      `${path}.issen`,
    );
    num(i.burstAtLineMs, `${path}.issen.burstAtLineMs`);
    if (!Array.isArray(i.lineSheets) || i.lineSheets.length === 0)
      throw new Error(`[data] ${path}.issen.lineSheets 는 비어 있지 않은 배열`);
    i.lineSheets.forEach((s, n) => str(s, `${path}.issen.lineSheets[${n}]`));
    if (typeof i.soloSuffix !== 'string') throw new Error(`[data] ${path}.issen.soloSuffix 없음`);
    str(i.shadow?.sheet, `${path}.issen.shadow.sheet`);
    nums(i.shadow, ['startAtMs', 'travelMs', 'hitAtMs', 'damageScale'], `${path}.issen.shadow`);
    if (!(i.dashEndMs > i.dashStartMs))
      throw new Error(`[data] ${path}.issen.dashEndMs 는 dashStartMs 보다 커야 합니다`);
  }
  const p = w.plunge;
  if (p) {
    str(p.art, `${path}.plunge.art`);
    nums(p, ['durationMs', 'hitAtMs', 'plantRadiusRatio', 'plantDamageMult'], `${path}.plunge`);
    str(p.wave?.sheet, `${path}.plunge.wave.sheet`);
    nums(p.wave, ['halfWidthPx', 'damageMult', 'travelMs'], `${path}.plunge.wave`);
    if (!Array.isArray(p.wave.lengthMultByStage) || p.wave.lengthMultByStage.length === 0)
      throw new Error(`[data] ${path}.plunge.wave.lengthMultByStage 는 숫자 배열`);
    p.wave.lengthMultByStage.forEach((v, n) => num(v, `${path}.plunge.wave.lengthMultByStage[${n}]`));
    str(p.crackRow, `${path}.plunge.crackRow`);
  }
  const d = w.draw;
  if (d) {
    nums(
      d,
      [
        'fullMs',
        'perfectWindowMs',
        'weakDamageMult',
        'perfectDamageMult',
        'strainAfterMs',
        'strainRampMs',
        'strainMinMult',
        'strainShakeDeg',
        'weakArrowTint',
        'releaseMs',
      ],
      `${path}.draw`,
    );
    str(d.weakArrowSheet, `${path}.draw.weakArrowSheet`);
    if (d.tapCancelMs !== undefined) num(d.tapCancelMs, `${path}.draw.tapCancelMs`);
  }
  if (g?.kind === 'brand' && g.backAfterShadowStepMs !== undefined)
    num(g.backAfterShadowStepMs, `${path}.gauge.backAfterShadowStepMs`);
  // 56라운드 2단계 새 기본기
  if (w.moves) validateMoves(w.moves, `${path}.moves`, w.combo?.art as Record<string, unknown> | undefined);
}
