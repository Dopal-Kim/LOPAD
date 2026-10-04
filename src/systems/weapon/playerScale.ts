/**
 * 58라운드 Q2 주인공·무기 그림 배율 (data/player.json `drawScale` — 캐릭터·무기만 약 1.25배, 타일·맵·적 그대로). Phaser 의존 없음.
 * - render: 주인공 몸·무기 오버레이·검기/울분 오버레이·상흔·주인공에 붙는 fx·판정 원점 높이(몸 중심 = 발 위 HIT_ORIGIN_BASE_PX × render)
 * - hit: 근접 무기 판정 크기 배율 (그림 대비 같은 비율 = render 와 같게, 기존 판정 유지 = 1) — 갈래·강화 배율과 곱한다
 * 이동 충돌(player.size)·대쉬 거리·이동 속도는 그대로.
 */
import { PLAYER_DATA } from '../../data';
import type { WeaponState } from './weapons';

/** 주인공 그림 배율 (몸·무기·붙는 fx) */
export const PLAYER_RENDER_SCALE = PLAYER_DATA.drawScale?.render ?? 1;
/** 근접 무기 판정 크기 배율 */
export const PLAYER_HIT_SCALE = PLAYER_DATA.drawScale?.hit ?? 1;

/** 판정 원점 높이 기준 (월드 px, 배율 1 — 아트 '피벗 위 40 도트' 53라운드 Q70) */
export const HIT_ORIGIN_BASE_PX = 10;

/** 판정 원점 = 발 위 이만큼 (몸 그림 배율만큼 올라간다) */
export const PLAYER_HIT_ORIGIN_UP_PX = HIT_ORIGIN_BASE_PX * PLAYER_RENDER_SCALE;

/** 갈래·강화 판정 배율 (현재 reach / 기본 reach) × 근접 무기면 주인공 판정 배율 */
export function weaponRangeScale(w: Pick<WeaponState, 'def' | 'hitbox'>): number {
  const base = w.def.hitbox.reach > 0 ? w.hitbox.reach / w.def.hitbox.reach : 1;
  return base * (w.def.kind === 'melee' ? PLAYER_HIT_SCALE : 1);
}
