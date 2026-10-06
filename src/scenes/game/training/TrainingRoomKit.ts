/**
 * 61 단계 6 (P14 §1) 수련장 방 준비물 — 데이터(`data/training.json` setup)대로 허수아비·줍기 물건·술 웅덩이·표식·적(다시 나옴)·
 * 만취 그림자(약한 보스)를 놓는다. 시험장 도구(LabDummy · LabTraits 의 웅덩이·적 부르기 방식)를 그대로 쓴다.
 */
import Phaser from 'phaser';
import { TILE } from '../../../core/Constants';
import { EventBus, Events } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BOSSES } from '../../../data';
import type { ConsumableId } from '../../../data/bundle2Types';
import type { TrainingRoomDef, TrainingSpawnDef, TrainingTuning } from '../../../data/training';
import { Boss } from '../../../objects/Boss';
import { Enemy } from '../../../objects/Enemy';
import { LabDummy } from '../../../objects/LabDummy';
import type { Pickup } from '../../../objects/Pickup';
import type { Game } from '../../Game';

/** 표식 그림 (임시 도형 — 아트 과제 표지판이 오면 바꾼다) */
const MARKER = { COLOR: 0xe8c070, ALPHA: 0.85, RADIUS_TILES: 0.45, LINE: 2 } as const;
/** 소모품이 바닥에 다시 놓이는 간격 (줍지 않고 사라졌을 때) */
const CONSUMABLE_RESPAWN_MS = 15000;
/** 보스가 나오기까지 (입구 걷힘이 끝난 뒤) */
const BOSS_DELAY_MS = 900;

interface SpawnSlot {
  def: TrainingSpawnDef;
  alive: Enemy[];
  nextAt: number;
}

export class TrainingRoomKit {
  readonly dummies: LabDummy[] = [];
  private slots: SpawnSlot[] = [];
  private marker: { x: number; y: number; gfx: Phaser.GameObjects.Graphics; reached: boolean } | null = null;
  private consumableAt = new Map<number, number>();
  boss: Boss | null = null;
  private bossTimer: Phaser.Time.TimerEvent | null = null;

  constructor(
    private readonly g: Game,
    private readonly room: TrainingRoomDef,
    private readonly tuning: TrainingTuning,
    /** 아직 이 방 과제가 남았나 (적·줍기 물건을 다시 놓을지) */
    private readonly wanted: () => boolean,
  ) {}

  /** 디버그: 표식 자리 */
  get markerAt(): { x: number; y: number; reached: boolean } | null {
    return this.marker ? { x: this.marker.x, y: this.marker.y, reached: this.marker.reached } : null;
  }

  /** 방 가운데 (월드 px) */
  center(): Phaser.Math.Vector2 {
    const g = this.g;
    const room = g.layout?.rooms[0];
    const c = room ? g.world.roomCenter(room) : { x: g.player.x, y: g.player.y };
    return new Phaser.Math.Vector2(c.x, c.y);
  }

  private at(t: readonly [number, number]): { x: number; y: number } {
    const c = this.center();
    return { x: c.x + t[0] * TILE, y: c.y + t[1] * TILE };
  }

  setup(): void {
    const g = this.g;
    const s = this.room.setup;
    for (const d of s.dummies ?? []) {
      const p = this.at(d.at);
      const dummy = new LabDummy(g, p.x, p.y, d.role);
      this.dummies.push(dummy);
      g.mobs.add(dummy);
    }
    (s.pickups ?? []).forEach((_p, i) => this.spawnPickup(i));
    for (const p of s.pools ?? []) {
      const q = this.at(p);
      if (g.world.isWalkableAt(q.x, q.y)) g.build.fx.liquorPool(q.x, q.y, TILE * 0.9, 600000);
    }
    if (s.marker) {
      const q = this.at(s.marker);
      const gfx = g.add.graphics().setDepth(1);
      gfx.lineStyle(MARKER.LINE, MARKER.COLOR, MARKER.ALPHA);
      gfx.strokeCircle(q.x, q.y, TILE * MARKER.RADIUS_TILES);
      gfx.fillStyle(MARKER.COLOR, 0.25);
      gfx.fillCircle(q.x, q.y, TILE * MARKER.RADIUS_TILES);
      this.marker = { x: q.x, y: q.y, gfx, reached: false };
    }
    const now = g.time.now;
    this.slots = (s.enemies ?? []).map((def) => ({ def, alive: [], nextAt: now + 600 }));
    if (s.boss) this.bossTimer = g.time.delayedCall(BOSS_DELAY_MS, () => this.spawnBoss());
  }

