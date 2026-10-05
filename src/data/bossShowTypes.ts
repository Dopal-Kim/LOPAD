/**
 * 61라운드 P6·점검 #5·#6: 보스 존재감·등장·처치 연출·대사·소등 가독성 데이터 형식 (data/bosses.json — 1층 '만취').
 * types.ts 의 BossDef·BossArenaParams 가 선택 필드로 붙는다. 검증은 `validateBossShow` (data/index.ts validateBosses 가 부른다).
 */
import type { BreakKind } from './bundle2Types';

/** 광원 한 벌 (월드 px, offsetY = 발에서 위로) */
export interface BossLightSpec {
  color: string;
  radius: number;
  intensity: number;
  flicker: number;
  offsetY?: number;
}

/** 등장 연출 (ms, 0 = 보스방 진입·보스 생성) */
export interface BossIntroShow {
  /** 카메라가 보스 쪽으로 옮겨 가는 시간 */
  panMs: number;
  /** 층 등장 자막(story floors.<층>.bossIntro) */
  floorLineAtMs: number;
  /** 보스 등장 대사(lines.intro) */
  speechAtMs: number;
  /** 카메라가 주인공으로 돌아가기 시작 · 걸리는 시간 */
  returnAtMs: number;
  returnMs: number;
  /** 전투 시작 (보스 패턴·입력 풀림) */
  fightAtMs: number;
}

/** 처치 연출 (ms, 0 = 마지막 일격) */
export interface BossDefeatShow {
  hitstopMs: number;
  /** 히트스톱 뒤 슬로모 길이(실시간) · 배속 (0~1) */
  slowMs: number;
  slowScale: number;
  /** 흰 섬광 · 흔들림 */
  flashMs: number;
  flashAlpha: number;
  shakePx: number;
  shakeMs: number;
  /** 카메라가 쓰러진 자리로 옮겨 가는 시간 */
  panMs: number;
  /** 쓰러짐 대사(lines.defeat) */
  speechAtMs: number;
  /** 대사 뒤 — 무기 한마디 자리(BOSS_FALLEN) */
  fallenAtMs: number;
  /** 보상 메뉴(감각 → 능력치 → 패시브) */
  rewardAtMs: number;
}

export interface BossShowDef {
  intro: BossIntroShow;
  defeat: BossDefeatShow;
}

/**
 * 보스 대사 (data/story.json `<linesKey>` — 스토리 텍스트 팩 boss1.*). break 은 파훼 종류별 그 런 첫 1회 —
 * 키는 스토리 이름(cup·pillar·cask·stumble), 파훼 종류(BreakKind)와 다른 것은 `BREAK_LINE_KEY` 로 잇는다
 */
export interface BossLines {
  speaker: string;
  intro?: string;
  phase2?: string;
  phase3?: string;
  break?: Record<string, string>;
  defeat?: string;
}

/** 파훼 종류 → 대사 키 (취권 넘어짐 reel = 스토리 stumble) */
export const BREAK_LINE_KEY: Record<BreakKind, string> = {
  cup: 'cup',
  pillar: 'pillar',
  cask: 'cask',
  reel: 'stumble',
};

/** 61라운드 등불 끄기 동안 주인공·보스에 붙는 최소 광원 */
export interface BossDarkLights {
  player?: BossLightSpec;
  boss?: BossLightSpec;
}

function num(v: unknown, path: string, min = 0): void {
  if (typeof v !== 'number' || Number.isNaN(v) || v < min) throw new Error(`[data] ${path} 는 ${min} 이상 숫자`);
}

function light(l: BossLightSpec | undefined, path: string): void {
  if (!l) return;
  if (typeof l.color !== 'string') throw new Error(`[data] ${path}.color 는 문자열`);
  for (const k of ['radius', 'intensity', 'flicker'] as const) num(l[k], `${path}.${k}`);
}

/** 61라운드 보스 연출 필드 검증 (없으면 통과) */
export function validateBossShow(
  b: {
    renderScale?: number;
    spawnOffsetTiles?: [number, number];
    breakDamageMult?: number;
    show?: BossShowDef;
    linesKey?: string;
    arena?: { darkLights?: BossDarkLights };
  },
  at: string,
): void {
  if (b.renderScale !== undefined) num(b.renderScale, `${at}.renderScale`, 0.1);
  if (b.breakDamageMult !== undefined) num(b.breakDamageMult, `${at}.breakDamageMult`, 1);
  if (b.spawnOffsetTiles !== undefined) {
    const o = b.spawnOffsetTiles;
    if (!Array.isArray(o) || o.length !== 2 || !o.every((v) => typeof v === 'number'))
      throw new Error(`[data] ${at}.spawnOffsetTiles 는 [dx, dy]`);
  }
  const s = b.show;
  if (s) {
    const I = s.intro;
    for (const k of ['panMs', 'floorLineAtMs', 'speechAtMs', 'returnAtMs', 'returnMs', 'fightAtMs'] as const)
      num(I?.[k], `${at}.show.intro.${k}`);
    if (I.fightAtMs < I.returnAtMs) throw new Error(`[data] ${at}.show.intro.fightAtMs 는 returnAtMs 뒤`);
    const D = s.defeat;
    for (const k of [
      'hitstopMs',
      'slowMs',
      'flashMs',
      'flashAlpha',
      'shakePx',
      'shakeMs',
      'panMs',
      'speechAtMs',
      'fallenAtMs',
      'rewardAtMs',
    ] as const)
      num(D?.[k], `${at}.show.defeat.${k}`);
    num(D.slowScale, `${at}.show.defeat.slowScale`, 0.05);
    if (D.slowScale > 1) throw new Error(`[data] ${at}.show.defeat.slowScale 는 1 이하`);
    if (!(D.speechAtMs <= D.fallenAtMs && D.fallenAtMs <= D.rewardAtMs))
      throw new Error(`[data] ${at}.show.defeat 순서: speechAtMs ≤ fallenAtMs ≤ rewardAtMs`);
  }
  if (b.linesKey !== undefined && typeof b.linesKey !== 'string') throw new Error(`[data] ${at}.linesKey 는 문자열`);
  const dl = b.arena?.darkLights;
  light(dl?.player, `${at}.arena.darkLights.player`);
  light(dl?.boss, `${at}.arena.darkLights.boss`);
}
