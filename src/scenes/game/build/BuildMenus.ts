/**
 * 57라운드 빌드 축 선택 메뉴 (계약 §14.4 줄 종류 · §14.7 curse): 패시브 3지선다·2택 (보스·궤짝·저주 이득·노드 보상·상점 진열 훅) ·
 * 저주 2택 · 구조물 저주 줄. 메뉴 그리기는 UI(MENU_OPEN), 시스템 임시 텍스트는 TextMenu.
 * 61 G (P12): 옛 개성 3지선다(갈래·강화·피의 계약·각성)·이중 개성 칸은 무기 성장(`growth/GrowthFlow`)으로 옮겼다.
 */
import { EventBus, Events, type CurseGainedPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUILD, CURSES, curseDef, curseOn, curseSourceOn, tagOn, themeTagOf } from '../../../data/build';
import { ECONOMY, STORY } from '../../../data';
import type { UiMenuLine, UiRarity, UiTagId } from '../../../contract/ui';
import type { PassiveDef } from '../../../systems/passives';
import type { Game } from '../../Game';

/** 패시브 메뉴 출처 (획득 경로 57 Q29): 보스 · 궤짝(2택) · 저주 이득 · 노드 보상(2차 묶음) · 상점 진열(2차 묶음) · 시험장 */
export type PassiveSource = 'boss' | 'chest' | 'curse' | 'node' | 'shop' | 'lab';

const RARITIES: readonly UiRarity[] = ['common', 'rare', 'epic', 'legendary'];
const asRarity = (r: string): UiRarity | undefined =>
  (RARITIES as readonly string[]).includes(r) ? (r as UiRarity) : undefined;

export class BuildMenus {
  constructor(private readonly g: Game) {}

  // --- 패시브 3지선다 · 2택 ---

  /**
   * 패시브 선택 메뉴: 희귀도 가중 패시브 (1층 테마 태그 ×2).
   * 고를 것이 없으면 바로 onDone
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
          ? BUILD.acquisition.bossChoices
          : BUILD.acquisition.nodeChoices);
    const theme = themeTagOf(gameState.floorReached);
    const picks = gameState.passives.rollChoices(g.rng, ECONOMY.rarity, count, {
      rarities: opts.rarities,
      guaranteed: opts.guaranteed,
      themeTag: theme,
      themeMult: BUILD.pool.themeWeightMult,
      floor: gameState.build.floor,
    });
    if (picks.length === 0) {
      onDone();
      return false;
    }
    const lines: UiMenuLine[] = [];
    const actions: (() => void)[] = [];
    for (const p of picks) {
      const lv = gameState.passives.level(p.id);
      lines.push(this.passiveLine(String(lines.length + 1), p, lv));
      actions.push(() => {
        gameState.passives.add(p.id);
        EventBus.emit(Events.PASSIVE_GAINED, { id: p.id, level: gameState.passives.level(p.id) });
        g.build.record('passive', { id: p.id, source });
      });
    }
    g.menu.open('passive', STORY.ui.hud.passiveTitle, lines, (key) => {
      const act = actions[Number(key) - 1];
      if (!act) return;
      act();
      g.menu.close();
      onDone();
    });
    return true;
  }

  private passiveLine(key: string, p: PassiveDef, lv: number): UiMenuLine {
    const rarity = asRarity(p.rarity);
    return {
      key,
      kind: 'passive',
      label: `${p.name}${lv > 0 ? ` (Lv${lv} → ${lv + 1})` : ''}`,
      enabled: true,
      detail: p.description,
      // 61라운드 P4: 이 층에서 꺼진 태그는 보이지 않는다 (점수도 없다)
      tags: p.tags.filter((t) => tagOn(t, gameState.build.floor)) as UiTagId[],
      ...(rarity ? { rarity } : {}),
    };
  }

  // --- 구조물 저주 줄 (57 Q37 획득 경로: 카운터·장부대·묘 — curses.json sources) ---

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
