/**
 * 61라운드 단계 4 P12 무기 성장 흐름 (씬 쪽 — 옛 Progression 개성 적립·BuildMenus 개성 3지선다·AwakenFlow 최종 각성 대체):
 * 각성 게이지 적립(누적) → 눈금 대기 → 다른 메뉴·보스 연출·각성 정지가 끝나면 그 눈금 메뉴(게임 정지, `growthMenu`) →
 * 개성 발현 / 1차 각성(갈래) / 2차 각성(길) / 단련. 각성 연출·외형은 `build/AwakenFlow`.
 * 계약 UI §18: 스냅샷 `growth` · 이벤트 GROWTH_GAIN·AWAKEN·TRAIT_GAINED · firstTime = 메타 일기장 `diary.guides`.
 * 시스템 이벤트(음향 sound §10·런 로그): GROWTH_GAINED · GROWTH_MARK · TRAIT_GAINED · WEAPON_AWAKEN · WEAPON_TEMPERED.
 */
import { ASSETS, BUILD_ART } from '../../../core/Constants';
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
import { effectiveKind, pendingMarkOf, type GrowthMark } from '../../../systems/growth/growth';
import { growthMenu, type GrowthChoice, type GrowthMenu } from '../../../systems/growth/growthMenu';
import { GUIDE_KINDS, uiGrowth, uiTrait, type GuideKind } from '../../../systems/growth/uiGrowth';
import { diaryNow, recordGuide, updateDiary } from '../../../systems/narrative/diary';
import { assetListed } from '../../../systems/sprites/sheetLoader';
import { evolutionLine, fill } from '../../../systems/story';
import type { Game } from '../../Game';

export class GrowthFlow {
  /** 디버그: 마지막 메뉴 · 최근 사건 */
  lastMenu: { kind: GrowthMarkKind; at: number; lines: string[] } | null = null;
  readonly log: { t: number; ev: string; info?: unknown }[] = [];
  /** 본 처음 안내 (메타 일기장 — 씬마다 한 번 읽는다) */
  private guides: string[];
  private open: { menu: GrowthMenu; mark: GrowthMark } | null = null;

  constructor(private readonly g: Game) {
    this.guides = [...diaryNow().guides];
    // art §26 미리보기 (UI 선택 화면·성장도 나무) — 이 무기 것만, 작은 정지 그림
    this.loadLooks();
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
    const w = gameState.weapon;
    const a = w.gain(Math.round(amount));
    if (a <= 0) return;
    EventBus.emit(Events.GROWTH_GAINED, { weapon: w.id, amount: a, gauge: w.gauge } satisfies GrowthGainedPayload);
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
    // 메뉴가 바깥에서 닫혔으면 (씬 전환 등) 다음에 다시 연다
    if (this.open && !g.menu.isOpen) this.open = null;
    if (this.open || g.menu.isOpen || g.frozen || g.bossFlow?.busy || g.build?.awaken.playing) return;
    if (gameState.gameOver || g.transitioning) return;
    const mark = this.pending();
    if (mark) this.openMark(mark);
  }

  private openMark(mark: GrowthMark): void {
    const g = this.g;
    const w = gameState.weapon;
    const kind = effectiveKind(mark.kind, w.stage);
    const menu = growthMenu(
      w,
      kind,
      this.floor,
      () => g.rng.next(),
      (wid, b, s, p) => this.lookKey(wid, b, s, p),
    );
    if (!menu) {
      // 고를 것이 없다 (개성·단련을 다 얻음) — 눈금만 지나간다
      w.marksDone += 1;
      this.record('skip', { at: mark.at, kind });
      return;
    }
    this.open = { menu, mark };
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
    __system.emit(UI_EVENTS.TRAIT_GAINED, uiTrait(t));
    EventBus.emit(Events.TRAIT_GAINED, {
      weapon: w.id,
      id,
      verb: t.verb,
      tag: t.tag,
      ...(t.branch ? { branch: t.branch } : {}),
    } satisfies TraitGainedPayload);
    g.ui.story('notice', fill(GROWTH.text.traitNotice, { name: t.name, line: t.line }));
    // 개성 획득 표시 (옛 이중 개성 dual_trait_get 그림 재사용) — 메뉴를 닫고 전투로 돌아온 뒤
    g.build.afterMenu(() => g.build.art.onPlayer(BUILD_ART.DUAL_GET));
    this.record('trait', id);
    return true;
  }

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

  // --- 미리보기 그림 (art §26 looks — 있으면 UI 가 쓴다) ---

  /** art §26 미리보기 파일: `<무기>_base` · `<무기>_<갈래>_a1` · `<무기>_<갈래>_a2_<길>`(길 색을 구운 완성 그림) */
  private lookFile(weapon: string, branch: string | null, stage: 0 | 1 | 2, path?: string): string {
    if (!branch || stage === 0) return `${weapon}_base.png`;
    return stage === 2 && path ? `${weapon}_${branch}_a2_${path}.png` : `${weapon}_${branch}_a${stage}.png`;
  }

  /** 로드된 미리보기 텍스처 키 (없으면 undefined) */
  lookKey(weapon: string, branch: string | null, stage: 0 | 1 | 2, path?: string): string | undefined {
    const key = `growth_look_${this.lookFile(weapon, branch, stage, path).replace('.png', '')}`;
    return this.g.textures.exists(key) ? key : undefined;
  }

  /** 씬 시작 — 이 무기의 기본·갈래 3·길 6 미리보기를 (매니페스트에 있으면) 받아 둔다 */
  private loadLooks(): void {
    const g = this.g;
    const w = gameState.weapon;
    const files = [this.lookFile(w.id, null, 0)];
    for (const b of GROWTH.weapons[w.id]?.branches ?? []) {
      files.push(this.lookFile(w.id, b.id, 1));
      for (const p of b.paths) files.push(this.lookFile(w.id, b.id, 2, p.id));
    }
    let queued = false;
    for (const f of files) {
      const rel = `${ASSETS.LOOKS_DIR}/${f}`;
      const key = `growth_look_${f.replace('.png', '')}`;
      if (g.textures.exists(key) || !assetListed(rel)) continue;
      g.load.image(key, `${ASSETS.URL}/${rel}`);
      queued = true;
    }
    if (queued && !g.load.isLoading()) g.load.start();
  }

  // --- 스냅샷 ---

  toUi(): UiGrowth {
    return uiGrowth(gameState.weapon, this.floor, {
      guides: this.guides,
      look: (wid, b, s, p) => this.lookKey(wid, b, s, p),
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
  }
}
