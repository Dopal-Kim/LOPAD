/**
 * 47라운드 상호작용 구조물 런타임 (결정 round-47, 초안 structures-draft.md, 계약 ui-system-interface §9).
 * - 타격형(crate·cask·hiddenWall·stakeBell): 근접 판정·대쉬 공격·화살이 구조물 사각형에 닿으면 반응
 * - E형: 1.5칸(24px) 안 가장 가까운 것 하나를 안내(`interactable`), 비전투 중에만 E 로 실행·메뉴
 * - 통과형(still): 베기 궤적·화살·대쉬 경로가 불꽃을 지나면 불붙은 무기/불화살
 * - 자동(roulette): 그 시련 방 시련 시작 때 판 규칙 결정
 * 상태는 층 안에서 완결된다(Q13) — 층을 넘으면 씬이 다시 만들어지며 사라진다.
 */
import Phaser from 'phaser';
import { STRUCTURE_FX, TILE } from '../../core/Constants';
import {
  EventBus,
  Events,
  type ChallengeEventPayload,
  type PlayerDamagedPayload,
  type PlayerSecondaryPayload,
  type StructureBellPayload,
  type StructureEventPayload,
  type StructureFirePayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { ECONOMY } from '../../data';
import {
  UI_EVENTS,
  __system,
  type StoryKind,
  type UiChallengeCleared,
  type UiChallengeStarted,
  type UiCost,
  type UiInteractBlockReason,
  type UiInteractable,
  type UiMenuLine,
  type UiStatus,
  type UiStructureBroken,
  type UiStructureKind,
  type UiStructureMenuId,
  type UiStructureResult,
  type UiStructureUsed,
} from '../../contract/ui';
import type { Mob } from '../../objects/Mob';
import type { Player } from '../../objects/Player';
import type { Projectile } from '../../objects/Projectile';
import type { FxPool } from '../fx';
import type { InputState } from '../InputSystem';
import type { Room } from '../mapgen';
import { metaStore } from '../meta';
import type { RoomDirector, WaveMods } from '../RoomDirector';
import type { Rng } from '../rng';
import type { KillKind } from '../senses';
import type { TextMenu } from '../TextMenu';
import { floorText } from '../story';
import type { TileWorld } from '../../world/TileWorld';
import { StructureView } from '../../world/StructureView';
import { INTERACT_KINDS, STRUCTURE_RULES, STRUCTURE_TEXT, num, structureDef, txt, type StructureDef } from './data';
import type { StructurePlacement } from './placement';
import {
  agingProgress,
  bloodCost,
  canSellBlood,
  cardStake,
  chestPrice,
  dealCards,
  debtPenalty,
  drunkMods,
  emberHeal,
  pawnValue,
  redeemCost,
  repaySplit,
  ringPayout,
  stakeMods,
  swayAngle,
  type CardOutcome,
  type DrunkParams,
} from './rules';

/** Game 이 넘겨주는 것 (씬 직접 참조 대신 필요한 것만) */
export interface StructureHost {
  scene: Phaser.Scene;
  world: TileWorld;
  director: RoomDirector;
  player: Player;
  mobs: Phaser.Physics.Arcade.Group;
  menu: TextMenu;
  fx: FxPool;
  rng: Rng;
  stageId: string;
  addGold(amount: number): void;
  spendGold(amount: number): void;
  spawnPickup(x: number, y: number, kind: 'gold' | 'potion', value: number): void;
  gainPersonality(amount: number): void;
  heal(amount: number): void;
  /** 적 피격 공통 경로 (Game.hitMob). 사망이면 true */
  hitMob(mob: Mob, dmg: number, opts: { crit: boolean; dirX: number; dirY: number; tick?: boolean }): boolean;
  /** 처치 처리 (Game.onKill) */
  onKill(mob: Mob, kind: KillKind): void;
  potionCarry(): number;
  /** 메뉴·연출·워프·보상 중 */
  isBusy(): boolean;
  openStatChooser(): void;
  story(kind: StoryKind, text: string): void;
}

type InstState = 'idle' | 'used' | 'broken' | 'active';

interface Inst {
  id: string;
  kind: UiStructureKind;
  def: StructureDef;
  roomId: string;
  p: StructurePlacement;
  /** 발판 사각형 (px) */
  rect: Phaser.Geom.Rectangle;
  views: StructureView[];
  bodies: Phaser.GameObjects.Zone[];
  state: InstState;
  hits: number;
  lastHitAt: number;
  /** 궤짝 할인 (저장고 궤짝 0.5) */
  discount: number;
  cups: number;
  round: number;
  bloodUses: number;
  lifeUses: number;
  loans: number;
  agingAt: number | null;
  rolling: { dx: number; dy: number; traveled: number } | null;
  rings: number;
  warned: boolean;
  deck: CardOutcome[] | null;
}

interface Puddle {
  rect: Phaser.Geom.Rectangle;
  until: number;
  fireUntil: number;
  nextTick: number;
  gfx: Phaser.GameObjects.Rectangle;
  fireGfx: Phaser.GameObjects.Rectangle | null;
  fireFx: ReturnType<FxPool['play']>[];
}

interface Burn {
  ticks: number;
  nextAt: number;
  dmg: number;
}

interface Pawned {
  key: string;
  type: 'passive' | 'potion';
  passiveId?: string;
  level?: number;
  name: string;
  received: number;
}

const ORDER: readonly UiStatus['id'][] = [
  'debt',
  'drunk',
  'stakes',
  'embers',
  'fireWeapon',
  'ring',
  'roulette',
  'aging',
  'pawn',
];

/** 메뉴 선택지 최대 (그만두기 제외) — UI 요청: '1'~'8' + '0' */
const MENU_MAX_LINES = 8;
/** 룰렛이 도는 연출 시간 */
const ROULETTE_SPIN_MS = 1200;

export class StructureSystem {
  private readonly list: Inst[] = [];
  private readonly solids: Phaser.Physics.Arcade.StaticGroup;
  private readonly colliders: Phaser.Physics.Arcade.Collider[] = [];
  private serial = 0;
  // --- 층 상태 (Q13: 층 안에서 완결) ---
  private chestsOpened = 0;
  private debt = 0;
  private drunk = 0;
  private stakeRings = 0;
  private embers = 0;
  private fireWeaponUntil = 0;
  private pawned: Pawned[] = [];
  private ring: { inst: Inst; until: number; hits: number; max: number; stake: number } | null = null;
  private cardFight: Inst | null = null;
  private roulette: { inst: Inst; roomId: string; ruleIndex: number } | null = null;
  private puddles: Puddle[] = [];
  private burns = new Map<Mob, Burn>();
  private mobsSlowed = false;
  // --- 상호작용 ---
  private nearest: Inst | null = null;
  private nearestReason: UiInteractBlockReason | null = null;
  private holdMs = 0;
  private debugInteract = false;
  /** 디버그: 최근 결과 */
  private readonly log: UiStructureResult[] = [];

  constructor(
    private readonly host: StructureHost,
    placements: readonly StructurePlacement[],
  ) {
    const scene = host.scene;
    this.solids = scene.physics.add.staticGroup();
    for (const p of placements) this.add(p);
    this.colliders.push(scene.physics.add.collider(host.player, this.solids));
    this.colliders.push(scene.physics.add.collider(host.mobs, this.solids));
    EventBus.on(Events.TRIAL_STARTED, this.onTrialStarted, this);
    EventBus.on(Events.TRIAL_CLEARED, this.onTrialCleared, this);
    EventBus.on(Events.BOSS_DIED, this.onBossDied, this);
    EventBus.on(Events.PLAYER_PARRIED, this.onParried, this);
    EventBus.on(Events.PLAYER_SECONDARY, this.onSecondary, this);
    EventBus.on(Events.PLAYER_DAMAGED, this.onPlayerDamaged, this);
  }

  // =====================================================================
  // 생성
  // =====================================================================

  private add(p: StructurePlacement, discount = 1): Inst {
    const def = structureDef(p.kind);
    const rect = new Phaser.Geom.Rectangle(p.tx * TILE, p.ty * TILE, p.w * TILE, p.h * TILE);
    const inst: Inst = {
      id: p.id,
      kind: p.kind,
      def,
      roomId: p.roomId,
      p,
      rect,
      views: [],
      bodies: [],
      state: 'idle',
      hits: 0,
      lastHitAt: -Infinity,
      discount,
      cups: 0,
      round: 0,
      bloodUses: 0,
      lifeUses: 0,
      loans: 0,
      agingAt: null,
      rolling: null,
      rings: 0,
      warned: false,
      deck: null,
    };
    const scene = this.host.scene;
    const floor = def.depth === 'floor';
    if (p.kind === 'hiddenWall') {
      // 입구 칸마다 벽 변형 1장 (cellar_wall 16×16, 북쪽 벽은 정면 · 그 외는 윗면 `_top`)
      for (let y = p.ty; y < p.ty + p.h; y++)
        for (let x = p.tx; x < p.tx + p.w; x++) {
          const r = new Phaser.Geom.Rectangle(x * TILE, y * TILE, TILE, TILE);
          inst.views.push(
            new StructureView(scene, {
              sheet: p.sprite,
              rect: r,
              color: def.placeholder.color,
              label: '',
              floor: false,
              subtle: true,
            }),
          );
        }
      this.setVisual(inst, 'idle');
    } else {
      inst.views.push(
        new StructureView(scene, {
          sheet: p.sprite,
          rect: new Phaser.Geom.Rectangle(rect.x, rect.y, rect.width, rect.height),
          color: def.placeholder.color,
          label: def.placeholder.label,
          floor,
          scale: def.spriteScale,
        }),
      );
    }
    if (p.solid && p.kind !== 'hiddenWall') {
      const z = scene.add.zone(rect.centerX, rect.centerY, rect.width, rect.height);
      this.solids.add(z);
      inst.bodies.push(z);
      for (let y = p.ty; y < p.ty + p.h; y++)
        for (let x = p.tx; x < p.tx + p.w; x++) this.host.world.setBlocked(x, y, true);
    }
    // 투견 링: 말뚝만 단단함 (시트 stakes, 링 바닥은 지나갈 수 있음)
    if (p.kind === 'dogRing') {
      const v = inst.views[0];
      for (const [sx, sy] of v.def?.stakes ?? []) {
        const w = v.frameToWorld(sx, sy);
        if (!w) continue;
        const z = scene.add.zone(w.x, w.y, 3 * (def.spriteScale ?? 1), 5 * (def.spriteScale ?? 1));
        this.solids.add(z);
        inst.bodies.push(z);
      }
    }
    // 초기 그림
    if (p.kind === 'still') this.setVisual(inst, 'active');
    if (p.kind === 'grave' && gameState.stageIndex === 1) this.setVisual(inst, 'idle_f2');
    this.list.push(inst);
    return inst;
  }

  /** 모든 그림에 같은 상태 (숨은 벽: 북쪽 벽이 아니면 `_top` 변형) */
  private setVisual(inst: Inst, state: string): void {
    for (const v of inst.views) {
      let s = state;
      if (inst.kind === 'hiddenWall' && inst.p.cellar && inst.p.cellar.side !== 'N' && state !== 'broken') {
        if (v.hasState(`${state}_top`)) s = `${state}_top`;
      }
      if (inst.kind === 'grave' && gameState.stageIndex === 1 && v.hasState(`${state}_f2`)) s = `${state}_f2`;
      v.setState(s);
    }
  }

  private removeBodies(inst: Inst): void {
    for (const z of inst.bodies) {
      this.solids.remove(z, true, true);
    }
    inst.bodies = [];
    for (let y = inst.p.ty; y < inst.p.ty + inst.p.h; y++)
      for (let x = inst.p.tx; x < inst.p.tx + inst.p.w; x++) this.host.world.setBlocked(x, y, false);
  }

  // =====================================================================
  // 매 프레임
  // =====================================================================

  /** 구조물 메뉴가 열려 있으면 플레이어 입력을 잠근다 (계약 §9.3) */
  get inputLocked(): boolean {
    return Boolean(this.host.menu.menu?.structureId);
  }

  update(input: InputState, time: number, delta: number): void {
    this.updateRolling(time, delta);
    this.updatePuddles(time);
    this.updateBurns(time);
    this.updateRing(time);
    this.updateInteract(input, delta);
  }

  /** 1-5 취기: 조준점을 플레이어 둘레로 흔든다 */
  adjustAim(input: InputState, time: number): InputState {
    if (this.drunk <= 0) return input;
    const a = swayAngle(this.drunk, time, this.drunkParams);
    if (a === 0) return input;
    const px = this.host.player.x;
    const py = this.host.player.y;
    const dx = input.aimX - px;
    const dy = input.aimY - py;
    const c = Math.cos(a);
    const s = Math.sin(a);
    return { ...input, aimX: px + dx * c - dy * s, aimY: py + dx * s + dy * c };
  }

  // =====================================================================
  // 전투 훅 (Game 이 부른다)
  // =====================================================================

  /** 공격 피해 배율: 취기 · 룰렛 규칙. kind = 공격 종류, crit = 치명 여부 */
  damageMult(kind: 'attack' | 'dashAttack' | 'aimed' | 'other', crit: boolean): number {
    let m = 1;
    if (this.drunk > 0) {
      const d = drunkMods(this.drunk, this.drunkParams);
      m *= d.attackMult;
      if (kind === 'dashAttack') m *= d.dashAttackMult;
    }
    const rule = this.activeRule();
    if (rule) {
      if (typeof rule.nonCritMult === 'number' && !crit) m *= rule.nonCritMult;
      if (kind === 'dashAttack' && typeof rule.dashAttackMult === 'number') m *= rule.dashAttackMult;
      if ((kind === 'attack' || kind === 'aimed') && typeof rule.attackMult === 'number') m *= rule.attackMult;
    }
    return m;
  }

  /** 치명타 확률 가산 (%p): 룰렛 '치명만 통한다' */
  critBonus(): number {
    const rule = this.activeRule();
    return rule && typeof rule.critBonus === 'number' ? rule.critBonus : 0;
  }

  /** 처치 보상 배율: 판돈 종(남은 시련) · 룰렛 '배수 판' */
  killMods(): { goldMult: number; personalityMult: number } {
    let goldMult = 1;
    let personalityMult = 1;
    const room = this.host.director.activeRoom;
    if (room?.type === 'trial' && !this.host.director.challengeRoomId) {
      if (this.stakeRings > 0) {
        const s = stakeMods(this.stakeRings, this.bellParams);
        goldMult *= s.goldMult;
        personalityMult *= s.personalityMult;
      }
      const rule = this.activeRule();
      if (rule && typeof rule.goldMult === 'number') goldMult *= rule.goldMult;
    }
    return { goldMult, personalityMult };
  }

  /** 시련 웨이브 배율 (RoomDirector host) */
  waveMods(room: Room): WaveMods {
    const out: WaveMods = { hpMult: 1, countMult: 1, extra: 0 };
    if (room.type !== 'trial') return out;
    if (this.stakeRings > 0) {
      const s = stakeMods(this.stakeRings, this.bellParams);
      out.hpMult = s.hpMult;
      out.extra = s.extra;
    }
    const rule = this.roulette?.roomId === room.id ? this.ruleAt(this.roulette.ruleIndex) : null;
    if (rule && typeof rule.countMult === 'number') out.countMult = rule.countMult;
    return out;
  }

  /** 주운 골드: 빚이 있으면 일부 자동 상환. 돌려준 값이 실제로 얻는 골드 */
  onGoldPickup(amount: number): number {
    if (this.debt <= 0) return amount;
    const ledger = this.list.find((i) => i.kind === 'ledger');
    const ratio = ledger ? num(ledger.def, 'repayRatio') : 0.5;
    const { kept, repaid } = repaySplit(amount, this.debt, ratio);
    this.debt -= repaid;
    if (this.debt <= 0 && repaid > 0 && ledger) this.result(ledger, 'gain', txt(ledger.def, 'autoRepaid'), {});
    return kept;
  }

  /** 근접 판정 사각형 (베기·대쉬 공격·충격파): 타격형 구조물 + 화로 점화 + 불붙은 무기로 웅덩이 점화 */
  onMeleeSwing(x: number, y: number, w: number, h: number, dirX: number, dirY: number): void {
    const r = new Phaser.Geom.Rectangle(x - w / 2, y - h / 2, w, h);
    this.hitRect(r, dirX, dirY);
    if (this.touchesFlame(r)) this.igniteWeapon('weapon');
    if (this.fireActive) this.ignitePuddlesIn(r);
  }

  /** 대쉬 시작: 대쉬 경로가 불꽃을 지나면 무기에 불 */
  onDash(x: number, y: number, dirX: number, dirY: number, lenPx: number): void {
    const line = new Phaser.Geom.Line(x, y, x + dirX * lenPx, y + dirY * lenPx);
    for (const s of this.list) {
      if (s.kind !== 'still') continue;
      if (Phaser.Geom.Intersects.LineToRectangle(line, this.flameRect(s))) {
        this.igniteWeapon('weapon');
        return;
      }
    }
  }

  /** 가드 해제 밀쳐내기: 반경 안 술통을 굴린다 */
  onPush(x: number, y: number, radiusPx: number): void {
    for (const s of this.list) {
      if (s.kind !== 'cask' || s.state !== 'idle' || s.rolling) continue;
      const dx = s.rect.centerX - x;
      const dy = s.rect.centerY - y;
      const d = Math.hypot(dx, dy);
      if (d > radiusPx + s.rect.width / 2) continue;
      this.startRoll(s, d > 0 ? dx / d : 1, d > 0 ? dy / d : 0);
    }
  }

  /** 플레이어 화살: 화로 불꽃 통과 → 불화살, 불화살 → 웅덩이 점화, 타격형 구조물 맞힘 */
  tickShots(shots: readonly Projectile[]): void {
    const fireOn = this.fireActive;
    for (const shot of shots) {
      if (!shot.active || shot.owner !== 'player') continue;
      const pt = { x: shot.x, y: shot.y };
      if (
        !shot.fire &&
        (fireOn || this.list.some((s) => s.kind === 'still' && this.flameRect(s).contains(pt.x, pt.y)))
      ) {
        shot.fire = true;
        shot.setTint(Phaser.Display.Color.HexStringToColor(this.stillTint).color);
        if (!fireOn) EventBus.emit(Events.STRUCTURE_FIRE, { target: 'arrow' } satisfies StructureFirePayload);
      }
      if (shot.fire)
        for (const p of this.puddles) if (p.fireUntil === 0 && p.rect.contains(pt.x, pt.y)) this.ignitePuddle(p);
      for (const s of this.list) {
        if (!this.isHittable(s) || !s.rect.contains(pt.x, pt.y)) continue;
        const v = shot.body.velocity;
        if (!shot.registerHit(s)) continue;
        const len = Math.hypot(v.x, v.y) || 1;
        this.onHit(s, v.x / len, v.y / len);
        if (!shot.active) break;
      }
    }
  }

  /** 무기 적중 직후 (근접·화살): 불붙은 무기·불화살이면 화상 */
  onMobHit(mob: Mob, viaFireArrow: boolean): void {
    if (!mob.active) return;
    if (!viaFireArrow && !this.fireActive) return;
    const def = this.stillDef;
    if (!def) return;
    const dmg = Math.max(1, Math.round(gameState.attack * num(def, 'burnAttackMult')));
    this.burns.set(mob, { ticks: num(def, 'burnTicks'), nextAt: this.now + num(def, 'burnTickMs'), dmg });
  }

  // =====================================================================
  // 타격형
  // =====================================================================

  private isHittable(s: Inst): boolean {
    if (s.state === 'broken' || s.state === 'used') return false;
    return s.kind === 'crate' || (s.kind === 'cask' && !s.rolling) || s.kind === 'hiddenWall' || s.kind === 'stakeBell';
  }

  private hitRect(r: Phaser.Geom.Rectangle, dirX: number, dirY: number): void {
    for (const s of [...this.list]) {
      if (!this.isHittable(s)) continue;
      if (!Phaser.Geom.Intersects.RectangleToRectangle(r, s.rect)) continue;
      this.onHit(s, dirX, dirY);
    }
  }

  private onHit(s: Inst, dirX: number, dirY: number): void {
    const now = this.now;
    if (now < s.lastHitAt + STRUCTURE_RULES.hitCooldownMs) return;
    s.lastHitAt = now;
    EventBus.emit(Events.STRUCTURE_HIT, this.evt(s));
    switch (s.kind) {
      case 'crate':
        this.breakCrate(s);
        break;
      case 'cask':
        this.setVisual(s, 'hit');
        this.startRoll(s, dirX, dirY);
        break;
      case 'hiddenWall':
        this.hitWall(s);
        break;
      case 'stakeBell':
        this.hitBell(s);
        break;
    }
  }

  private breakCrate(s: Inst): void {
    s.state = 'broken';
    this.removeBodies(s);
    this.setVisual(s, 'broken');
    this.emitBroken(s);
    const d = s.def;
    const rng = this.host.rng;
    const c = s.rect;
    const deltas: UiStructureResult['deltas'] = {};
    if (rng.chance(num(d, 'goldChance'))) {
      const [lo, hi] = d.params.gold as [number, number];
      const g = rng.int(lo, hi);
      this.host.spawnPickup(c.centerX, c.centerY, 'gold', g);
      deltas.gold = g;
    }
    if (rng.chance(num(d, 'potionChance'))) {
      this.host.spawnPickup(c.centerX + 6, c.centerY, 'potion', 1);
      deltas.potions = 1;
    }
  }

  // --- 1-1 독주 술통 ---

  private startRoll(s: Inst, dx: number, dy: number): void {
    const len = Math.hypot(dx, dy);
    if (len === 0 || s.rolling) return;
    s.rolling = { dx: dx / len, dy: dy / len, traveled: 0 };
    this.removeBodies(s);
    this.setVisual(s, 'active');
    const v = s.views[0];
    if (v.def?.rollRotate !== false) v.setRotation(Math.atan2(dy, dx) - Math.PI / 2);
  }

  private updateRolling(time: number, delta: number): void {
    for (const s of this.list) {
      const r = s.rolling;
      if (!r || s.state === 'broken') continue;
      const d = s.def;
      const speed = num(d, 'rollTilesPerSec') * TILE;
      const step = (speed * delta) / 1000;
      const cx = s.rect.centerX + r.dx * step;
      const cy = s.rect.centerY + r.dy * step;
      const half = s.rect.width / 2;
      // 벽·단단한 칸
      if (!this.host.world.isWalkableAt(cx + r.dx * half, cy + r.dy * half)) {
        this.shatterCask(s, time);
        continue;
      }
      // 다른 단단한 구조물
      const next = new Phaser.Geom.Rectangle(cx - half, cy - s.rect.height / 2, s.rect.width, s.rect.height);
      if (
        this.list.some(
          (o) => o !== s && o.bodies.length > 0 && Phaser.Geom.Intersects.RectangleToRectangle(next, o.rect),
        )
      ) {
        this.shatterCask(s, time);
        continue;
      }
      // 적
      let victim: Mob | null = null;
      for (const child of this.host.mobs.getChildren()) {
        const m = child as Mob;
        if (!m.active) continue;
        const b = m.body;
        if (Phaser.Geom.Intersects.RectangleToRectangle(next, new Phaser.Geom.Rectangle(b.x, b.y, b.width, b.height))) {
          victim = m;
          break;
        }
      }
      s.rect.setPosition(next.x, next.y);
      s.views[0].moveTo(next.centerX, next.bottom);
      r.traveled += step;
      if (victim) {
        const dmg = Math.round(gameState.attack * num(d, 'impactAttackMult'));
        if (this.host.hitMob(victim, dmg, { crit: false, dirX: r.dx, dirY: r.dy }))
          this.host.onKill(victim, 'environment');
        else victim.stun(time, num(d, 'impactStunMs'), 'hit');
        this.shatterCask(s, time);
        continue;
      }
      if (r.traveled >= num(d, 'rollMaxTiles') * TILE) this.stopRoll(s);
    }
  }

  /** 다 굴러가고 멈춤: 그 자리 칸에 다시 단단하게 */
  private stopRoll(s: Inst): void {
    s.rolling = null;
    const tx = Math.floor(s.rect.centerX / TILE);
    const ty = Math.floor(s.rect.centerY / TILE);
    s.rect.setPosition(tx * TILE, ty * TILE);
    s.p = { ...s.p, tx, ty };
    s.views[0].moveTo(s.rect.centerX, s.rect.bottom);
    s.views[0].setRotation(0);
    this.setVisual(s, 'idle');
    const z = this.host.scene.add.zone(s.rect.centerX, s.rect.centerY, s.rect.width, s.rect.height);
    this.solids.add(z);
    s.bodies.push(z);
    this.host.world.setBlocked(tx, ty, true);
  }

  private shatterCask(s: Inst, time: number): void {
    s.rolling = null;
    s.state = 'broken';
    s.views[0].setRotation(0);
    this.setVisual(s, 'broken');
    this.emitBroken(s);
    this.spawnPuddle(s.def, s.rect.centerX, s.rect.centerY, time);
  }

  private spawnPuddle(d: StructureDef, x: number, y: number, time: number): void {
    const size = num(d, 'puddleTiles') * TILE;
    const rect = new Phaser.Geom.Rectangle(x - size / 2, y - size / 2, size, size);
    const gfx = this.host.scene.add
      .rectangle(rect.centerX, rect.centerY, size, size, STRUCTURE_FX.PUDDLE_COLOR, STRUCTURE_FX.PUDDLE_ALPHA)
      .setDepth(STRUCTURE_FX.FLOOR_DEPTH);
    const p: Puddle = {
      rect,
      until: time + num(d, 'puddleMs'),
      fireUntil: 0,
      nextTick: 0,
      gfx,
      fireGfx: null,
      fireFx: [],
    };
    this.puddles.push(p);
    // 화로 곁이면 바로 불바다
    if (
      this.list.some((s) => s.kind === 'still' && Phaser.Geom.Intersects.RectangleToRectangle(rect, this.flameRect(s)))
    )
      this.ignitePuddle(p);
  }

  private ignitePuddlesIn(r: Phaser.Geom.Rectangle): void {
    for (const p of this.puddles)
      if (p.fireUntil === 0 && Phaser.Geom.Intersects.RectangleToRectangle(r, p.rect)) this.ignitePuddle(p);
  }

  private ignitePuddle(p: Puddle): void {
    const d = structureDef('cask');
    const now = this.now;
    p.fireUntil = now + num(d, 'fireMs');
    p.until = Math.max(p.until, p.fireUntil);
    p.nextTick = now + num(d, 'fireTickMs');
    const fxId = String(d.params.fireFx ?? 'fire_pool');
    const fx = this.host.fx;
    if (fx.has(fxId)) {
      // 48×24 시트로 3×3 타일을 덮기: y-10 / y+10 두 장, 두 번째는 1프레임 어긋나게 (아트 pivotNote)
      const dur = num(d, 'fireMs');
      p.fireFx.push(
        fx.play(fxId, p.rect.centerX, p.rect.centerY - 10, { depth: STRUCTURE_FX.FLOOR_DEPTH + 0.01, durationMs: dur }),
      );
      const second = fx.sheet(fxId)?.frameDurationsMs?.[0] ?? 110;
      this.host.scene.time.delayedCall(second, () => {
        if (p.fireUntil > this.now)
          p.fireFx.push(
            fx.play(fxId, p.rect.centerX, p.rect.centerY + 10, {
              depth: STRUCTURE_FX.FLOOR_DEPTH + 0.02,
              durationMs: Math.max(0, p.fireUntil - this.now),
            }),
          );
      });
    } else {
      p.fireGfx = this.host.scene.add
        .rectangle(
          p.rect.centerX,
          p.rect.centerY,
          p.rect.width,
          p.rect.height,
          STRUCTURE_FX.FIRE_COLOR,
          STRUCTURE_FX.FIRE_ALPHA,
        )
        .setDepth(STRUCTURE_FX.FLOOR_DEPTH + 0.01);
    }
    EventBus.emit(Events.STRUCTURE_FIRE, { target: 'pool' } satisfies StructureFirePayload);
    const cask = this.list.find((s) => s.kind === 'cask');
    if (cask) this.result(cask, 'info', txt(cask.def, 'ignite'), {});
  }

  private updatePuddles(time: number): void {
    const P = this.host.player;
    if (this.puddles.length === 0) {
      if (this.mobsSlowed) {
        for (const c of this.host.mobs.getChildren()) (c as Mob).speedMult = 1;
        this.mobsSlowed = false;
      }
      P.envSpeedMult = 1;
      return;
    }
    const d = structureDef('cask');
    const pc = P.body.center;
    let playerIn: Puddle | null = null;
    for (const p of this.puddles) if (p.rect.contains(pc.x, pc.y)) playerIn = p;
    P.envSpeedMult = playerIn ? 1 - num(d, 'playerSlow') : 1;
    for (const c of this.host.mobs.getChildren()) {
      const m = c as Mob;
      if (!m.active) continue;
      const inside = this.puddles.some((p) => p.rect.contains(m.body.center.x, m.body.center.y));
      m.speedMult = inside ? 1 - num(d, 'enemySlow') : 1;
    }
    this.mobsSlowed = true;
    // 불바다 틱
    for (const p of this.puddles) {
      if (p.fireUntil === 0 || time >= p.fireUntil || time < p.nextTick) continue;
      p.nextTick = time + num(d, 'fireTickMs');
      const dmg = Math.max(1, Math.round(gameState.attack * num(d, 'fireAttackMult')));
      for (const c of [...this.host.mobs.getChildren()]) {
        const m = c as Mob;
        if (!m.active || !p.rect.contains(m.body.center.x, m.body.center.y)) continue;
        if (this.host.hitMob(m, dmg, { crit: false, dirX: 0, dirY: 0, tick: true })) this.host.onKill(m, 'environment');
      }
      if (p.rect.contains(pc.x, pc.y)) P.takeHit(num(d, 'firePlayerAttack'), time);
    }
    // 만료
    for (const p of this.puddles) {
      const burntOut = p.fireUntil > 0 && time >= p.fireUntil;
      if (time < p.until && !burntOut) continue;
      p.gfx.destroy();
      p.fireGfx?.destroy();
      for (const h of p.fireFx) if (this.host.fx.isActive(h)) this.host.fx.stop(h);
    }
    this.puddles = this.puddles.filter((p) => time < p.until && !(p.fireUntil > 0 && time >= p.fireUntil));
  }

  // --- 1-2 증류 화로 · 화상 ---

  private get stillDef(): StructureDef | null {
    return this.list.find((s) => s.kind === 'still')?.def ?? null;
  }

  private get stillTint(): string {
    const d = this.stillDef;
    return d && typeof d.params.arrowTint === 'string' ? d.params.arrowTint : '#ff9a3c';
  }

  get fireActive(): boolean {
    return this.now < this.fireWeaponUntil;
  }

  /** 불꽃 영역: 시트 fireBox(프레임 좌표) → 월드, 없으면 발판. 여유 flamePadPx */
  private flameRect(s: Inst): Phaser.Geom.Rectangle {
    const pad = num(s.def, 'flamePadPx');
    const v = s.views[0];
    const fb = v.def?.fireBox;
    if (fb) {
      const a = v.frameToWorld(fb.x, fb.y);
      if (a) return new Phaser.Geom.Rectangle(a.x - pad, a.y - pad, fb.w + pad * 2, fb.h + pad * 2);
    }
    return new Phaser.Geom.Rectangle(s.rect.x - pad, s.rect.y - pad, s.rect.width + pad * 2, s.rect.height + pad * 2);
  }

  private touchesFlame(r: Phaser.Geom.Rectangle): boolean {
    return this.list.some(
      (s) => s.kind === 'still' && Phaser.Geom.Intersects.RectangleToRectangle(r, this.flameRect(s)),
    );
  }

  private igniteWeapon(target: 'weapon' | 'arrow'): void {
    const d = this.stillDef;
    if (!d) return;
    const was = this.fireActive;
    this.fireWeaponUntil = this.now + num(d, 'fireMs');
    if (!was) {
      EventBus.emit(Events.STRUCTURE_FIRE, { target } satisfies StructureFirePayload);
      const s = this.list.find((i) => i.kind === 'still')!;
      this.result(s, 'gain', txt(d, 'ignite'), {});
    }
  }

  private updateBurns(time: number): void {
    if (this.burns.size === 0) return;
    const d = this.stillDef;
    const tick = d ? num(d, 'burnTickMs') : 500;
    for (const [mob, b] of [...this.burns]) {
      if (!mob.active) {
        this.burns.delete(mob);
        continue;
      }
      if (time < b.nextAt) continue;
      b.nextAt = time + tick;
      b.ticks -= 1;
      if (this.host.hitMob(mob, b.dmg, { crit: false, dirX: 0, dirY: 0, tick: true })) {
        this.host.onKill(mob, 'attack');
        this.burns.delete(mob);
        continue;
      }
      mob.flashColor(STRUCTURE_FX.BURN_COLOR);
      if (b.ticks <= 0) this.burns.delete(mob);
    }
  }

  // --- 1-6 숨은 벽 ---

  private hitWall(s: Inst): void {
    s.hits += 1;
    const need = num(s.def, 'hits');
    if (s.hits < need) {
      this.setVisual(s, 'hit');
      this.host.scene.time.delayedCall(STRUCTURE_FX.HIT_FLASH_MS + 10, () => {
        if (s.state === 'idle') this.setVisual(s, `damaged${Math.min(2, s.hits)}`);
      });
      return;
    }
    s.state = 'broken';
    this.setVisual(s, 'broken');
    const c = s.p.cellar!;
    this.host.world.carveCellar(c.inner, c.opening, c.ring);
    this.emitBroken(s);
    this.fillCellar(s);
  }

  /** 저장고 안: 짐 3~4 + 70% 궤짝(반값) / 30% 물약 + 골드 */
  private fillCellar(s: Inst): void {
    const d = s.def;
    const c = s.p.cellar!;
    const rng = this.host.rng;
    const free: { x: number; y: number }[] = [];
    for (let y = c.inner.y; y < c.inner.y + c.inner.h; y++)
      for (let x = c.inner.x; x < c.inner.x + c.inner.w; x++) free.push({ x, y });
    // 입구 바로 안쪽 줄은 비워 통로로 둔다
    const nearOpening = (t: { x: number; y: number }) =>
      c.opening.some((o) => Math.abs(o.x - t.x) + Math.abs(o.y - t.y) <= 1);
    const spots = rng.shuffle(free.filter((t) => !nearOpening(t)));
    const used = new Set<string>();
    const take = (w: number, h: number): { x: number; y: number } | null => {
      for (const t of spots) {
        let ok = true;
        for (let y = t.y; y < t.y + h && ok; y++)
          for (let x = t.x; x < t.x + w && ok; x++) {
            const inside = x < c.inner.x + c.inner.w && y < c.inner.y + c.inner.h;
            if (!inside || used.has(`${x},${y}`) || nearOpening({ x, y })) ok = false;
          }
        if (!ok) continue;
        for (let y = t.y; y < t.y + h; y++) for (let x = t.x; x < t.x + w; x++) used.add(`${x},${y}`);
        return t;
      }
      return null;
    };
    const deltas: UiStructureResult['deltas'] = {};
    if (rng.chance(num(d, 'chestChance'))) {
      const chest = structureDef('chest');
      const t = take(chest.size[0], chest.size[1]);
      if (t) this.spawnExtra('chest', s.roomId, t.x, t.y, num(d, 'chestDiscount'));
    } else {
      const cx = (c.inner.x + c.inner.w / 2) * TILE;
      const cy = (c.inner.y + c.inner.h / 2) * TILE;
      for (let i = 0; i < num(d, 'potions'); i++) this.host.spawnPickup(cx + i * 8, cy, 'potion', 1);
      this.host.spawnPickup(cx, cy + 8, 'gold', num(d, 'gold'));
      deltas.potions = num(d, 'potions');
      deltas.gold = num(d, 'gold');
    }
    const [lo, hi] = d.params.crates as [number, number];
    const n = rng.int(lo, hi);
    for (let i = 0; i < n; i++) {
      const t = take(1, 1);
      if (t) this.spawnExtra('crate', s.roomId, t.x, t.y);
    }
    this.result(s, 'gain', txt(d, 'broken'), deltas);
  }

  private spawnExtra(kind: UiStructureKind, roomId: string, tx: number, ty: number, discount = 1): Inst {
    const d = structureDef(kind);
    const sprite = typeof d.sprite === 'string' ? d.sprite : (d.sprite[this.host.stageId] ?? d.sprite.default);
    return this.add(
      {
        id: `cellar-${kind}-${this.serial++}`,
        kind,
        roomId,
        tx,
        ty,
        w: d.size[0],
        h: d.size[1],
        solid: d.solid,
        sprite,
      },
      discount,
    );
  }

  // --- 2-4 판돈 종 ---

  private get bellParams() {
    const d = structureDef('stakeBell');
    return {
      hpPerRing: num(d, 'hpPerRing'),
      extraPerRing: num(d, 'extraPerRing'),
      goldPerRing: num(d, 'goldPerRing'),
      personalityPerRing: num(d, 'personalityPerRing'),
    };
  }

  private hitBell(s: Inst): void {
    const d = s.def;
    const max = num(d, 'maxRings');
    if (s.rings >= max) return;
    const next = stakeMods(this.stakeRings + 1, this.bellParams);
    const vars = {
      hp: Math.round((next.hpMult - 1) * 100),
      extra: next.extra,
      gold: next.goldMult.toFixed(1),
      pers: next.personalityMult.toFixed(1),
    };
    if (!s.warned) {
      s.warned = true;
      this.setVisual(s, 'hit');
      EventBus.emit(Events.STRUCTURE_BELL, {
        id: s.id,
        confirmed: false,
        rings: this.stakeRings,
      } satisfies StructureBellPayload);
      this.result(s, 'warn', txt(d, 'warn', vars), {});
      return;
    }
    s.warned = false;
    s.rings += 1;
    this.stakeRings += 1;
    this.setVisual(s, 'active');
    EventBus.emit(Events.STRUCTURE_BELL, {
      id: s.id,
      confirmed: true,
      rings: this.stakeRings,
    } satisfies StructureBellPayload);
    this.result(s, 'mixed', txt(d, 'rung', vars), {});
    if (s.rings >= max) {
      s.state = 'used';
      this.host.scene.time.delayedCall(600, () => this.setVisual(s, 'used'));
    }
  }

  // =====================================================================
  // E형
  // =====================================================================

  private updateInteract(input: InputState, delta: number): void {
    const pc = this.host.player.body.center;
    const range = STRUCTURE_RULES.interactRangePx;
    let best: Inst | null = null;
    let bestD = Infinity;
    for (const s of this.list) {
      if (!INTERACT_KINDS.includes(s.kind) || this.exhausted(s)) continue;
      const r = this.interactRect(s);
      const nx = Phaser.Math.Clamp(pc.x, r.left, r.right);
      const ny = Phaser.Math.Clamp(pc.y, r.top, r.bottom);
      const d = Math.hypot(pc.x - nx, pc.y - ny);
      if (d <= range && d < bestD) {
        bestD = d;
        best = s;
      }
    }
    if (best !== this.nearest) this.holdMs = 0;
    this.nearest = best;
    this.nearestReason = best ? this.reasonFor(best) : null;
    const pressed = input.interactPressed || this.debugInteract;
    this.debugInteract = false;
    if (!best) return;
    // C3 묘: 길게 누르기 (이동하면 0)
    if (best.kind === 'grave') {
      const moving = input.moveX !== 0 || input.moveY !== 0;
      const held = input.interactHeld || pressed;
      if (this.nearestReason === null && held && !moving) {
        this.holdMs += pressed && !input.interactHeld ? (best.def.holdMs ?? 2000) : delta;
        if (this.holdMs >= (best.def.holdMs ?? 2000)) {
          this.holdMs = 0;
          this.openGraveMenu(best);
        }
      } else this.holdMs = 0;
      return;
    }
    if (!pressed || this.nearestReason !== null) return;
    this.activate(best);
  }

  /** E 판정 영역: 투견 링은 판돈 깃대(시트 flagpost) 둘레, 그 외 발판 */
  private interactRect(s: Inst): Phaser.Geom.Rectangle {
    if (s.kind === 'dogRing') {
      const v = s.views[0];
      const fp = v.def?.flagpost;
      const w = fp ? v.frameToWorld(fp.x, fp.y) : null;
      if (w) return new Phaser.Geom.Rectangle(w.x - TILE / 2, w.y - TILE / 2, TILE, TILE);
      return new Phaser.Geom.Rectangle(s.rect.centerX - TILE / 2, s.rect.y, TILE, TILE);
    }
    return s.rect;
  }

  /** 더 할 수 있는 행동이 없음 → 안내·미니맵 점에서 빠진다 */
  private exhausted(s: Inst): boolean {
    if (s.state === 'used' || s.state === 'broken') return true;
    const d = s.def;
    switch (s.kind) {
      case 'ledger':
        return s.loans >= num(d, 'loansPerFloor') && this.debt <= 0;
      case 'counter':
        return s.cups >= num(d, 'cups');
      case 'cardTable':
        return s.round >= num(d, 'maxRounds');
      case 'exchange':
        return s.bloodUses >= num(d, 'bloodLimit') && s.lifeUses >= num(d, 'lifeLimit');
      default:
        return false;
    }
  }

  private reasonFor(s: Inst): UiInteractBlockReason | null {
    if (this.host.isBusy() || this.ring || this.cardFight) return 'busy';
    if (this.host.director.inCombat) return 'combat';
    const d = s.def;
    switch (s.kind) {
      case 'chest':
        return gameState.gold < this.chestCost(s) ? 'gold' : null;
      case 'campfire':
        return this.embers <= 0 ? 'notReady' : gameState.hp >= gameState.maxHp ? 'full' : null;
      case 'agingBarrel': {
        if (s.agingAt === null) return gameState.potions < num(d, 'potionIn') ? 'potion' : null;
        return this.agingReady(s) ? null : 'notReady';
      }
      case 'counter':
        return gameState.gold < num(d, 'cupPrice') ? 'gold' : this.drunk >= num(d, 'maxLevel') ? 'full' : null;
      case 'cardTable':
        return gameState.gold < cardStake(s.round + 1, this.cardParams(d)) ? 'gold' : null;
      case 'dogRing':
        return gameState.gold < num(d, 'stake') ? 'gold' : null;
      case 'pawn':
        return this.pawnLines(s).length === 0 ? 'limit' : null;
      default:
        return null;
    }
  }

  private costFor(s: Inst): UiCost | null {
    const d = s.def;
    const gold = (n: number): UiCost => ({
      kind: 'gold',
      amount: n,
      label: `${n}${STRUCTURE_TEXT.goldUnit}`,
      affordable: gameState.gold >= n,
    });
    switch (s.kind) {
      case 'chest':
        return gold(this.chestCost(s));
      case 'counter':
        return gold(num(d, 'cupPrice'));
      case 'cardTable':
        return gold(cardStake(s.round + 1, this.cardParams(d)));
      case 'dogRing':
        return gold(num(d, 'stake'));
      case 'agingBarrel':
        if (s.agingAt !== null) return null;
        return {
          kind: 'potion',
          amount: num(d, 'potionIn'),
          label: `잔의 독주 ${num(d, 'potionIn')}`,
          affordable: gameState.potions >= num(d, 'potionIn'),
        };
      case 'campfire':
        return this.embers > 0
          ? { kind: 'none', amount: this.embers, label: txt(d, 'costLabel', { n: this.embers }), affordable: true }
          : null;
      default:
        return null;
    }
  }

  private actionOf(s: Inst): { key: string; text: string } {
    const d = s.def;
    if (s.kind === 'agingBarrel') {
      if (s.agingAt === null) return { key: d.text.putActionKey, text: d.text.putAction };
      if (this.agingReady(s)) return { key: d.text.takeActionKey, text: d.text.takeAction };
      return { key: d.text.putActionKey, text: d.text.waitAction };
    }
    return { key: d.text.actionKey ?? `${s.kind}.use`, text: d.text.action ?? '' };
  }

  /** E 즉시 실행 또는 메뉴 */
  private activate(s: Inst): void {
    switch (s.kind) {
      case 'chest':
        return this.openChest(s);
      case 'campfire':
        return this.useCampfire(s);
      case 'agingBarrel':
        return this.useAging(s);
      case 'dogRing':
        return this.startRing(s);
      case 'ledger':
        return this.openLedger(s);
      case 'counter':
        return this.openCounter(s);
      case 'cardTable':
        return this.openCards(s);
      case 'exchange':
        return this.openExchange(s);
      case 'pawn':
        return this.openPawn(s);
    }
  }

  // --- C2 궤짝 ---

  private chestCost(s: Inst): number {
    const d = s.def;
    return chestPrice(
      { basePrice: num(d, 'basePrice'), stepPrice: num(d, 'stepPrice'), perFloorPrice: num(d, 'perFloorPrice') },
      this.chestsOpened,
      gameState.stageIndex,
      s.discount,
    );
  }

  private openChest(s: Inst): void {
    const d = s.def;
    const price = this.chestCost(s);
    if (gameState.gold < price) return;
    this.host.spendGold(price);
    this.chestsOpened += 1;
    s.state = 'used';
    this.setVisual(s, 'used');
    const pick = gameState.passives.rollChoices(this.host.rng, ECONOMY.rarity, 1)[0];
    if (pick) {
      gameState.passives.add(pick.id);
      EventBus.emit(Events.PASSIVE_GAINED, { id: pick.id, level: gameState.passives.level(pick.id) });
      this.result(s, 'mixed', txt(d, 'passive', { name: pick.name }), { gold: -price });
    } else {
      const refund = Math.round(price * num(d, 'fallbackRefund'));
      this.givePotions(s, num(d, 'fallbackPotions'));
      this.host.addGold(refund);
      this.result(s, 'mixed', txt(d, 'fallback', { potion: '잔의 독주', gold: refund }), {
        gold: refund - price,
        potions: num(d, 'fallbackPotions'),
      });
    }
    this.used(s, d.text.actionKey);
  }

  // --- C5 모닥불 ---

  private useCampfire(s: Inst): void {
    const d = s.def;
    if (this.embers <= 0) return;
    const before = gameState.hp;
    this.host.heal(emberHeal(this.embers, gameState.maxHp, num(d, 'healPerEmber')));
    const n = this.embers;
    this.embers = 0;
    this.setVisual(s, 'used');
    this.result(s, 'gain', txt(d, 'used', { n, hp: gameState.hp - before }), { hp: gameState.hp - before });
    if (d.params.restNoteOnUse) this.host.story('rest', floorText(gameState.stageId)?.restNote ?? '');
    this.used(s, d.text.actionKey);
  }

  // --- 1-4 숙성 통 ---

  private agingReady(s: Inst): boolean {
    if (s.agingAt === null) return false;
    return agingProgress(s.agingAt, gameState.trialsCleared, num(s.def, 'trialsNeeded')).ready;
  }

  private useAging(s: Inst): void {
    const d = s.def;
    if (s.agingAt === null) {
      const n = num(d, 'potionIn');
      if (gameState.potions < n) return;
      gameState.potions -= n;
      EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
      s.agingAt = gameState.trialsCleared;
      s.state = 'active';
      this.setVisual(s, 'active');
      this.result(s, 'info', txt(d, 'put', { n: num(d, 'trialsNeeded') }), { potions: -n });
      this.used(s, d.text.putActionKey);
      return;
    }
    if (!this.agingReady(s)) return;
    const out = num(d, 'potionsOut');
    this.givePotions(s, out);
    s.state = 'used';
    this.setVisual(s, 'used');
    this.result(s, 'gain', txt(d, 'take', { n: out }), { potions: out });
    this.used(s, d.text.takeActionKey);
  }

  /** 물약 지급: 소지 상한을 넘으면 구조물 앞 바닥에 드랍 */
  private givePotions(s: Inst, n: number): void {
    for (let i = 0; i < n; i++) {
      if (gameState.potions < this.host.potionCarry()) {
        gameState.potions += 1;
        EventBus.emit(Events.ITEM_PICKED, { kind: 'potion', value: 1 });
      } else this.host.spawnPickup(s.rect.centerX + (i - n / 2) * 8, s.rect.bottom + 8, 'potion', 1);
    }
    EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
  }

  // --- C3 묘 ---

  private openGraveMenu(s: Inst): void {
    const d = s.def;
    const souls = num(d, 'souls');
    const pers = num(d, 'personality');
    this.openMenu(
      'grave',
      s,
      txt(d, 'menuTitle'),
      [
        { key: '1', label: txt(d, 'record'), enabled: true, detail: txt(d, 'recordDetail', { souls }) },
        { key: '2', label: txt(d, 'accept'), enabled: true, detail: txt(d, 'acceptDetail', { personality: pers }) },
      ],
      (key) => {
        this.host.menu.close();
        s.state = 'used';
        this.setVisual(s, 'used');
        if (key === '1') {
          const m = metaStore.read();
          metaStore.write({ ...m, souls: m.souls + souls, totalSouls: m.totalSouls + souls });
          gameState.bonusSouls += souls;
          this.result(s, 'gain', txt(d, 'recorded', { souls }), { souls });
          this.used(s, 'grave.record');
        } else {
          this.host.gainPersonality(pers);
          this.result(s, 'gain', txt(d, 'accepted', { personality: pers }), { personality: pers });
          this.used(s, 'grave.accept');
        }
      },
    );
  }

  // --- 1-3 외상 장부대 ---

  private openLedger(s: Inst): void {
    const d = s.def;
    const loan = num(d, 'loan');
    const debtAdd = num(d, 'debt');
    const repay = Math.min(gameState.gold, this.debt);
    this.openMenu(
      'ledger',
      s,
      txt(d, 'menuTitle', { debt: this.debt }),
      [
        {
          key: '1',
          label: txt(d, 'borrow', { loan, debt: debtAdd }),
          enabled: s.loans < num(d, 'loansPerFloor'),
          detail: txt(d, 'borrowDetail', { pct: Math.round(num(d, 'repayRatio') * 100), hp: num(d, 'maxHpPer10Debt') }),
        },
        {
          key: '2',
          label: txt(d, 'repay', { amount: repay }),
          enabled: this.debt > 0 && repay > 0,
          detail: txt(d, 'repayDetail'),
        },
      ],
      (key) => {
        this.host.menu.close();
        if (key === '1') {
          s.loans += 1;
          this.debt += debtAdd;
          this.host.addGold(loan);
          this.setVisual(s, 'used');
          this.result(s, 'mixed', txt(d, 'borrowed', { loan, debt: this.debt }), { gold: loan });
          this.used(s, 'ledger.borrow');
        } else {
          const pay = Math.min(gameState.gold, this.debt);
          if (pay <= 0) return;
          this.host.spendGold(pay);
          this.debt -= pay;
          this.result(s, 'info', txt(d, 'repaid', { amount: pay, debt: this.debt }), { gold: -pay });
          this.used(s, 'ledger.repay');
        }
      },
    );
  }

  // --- 1-5 선술집 카운터 ---

  private get drunkParams(): DrunkParams {
    const d = structureDef('counter');
    return {
      maxLevel: num(d, 'maxLevel'),
      attackPerLevel: num(d, 'attackPerLevel'),
      defensePerLevel: num(d, 'defensePerLevel'),
      swayDegPerLevel: num(d, 'swayDegPerLevel'),
      swayPeriodMs: num(d, 'swayPeriodMs'),
      dashAttackBonusAtMax: num(d, 'dashAttackBonusAtMax'),
    };
  }

  private setDrunk(level: number): void {
    this.drunk = level;
    gameState.structureDefense = drunkMods(level, this.drunkParams).defense;
  }

  private openCounter(s: Inst): void {
    const d = s.def;
    const price = num(d, 'cupPrice');
    const P = this.drunkParams;
    const lines: UiMenuLine[] = [];
    for (let i = 0; i < num(d, 'cups'); i++) {
      const drunkCup = i < s.cups;
      const next = i === s.cups;
      lines.push({
        key: String(i + 1),
        label: drunkCup ? txt(d, 'cupEmpty', { n: i + 1 }) : txt(d, 'cup', { n: i + 1, price }),
        enabled: next && gameState.gold >= price && this.drunk < P.maxLevel,
        detail: txt(d, 'cupDetail', { atk: Math.round(P.attackPerLevel * 100), def: P.defensePerLevel }),
      });
    }
    this.openMenu('counter', s, txt(d, 'menuTitle', { level: this.drunk }), lines, () => {
      this.host.menu.close();
      if (gameState.gold < price) return;
      this.host.spendGold(price);
      s.cups += 1;
      this.setDrunk(Math.min(P.maxLevel, this.drunk + 1));
      if (s.cups >= num(d, 'cups')) {
        s.state = 'used';
        this.setVisual(s, 'used');
      } else this.setVisual(s, `used${s.cups}`);
      this.result(s, 'mixed', txt(d, 'drank', { level: this.drunk }), { gold: -price });
      this.used(s, 'counter.drink');
    });
  }

  private sober(): void {
    if (this.drunk <= 0) return;
    this.setDrunk(0);
    const s = this.list.find((i) => i.kind === 'counter');
    if (s) this.result(s, 'info', txt(s.def, 'sober'), {});
  }

  // --- 2-1 패 탁자 ---

  private cardParams(d: StructureDef) {
    return {
      stake: num(d, 'stake'),
      stakeStep: num(d, 'stakeStep'),
      goodGoldMult: num(d, 'goodGoldMult'),
      goodBoostPerRound: num(d, 'goodBoostPerRound'),
      goodWeights: d.params.goodWeights as Record<string, number>,
    };
  }

  private openCards(s: Inst): void {
    const d = s.def;
    const round = s.round + 1;
    const P = this.cardParams(d);
    const stake = cardStake(round, P);
    s.deck = dealCards(this.host.rng, stake, round, P);
    const can = gameState.gold >= stake;
    const lines: UiMenuLine[] = [1, 2, 3].map((n) => ({
      key: String(n),
      label: txt(d, 'card', { n }),
      enabled: can,
      detail: can ? txt(d, 'cardDetail', { stake }) : STRUCTURE_TEXT.reasons.gold,
    }));
    this.openMenu(
      'cards',
      s,
      txt(d, 'menuTitle', { stake, round, max: num(d, 'maxRounds') }),
      lines,
      (key) => {
        this.host.menu.close();
        const card = s.deck?.[Number(key) - 1];
        if (!card || gameState.gold < stake) return;
        this.host.spendGold(stake);
        s.round = round;
        this.setVisual(s, 'active');
        if (s.round >= num(d, 'maxRounds')) {
          s.state = 'used';
          this.host.scene.time.delayedCall(600, () => this.setVisual(s, 'used'));
        }
        this.used(s, `cards.pick${key}`);
        switch (card.kind) {
          case 'gold':
            this.host.addGold(card.gold);
            this.result(s, 'gain', txt(d, 'goodGold', { gold: card.gold }), { gold: card.gold - stake });
            break;
          case 'potion':
            this.givePotions(s, 1);
            this.result(s, 'mixed', txt(d, 'goodPotion'), { gold: -stake, potions: 1 });
            break;
          case 'point':
            gameState.pointsPending += 1;
            this.result(s, 'mixed', txt(d, 'goodPoint'), { gold: -stake, points: 1 });
            this.host.openStatChooser();
            break;
          case 'bad':
            this.result(s, 'loss', txt(d, 'bad'), { gold: -stake });
            this.startCardFight(s);
            break;
        }
      },
      txt(d, 'menuFooter'),
    );
  }

  private startCardFight(s: Inst): void {
    const d = s.def;
    const count = num(d, 'badCount');
    const ok = this.host.director.startChallenge(
      s.roomId,
      [{ enemy: String(d.params.badEnemy), count, hpMult: num(d, 'eliteHp'), attackMult: num(d, 'eliteAttack') }],
      () => {
        this.cardFight = null;
        this.challengeCleared(s, 'cardTable', 'clear', txt(d, 'challengeClear'));
      },
    );
    if (!ok) return;
    this.cardFight = s;
    this.challengeStarted(s, 'cardTable', txt(d, 'challengeLabel'), txt(d, 'challengeGoal', { n: count }), null);
  }

  // --- 2-2 목숨 칩 환전대 ---

  private openExchange(s: Inst): void {
    const d = s.def;
    const cost = bloodCost(gameState.hp, num(d, 'bloodHpRatio'));
    const bloodLeft = num(d, 'bloodLimit') - s.bloodUses;
    const lifeLeft = num(d, 'lifeLimit') - s.lifeUses;
    const lifeHp = num(d, 'lifeMaxHp');
    this.openMenu(
      'exchange',
      s,
      txt(d, 'menuTitle'),
      [
        {
          key: '1',
          label: txt(d, 'blood', { hp: cost, gold: num(d, 'bloodGold') }),
          enabled: bloodLeft > 0 && canSellBlood(gameState.hp, gameState.maxHp, num(d, 'bloodMinRatio')),
          detail: txt(d, 'bloodDetail', { pct: Math.round(num(d, 'bloodHpRatio') * 100), left: bloodLeft }),
        },
        {
          key: '2',
          label: txt(d, 'life', { maxHp: lifeHp, points: num(d, 'lifePoints') }),
          enabled: lifeLeft > 0 && gameState.maxHp > lifeHp + 1,
          detail: txt(d, 'lifeDetail', { left: lifeLeft }),
        },
      ],
      (key) => {
        this.host.menu.close();
        if (key === '1') {
          s.bloodUses += 1;
          const pay = bloodCost(gameState.hp, num(d, 'bloodHpRatio'));
          gameState.hp = Math.max(1, gameState.hp - pay);
          EventBus.emit(Events.PLAYER_DAMAGED, {
            hp: gameState.hp,
            maxHp: gameState.maxHp,
            amount: pay,
          } satisfies PlayerDamagedPayload);
          this.host.addGold(num(d, 'bloodGold'));
          this.result(s, 'mixed', txt(d, 'sold', { gold: num(d, 'bloodGold') }), {
            hp: -pay,
            gold: num(d, 'bloodGold'),
          });
          this.used(s, 'exchange.blood');
        } else {
          s.lifeUses += 1;
          this.loseMaxHp(lifeHp);
          gameState.pointsPending += num(d, 'lifePoints');
          this.result(s, 'mixed', txt(d, 'staked'), { maxHp: -lifeHp, points: num(d, 'lifePoints') });
          this.used(s, 'exchange.life');
          this.host.openStatChooser();
        }
        if (this.exhausted(s)) this.setVisual(s, 'used');
      },
    );
  }

  private loseMaxHp(n: number): void {
    const before = gameState.hp;
    gameState.maxHp = Math.max(1, gameState.maxHp - n);
    gameState.hp = Math.min(gameState.hp, gameState.maxHp);
    __system.emit(UI_EVENTS.PLAYER_DAMAGED, {
      hp: gameState.hp,
      maxHp: gameState.maxHp,
      amount: before - gameState.hp,
    });
  }

  // --- 2-3 투견 링 ---

  private startRing(s: Inst): void {
    const d = s.def;
    const stake = num(d, 'stake');
    if (gameState.gold < stake) return;
    const count = num(d, 'count');
    const center = { x: s.rect.centerX, y: s.rect.centerY };
    const ok = this.host.director.startChallenge(
      s.roomId,
      [{ enemy: String(d.params.enemy), count, hpMult: num(d, 'eliteHp'), attackMult: num(d, 'eliteAttack') }],
      () => this.finishRing(this.ring?.hits === 0 ? 'flawless' : 'clear'),
      { ...center, radiusTiles: num(d, 'spawnRadiusTiles') },
    );
    if (!ok) return;
    this.host.spendGold(stake);
    // 링 안으로
    this.host.player.body.reset(center.x, center.y + TILE * STRUCTURE_FX.RING_ENTER_TILES);
    const limit = num(d, 'timeLimitMs');
    this.ring = { inst: s, until: this.now + limit, hits: 0, max: count, stake };
    s.state = 'active';
    this.setVisual(s, 'active');
    this.used(s, d.text.actionKey);
    this.challengeStarted(
      s,
      'dogRing',
      txt(d, 'challengeLabel'),
      txt(d, 'challengeGoal', { sec: Math.round(limit / 1000), n: count }),
      limit,
    );
  }

  private updateRing(time: number): void {
    if (!this.ring || time < this.ring.until) return;
    this.host.director.abortChallenge();
    this.finishRing('timeout');
  }

  private finishRing(outcome: 'clear' | 'flawless' | 'timeout'): void {
    const r = this.ring;
    if (!r) return;
    this.ring = null;
    const s = r.inst;
    const d = s.def;
    s.state = 'used';
    this.setVisual(s, 'used');
    const gold = ringPayout(r.stake, outcome, { clearMult: num(d, 'clearMult'), flawlessMult: num(d, 'flawlessMult') });
    if (gold > 0) this.host.addGold(gold);
    const mult = outcome === 'flawless' ? num(d, 'flawlessMult') : num(d, 'clearMult');
    const text = outcome === 'timeout' ? txt(d, 'timeout') : txt(d, outcome, { mult, gold });
    this.result(s, outcome === 'timeout' ? 'loss' : 'gain', text, outcome === 'timeout' ? {} : { gold });
    this.challengeCleared(s, 'dogRing', outcome, text);
  }

  // --- 2-6 전당포 ---

  private pawnLines(s: Inst): { label: string; enabled: boolean; detail?: string; run: () => void }[] {
    const d = s.def;
    const P = { rarityValue: d.params.rarityValue as Record<string, number>, levelBonus: num(d, 'levelBonus') };
    const out: { label: string; enabled: boolean; detail?: string; run: () => void }[] = [];
    for (const [id, level] of Object.entries(gameState.passives.owned)) {
      const def = gameState.passives.def(id);
      if (!def) continue;
      const gold = pawnValue(def.rarity, level, P);
      out.push({
        label: txt(d, 'pawnPassive', { name: def.name, level, gold }),
        enabled: true,
        detail: def.description,
        run: () => {
          const lv = gameState.passives.remove(id);
          this.pawned.push({
            key: `p:${id}`,
            type: 'passive',
            passiveId: id,
            level: lv,
            name: def.name,
            received: gold,
          });
          this.host.addGold(gold);
          this.result(s, 'mixed', txt(d, 'pawned', { name: def.name, gold }), { gold });
        },
      });
    }
    if (gameState.potions > 0) {
      const gold = num(d, 'potionValue');
      out.push({
        label: txt(d, 'pawnPotion', { gold }),
        enabled: true,
        run: () => {
          gameState.potions -= 1;
          EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
          this.pawned.push({ key: `potion:${this.serial++}`, type: 'potion', name: '잔의 독주', received: gold });
          this.host.addGold(gold);
          this.result(s, 'mixed', txt(d, 'pawned', { name: '잔의 독주', gold }), { gold, potions: -1 });
        },
      });
    }
    for (const it of this.pawned) {
      const cost = redeemCost(it.received, num(d, 'redeemMult'));
      out.push({
        label: txt(d, 'redeem', { name: it.name, gold: cost }),
        enabled: gameState.gold >= cost && (it.type !== 'potion' || gameState.potions < this.host.potionCarry()),
        run: () => {
          if (gameState.gold < cost) return;
          this.host.spendGold(cost);
          this.pawned = this.pawned.filter((p) => p !== it);
          if (it.type === 'passive' && it.passiveId) {
            gameState.passives.setLevel(it.passiveId, it.level ?? 1);
            EventBus.emit(Events.PASSIVE_GAINED, { id: it.passiveId, level: gameState.passives.level(it.passiveId) });
          } else this.givePotions(s, 1);
          this.result(s, 'info', txt(d, 'redeemed', { name: it.name }), { gold: -cost });
        },
      });
    }
    return out;
  }

  private openPawn(s: Inst): void {
    const d = s.def;
    const all = this.pawnLines(s);
    if (all.length === 0) return;
    // UI 요청: 선택지 '1'~'8' + 그만두기 '0' (길면 8개까지만, 임시)
    const shown = all.slice(0, MENU_MAX_LINES);
    const lines: UiMenuLine[] = shown.map((l, i) => ({
      key: String(i + 1),
      label: l.label,
      enabled: l.enabled,
      detail: l.detail,
    }));
    this.openMenu(
      'pawn',
      s,
      txt(d, 'menuTitle', { gold: gameState.gold }),
      lines,
      (key) => {
        const pick = shown[Number(key) - 1];
        if (!pick) return;
        pick.run();
        this.used(s, 'pawn.deal');
        // 선택마다 다시 그림 (계약 §9.4)
        if (this.pawnLines(s).length > 0) this.openPawn(s);
        else this.host.menu.close();
      },
      txt(d, 'menuFooter'),
    );
  }

  // =====================================================================
  // 메뉴·이벤트 공통
  // =====================================================================

  private openMenu(
    id: UiStructureMenuId,
    s: Inst,
    title: string,
    lines: UiMenuLine[],
    onPick: (key: string) => void,
    footer = '',
  ): void {
    const body = lines.slice(0, MENU_MAX_LINES);
    body.push({ key: '0', label: STRUCTURE_TEXT.cancel, enabled: true });
    this.host.player.body.setVelocity(0, 0);
    this.host.menu.open(
      id,
      title,
      body,
      (key) => {
        if (key === '0') {
          this.host.menu.close();
          return;
        }
        onPick(key);
      },
      footer,
      { cancelKey: '0', structureId: s.id },
    );
  }

  private evt(s: Inst, actionKey?: string): StructureEventPayload {
    return { id: s.id, kind: s.kind, roomId: s.roomId, actionKey };
  }

  private used(s: Inst, actionKey: string): void {
    EventBus.emit(Events.STRUCTURE_USED, this.evt(s, actionKey));
    __system.emit(UI_EVENTS.STRUCTURE_USED, {
      id: s.id,
      kind: s.kind,
      roomId: s.roomId,
      actionKey,
    } satisfies UiStructureUsed);
  }

  private emitBroken(s: Inst): void {
    EventBus.emit(Events.STRUCTURE_BROKEN, this.evt(s));
    __system.emit(UI_EVENTS.STRUCTURE_BROKEN, { id: s.id, kind: s.kind, roomId: s.roomId } satisfies UiStructureBroken);
  }

  private result(s: Inst, tone: UiStructureResult['tone'], text: string, deltas: UiStructureResult['deltas']): void {
    const r: UiStructureResult = { id: s.id, kind: s.kind, tone, text, deltas };
    this.log.push(r);
    if (this.log.length > 20) this.log.shift();
    __system.emit(UI_EVENTS.STRUCTURE_RESULT, r);
  }

  private challengeStarted(
    s: Inst,
    kind: 'dogRing' | 'cardTable',
    label: string,
    goal: string,
    timeLimitMs: number | null,
  ): void {
    EventBus.emit(Events.CHALLENGE_STARTED, { id: s.id, kind } satisfies ChallengeEventPayload);
    __system.emit(UI_EVENTS.CHALLENGE_STARTED, {
      id: s.id,
      kind,
      roomId: s.roomId,
      label,
      goal,
      timeLimitMs,
    } satisfies UiChallengeStarted);
  }

  private challengeCleared(
    s: Inst,
    kind: 'dogRing' | 'cardTable',
    outcome: UiChallengeCleared['outcome'],
    text: string,
  ): void {
    EventBus.emit(Events.CHALLENGE_CLEARED, { id: s.id, kind, outcome } satisfies ChallengeEventPayload);
    __system.emit(UI_EVENTS.CHALLENGE_CLEARED, {
      id: s.id,
      kind,
      roomId: s.roomId,
      outcome,
      text,
    } satisfies UiChallengeCleared);
  }

  // =====================================================================
  // 이벤트 구독
  // =====================================================================

  /** 2-5 룰렛: 그 시련 방 시련 시작(웨이브 생성 전) → 규칙 결정 */
  private onTrialStarted(p: { roomId: string }): void {
    const s = this.list.find((i) => i.kind === 'roulette' && i.roomId === p.roomId && i.state === 'idle');
    if (!s) return;
    const rules = s.def.params.rules as Record<string, unknown>[];
    const idx = this.host.rng.int(0, rules.length - 1);
    s.state = 'active';
    this.roulette = { inst: s, roomId: p.roomId, ruleIndex: idx };
    this.setVisual(s, 'active');
    const stop = s.views[0].def?.stopFrames?.[String(idx)];
    this.host.scene.time.delayedCall(ROULETTE_SPIN_MS, () => {
      if (stop !== undefined && this.roulette?.inst === s) s.views[0].showFrame(stop);
    });
    EventBus.emit(Events.STRUCTURE_ROULETTE, this.evt(s));
    const rule = rules[idx];
    this.result(s, 'info', txt(s.def, 'spin', { rule: String(rule.name), detail: String(rule.detail) }), {});
  }

  private onTrialCleared(p: { roomId: string }): void {
    // C5 불씨 (모닥불이 있는 층만)
    const fire = this.list.find((i) => i.kind === 'campfire');
    if (fire) {
      const before = this.embers;
      this.embers = Math.min(num(fire.def, 'maxEmbers'), this.embers + num(fire.def, 'emberPerTrial'));
      if (this.embers > 0 && before === 0) this.setVisual(fire, 'active');
    }
    // 1-4 숙성 진행
    for (const s of this.list)
      if (s.kind === 'agingBarrel' && s.state === 'active' && this.agingReady(s)) this.setVisual(s, 'ready');
    // 1-5 취기 해제
    this.sober();
    // 2-5 룰렛 보너스
    if (this.roulette?.roomId === p.roomId) {
      const s = this.roulette.inst;
      const rule = this.ruleAt(this.roulette.ruleIndex);
      let gold = num(s.def, 'clearBonusGold');
      if (rule && typeof rule.trialBonusMult === 'number')
        gold += Math.round(ECONOMY.gold.trialBonus * (rule.trialBonusMult - 1));
      this.roulette = null;
      s.state = 'used';
      this.setVisual(s, 'used');
      this.host.addGold(gold);
      this.result(s, 'gain', txt(s.def, 'bonus', { gold }), { gold });
    }
  }

  /** 보스 처치: 1-3 빚 정산(최대 HP), 취기 해제 */
  private onBossDied(): void {
    const ledger = this.list.find((i) => i.kind === 'ledger');
    if (this.debt > 0 && ledger) {
      const hp = debtPenalty(this.debt, num(ledger.def, 'maxHpPer10Debt'));
      const debt = this.debt;
      this.debt = 0;
      this.loseMaxHp(hp);
      this.result(ledger, 'loss', txt(ledger.def, 'penalty', { debt, hp }), { maxHp: -hp });
    }
    this.sober();
  }

  /** 2-5 '받아쳐라': 패링·가드 성공마다 개성 */
  private onParried(): void {
    this.counterRule();
  }

  private onSecondary(p: PlayerSecondaryPayload): void {
    if (p.kind === 'guard' && p.phase === 'block') this.counterRule();
  }

  private counterRule(): void {
    const rule = this.activeRule();
    if (rule && typeof rule.parryPersonality === 'number') this.host.gainPersonality(rule.parryPersonality);
  }

  private onPlayerDamaged(p: PlayerDamagedPayload): void {
    if (this.ring && p.amount > 0) this.ring.hits += 1;
  }

  private ruleAt(i: number): Record<string, unknown> | null {
    const s = this.roulette?.inst ?? this.list.find((x) => x.kind === 'roulette');
    if (!s) return null;
    return (s.def.params.rules as Record<string, unknown>[])[i] ?? null;
  }

  /** 지금 적용 중인 룰렛 규칙 (그 시련 방이 진행 중일 때만) */
  private activeRule(): Record<string, number | string> | null {
    const r = this.roulette;
    if (!r) return null;
    const room = this.host.director.activeRoom;
    if (!room || room.id !== r.roomId) return null;
    return this.ruleAt(r.ruleIndex) as Record<string, number | string> | null;
  }

  // =====================================================================
  // 스냅샷 (계약 §9.1·9.2·9.5)
  // =====================================================================

  interactable(): UiInteractable | null {
    const s = this.nearest;
    if (!s || !s.views[0]) return null;
    const reason = this.nearestReason;
    const cam = this.host.scene.cameras.main;
    const ir = this.interactRect(s);
    const wx = ir.centerX;
    const wy = s.kind === 'dogRing' ? ir.top : Math.min(s.views[0].topY, s.rect.top);
    // 게임 캔버스 픽셀 (카메라 스크롤·배율 반영, 960×540 기준)
    const sx = (wx - cam.scrollX - cam.width * cam.originX) * cam.zoom + cam.width * cam.originX + cam.x;
    const sy = (wy - cam.scrollY - cam.height * cam.originY) * cam.zoom + cam.height * cam.originY + cam.y;
    const action = this.actionOf(s);
    const hold = s.kind === 'grave' ? (s.def.holdMs ?? 2000) : 0;
    return {
      id: s.id,
      kind: s.kind,
      name: s.def.name,
      roomId: s.roomId,
      key: STRUCTURE_RULES.interactKey,
      actionKey: action.key,
      action: action.text,
      cost: this.costFor(s),
      hold: hold > 0 ? { durationMs: hold, progress: Phaser.Math.Clamp(this.holdMs / hold, 0, 1) } : null,
      usable: reason === null,
      reason,
      reasonText: reason ? STRUCTURE_TEXT.reasons[reason] : '',
      screen: { x: Math.round(sx), y: Math.round(sy) },
    };
  }

  statuses(): UiStatus[] {
    const out: UiStatus[] = [];
    const now = this.now;
    const ledger = structureDef('ledger');
    if (this.debt > 0)
      out.push({
        id: 'debt',
        kind: 'debuff',
        label: txt(ledger, 'statusLabel'),
        value: `${this.debt}G`,
        amount: this.debt,
        detail: txt(ledger, 'statusDetail', { pct: Math.round(num(ledger, 'repayRatio') * 100) }),
      });
    if (this.drunk > 0) {
      const c = structureDef('counter');
      const P = this.drunkParams;
      const m = drunkMods(this.drunk, P);
      out.push({
        id: 'drunk',
        kind: 'buff',
        label: txt(c, 'statusLabel'),
        value: `${this.drunk}단`,
        amount: this.drunk,
        max: P.maxLevel,
        detail: txt(c, 'statusDetail', { atk: Math.round((m.attackMult - 1) * 100), def: m.defense, deg: m.swayDeg }),
      });
    }
    if (this.stakeRings > 0) {
      const b = structureDef('stakeBell');
      const m = stakeMods(this.stakeRings, this.bellParams);
      out.push({
        id: 'stakes',
        kind: 'debuff',
        label: txt(b, 'statusLabel'),
        value: `×${m.goldMult.toFixed(1)}`,
        amount: this.stakeRings,
        max: num(b, 'maxRings'),
        detail: txt(b, 'statusDetail', {
          hp: Math.round((m.hpMult - 1) * 100),
          extra: m.extra,
          gold: m.goldMult.toFixed(1),
          pers: m.personalityMult.toFixed(1),
        }),
      });
    }
    const fire = this.list.find((i) => i.kind === 'campfire');
    if (fire && this.embers > 0)
      out.push({
        id: 'embers',
        kind: 'resource',
        label: txt(fire.def, 'statusLabel'),
        value: String(this.embers),
        amount: this.embers,
        max: num(fire.def, 'maxEmbers'),
        detail: txt(fire.def, 'statusDetail', { pct: Math.round(num(fire.def, 'healPerEmber') * 100) }),
      });
    const still = this.stillDef;
    if (still && this.fireActive)
      out.push({
        id: 'fireWeapon',
        kind: 'buff',
        label: txt(still, 'statusLabel'),
        value: txt(still, 'statusValue'),
        remainMs: Math.max(0, this.fireWeaponUntil - now),
        durationMs: num(still, 'fireMs'),
        detail: txt(still, 'statusDetail'),
      });
    if (this.ring) {
      const d = this.ring.inst.def;
      const killed = Math.max(0, this.ring.max - this.host.director.debugInfo.alive);
      out.push({
        id: 'ring',
        kind: 'timer',
        label: txt(d, 'statusLabel'),
        value: `${killed}/${this.ring.max}`,
        amount: killed,
        max: this.ring.max,
        remainMs: Math.max(0, this.ring.until - now),
        durationMs: num(d, 'timeLimitMs'),
      });
    }
    if (this.roulette) {
      const rule = this.ruleAt(this.roulette.ruleIndex);
      if (rule)
        out.push({
          id: 'roulette',
          kind: 'rule',
          label: txt(this.roulette.inst.def, 'statusLabel'),
          value: String(rule.name),
          detail: String(rule.detail),
        });
    }
    for (const s of this.list) {
      if (s.kind !== 'agingBarrel' || s.agingAt === null || s.state === 'used') continue;
      const need = num(s.def, 'trialsNeeded');
      const g = agingProgress(s.agingAt, gameState.trialsCleared, need);
      out.push({
        id: 'aging',
        kind: 'progress',
        label: txt(s.def, 'statusLabel'),
        value: g.ready ? txt(s.def, 'statusDone') : `${g.done}/${need}`,
        amount: g.done,
        max: need,
        detail: txt(s.def, 'statusDetail', { n: need }),
      });
    }
    if (this.pawned.length > 0) {
      const p = structureDef('pawn');
      out.push({
        id: 'pawn',
        kind: 'resource',
        label: txt(p, 'statusLabel'),
        value: String(this.pawned.length),
        amount: this.pawned.length,
        detail: txt(p, 'statusDetail'),
      });
    }
    return out.sort((a, b) => ORDER.indexOf(a.id) - ORDER.indexOf(b.id));
  }

  /** 사용 가능한 E형 구조물이 남은 방 (미니맵 점) */
  structureRooms(): Set<string> {
    const out = new Set<string>();
    for (const s of this.list) if (INTERACT_KINDS.includes(s.kind) && !this.exhausted(s)) out.add(s.roomId);
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
    return this.list.map((s) => ({
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
      exhausted: INTERACT_KINDS.includes(s.kind) ? this.exhausted(s) : s.state !== 'idle',
      rolling: Boolean(s.rolling),
    }));
  }

  /** 구조물 앞(아래쪽 우선) 걸을 수 있는 지점 */
  standPoint(id: string): { x: number; y: number } | null {
    const s = this.list.find((i) => i.id === id);
    if (!s) return null;
    const r = this.interactRect(s);
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
    return {
      chestsOpened: this.chestsOpened,
      debt: this.debt,
      drunk: this.drunk,
      stakeRings: this.stakeRings,
      embers: this.embers,
      fireWeapon: this.fireActive,
      pawned: this.pawned.map((p) => ({ ...p })),
      ring: this.ring ? { id: this.ring.inst.id, remainMs: this.ring.until - this.now, hits: this.ring.hits } : null,
      cardFight: this.cardFight?.id ?? null,
      roulette: this.roulette ? { id: this.roulette.inst.id, rule: this.ruleAt(this.roulette.ruleIndex)?.id } : null,
      puddles: this.puddles.map((p) => ({ x: p.rect.centerX, y: p.rect.centerY, fire: p.fireUntil > this.now })),
      burns: this.burns.size,
      nearest: this.nearest?.id ?? null,
      reason: this.nearestReason,
      hold: this.holdMs,
      log: this.log.map((r) => ({ ...r })),
    };
  }

  /** 다음 update 에서 E 를 누른 것으로 친다 (묘는 즉시 완료) */
  debugPressE(): void {
    this.debugInteract = true;
  }

  /** 구조물을 플레이어 방향에서 한 번 친다 */
  debugHit(id: string): boolean {
    const s = this.list.find((i) => i.id === id);
    if (!s || !this.isHittable(s)) return false;
    const dx = s.rect.centerX - this.host.player.x;
    const dy = s.rect.centerY - this.host.player.y;
    const len = Math.hypot(dx, dy) || 1;
    s.lastHitAt = -Infinity;
    this.onHit(s, dx / len, dy / len);
    return true;
  }

  // =====================================================================

  private get now(): number {
    return this.host.scene.time.now;
  }

  destroy(): void {
    EventBus.off(Events.TRIAL_STARTED, this.onTrialStarted, this);
    EventBus.off(Events.TRIAL_CLEARED, this.onTrialCleared, this);
    EventBus.off(Events.BOSS_DIED, this.onBossDied, this);
    EventBus.off(Events.PLAYER_PARRIED, this.onParried, this);
    EventBus.off(Events.PLAYER_SECONDARY, this.onSecondary, this);
    EventBus.off(Events.PLAYER_DAMAGED, this.onPlayerDamaged, this);
    const world = this.host.scene.physics.world;
    if (world) for (const c of this.colliders) world.removeCollider(c);
    for (const s of this.list) for (const v of s.views) v.destroy();
    for (const p of this.puddles) {
      p.gfx.destroy();
      p.fireGfx?.destroy();
    }
    this.puddles = [];
    this.burns.clear();
    this.list.length = 0;
    gameState.structureDefense = 0;
  }
}
