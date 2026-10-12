/**
 * 62 루프 2 시스템 C 사망 먹 번짐 방울 배치 (순수 — Phaser 의존 없음). 그리기는 `inkSmear`.
 */
import { GAME, INK_SMEAR } from '../../core/Constants';

export interface InkBlob {
  x: number;
  y: number;
  r: number;
  /** 0..1 진행 비에서 시작 */
  delay: number;
  lobes: { a: number; d: number; r: number }[];
}

export const easeOut = (t: number): number => 1 - Math.pow(1 - t, 3);

/** 화면 둘레 길이 d 의 점 (위 → 오른쪽 → 아래 → 왼쪽, 가장자리 바깥 20px) */
function edgePoint(d: number, W: number, H: number): [number, number] {
  if (d < W) return [d, -20];
  if ((d -= W) < H) return [W + 20, d];
  if ((d -= H) < W) return [W - d, H + 20];
  return [-20, H - (d - W)];
}

/** 방울 배치 (순수 — 시험용): center = 주인공 논리 화면 자리 · rnd ∈ [0,1) */
export function inkBlobs(center: { x: number; y: number }, rnd: () => number): InkBlob[] {
  const I = INK_SMEAR;
  const lobes = (): InkBlob['lobes'] =>
    Array.from({ length: I.LOBES }, (_, i) => ({
      a: (i / I.LOBES) * Math.PI * 2 + rnd() * 0.6,
      d: I.LOBE_DIST * (0.7 + rnd() * 0.5),
      r: I.LOBE_R * (0.6 + rnd() * 0.7),
    }));
  const out: InkBlob[] = [{ x: center.x, y: center.y, r: I.CENTER_R, delay: 0, lobes: lobes() }];
  const W = GAME.WIDTH;
  const H = GAME.HEIGHT;
  for (let i = 0; i < I.EDGE_SEEDS; i++) {
    // 화면 둘레를 고르게 돌며 가장자리 바깥쪽에 씨앗
    const t = (i + rnd() * 0.6) / I.EDGE_SEEDS;
    const per = 2 * (W + H);
    const [x, y] = edgePoint(t * per, W, H);
    out.push({
      x,
      y,
      r: I.EDGE_R_MIN + rnd() * (I.EDGE_R_MAX - I.EDGE_R_MIN),
      delay: I.EDGE_DELAY * (0.5 + rnd()),
      lobes: lobes(),
    });
  }
  return out;
}
