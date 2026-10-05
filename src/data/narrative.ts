/**
 * 61라운드 P8 서사 연결 데이터 (Phaser 의존 없음): 문장(`data/story.json` clues · weaponVoice · boss1 · nameSmudge — 스토리 팩
 * `parts/story/text-pack-61-stage1.json` 사본) + 시스템 수치·배치(`data/narrative.json`). 형식이 틀리면 부팅에서 바로 예외.
 */
import storyJson from '../../data/story.json';
import narrativeJson from '../../data/narrative.json';
import { WEAPONS } from './index';

/** 무기 한마디 장면 (런당 1회) */
export const VOICE_SCENES = ['pickup', 'firstKill', 'crisis', 'bossBefore', 'bossKill'] as const;
export type VoiceScene = (typeof VOICE_SCENES)[number];

export interface ClueText {
  lines: string[];
  /** 두 번째 생부터(일기장에 이 단서를 본 기록이 있을 때) 마지막 줄 대신 */
  repeatLast: string;
}

export interface Boss1Lines {
  speaker: string;
  intro: string;
  phase2: string;
  phase3: string;
  /** 파훼 종류(cup · pillar · cask · stumble) → 그 런에서 처음 일어났을 때 한 줄 */
  break: Record<string, string>;
  defeat: string;
}

/** 이름 번짐 (P7 덧쓰기) */
export interface NameSmudgeText {
  onDeath: string;
  returnFirst: string;
  diaryOpen: string;
  layers: string;
  prompt: string;
  actionSame: string;
  actionEdit: string;
  resultSame: string;
  resultChanged: string;
}

export interface NarrativeStory {
  clues: Record<string, ClueText>;
  weaponVoice: Record<string, Record<VoiceScene, string>>;
  boss1: Boss1Lines;
  nameSmudge: NameSmudgeText;
}

/** 서사 소품 (계약 art §23 — E 조사) */
export interface NarrativePropDef {
  clue: string;
  /** structures/v3 시트 id */
  sheet: string;
  /** 상호작용 안내 이름 */
  name: string;
  /** 놓는 노드 종류 (birth · post · boss) */
  node: string;
  /** 기준점: spawn = 주인공 시작 자리 · center = 전투장 가운데 */
  anchor: 'spawn' | 'center';
  /** 기준점에서 칸 */
  offset: [number, number];
  /** bossDied = 보스를 쓰러뜨린 뒤에 놓는다 */
  after?: 'bossDied';
}

export interface NarrativeData {
  voice: { crisisHpRatio: number; crisisHoldMs: number; bossKillDelayMs: number };
  props: NarrativePropDef[];
  diary: { pastLivesMax: number };
  ritual: { trialKey: string; trialPrompt: string; trialSkipped: string; namePrompt: string };
}

function fail(msg: string): never {
  throw new Error(`[data] ${msg}`);
}

const str = (v: unknown, at: string): string => {
  if (typeof v !== 'string' || !v) fail(`${at} 비어 있음`);
  return v;
};

export function validateNarrativeStory(s: NarrativeStory, weapons: readonly string[]): NarrativeStory {
  if (!s.clues || Object.keys(s.clues).length === 0) fail('story.clues 없음');
  for (const [id, c] of Object.entries(s.clues)) {
    if (!Array.isArray(c.lines) || c.lines.length === 0) fail(`story.clues.${id}.lines 비어 있음`);
    c.lines.forEach((l, i) => str(l, `story.clues.${id}.lines[${i}]`));
    str(c.repeatLast, `story.clues.${id}.repeatLast`);
  }
  for (const w of weapons) for (const sc of VOICE_SCENES) str(s.weaponVoice?.[w]?.[sc], `story.weaponVoice.${w}.${sc}`);
  for (const k of ['speaker', 'intro', 'phase2', 'phase3', 'defeat'] as const) str(s.boss1?.[k], `story.boss1.${k}`);
  for (const k of [
    'onDeath',
    'returnFirst',
    'diaryOpen',
    'layers',
    'prompt',
    'actionSame',
    'actionEdit',
    'resultSame',
    'resultChanged',
  ] as const)
    str(s.nameSmudge?.[k], `story.nameSmudge.${k}`);
  return s;
}

export function validateNarrative(d: NarrativeData, clues: Record<string, ClueText>): NarrativeData {
  const V = d.voice;
  if (!(V.crisisHpRatio > 0 && V.crisisHpRatio < 1)) fail('narrative.voice.crisisHpRatio 는 0..1');
  for (const k of ['crisisHoldMs', 'bossKillDelayMs'] as const)
    if (!(V[k] >= 0)) fail(`narrative.voice.${k} 는 0 이상`);
  const seen = new Set<string>();
  for (const p of d.props) {
    if (!clues[p.clue]) fail(`narrative.props: 단서 ${p.clue} 문장 없음 (story.clues)`);
    if (seen.has(p.clue)) fail(`narrative.props 중복 단서 ${p.clue}`);
    seen.add(p.clue);
    str(p.sheet, `narrative.props.${p.clue}.sheet`);
    str(p.name, `narrative.props.${p.clue}.name`);
    if (p.anchor !== 'spawn' && p.anchor !== 'center') fail(`narrative.props.${p.clue}.anchor 는 spawn | center`);
    if (!Array.isArray(p.offset) || p.offset.length !== 2) fail(`narrative.props.${p.clue}.offset 는 [x, y]`);
  }
  if (!(d.diary.pastLivesMax >= 1)) fail('narrative.diary.pastLivesMax 는 1 이상');
  for (const k of ['trialKey', 'trialPrompt', 'trialSkipped', 'namePrompt'] as const)
    str(d.ritual[k], `narrative.ritual.${k}`);
  return d;
}

export const NARRATIVE_STORY: NarrativeStory = validateNarrativeStory(
  storyJson as unknown as NarrativeStory,
  Object.keys(WEAPONS),
);
export const NARRATIVE: NarrativeData = validateNarrative(
  narrativeJson as unknown as NarrativeData,
  NARRATIVE_STORY.clues,
);

/** 무기 한마디 (없으면 '') */
export function voiceLine(weapon: string, scene: VoiceScene): string {
  return NARRATIVE_STORY.weaponVoice[weapon]?.[scene] ?? '';
}
