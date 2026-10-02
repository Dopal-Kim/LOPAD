/**
 * 47라운드 상호작용 구조물 런타임 (결정 round-47, 초안 structures-draft.md, 계약 ui-system-interface §9) — Game 이 보는 창구.
 * - 타격형(crate·cask·hiddenWall·stakeBell): 근접 판정·대쉬 공격·화살이 구조물 사각형에 닿으면 반응
 * - E형: 1.5칸(24px) 안 가장 가까운 것 하나를 안내(`interactable`), 비전투 중에만 E 로 실행·메뉴
 * - 통과형(still): 베기 궤적·화살·대쉬 경로가 불꽃을 지나면 불붙은 무기/불화살
 * - 자동(roulette): 그 시련 방 시련 시작 때 판 규칙 결정
 * 상태는 층 안에서 완결된다(Q13) — 48라운드 노드 지도는 exportFloorState/importFloorState 로 노드 사이에 이어받는다.
 *
 * 50라운드 분리: 공통부 `core.ts` · 타격형/불/웅덩이 `kinds/strikeKinds.ts` · 공통·1층 E형 `kinds/serviceKinds.ts` ·
 * 2층 도박 `kinds/gambleKinds.ts` · E 안내·실행 `interact.ts` · HUD 상태 `status.ts`.
 */
