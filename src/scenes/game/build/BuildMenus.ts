/**
 * 57라운드 빌드 축 선택 메뉴 (계약 §14.4 줄 종류 · §14.7 curse): 패시브 3지선다·2택 (보스·궤짝·저주 이득·노드 보상·상점 진열 훅) ·
 * 저주 2택 · 구조물 저주 줄. 메뉴 그리기는 UI(MENU_OPEN), 시스템 임시 텍스트는 TextMenu.
 * 61 G (P12): 옛 개성 3지선다(갈래·강화·피의 계약·각성)·이중 개성 칸은 무기 성장(`growth/GrowthFlow`)으로 옮겼다.
 */
import { EventBus, Events, type CurseGainedPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUILD, CURSES, curseDef, curseOn, curseSourceOn, tagOn, themeTagOf } from '../../../data/build';
import { ECONOMY } from '../../../data';
import { UI_EVENTS, __system, type UiMenuLine, type UiRarity, type UiRelicSource } from '../../../contract/ui';
import type { PassiveDef } from '../../../systems/passives';
import { RELICS } from '../../../data/relics';
import { rollRelics, uiRelic } from '../../../systems/relics';
import type { Game } from '../../Game';

/** 패시브 메뉴 출처 (획득 경로 57 Q29): 보스 · 궤짝(2택) · 저주 이득 · 노드 보상(2차 묶음) · 상점 진열(2차 묶음) · 시험장 */
export type PassiveSource = 'boss' | 'chest' | 'curse' | 'node' | 'shop' | 'lab';

const RARITIES: readonly UiRarity[] = ['common', 'rare', 'epic', 'legendary'];
const asRarity = (r: string): UiRarity | undefined =>
  (RARITIES as readonly string[]).includes(r) ? (r as UiRarity) : undefined;
/** 메뉴 출처 → 계약 유품 출처 */
const relicSource = (s: PassiveSource): UiRelicSource => s;

export class BuildMenus {
  constructor(private readonly g: Game) {}

  // --- 유품 3지선다 · 2택 (62 루프 2 C P1-5: 옛 패시브 → '유품' 카드 — 효과는 같은 id 패시브 1레벨) ---

  /**
   * 유품 선택 메뉴: 들고 있는 무기 문장이 있는 유품만 · 이미 가진 것 제외 · 희귀도 가중(1층 테마 태그 ×2).
   * 메뉴 id 는 'passive' 그대로(카드 3장 레이아웃) — 줄 `relic`(계약 C 절). 보스 = '군주의 유품'. 고를 것이 없으면 바로 onDone
   */
  openPassiveMenu(
    source: PassiveSource,
    opts: {
      choices?: number;
      rarities?: readonly string[];
      /** 60라운드 Q30: 이 희귀도 count 개 확정 + 나머지 일반 확률 */
      guaranteed?: { rarities: readonly string[]; count: number };
    } = {},
    onDone: () => void = () => {},
  ): boolean {
    const g = this.g;
    const count =
      opts.choices ??
      (source === 'chest'
        ? BUILD.acquisition.chestChoices
        : source === 'boss'
          ? RELICS.bossChoices
          : BUILD.acquisition.nodeChoices);
    const weapon = gameState.weapon.id;
    const picks = rollRelics(gameState.passives, weapon, g.rng, ECONOMY.rarity, count, {
      rarities: opts.rarities,
      guaranteed: opts.guaranteed,
      themeTag: themeTagOf(gameState.floorReached),
      themeMult: BUILD.pool.themeWeightMult,
      floor: gameState.build.floor,
    });
    const lines: UiMenuLine[] = [];
    const actions: (() => void)[] = [];
    for (const p of picks) {
      const line = this.relicLine(String(lines.length + 1), p, source);
      if (!line) continue;
      lines.push(line);
      actions.push(() => this.grantRelic(p.id, source));
    }
    if (lines.length === 0) {
      onDone();
      return false;
    }
    const T = RELICS.ui;
    const title = source === 'boss' ? T.bossTitle : source === 'curse' ? T.curseTitle : T.rewardTitle;
    const footer =
      source === 'boss' ? (T.bossSub[gameState.stageId] ?? T.footer) : source === 'node' ? T.rewardSub : T.footer;
    g.menu.open(
      'passive',
      title,
      lines,
      (key) => {
        const act = actions[Number(key) - 1];
        if (!act) return;
        act();
        g.menu.close();
        onDone();
      },
      footer,
    );
    return true;
  }

