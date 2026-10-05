/**
 * 61라운드 단계 4 P12 무기 성장 데이터 형식 (`data/growth.json` · `data/traits.json`). Phaser 의존 없음.
 * 갈래·길 id 는 art §26 (화면·그림 공용), node 는 weapons.json 갈래 트리의 시스템 노드 id.
 */
import type { RuleDef, TagId } from './buildTypes';
import type { WeaponVerbSlot } from './types';

/** 눈금 종류: ◇ 개성 발현 · ◆ 1차 각성 · ◆ 2차 각성 · 단련(단련 또는 개성) */
export type GrowthMarkKind = 'trait' | 'awaken1' | 'awaken2' | 'temper';
export const GROWTH_MARK_KINDS: readonly GrowthMarkKind[] = ['trait', 'awaken1', 'awaken2', 'temper'];

export interface GrowthMarkDef {
  at: number;
  kind: GrowthMarkKind;
}

/** 2차 길 */
export interface GrowthPathDef {
  id: string;
  node: string;
  name: string;
  /** 한 줄 양상 (수치·내부 용어 없음) */
  line: string;
  verb: WeaponVerbSlot;
  /** 길 강조색 [r,g,b] (art §26 pathTint — 2차 외형 glow·휘두름 궤적·연출 fx) */
  tint: [number, number, number];
}

/** 1차 갈래 */
export interface GrowthBranchDef {
  id: string;
  node: string;
  name: string;
  line: string;
  /** 1차 각성 때 바뀌는 칸 */
  verb: WeaponVerbSlot;
  /** 셋째 갈래 = 옛 최종 각성 모양·궤적(`_awaken`)을 1차 모양으로 재사용 (art §26) */
  legacyLook?: boolean;
  paths: [GrowthPathDef, GrowthPathDef];
}

export interface GrowthData {
  /** 층(1부터 문자열) → 눈금. 표에 없는 층은 가장 가까운 아래 층 */
  marks: Record<string, GrowthMarkDef[]>;
  /** 마지막 눈금 뒤 단련 눈금 간격 */
  repeatEvery: number;
  gain: { normalKillMult: number };
  temper: { max: number; damageBonus: number; rangeBonus: number; name: string; line: string };
  traitChoices: number;
  awaken: {
    pauseMs: Record<'1' | '2', number>;
    fx: Record<'1' | '2', string>;
  };
  text: Record<string, string>;
  weapons: Record<string, { branches: GrowthBranchDef[] }>;
}

/** 개성 카드 */
export interface TraitDef {
  id: string;
  weapon: string;
  verb: WeaponVerbSlot;
  tag: TagId;
  /** 1차 갈래 id (그 갈래를 고른 뒤에만 나온다) */
  branch?: string;
  name: string;
  /** 조건 → 행동 변화 한 문장 */
  line: string;
  effect: RuleDef;
}
