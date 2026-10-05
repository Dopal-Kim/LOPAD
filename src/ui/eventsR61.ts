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