  /** 유품 하나를 지닌다 (또 고르면 한 단계 깊어진다 — 메뉴·시험장·장터 공용). 효과 = 같은 id 패시브 */
  grantRelic(id: string, source: PassiveSource): boolean {
    if (!gameState.passives.add(id)) return false;
    const level = gameState.passives.level(id);
    EventBus.emit(Events.PASSIVE_GAINED, { id, level });
    this.g.build.record('passive', { id, source });
    const p = gameState.passives.def(id);
    const relic = p
      ? uiRelic(p, gameState.weapon.id, level, gameState.passives.maxLevel, { source: relicSource(source) })
      : null;
    if (relic) __system.emit(UI_EVENTS.RELIC_GAINED, relic);
    return true;
  }

  /** 유품 카드 줄 (보상 메뉴 · 62 D 장터 노점 카드 공용) */
  relicLine(key: string, p: PassiveDef, source: PassiveSource): UiMenuLine | null {
    const have = gameState.passives.level(p.id);
    const relic = uiRelic(p, gameState.weapon.id, have + 1, gameState.passives.maxLevel, {
      source: relicSource(source),
      owned: have > 0,
    });
    if (!relic) return null;
    const rarity = asRarity(p.rarity);
    return {
      key,
      // 계약 C 절: 줄 kind 는 호환으로 'passive' — `relic` 이 있으면 유품 카드
      kind: 'passive',
      label: relic.name,
      enabled: true,
      detail: relic.line,
      relic,
      // 태그 1개 (1층에서 켜진 태그)
      ...(relic.tag && tagOn(relic.tag, gameState.build.floor) ? { tags: [relic.tag] } : {}),
      ...(rarity ? { rarity } : {}),
    };
  }

  // --- 구조물 저주 줄 (57 Q37 획득 경로: 카운터·묘 — curses.json sources) ---

  private structureCurse(kind: string) {
    // 61라운드 P4: 1층은 구조물에서 저주를 주지 않는다 (위험 노드·E9 만)
    const floor = gameState.build.floor;
    if (!curseSourceOn('structure', floor)) return null;
    return CURSES.items.find((c) => c.sources.includes(kind) && curseOn(c, floor)) ?? null;
  }

  structureCurseLine(kind: string, key: string): UiMenuLine | null {
    const d = this.structureCurse(kind);
    if (!d) return null;
    const busy = gameState.build.curse !== null;
    return {
      key,
      kind: 'curse',
      label: `저주 — ${d.name}`,
      enabled: !busy,
      detail: busy
        ? '저주는 동시에 하나'
        : `${d.benefit} / ${d.penalty} · ${d.nodes !== undefined ? `${d.nodes}노드` : `${d.kills}처치`}`,
    };
  }

  grantStructureCurse(kind: string): boolean {
    const d = this.structureCurse(kind);
    return d ? this.g.build.grantCurse(d.id, { source: 'structure' }) : false;
  }

  // --- 저주 2택 (위험 노드 '저주 길'·이벤트 — 2차 묶음 훅) ---

  /** 저주 2택 (필수 — cancelKey 없음). ids 가 없으면 7종에서 무작위 2개 */
  openCurseMenu(
    ids?: readonly string[],
    onDone: () => void = () => {},
    source: CurseGainedPayload['source'] = 'other',
  ): boolean {
    const g = this.g;
    if (gameState.build.curse) {
      onDone();
      return false;
    }
    // 61라운드 P4: 이 층 저주만 (1층 3종)
    const pool = CURSES.items.filter((c) => curseOn(c, gameState.build.floor)).map((c) => c.id);
    const pick = ids ? [...ids] : [];
    while (!ids && pick.length < 2 && pick.length < pool.length) {
      const id = pool[Math.floor(g.rng.next() * pool.length)];
      if (!pick.includes(id)) pick.push(id);
    }
    const defs = pick.map((id) => curseDef(id)).filter((d): d is NonNullable<typeof d> => Boolean(d));
    if (defs.length === 0) {
      onDone();
      return false;
    }
    const lines: UiMenuLine[] = defs.map((d, i) => ({
      key: String(i + 1),
      kind: 'curse',
      label: d.name,
      enabled: true,
      detail: `${d.benefit} / ${d.penalty} · ${d.nodes !== undefined ? `${d.nodes}노드` : `${d.kills}처치`}`,
    }));
    g.setFrozen(true);
    g.menu.open('curse', '저주 — 하나를 받는다', lines, (key) => {
      const d = defs[Number(key) - 1];
      if (!d) return;
      g.menu.close();
      g.setFrozen(false);
      g.build.grantCurse(d.id, { source });
      onDone();
    });
    return true;
  }
}