import type Phaser from 'phaser';
import { EventBus, Events, type PlayerSecondaryPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { UiInteractable, UiStatus } from '../../contract/ui';
import type { Mob } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import type { InputState } from '../InputSystem';
import type { Room } from '../mapgen';
import type { WaveMods } from '../RoomDirector';
import { TILE } from '../../core/Constants';
import { INTERACT_KINDS, num, structureDef, txt } from './data';
import type { StructurePlacement } from './placement';
import { agingProgress, debtPenalty, drunkMods, repaySplit, stakeMods, swayAngle } from './rules';
import { StructureCore, type StructureFloorCarry, type StructureHost } from './core';
import { Interaction } from './interact';
import { GambleKinds } from './kinds/gambleKinds';
import { ServiceKinds } from './kinds/serviceKinds';
import { StrikeKinds } from './kinds/strikeKinds';
import { structureStatuses } from './status';

export type { StructureFloorCarry, StructureHost } from './core';

export class StructureSystem {
  private readonly c: StructureCore;
  private readonly strike: StrikeKinds;
  private readonly service: ServiceKinds;
  private readonly gamble: GambleKinds;
  private readonly interact: Interaction;
  private readonly colliders: Phaser.Physics.Arcade.Collider[] = [];

  constructor(
    private readonly host: StructureHost,
    placements: readonly StructurePlacement[],
  ) {
    const c = (this.c = new StructureCore(host));
    this.strike = new StrikeKinds(c);
    this.service = new ServiceKinds(c);
    this.gamble = new GambleKinds(c);
    this.interact = new Interaction(c, this.service, this.gamble);
    for (const p of placements) c.add(p);
    const scene = host.scene;
    this.colliders.push(scene.physics.add.collider(host.player, c.solids));
    this.colliders.push(scene.physics.add.collider(host.mobs, c.solids));
    EventBus.on(Events.TRIAL_STARTED, this.onTrialStarted, this);
    EventBus.on(Events.TRIAL_CLEARED, this.onTrialCleared, this);
    EventBus.on(Events.BOSS_DIED, this.onBossDied, this);
    EventBus.on(Events.PLAYER_PARRIED, this.onParried, this);
    EventBus.on(Events.PLAYER_SECONDARY, this.onSecondary, this);
    EventBus.on(Events.PLAYER_DAMAGED, this.gamble.onPlayerDamaged, this.gamble);
  }

  // =====================================================================
  // 매 프레임
  // =====================================================================

  /** 구조물 메뉴가 열려 있으면 플레이어 입력을 잠근다 (계약 §9.3) */
  get inputLocked(): boolean {
    return Boolean(this.host.menu.menu?.structureId);
  }

  update(input: InputState, time: number, delta: number): void {
    this.strike.update(time, delta);
    this.gamble.updateRing(time);
    this.interact.update(input, delta);
  }

  /** 1-5 취기: 조준점을 플레이어 둘레로 흔든다 */
  adjustAim(input: InputState, time: number): InputState {
    const c = this.c;
    if (c.drunk <= 0) return input;
    const a = swayAngle(c.drunk, time, c.drunkParams);
    if (a === 0) return input;
    const px = this.host.player.x;
    const py = this.host.player.y;
    const dx = input.aimX - px;
    const dy = input.aimY - py;
    const cos = Math.cos(a);
    const sin = Math.sin(a);
    return { ...input, aimX: px + dx * cos - dy * sin, aimY: py + dx * sin + dy * cos };
  }

  // =====================================================================
  // 전투 훅 (Game 이 부른다)
  // =====================================================================

  /** 공격 피해 배율: 취기 · 룰렛 규칙. kind = 공격 종류, crit = 치명 여부 */
  damageMult(kind: 'attack' | 'dashAttack' | 'aimed' | 'other', crit: boolean): number {
    const c = this.c;
    let m = 1;
    if (c.drunk > 0) {
      const d = drunkMods(c.drunk, c.drunkParams);
      m *= d.attackMult;
      if (kind === 'dashAttack') m *= d.dashAttackMult;
    }
    const rule = c.activeRule();
    if (rule) {
      if (typeof rule.nonCritMult === 'number' && !crit) m *= rule.nonCritMult;
      if (kind === 'dashAttack' && typeof rule.dashAttackMult === 'number') m *= rule.dashAttackMult;
      if ((kind === 'attack' || kind === 'aimed') && typeof rule.attackMult === 'number') m *= rule.attackMult;
    }
    return m;
  }

  /** 치명타 확률 가산 (%p): 룰렛 '치명만 통한다' */
  critBonus(): number {
    const rule = this.c.activeRule();
    return rule && typeof rule.critBonus === 'number' ? rule.critBonus : 0;
  }

  /** 처치 보상 배율: 판돈 종(남은 시련) · 룰렛 '배수 판' */
  killMods(): { goldMult: number; personalityMult: number } {
    const c = this.c;
    let goldMult = 1;
    let personalityMult = 1;
    const room = this.host.director.activeRoom;
    if (room?.type === 'trial' && !this.host.director.challengeRoomId) {
      if (c.stakeRings > 0) {
        const s = c.stakes;
        goldMult *= s.goldMult;
        personalityMult *= s.personalityMult;
      }
      const rule = c.activeRule();
      if (rule && typeof rule.goldMult === 'number') goldMult *= rule.goldMult;
    }
    return { goldMult, personalityMult };
  }

  /** 시련 웨이브 배율 (RoomDirector host) */
  waveMods(room: Room): WaveMods {
    const c = this.c;
    const out: WaveMods = { hpMult: 1, countMult: 1, extra: 0 };
    if (room.type !== 'trial') return out;
    if (c.stakeRings > 0) {
      const s = stakeMods(c.stakeRings, c.bellParams);
      out.hpMult = s.hpMult;
      out.extra = s.extra;
    }
    const rule = c.roulette?.roomId === room.id ? c.ruleAt(c.roulette.ruleIndex) : null;
    if (rule && typeof rule.countMult === 'number') out.countMult = rule.countMult;
    return out;
  }

  /** 주운 골드: 빚이 있으면 일부 자동 상환. 돌려준 값이 실제로 얻는 골드 */
  onGoldPickup(amount: number): number {
    const c = this.c;
    if (c.debt <= 0) return amount;
    const ledger = c.find('ledger');
    const ld = ledger?.def ?? structureDef('ledger');
    const { kept, repaid } = repaySplit(amount, c.debt, num(ld, 'repayRatio'));
    c.debt -= repaid;
    if (c.debt <= 0 && repaid > 0) c.resultOf('ledger', ledger?.id ?? 'ledger', 'gain', txt(ld, 'autoRepaid'), {});
    return kept;
  }

  onMeleeSwing(x: number, y: number, w: number, h: number, dirX: number, dirY: number): void {
    this.strike.onMeleeSwing(x, y, w, h, dirX, dirY);
  }

  onDash(x: number, y: number, dirX: number, dirY: number, lenPx: number): void {
    this.strike.onDash(x, y, dirX, dirY, lenPx);
  }

  onPush(x: number, y: number, radiusPx: number): void {
    this.strike.onPush(x, y, radiusPx);
  }

  tickShots(shots: readonly Projectile[]): void {
    this.strike.tickShots(shots);
  }

  onMobHit(mob: Mob, viaFireArrow: boolean): void {
    this.strike.onMobHit(mob, viaFireArrow);
  }

  get fireActive(): boolean {
    return this.c.fireActive;
  }

  // =====================================================================
  // 이벤트 구독
  // =====================================================================

  private onTrialStarted(p: { roomId: string }): void {
    this.gamble.onTrialStarted(p);
  }

  private onTrialCleared(p: { roomId: string }): void {
    const c = this.c;
    // C5 불씨 (모닥불이 있는 층만) · 48라운드 노드 지도: 모닥불은 휴식 노드에만 있으므로 불씨는 층 상태로 쌓는다
    const fire = c.find('campfire');
    if (fire || this.host.nodeMode) {
      const fd = fire?.def ?? structureDef('campfire');
      const before = c.embers;
      c.embers = Math.min(num(fd, 'maxEmbers'), c.embers + num(fd, 'emberPerTrial'));
      if (fire && c.embers > 0 && before === 0) c.setVisual(fire, 'active');
    }
    this.deliverCarriedAging();
    // 1-4 숙성 진행
    for (const s of c.list)
      if (s.kind === 'agingBarrel' && s.state === 'active' && this.service.agingReady(s)) c.setVisual(s, 'ready');
    // 1-5 취기 해제
    this.service.sober();
    // 2-5 룰렛 보너스
    this.gamble.onTrialCleared(p.roomId);
  }

  /** 보스 처치: 1-3 빚 정산(최대 HP), 취기 해제 */
  private onBossDied(): void {
    const c = this.c;
    const ledger = c.find('ledger');
    // 48라운드 노드 지도: 장부대는 상점 노드에 있고 보스는 다른 노드 — 정의로 정산한다
    const ld = ledger?.def ?? (this.host.nodeMode ? structureDef('ledger') : null);
    if (c.debt > 0 && ld) {
      const hp = debtPenalty(c.debt, num(ld, 'maxHpPer10Debt'));
      const debt = c.debt;
      c.debt = 0;
      c.loseMaxHp(hp);
      c.resultOf('ledger', ledger?.id ?? 'ledger', 'loss', txt(ld, 'penalty', { debt, hp }), { maxHp: -hp });
    }
    this.service.sober();
  }

  /** 2-5 '받아쳐라': 패링·가드 성공마다 개성 */
  private onParried(): void {
    this.gamble.counterRule();
  }

  private onSecondary(p: PlayerSecondaryPayload): void {
    if (p.kind === 'guard' && p.phase === 'block') this.gamble.counterRule();
  }

  // =====================================================================
  // 스냅샷 (계약 §9.1·9.2·9.5)
  // =====================================================================

  interactable(): UiInteractable | null {
    return this.interact.interactable();
  }

  statuses(): UiStatus[] {
    return structureStatuses(this.c);
  }

  /** 사용 가능한 E형 구조물이 남은 방 (미니맵 점) */
  structureRooms(): Set<string> {
    const out = new Set<string>();
    for (const s of this.c.list) if (INTERACT_KINDS.includes(s.kind) && !this.interact.exhausted(s)) out.add(s.roomId);
    return out;
  }

  // =====================================================================
  // 디버그
  // =====================================================================

  debugList(): {
    id: string;
    kind: string;
    roomId: string;
    x: number;
    y: number;
    tx: number;
    ty: number;
    w: number;
    h: number;
    state: string;
    visual: string;
    art: boolean;
    exhausted: boolean;
    rolling: boolean;
  }[] {
    return this.c.list.map((s) => ({
      id: s.id,
      kind: s.kind,
      roomId: s.roomId,
      x: s.rect.centerX,
      y: s.rect.centerY,
      tx: s.p.tx,
      ty: s.p.ty,
      w: s.p.w,
      h: s.p.h,
      state: s.state,
      visual: s.views[0]?.current ?? '',
      art: s.views[0]?.art ?? false,
      exhausted: INTERACT_KINDS.includes(s.kind) ? this.interact.exhausted(s) : s.state !== 'idle',
      rolling: Boolean(s.rolling),
    }));
  }

  /** 구조물 앞(아래쪽 우선) 걸을 수 있는 지점 */
  standPoint(id: string): { x: number; y: number } | null {
    const s = this.c.list.find((i) => i.id === id);
    if (!s) return null;
    const r = this.interact.rectOf(s);
    const gap = 10;
    const tries = [
      { x: r.centerX, y: r.bottom + gap },
      { x: r.centerX, y: r.top - gap },
      { x: r.left - gap, y: r.centerY },
      { x: r.right + gap, y: r.centerY },
      { x: r.centerX, y: r.bottom + gap + TILE },
    ];
    for (const t of tries) if (this.host.world.isWalkableAt(t.x, t.y)) return t;
    return tries[0];
  }

  debugState(): Record<string, unknown> {
    const c = this.c;
    return {
      chestsOpened: c.chestsOpened,
      debt: c.debt,
      drunk: c.drunk,
      stakeRings: c.stakeRings,
      embers: c.embers,
      fireWeapon: c.fireActive,
      pawned: c.pawned.map((p) => ({ ...p })),
      ring: c.ring ? { id: c.ring.inst.id, remainMs: c.ring.until - c.now, hits: c.ring.hits } : null,
      cardFight: c.cardFight?.id ?? null,
      roulette: c.roulette ? { id: c.roulette.inst.id, rule: c.ruleAt(c.roulette.ruleIndex)?.id } : null,
      puddles: this.strike.puddles.map((p) => ({ x: p.rect.centerX, y: p.rect.centerY, fire: p.fireUntil > c.now })),
      burns: this.strike.burns.size,
      nearest: this.interact.nearestId,
      reason: this.interact.nearestReason,
      hold: this.interact.holdMs,
      log: c.log.map((r) => ({ ...r })),
    };
  }

  /** 다음 update 에서 E 를 누른 것으로 친다 (묘는 즉시 완료) */
  debugPressE(): void {
    this.interact.debugPress = true;
  }

  /** 구조물을 플레이어 방향에서 한 번 친다 */
  debugHit(id: string): boolean {
    const s = this.c.list.find((i) => i.id === id);
    if (!s || !this.strike.isHittable(s)) return false;
    const dx = s.rect.centerX - this.host.player.x;
    const dy = s.rect.centerY - this.host.player.y;
    const len = Math.hypot(dx, dy) || 1;
    s.lastHitAt = -Infinity;
    this.strike.onHit(s, dx / len, dy / len);
    return true;
  }

  // =====================================================================
  // 48라운드: 노드 사이 층 상태
  // =====================================================================

  /** 노드를 떠날 때: 들고 갈 층 상태 */
  exportFloorState(): StructureFloorCarry {
    const c = this.c;
    const aging = [...c.agingCarry];
    for (const s of c.list)
      if (s.kind === 'agingBarrel' && s.agingAt !== null && s.state === 'active') aging.push(s.agingAt);
    return {
      chestsOpened: c.chestsOpened,
      debt: c.debt,
      drunk: c.drunk,
      stakeRings: c.stakeRings,
      embers: c.embers,
      fireWeaponMs: Math.max(0, c.fireWeaponUntil - c.now),
      pawned: c.pawned.map((p) => ({ ...p })),
      aging,
    };
  }

  /** 새 노드에서: 앞 노드의 층 상태를 이어받는다 */
  importFloorState(carry: StructureFloorCarry | null | undefined): void {
    if (!carry) return;
    const c = this.c;
    c.chestsOpened = carry.chestsOpened;
    c.debt = carry.debt;
    c.stakeRings = carry.stakeRings;
    c.embers = carry.embers;
    c.fireWeaponUntil = carry.fireWeaponMs > 0 ? c.now + carry.fireWeaponMs : 0;
    c.pawned = carry.pawned.map((p) => ({ ...p }));
    c.agingCarry = [...carry.aging];
    if (carry.drunk > 0) c.setDrunk(carry.drunk);
    const fire = c.find('campfire');
    if (fire && c.embers > 0) c.setVisual(fire, 'active');
  }

  /** 앞 노드 숙성 통의 물약이 익으면 바로 받는다 (노드 지도에서는 되돌아갈 수 없으므로) */
  private deliverCarriedAging(): void {
    const c = this.c;
    if (c.agingCarry.length === 0) return;
    const d = structureDef('agingBarrel');
    const need = num(d, 'trialsNeeded');
    const keep: number[] = [];
    for (const at of c.agingCarry) {
      if (!agingProgress(at, gameState.trialsCleared, need).ready) {
        keep.push(at);
        continue;
      }
      const out = num(d, 'potionsOut');
      for (let i = 0; i < out; i++) {
        if (gameState.potions < this.host.potionCarry()) gameState.potions += 1;
        else this.host.spawnPickup(this.host.player.x + (i - out / 2) * 8, this.host.player.y + 8, 'potion', 1);
      }
      EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
      c.resultOf('agingBarrel', 'agingBarrel', 'gain', txt(d, 'take', { n: out }), { potions: out });
    }
    c.agingCarry = keep;
  }

  destroy(): void {
    EventBus.off(Events.TRIAL_STARTED, this.onTrialStarted, this);
    EventBus.off(Events.TRIAL_CLEARED, this.onTrialCleared, this);
    EventBus.off(Events.BOSS_DIED, this.onBossDied, this);
    EventBus.off(Events.PLAYER_PARRIED, this.onParried, this);
    EventBus.off(Events.PLAYER_SECONDARY, this.onSecondary, this);
    EventBus.off(Events.PLAYER_DAMAGED, this.gamble.onPlayerDamaged, this.gamble);
    const world = this.host.scene.physics.world;
    if (world) for (const col of this.colliders) world.removeCollider(col);
    for (const s of this.c.list) for (const v of s.views) v.destroy();
    this.strike.destroy();
    this.c.list.length = 0;
    gameState.structureDefense = 0;
  }
}
