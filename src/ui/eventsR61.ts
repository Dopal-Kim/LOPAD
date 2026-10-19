import { UI_EVENTS } from '../contract/ui';

/**
 * 61라운드 단계 2·3 이벤트 이름 — 시스템 C1(신규 적 소개)·D(보스 파훼)가 계약 `UI_EVENTS` 에 넣을 이벤트.
 * 계약 코드에 키가 생기면 그 값을, 아직 없으면 UI 가 기다리는 이름(계약 요청, parts/ui/README 61 단계 2·3 절)을 쓴다.
 */
function contractEvent(key: string, fallback: string): string {
  const v = (UI_EVENTS as Readonly<Record<string, string>>)[key];
  return typeof v === 'string' && v.length > 0 ? v : fallback;
}

export const R61_EVENTS = {
  /** 보스 파훼·결정타 `{ kind: 'cup'|'pillar'|'cask'|'stumble'|'finisher', label?, text? }` */
  BOSS_BREAK: contractEvent('BOSS_BREAK', 'ui:boss-break'),
  /** 신규 적 첫 등장 `{ id?, name, desc? }` */
  ENEMY_INTRO: contractEvent('ENEMY_INTRO', 'ui:enemy-intro'),
} as const;

/** P19 S1 자유 전투 반응 이벤트 (계약 free-combat §1 — 시스템이 `ui:` 접두로 중계, 페이로드는 월드 좌표) */
export const P19_EVENTS = {
  ENEMY_WALL_SLAM: contractEvent('ENEMY_WALL_SLAM', 'ui:enemy-wall-slam'),
  ENEMY_BOWLED: contractEvent('ENEMY_BOWLED', 'ui:enemy-bowled'),
  ENEMY_FELL: contractEvent('ENEMY_FELL', 'ui:enemy-fell'),
  HAZARD_EXPLODED: contractEvent('HAZARD_EXPLODED', 'ui:hazard-exploded'),
  COMBO_STREAK: contractEvent('COMBO_STREAK', 'ui:combo-streak'),
} as const;

/** P21 어두운 톤 · 잔혹 전투 (계약 dark-brutal §2 — 시스템이 `ui:` 로 중계, 처형 표식은 screen 포함) */
export const P21_EVENTS = {
  ENEMY_EXECUTABLE: contractEvent('ENEMY_EXECUTABLE', 'ui:enemy-executable'),
  PLAYER_EXECUTE: contractEvent('PLAYER_EXECUTE', 'ui:player-execute'),
  PLAYER_WOUNDED: contractEvent('PLAYER_WOUNDED', 'ui:player-wounded'),
  LOW_HP: contractEvent('LOW_HP', 'ui:low-hp'),
} as const;
