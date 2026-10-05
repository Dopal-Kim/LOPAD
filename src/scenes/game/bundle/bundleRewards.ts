/**
 * 60라운드 2차 묶음 보상 지급 (data/bundle2.json rewards · events effects): 노드 보상 종류 → 지급, 이벤트 효과 목록 → 차례대로 지급.
 * 메뉴가 필요한 것(패시브·능력치·소모품 바꾸기)은 닫힌 뒤 다음 단계로 이어진다 (`chain`).
 */
import { EventBus, Events } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUNDLE2, CONSUMABLE_IDS, consumableIdsOn } from '../../../data/bundle2';
import type { EventEffect, RewardKind } from '../../../data/bundle2Types';
import { rewardGold } from '../../../systems/bundle2/BundleState';
import type { Game } from '../../Game';

export type Step = (next: () => void) => void;

/** 단계들을 차례대로 (각 단계는 끝나면 next) */
export function chain(steps: readonly Step[], onDone: () => void = () => {}): void {
  let i = 0;
  const run = (): void => {
    const s = steps[i++];
    if (!s) return onDone();
    s(run);
  };
  run();
}

/** 무작위 층 소모품 id (61라운드 P5: 이 층에서 나오는 것 — 1층 = 화염 술병) */
export function randomConsumable(g: Game) {
  const ids = consumableIdsOn(gameState.build.floor);
  const list = ids.length > 0 ? ids : CONSUMABLE_IDS;
  return list[Math.floor(g.rng.next() * list.length)];
}

/** 소모품 하나 (칸이 가득이면 대신 전표 fallbackGold) */
function consumableStep(g: Game): Step {
  return (next) => {
    const bundle = g.bundle;
    if (!bundle) return next();
    const id = randomConsumable(g);
    const r = gameState.bundle.consumable.tryGain(id);
    if (r === 'added') return next();
    if (r === 'full') {
      g.economy.addGold(BUNDLE2.rewards.consumable.fallbackGold);
      return next();
    }
    bundle.consumables.gain(id, next);
  };
}

/** 최대 HP 증감 (줄면 현재 HP 도 그 안으로, 늘면 늘린 만큼 회복) */
export function changeMaxHp(g: Game, delta: number): void {
  gameState.maxHp = Math.max(1, gameState.maxHp + delta);
  if (delta > 0) g.player.heal(delta, 'event');
  gameState.hp = Math.min(gameState.hp, gameState.maxHp);
}

/** 독주 증감 (0 ~ 최대 소지) */
export function changePotions(g: Game, delta: number | 'fill'): void {
  const carry = g.economy.potionCarry;
  gameState.potions = delta === 'fill' ? carry : Math.max(0, Math.min(carry, gameState.potions + delta));
  EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
}

/**
 * 노드 보상 종류 → 지급 단계. mult = 위험 노드 ×2 (전표·개성·능력치·소모품은 양 ×mult, 패시브는 한 번 — 엘리트 길이면 희귀 이상).
 * rand = 전표 흔들림
 */
export function rewardSteps(
  g: Game,
  kind: RewardKind,
  mult: number,
  opts: { rarities?: readonly string[] } = {},
): Step[] {
  const R = BUNDLE2.rewards;
  const n = Math.max(1, Math.round(mult));
  switch (kind) {
    case 'gold':
      return [
        (next) => {
          g.economy.addGold(rewardGold(R.gold.amount, R.gold.jitter, mult, g.rng.next()));
          next();
        },
      ];
    case 'personality':
      return [
        (next) => {
          g.progress.gainGrowth(Math.round(R.personality.amount * mult));
          next();
        },
      ];
    case 'statPoint':
      return [
        (next) => {
          gameState.pointsPending += R.statPoint.amount * n;
          g.progress.openStatChooser(next);
        },
      ];
    case 'consumable':
      return Array.from({ length: n }, () => consumableStep(g));
    case 'passive':
      return [
        (next) => {
          g.buildMenus.openPassiveMenu('node', { choices: R.passive.choices, rarities: opts.rarities }, next);
        },
      ];
  }
}

/** 이벤트 효과 하나 → 단계 (lore = 자막) */
export function effectStep(g: Game, e: EventEffect, lore = ''): Step {
  return (next) => {
    const B = gameState.bundle;
    switch (e.kind) {
      case 'gold':
        if (e.value >= 0) g.economy.addGold(e.value);
        else g.economy.spendGold(-e.value);
        return next();
      case 'personality':
        g.progress.gainGrowth(e.value);
        return next();
      case 'sense':
        gameState.senses.sense += e.value;
        gameState.pointsPending += e.value;
        return g.progress.openStatChooser(next);
      case 'maxHp':
        changeMaxHp(g, e.value);
        return next();
      case 'potion':
        changePotions(g, e.value);
        return next();
      case 'potionFill':
        changePotions(g, 'fill');
        return next();
      case 'laterGold':
        B.laterGold += e.value;
        return next();
      case 'extraWave':
        B.extraWave += e.value;
        return next();
      case 'consumable':
        return chain(
          Array.from({ length: Math.max(1, e.value) }, () => consumableStep(g)),
          next,
        );
      case 'lore':
        g.ui.story('notice', lore);
        return next();
      case 'diaryRead':
        // 61라운드 E4: 일기장 이력으로 한 줄 (EventNode 가 lore 로 넘긴다)
        g.ui.story('event', lore);
        return next();
      case 'shopDiscount':
        B.shopDiscount = Math.max(B.shopDiscount, e.value);
        return next();
      case 'passive':
        return void g.buildMenus.openPassiveMenu('node', { choices: e.choices, rarities: e.rarities }, next);
      case 'curse':
        g.build.grantCurse(e.id, { source: 'event' });
        return next();
    }
  };
}

export function effectSteps(g: Game, effects: readonly EventEffect[] | undefined, lore = ''): Step[] {
  return (effects ?? []).map((e) => effectStep(g, e, lore));
}
