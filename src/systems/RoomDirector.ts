import Phaser from 'phaser';
import { EventBus, Events, type RoomEnteredPayload, type TrialClearedPayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import type { StageDef } from '../data/types';
import { Boss } from '../objects/Boss';
import { Enemy } from '../objects/Enemy';
import type { Mob } from '../objects/Mob';
import type { TileWorld } from '../world/TileWorld';
import type { Room } from './mapgen';
import { Rng } from './rng';

type RoomState = 'idle' | 'active' | 'cleared';

export interface RoomDirectorHost {
  world: TileWorld;
  stage: StageDef;
  rng: Rng;
  player: { x: number; y: number };
  mobs: Phaser.Physics.Arcade.Group;
  heal(fraction: number): void;
  onRunCleared(): void;
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

  constructor(private host: RoomDirectorHost) {
    for (const r of host.world.layout.rooms) this.states.set(r.id, 'idle');
    this.states.set('start', 'cleared');
    gameState.trialsTotal = host.stage.layout.trialCount;
  }

  /** 디버그용: 현재 활성 방의 남은 적 수와 웨이브 번호 */
  get debugInfo(): { alive: number; wave: number; active: string | undefined } {
    return { alive: this.alive.size, wave: this.waveIndex, active: this.activeRoom?.id };
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

  /** 적 사망 시 호출 */
  onMobDied(mob: Mob): void {
    this.alive.delete(mob);
    const room = this.activeRoom;
    if (!room || this.alive.size > 0) return;
    if (room.type === 'trial') {
      this.waveIndex += 1;
      if (this.waveIndex < this.host.stage.trial.waves.length) {
        this.spawnWave(room, this.waveIndex);
      } else {
        this.clearTrial(room);
      }
    } else if (room.type === 'boss') {
      this.states.set(room.id, 'cleared');
      gameState.cleared = true;
      this.host.world.setRoomDoors(room, 'open');
      EventBus.emit(Events.RUN_CLEARED);
      this.host.onRunCleared();
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
    const wave = this.host.stage.trial.waves[index];
    EventBus.emit(Events.TRIAL_WAVE, { roomId: room.id, wave: index + 1, total: this.host.stage.trial.waves.length });
    for (const entry of wave) {
      for (let i = 0; i < entry.count; i++) {
        const p = this.host.world.randomPointInRoom(
          room,
          this.host.rng,
          this.host.player,
          this.host.stage.trial.spawnMinDistTiles,
        );
        const e = new Enemy(this.host.mobs.scene, p.x, p.y, entry.enemy);
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
    EventBus.emit(Events.TRIAL_CLEARED, payload);
    if (gameState.trialsCleared >= gameState.trialsTotal && !gameState.bossUnlocked) {
      gameState.bossUnlocked = true;
      const boss = this.host.world.layout.rooms.find((r) => r.type === 'boss')!;
      this.host.world.setRoomDoors(boss, 'open');
      EventBus.emit(Events.BOSS_UNLOCKED);
    }
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
