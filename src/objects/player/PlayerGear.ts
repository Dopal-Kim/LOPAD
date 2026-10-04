/**
 * 49라운드 무기 자원(기력·탄창·과열) + 무기 휴대(칼집·등·손, 뽑기·넣기) 상태. 무기가 바뀌면 새로 시작한다.
 * 상태 변화는 WEAPON_RESOURCE · PLAYER_WEAPON_DRAWN/SHEATHED 로 알린다(음향 훅).
 */
import { EventBus, Events, type WeaponCarryPayload, type WeaponResourcePayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { WeaponCarryDef, WeaponFirstStrikeDef } from '../../data/types';
import { frameDurations, motionAction } from '../../systems/sprites/spriteDefs';
import { WeaponResource, effectiveResource } from '../../systems/weapon/weaponResource';
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
    const def = w.def.resource ? effectiveResource(w.def.resource, w.mods) : null;
    const key = def ? `${w.id}|${def.max}|${def.kind === 'ammo' ? def.reloadMs : ''}` : w.id;
    if (this.trackerWeapon !== key) {
      const sameWeapon = this.trackerWeapon.split('|')[0] === w.id;
      const prev = this.tracker;
      this.trackerWeapon = key;
      // 56라운드 Q18: 단검 낙인 연동 — 과열 식는 동안 공격 가능·느려짐
      const g = w.def.gauge;
      const cooling = g?.kind === 'brand' ? { speedMult: g.coolingSpeedMult, moveMult: g.coolingMoveMult } : null;
      this.tracker = def ? new WeaponResource(def, cooling) : null;
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

  /** 넣은 상태 첫 타 보너스 (넣은 상태가 아니거나 데이터가 없으면 null) */
  get firstStrike(): WeaponFirstStrikeDef | null {
    return this.sheathed ? (gameState.weapon.def.carry?.firstStrike ?? null) : null;
  }

  /**
   * 51라운드 Q4 F 키: 넣기/뽑기 (칼집·등 무기만). 몸·무기 `<무기>_draw` / `<무기>_sheathe` 시트 1회 (같은 열 겹침).
   * 반환: 새 상태와 동작 길이 ms (시트가 없으면 0). 손에 드는 무기면 null
   */
  toggle(time: number): { drawn: boolean; ms: number } | null {
    if (this.carryMode === 'hand') return null;
    const next = !this.drawn;
    const visual = this.p.visual;
    const act = motionAction(gameState.weapon.id, next ? 'draw' : 'sheathe');
    const ms = visual.hasAction(act) ? visual.oneShot(act, visual.facing, time) : 0;
    this.drawn = next;
    if (next) this.lastAttackAt = time;
    this.emitCarry(next ? Events.PLAYER_WEAPON_DRAWN : Events.PLAYER_WEAPON_SHEATHED);
    return { drawn: next, ms };
  }

  /** 휴대 위치 (데이터 carry 가 없으면 손) */
  get carryMode(): WeaponCarryDef['mode'] {
    return gameState.weapon.def.carry?.mode ?? 'hand';
  }

  /** 자원 진행 + 상태 변화 이벤트 (기력 바닥·회복 / 장전 끝 / 과열·냉각 끝 / 가열 단계) */
  tick(res: WeaponResource, time: number, delta: number): void {
    // 51라운드 Q4: 넣은 동안 기력이 빨리 찬다
    res.regenMult = this.sheathed ? (gameState.weapon.def.carry?.sheathedRegenMult ?? 1) : 1;
    const before = { ex: res.isExhausted, rl: res.reloading, oh: res.overheated };
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
    if (before.oh && !res.overheated) emit('cooled');
    if (!before.oh && res.overheated) emit('overheat');
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
