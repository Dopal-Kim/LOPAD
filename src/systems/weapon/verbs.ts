/**
 * 61라운드 P1 무기 4동사 표시 (Phaser 의존 없음): 좌 = 연격 · 우 = 시그니처 · 스페이스 = 대쉬(+대쉬 공격) · 좌 홀드 = 고유 자원 기술.
 * 이름·설명은 데이터 `weapons.<무기>.verbs`, 1단 갈래가 바꾼 칸은 그 노드의 `verbs` 가 덮는다(뒤 노드가 우선). 키캡 문자열은 Constants.
 * 스냅샷 `weaponVerbs`(계약 61라운드 추가) · 무기 시험장 메뉴 · 튜토리얼 안내가 쓴다.
 */
import { VERB_KEYS } from '../../core/Constants';
import type { WeaponDef, WeaponEvolution, WeaponVerbSlot } from '../../data/types';
import type { UiWeaponVerb, UiWeaponVerbs } from '../../contract/ui';

/** 칸 순서 (계약 고정) */
export const VERB_SLOTS: readonly WeaponVerbSlot[] = ['attack', 'signature', 'dash', 'hold'];

/** 이 무기·갈래 경로의 4동사 (갈래가 바꾼 칸은 branch = 갈래 이름) */
export function weaponVerbs(id: string, def: WeaponDef, nodes: readonly WeaponEvolution[]): UiWeaponVerbs {
  const verbs: UiWeaponVerb[] = VERB_SLOTS.map((slot) => {
    let d = def.verbs[slot];
    let branch: string | null = null;
    for (const n of nodes) {
      const o = n.verbs?.[slot];
      if (o) {
        d = o;
        branch = n.name;
      }
    }
    return { slot, key: VERB_KEYS[slot], name: d.name, hint: d.hint, branch };
  });
  return { weapon: id, verbs };
}

/** 한 줄 요약 (시험장 메뉴 detail — '좌 3연격 · 우 가드 · 패링 · …') */
export function verbsLine(v: UiWeaponVerbs): string {
  const short: Record<WeaponVerbSlot, string> = { attack: '좌', signature: '우', dash: 'Space', hold: '홀드' };
  return v.verbs.map((x) => `${short[x.slot]} ${x.name}`).join(' · ');
}
