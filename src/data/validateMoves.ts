/**
 * 56라운드 2단계 새 기본기 데이터 검증 (data/weapons.json `moves` — 형식은 `moveTypes`). validateWeaponKit 이 부른다.
 */
import type { MoveTravelDef, MoveStrikeDef, WeaponMovesDef } from './moveTypes';
import { validateHit, validateHitShape } from './validateCombo';
import { num, nums, str } from './validateUtil';

function numList(v: unknown, path: string, minLen = 1): void {
  if (!Array.isArray(v) || v.length < minLen) throw new Error(`[data] ${path} 는 숫자 배열 (${minLen}개 이상)`);
  v.forEach((x, i) => num(x, `${path}[${i}]`));
}

function travel(t: MoveTravelDef | undefined, path: string): void {
  if (!t) throw new Error(`[data] ${path} 없음`);
  nums(t, ['px', 'fromMs', 'ms'], path);
  if (t.ms <= 0) throw new Error(`[data] ${path}.ms 는 0 보다 커야 합니다`);
  if (t.easing !== undefined && t.easing !== 'linear' && t.easing !== 'easeOut')
    throw new Error(`[data] ${path}.easing 은 linear·easeOut`);
}

function strike(m: MoveStrikeDef, path: string, art: Record<string, unknown> | undefined): void {
  str(m.art, `${path}.art`);
  if (art && !(m.art in art)) throw new Error(`[data] ${path}.art '${m.art}' 이 combo.art 표에 없음`);
  validateHit(m.hit, `${path}.hit`, art);
  if (m.staminaCost !== undefined) num(m.staminaCost, `${path}.staminaCost`);
}

export function validateMoves(m: WeaponMovesDef, path: string, art: Record<string, unknown> | undefined): void {
  if (m.thrust?.lunge) travel(m.thrust.lunge, `${path}.thrust.lunge`);
  if (m.issenDash) strike(m.issenDash, `${path}.issenDash`, art);
  if (m.counter) {
    strike(m.counter, `${path}.counter`, art);
    num(m.counter.windowMs, `${path}.counter.windowMs`);
    travel(m.counter.sidestep, `${path}.counter.sidestep`);
  }
  if (m.iai) {
    strike(m.iai, `${path}.iai`, art);
    num(m.iai.holdMs, `${path}.iai.holdMs`);
    num(m.iai.readyAfterHoldMs, `${path}.iai.readyAfterHoldMs`);
    str(m.iai.readyFx, `${path}.iai.readyFx`);
    nums(m.iai.release, ['hitMs', 'activeMs', 'clickMs', 'totalMs'], `${path}.iai.release`);
    if (!(m.iai.release.hitMs < m.iai.release.totalMs))
      throw new Error(`[data] ${path}.iai.release.hitMs 는 totalMs 보다 작아야 합니다`);
  }
  if (m.tackle) {
    strike(m.tackle, `${path}.tackle`, art);
    travel(m.tackle.dash, `${path}.tackle.dash`);
    num(m.tackle.carryExtraPx, `${path}.tackle.carryExtraPx`);
  }
  if (m.brace) {
    const b = m.brace;
    strike(b, `${path}.brace`, art);
    nums(b, ['windowMs', 'superArmorMs', 'rageMinRatio'], `${path}.brace`);
    str(b.rageArt, `${path}.brace.rageArt`);
    if (art && !(b.rageArt in art))
      throw new Error(`[data] ${path}.brace.rageArt '${b.rageArt}' 이 combo.art 표에 없음`);
    validateHitShape(b.rageHitShape, `${path}.brace.rageHitShape`);
    str(b.absorbFx, `${path}.brace.absorbFx`);
  }
  if (m.leap) {
    const l = m.leap;
    strike(l, `${path}.leap`, art);
    travel(l.leap, `${path}.leap.leap`);
    num(l.lengthMult, `${path}.leap.lengthMult`);
    if (l.crackRow !== undefined) str(l.crackRow, `${path}.leap.crackRow`);
    nums(l.landingRing, ['radiusMult', 'damageMult'], `${path}.leap.landingRing`);
    str(l.spiralFx, `${path}.leap.spiralFx`);
    if (typeof l.consumesGrudge !== 'boolean') throw new Error(`[data] ${path}.leap.consumesGrudge 는 true·false`);
  }
  if (m.backstab) strike(m.backstab, `${path}.backstab`, art);
  if (m.flurry) {
    const f = m.flurry;
    strike(f, `${path}.flurry`, art);
    nums(f, ['holdMs', 'tempoPerStab', 'moveMult'], `${path}.flurry`);
    numList(f.heatBounds, `${path}.flurry.heatBounds`, 0);
    if (!Array.isArray(f.heatFx) || f.heatFx.length !== f.heatBounds.length + 1)
      throw new Error(`[data] ${path}.flurry.heatFx 는 heatBounds 수 + 1 개`);
    f.heatFx.forEach((n, i) => str(n, `${path}.flurry.heatFx[${i}]`));
  }
  if (m.arrowRain) {
    const a = m.arrowRain;
    str(a.art, `${path}.arrowRain.art`);
    nums(
      a,
      [
        'holdMs',
        'durationMs',
        'ammoCost',
        'markRadiusPx',
        'drops',
        'dropIntervalMs',
        'firstDropAtMs',
        'dropRadiusPx',
        'damageMult',
      ],
      `${path}.arrowRain`,
    );
    numList(a.releasesAtMs, `${path}.arrowRain.releasesAtMs`);
    if (
      a.cancelFromMs !== undefined &&
      !(a.cancelFromMs >= Math.max(0, ...a.releasesAtMs) && a.cancelFromMs <= a.durationMs)
    )
      throw new Error(`[data] ${path}.arrowRain.cancelFromMs 는 마지막 발사 ~ durationMs 사이`);
    for (const k of ['markRow', 'riseFx', 'markFx', 'fallFx'] as const) str(a[k], `${path}.arrowRain.${k}`);
  }
}
