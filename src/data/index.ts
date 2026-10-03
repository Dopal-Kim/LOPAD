import playerJson from '../../data/player.json';
import enemiesJson from '../../data/enemies.json';
import bossesJson from '../../data/bosses.json';
import stagesJson from '../../data/stages.json';
import weaponsJson from '../../data/weapons.json';
import economyJson from '../../data/economy.json';
import personalityJson from '../../data/personality.json';
import storyJson from '../../data/story.json';
import paletteJson from '../../data/palette.json';
import lightingJson from '../../data/lighting.json';
import { checkPatternParams, isBossPatternName, resolvePatternParams, type BossPatternName } from './bossPatterns';
import type {
  BossTable,
  ComboDef,
  EconomyData,
  EnemyTable,
  LightDefData,
  LightingAmbient,
  LightingData,
  PaletteData,
  PersonalityData,
  PlayerData,
  RunDef,
  StageTable,
  StagesFile,
  SecondaryDef,
  StoryData,
  WeaponDef,
  WeaponEvolution,
  WeaponResourceDef,
  WeaponRules,
  WeaponTable,
  WeaponsFile,
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
  if (!p.sprint) throw new Error('[data] player.sprint 없음');
  for (const [k, val] of Object.entries(p.sprint)) assertNumber(val, `player.sprint.${k}`);
  if (p.sprint.speedMult < 1) throw new Error('[data] player.sprint.speedMult 는 1 이상');
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
    // 35라운드 2단계 보조 행동
    if (e.ranged?.reload) {
      for (const k of ['shots', 'reloadMs', 'retreatSpeedMult'] as const)
        assertNumber(e.ranged.reload[k], `enemies.${id}.ranged.reload.${k}`);
    }
    if (e.ranged?.telegraphMs !== undefined) assertNumber(e.ranged.telegraphMs, `enemies.${id}.ranged.telegraphMs`);
    if (e.shield) {
      assertNumber(e.shield.frontDeg, `enemies.${id}.shield.frontDeg`);
      assertNumber(e.shield.reduction, `enemies.${id}.shield.reduction`);
      if (e.shield.reduction < 0 || e.shield.reduction > 1)
        throw new Error(`[data] enemies.${id}.shield.reduction 는 0..1`);
    }
    if (e.pack) {
      for (const k of ['minCount', 'rangeTiles', 'speedMult', 'durationMs', 'cooldownMs'] as const)
        assertNumber(e.pack[k], `enemies.${id}.pack.${k}`);
    }
  }
  return t;
}

/**
 * 54라운드 Q4: 보스 검증 — 페이즈 pick 은 알려진 패턴 이름이어야 하고, 고르는 패턴은 그 페이즈에서 해석한 수치
 * (공통 → 페이즈 → 강화)가 형식(BOSS_PATTERN_SCHEMAS)에 맞아야 한다. 패턴이 부르는 다음 패턴(drink.triggers·spin.next 등)도 같은 검사
 */
