/**
 * 61라운드 단계 2 방 다양화: 세트 배치 템플릿 뒤집기 (Phaser 없음 · 순수). 좌표는 전투장 중앙 기준 [dx, dy] 라
 * 좌우 뒤집기 = dx → −dx, 상하 = dy → −dy. 고리 각도는 거울상(좌우 180−a · 상하 −a), 엄폐 모양 칸도 같이 뒤집는다.
 * 기둥(왼쪽 위 칸 + 크기)은 크기만큼 보정해 같은 칸을 덮게 한다.
 */
import type { SetPieceDef } from './setpiece';

type Vec = [number, number];

export interface Mirror {
  x: boolean;
  y: boolean;
}

const flipVec = (v: Vec, m: Mirror): Vec => [m.x ? -v[0] : v[0], m.y ? -v[1] : v[1]];

const flipAngle = (deg: number, m: Mirror): number => {
  let a = deg;
  if (m.x) a = 180 - a;
  if (m.y) a = -a;
  return ((a % 360) + 360) % 360;
};

/** 뒤집은 복사본 (뒤집기가 없으면 원본 그대로) */
export function mirrorSetPiece(t: SetPieceDef, m: Mirror): SetPieceDef {
  if (!m.x && !m.y) return t;
  const v = (p: Vec | undefined) => (p ? flipVec(p, m) : p);
  const ang = (a: number | undefined) => (a === undefined ? a : flipAngle(a, m));
  return {
    ...t,
    ...(t.slots ? { slots: t.slots.map((s) => ({ ...s, at: v(s.at), angle: ang(s.angle) })) } : {}),
    ...(t.decor ? { decor: t.decor.map((d) => ({ ...d, at: v(d.at), angle: ang(d.angle) })) } : {}),
    ...(t.cover
      ? {
          cover: {
            ...t.cover,
            anchors: t.cover.anchors.map((a) => flipVec(a, m)),
            shapes: t.cover.shapes.map((sh) => sh.map((c) => flipVec(c, m))),
          },
        }
      : {}),
    ...(t.pillars
      ? {
          pillars: t.pillars.map((p) => {
            const [w, h] = p.size ?? [1, 1];
            return {
              ...p,
              at: [m.x ? -p.at[0] - (w - 1) : p.at[0], m.y ? -p.at[1] - (h - 1) : p.at[1]] as Vec,
            };
          }),
        }
      : {}),
    ...(t.candles ? { candles: t.candles.map((c) => flipVec(c, m)) } : {}),
  };
}
