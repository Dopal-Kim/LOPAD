/**
 * 49라운드 무기 자원(기력·탄창·가속) + 무기 휴대(칼집·등·손, 뽑기·넣기) 상태. 무기가 바뀌면 새로 시작한다.
 * 상태 변화는 WEAPON_RESOURCE · PLAYER_WEAPON_DRAWN/SHEATHED 로 알린다(음향 훅).
 * 61라운드: F 넣기/뽑기·넣은 채 첫 타 보너스 삭제 — 칼은 좌 홀드 발도가 칼집에 넣고(`sheatheQuiet`), 다음 공격이 다시 뽑는다.
 */
import { EventBus, Events, type WeaponCarryPayload, type WeaponResourcePayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { WeaponCarryDef } from '../../data/types';
import { frameDurations, motionAction } from '../../systems/sprites/spriteDefs';
import { WeaponResource, effectiveResource } from '../../systems/weapon/weaponResource';
import { resourceAdjust } from '../../systems/build/current';
import type { WeaponResourceDef } from '../../data/types';

/** 자원 정의가 바뀌었는지 (장전·식힘·그로기 시간) */
function resourceKeyPart(def: WeaponResourceDef): string {
  if (def.kind === 'ammo') return String(def.reloadMs);
  if (def.kind === 'heat') return String(def.max);
  return String(def.groggyMs ?? '');
}
import type { Player } from '../Player';

export class PlayerGear {
  private tracker: WeaponResource | null = null;
  private trackerWeapon = '';
  /** 칼·대검을 뽑아 든 상태 · 마지막 공격 시각 (sheatheAfterMs 뒤 넣는다) */
  drawn = false;
  lastAttackAt = -Infinity;
  /** 디버그: 마지막 휴대·자원 이벤트 */
  lastEvent: string | null = null;
  /** 자원 이벤트 경계 검출 (기력 바닥 · 가열 단계) */
  private prevExhausted = false;
  private prevStage = 0;

  constructor(private readonly p: Player) {}

  /** 현재 무기의 자원 상태 (자원이 없는 무기면 null). 51라운드 속사: 갈래가 탄창·장전을 바꾸면 값을 이어 새로 만든다 */
  get resource(): WeaponResource | null {
    const w = gameState.weapon;
    // 57라운드: 빌드 축 자원 조정 (피멍·버팀 4)
    const def = w.def.resource ? effectiveResource(w.def.resource, w.mods, resourceAdjust()) : null;
    const key = def ? `${w.id}|${def.max}|${resourceKeyPart(def)}` : w.id;
    if (this.trackerWeapon !== key) {
      const sameWeapon = this.trackerWeapon.split('|')[0] === w.id;
      const prev = this.tracker;
      this.trackerWeapon = key;
      this.tracker = def ? new WeaponResource(def) : null;
      if (sameWeapon && prev && this.tracker) {
        // 탄창이 커지면 늘어난 만큼 채워 준다
        const grow = Math.max(0, this.tracker.max - prev.max);
        this.tracker.value = Math.min(this.tracker.max, prev.value + (def!.kind === 'ammo' ? grow : 0));
      }
      if (!sameWeapon) {
        this.drawn = false;
        this.lastAttackAt = -Infinity;
      }
    }
    return this.tracker;
  }

  /** 51라운드 Q4: 칼집·등에 넣은 상태 (손에 드는 무기는 늘 false) */
  get sheathed(): boolean {
    return this.carryMode !== 'hand' && !this.drawn;
  }

  /**
   * 61라운드 칼 발도: 칼집에 넣은 상태로 (소리·이벤트 없음 — 발도 동작 그림이 납도까지 그린다). 다음 공격의 markDrawn 이 다시 뽑는다
   */
  sheatheQuiet(): void {
    if (this.carryMode !== 'hand') this.drawn = false;
  }

  /** 휴대 위치 (데이터 carry 가 없으면 손) */
  get carryMode(): WeaponCarryDef['mode'] {
    return gameState.weapon.def.carry?.mode ?? 'hand';
  }

  /** 자원 진행 + 상태 변화 이벤트 (기력 바닥·회복 / 장전 끝 / 가속 단계) */
  tick(res: WeaponResource, time: number, delta: number): void {
    const before = { ex: res.isExhausted, rl: res.reloading };
    res.tick(time, delta);
    const emit = (event: WeaponResourcePayload['event'], stage?: number) => {
      this.lastEvent = event;
      EventBus.emit(Events.WEAPON_RESOURCE, {
        weapon: gameState.weapon.id,
        kind: res.kind,
        event,
        stage,
      } satisfies WeaponResourcePayload);
    };
    if (before.ex && !res.isExhausted) emit('recovered');
    if (before.rl && !res.reloading) emit('reloadDone');
    // 소모·가열(공격 시점)로 생긴 변화는 다음 프레임에 잡는다
    if (!this.prevExhausted && res.isExhausted) emit(res.isGroggy ? 'groggy' : 'exhausted');
    this.prevExhausted = res.isExhausted;
    if (res.kind === 'heat' && res.stage !== this.prevStage) emit('heatStage', res.stage);
    this.prevStage = res.stage;
  }

  /** 장전 시작 (자동·수동): 이벤트 + 장전 동작 (`player_bow_reload`, 장전 시간에 맞춤) */
  onReloadStart(time: number): void {
    const res = this.tracker;
    if (!res || res.def.kind !== 'ammo') return;
    this.lastEvent = 'reloadStart';
    EventBus.emit(Events.WEAPON_RESOURCE, {
      weapon: gameState.weapon.id,
      kind: 'ammo',
      event: 'reloadStart',
    } satisfies WeaponResourcePayload);
    const visual = this.p.visual;
    const act = motionAction(gameState.weapon.id, 'reload');
    if (!visual.hasAction(act) || this.p.action !== 'normal') return;
    // 아트 refillFrame(탄창이 차는 프레임) 시작이 장전 완료 순간에 오도록 늘인다. 메모가 없으면 전체를 장전 시간에
    const def = visual.sheet(act)!;
    const durations = frameDurations(def);
    const natural = durations.reduce((a, b) => a + b, 0);
    const refillAt =
      typeof def.refillFrame === 'number' ? durations.slice(0, def.refillFrame).reduce((a, b) => a + b, 0) : 0;
    const fit = refillAt > 0 ? (res.def.reloadMs * natural) / refillAt : res.def.reloadMs;
    visual.oneShot(act, visual.facing, time, fit);
  }

  /** 공격 시작: 칼·대검은 뽑은 상태로 (칼은 1타가 곧 발도) */
  markDrawn(time: number): void {
    this.lastAttackAt = time;
    if (this.carryMode === 'hand' || this.drawn) return;
    this.drawn = true;
    this.emitCarry(Events.PLAYER_WEAPON_DRAWN);
  }

  /** 대검: 등에서 두 손으로 끌어냄 시작 (동작·이동 잠금은 Player) */
  beginDraw(time: number): void {
    this.drawn = true;
    this.lastAttackAt = time;
    this.emitCarry(Events.PLAYER_WEAPON_DRAWN);
  }

  /** 마지막 공격 뒤 sheatheAfterMs 가 지나면 넣는다 (`<무기>_sheathe` — 칼은 납도) */
  updateCarry(time: number): void {
    const carry = gameState.weapon.def.carry;
    const visual = this.p.visual;
    // 51라운드 Q4: sheatheAfterMs 0 = 자동으로 넣지 않음 (F 키로만)
    if (!this.drawn || !carry || carry.mode === 'hand' || carry.sheatheAfterMs <= 0 || this.p.action !== 'normal')
      return;
    if (time - this.lastAttackAt < carry.sheatheAfterMs || visual.isBusy(time)) return;
    this.drawn = false;
    const act = motionAction(gameState.weapon.id, 'sheathe');
    if (visual.hasAction(act)) visual.oneShot(act, visual.facing, time);
    this.emitCarry(Events.PLAYER_WEAPON_SHEATHED);
  }

  private emitCarry(event: string): void {
    this.lastEvent = event;
    EventBus.emit(event, { weapon: gameState.weapon.id, mode: this.carryMode } satisfies WeaponCarryPayload);
  }
}