export function validateBosses(t: BossTable): BossTable {
  for (const [id, b] of Object.entries(t)) {
    assertNumber(b.hp, `bosses.${id}.hp`);
    assertNumber(b.contactAttack, `bosses.${id}.contactAttack`);
    assertNumber(b.contactIntervalMs, `bosses.${id}.contactIntervalMs`);
    assertNumber(b.personalityValue, `bosses.${id}.personalityValue`);
    assertNumber(b.gold, `bosses.${id}.gold`);
    assertNumber(b.approachSpeedTiles, `bosses.${id}.approachSpeedTiles`);
    assertPair(b.size, `bosses.${id}.size`);
    if (b.bodyFromArt) {
      assertNumber(b.bodyFromArt.w, `bosses.${id}.bodyFromArt.w`);
      assertNumber(b.bodyFromArt.h, `bosses.${id}.bodyFromArt.h`);
    }
    if (!b.patterns || typeof b.patterns !== 'object') throw new Error(`[data] bosses.${id}.patterns 없음`);
    for (const name of Object.keys(b.patterns))
      if (!isBossPatternName(name)) throw new Error(`[data] bosses.${id}.patterns 알 수 없는 패턴: ${name}`);
    if (!Array.isArray(b.phases) || b.phases.length === 0) throw new Error(`[data] bosses.${id}.phases 비어 있음`);
    if (b.phases[0].hpFraction !== 1) throw new Error(`[data] bosses.${id}.phases[0].hpFraction 은 1 이어야 합니다`);
    b.phases.forEach((ph, i) => {
      const at = `bosses.${id}.phases[${i}]`;
      assertNumber(ph.hpFraction, `${at}.hpFraction`);
      assertNumber(ph.intervalMs, `${at}.intervalMs`);
      if (!Array.isArray(ph.pick) || ph.pick.length === 0) throw new Error(`[data] ${at}.pick 비어 있음`);
      for (const name of Object.keys(ph.patterns ?? {}))
        if (!isBossPatternName(name)) throw new Error(`[data] ${at}.patterns 알 수 없는 패턴: ${name}`);
      // 고르는 패턴 + 페이즈 진입 연출 + 그 패턴들이 부르는 다음 패턴 (한 단계씩 따라간다)
      const seen = new Set<BossPatternName>();
      const queue: unknown[] = [...ph.pick];
      if (ph.enterPattern !== undefined) queue.push(ph.enterPattern);
      while (queue.length > 0) {
        const name = queue.shift();
        if (!isBossPatternName(name)) throw new Error(`[data] ${at}: 알 수 없는 패턴 ${String(name)}`);
        if (seen.has(name)) continue;
        seen.add(name);
        for (const empowered of [false, true]) {
          const p = resolvePatternParams(b, i, name, empowered);
          if (!p) throw new Error(`[data] ${at}: ${name} 패턴인데 ${name} 수치 없음`);
          const errs = checkPatternParams(name, p, `${at}.${name}${empowered ? '(강화)' : ''}`);
          if (errs.length > 0) throw new Error(`[data] ${errs[0]}`);
          if (Array.isArray(p.triggers)) queue.push(...(p.triggers as unknown[]));
          if (p.next !== undefined) queue.push(p.next);
        }
      }
      // 기존 규칙: 부채꼴은 돌진 뒤 연계가 있으므로 fan 을 고르는 페이즈만 fan 수치를 본다 (위 검사로 충분)
    });
  }
  return t;
}

