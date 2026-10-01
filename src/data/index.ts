import playerJson from '../../data/player.json';
import enemiesJson from '../../data/enemies.json';
import bossesJson from '../../data/bosses.json';
import stagesJson from '../../data/stages.json';
import type { BossTable, EnemyTable, PlayerData, StageTable } from './types';

function assertNumber(v: unknown, path: string): void {
  if (typeof v !== 'number' || Number.isNaN(v)) {
    throw new Error(`[data] ${path} 는 숫자여야 합니다 (받은 값: ${String(v)})`);
  }
}

function assertPair(v: unknown, path: string): void {
  if (!Array.isArray(v) || v.length !== 2) throw new Error(`[data] ${path} 는 [a, b] 여야 합니다`);
  assertNumber(v[0], `${path}[0]`);
  assertNumber(v[1], `${path}[1]`);
}

export function validatePlayer(p: PlayerData): PlayerData {
  for (const [k, v] of Object.entries(p.stats)) assertNumber(v, `player.stats.${k}`);
  for (const [k, v] of Object.entries(p.attackHitbox)) assertNumber(v, `player.attackHitbox.${k}`);
  assertNumber(p.invulnerableMs, 'player.invulnerableMs');
  assertPair(p.size, 'player.size');
  return p;
}

export function validateEnemies(t: EnemyTable): EnemyTable {
  for (const [id, e] of Object.entries(t)) {
    for (const k of ['hp', 'attack', 'speedTiles', 'attackIntervalMs'] as const) {
      assertNumber(e[k], `enemies.${id}.${k}`);
    }
    assertPair(e.size, `enemies.${id}.size`);
    if (e.behavior === 'ranged' && !e.ranged) throw new Error(`[data] enemies.${id}: ranged 파라미터 없음`);
    if (e.behavior === 'charge' && !e.charge) throw new Error(`[data] enemies.${id}: charge 파라미터 없음`);
    if (!['chase', 'ranged', 'charge'].includes(e.behavior)) {
      throw new Error(`[data] enemies.${id}.behavior 알 수 없음: ${e.behavior}`);
    }
  }
  return t;
}

export function validateBosses(t: BossTable): BossTable {
  for (const [id, b] of Object.entries(t)) {
    assertNumber(b.hp, `bosses.${id}.hp`);
    assertNumber(b.contactAttack, `bosses.${id}.contactAttack`);
    assertNumber(b.contactIntervalMs, `bosses.${id}.contactIntervalMs`);
    assertNumber(b.approachSpeedTiles, `bosses.${id}.approachSpeedTiles`);
    assertPair(b.size, `bosses.${id}.size`);
    if (!Array.isArray(b.phases) || b.phases.length === 0) throw new Error(`[data] bosses.${id}.phases 비어 있음`);
    if (b.phases[0].hpFraction !== 1) throw new Error(`[data] bosses.${id}.phases[0].hpFraction 은 1 이어야 합니다`);
    b.phases.forEach((ph, i) => {
      assertNumber(ph.hpFraction, `bosses.${id}.phases[${i}].hpFraction`);
      for (const [k, v] of Object.entries(ph.dash)) assertNumber(v, `bosses.${id}.phases[${i}].dash.${k}`);
      if (ph.fan) {
        for (const [k, v] of Object.entries(ph.fan)) {
          if (k !== 'afterDash') assertNumber(v, `bosses.${id}.phases[${i}].fan.${k}`);
        }
      }
    });
  }
  return t;
}

export function validateStages(t: StageTable, enemies: EnemyTable, bosses: BossTable): StageTable {
  for (const [id, s] of Object.entries(t)) {
    if (!bosses[s.boss]) throw new Error(`[data] stages.${id}.boss 정의 없음: ${s.boss}`);
    const L = s.layout;
    for (const k of [
      'gridW',
      'gridH',
      'trialCount',
      'restCount',
      'corridorWidth',
      'trialMinDistFromStart',
      'extraLoopChance',
    ] as const) {
      assertNumber(L[k], `stages.${id}.layout.${k}`);
    }
    for (const k of ['roomW', 'roomH', 'bossRoomW', 'bossRoomH'] as const) assertPair(L[k], `stages.${id}.layout.${k}`);
    if (L.corridorWidth % 2 === 0) throw new Error(`[data] stages.${id}.layout.corridorWidth 는 홀수여야 합니다`);
    if (s.trial.waves.length === 0) throw new Error(`[data] stages.${id}.trial.waves 비어 있음`);
    for (const wave of s.trial.waves) {
      for (const w of wave) {
        if (!enemies[w.enemy]) throw new Error(`[data] stages.${id}: 적 정의 없음 ${w.enemy}`);
        assertNumber(w.count, `stages.${id}.trial.waves.count`);
      }
    }
    assertNumber(s.trial.spawnMinDistTiles, `stages.${id}.trial.spawnMinDistTiles`);
    assertNumber(s.rest.healFraction, `stages.${id}.rest.healFraction`);
  }
  return t;
}

export const PLAYER_DATA: PlayerData = validatePlayer(playerJson as unknown as PlayerData);
export const ENEMIES: EnemyTable = validateEnemies(enemiesJson as unknown as EnemyTable);
export const BOSSES: BossTable = validateBosses(bossesJson as unknown as BossTable);
export const STAGES: StageTable = validateStages(stagesJson as unknown as StageTable, ENEMIES, BOSSES);
