import { PLAYER_DATA, RUN, STAGES, WEAPONS } from '../data';
import type { StageDef } from '../data/types';
import type { SaveData } from '../systems/save';
import { SAVE_VERSION } from '../systems/save';
import { SenseTracker } from '../systems/senses';
import { WeaponState } from '../systems/weapons';
import { EMPTY_BONUS, type StatBonus } from '../systems/economy';

/** 런 상태의 단일 출처. 런 시작은 startRun(), 층 전환은 nextStage(). */
class GameState {
  seed = '';
  stageIndex = 0;
  savesLeft = RUN.maxSaves;
  hp = PLAYER_DATA.stats.hp;
  maxHp = PLAYER_DATA.stats.hp;
  kills = 0;
  readonly senses = new SenseTracker();
  gold = 0;
  potions = 0;
  /** 아직 쓰지 않은 능력치 포인트 */
  pointsPending = 0;
  bonus: StatBonus = { ...EMPTY_BONUS };
  /** 보상 선택 중 (출구는 끝난 뒤 열림) */
  rewardPending = false;
  weapon = new WeaponState(PLAYER_DATA.startWeapon, WEAPONS[PLAYER_DATA.startWeapon]);
  trialsCleared = 0;
  trialsTotal = 0;
  roomId = '';
  roomType = '';
  bossHp = 0;
  bossMaxHp = 0;
  bossPhase = 0;
  bossUnlocked = false;
  gameOver = false;
  cleared = false;
  /** 보스 처치 후 출구가 열린 상태 */
  exitOpen = false;

  get stageId(): string {
    return RUN.order[this.stageIndex];
  }

  get stage(): StageDef {
    return STAGES[this.stageId];
  }

  get isLastStage(): boolean {
    return this.stageIndex >= RUN.order.length - 1;
  }

  /** 이 층의 맵 시드 (런 시드 + 층 번호) */
  get floorSeed(): string {
    return `${this.seed}:${this.stageIndex}`;
  }

  /** 새 런 */
  startRun(seed: string): void {
    this.seed = seed;
    this.stageIndex = 0;
    this.savesLeft = RUN.maxSaves;
    this.hp = PLAYER_DATA.stats.hp;
    this.maxHp = PLAYER_DATA.stats.hp;
    this.kills = 0;
    this.senses.reset();
    this.gold = 0;
    this.potions = 0;
    this.pointsPending = 0;
    this.bonus = { ...EMPTY_BONUS };
    this.weapon = new WeaponState(PLAYER_DATA.startWeapon, WEAPONS[PLAYER_DATA.startWeapon]); // 사망 시 무기 초기화 (기획 3장)
    this.resetStage();
  }

  /** 다음 층으로 (HP·무기·감각·처치 수 유지) */
  nextStage(): void {
    this.stageIndex += 1;
    this.senses.nextStage();
    this.resetStage();
  }

  private resetStage(): void {
    this.trialsCleared = 0;
    this.trialsTotal = 0;
    this.roomId = '';
    this.roomType = '';
    this.bossHp = 0;
    this.bossMaxHp = 0;
    this.bossPhase = 0;
    this.bossUnlocked = false;
    this.gameOver = false;
    this.cleared = false;
    this.exitOpen = false;
    this.rewardPending = false;
  }

  /** 기본 스탯 + 런 보너스 */
  get attack(): number {
    return PLAYER_DATA.stats.attack + this.bonus.attack;
  }

  get defense(): number {
    return PLAYER_DATA.stats.defense + this.bonus.defense;
  }

  get crit(): number {
    return PLAYER_DATA.stats.crit + this.bonus.crit;
  }

  toSave(): SaveData {
    return {
      version: SAVE_VERSION,
      seed: this.seed,
      stageIndex: this.stageIndex,
      hp: this.hp,
      maxHp: this.maxHp,
      kills: this.kills,
      sense: this.senses.sense,
      savesLeft: this.savesLeft,
      weapon: { id: this.weapon.id, personality: this.weapon.personality, stage: this.weapon.stage },
      gold: this.gold,
      potions: this.potions,
      pointsPending: this.pointsPending,
      bonus: { ...this.bonus },
      savedAt: Date.now(),
    };
  }

  applySave(d: SaveData): void {
    this.startRun(d.seed);
    this.stageIndex = Math.min(d.stageIndex, RUN.order.length - 1);
    this.hp = d.hp;
    this.maxHp = d.maxHp;
    this.kills = d.kills;
    this.senses.sense = d.sense;
    this.savesLeft = d.savesLeft;
    const weaponId = WEAPONS[d.weapon.id] ? d.weapon.id : PLAYER_DATA.startWeapon;
    this.weapon = new WeaponState(weaponId, WEAPONS[weaponId]);
    this.weapon.restore(d.weapon.personality, d.weapon.stage);
    this.gold = d.gold;
    this.potions = d.potions;
    this.pointsPending = d.pointsPending;
    this.bonus = { ...EMPTY_BONUS, ...d.bonus };
  }
}

export const gameState = new GameState();
