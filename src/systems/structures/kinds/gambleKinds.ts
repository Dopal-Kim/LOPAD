/**
 * E형·자동 구조물 — 2층 도박: 패 탁자(2-1, 나쁜 패 = 정예 도전) · 목숨 칩 환전대(2-2) · 투견 링(2-3, 시간 제한 도전) ·
 * 룰렛(2-5, 시련 시작 때 규칙) · 전당포(2-6).
 */
import { STRUCTURE_FX, TILE } from '../../../core/Constants';
import { EventBus, Events, type PlayerDamagedPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { ECONOMY } from '../../../data';
import type { UiMenuLine } from '../../../contract/ui';
import { STRUCTURE_TEXT, num, txt, type StructureDef } from '../data';
import { bloodCost, canSellBlood, cardStake, dealCards, pawnValue, redeemCost, ringPayout } from '../rules';
import { MENU_MAX_LINES, type Inst, type StructureCore } from '../core';

/** 룰렛이 도는 연출 시간 */
const ROULETTE_SPIN_MS = 1200;

export interface PawnLine {
  label: string;
  enabled: boolean;
  detail?: string;
  run: () => void;
}

export class GambleKinds {
  constructor(private readonly c: StructureCore) {}

  // --- 2-1 패 탁자 ---

  cardParams(d: StructureDef) {
    return {
      stake: num(d, 'stake'),
      stakeStep: num(d, 'stakeStep'),
      goodGoldMult: num(d, 'goodGoldMult'),
      goodBoostPerRound: num(d, 'goodBoostPerRound'),
      goodWeights: d.params.goodWeights as Record<string, number>,
    };
  }

  openCards(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const round = s.round + 1;
    const P = this.cardParams(d);
    const stake = cardStake(round, P);
    s.deck = dealCards(c.host.rng, stake, round, P);
    const can = gameState.gold >= stake;
    const lines: UiMenuLine[] = [1, 2, 3].map((n) => ({
      key: String(n),
      label: txt(d, 'card', { n }),
      enabled: can,
      detail: can ? txt(d, 'cardDetail', { stake }) : STRUCTURE_TEXT.reasons.gold,
    }));
    c.openMenu(
      'cards',
      s,
      txt(d, 'menuTitle', { stake, round, max: num(d, 'maxRounds') }),
      lines,
      (key) => {
        c.host.menu.close();
        const card = s.deck?.[Number(key) - 1];
        if (!card || gameState.gold < stake) return;
        c.host.spendGold(stake);
        s.round = round;
        c.setVisual(s, 'active');
        if (s.round >= num(d, 'maxRounds')) {
          s.state = 'used';
          c.host.scene.time.delayedCall(600, () => c.setVisual(s, 'used'));
        }
        c.used(s, `cards.pick${key}`);
        switch (card.kind) {
          case 'gold':
            c.host.addGold(card.gold);
            c.result(s, 'gain', txt(d, 'goodGold', { gold: card.gold }), { gold: card.gold - stake });
            break;
          case 'potion':
            c.givePotions(s, 1);
            c.result(s, 'mixed', txt(d, 'goodPotion'), { gold: -stake, potions: 1 });
            break;
          case 'point':
            gameState.pointsPending += 1;
            c.result(s, 'mixed', txt(d, 'goodPoint'), { gold: -stake, points: 1 });
            c.host.openStatChooser();
            break;
          case 'bad':
            c.result(s, 'loss', txt(d, 'bad'), { gold: -stake });
            this.startCardFight(s);
            break;
        }
      },
      txt(d, 'menuFooter'),
    );
  }

  private startCardFight(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const count = num(d, 'badCount');
    const ok = c.host.director.startChallenge(
      s.roomId,
      [{ enemy: String(d.params.badEnemy), count, hpMult: num(d, 'eliteHp'), attackMult: num(d, 'eliteAttack') }],
      () => {
        c.cardFight = null;
        c.challengeCleared(s, 'cardTable', 'clear', txt(d, 'challengeClear'));
      },
    );
    if (!ok) return;
    c.cardFight = s;
    c.challengeStarted(s, 'cardTable', txt(d, 'challengeLabel'), txt(d, 'challengeGoal', { n: count }), null);
  }

  // --- 2-2 목숨 칩 환전대 ---

  openExchange(s: Inst, exhausted: (s: Inst) => boolean): void {
    const c = this.c;
    const d = s.def;
    const cost = bloodCost(gameState.hp, num(d, 'bloodHpRatio'));
    const bloodLeft = num(d, 'bloodLimit') - s.bloodUses;
    const lifeLeft = num(d, 'lifeLimit') - s.lifeUses;
    const lifeHp = num(d, 'lifeMaxHp');
    c.openMenu(
      'exchange',
      s,
      txt(d, 'menuTitle'),
      [
        {
          key: '1',
          label: txt(d, 'blood', { hp: cost, gold: num(d, 'bloodGold') }),
          enabled: bloodLeft > 0 && canSellBlood(gameState.hp, gameState.maxHp, num(d, 'bloodMinRatio')),
          detail: txt(d, 'bloodDetail', { pct: Math.round(num(d, 'bloodHpRatio') * 100), left: bloodLeft }),
        },
        {
          key: '2',
          label: txt(d, 'life', { maxHp: lifeHp, points: num(d, 'lifePoints') }),
          enabled: lifeLeft > 0 && gameState.maxHp > lifeHp + 1,
          detail: txt(d, 'lifeDetail', { left: lifeLeft }),
        },
      ],
      (key) => {
        c.host.menu.close();
        if (key === '1') {
          s.bloodUses += 1;
          const pay = bloodCost(gameState.hp, num(d, 'bloodHpRatio'));
          gameState.hp = Math.max(1, gameState.hp - pay);
          EventBus.emit(Events.PLAYER_DAMAGED, {
            hp: gameState.hp,
            maxHp: gameState.maxHp,
            amount: pay,
          } satisfies PlayerDamagedPayload);
          c.host.addGold(num(d, 'bloodGold'));
          c.result(s, 'mixed', txt(d, 'sold', { gold: num(d, 'bloodGold') }), { hp: -pay, gold: num(d, 'bloodGold') });
          c.used(s, 'exchange.blood');
        } else {
          s.lifeUses += 1;
          c.loseMaxHp(lifeHp);
          gameState.pointsPending += num(d, 'lifePoints');
          c.result(s, 'mixed', txt(d, 'staked'), { maxHp: -lifeHp, points: num(d, 'lifePoints') });
          c.used(s, 'exchange.life');
          c.host.openStatChooser();
        }
        if (exhausted(s)) c.setVisual(s, 'used');
      },
    );
  }

  // --- 2-3 투견 링 ---

  startRing(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const stake = num(d, 'stake');
    if (gameState.gold < stake) return;
    const count = num(d, 'count');
    const center = { x: s.rect.centerX, y: s.rect.centerY };
    const ok = c.host.director.startChallenge(
      s.roomId,
      [{ enemy: String(d.params.enemy), count, hpMult: num(d, 'eliteHp'), attackMult: num(d, 'eliteAttack') }],
      () => this.finishRing(c.ring?.hits === 0 ? 'flawless' : 'clear'),
      { ...center, radiusTiles: num(d, 'spawnRadiusTiles') },
    );
    if (!ok) return;
    c.host.spendGold(stake);
    // 링 안으로
    c.host.player.body.reset(center.x, center.y + TILE * STRUCTURE_FX.RING_ENTER_TILES);
    const limit = num(d, 'timeLimitMs');
    c.ring = { inst: s, until: c.now + limit, hits: 0, max: count, stake };
    s.state = 'active';
    c.setVisual(s, 'active');
    c.used(s, d.text.actionKey);
    c.challengeStarted(
      s,
      'dogRing',
      txt(d, 'challengeLabel'),
      txt(d, 'challengeGoal', { sec: Math.round(limit / 1000), n: count }),
      limit,
    );
  }

  updateRing(time: number): void {
    if (!this.c.ring || time < this.c.ring.until) return;
    this.c.host.director.abortChallenge();
    this.finishRing('timeout');
  }

  private finishRing(outcome: 'clear' | 'flawless' | 'timeout'): void {
    const c = this.c;
    const r = c.ring;
    if (!r) return;
    c.ring = null;
    const s = r.inst;
    const d = s.def;
    s.state = 'used';
    c.setVisual(s, 'used');
    const gold = ringPayout(r.stake, outcome, { clearMult: num(d, 'clearMult'), flawlessMult: num(d, 'flawlessMult') });
    if (gold > 0) c.host.addGold(gold);
    const mult = outcome === 'flawless' ? num(d, 'flawlessMult') : num(d, 'clearMult');
    const text = outcome === 'timeout' ? txt(d, 'timeout') : txt(d, outcome, { mult, gold });
    c.result(s, outcome === 'timeout' ? 'loss' : 'gain', text, outcome === 'timeout' ? {} : { gold });
    c.challengeCleared(s, 'dogRing', outcome, text);
  }

  /** 링 도전 중 피격 횟수 (무피해 판정) */
  onPlayerDamaged(p: PlayerDamagedPayload): void {
    if (this.c.ring && p.amount > 0) this.c.ring.hits += 1;
  }

  // --- 2-5 룰렛 ---

  /** 그 시련 방 시련 시작(웨이브 생성 전) → 규칙 결정 */
  onTrialStarted(p: { roomId: string }): void {
    const c = this.c;
    const s = c.list.find((i) => i.kind === 'roulette' && i.roomId === p.roomId && i.state === 'idle');
    if (!s) return;
    const rules = s.def.params.rules as Record<string, unknown>[];
    const idx = c.host.rng.int(0, rules.length - 1);
    s.state = 'active';
    c.roulette = { inst: s, roomId: p.roomId, ruleIndex: idx };
    c.setVisual(s, 'active');
    const stop = s.views[0].def?.stopFrames?.[String(idx)];
    c.host.scene.time.delayedCall(ROULETTE_SPIN_MS, () => {
      if (stop !== undefined && c.roulette?.inst === s) s.views[0].showFrame(stop);
    });
    EventBus.emit(Events.STRUCTURE_ROULETTE, c.evt(s));
    const rule = rules[idx];
    c.result(s, 'info', txt(s.def, 'spin', { rule: String(rule.name), detail: String(rule.detail) }), {});
  }

  /** 그 시련 방 클리어: 룰렛 보너스 */
  onTrialCleared(roomId: string): void {
    const c = this.c;
    if (c.roulette?.roomId !== roomId) return;
    const s = c.roulette.inst;
    const rule = c.ruleAt(c.roulette.ruleIndex);
    let gold = num(s.def, 'clearBonusGold');
    if (rule && typeof rule.trialBonusMult === 'number')
      gold += Math.round(ECONOMY.gold.trialBonus * (rule.trialBonusMult - 1));
    c.roulette = null;
    s.state = 'used';
    c.setVisual(s, 'used');
    c.host.addGold(gold);
    c.result(s, 'gain', txt(s.def, 'bonus', { gold }), { gold });
  }

  /** '받아쳐라': 패링·가드 성공마다 개성 */
  counterRule(): void {
    const rule = this.c.activeRule();
    if (rule && typeof rule.parryPersonality === 'number') this.c.host.gainGrowth(rule.parryPersonality);
  }

  // --- 2-6 전당포 ---

  pawnLines(s: Inst): PawnLine[] {
    const c = this.c;
    const d = s.def;
    const P = { rarityValue: d.params.rarityValue as Record<string, number>, levelBonus: num(d, 'levelBonus') };
    const out: PawnLine[] = [];
    for (const [id, level] of Object.entries(gameState.passives.owned)) {
      const def = gameState.passives.def(id);
      if (!def) continue;
      const gold = pawnValue(def.rarity, level, P);
      out.push({
        label: txt(d, 'pawnPassive', { name: def.name, level, gold }),
        enabled: true,
        detail: def.description,
        run: () => {
          const lv = gameState.passives.remove(id);
          c.pawned.push({ key: `p:${id}`, type: 'passive', passiveId: id, level: lv, name: def.name, received: gold });
          c.host.addGold(gold);
          c.result(s, 'mixed', txt(d, 'pawned', { name: def.name, gold }), { gold });
        },
      });
    }
    if (gameState.potions > 0) {
      const gold = num(d, 'potionValue');
      out.push({
        label: txt(d, 'pawnPotion', { gold }),
        enabled: true,
        run: () => {
          gameState.potions -= 1;
          EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
          c.pawned.push({ key: `potion:${c.serial++}`, type: 'potion', name: '잔의 독주', received: gold });
          c.host.addGold(gold);
          c.result(s, 'mixed', txt(d, 'pawned', { name: '잔의 독주', gold }), { gold, potions: -1 });
        },
      });
    }
    for (const it of c.pawned) {
      const cost = redeemCost(it.received, num(d, 'redeemMult'));
      out.push({
        label: txt(d, 'redeem', { name: it.name, gold: cost }),
        enabled: gameState.gold >= cost && (it.type !== 'potion' || gameState.potions < c.host.potionCarry()),
        run: () => {
          if (gameState.gold < cost) return;
          c.host.spendGold(cost);
          c.pawned = c.pawned.filter((p) => p !== it);
          if (it.type === 'passive' && it.passiveId) {
            gameState.passives.setLevel(it.passiveId, it.level ?? 1);
            EventBus.emit(Events.PASSIVE_GAINED, { id: it.passiveId, level: gameState.passives.level(it.passiveId) });
          } else c.givePotions(s, 1);
          c.result(s, 'info', txt(d, 'redeemed', { name: it.name }), { gold: -cost });
        },
      });
    }
    return out;
  }

  openPawn(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const all = this.pawnLines(s);
    if (all.length === 0) return;
    // UI 요청: 선택지 '1'~'8' + 그만두기 '0' (길면 8개까지만, 임시)
    const shown = all.slice(0, MENU_MAX_LINES);
    const lines: UiMenuLine[] = shown.map((l, i) => ({
      key: String(i + 1),
      label: l.label,
      enabled: l.enabled,
      detail: l.detail,
    }));
    c.openMenu(
      'pawn',
      s,
      txt(d, 'menuTitle', { gold: gameState.gold }),
      lines,
      (key) => {
        const pick = shown[Number(key) - 1];
        if (!pick) return;
        pick.run();
        c.used(s, 'pawn.deal');
        // 선택마다 다시 그림 (계약 §9.4)
        if (this.pawnLines(s).length > 0) this.openPawn(s);
        else c.host.menu.close();
      },
      txt(d, 'menuFooter'),
    );
  }
}