  update(now: number): void {
    const g = this.g;
    if (this.marker && !this.marker.reached) {
      const m = this.marker;
      if (Math.hypot(g.player.x - m.x, g.player.y - m.y) <= TILE * this.tuning.reachTiles) {
        m.reached = true;
        m.gfx.setAlpha(0.3);
        EventBus.emit(Events.TRAINING_REACH, {});
      }
    }
    if (!this.wanted()) return;
    for (const slot of this.slots) {
      slot.alive = slot.alive.filter((e) => e.active);
      if (slot.alive.length >= slot.def.count) {
        slot.nextAt = now + this.tuning.respawnMs;
        continue;
      }
      if (now < slot.nextAt) continue;
      this.spawnEnemy(slot);
      slot.nextAt = now + this.tuning.respawnMs;
    }
    this.refreshPickups(now);
  }

  private spawnEnemy(slot: SpawnSlot): void {
    const g = this.g;
    const c = this.center();
    for (let tries = 0; tries < 8; tries++) {
      const a = g.rng.next() * Math.PI * 2;
      const x = c.x + Math.cos(a) * TILE * this.tuning.enemyRingTiles;
      const y = c.y + Math.sin(a) * TILE * this.tuning.enemyRingTiles * 0.6;
      if (!g.world.isWalkableAt(x, y) || Math.hypot(x - g.player.x, y - g.player.y) < TILE * 3) continue;
      const e = new Enemy(g, x, y, slot.def.id);
      g.mobs.add(e);
      if (slot.def.elite) g.bundle.elites.makeElite(e, null);
      slot.alive.push(e);
      return;
    }
  }

  /** 줍기 물건: 전표·물약은 바닥에 없으면, 소모품은 칸이 비었고 한동안 없으면 다시 */
  private refreshPickups(now: number): void {
    const g = this.g;
    const list = this.room.setup.pickups ?? [];
    if (list.length === 0) return;
    const active = (kind: string) => (g.pickups.getChildren() as Pickup[]).some((p) => p.active && p.kind === kind);
    list.forEach((p, i) => {
      if (p.kind === 'consumable') {
        if (g.bundle.consumableUi().item !== null) return;
        if (now - (this.consumableAt.get(i) ?? 0) < CONSUMABLE_RESPAWN_MS) return;
        this.spawnPickup(i);
      } else if (!active(p.kind)) {
        if (p.kind === 'potion' && gameState.potions > 0) return;
        this.spawnPickup(i);
      }
    });
  }

  private spawnPickup(i: number): void {
    const g = this.g;
    const p = (this.room.setup.pickups ?? [])[i];
    if (!p) return;
    const q = this.at(p.at);
    if (p.kind === 'consumable') {
      g.bundle.consumables.spawnDrop(q.x, q.y, (p.id ?? 'fireBottle') as ConsumableId);
      this.consumableAt.set(i, g.time.now);
    } else g.economy.spawnPickup(q.x, q.y, p.kind, p.value ?? 1);
  }

  /** 만취 그림자: 이 층 보스를 약하게 (체력 bossHpMult) — 방 상태 머신 없이 바로 */
  private spawnBoss(): void {
    const g = this.g;
    this.bossTimer = null;
    if (!g.scene.isActive()) return;
    const id = gameState.stage.boss;
    const def = BOSSES[id];
    if (!def) return;
    const room = g.layout?.rooms.find((r) => r.type === 'boss') ?? g.layout?.rooms[0];
    if (!room) return;
    const c = g.world.roomCenter(room);
    const off = def.spawnOffsetTiles;
    const sx = c.x + (off?.[0] ?? 0) * TILE;
    const sy = c.y + (off?.[1] ?? 0) * TILE;
    const at = g.world.isWalkableAt(sx, sy) ? { x: sx, y: sy } : c;
    const boss = new Boss(g, at.x, at.y, id);
    boss.scaleMaxHp(this.tuning.bossHpMult);
    gameState.bossHp = boss.hp;
    gameState.bossMaxHp = boss.maxHp;
    g.mobs.add(boss);
    this.boss = boss;
    EventBus.emit(Events.BOSS_STARTED, { roomId: room.id, boss: id });
  }

  destroy(): void {
    this.bossTimer?.remove(false);
    this.bossTimer = null;
    this.marker?.gfx.destroy();
    this.marker = null;
    this.slots = [];
    this.dummies.length = 0;
    this.boss = null;
  }
}
