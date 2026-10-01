import { PLAYER_DATA, WEAPONS } from '../data';
import { WeaponState } from '../systems/weapons';
import { SenseTracker } from '../systems/senses';

/** 런 상태의 단일 출처. 런 재시작은 reset()으로. */
class GameState {
  seed = '';
  hp = PLAYER_DATA.stats.hp;
  maxHp = PLAYER_DATA.stats.hp;
  kills = 0;
  readonly senses = new SenseTracker();
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

  reset(seed: string): void {
    this.seed = seed;
    this.hp = PLAYER_DATA.stats.hp;
    this.maxHp = PLAYER_DATA.stats.hp;
    this.kills = 0;
    this.senses.reset();
    this.weapon = new WeaponState(PLAYER_DATA.startWeapon, WEAPONS[PLAYER_DATA.startWeapon]); // 사망 시 무기 초기화 (기획 3장)
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
  }
}

export const gameState = new GameState();
