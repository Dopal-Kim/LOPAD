import { PLAYER_DATA } from '../data';

/** 런 상태의 단일 출처. 런 재시작은 reset()으로. */
class GameState {
  hp = PLAYER_DATA.stats.hp;
  maxHp = PLAYER_DATA.stats.hp;
  enemiesKilled = 0;
  enemiesRemaining = 0;
  gameOver = false;
  cleared = false;

  reset(): void {
    this.hp = PLAYER_DATA.stats.hp;
    this.maxHp = PLAYER_DATA.stats.hp;
    this.enemiesKilled = 0;
    this.enemiesRemaining = 0;
    this.gameOver = false;
    this.cleared = false;
  }
}

export const gameState = new GameState();
