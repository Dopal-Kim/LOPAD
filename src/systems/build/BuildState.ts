/**
 * 57라운드 빌드 축 런 상태 (GameState.build — 런 시작에 새로, 세이브에 남음). Phaser 의존 없음.
 * 지금 저주 · 처치한 보스 최고 층 · 영구 보너스(불붙은 혀 상흔 +1·화상 10%, 피멍 자원 +30%) · 층당 1회 표시.
 * 61 G (P12): 이중 개성·최종 각성은 폐지 — 개성 카드·각성 단계는 무기 상태(`WeaponState.traits`·`path`).
 * 합산(`computeBuildMods`)은 런타임이 상태 서명이 바뀔 때만 다시 한다.
 */
import { BUILD, curseDef, setThresholdsOn, tagName, tagOn } from '../../data/build';
import type { FloorScope } from '../../data/floorScope';
import { TAG_IDS, type TagId } from '../../data/buildTypes';
import type { UiBuildState, UiCurse, UiTagState } from '../../contract/ui';
import type { PassiveSet } from '../passives';
import type { WeaponState } from '../weapon/weapons';
import { computeBuildMods, type BuildMods } from './buildMods';
import { CurseState, type CurseSave } from './curses';
import { nextThreshold } from './tagScore';

export interface BuildSave {
  curse: CurseSave | null;
  bossFloorCleared: number;
  permanentTags: Partial<Record<TagId, number>>;
  permanentBurnChance: number;
  resourceMaxBonus: number;
}

export class BuildState {
  curse: CurseState | null = null;
  /** 처치한 보스의 가장 높은 층 (1부터, 없으면 0) */
  bossFloorCleared = 0;
  permanentTags: Partial<Record<TagId, number>> = {};
  permanentBurnChance = 0;
  /** 피멍: 무기 자원 최대치 +비율 (영구) */
  resourceMaxBonus = 0;
  /** 층당 1회 (버팀 4 위기·버팀 6·마지막 잔) — 층 시작에 비움, 세이브 안 함 */
  readonly floorOnce = new Set<string>();
  /** 상태가 바뀔 때마다 +1 (합산 캐시 무효화) */
  version = 0;
  /**
   * 61라운드 P4 층 노출: 지금 층 (1부터 — 그 층에서 꺼진 태그·세트 단계는 세지 않는다). null = 제한 없음(시험장·검사 기본).
   * GameState 가 층 시작마다 넣는다 (`onFloorStart`)
   */
  floor: FloorScope = null;
  private cache: { sig: string; mods: BuildMods } | null = null;

  touch(): void {
    this.version += 1;
  }

  onFloorStart(floor?: FloorScope): void {
    this.floorOnce.clear();
    if (floor !== undefined) this.setFloor(floor);
  }

  /** 층 노출 범위 (null = 제한 없음 — 시험장) */
  setFloor(floor: FloorScope): void {
    if (this.floor === floor) return;
    this.floor = floor;
    this.touch();
  }

  /** 층당 1회 표시 — 처음이면 true (이번에 쓴 것으로 남긴다) */
  takeFloorOnce(key: string): boolean {
    if (this.floorOnce.has(key)) return false;
    this.floorOnce.add(key);
    return true;
  }

  /** 합산 (서명 — 상태 version · 패시브 · 갈래 경로 · 개성 — 이 같으면 캐시) */
  mods(passives: PassiveSet, weapon: WeaponState): BuildMods {
    const sig = `${this.version}|${this.floor}|${JSON.stringify(passives.owned)}|${weapon.id}|${weapon.path.join('/')}|${weapon.traits.join(',')}`;
    if (this.cache?.sig !== sig) this.cache = { sig, mods: this.compute(passives, weapon) };
    return this.cache.mods;
  }

  compute(passives: PassiveSet, weapon: WeaponState): BuildMods {
    return computeBuildMods({
      data: BUILD,
      passives,
      nodes: weapon.nodes,
      traits: weapon.traitDefs,
      curse: this.curse,
      permanentTags: this.permanentTags,
      floor: this.floor,
    });
  }

  toSave(): BuildSave {
    return {
      curse: this.curse ? this.curse.toSave() : null,
      bossFloorCleared: this.bossFloorCleared,
      permanentTags: { ...this.permanentTags },
      permanentBurnChance: this.permanentBurnChance,
      resourceMaxBonus: this.resourceMaxBonus,
    };
  }

  restore(s: Partial<BuildSave> | undefined): void {
    const cd = s?.curse ? curseDef(s.curse.id) : undefined;
    this.curse = cd && s?.curse ? CurseState.restore(cd, s.curse) : null;
    this.bossFloorCleared = Math.max(0, Number(s?.bossFloorCleared) || 0);
    this.permanentTags = {};
    for (const [k, v] of Object.entries(s?.permanentTags ?? {}))
      if ((TAG_IDS as readonly string[]).includes(k) && typeof v === 'number') this.permanentTags[k as TagId] = v;
    this.permanentBurnChance = Math.max(0, Number(s?.permanentBurnChance) || 0);
    this.resourceMaxBonus = Math.max(0, Number(s?.resourceMaxBonus) || 0);
    this.floorOnce.clear();
    this.touch();
  }
}

/** 계약 §14.3 */
export function uiCurse(c: CurseState): UiCurse {
  return {
    id: c.id,
    name: c.def.name,
    benefit: c.def.benefit,
    penalty: c.def.penalty,
    nodesLeft: c.nodesLeft,
    killsLeft: c.killsLeft,
  };
}

/**
 * 계약 §14.1 태그 상태 (score > 0 만, 점수 높은 순 — 같으면 태그 순서). 61라운드 P4: 층에서 꺼진 태그는 빼고,
 * 세트 효과는 그 층에서 켜진 단계만 (1층판 = 2·4 두 칸, 4 달성이면 next null)
 */
export function uiTags(mods: BuildMods, floor: FloorScope = null): UiTagState[] {
  return TAG_IDS.filter((t) => mods.scores[t] > 0 && tagOn(t, floor))
    .sort((a, b) => mods.scores[b] - mods.scores[a] || TAG_IDS.indexOf(a) - TAG_IDS.indexOf(b))
    .map((t) => {
      const T = setThresholdsOn(t, floor);
      return {
        id: t,
        name: tagName(t),
        score: mods.scores[t],
        stage: mods.stages[t],
        next: nextThreshold(mods.scores[t], T),
        effects: BUILD.sets[t]
          .filter((st) => T.includes(st.threshold))
          .map((st) => ({
            threshold: st.threshold,
            name: st.name,
            description: st.description,
            active: mods.stages[t] >= st.threshold,
          })),
      };
    });
}

export function uiBuild(mods: BuildMods, state: BuildState): UiBuildState {
  return {
    tags: uiTags(mods, state.floor),
    // 61 G (§18): 이중 개성 폐지 — 개성은 UiSnapshot.growth.traits
    dualTraits: [],
    curse: state.curse ? uiCurse(state.curse) : null,
  };
}
