/**
 * 61라운드 단계 4 P12 무기 성장 흐름 (씬 쪽 — 옛 Progression 개성 적립·BuildMenus 개성 3지선다·AwakenFlow 최종 각성 대체):
 * 각성 게이지 적립(누적) → 눈금 대기 → 다른 메뉴·보스 연출·각성 정지가 끝나면 그 눈금 메뉴(게임 정지, `growthMenu`) →
 * 개성 발현 / 1차 각성(갈래) / 2차 각성(길) / 단련. 각성 연출·외형은 `build/AwakenFlow`.
 * 계약 UI §18: 스냅샷 `growth` · 이벤트 GROWTH_GAIN·AWAKEN·TRAIT_GAINED · firstTime = 메타 일기장 `diary.guides`.
 * 시스템 이벤트(음향 sound §10·런 로그): GROWTH_GAINED · GROWTH_MARK · TRAIT_GAINED · WEAPON_AWAKEN · WEAPON_TEMPERED.
 */
import { BUILD_ART, MENU_GUARD } from '../../../core/Constants';
import {
  EventBus,
  Events,
  type GrowthGainedPayload,
  type GrowthMarkPayload,
  type TraitGainedPayload,
  type WeaponAwakenPayload,
  type WeaponTemperedPayload,
} from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { STORY } from '../../../data';
import { GROWTH, growthBranch, traitDef } from '../../../data/growth';
import type { GrowthMarkKind } from '../../../data/growthTypes';
import { UI_EVENTS, __system, type UiAwaken, type UiGrowth, type UiGrowthGain } from '../../../contract/ui';
import { effectiveKind, nextMarkOf, pendingMarkOf, type GrowthMark } from '../../../systems/growth/growth';
import { growthMenu, type GrowthChoice, type GrowthMenu } from '../../../systems/growth/growthMenu';
import { GUIDE_KINDS, uiGrowth, uiTrait, type GuideKind } from '../../../systems/growth/uiGrowth';
import { diaryNow, recordGuide, updateDiary } from '../../../systems/narrative/diary';
import { evolutionLine, fill } from '../../../systems/story';
import type { Game } from '../../Game';
import { GrowthArt } from './GrowthArt';
import { lockedTraits } from '../../../systems/memory/memory';
import { RUN_END } from '../../../data/runEnd';
import { metaStore } from '../../../systems/meta';

export class GrowthFlow {
  /** 디버그: 마지막 메뉴 · 최근 사건 */
  lastMenu: { kind: GrowthMarkKind; at: number; lines: string[] } | null = null;
  readonly log: { t: number; ev: string; info?: unknown }[] = [];
  /** 본 처음 안내 (메타 일기장 — 씬마다 한 번 읽는다) */
  private guides: string[];
  private open: { menu: GrowthMenu; mark: GrowthMark; traitCards?: number } | null = null;

  private readonly art: GrowthArt;

  /** 62 루프 2 E: 이 시각(씬 ms)까지 눈금 메뉴를 열지 않는다 (성과 등급 카드 — MENU_GUARD.GRADE_HOLD_MS) */
  private holdUntil = 0;
  /** 62 루프 2 E: 각성 연출 시트를 미리 받은 단계 */
  private readonly prefetched = new Set<1 | 2>();
  private primed = false;

  private readonly onGraded = (): void => {
    this.holdUntil = this.g.time.now + MENU_GUARD.GRADE_HOLD_MS;
  };

  constructor(private readonly g: Game) {
    EventBus.on(Events.NODE_GRADED, this.onGraded);
    this.guides = [...diaryNow().guides];
    // art §26 미리보기 (UI 선택 화면·성장도 나무) · §27 개성 카드 그림 — 이 무기 것만, 작은 정지 그림
    this.art = new GrowthArt(g);
    this.art.load(gameState.weapon.id);
  }

  private get floor() {
    return gameState.build.floor;
  }

  private record(ev: string, info?: unknown): void {
    this.log.push({ t: Math.round(this.g.time.now), ev, ...(info !== undefined ? { info } : {}) });
    if (this.log.length > 30) this.log.shift();
  }

  // --- 적립 ---

