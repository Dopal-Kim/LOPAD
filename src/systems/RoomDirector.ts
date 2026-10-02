import Phaser from 'phaser';
import { TILE } from '../core/Constants';
import { EventBus, Events, type RoomEnteredPayload, type TrialClearedPayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import type { StageDef, WaveEntry } from '../data/types';
import { Boss } from '../objects/Boss';
import { Enemy } from '../objects/Enemy';
import type { Mob } from '../objects/Mob';
import type { TileWorld } from '../world/TileWorld';
import type { Room } from './mapgen';
import { Rng } from './rng';
import { isInCombat, type RoomProgress } from './traversal';
import { scaleWave } from './structures/rules';

type RoomState = RoomProgress;

/** 47라운드: 시련 웨이브 배율 (2-4 판돈 종 · 2-5 룰렛). 없으면 1·1·0 */
export interface WaveMods {
  hpMult: number;
  countMult: number;
  extra: number;
}

/** 47라운드: 구조물 도전(투견 링·흉패)으로 부르는 적 */
export interface ChallengeSpawn {
  enemy: string;
  count: number;
  hpMult: number;
  attackMult: number;
}

export interface RoomDirectorHost {
  world: TileWorld;
  stage: StageDef;
  rng: Rng;
  player: { x: number; y: number };
  mobs: Phaser.Physics.Arcade.Group;
  heal(fraction: number): void;
  onRunCleared(): void;
  /** 마지막 층이 아니면 보스 방에 출구를 연다 */
  onStageCleared(room: Room): void;
  isLastStage(): boolean;
  /** 47라운드: 시련 웨이브 배율 (웨이브를 낼 때마다 묻는다) */
  waveMods?(room: Room): WaveMods;
  /** 48라운드 노드 전투장: 이 노드 전용 웨이브 (버려진 길 = 쉬운 전투). 없으면 층 trial.waves */
  waves?: WaveEntry[][];
}

/**
 * 방 상태 머신: 시련(문 잠금 → 웨이브 → 해제), 휴식(회복), 보스(잠금 해제 → 전투 → 클리어).
 * 방 진입 판정은 플레이어 중심이 방 내부 바닥에 들어온 순간.
 */
export class RoomDirector {
  private states = new Map<string, RoomState>();
  private currentRoom?: Room;
  private waveIndex = 0;
  private alive = new Set<Mob>();
  /** 47라운드: 진행 중인 구조물 도전 (클리어한 방을 다시 active 로 — 45라운드 비전투 판정과 일관) */
  private challenge: { roomId: string; onDone: () => void } | null = null;

  constructor(private host: RoomDirectorHost) {
    for (const r of host.world.layout.rooms) this.states.set(r.id, 'idle');
    this.states.set('start', 'cleared');
    gameState.trialsTotal = host.stage.layout.trialCount;
  }

  /** 시련 웨이브 목록 (48라운드: 노드 전용 웨이브가 있으면 그것) */
  private get waves(): WaveEntry[][] {
    return this.host.waves ?? this.host.stage.trial.waves;
  }

  /** 디버그용: 현재 활성 방의 남은 적 수와 웨이브 번호 */
  get debugInfo(): { alive: number; wave: number; active: string | undefined } {
    return { alive: this.alive.size, wave: this.waveIndex, active: this.activeRoom?.id };
  }

  /** 45라운드: 비전투 판정의 단일 기준 — 활성 전투 방(시련 웨이브·보스전 진행 중)이 있으면 true */
  get inCombat(): boolean {
    return isInCombat(this.states);
  }

  /** 방별 진행 상태 (워프 대상 판정용, 읽기 전용) */
  get progress(): ReadonlyMap<string, RoomProgress> {
    return this.states;
  }

  get activeRoom(): Room | undefined {
    return this.currentRoom && this.states.get(this.currentRoom.id) === 'active' ? this.currentRoom : undefined;
  }

  /** 매 프레임: 플레이어가 어느 방 내부에 있는지 추적 */
  update(): void {
    const cell = this.host.world.cellAt(this.host.player.x, this.host.player.y);
    const room = this.host.world.roomAtCell(cell);
    if (!room) return;
    if (this.currentRoom?.id === room.id) return;
    if (!this.host.world.isInsideRoom(room, this.host.player.x, this.host.player.y)) return;
    this.currentRoom = room;
    gameState.roomId = room.id;
    gameState.roomType = room.type;
    const payload: RoomEnteredPayload = { roomId: room.id, type: room.type };
    EventBus.emit(Events.ROOM_ENTERED, payload);
    if (this.states.get(room.id) !== 'idle') return;
    switch (room.type) {
      case 'start':
        // 48라운드 노드 전투장(탄생지·상점·이벤트): 비전투 방은 들어서면 클리어
        this.states.set(room.id, 'cleared');
        break;
      case 'trial':
        this.startTrial(room);
        break;
      case 'rest':
        this.states.set(room.id, 'cleared');
        this.host.heal(this.host.stage.rest.healFraction);
        break;
      case 'boss':
        this.startBoss(room);
        break;
    }
  }

  /**
   * 보스 소환(35라운드 2단계): 활성 방에 적을 추가한다. 걸을 수 없는 자리면 방 안 무작위 지점으로.
   * 처치 대기 목록에 들어가므로 보스가 죽으면 함께 정리된다
   */
  spawnExtra(enemyId: string, x: number, y: number): boolean {
    const room = this.activeRoom;
    if (!room) return false;
    let p = { x, y };
    if (!this.host.world.isWalkableAt(x, y) || !this.host.world.isInsideRoom(room, x, y)) {
      const q = this.host.world.randomPointInRoom(room, this.host.rng, this.host.player, 2);
      p = { x: q.x, y: q.y };
    }
    const e = new Enemy(this.host.mobs.scene, p.x, p.y, enemyId, this.host.stage.enemyScale);
    this.host.mobs.add(e);
    this.alive.add(e);
    return true;
  }

  /** 방 진행 상태 */
  stateOf(roomId: string): RoomProgress | undefined {
    return this.states.get(roomId);
  }

  /** 진행 중인 구조물 도전의 방 id (없으면 null) */
  get challengeRoomId(): string | null {
    return this.challenge?.roomId ?? null;
  }

  /**
   * 47라운드 구조물 도전 시작 (2-3 투견 링 · 2-1 흉패): 클리어한 방을 다시 active 로 만들고 문을 닫은 뒤 적을 부른다.
   * at 이 있으면 그 지점 반경 radiusTiles 안, 없으면 방 안 무작위(플레이어에게서 4칸 이상). 전멸하면 onDone
   */
  startChallenge(
    roomId: string,
    spawns: readonly ChallengeSpawn[],
    onDone: () => void,
    at?: { x: number; y: number; radiusTiles: number },
  ): boolean {
    if (this.inCombat || this.challenge || this.states.get(roomId) !== 'cleared') return false;
    const room = this.host.world.room(roomId);
    this.challenge = { roomId, onDone };
    this.states.set(roomId, 'active');
    this.currentRoom = room;
    this.host.world.setRoomDoors(room, 'closed');
    const S = this.host.stage.enemyScale;
    for (const sp of spawns) {
      for (let i = 0; i < sp.count; i++) {
        let p = this.host.world.randomPointInRoom(room, this.host.rng, this.host.player, 4);
        if (at) {
          for (let t = 0; t < 30; t++) {
            const a = this.host.rng.next() * Math.PI * 2;
            const r = (0.4 + this.host.rng.next() * 0.6) * at.radiusTiles * TILE;
            const q = new Phaser.Math.Vector2(at.x + Math.cos(a) * r, at.y + Math.sin(a) * r);
            if (this.host.world.isWalkableAt(q.x, q.y) && this.host.world.isInsideRoom(room, q.x, q.y)) {
              p = q;
              break;
            }
          }
        }
        const e = new Enemy(this.host.mobs.scene, p.x, p.y, sp.enemy, {
          hp: S.hp * sp.hpMult,
          attack: S.attack * sp.attackMult,
        });
        this.host.mobs.add(e);
        this.alive.add(e);
      }
    }
    return true;
  }

  /** 47라운드: 도전 강제 종료 (투견 링 시간 초과) — 남은 적은 사라지고 방은 다시 클리어. onDone 은 부르지 않는다 */
  abortChallenge(): number {
    if (!this.challenge) return 0;
    let n = 0;
    for (const m of [...this.alive]) {
      if (m.active) {
        m.visual.spawnCorpse();
        m.destroy();
        n++;
      }
    }
    this.alive.clear();
    this.endChallenge();
    return n;
  }

  private endChallenge(): { onDone: () => void } | null {
    const c = this.challenge;
    if (!c) return null;
    this.challenge = null;
    this.states.set(c.roomId, 'cleared');
    this.host.world.setRoomDoors(this.host.world.room(c.roomId), 'open');
    return c;
  }

  /** 적 사망 시 호출 */
  onMobDied(mob: Mob): void {
    this.alive.delete(mob);
    if (this.challenge) {
      if (this.alive.size === 0) this.endChallenge()?.onDone();
      return;
    }
    const room = this.activeRoom;
    if (!room) return;
    // 보스가 죽으면 소환된 부하는 함께 사라진다 (보상 없음)
    if (room.type === 'boss' && mob.isBoss) {
      for (const m of [...this.alive]) {
        if (m.active) {
          m.visual.spawnCorpse();
          m.destroy();
        }
      }
      this.alive.clear();
    }
    if (this.alive.size > 0) return;
    if (room.type === 'trial') {
      this.waveIndex += 1;
      if (this.waveIndex < this.waves.length) {
        this.spawnWave(room, this.waveIndex);
      } else {
        this.clearTrial(room);
      }
    } else if (room.type === 'boss') {
      this.states.set(room.id, 'cleared');
      this.host.world.setRoomDoors(room, 'open');
      if (this.host.isLastStage()) {
        gameState.cleared = true;
        EventBus.emit(Events.RUN_CLEARED);
        this.host.onRunCleared();
      } else {
        EventBus.emit(Events.STAGE_CLEARED, { stageIndex: gameState.stageIndex });
        this.host.onStageCleared(room);
      }
    }
  }

  private startTrial(room: Room): void {
    this.states.set(room.id, 'active');
    this.waveIndex = 0;
    this.host.world.setRoomDoors(room, 'closed');
    EventBus.emit(Events.TRIAL_STARTED, { roomId: room.id });
    this.spawnWave(room, 0);
  }

  private spawnWave(room: Room, index: number): void {
    const mods = this.host.waveMods?.(room) ?? { hpMult: 1, countMult: 1, extra: 0 };
    const wave = scaleWave(this.waves[index], mods.countMult, mods.extra);
    const scale = { hp: this.host.stage.enemyScale.hp * mods.hpMult, attack: this.host.stage.enemyScale.attack };
    EventBus.emit(Events.TRIAL_WAVE, { roomId: room.id, wave: index + 1, total: this.waves.length });
    for (const entry of wave) {
      for (let i = 0; i < entry.count; i++) {
        const p = this.host.world.randomPointInRoom(
          room,
          this.host.rng,
          this.host.player,
          this.host.stage.trial.spawnMinDistTiles,
        );
        const e = new Enemy(this.host.mobs.scene, p.x, p.y, entry.enemy, scale);
        this.host.mobs.add(e);
        this.alive.add(e);
      }
    }
  }

  private clearTrial(room: Room): void {
    this.states.set(room.id, 'cleared');
    this.host.world.setRoomDoors(room, 'open');
    gameState.trialsCleared += 1;
    const payload: TrialClearedPayload = {
      roomId: room.id,
      cleared: gameState.trialsCleared,
      total: gameState.trialsTotal,
    };
    // 본영 해금을 먼저 반영해야 TRIAL_CLEARED 구독자(자막·음향)가 bossUnlocked 를 볼 수 있다
    // 48라운드 노드 전투장에는 보스 방이 없다 (보스 해금은 노드 지도가 정한다)
    const boss = this.host.world.layout.rooms.find((r) => r.type === 'boss');
    if (boss && gameState.trialsCleared >= gameState.trialsTotal && !gameState.bossUnlocked) {
      gameState.bossUnlocked = true;
      this.host.world.setRoomDoors(boss, 'open');
      EventBus.emit(Events.BOSS_UNLOCKED);
    }
    EventBus.emit(Events.TRIAL_CLEARED, payload);
  }

  private startBoss(room: Room): void {
    this.states.set(room.id, 'active');
    this.host.world.setRoomDoors(room, 'closed');
    const c = this.host.world.roomCenter(room);
    const boss = new Boss(this.host.mobs.scene, c.x, c.y, this.host.stage.boss);
    this.host.mobs.add(boss);
    this.alive.add(boss);
    EventBus.emit(Events.BOSS_STARTED, { roomId: room.id, boss: this.host.stage.boss });
  }
}
