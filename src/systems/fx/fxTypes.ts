/**
 * FxPool 재생 옵션·훅 형식 (55라운드 6-1 정리 — fx.ts 에서 분리, 내용 그대로). Phaser 형식만 쓴다.
 */
import type Phaser from 'phaser';
import type { FxVariant } from './fxVariants';
import type { Facing, FxFlashSpec, FxShakeSpec, FxTrailSpec } from '../sprites/spriteDefs';

/** 따라갈 대상 (플레이어·투사체·적). 비활성화되면 이펙트도 멈춘다 */
export interface FxFollowTarget {
  x: number;
  y: number;
  active: boolean;
  depth: number;
  rotation: number;
}

export interface FxPlayOptions {
  /**
   * 시트의 행 이름: 4방향 · 56라운드 대각(8행 시트, 4행 시트면 가로 성분 행) · 크기(균열 s·m·l).
   * `directions: ["any"]` 시트는 무시된다
   */
  dir?: Facing | string;
  /** 투사체 앵커(`rotate: true`): 진행 각도(rad). 우향으로 그려졌으므로 그대로 회전 */
  angle?: number;
  /** 절대 깊이. follow 가 있고 depthOffset 이 있으면 대상 깊이 + 오프셋을 매 프레임 쓴다 */
  depth?: number;
  depthOffset?: number;
  follow?: FxFollowTarget;
  /** follow 대상 기준 오프셋 (몸 중심 등) */
  followOffset?: { x: number; y: number };
  /** follow 대상의 회전을 따른다 (관통 빛줄) */
  followRotation?: boolean;
  /** 루프 시트의 재생 시간. 없으면 follow 대상이 사라질 때까지 */
  durationMs?: number;
  /** 시트의 마지막 `tailFrames` 프레임만 루프 (잔월: 거합 4~6프레임 반복) */
  tailFrames?: number;
  /** 56라운드: 처음부터 한 번 재생한 뒤 이 열부터 끝까지 반복 (낙인 표식 찍힘 0~1 → 2~5 루프). 멈추려면 stop / follow 해제 */
  loopFrom?: number;
  /** 일회성 재생이 끝난 뒤 마지막 프레임을 이 시간만큼 유지하고 페이드 (피 바닥 얼룩) */
  holdLastMs?: number;
  /** 애니 대신 고정 프레임 (진행도 주도 aim_charge). `setFrame` 으로 바꾸고 `stop` 으로 끝낸다 */
  staticFrame?: number;
  /** 틴트 (dash_trail 무기 보조색). 없으면 원색 */
  tint?: number;
  /** true 면 `setTintFill`(평면 틴트 — 어두운 무채 시트용, JSON tint.method), 아니면 곱셈 `setTint` */
  tintFill?: boolean;
  /** JSON `trail` 이 따라갈 궤적 (베기 호 등). 없으면 스프라이트 위치(앵커가 player_pivot 이면 몸 중심) */
  trailSource?: () => { x: number; y: number } | null;
  /** false 면 JSON flash·shake·trail 훅을 쓰지 않는다 (달리기·워프 먼지처럼 반복·보조 재생) */
  hooks?: boolean;
  /**
   * true 면 깊이를 라이트맵 위 띠로 옮기지 않는다 (54라운드 Q26 불 웅덩이: `entityDepth(발 y)` 로 개체와 앞뒤 정렬).
   * 그림은 어둠에 잠기므로 밝기는 시트 광원(라이트맵)이 낸다
   */
  belowLighting?: boolean;
  /** 시트 배율에 곱하는 배율 (45라운드 달리기 먼지: dash_dust 를 작게). 기본 1 */
  scaleMult?: number;
  /** 시작 알파 (기본 1) */
  alpha?: number;
  /** 53라운드 계약 §10: 2단 갈래·가열 변주 (`resolveFxVariant`). 색 교체 텍스처·훅 덮어쓰기 */
  variant?: FxVariant | null;
  /** 55라운드 Q14 ①: 히트스톱 중 멈출 프레임 열 (판정 백열 · 적중 시트 holdFrame) */
  hitstopFrame?: number;
  /** 55라운드 Q23: 재생 배속 (대검 관성 — 몸과 같은 배속). 기본 1 */
  timeScale?: number;
  /** false 면 JSON trail 리본을 쓰지 않는다 (55라운드: 연격은 칼끝 리본을 SwingFx 가 따로 그린다) */
  trail?: boolean;
  /** 위아래 뒤집기 (적중 스파크 flipY) */
  flipY?: boolean;
  /** 56라운드 2단계: 좌우 뒤집기 (화살비 낙하 화살 `flipX: allowed`) */
  flipX?: boolean;
}

export interface FxHandle {
  readonly sprite: Phaser.GameObjects.Sprite;
  readonly token: number;
}

/** 리본 트레일 요청 (훅 인자) */
export interface FxTrailRequest {
  spec: FxTrailSpec;
  /** 위치 공급. null 이면 끝 */
  source: () => { x: number; y: number } | null;
  /** 이펙트 스프라이트 깊이 (리본은 바로 아래) */
  depth: number;
}

/** §3.2 필드를 바깥 시스템으로 넘기는 훅 (Game 이 등록) */
export interface FxHooks {
  shake?: (spec: FxShakeSpec) => void;
  flash?: (spec: FxFlashSpec) => void;
  /** 리본 트레일 시작. 반환: 샘플링 끝내기 */
  trail?: (req: FxTrailRequest) => (() => void) | null;
  /** 몸 중심 = 발 피벗에서 위로 px (player_pivot 앵커 트레일 기본 궤적) */
  bodyCenterUpPx?: number;
}
