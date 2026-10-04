/**
 * 57라운드 빌드 축 선택 메뉴 (계약 §14.4 줄 종류 · §14.7 curse): 개성 3지선다 칸 (Q37 — 100 = [1단 A/B/강화] · 200 = [2단 α/β/강화] ·
 * 이후 200마다 [강화 / 피의 계약 / 각성(잠김)]) · 패시브 3지선다·2택 (보스·궤짝·저주 이득·노드 보상·상점 진열 훅 — 이중 개성 대기 시
 * 첫 칸 확정, Q27) · 저주 2택. 메뉴 그리기는 UI(MENU_OPEN), 시스템 임시 텍스트는 TextMenu.
 */
import { EventBus, Events } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { AWAKENINGS, BUILD, CURSES, DUAL_TRAITS, curseDef, themeTagOf } from '../../../data/build';
import { ECONOMY, STORY, WEAPON_RULES } from '../../../data';
import { UI_EVENTS, __system, type UiMenuLine, type UiRarity, type UiTagId } from '../../../contract/ui';
import type { DualTraitDef } from '../../../data/buildTypes';
import type { PassiveDef } from '../../../systems/passives';
import { currentBuild } from '../../../systems/build/current';
import {
  anySlotOpen,
  awakenReady,
  eligibleDualTraits,
  evolveSlots,
  type EvolveSlot,
} from '../../../systems/build/evolveSlots';
import { fill } from '../../../systems/story';
import type { Game } from '../../Game';

/** 패시브 메뉴 출처 (획득 경로 57 Q29): 보스 · 궤짝(2택) · 저주 이득 · 노드 보상(2차 묶음) · 상점 진열(2차 묶음) · 시험장 */
export type PassiveSource = 'boss' | 'chest' | 'curse' | 'node' | 'shop' | 'lab';

const RARITIES: readonly UiRarity[] = ['common', 'rare', 'epic', 'legendary'];
const asRarity = (r: string): UiRarity | undefined =>
  (RARITIES as readonly string[]).includes(r) ? (r as UiRarity) : undefined;

export class BuildMenus {
  /** 디버그: 마지막 개성 칸 */
  lastSlots: EvolveSlot[] = [];

  constructor(private readonly g: Game) {}

  // --- 개성 3지선다 ---

  private awakenState() {
    const w = gameState.weapon;
    const A = BUILD.awaken;
    const r = awakenReady({
      nodes: w.nodes,
      scores: currentBuild().scores,
      bossFloorCleared: gameState.build.bossFloorCleared,
      lab: this.g.lab,
      tagScore: A.tagScore,
      afterBossFloor: A.afterBossFloor,
    });
    return { ready: r.ready, done: gameState.build.awakened, condition: A.condition };
  }

  slots(): EvolveSlot[] {
    const w = gameState.weapon;
    return evolveSlots({
      options: w.options,
      canReinforce: w.canReinforce,
      curseActive: gameState.build.curse !== null,
      pactAvailable: CURSES.pactPool.length > 0,
      awaken: this.awakenState(),
    });
  }

  /** 게이지가 의미가 있는가 (열린 칸이 하나라도) — Progression.gainPersonality */
  canEvolve(): boolean {
    return anySlotOpen(this.slots());
  }

  openEvolveMenu(): void {
    const g = this.g;
    const w = gameState.weapon;
    const slots = this.slots();
    this.lastSlots = slots;
    if (!anySlotOpen(slots)) {
      w.choicePending = false;
      return;
    }
    g.setFrozen(true);
    const cur = w.evolution ? w.evolution.name : w.def.name;
    const bonusPct = Math.round(WEAPON_RULES.reinforceBonus * 100);
    const A = AWAKENINGS[w.id];
    const lines: UiMenuLine[] = slots.map((s, i) => {
      const key = String(i + 1);
      switch (s.kind) {
        case 'branchA':
        case 'branchB':
          return {
            key,
            kind: s.kind,
            label: s.node ? s.node.name : '변환 (완료)',
            enabled: s.enabled,
            detail: s.node?.description,
            ...(s.node?.tags ? { tags: [...s.node.tags] as UiTagId[] } : {}),
          };
        case 'reinforce': {
          const node = w.evolution;
          const tagTarget = node?.tags?.length
            ? node.tags.slice(0, BUILD.scoring.reinforceTagTarget === 'all' ? 2 : 1)
            : [];
          return {
            key,
            kind: 'reinforce',
            label: `${fill(STORY.ui.evolveMenu.reinforceItem, { n: w.reinforce + 1 })} — ${cur}`,
            enabled: s.enabled,
            detail: `피해·범위 +${bonusPct}% · 강화 ${w.reinforce}/${w.reinforceCap}${tagTarget.length && w.reinforce < BUILD.scoring.reinforceTagMax ? ' · 갈래 태그 +1' : ''}`,
            ...(tagTarget.length ? { tags: [...tagTarget] as UiTagId[] } : {}),
          };
        }
        case 'bloodPact':
          return {
            key,
            kind: 'bloodPact',
            label: '피의 계약',
            enabled: s.enabled,
            detail: s.enabled
              ? `저주 하나 (무작위) — 이득 ×${BUILD.evolve.pactBenefitMult}, 지속 +${BUILD.evolve.pactExtraNodes}노드`
              : (s.reason ?? ''),
          };
        case 'awaken':
          return {
            key,
            kind: 'awaken',
            label: A ? `최종 각성 — ${A.name}` : '최종 각성',
            enabled: s.enabled,
            detail: s.locked ? `잠김: ${s.locked.condition}` : s.enabled ? (A?.description ?? '') : (s.reason ?? ''),
            locked: s.locked ?? null,
          };
      }
    });
    g.menu.open(
      'evolve',
      fill(STORY.ui.evolveMenu.title, { weapon: w.def.name, threshold: w.threshold }),
      lines,
      (key) => {
        const s = slots[Number(key) - 1];
        if (!s?.enabled) return;
        if ((s.kind === 'branchA' || s.kind === 'branchB') && s.node) g.progress.applyEvolution(s.node.id);
        else if (s.kind === 'reinforce') g.progress.applyReinforce();
        else if (s.kind === 'bloodPact') this.applyPact();
        else if (s.kind === 'awaken') this.applyAwaken();
      },
      STORY.ui.evolveMenu.footer,
    );
  }

