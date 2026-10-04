/**
 * 55라운드 Q7 칼끝 리본의 위치 공급 (SwingFx 에서 분리): 무기 v3 시트 `bladeTipAnchors`(방향 → 열별 칼끝 도트)를
 * 몸 연격의 실제 프레임 시작에 얹어 플레이 시계 t 의 칼끝 월드 좌표를 낸다. 칼끝 메모가 없으면(칼 v3) 판정 호 위를 훑는다.
 */
import { FEEL } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { arcTipAt, swingWindow, tipAt, type TipTrack, type Vec } from '../../systems/weapon/bladeTipMath';
import { facingAngle, rotateDir, type HitShape } from '../../systems/weapon/hitShapes';
import { overlayPivot } from '../../systems/sprites/spriteMeta';
import { gameState } from '../../core/GameState';
import { overlayArtCandidates } from '../../systems/weapon/comboArt';
import { spriteLibrary } from '../../systems/sprites/sprites';
import {
  animDurationMs,
  artScale,
  frameStarts,
  overlayActionsFor,
  type Facing,
} from '../../systems/sprites/spriteDefs';
import { HIT_ORIGIN_UP_PX, shapeFacing } from './shared';

/** 칼끝 리본 계획: 찍는 구간(공격 시작부터 ms) + 시각(공격 시작부터 ms) → 발 피벗 기준 칼끝 오프셋 */
export interface TipPlan {
  from: number;
  to: number;
  at: (elapsedMs: number) => Vec | null;
  /** 디버그: 칼끝 메모(anchors) 또는 판정 호(arc) */
  mode: 'anchors' | 'arc';
}

function isPoint(v: unknown): v is [number, number] {
  return Array.isArray(v) && typeof v[0] === 'number' && typeof v[1] === 'number';
}

/** 무기 오버레이 시트의 칼끝 메모로 만든 궤적 (없으면 null) */
function anchorTrack(
  weaponId: string,
  bodyAction: string,
  dir: Facing,
  starts: number[],
  total: number,
): TipTrack | null {
  const body = spriteLibrary.sheet('player', bodyAction);
  const combo = gameState.weapon.def.combo;
  for (const a of overlayActionsFor(bodyAction, weaponId, (r) => overlayArtCandidates(combo, r))) {
    const def = spriteLibrary.sheet(weaponId, a);
    if (!def) continue;
    const list = def.bladeTipAnchors?.[dir];
    if (!Array.isArray(list) || list.length === 0) return null;
    const pv = overlayPivot(def, body);
    const k = artScale(def);
    const tips = starts.map((_, c) => {
      const p = list[Math.min(c, list.length - 1)];
      return isPoint(p) ? { x: (p[0] - pv.x) * k, y: (p[1] - pv.y) * k } : null;
    });
    return { starts, total, tips, center: { x: 0, y: -HIT_ORIGIN_UP_PX } };
  }
  return null;
}

/**
 * 칼끝 리본 계획. `shape` = 판정 모양(호 폴백), `tipRadius` = 칼끝 반경(월드, 아트 trailFill — 없으면 판정 반경 × 비율)
 */
export function planBladeTip(
  p: PlayerAttackPayload,
  weaponId: string,
  dir: Facing,
  shape: HitShape | null,
  tipRadius: number | null,
): TipPlan | null {
  const body = p.bodyAction ? spriteLibrary.sheet('player', p.bodyAction) : undefined;
  const starts =
    p.bodyFrameStartsMs && p.bodyFrameStartsMs.length > 0 ? p.bodyFrameStartsMs : body ? frameStarts(body) : [];
  const total = p.durationMs ?? (body ? animDurationMs(body) : 0);
  const R = FEEL.RIBBON;
  const win = swingWindow(starts, total, body?.activeFrames ?? body?.hitFrames, R.LEAD_FRAMES, R.TAIL_FRAMES) ?? {
    from: Math.max(0, p.swingDelayMs - R.LIFE_MS / 2),
    to: p.swingDelayMs + (p.activeMs ?? R.LIFE_MS),
  };
  const track = p.bodyAction ? anchorTrack(weaponId, p.bodyAction, dir, starts, total) : null;
  if (track) return { ...win, mode: 'anchors', at: (t) => tipAt(track, t) };
  if (!shape || shape.kind === 'ring') return null;
  // 55라운드: 새 연격(rotate 무기)은 왼쪽도 회전만 — 판정과 같은 규칙
  const sf = shapeFacing(p, dir);
  const center = { x: 0, y: -HIT_ORIGIN_UP_PX };
  const base = Math.atan2(p.dirY, p.dirX);
  const span = Math.max(1, win.to - win.from);
  if (shape.kind === 'thrust' || shape.kind === 'wedge') {
    // 찌르기 = 몸에서 앞으로, 55라운드 내려찍기 쐐기 = 몸 가까이에서 끝점으로 (세로로 선 칼날이 앞으로 떨어짐)
    const thrust = shape.kind === 'thrust';
    const d = rotateDir(p.dirX, p.dirY, facingAngle(thrust ? shape.angleDeg : shape.centerDeg, sf));
    const r0 = thrust ? shape.fromPx : shape.length * R.WEDGE_START_RATIO;
    const r1 = thrust ? shape.fromPx + shape.length : shape.length;
    return {
      ...win,
      mode: 'arc',
      at: (t) => {
        const r = r0 + (r1 - r0) * Math.min(1, (t - win.from) / span);
        return { x: center.x + d.x * r, y: center.y + d.y * r };
      },
    };
  }
  // 리본이 훑는 방향은 몸 시트 메모(arcFromDeg→arcToDeg, 그린 휘두름)를 따른다 — 범위는 판정 호 (칼 3타: 판정·그림 모두 −75→+75, Q26)
  const drawnFrom = body?.arcFromDeg;
  const drawnTo = body?.arcToDeg;
  const flip =
    typeof drawnFrom === 'number' && typeof drawnTo === 'number' && drawnTo - drawnFrom !== 0
      ? Math.sign(drawnTo - drawnFrom) !== Math.sign(shape.toDeg - shape.fromDeg)
      : false;
  const deg = Math.PI / 180;
  const from = base + facingAngle(flip ? shape.toDeg : shape.fromDeg, sf) * deg;
  const to = base + facingAngle(flip ? shape.fromDeg : shape.toDeg, sf) * deg;
  const r = tipRadius ?? shape.radius * R.FALLBACK_RADIUS_RATIO;
  return { ...win, mode: 'arc', at: (t) => arcTipAt(center, r, from, to, (t - win.from) / span) };
}