export function validateStages(t: StageTable, enemies: EnemyTable, bosses: BossTable): StageTable {
  for (const [, b] of Object.entries(bosses)) {
    const summon = b.patterns.summon as { enemy?: string } | undefined;
    if (summon?.enemy && !enemies[summon.enemy]) throw new Error(`[data] bosses: 소환 적 정의 없음 ${summon.enemy}`);
  }
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

const MOD_KEYS = new Set([
  'slashTrail',
  'trailDot',
  'dashCooldownMult',
  'dashAttackMult',
  'dashInvulnExtraMs',
  'dashAttackForceCrit',
  'shockwave',
  'shockwaveSecond',
  'shockwaveClearsProjectiles',
  'hitStunMs',
  'attackSlowMult',
  'guardReduction',
  'guardCounterMult',
  'superArmorReduction',
  'hits',
  'bleed',
  'moveSpeedMult',
  'dashTrailDamageMult',
  'shadowStepMult',
  'pierce',
  'pierceInfinite',
  'projectileSpeedMult',
  'aimedShotMult',
  'aimedShotStunMs',
  'spread',
  'homingTurnDeg',
  'fireRateMult',
  'magazineBonus',
  'reloadMult',
  'snipe',
]);

const SECONDARY_NUMERIC: Record<SecondaryDef['kind'], string[]> = {
  parry: [],
  guard: ['damageReduction', 'moveMult', 'pushRadiusTiles', 'pushSpeedTiles', 'pushMs'],
  shadowstep: ['rangeTiles', 'fallbackTiles', 'cooldownMs', 'primeMs'],
  aimedshot: ['chargeMs', 'damageMult', 'moveMult', 'cooldownMs'],
};

function validateEvolution(ev: WeaponEvolution, path: string, ids: Set<string>, depth: number, maxDepth: number): void {
  if (typeof ev.id !== 'string' || !ev.id) throw new Error(`[data] ${path}.id 없음`);
  if (ids.has(ev.id)) throw new Error(`[data] ${path}.id 중복: ${ev.id}`);
  ids.add(ev.id);
  if (typeof ev.name !== 'string' || !ev.name) throw new Error(`[data] ${path}.name 없음`);
  assertNumber(ev.damageMult, `${path}.damageMult`);
  assertNumber(ev.hitboxMult, `${path}.hitboxMult`);
  if (!ev.mods || typeof ev.mods !== 'object') throw new Error(`[data] ${path}.mods 없음`);
  for (const k of Object.keys(ev.mods)) if (!MOD_KEYS.has(k)) throw new Error(`[data] ${path}.mods.${k} 알 수 없음`);
  if (depth < maxDepth) {
    if (!Array.isArray(ev.next) || ev.next.length !== 2) throw new Error(`[data] ${path}.next 는 2개여야 합니다`);
    ev.next.forEach((n, i) => validateEvolution(n, `${path}.next[${i}]`, ids, depth + 1, maxDepth));
  } else if (ev.next && ev.next.length > 0) {
    throw new Error(`[data] ${path}.next: 트리 깊이 초과`);
  }
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
    // 55라운드 타격감 (선택)
    if (w.feel) {
      assertNumber(w.feel.hitstopMs, `weapons.${id}.feel.hitstopMs`);
      if (w.feel.ribbon !== undefined && typeof w.feel.ribbon !== 'string')
        throw new Error(`[data] weapons.${id}.feel.ribbon 은 문자열`);
    }
    if (w.combo) validateCombo(w.combo, `weapons.${id}.combo`);
    validateWeaponExtras(w, `weapons.${id}`);
    // 우클릭 보조 동작
    const sec = w.secondary as SecondaryDef | undefined;
    if (!sec || !(sec.kind in SECONDARY_NUMERIC)) throw new Error(`[data] weapons.${id}.secondary.kind 알 수 없음`);
    if (typeof sec.name !== 'string' || !sec.name) throw new Error(`[data] weapons.${id}.secondary.name 없음`);
    for (const k of SECONDARY_NUMERIC[sec.kind])
      assertNumber((sec as unknown as Record<string, unknown>)[k], `weapons.${id}.secondary.${k}`);
    // 분기 트리: thresholds 오름차순, 각 단계 선택지 2개
    const P = w.personality;
    if (!Array.isArray(P.thresholds) || P.thresholds.length === 0)
      throw new Error(`[data] weapons.${id}.personality.thresholds 비어 있음`);
    P.thresholds.forEach((th, i) => {
      assertNumber(th, `weapons.${id}.personality.thresholds[${i}]`);
      if (i > 0 && th <= P.thresholds[i - 1])
        throw new Error(`[data] weapons.${id}.personality.thresholds 는 오름차순이어야 합니다`);
    });
    if (!Array.isArray(P.branches) || P.branches.length !== 2)
      throw new Error(`[data] weapons.${id}.personality.branches 는 2개여야 합니다`);
    const ids = new Set<string>();
    P.branches.forEach((b, i) =>
      validateEvolution(b, `weapons.${id}.personality.branches[${i}]`, ids, 1, P.thresholds.length),
    );
  }
  return t;
}

/** 48라운드 3연격: 모양·버퍼·타별 수치 (마지막 타의 cancelFromMs 는 durationMs 이상) */
export function validateCombo(c: ComboDef, path: string): ComboDef {
  if (c.shape !== 'arc' && c.shape !== 'thrust') throw new Error(`[data] ${path}.shape 는 arc|thrust`);
  if (c.shape === 'arc') assertNumber(c.arcDeg, `${path}.arcDeg`);
  if (c.radiusPx !== undefined) assertNumber(c.radiusPx, `${path}.radiusPx`);
  if (c.shape === 'thrust') {
    assertNumber(c.thrust?.lengthPx, `${path}.thrust.lengthPx`);
    assertNumber(c.thrust?.widthPx, `${path}.thrust.widthPx`);
  }
  for (const k of ['bufferMs', 'resetMs', 'finisherRecoverMs'] as const) assertNumber(c[k], `${path}.${k}`);
  if (!Array.isArray(c.hits) || c.hits.length === 0) throw new Error(`[data] ${path}.hits 비어 있음`);
  c.hits.forEach((h, i) => {
    for (const k of ['damageMult', 'sizeMult', 'durationMs', 'cancelFromMs', 'activeMs'] as const)
      assertNumber(h[k], `${path}.hits[${i}].${k}`);
    if (h.cancelFromMs > h.durationMs) throw new Error(`[data] ${path}.hits[${i}].cancelFromMs 는 durationMs 이하`);
    if (h.hitAtMs !== undefined && !(h.hitAtMs > 0 && h.hitAtMs < h.durationMs))
      throw new Error(`[data] ${path}.hits[${i}].hitAtMs 는 0 과 durationMs 사이`);
  });
  return c;
}