  private closeChoice(): void {
    gameState.weapon.consumeChoice();
    this.g.menu.close();
    this.g.setFrozen(false);
  }

  private applyPact(): void {
    this.closeChoice();
    this.g.build.grantPactCurse();
  }

  /** 최종 각성 (57 Q33): 강화 상한 5, 각성 규칙(공통 + 2단별) 켜짐 */
  applyAwaken(): boolean {
    const g = this.g;
    const w = gameState.weapon;
    const A = AWAKENINGS[w.id];
    if (!A || gameState.build.awakened) return false;
    this.closeChoice();
    gameState.build.awakened = true;
    gameState.build.touch();
    w.reinforceCapOverride = BUILD.evolve.reinforceMaxAwakened;
    g.screenFx.evolve();
    const name = `${w.displayName} · ${A.name}`;
    EventBus.emit(Events.WEAPON_EVOLVED, { weapon: w.id, stage: w.stage + 1, name });
    __system.emit(UI_EVENTS.WEAPON_EVOLVED, { name });
    g.ui.story('evolution', `${A.name} — ${A.description}`);
    g.build.record('awaken', w.id);
    return true;
  }

  // --- 패시브 3지선다 · 2택 (이중 개성 확정 칸) ---

  /** 지금 보상 칸에 나올 이중 개성 (조건 충족·미획득, 데이터 순서 첫 번째) */
  pendingDual(): DualTraitDef | null {
    const w = gameState.weapon;
    const list = eligibleDualTraits(
      DUAL_TRAITS,
      w.id,
      w.path,
      currentBuild().scores,
      new Set(gameState.build.dualOwned),
      BUILD.dual,
    );
    return list[0] ?? null;
  }

  /**
   * 패시브 선택 메뉴. 이중 개성이 대기 중이면 첫 칸이 그 이중 개성(kind 'dual'), 나머지는 희귀도 가중 패시브 (1층 테마 태그 ×2).
   * 고를 것이 없으면 바로 onDone
   */
  openPassiveMenu(
    source: PassiveSource,
    opts: { choices?: number; rarities?: readonly string[] } = {},
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
    const dual = source === 'curse' || source === 'shop' ? null : this.pendingDual();
    const theme = themeTagOf(gameState.floorReached);
    const picks = gameState.passives.rollChoices(g.rng, ECONOMY.rarity, count - (dual ? 1 : 0), {
      rarities: opts.rarities,
      themeTag: theme,
      themeMult: BUILD.pool.themeWeightMult,
    });
    if (!dual && picks.length === 0) {
      onDone();
      return false;
    }
    const lines: UiMenuLine[] = [];
    const actions: (() => void)[] = [];
    if (dual) {
      const node = gameState.weapon.nodes.find((n) => n.id === dual.branch);
      lines.push({
        key: '1',
        kind: 'dual',
        label: `[이중 개성] ${dual.name}`,
        enabled: true,
        detail: `${node?.name ?? dual.branch} × ${dual.tag} — ${dual.description}`,
        tags: [dual.tag],
      });
      actions.push(() => g.build.addDualTrait(dual.id));
    }
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
      label: `[${p.rarity}] ${p.name}${lv > 0 ? ` (Lv${lv} → ${lv + 1})` : ''}`,
      enabled: true,
      detail: p.description,
      tags: [...p.tags] as UiTagId[],
      ...(rarity ? { rarity } : {}),
    };
  }

  // --- 구조물 저주 줄 (57 Q37 획득 경로: 카운터·장부대·묘 — curses.json sources) ---

  private structureCurse(kind: string) {
    return CURSES.items.find((c) => c.sources.includes(kind)) ?? null;
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
    return d ? this.g.build.grantCurse(d.id) : false;
  }

  // --- 저주 2택 (위험 노드 '저주 길'·이벤트 — 2차 묶음 훅) ---

  /** 저주 2택 (필수 — cancelKey 없음). ids 가 없으면 7종에서 무작위 2개 */
  openCurseMenu(ids?: readonly string[], onDone: () => void = () => {}): boolean {
    const g = this.g;
    if (gameState.build.curse) {
      onDone();
      return false;
    }
    const pool = CURSES.items.map((c) => c.id);
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
      g.build.grantCurse(d.id);
      onDone();
    });
    return true;
  }
}
