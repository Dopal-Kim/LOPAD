/**
 * E형 구조물 — 공통·1층: 궤짝(C2) · 무명 전사의 묘(C3, 길게 누르기) · 모닥불(C5, 불씨) · 외상 장부대(1-3, 빚) ·
 * 숙성 통(1-4) · 선술집 카운터(1-5, 취기).
 */
import { EventBus, Events } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { ECONOMY } from '../../../data';
import type { UiMenuLine } from '../../../contract/ui';
import { metaStore } from '../../meta';
import { floorText } from '../../story';
import { num, txt } from '../data';
import { agingProgress, chestPrice, emberHeal } from '../rules';
import type { Inst, StructureCore } from '../core';

export class ServiceKinds {
  constructor(private readonly c: StructureCore) {}

  // --- C2 궤짝 ---

  chestCost(s: Inst): number {
    const d = s.def;
    return chestPrice(
      { basePrice: num(d, 'basePrice'), stepPrice: num(d, 'stepPrice'), perFloorPrice: num(d, 'perFloorPrice') },
      this.c.chestsOpened,
      gameState.stageIndex,
      s.discount,
    );
  }

  openChest(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const price = this.chestCost(s);
    if (gameState.gold < price) return;
    c.host.spendGold(price);
    c.chestsOpened += 1;
    s.state = 'used';
    c.setVisual(s, 'used');
    // 57라운드 Q29: 궤짝 = 패시브 2택 (47 Q8 임시 1개 대체) — 빌드 메뉴가 열리면 결과는 메뉴에서
    if (c.host.build?.chestPick(() => {})) {
      c.result(s, 'mixed', txt(d, 'pick'), { gold: -price });
      c.used(s, d.text.actionKey);
      return;
    }
    const pick = gameState.passives.rollChoices(c.host.rng, ECONOMY.rarity, 1, { floor: gameState.build.floor })[0];
    if (pick) {
      gameState.passives.add(pick.id);
      EventBus.emit(Events.PASSIVE_GAINED, { id: pick.id, level: gameState.passives.level(pick.id) });
      c.result(s, 'mixed', txt(d, 'passive', { name: pick.name }), { gold: -price });
    } else {
      const refund = Math.round(price * num(d, 'fallbackRefund'));
      c.givePotions(s, num(d, 'fallbackPotions'));
      c.host.addGold(refund);
      c.result(s, 'mixed', txt(d, 'fallback', { potion: '잔의 독주', gold: refund }), {
        gold: refund - price,
        potions: num(d, 'fallbackPotions'),
      });
    }
    c.used(s, d.text.actionKey);
  }

  // --- C5 모닥불 ---

  useCampfire(s: Inst): void {
    const c = this.c;
    const d = s.def;
    if (c.embers <= 0) return;
    const before = gameState.hp;
    c.host.heal(emberHeal(c.embers, gameState.maxHp, num(d, 'healPerEmber')));
    const n = c.embers;
    c.embers = 0;
    c.setVisual(s, 'used');
    c.result(s, 'gain', txt(d, 'used', { n, hp: gameState.hp - before }), { hp: gameState.hp - before });
    if (d.params.restNoteOnUse) c.host.story('rest', floorText(gameState.stageId)?.restNote ?? '');
    c.used(s, d.text.actionKey);
  }

  // --- 1-4 숙성 통 ---

  agingReady(s: Inst): boolean {
    if (s.agingAt === null) return false;
    return agingProgress(s.agingAt, gameState.trialsCleared, num(s.def, 'trialsNeeded')).ready;
  }

  useAging(s: Inst): void {
    const c = this.c;
    const d = s.def;
    if (s.agingAt === null) {
      const n = num(d, 'potionIn');
      if (gameState.potions < n) return;
      gameState.potions -= n;
      EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
      s.agingAt = gameState.trialsCleared;
      s.state = 'active';
      c.setVisual(s, 'active');
      c.result(s, 'info', txt(d, 'put', { n: num(d, 'trialsNeeded') }), { potions: -n });
      c.used(s, d.text.putActionKey);
      return;
    }
    if (!this.agingReady(s)) return;
    const out = num(d, 'potionsOut');
    c.givePotions(s, out);
    s.state = 'used';
    c.setVisual(s, 'used');
    c.result(s, 'gain', txt(d, 'take', { n: out }), { potions: out });
    c.used(s, d.text.takeActionKey);
  }

  // --- C3 묘 ---

