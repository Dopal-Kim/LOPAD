/**
 * 57라운드 A2: 씬 시작이 쓸 런 무기를 create 전(preload)에 안다 — 그 무기 시트만 로드하려고.
 * 규칙은 create 의 `Progression.prepareRun`·`LabMode.prepareRun` 과 같다 (둘 다 여기 함수를 쓴다).
 */
import { gameState } from '../../core/GameState';
import { PLAYER_DATA, WEAPONS } from '../../data';
import type { SaveData, SaveSlot } from '../../systems/save';
import { urlParams, type GameInitData } from './shared';

const valid = (id: string | null | undefined): string | null => (id && WEAPONS[id] ? id : null);

/** 이어하기 세이브 (`?new`·`?seed` 면 없음) */
export function continueSave(slot: SaveSlot): SaveData | null {
  const params = urlParams();
  return params.has('new') || params.has('seed') ? null : slot.read();
}

/** 시험장 무기: 고른 무기 → 지금 무기 → 시작 무기 */
export function labWeaponFor(init: Pick<GameInitData, 'labWeapon'>): string {
  return valid(init.labWeapon ?? gameState.weapon?.id) ?? PLAYER_DATA.startWeapon;
}

/** 이 씬 시작의 런 무기 (새 런 = 고른 무기 · 같은 런의 노드·층 = 지금 무기 · 이어하기 = 세이브 무기 · 그 밖 = 시작 무기) */
export function runWeaponFor(init: GameInitData, lab: boolean, slot: SaveSlot): string {
  if (lab) return labWeaponFor(init);
  switch (init.mode) {
    case 'new':
      return valid(init.weapon) ?? PLAYER_DATA.startWeapon;
    case 'node':
    case 'next':
    case 'floor':
      return gameState.weapon.id;
    default:
      return valid(continueSave(slot)?.weapon.id) ?? PLAYER_DATA.startWeapon;
  }
}