  /** 각성 게이지 적립 (처치·완·획 자국·이벤트·보스·결정타·구조물·저주 이득). 눈금 메뉴는 update 에서 */
  gain(amount: number): void {
    // 61 단계 6 수련장: 각성 게이지 과제가 남은 무기 방에서만 오른다 (다른 방에서 눈금 메뉴가 끼어들지 않게)
    if (this.g.training && !this.g.training.allowsGrowth) return;
    const w = gameState.weapon;
    const a = w.gain(Math.round(amount));
    if (a <= 0) return;
    EventBus.emit(Events.GROWTH_GAINED, { weapon: w.id, amount: a, gauge: w.gauge } satisfies GrowthGainedPayload);
    this.prefetchAwaken();
    __system.emit(UI_EVENTS.GROWTH_GAIN, { amount: a, gauge: w.gauge } satisfies UiGrowthGain);
  }

  /** 지금 처리할 눈금 (게이지가 넘었는데 아직 고르지 않은) */
  pending(): GrowthMark | null {
    const w = gameState.weapon;
    return pendingMarkOf(this.floor, w.gauge, w.marksDone);
  }

  /** 매 프레임 (정지 중에도): 눈금 대기 → 다른 메뉴·보스 연출·각성 정지가 끝나면 메뉴 */
  maybeOpen(): void {
    const g = this.g;
    // 62 루프 2 E: 노드 시작 때 이미 각성 눈금 가까이면 미리 받기 (BuildRuntime 이 생긴 뒤 첫 프레임 한 번)
    if (this.prefetched.size === 0 && !this.primed && g.build) {
      this.primed = true;
      this.prefetchAwaken();
    }
    // 메뉴가 바깥에서 닫혔으면 (씬 전환 등) 다음에 다시 연다
    if (this.open && !g.menu.isOpen) this.open = null;
    if (this.open || g.menu.isOpen || g.frozen || g.bossFlow?.busy || g.build?.awaken.playing) return;
    // 62 루프 2 C (P1-6): 층 끝 결산 흐름이 개성 발현을 막는 동안 (군주의 유품 뒤 최대 장 수)
    if (g.runEnd?.holdsGrowth()) return;
    if (gameState.gameOver || g.transitioning) return;
    // 62 루프 2 E: 성과 카드·막타 슬로모 동안은 미룬다 (UI 가 카드를 다 보일 때까지 멈춘 화면으로 기다리지 않게)
    if (g.time.now < this.holdUntil || g.combatFeel?.active) return;
    const mark = this.pending();
    if (mark) this.openMark(mark);
  }

  /** 62 루프 2 E: 다음 눈금이 각성이고 게이지가 절반을 넘었으면 각성 연출 시트를 미리 받는다 (한 번) */
  private prefetchAwaken(): void {
    const w = gameState.weapon;
    const next = nextMarkOf(this.floor, w.marksDone);
    const kind = effectiveKind(next.kind, w.stage);
    const stage = kind === 'awaken1' ? 1 : kind === 'awaken2' ? 2 : null;
    if (!stage || this.prefetched.has(stage) || !this.g.build) return;
    if (w.gauge < next.at * MENU_GUARD.AWAKEN_PREFETCH_AT) return;
    this.prefetched.add(stage);
    this.g.build.awaken.prefetch(stage);
    this.record('prefetch', stage);
  }

  private openMark(mark: GrowthMark, rerollCards?: number): void {
    const g = this.g;
    const w = gameState.weapon;
    const kind = effectiveKind(mark.kind, w.stage);
    // 62 루프 2 C: 첫 개성 발현 카드 수(회피 시험 등급·먹 묻은 붓) · '기억'으로 열지 않은 개성은 풀에 없다 (시험장·수련장은 제한 없음)
    const run = !g.lab;
    const traitCards =
      rerollCards ?? (run && kind === 'trait' ? gameState.memory.takeTraitCards(GROWTH.traitChoices) : undefined);
    const menu = growthMenu(
      w,
      kind,
      this.floor,
      () => g.rng.next(),
      (wid, b, s, p) => this.lookKey(wid, b, s, p),
      (wid, id) => this.iconKey(wid, id),
      { locked: run ? lockedTraits(metaStore.read(), w.id) : undefined, traitCards },
    );
    if (!menu) {
      // 고를 것이 없다 (개성·단련을 다 얻음) — 눈금만 지나간다
      w.marksDone += 1;
      this.record('skip', { at: mark.at, kind });
      return;
    }
    // 62 루프 2 C: 다시 뽑기(먹물 한 병·사연)가 남았으면 개성 발현 메뉴에 한 줄 (key 'reroll' — 고르면 카드를 새로 뽑는다)
    const R = RUN_END.reroll;
    if (run && kind === 'trait' && gameState.memory.rerolls > 0)
      menu.lines.push({
        key: R.key,
        label: R.label,
        enabled: true,
        detail: fill(R.detail, { n: gameState.memory.rerolls }),
      });
    this.open = { menu, mark, traitCards };
    this.lastMenu = { kind, at: mark.at, lines: menu.lines.map((l) => l.label) };
    if (kind === 'awaken1' || kind === 'awaken2') g.build.awaken.prefetch(kind === 'awaken1' ? 1 : 2);
    EventBus.emit(Events.GROWTH_MARK, {
      weapon: w.id,
      kind,
      at: mark.at,
      index: mark.index,
    } satisfies GrowthMarkPayload);
    g.setFrozen(true);
    g.menu.open('evolve', menu.title, menu.lines, (key) => this.select(key), menu.footer);
    this.record('open', { at: mark.at, kind });
  }

