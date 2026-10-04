/** 공격 예고 공용 타입 (57라운드 B8: telegraph.ts 에서 분리). 설명은 `TelegraphFx.ts` 머리말 */
import type Phaser from 'phaser';

export type TelegraphKind = 'line' | 'circle' | 'cone';

export interface TelegraphOptions {
  /** 공격자 위치(선 시작·부채꼴 꼭짓점·원 중심)에 수렴 오라 (46라운드 Q3: 보스 예고 전부 + 결사병 돌진) */
  aura?: boolean;
  /** 오라를 마커와 다른 곳(공격자)에 둔다 (내리찍기: 원 = 착지점, 오라 = 보스). `aim()` 은 이 오라를 옮기지 않는다 */
  auraAt?: { x: number; y: number };
}

export interface TelegraphHandle {
  readonly kind: TelegraphKind | 'path';
  /** 위치·방향 갱신 (각도 rad, 선·부채꼴만 의미) */
  aim(x: number, y: number, angle?: number): void;
  /** 조기 종료 (경직·사망) */
  end(): void;
  readonly active: boolean;
}

/** 54라운드: 꺾은선·곡선 예고 (휘는 돌진·술통 튕김 경로·술 뿌리기). setPoints 로 예고 중 경로를 다시 그린다 */
export interface TelegraphPathHandle extends TelegraphHandle {
  setPoints(points: readonly { x: number; y: number }[]): void;
}

/** 층 램프 색 (화살촉 몸·테두리, 플레이스홀더 오라). `TelegraphFx.setFloor` 가 바꾸고 경로 예고와 함께 쓴다 */
export interface TelegraphStyle {
  tipColor: number;
  tipEdge: number;
}

/** 수렴 오라: 시트 스프라이트 또는 Graphics 원 */
export type AuraObject = Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;

export type Point = { x: number; y: number };

/** 활성 마커 요약 한 줄 (디버그) */
export interface TelegraphSummary {
  kind: TelegraphKind | 'path';
  x: number;
  y: number;
  angle: number;
  length: number;
  radius: number;
  sheet: boolean;
  remainingMs: number;
  final: boolean;
  frame: number | null;
  scale: number;
  closingRatio: number | null;
  tip: boolean;
  aura: string | null;
  alpha: number;
  points?: number;
}
