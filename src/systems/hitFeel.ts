/**
 * 55라운드 적중 반응 규칙 (Q6 히트스톱 · Q8 스파크·흔들림 · Q10 막타 기준, 계약 §16). Phaser 의존 없음.
 * - 막타 = 연격 마지막 타 · 대쉬 공격(마무리) · 치명타 → `hit_<무기>_heavy`, 히트스톱 × HEAVY_MULT, 흔들림
 * - 일반 적중 = `hit_<무기>` (없으면 기존 hit_burst), 흔들림은 대검(shakeEveryHit)만
 */
import { FEEL } from '../core/Constants';
import type { WeaponFeelDef } from '../data/types';

/** 막타 판정에 필요한 공격 페이로드 필드 */
export interface StrikeShape {
  kind: string;
  comboIndex?: number;
  comboCount?: number;
}

/** Q10: 연격 마지막 타 또는 대쉬 공격 (치명타는 굴린 뒤 따로 더한다) */
export function isHeavyStrike(p: StrikeShape): boolean {
  if (p.kind === 'dashAttack') return true;
  return p.comboIndex !== undefined && p.comboCount !== undefined && p.comboIndex === p.comboCount - 1;
}

/** Q6: 무기 히트스톱 ms (막타·치명타 ×HEAVY_MULT) */
export function weaponHitstopMs(feel: Pick<WeaponFeelDef, 'hitstopMs'> | undefined, heavy: boolean): number {
  const base = feel && feel.hitstopMs > 0 ? feel.hitstopMs : FEEL.HITSTOP.WEAPON_FALLBACK_MS;
  return Math.round(base * (heavy ? FEEL.HITSTOP.HEAVY_MULT : 1));
}

/** 적중 스파크 시트: 막타면 `hit_<무기>_heavy` → `hit_<무기>`, 아니면 `hit_<무기>`. 로드된 것이 없으면 null (호출 쪽 hit_burst) */
export function weaponHitSheet(weaponId: string, heavy: boolean, has: (id: string) => boolean): string | null {
  const base = `${FEEL.FX_IDS.WEAPON_HIT_PREFIX}${weaponId}`;
  const heavyId = `${base}${FEEL.FX_IDS.WEAPON_HIT_HEAVY_SUFFIX}`;
  if (heavy && has(heavyId)) return heavyId;
  return has(base) ? base : null;
}

/** Q8: 흔들림은 막타·치명타, 그리고 대검(모든 적중) */
export function shakesOnHit(feel: Pick<WeaponFeelDef, 'shakeEveryHit'> | undefined, heavy: boolean): boolean {
  return heavy || Boolean(feel?.shakeEveryHit);
}

/** 흔들림 값: 적중 시트 `shakeHint`(아트 제안) → 없으면 FEEL.SHAKE.HEAVY_HIT */
export function hitShake(def: { shakeHint?: unknown } | null | undefined): { px: number; ms: number } {
  const h = def?.shakeHint as { px?: unknown; ms?: unknown } | undefined;
  if (h && typeof h.px === 'number' && typeof h.ms === 'number' && h.px > 0 && h.ms > 0) return { px: h.px, ms: h.ms };
  return { px: FEEL.SHAKE.HEAVY_HIT.PX, ms: FEEL.SHAKE.HEAVY_HIT.MS };
}

const FACING_ANGLE: Record<string, number> = { right: 0, down: Math.PI / 2, left: Math.PI, up: -Math.PI / 2 };

/**
 * 회전 스파크 방향 (계약 §16 rotate·drawnFacing·flipY): 각도 = 공격 진행 방향 − 그린 방향.
 * 왼쪽으로 돌면 그림이 뒤집히므로 flipY 로 바로 세우고, 연격 짝수 번째 타(되돌아 휘두름)는 한 번 더 뒤집는다 (flipY 허용 시트만)
 */
export function sparkOrientation(
  dirX: number,
  dirY: number,
  opts: { drawnFacing?: string; flipAllowed?: boolean; backswing?: boolean } = {},
): { angle: number; flipY: boolean } {
  const angle = Math.atan2(dirY, dirX) - (FACING_ANGLE[opts.drawnFacing ?? 'right'] ?? 0);
  if (!opts.flipAllowed) return { angle, flipY: false };
  return { angle, flipY: dirX < 0 !== Boolean(opts.backswing) };
}

/**
 * 되돌아 휘두름 = 판정 호가 반대 방향으로 훑는 타 (fromDeg → toDeg 가 줄어듦). 찌르기·원형은 아님.
 * 타마다 판정 모양이 데이터(시트 메모·combo)로 바뀌어도 그 모양에서 읽는다 — 홀짝 규칙을 하드코딩하지 않는다
 */
export function isBackswing(
  shape: { kind: string; fromDeg?: number; toDeg?: number; arcDeg?: number } | null,
): boolean {
  if (!shape || shape.kind !== 'arc' || (shape.arcDeg ?? 0) >= 360) return false;
  return typeof shape.fromDeg === 'number' && typeof shape.toDeg === 'number' && shape.toDeg < shape.fromDeg;
}
