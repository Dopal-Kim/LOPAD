/**
 * Game 씬 분리 모듈(50라운드 1단계)이 함께 쓰는 형식·작은 함수.
 * 씬 시작 데이터 · 판정 원점 · 연격 마지막 타 판정 · 주소 옵션 (60라운드: 옛 개성 경로 이펙트 고르기 pathFx 삭제 — 57 Q42).
 */
import { TILE } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PLAYER_HIT_ORIGIN_UP_PX } from '../../systems/weapon/playerScale';

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
  /** 61 단계 6 수련장 (씬 Training): 들어갈 방 id (없으면 지도 마당) */
  trainingRoom?: string;
  /** 61 단계 6: 수련장에서 맡겨 둔 런으로 돌아옴 (mode 'node') — 마친 노드면 출구가 열린 채로 */
  resume?: boolean;
};

/** 칸 → 월드 px (60라운드 6-1: 빌드·묶음 모듈이 따로 두던 같은 도우미를 하나로) */
export const T = (tiles: number): number => tiles * TILE;

/** 49라운드 회피 시험 보상 상한 (결정 49 Q2: 시작 감각 +0~3) */
export const SENSE_BONUS_MAX = 3;

/** 판정 원점 = 몸 중심 (발 위 10px, 48라운드 아트 메모 hitOrigin — 58라운드 Q2 주인공 그림 배율만큼 올라간다) */
export const HIT_ORIGIN_UP_PX = PLAYER_HIT_ORIGIN_UP_PX;

/**
 * 연격의 마무리 타(충격파·진화 베기 시점). 연격이 아니면 true, 대검 대쉬 공격은 false (49라운드: 충격파 없음).
 * 55라운드: 타별 데이터 `heavy` 가 있으면 그것 (칼 = 3타·잔상 베기, 대검 = 차지 내려찍기만 — Q30 연격 V 는 일반 타격)
 */
export function isFinisher(p: PlayerAttackPayload): boolean {
  if (p.dashSlash) return false;
  if (p.heavy !== undefined) return p.heavy;
  return p.comboIndex === undefined || p.comboIndex === (p.comboCount ?? 1) - 1;
}

/**
 * 55라운드 §17 판정 모양에 넘길 방향: 타별 모양(hitShape)이 있고 무기가 `leftTransform: rotate` 면 왼쪽도 회전만
 * (`facingAngle` 은 'left' 일 때만 반전하므로 'right' 를 넘긴다). 그 밖은 그대로 (48라운드 좌우 반전)
 */
export function shapeFacing<F extends string>(p: PlayerAttackPayload, facing: F): F | 'right' {
  return rotatesLeft(p) ? 'right' : facing;
}

/** 55라운드 Q28: 이 타는 왼쪽 조준을 180° 회전으로 그리고 판정한다 (타별 모양 + `leftTransform: rotate`) — 스파크도 바로 세우지 않음 */
export function rotatesLeft(p: PlayerAttackPayload): boolean {
  return Boolean(p.hitShape) && gameState.weapon.def.combo?.leftTransform === 'rotate';
}

/** 55라운드: 근접 연격 타(연격 번호가 있거나 차지 내려찍기) — 판정을 몸 판정 프레임(swingDelayMs)에, 위치는 그때 몸 */
export function isMeleeStrike(p: PlayerAttackPayload): boolean {
  return p.comboIndex !== undefined || p.charge !== undefined;
}

/**
 * 61라운드 계약 sound §9 `PLAYER_COMBO_FINISH`: 연격의 마지막 타인가 (대쉬 공격·차지·기본기 제외 — 연격 번호가 있고 마지막 번호)
 */
export function isComboFinish(p: PlayerAttackPayload): boolean {
  if (p.dashSlash || p.comboIndex === undefined || p.move) return false;
  return p.comboIndex === (p.comboCount ?? 1) - 1 && (p.comboCount ?? 1) > 1;
}

/** 주소 옵션 (`?debug`·`?nobirth` 등). 브라우저 밖(테스트)에서는 빈 값 */
export function urlParams(): URLSearchParams {
  if (typeof location === 'undefined') return new URLSearchParams();
  const own = new URLSearchParams(location.search);
  if (own.toString() !== '') return own;
  // 데모(아티팩트)는 주소 옵션을 못 넘기고 `#lab` 같은 해시 한 단어만 넘어온다 — 그 단어를 옵션 하나로 읽는다
  const hash = location.hash.replace(/^#/, '');
  if (/^[A-Za-z]+$/.test(hash)) return new URLSearchParams(hash);
  const demo = import.meta.env?.VITE_DEMO_QUERY;
  return demo ? new URLSearchParams(demo) : own;
}