  private select(key: string): void {
    const o = this.open;
    if (!o) return;
    if (key === RUN_END.reroll.key) {
      if (!gameState.memory.takeReroll()) return;
      this.open = null;
      this.record('reroll', { at: o.mark.at });
      this.openMark(o.mark, o.traitCards ?? GROWTH.traitChoices);
      return;
    }
    const i = Number(key) - 1;
    const c = o.menu.choices[i];
    if (!c || !o.menu.lines[i]?.enabled) return;
    this.open = null;
    const g = this.g;
    gameState.weapon.marksDone = Math.max(gameState.weapon.marksDone, o.mark.index + 1);
    g.menu.close();
    g.setFrozen(false);
    this.seeGuide(o.menu.kind);
    this.apply(c);
  }

  /** 고른 것 적용 (메뉴·시험장 공용) */
  apply(c: GrowthChoice): void {
    if (c.kind === 'trait') this.gainTrait(c.id);
    else if (c.kind === 'temper') this.temper();
    else this.awaken(c.kind === 'awaken1' ? 1 : 2, c.node);
  }

  // --- 개성 · 단련 · 각성 ---

  gainTrait(id: string): boolean {
    const g = this.g;
    const w = gameState.weapon;
    const t = traitDef(id);
    if (!t || !w.addTrait(id)) return false;
    gameState.build.touch();
    __system.emit(
      UI_EVENTS.TRAIT_GAINED,
      uiTrait(t, (wid, tid) => this.iconKey(wid, tid)),
    );
    EventBus.emit(Events.TRAIT_GAINED, {
      weapon: w.id,
      id,
      verb: t.verb,
      tag: t.tag,
      ...(t.branch ? { branch: t.branch } : {}),
    } satisfies TraitGainedPayload);
    // 62 I (P1-N2): 개성 획득은 UI 카드 토스트(TRAIT_GAINED) 하나만 — 같은 문장을 STORY notice 로 또 보내지 않는다.
    // UI 렌더러가 없을 때(시스템 대체 화면)만 notice 로
    if (!__system.rendererRegistered())
      g.ui.story('notice', fill(GROWTH.text.traitNotice, { name: t.name, line: t.line }));
    // 개성 획득 표시 (옛 이중 개성 dual_trait_get 그림 재사용) — 메뉴를 닫고 전투로 돌아온 뒤
    g.build.afterMenu(() => g.build.art.onPlayer(BUILD_ART.DUAL_GET));
    this.record('trait', id);
    return true;
  }

  /** 62 루프 2 C: 다시 뽑기 n 개 (장터 '먹물 한 병' · 사연 '다듬는다') — 다음 개성 발현 메뉴에 한 줄로 */
  addRerolls(n: number): void {
    if (n <= 0) return;
    gameState.memory.rerolls += Math.floor(n);
    this.record('rerolls', gameState.memory.rerolls);
  }

  /** 단련 1회 (단련 눈금 · 62 루프 2 C 장터 '풀무질 한 번' — 더 할 수 없으면 false) */
  temper(): boolean {
    const g = this.g;
    const w = gameState.weapon;
    if (!w.temperNow()) return false;
    EventBus.emit(Events.WEAPON_TEMPERED, {
      weapon: w.id,
      temper: w.temper,
      name: w.displayName,
    } satisfies WeaponTemperedPayload);
    g.ui.story('evolution', STORY.reinforce[w.temper - 1] ?? STORY.reinforce[STORY.reinforce.length - 1]);
    this.record('temper', w.temper);
    return true;
  }

