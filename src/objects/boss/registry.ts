/**
 * 54라운드 Q4 보스 패턴 레지스트리: 이름 → 모듈. 새 패턴은 patterns/ 에 모듈을 만들고 여기 한 줄 + data/bossPatterns.ts 이름·형식.
 */
import type { BossPatternName } from '../../data/bossPatterns';
import { caskRollPattern } from './patterns/caskRoll';
import { dashPattern } from './patterns/dash';
import { drinkPattern, phaseDrinkPattern, spinPattern } from './patterns/drink';
import { drunkDashPattern } from './patterns/drunkDash';
import { fanPattern } from './patterns/fan';
import { fireSpillPattern } from './patterns/fireSpill';
import { lightsOutPattern } from './patterns/lightsOut';
import { slamPattern } from './patterns/slam';
import { summonPattern } from './patterns/summon';
import { volleyPattern } from './patterns/volley';
import type { BossPatternModule } from './types';

export const BOSS_PATTERNS: Record<BossPatternName, BossPatternModule> = {
  dash: dashPattern,
  fan: fanPattern,
  slam: slamPattern,
  summon: summonPattern,
  volley: volleyPattern,
  drink: drinkPattern,
  spin: spinPattern,
  drunkDash: drunkDashPattern,
  caskRoll: caskRollPattern,
  fireSpill: fireSpillPattern,
  lightsOut: lightsOutPattern,
  phaseDrink: phaseDrinkPattern,
};

export function patternModule(name: BossPatternName): BossPatternModule {
  return BOSS_PATTERNS[name];
}