const RESOURCE_NUMERIC: Record<WeaponResourceDef['kind'], string[]> = {
  stamina: ['max', 'regenPerSec', 'regenDelayMs', 'lowRatio', 'recoverRatio', 'exhaustedMoveMult'],
  ammo: ['max', 'reloadMs', 'lowCount'],
  heat: ['max', 'decayPerSec', 'decayDelayMs', 'overheatHoldMs', 'cooldownMs'],
};

/** 49라운드: 무기 자원 · 휴대 · 대검 무게감·내리찍기·대쉬 공격 (모두 선택 필드) */
export function validateWeaponExtras(w: WeaponDef, path: string): void {
  const r = w.resource;
  if (r) {
    if (!(r.kind in RESOURCE_NUMERIC)) throw new Error(`[data] ${path}.resource.kind 알 수 없음`);
    if (typeof r.label !== 'string' || !r.label) throw new Error(`[data] ${path}.resource.label 없음`);
    for (const k of RESOURCE_NUMERIC[r.kind])
      assertNumber((r as unknown as Record<string, unknown>)[k], `${path}.resource.${k}`);
    if (!(r.max > 0)) throw new Error(`[data] ${path}.resource.max 는 0 보다 커야 합니다`);
    const nums = (v: unknown, p: string) => {
      if (!Array.isArray(v) || v.length === 0) throw new Error(`[data] ${p} 는 숫자 배열이어야 합니다`);
      v.forEach((x, i) => assertNumber(x, `${p}[${i}]`));
    };
    if (r.kind === 'stamina') {
      nums(r.cost?.hits, `${path}.resource.cost.hits`);
      for (const k of ['dash', 'dashAttack', 'slam'] as const) assertNumber(r.cost[k], `${path}.resource.cost.${k}`);
    }
    if (r.kind === 'heat') {
      nums(r.gainPerHit, `${path}.resource.gainPerHit`);
      nums(r.stages, `${path}.resource.stages`);
      nums(r.speedMults, `${path}.resource.speedMults`);
      if (r.speedMults.length !== r.stages.length + 1)
        throw new Error(`[data] ${path}.resource.speedMults 길이는 stages + 1`);
    }
  }
  const c = w.carry;
  if (c) {
    if (!['sheath', 'back', 'hand'].includes(c.mode)) throw new Error(`[data] ${path}.carry.mode 알 수 없음`);
    assertNumber(c.drawMs, `${path}.carry.drawMs`);
    assertNumber(c.sheatheAfterMs, `${path}.carry.sheatheAfterMs`);
    if (c.sheathedRegenMult !== undefined) assertNumber(c.sheathedRegenMult, `${path}.carry.sheathedRegenMult`);
    if (c.firstStrike && (typeof c.firstStrike.label !== 'string' || !c.firstStrike.label))
      throw new Error(`[data] ${path}.carry.firstStrike.label 없음`);
  }
  const blocks: [string, object | undefined, string[]][] = [
    ['weight', w.weight, ['stepPx', 'stepMs', 'postSlowMs', 'finisherStopMs']],
    ['slam', w.slam, ['leapMs', 'recoverMs', 'leapMinPx', 'leapMaxPx', 'radiusPx', 'damageMult']],
    ['dashSlash', w.dashSlash, ['stepPx', 'stepMs', 'swingMs', 'recoverMs', 'arcDeg', 'fxCombo', 'fxSpawnAtMs']],
  ];
  for (const [name, b, keys] of blocks)
    if (b) for (const k of keys) assertNumber((b as Record<string, unknown>)[k], `${path}.${name}.${k}`);
}

export function validateWeaponRules(r: WeaponRules): WeaponRules {
  assertNumber(r.reinforceBonus, 'weapons.rules.reinforceBonus');
  assertNumber(r.reinforceMax, 'weapons.rules.reinforceMax');
  return r;
}

