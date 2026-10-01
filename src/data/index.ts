import playerJson from '../../data/player.json';
import enemiesJson from '../../data/enemies.json';
import bossesJson from '../../data/bosses.json';
import stagesJson from '../../data/stages.json';
import weaponsJson from '../../data/weapons.json';
import economyJson from '../../data/economy.json';
import personalityJson from '../../data/personality.json';
import storyJson from '../../data/story.json';
import type {
  BossTable,
  EconomyData,
  EnemyTable,
  PersonalityData,
  PlayerData,
  RunDef,
  StageTable,
  StagesFile,
  StoryData,
  WeaponTable,
} from './types';

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
  assertNumber(p.invulnerableMs, 'player.invulnerableMs');
  assertPair(p.size, 'player.size');
  for (const [k, val] of Object.entries(p.dash)) if (k !== 'invulnerable') assertNumber(val, `player.dash.${k}`);
  for (const [k, val] of Object.entries(p.parry)) assertNumber(val, `player.parry.${k}`);
  if (typeof p.startWeapon !== 'string') throw new Error('[data] player.startWeapon 없음');
  assertNumber(p.attackSlowMinMs, 'player.attackSlowMinMs');
  return p;
}

export function validateEnemies(t: EnemyTable): EnemyTable {
  for (const [id, e] of Object.entries(t)) {
    for (const k of ['hp', 'attack', 'speedTiles', 'attackIntervalMs'] as const) {
      assertNumber(e[k], `enemies.${id}.${k}`);
    }
    assertPair(e.size, `enemies.${id}.size`);
    assertNumber(e.personalityValue, `enemies.${id}.personalityValue`);
    assertNumber(e.gold, `enemies.${id}.gold`);
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
    assertNumber(b.personalityValue, `bosses.${id}.personalityValue`);
    assertNumber(b.gold, `bosses.${id}.gold`);
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
    assertNumber(s.enemyScale?.hp, `stages.${id}.enemyScale.hp`);
    assertNumber(s.enemyScale?.attack, `stages.${id}.enemyScale.attack`);
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

export function validateWeapons(t: WeaponTable): WeaponTable {
  for (const [id, w] of Object.entries(t)) {
    assertNumber(w.damageMult, `weapons.${id}.damageMult`);
    assertNumber(w.critBonus, `weapons.${id}.critBonus`);
    assertNumber(w.attackSlowMult, `weapons.${id}.attackSlowMult`);
    if (w.kind !== 'melee' && w.kind !== 'ranged') throw new Error(`[data] weapons.${id}.kind 알 수 없음`);
    if (w.kind === 'ranged' && !w.ranged) throw new Error(`[data] weapons.${id}: ranged 파라미터 없음`);
    for (const [k, val] of Object.entries(w.affinity)) {
      assertNumber(val, `weapons.${id}.affinity.${k}`);
      if (val < 0 || val > 1) throw new Error(`[data] weapons.${id}.affinity.${k} 는 0..1`);
    }
    for (const [k, val] of Object.entries(w.hitbox)) assertNumber(val, `weapons.${id}.hitbox.${k}`);
    assertNumber(w.personality.threshold, `weapons.${id}.personality.threshold`);
    w.personality.evolutions.forEach((ev, i) => {
      assertNumber(ev.damageMult, `weapons.${id}.evolutions[${i}].damageMult`);
      assertNumber(ev.hitboxMult, `weapons.${id}.evolutions[${i}].hitboxMult`);
      if (ev.effect !== null && !['slash-trail', 'shockwave', 'twin', 'pierce'].includes(ev.effect))
        throw new Error(`[data] weapons.${id}.evolutions[${i}].effect 알 수 없음`);
    });
  }
  return t;
}

export const WEAPONS: WeaponTable = validateWeapons(weaponsJson as unknown as WeaponTable);
export const PLAYER_DATA: PlayerData = validatePlayer(playerJson as unknown as PlayerData);
if (!WEAPONS[PLAYER_DATA.startWeapon])
  throw new Error(`[data] player.startWeapon 정의 없음: ${PLAYER_DATA.startWeapon}`);
export const ENEMIES: EnemyTable = validateEnemies(enemiesJson as unknown as EnemyTable);
export const BOSSES: BossTable = validateBosses(bossesJson as unknown as BossTable);
const stagesFile = stagesJson as unknown as StagesFile;
export const STAGES: StageTable = validateStages(stagesFile.stages, ENEMIES, BOSSES);
export const RUN: RunDef = validateRun(stagesFile.run, STAGES);

export function validateRun(run: RunDef, stages: StageTable): RunDef {
  if (!Array.isArray(run.order) || run.order.length === 0) throw new Error('[data] run.order 비어 있음');
  for (const id of run.order) if (!stages[id]) throw new Error(`[data] run.order 에 없는 스테이지: ${id}`);
  assertNumber(run.maxSaves, 'run.maxSaves');
  return run;
}

export function validateEconomy(e: EconomyData): EconomyData {
  for (const [k, val] of Object.entries(e.gold)) assertNumber(val, `economy.gold.${k}`);
  for (const k of ['chance', 'heal', 'maxCarry'] as const) assertNumber(e.drops.potion[k], `economy.drops.potion.${k}`);
  if (!(e.drops.potion.rarity in e.rarity)) throw new Error('[data] economy.drops.potion.rarity 가 rarity 표에 없음');
  const raritySum = Object.values(e.rarity).reduce((a, b) => a + b, 0);
  if (raritySum !== 100) throw new Error(`[data] economy.rarity 합이 100 이어야 합니다 (현재 ${raritySum})`);
  if (e.shop.items.length === 0) throw new Error('[data] economy.shop.items 비어 있음');
  for (const it of e.shop.items) {
    assertNumber(it.price, `economy.shop.${it.id}.price`);
    assertNumber(it.pricePerStage, `economy.shop.${it.id}.pricePerStage`);
  }
  assertNumber(e.shop.healFraction, 'economy.shop.healFraction');
  if (e.statRewards.length === 0) throw new Error('[data] economy.statRewards 비어 있음');
  assertNumber(e.critDamageMult, 'economy.critDamageMult');
  return e;
}

export const ECONOMY: EconomyData = validateEconomy(economyJson as unknown as EconomyData);

export const PERSONALITY: PersonalityData = personalityJson as unknown as PersonalityData;

export function validateStory(s: StoryData, run: RunDef): StoryData {
  for (const id of run.order) {
    const f = s.floors[id];
    if (!f) throw new Error(`[data] story.floors.${id} 없음`);
    for (const k of ['title', 'empire', 'bossName', 'enter', 'bossIntro', 'restNote'] as const) {
      if (typeof f[k] !== 'string' || !f[k]) throw new Error(`[data] story.floors.${id}.${k} 비어 있음`);
    }
  }
  for (const k of ['trialStart', 'trialClear', 'bossUnlocked', 'saved'] as const) {
    if (!s.notices[k]) throw new Error(`[data] story.notices.${k} 없음`);
  }
  if (!s.death.includes('{name}')) throw new Error('[data] story.death 에 {name} 치환자가 없음');
  return s;
}

export const STORY: StoryData = validateStory(storyJson as unknown as StoryData, RUN);
