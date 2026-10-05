/**
 * 60라운드 최종 각성 연출 (계약 art §21 '60라운드 제작 결과' — BuildRuntime 에서 분리):
 * - 각성 획득(개성 '각성' 칸·시험장 a): 각성 시트(오버레이 `_awaken` · 각성 순간 `<무기>_awaken_in` · 각성 궤적 `<fx>_awaken`)를 로드하고,
 *   로드·메뉴 닫힘 뒤 **같은 순간에** 각성 순간 fx 1회(주인공 피벗을 따라감) + 무기 외형 오버레이를 켠다.
 *   각성 순간 시트가 없으면 예전처럼 시그니처 fx 1회.
 * - 각성 런: 기본 fx 를 각성 궤적으로 1:1 교체(FxPool 교체 표 — `awakenFxAliases`, 갈래 replaceFx 가 같은 fx 를 바꾸면 갈래가 우선).
 */
import { EventBus, Events, type WeaponEvolvedPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { AWAKENINGS } from '../../../data/build';
import { loadAwakenSheets } from '../../../systems/sprites/sheetLoader';
import { awakenFxAliases, awakenInFxId } from '../../../systems/sprites/sheetSets';
import type { Game } from '../../Game';
import type { BuildRuntime } from './BuildRuntime';

export class AwakenFlow {
  /** 디버그: 마지막 각성 연출 (각성 순간 fx id · 폴백 시그니처 여부) */
  last: { fx: string | null; signature: boolean } | null = null;

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {}

  /** 씬 시작: 각성 런이면 각성 시트 (preload 에서 못 읽었으면 지금) — 오버레이는 바로 켜진다 */
  onSceneStart(): void {
    if (gameState.build.awakened) loadAwakenSheets(this.g, gameState.weapon.id);
  }

  /** 최종 각성 획득. emit = 시험장처럼 WEAPON_EVOLVED 를 따로 내지 않은 곳이면 true */
  onAwakened(emit = true): void {
    const w = gameState.weapon;
    const id = w.id;
    this.g.player.overlay.holdAwaken(true);
    loadAwakenSheets(this.g, id, () => this.rt.afterMenu(() => this.reveal(id)));
    if (emit)
      EventBus.emit(Events.WEAPON_EVOLVED, {
        weapon: id,
        stage: w.stage + 1,
        name: AWAKENINGS[id]?.name ?? w.displayName,
        kind: 'awaken',
      } satisfies WeaponEvolvedPayload);
  }

  /** 각성 순간: 각성 순간 fx 1회 + 오버레이 켬 (같은 프레임) */
  private reveal(weaponId: string): void {
    if (!this.g.scene.isActive()) return;
    this.g.player.overlay.holdAwaken(false);
    if (!gameState.build.awakened || gameState.weapon.id !== weaponId) return;
    const inFx = awakenInFxId(weaponId);
    if (this.rt.art.onPlayer(inFx)) {
      this.last = { fx: inFx, signature: false };
      return;
    }
    const sig = AWAKENINGS[weaponId]?.art?.fx?.[0] ?? null;
    this.last = { fx: sig, signature: Boolean(sig && this.rt.art.onPlayer(sig)) };
  }

  /** 각성 런의 fx 교체 표 (각성 궤적) — 아니면 빈 표 */
  aliases(): Record<string, string> {
    return gameState.build.awakened ? awakenFxAliases(gameState.weapon.id) : {};
  }
}
