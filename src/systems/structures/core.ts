/**
 * 구조물 런타임 공통부 (50라운드 1단계 분리): 인스턴스 목록·물리 바디·층 상태(빚·취기·판돈·불씨·불붙은 무기·전당·숙성)와
 * 그림 상태·결과 알림·메뉴·도전 이벤트 같은 공통 동작. 종류별 동작은 kinds/*.ts, 상호작용(E)은 interact.ts.
 */
import Phaser from 'phaser';
import { TILE } from '../../core/Constants';
import { EventBus, Events, type ChallengeEventPayload, type StructureEventPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import {
  UI_EVENTS,
  __system,
  type StoryKind,
  type UiChallengeCleared,
  type UiChallengeStarted,
  type UiMenuLine,
  type UiStructureBroken,
  type UiStructureKind,
  type UiStructureMenuId,
  type UiStructureResult,
  type UiStructureUsed,
} from '../../contract/ui';
import type { Mob } from '../../objects/Mob';
import type { Player } from '../../objects/Player';
import type { LiquorPools } from '../hazards/LiquorPools';
import type { FxPool } from '../fx';
import type { RoomDirector } from '../RoomDirector';
import type { Rng } from '../rng';
import type { KillKind } from '../senses';
import type { TextMenu } from '../TextMenu';
import type { TileWorld } from '../../world/TileWorld';
import { StructureView } from '../../world/StructureView';
import { STRUCTURE_TEXT, num, structureDef, type StructureDef } from './data';
import type { StructurePlacement } from './placement';
import { drunkMods, stakeMods, type CardOutcome, type DrunkParams } from './rules';

/** Game 이 넘겨주는 것 (씬 직접 참조 대신 필요한 것만) */
export interface StructureHost {
  scene: Phaser.Scene;
  world: TileWorld;
  director: RoomDirector;
  player: Player;
  mobs: Phaser.Physics.Arcade.Group;
  menu: TextMenu;
  fx: FxPool;
  /** 54라운드: 술 웅덩이·불바다 (보스방과 같은 목록, systems/hazards/LiquorPools) */
  pools: LiquorPools;
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
  /** 메뉴·연출·보상 중 */
  isBusy(): boolean;
  openStatChooser(): void;
  story(kind: StoryKind, text: string): void;
  /**
   * 48라운드 노드 지도: 층 상태(빚·취기·판돈·불씨·불붙은 무기·전당·궤짝 수·숙성)를 노드 사이에 들고 다닌다.
   * 불씨는 모닥불이 없는 노드에서도 쌓이고, 숙성 통에 넣은 물약은 노드를 떠나도 익으면 자동으로 받는다
   */
  nodeMode?: boolean;
}

/** 48라운드: 노드 사이에 들고 다니는 층 상태 (Q13 '층 안에서 완결' 을 노드 진행에 맞게) */
export interface StructureFloorCarry {
  chestsOpened: number;
  debt: number;
  drunk: number;
  stakeRings: number;
  embers: number;
  /** 남은 ms (씬 시각이 노드마다 이어지지만 안전하게 남은 시간으로) */
  fireWeaponMs: number;
  pawned: Pawned[];
  /** 숙성 통에 넣은 시점 (trialsCleared) 목록 */
  aging: number[];
}

export type InstState = 'idle' | 'used' | 'broken' | 'active';

export interface Inst {
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

export interface Pawned {
  key: string;
  type: 'passive' | 'potion';
  passiveId?: string;
  level?: number;
  name: string;
  received: number;
}

/** 메뉴 선택지 최대 (그만두기 제외) — UI 요청: '1'~'8' + '0' */
export const MENU_MAX_LINES = 8;

export class StructureCore {
  readonly list: Inst[] = [];
  readonly solids: Phaser.Physics.Arcade.StaticGroup;
  serial = 0;
  // --- 층 상태 (Q13: 층 안에서 완결, 48라운드: 노드 사이 이어받기) ---
  chestsOpened = 0;
  debt = 0;
  drunk = 0;
  stakeRings = 0;
  embers = 0;
  fireWeaponUntil = 0;
  pawned: Pawned[] = [];
  /** 48라운드: 앞 노드 숙성 통에 넣은 물약 (넣은 시점의 trialsCleared) */
  agingCarry: number[] = [];
  // --- 진행 중인 도전·규칙 ---
  ring: { inst: Inst; until: number; hits: number; max: number; stake: number } | null = null;
  cardFight: Inst | null = null;
  roulette: { inst: Inst; roomId: string; ruleIndex: number } | null = null;
  /** 디버그: 최근 결과 */
  readonly log: UiStructureResult[] = [];

  constructor(readonly host: StructureHost) {
    this.solids = host.scene.physics.add.staticGroup();
  }

  get now(): number {
    return this.host.scene.time.now;
  }

  find(kind: UiStructureKind): Inst | undefined {
    return this.list.find((i) => i.kind === kind);
  }

  // --- 생성 · 그림 · 바디 ---

  add(p: StructurePlacement, discount = 1): Inst {
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
    if (p.solid && p.kind !== 'hiddenWall') this.addSolid(inst);
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

  /** 발판 전체를 단단하게 (바디 + 걸을 수 없는 칸) */
  addSolid(inst: Inst): void {
    const r = inst.rect;
    const z = this.host.scene.add.zone(r.centerX, r.centerY, r.width, r.height);
    this.solids.add(z);
    inst.bodies.push(z);
    for (let y = inst.p.ty; y < inst.p.ty + inst.p.h; y++)
      for (let x = inst.p.tx; x < inst.p.tx + inst.p.w; x++) this.host.world.setBlocked(x, y, true);
  }

  /** 모든 그림에 같은 상태 (숨은 벽: 북쪽 벽이 아니면 `_top` 변형) */
  setVisual(inst: Inst, state: string): void {
    for (const v of inst.views) {
      let s = state;
      if (inst.kind === 'hiddenWall' && inst.p.cellar && inst.p.cellar.side !== 'N' && state !== 'broken') {
        if (v.hasState(`${state}_top`)) s = `${state}_top`;
      }
      if (inst.kind === 'grave' && gameState.stageIndex === 1 && v.hasState(`${state}_f2`)) s = `${state}_f2`;
      v.setState(s);
    }
  }

  removeBodies(inst: Inst): void {
    for (const z of inst.bodies) this.solids.remove(z, true, true);
    inst.bodies = [];
    for (let y = inst.p.ty; y < inst.p.ty + inst.p.h; y++)
      for (let x = inst.p.tx; x < inst.p.tx + inst.p.w; x++) this.host.world.setBlocked(x, y, false);
  }

  /** 저장고 등에서 새로 놓는 구조물 */
  spawnExtra(kind: UiStructureKind, roomId: string, tx: number, ty: number, discount = 1): Inst {
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

  // --- 플레이어 자원 ---

  /** 물약 지급: 소지 상한을 넘으면 구조물 앞 바닥에 드랍 */
  givePotions(s: Inst, n: number): void {
    for (let i = 0; i < n; i++) {
      if (gameState.potions < this.host.potionCarry()) {
        gameState.potions += 1;
        EventBus.emit(Events.ITEM_PICKED, { kind: 'potion', value: 1 });
      } else this.host.spawnPickup(s.rect.centerX + (i - n / 2) * 8, s.rect.bottom + 8, 'potion', 1);
    }
    EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
  }

  loseMaxHp(n: number): void {
    const before = gameState.hp;
    gameState.maxHp = Math.max(1, gameState.maxHp - n);
    gameState.hp = Math.min(gameState.hp, gameState.maxHp);
    __system.emit(UI_EVENTS.PLAYER_DAMAGED, {
      hp: gameState.hp,
      maxHp: gameState.maxHp,
      amount: before - gameState.hp,
    });
  }

  // --- 층 상태 수치 (데이터에서) ---

  get drunkParams(): DrunkParams {
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

  setDrunk(level: number): void {
    this.drunk = level;
    gameState.structureDefense = drunkMods(level, this.drunkParams).defense;
  }

  get bellParams() {
    const d = structureDef('stakeBell');
    return {
      hpPerRing: num(d, 'hpPerRing'),
      extraPerRing: num(d, 'extraPerRing'),
      goldPerRing: num(d, 'goldPerRing'),
      personalityPerRing: num(d, 'personalityPerRing'),
    };
  }

  /** 판돈 종 현재 배율 */
  get stakes(): ReturnType<typeof stakeMods> {
    return stakeMods(this.stakeRings, this.bellParams);
  }

  get stillDef(): StructureDef | null {
    return this.find('still')?.def ?? null;
  }

  get fireActive(): boolean {
    return this.now < this.fireWeaponUntil;
  }

  ruleAt(i: number): Record<string, unknown> | null {
    const s = this.roulette?.inst ?? this.find('roulette');
    if (!s) return null;
    return (s.def.params.rules as Record<string, unknown>[])[i] ?? null;
  }

  /** 지금 적용 중인 룰렛 규칙 (그 시련 방이 진행 중일 때만) */
  activeRule(): Record<string, number | string> | null {
    const r = this.roulette;
    if (!r) return null;
    const room = this.host.director.activeRoom;
    if (!room || room.id !== r.roomId) return null;
    return this.ruleAt(r.ruleIndex) as Record<string, number | string> | null;
  }

  // --- 메뉴 · 이벤트 공통 ---

  openMenu(
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

  evt(s: Inst, actionKey?: string): StructureEventPayload {
    return { id: s.id, kind: s.kind, roomId: s.roomId, actionKey };
  }

  used(s: Inst, actionKey: string): void {
    EventBus.emit(Events.STRUCTURE_USED, this.evt(s, actionKey));
    __system.emit(UI_EVENTS.STRUCTURE_USED, {
      id: s.id,
      kind: s.kind,
      roomId: s.roomId,
      actionKey,
    } satisfies UiStructureUsed);
  }

  emitBroken(s: Inst): void {
    EventBus.emit(Events.STRUCTURE_BROKEN, this.evt(s));
    __system.emit(UI_EVENTS.STRUCTURE_BROKEN, { id: s.id, kind: s.kind, roomId: s.roomId } satisfies UiStructureBroken);
  }

  result(s: Inst, tone: UiStructureResult['tone'], text: string, deltas: UiStructureResult['deltas']): void {
    this.resultOf(s.kind, s.id, tone, text, deltas);
  }

  /** 결과 알림 (48라운드: 인스턴스가 없는 노드에서의 정산·숙성 배달도 같은 경로) */
  resultOf(
    kind: UiStructureKind,
    id: string,
    tone: UiStructureResult['tone'],
    text: string,
    deltas: UiStructureResult['deltas'],
  ): void {
    const r: UiStructureResult = { id, kind, tone, text, deltas };
    this.log.push(r);
    if (this.log.length > 20) this.log.shift();
    __system.emit(UI_EVENTS.STRUCTURE_RESULT, r);
  }

  challengeStarted(
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

  challengeCleared(s: Inst, kind: 'dogRing' | 'cardTable', outcome: UiChallengeCleared['outcome'], text: string): void {
    EventBus.emit(Events.CHALLENGE_CLEARED, { id: s.id, kind, outcome } satisfies ChallengeEventPayload);
    __system.emit(UI_EVENTS.CHALLENGE_CLEARED, {
      id: s.id,
      kind,
      roomId: s.roomId,
      outcome,
      text,
    } satisfies UiChallengeCleared);
  }
}