  /** 1차·2차 각성: 경로를 바꾸고 연출 (정지·fx·외형) */
  awaken(stage: 1 | 2, node: string): boolean {
    const g = this.g;
    const w = gameState.weapon;
    if (w.stage !== stage - 1 || !w.choose(node)) return false;
    gameState.build.touch();
    const branch = growthBranch(w.id, w.branchId);
    const path = branch?.paths.find((p) => p.id === w.pathId) ?? null;
    const name = stage === 1 ? (branch?.name ?? '') : (path?.name ?? '');
    const line = stage === 1 ? (branch?.line ?? '') : (path?.line ?? '');
    const lookKey = this.lookKey(w.id, w.branchId, stage, stage === 2 ? (w.pathId ?? undefined) : undefined);
    g.build.awaken.begin(stage);
    const ui: UiAwaken = {
      stage,
      weapon: w.id,
      branch: w.branchId ?? '',
      ...(w.pathId && stage === 2 ? { path: w.pathId } : {}),
      name,
      line,
      ...(lookKey ? { lookKey } : {}),
    };
    __system.emit(UI_EVENTS.AWAKEN, ui);
    EventBus.emit(Events.WEAPON_AWAKEN, {
      stage,
      weapon: w.id,
      branch: ui.branch,
      ...(ui.path ? { path: ui.path } : {}),
      name,
    } satisfies WeaponAwakenPayload);
    g.ui.story('evolution', evolutionLine(name));
    this.record('awaken', { stage, branch: ui.branch, path: ui.path });
    return true;
  }

  // --- 처음 안내 (계약 §18 firstTime → 메타 diary.guides) ---

  private seeGuide(kind: GrowthMarkKind): void {
    if (this.g.lab || !(GUIDE_KINDS as readonly string[]).includes(kind) || this.guides.includes(kind)) return;
    this.guides.push(kind);
    updateDiary((d) => recordGuide(d, kind as GuideKind));
  }

  // --- 그림 (art §26 미리보기 · §27 개성 카드 — GrowthArt) ---

  /** 로드된 미리보기 텍스처 키 (없으면 undefined) */
  lookKey(weapon: string, branch: string | null, stage: 0 | 1 | 2, path?: string): string | undefined {
    return this.art.lookKey(weapon, branch, stage, path);
  }

  /** 로드된 개성 카드 그림 키 (없으면 undefined) */
  iconKey(weapon: string, traitId: string): string | undefined {
    return this.art.iconKey(weapon, traitId);
  }

  // --- 스냅샷 ---

  toUi(): UiGrowth {
    return uiGrowth(gameState.weapon, this.floor, {
      guides: this.guides,
      look: (wid, b, s, p) => this.lookKey(wid, b, s, p),
      icon: (wid, id) => this.iconKey(wid, id),
    });
  }

  // --- 시험장 (#lab: 게이지 자유 조작 · 모든 갈래·길) ---

  /** 게이지 +n (눈금 메뉴가 그대로 열린다) */
  labGain(n: number): void {
    this.gain(n);
  }

  /** 게이지·개성·단련·눈금 처음으로 (경로는 그대로) */
  labReset(): void {
    const w = gameState.weapon;
    w.gauge = 0;
    w.marksDone = 0;
    w.traits = [];
    w.temper = 0;
    gameState.build.touch();
  }

  /** 경로를 바로 정한다 (갈래·길) — 연출 없이 외형·그림만 */
  labSetPath(path: readonly string[]): void {
    const w = gameState.weapon;
    w.setPath(path);
    // 갈래가 바뀌면 그 갈래 개성은 버린다
    w.traits = w.traits.filter((id) => {
      const t = traitDef(id);
      return !t?.branch || t.branch === w.branchId;
    });
    gameState.build.touch();
    this.g.build.awaken.sync(true);
  }

  debug(): Record<string, unknown> {
    const w = gameState.weapon;
    const p = this.pending();
    return {
      gauge: w.gauge,
      marksDone: w.marksDone,
      stage: w.stage,
      branch: w.branchId,
      path: w.pathId,
      traits: [...w.traits],
      temper: w.temper,
      pending: p ? { ...p, effective: effectiveKind(p.kind, w.stage) } : null,
      open: this.open ? { kind: this.open.menu.kind, at: this.open.mark.at } : null,
      lastMenu: this.lastMenu,
      awaken: this.g.build?.awaken.last ?? null,
      // 메뉴를 미루는 것들 (maybeOpen 조건)
      blockers: {
        menu: this.g.menu.isOpen,
        frozen: this.g.frozen,
        boss: Boolean(this.g.bossFlow?.busy),
        awakenPlaying: Boolean(this.g.build?.awaken.playing),
        gameOver: gameState.gameOver,
        transitioning: this.g.transitioning,
      },
      log: [...this.log],
    };
  }

  destroy(): void {
    this.open = null;
    EventBus.off(Events.NODE_GRADED, this.onGraded);
  }
}