const weaponsFile = weaponsJson as unknown as WeaponsFile;
export const WEAPON_RULES: WeaponRules = validateWeaponRules(weaponsFile.rules);
export const WEAPONS: WeaponTable = validateWeapons(weaponsFile.weapons);
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
  if (!Array.isArray(s.reinforce) || s.reinforce.length < 3) throw new Error('[data] story.reinforce 3줄 필요');
  for (const k of ['title', 'evolveMenu', 'result', 'pause', 'hud'] as const) {
    if (!s.ui?.[k]) throw new Error(`[data] story.ui.${k} 없음`);
  }
  return s;
}

export const STORY: StoryData = validateStory(storyJson as unknown as StoryData, RUN);

/** 팔레트: 무채색 16 + 층별 강조 램프 12 (계약 art-assets.md §2) */
export function validatePalette(p: PaletteData): PaletteData {
  if (!Array.isArray(p.gray) || p.gray.length === 0) throw new Error('[data] palette.gray 없음');
  const n = p.accent_slots?.count;
  assertNumber(n, 'palette.accent_slots.count');
  if (!Array.isArray(p.floors) || p.floors.length === 0) throw new Error('[data] palette.floors 없음');
  for (const f of p.floors) {
    assertNumber(f.floor, 'palette.floors[].floor');
    if (!Array.isArray(f.ramp) || f.ramp.length !== n)
      throw new Error(`[data] palette.floors[${f.floor}].ramp 는 ${n}칸이어야 합니다`);
    for (const c of f.ramp) if (!/^#[0-9a-fA-F]{6}$/.test(c)) throw new Error(`[data] palette 색 형식 오류: ${c}`);
  }
  if (p.fx) {
    if (!Array.isArray(p.fx.core) || p.fx.core.length === 0) throw new Error('[data] palette.fx.core 없음');
    for (const [id, w] of Object.entries(p.fx.weapons ?? {})) {
      if (!Array.isArray(w.ramp) || w.ramp.length === 0) throw new Error(`[data] palette.fx.weapons.${id}.ramp 없음`);
      for (const c of w.ramp) if (!/^#[0-9a-fA-F]{6}$/.test(c)) throw new Error(`[data] palette fx 색 형식 오류: ${c}`);
    }
  }
  return p;
}

export const PALETTE: PaletteData = validatePalette(paletteJson as unknown as PaletteData);

const HEX = /^#[0-9a-fA-F]{6}$/;

function validateLight(l: LightDefData, path: string): void {
  assertNumber(l.radius, `${path}.radius`);
  if (!(l.radius > 0)) throw new Error(`[data] ${path}.radius 는 0 보다 커야 합니다`);
  if (l.color !== undefined && !HEX.test(l.color)) throw new Error(`[data] ${path}.color 형식 오류: ${l.color}`);
  for (const k of ['intensity', 'flicker', 'offsetY'] as const)
    if (l[k] !== undefined) assertNumber(l[k], `${path}.${k}`);
}

/** 50라운드 조명 데이터 */
export function validateLighting(d: LightingData): LightingData {
  const amb = (a: LightingAmbient, path: string) => {
    if (!a || !HEX.test(a.ambient)) throw new Error(`[data] ${path}.ambient 형식 오류`);
  };
  for (const [id, a] of Object.entries(d.regions)) amb(a, `lighting.regions.${id}`);
  amb(d.default, 'lighting.default');
  validateLight(d.player, 'lighting.player');
  if (d.mob) validateLight(d.mob, 'lighting.mob');
  validateLight(d.weaponFx, 'lighting.weaponFx');
  validateLight(d.telegraph, 'lighting.telegraph');
  for (const [id, l] of Object.entries(d.fallback))
    if (!id.startsWith('_')) validateLight(l, `lighting.fallback.${id}`);
  for (const k of ['maxLights', 'lightmapScale'] as const) assertNumber(d[k], `lighting.${k}`);
  if (!(d.lightmapScale > 0 && d.lightmapScale <= 1)) throw new Error('[data] lighting.lightmapScale 는 0~1');
  if (!Array.isArray(d.flickerHz) || d.flickerHz.length !== 2)
    throw new Error('[data] lighting.flickerHz 는 [최소, 최대]');
  return d;
}

export const LIGHTING: LightingData = validateLighting(lightingJson as unknown as LightingData);