  openGraveMenu(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const souls = num(d, 'souls');
    const pers = num(d, 'personality');
    c.openMenu(
      'grave',
      s,
      txt(d, 'menuTitle'),
      [
        { key: '1', label: txt(d, 'record'), enabled: true, detail: txt(d, 'recordDetail', { souls }) },
        { key: '2', label: txt(d, 'accept'), enabled: true, detail: txt(d, 'acceptDetail', { personality: pers }) },
        ...curseLines(c, 'grave', '3'),
      ],
      (key) => {
        c.host.menu.close();
        if (key === '3') {
          if (c.host.build?.grantCurse('grave')) c.used(s, 'grave.curse');
          return;
        }
        s.state = 'used';
        c.setVisual(s, 'used');
        if (key === '1') {
          const m = metaStore.read();
          metaStore.write({ ...m, souls: m.souls + souls, totalSouls: m.totalSouls + souls });
          gameState.bonusSouls += souls;
          c.result(s, 'gain', txt(d, 'recorded', { souls }), { souls });
          c.used(s, 'grave.record');
        } else {
          c.host.gainPersonality(pers);
          c.result(s, 'gain', txt(d, 'accepted', { personality: pers }), { personality: pers });
          c.used(s, 'grave.accept');
        }
      },
    );
  }

  // --- 1-3 외상 장부대 ---

  openLedger(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const loan = num(d, 'loan');
    const debtAdd = num(d, 'debt');
    const repay = Math.min(gameState.gold, c.debt);
    c.openMenu(
      'ledger',
      s,
      txt(d, 'menuTitle', { debt: c.debt }),
      [
        {
          key: '1',
          label: txt(d, 'borrow', { loan, debt: debtAdd }),
          enabled: s.loans < num(d, 'loansPerFloor'),
          detail: txt(d, 'borrowDetail', { pct: Math.round(num(d, 'repayRatio') * 100), hp: num(d, 'maxHpPer10Debt') }),
        },
        {
          key: '2',
          label: txt(d, 'repay', { amount: repay }),
          enabled: c.debt > 0 && repay > 0,
          detail: txt(d, 'repayDetail'),
        },
        ...curseLines(c, 'ledger', '3'),
      ],
      (key) => {
        c.host.menu.close();
        if (key === '3') {
          if (c.host.build?.grantCurse('ledger')) c.used(s, 'ledger.curse');
          return;
        }
        if (key === '1') {
          s.loans += 1;
          c.debt += debtAdd;
          c.host.addGold(loan);
          c.setVisual(s, 'used');
          c.result(s, 'mixed', txt(d, 'borrowed', { loan, debt: c.debt }), { gold: loan });
          c.used(s, 'ledger.borrow');
        } else {
          const pay = Math.min(gameState.gold, c.debt);
          if (pay <= 0) return;
          c.host.spendGold(pay);
          c.debt -= pay;
          c.result(s, 'info', txt(d, 'repaid', { amount: pay, debt: c.debt }), { gold: -pay });
          c.used(s, 'ledger.repay');
        }
      },
    );
  }

  // --- 1-5 선술집 카운터 ---

  openCounter(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const price = num(d, 'cupPrice');
    const P = c.drunkParams;
    const lines: UiMenuLine[] = [];
    for (let i = 0; i < num(d, 'cups'); i++) {
      const drunkCup = i < s.cups;
      const next = i === s.cups;
      lines.push({
        key: String(i + 1),
        label: drunkCup ? txt(d, 'cupEmpty', { n: i + 1 }) : txt(d, 'cup', { n: i + 1, price }),
        enabled: next && gameState.gold >= price && c.drunk < P.maxLevel,
        detail: txt(d, 'cupDetail', { atk: Math.round(P.attackPerLevel * 100), def: P.defensePerLevel }),
      });
    }
    lines.push(...curseLines(c, 'counter', String(num(d, 'cups') + 1)));
    const curseKey = String(num(d, 'cups') + 1);
    c.openMenu('counter', s, txt(d, 'menuTitle', { level: c.drunk }), lines, (key) => {
      c.host.menu.close();
      if (key === curseKey) {
        if (c.host.build?.grantCurse('counter')) c.used(s, 'counter.curse');
        return;
      }
      if (gameState.gold < price) return;
      c.host.spendGold(price);
      s.cups += 1;
      c.setDrunk(Math.min(P.maxLevel, c.drunk + 1));
      if (s.cups >= num(d, 'cups')) {
        s.state = 'used';
        c.setVisual(s, 'used');
      } else c.setVisual(s, `used${s.cups}`);
      c.result(s, 'mixed', txt(d, 'drank', { level: c.drunk }), { gold: -price });
      c.used(s, 'counter.drink');
    });
  }

  /** 시련 클리어·보스 처치: 취기 해제 */
  sober(): void {
    const c = this.c;
    if (c.drunk <= 0) return;
    c.setDrunk(0);
    const s = c.find('counter');
    if (s) c.result(s, 'info', txt(s.def, 'sober'), {});
  }
}

/** 57라운드: 구조물 저주 줄 (빌드 축 훅이 없거나 이 구조물이 주는 저주가 없으면 []) */
function curseLines(c: StructureCore, kind: string, key: string): UiMenuLine[] {
  const line = c.host.build?.curseLine(kind, key);
  return line ? [line] : [];
}
