import playerJson from '../../data/player.json';
import enemiesJson from '../../data/enemies.json';
import type { EnemyTable, PlayerData } from './types';

function assertNumber(v: unknown, path: string): void {
  if (typeof v !== 'number' || Number.isNaN(v)) {
    throw new Error(`[data] ${path} 는 숫자여야 합니다 (받은 값: ${String(v)})`);
  }
}

function validatePlayer(p: PlayerData): PlayerData {
  for (const [k, v] of Object.entries(p.stats)) assertNumber(v, `player.stats.${k}`);
  for (const [k, v] of Object.entries(p.attackHitbox)) assertNumber(v, `player.attackHitbox.${k}`);
  assertNumber(p.invulnerableMs, 'player.invulnerableMs');
  if (!Array.isArray(p.size) || p.size.length !== 2) throw new Error('[data] player.size 는 [w, h] 여야 합니다');
  return p;
}

function validateEnemies(t: EnemyTable): EnemyTable {
  for (const [id, e] of Object.entries(t)) {
    for (const k of ['hp', 'attack', 'speedTiles', 'attackIntervalMs'] as const) {
      assertNumber(e[k], `enemies.${id}.${k}`);
    }
    if (e.behavior !== 'chase') throw new Error(`[data] enemies.${id}.behavior 알 수 없음: ${e.behavior}`);
    if (!Array.isArray(e.size) || e.size.length !== 2) throw new Error(`[data] enemies.${id}.size 는 [w, h] 여야 합니다`);
  }
  return t;
}

export const PLAYER_DATA: PlayerData = validatePlayer(playerJson as unknown as PlayerData);
export const ENEMIES: EnemyTable = validateEnemies(enemiesJson as unknown as EnemyTable);
