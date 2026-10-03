/**
 * Game 씬 분리 모듈(50라운드 1단계)이 함께 쓰는 형식·작은 함수.
 * 씬 시작 데이터 · 판정 원점 · 연격 마지막 타 판정 · 개성 경로 이펙트 고르기 · 주소 옵션.
 */
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { FxPool } from '../../systems/fx';

/**
 * mode 'floor' = 디버그·검증용 층 이동 (47라운드, 세이브 없음) · 'node' = 같은 층 안 다음 노드 (48라운드).
 * 49라운드: senseBonus = 회피 시험 등급 보상(시작 감각 +0~3, 새 런만) · labWeapon·labMenu = 무기 시험장 재시작 시 무기·열 메뉴
 */
export type GameInitData = {
  mode?: 'new' | 'next' | 'floor' | 'node';
  weapon?: string;
  playerName?: string;
  floor?: number;
  senseBonus?: number;
  labWeapon?: string;
  labMenu?: 'lab' | 'labBranch';
  /** 50라운드 시범 확인: 이 지역(route.json regions id, 예: 'outer')의 전투 노드로 바로 (`?slice=outer`, 새 런만) */
  slice?: string;
  /** 54라운드 `?boss`·`?bossPhase`·`?bossPattern`: 새 런으로 이 층 보스 노드에 바로 (보스 확인용) */
  bossJump?: boolean;
};

/** 49라운드 회피 시험 보상 상한 (결정 49 Q2: 시작 감각 +0~3) */
export const SENSE_BONUS_MAX = 3;

/** 판정 원점 = 몸 중심 (발 위 10px, 48라운드 아트 메모 hitOrigin) */
export const HIT_ORIGIN_UP_PX = 10;

/** 연격의 마지막 타(충격파·진화 베기 시점). 연격이 아니면 true, 대검 대쉬 공격은 false (49라운드: 충격파 없음) */
export function isFinisher(p: PlayerAttackPayload): boolean {
  if (p.dashSlash) return false;
  return p.comboIndex === undefined || p.comboIndex === (p.comboCount ?? 1) - 1;
}

/**
 * 현재 개성 경로에 있고 시트가 로드된 첫 후보 id. 2차 노드를 앞에, 그것이 대신하는 1차 노드를 뒤에 적는다
 * (예: `pathFx(fx, 'wide', 'iai')` = 만월이 있으면 만월, 아니면 거합). 아무것도 없으면 null → 호출 쪽 플레이스홀더
 */
export function pathFx(fx: FxPool, ...candidates: string[]): string | null {
  const path = gameState.weapon.path;
  for (const id of candidates) if (path.includes(id) && fx.has(id)) return id;
  return null;
}

/** 1차 진화 이펙트 id = 경로의 첫 노드. 시트가 없으면 null (질풍·발도술 루프 판정용) */
export function evolutionFxId(fx: FxPool): string | null {
  const first = gameState.weapon.path[0];
  return first && fx.has(first) ? first : null;
}

/** 주소 옵션 (`?debug`·`?nobirth` 등). 브라우저 밖(테스트)에서는 빈 값 */
export function urlParams(): URLSearchParams {
  if (typeof location === 'undefined') return new URLSearchParams();
  const own = new URLSearchParams(location.search);
  const demo = import.meta.env?.VITE_DEMO_QUERY;
  return demo && own.toString() === '' ? new URLSearchParams(demo) : own;
}
