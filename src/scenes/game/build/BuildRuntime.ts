/**
 * 57라운드 빌드 축 런타임 (씬 쪽, Game 마다 새로 — 런 상태는 GameState.build): 합산(`currentBuild`)을 읽어
 * 공통 사건 훅(완벽 성공·이동기·강공·원거리 판정·표식·위기·마시기·처치)에 세트·패시브·개성 카드·갈래·길·저주 규칙을 건다.
 * 일은 나눠서: 타격·처치·투사체 = `BuildCombat`, 피격·버팀·취보 = `BuildDefense`, 완벽 성공·정적 = `BuildPerfect`,
 * 갈래 수단 = `BranchStrikes`, 월드 도우미·플레이스홀더 = `BuildEffects`. UI 이벤트(계약 §14.11)도 여기서.
 */
import {
  EventBus,
  Events,
  type CurseGainedPayload,
  type PlayerAttackPayload,
  type StructureEventPayload,
  type TagSetChangedPayload,
} from '../../../core/EventBus';
import { BUILD_ART } from '../../../core/Constants';
import { gameState } from '../../../core/GameState';
import { BUILD, CURSES, curseDef, tagName } from '../../../data/build';
import { TAG_IDS, type BuildStatKey, type TagId } from '../../../data/buildTypes';
import { ECONOMY } from '../../../data';
import {
  UI_EVENTS,
  __system,
  type UiBuildState,
  type UiCurseEnded,
  type UiStatus,
  type UiTagSetChanged,
} from '../../../contract/ui';
import type { Mob } from '../../../objects/Mob';
import type { Projectile } from '../../../objects/Projectile';
import { isStrongAttack } from '../../../systems/build/strikeKinds';
import { param, ruleOf, rulesOf, type ActiveRule, type BuildMods } from '../../../systems/build/buildMods';
import { uiBuild, uiCurse } from '../../../systems/build/BuildState';
import { currentBuild } from '../../../systems/build/current';
import { CurseState, pickPactCurse, scaledBenefit } from '../../../systems/build/curses';
import { DotBook, DrunkTimer, EvadeTracker, MarkBook } from '../../../systems/build/statusBooks';
import { fxSwapTable } from '../../../systems/sprites/sheetSets';
import type { Game } from '../../Game';
import { AwakenFlow } from './AwakenFlow';
import { TraitRules } from './traits/TraitRules';
import { BranchStrikes } from './BranchStrikes';
import { BuildArt } from './BuildArt';
import { BuildCombat } from './BuildCombat';
import { BuildDefense } from './BuildDefense';
import { BuildEffects } from './BuildEffects';
import { BuildPerfect } from './BuildPerfect';

/** 마시기 사건 출처 (취기 1장) */
export type DrinkSource = 'potion' | 'counter' | 'lastCup' | 'poolKill' | 'consumable';

type Sub = [event: string, fn: (p: never) => void];

export class BuildRuntime {
  readonly fx: BuildEffects;
  /** 60라운드 계약 art §21 상태·세트·저주 시트 */
  readonly art: BuildArt;
  readonly combat: BuildCombat;
  readonly defense: BuildDefense;
  readonly perfect: BuildPerfect;
  readonly branch: BranchStrikes;
  /** 61 G 각성 연출·외형·셋째 갈래 궤적 교체 */
  readonly awaken: AwakenFlow;
  /** 61 G 개성 카드·셋째 갈래 규칙 실행 */
  readonly traits: TraitRules;
  readonly drunk = new DrunkTimer();
  readonly marks = new MarkBook<Mob>();
  readonly dots = new DotBook<Mob>();
  readonly evade = new EvadeTracker();
  /** 세트 단계 (바뀌면 TAG_SET_CHANGED) */
  private stages: Record<TagId, number>;
  /** 디버그: 최근 빌드 사건 */
  readonly log: { t: number; ev: string; info?: unknown }[] = [];
  private subs: Sub[] = [];
  /** 독한 숨: 마시기 직후 다음 공격 1회 */
  liquorBreathUntil = -Infinity;
  /** 대쉬 끝 시각 (깨진 거울·취권·굳은살) */
  dashAt = -Infinity;

  constructor(private readonly g: Game) {
    this.fx = new BuildEffects(g);
    this.art = new BuildArt(g, this);
    this.combat = new BuildCombat(g, this);
    this.defense = new BuildDefense(g, this);
    this.perfect = new BuildPerfect(g, this);
    this.branch = new BranchStrikes(g, this);
    this.awaken = new AwakenFlow(g, this);
    this.traits = new TraitRules(g, this);
    this.stages = { ...currentBuild().stages };
    this.subs = [
      [Events.PLAYER_DASHED, (p: { x: number; y: number; dirX: number; dirY: number }) => this.onDash(p)],
      [Events.POTION_USED, () => this.drink('potion')],
      [Events.STRUCTURE_USED, (p: StructureEventPayload) => this.onStructureUsed(p)],
      [Events.BOSS_DIED, () => this.onBossDied()],
      [Events.PLAYER_ATTACKED, (p: PlayerAttackPayload) => this.combat.onAttack(p)],
      [
        Events.PLAYER_PARRIED,
        (p: { attack: number; dirX?: number; dirY?: number }) =>
          this.perfect.onPerfect('parry', p.attack, p.dirX, p.dirY),
      ],
      [
        Events.PLAYER_PERFECT_GUARD,
        (p: { attack: number; dirX?: number; dirY?: number }) =>
          this.perfect.onPerfect('perfectGuard', p.attack, p.dirX, p.dirY),
      ],
      [Events.ENEMY_ATTACK, (p: { id: string }) => this.perfect.onEnemyAttack(p.id)],
      [Events.PLAYER_DAMAGED, () => this.defense.onDamaged()],
      [Events.WEAPON_RESOURCE, (p: { event: string }) => this.defense.onResource(p.event)],
    ];
    for (const [ev, fn] of this.subs) EventBus.on(ev, fn, this);
    // 48라운드 노드 지도: 이 씬 = 노드 하나 진입 (저주 노드 수)
    if (g.routeMode && g.node)
      this.onNodeEntered(g.nodeKind === 'battle' || g.nodeKind === 'boss' || g.nodeKind === 'road');
    // 만취 서약: 취기 상태 유지
    if (this.mods.flags.drunkAlways) this.drink('counter', true);
    // 61 G: 각성 외형·궤적 색 (preload 에서 못 읽은 그림은 지금)
    this.awaken.onSceneStart();
  }

  // --- 합산 읽기 ---

  get mods(): BuildMods {
    return currentBuild();
  }

  stat(k: BuildStatKey): number {
    return this.mods.stats[k];
  }

  rules(kind: string): ActiveRule[] {
    return rulesOf(this.mods, kind);
  }

  rule(kind: string): ActiveRule | null {
    return ruleOf(this.mods, kind);
  }

  stage(tag: TagId): number {
    return this.mods.stages[tag];
  }

  get now(): number {
    return this.g.time.now;
  }

  get weaponId(): string {
    return gameState.weapon.id;
  }

  /** 갈래 경로에 이 노드가 있는가 */
  hasBranch(id: string): boolean {
    return gameState.weapon.path.includes(id);
  }

  record(ev: string, info?: unknown): void {
    this.log.push({ t: Math.round(this.now), ev, ...(info !== undefined ? { info } : {}) });
    if (this.log.length > 40) this.log.shift();
  }

  // --- 수치 훅 (GameCombat · Player · Economy · BowShots …) ---

  critChanceAdd(): number {
    return this.stat('critChanceAdd');
  }

  /** 치명 피해 배율 = 13라운드 ×1.5 + 급소 4 (+0.5) + 견장 */
  critDamageMult(): number {
    return ECONOMY.critDamageMult + this.stat('critDamageAdd');
  }

  /** 받는 피해 배율 (저주 만취 서약 등) */
  damageTakenMult(): number {
    return Math.max(0, 1 + this.stat('damageTakenMult'));
  }

  shopPriceMult(): number {
    return Math.max(0, 1 + this.stat('shopPriceMult'));
  }

  killGoldMult(): number {
    return Math.max(0, 1 + this.stat('killGoldMult'));
  }

  potionMaxAdd(): number {
    return this.stat('potionMaxAdd');
  }

  potionDropAdd(): number {
    return this.stat('potionDropAdd');
  }

  /** 단검 낙인 최대 추가 (표식 2: 5 → 7) */
  brandMaxAdd(): number {
    const r = this.rule('markOnHits');
    return r ? param(r, 'brandMaxAdd') : 0;
  }

  potionAllowed(): boolean {
    return !this.mods.flags.noPotion;
  }

  /** 완벽 창 추가 ms (철벽 패링 + 울혈 그로기 중 2배 + 명경 패링 창) */
  perfectWindowAddMs(baseMs: number): number {
    let add = this.stat('perfectWindowAddMs');
    const clot = this.rule('clot');
    if (clot && this.g.player?.groggy) add += baseMs * (param(clot, 'perfectWindowMult', 1) - 1);
    const meikyo = this.rule('meikyo');
    if (meikyo) add += Math.max(0, param(meikyo, 'parryWindowMs') - baseMs);
    return add;
  }

  // --- 투사체 (BowShots · GameCombat.onPlayerShotHit) ---

  private readonly strongShots = new WeakSet<Projectile>();
  private readonly perfectShots = new WeakSet<Projectile>();

  /** 화살 발사 배율 (BowShots.spawnArrows) */
  arrowMods(p: PlayerAttackPayload): {
    mult: number;
    forceCrit: boolean;
    sizeMult: number;
    speedMult: number;
    lifeMult: number;
    pierceAdd: number;
  } {
    const c = this.combat.payloadMods(p);
    const b = this.branch.arrowBonus(p);
    const s = this.combat.shotMods();
    return {
      mult: c.mult * b.mult,
      forceCrit: c.forceCrit || b.forceCrit,
      sizeMult: b.sizeMult,
      speedMult: s.speedMult,
      lifeMult: s.lifeMult,
      pierceAdd: s.pierceAdd,
    };
  }

  onArrowSpawn(shot: Projectile, p: PlayerAttackPayload): void {
    if (isStrongAttack(p)) this.strongShots.add(shot);
    if (p.bowPower === 'perfect') this.perfectShots.add(shot);
    this.combat.onShotSpawn(shot);
    this.branch.onArrowSpawn(shot, p);
    this.traits.onArrowSpawn(shot, p);
  }

  isStrongShot(shot: Projectile): boolean {
    return this.strongShots.has(shot);
  }

  isPerfectShot(shot: Projectile): boolean {
    return this.perfectShots.has(shot);
  }

  /** 투사체 적중 배율 · 치명 (금·견장 — 새로 치명이면 치명 피해 배율을 곱한다) */
  shotHit(shot: Projectile, mob: Mob, crit: boolean): { mult: number; crit: boolean } {
    const b = this.combat.shotBonus(shot, mob);
    const c = crit || b.forceCrit;
    return { mult: b.mult * (c && !crit ? this.critDamageMult() : 1), crit: c };
  }

  afterShotHit(shot: Projectile, mob: Mob, crit: boolean, died: boolean): void {
    this.combat.afterShot(shot, mob, crit, died);
    this.branch.onShotHit(shot, mob, died);
    this.branch.onArrowHit(shot, mob);
    this.traits.onShotHit(shot, mob, died);
  }

  // --- 이동기 ---

  private onDash(p: { x: number; y: number; dirX: number; dirY: number }): void {
    this.dashAt = this.now;
    this.evade.arm(this.now, p.x, p.y);
    this.combat.onMove(p.x, p.y, p.dirX, p.dirY, 'dash');
  }

  /** 그림자 걸음 (MotionFx 가 목적지를 정한 뒤) — 이동기 사건 */
  onShadowStep(fromX: number, fromY: number, toX: number, toY: number): void {
    this.evade.arm(this.now, fromX, fromY);
    this.combat.onMove(fromX, fromY, toX - fromX, toY - fromY, 'shadowstep', Math.hypot(toX - fromX, toY - fromY));
    this.traits.onShadowStep({ x: fromX, y: fromY }, { x: toX, y: toY });
  }

  // --- 마시기 · 취기 ---

  /** 마시기 사건 (취기 1장): 취기 세트 2 이상이면 취기 상태, 독한 숨 장전 */
  drink(source: DrinkSource, quiet = false): void {
    const now = this.now;
    const set2 = BUILD.sets.drunk[0].effect;
    const set6 = BUILD.sets.drunk[2].effect;
    const always = this.mods.flags.drunkAlways;
    if (this.stage('drunk') >= 2 || always) {
      const ms = Number(set2.ms) || 0;
      const max = this.stage('drunk') >= 6 ? Number(set6.maxMs) || ms : ms;
      this.drunk.drink(now, ms, max);
    }
    const breath = this.rule('liquorBreath');
    if (breath) this.liquorBreathUntil = now + param(breath, 'windowMs');
    if (!quiet) this.record('drink', source);
  }

  /** 취기 상태 중 (세트 2 이상 또는 만취 서약) */
  get drunkActive(): boolean {
    return this.drunk.active(this.now);
  }

  private onStructureUsed(p: StructureEventPayload): void {
    if (p.actionKey === 'counter.drink') this.drink('counter');
  }

  // --- 노드 · 보스 · 저주 ---

  onNodeEntered(combat: boolean): void {
    const c = gameState.build.curse;
    if (!c) return;
    const ended = c.onNodeEntered(combat);
    gameState.build.touch();
    if (ended) this.endCurse();
  }

  private onBossDied(): void {
    const floor = gameState.floorReached;
    if (floor > gameState.build.bossFloorCleared) {
      gameState.build.bossFloorCleared = floor;
      gameState.build.touch();
    }
  }

  /**
   * 저주 받기 (구조물·위험 노드·이벤트·피의 계약). 동시 1개 — 이미 있으면 false. pact = 개성 '피의 계약' 칸(이득 ×1.5, 지속 +1)
   */
  grantCurse(id: string, opts: { pact?: boolean; source?: CurseGainedPayload['source'] } = {}): boolean {
    const def = curseDef(id);
    if (!def || gameState.build.curse) return false;
    const pact = Boolean(opts.pact);
    const c = new CurseState(def, pact, BUILD.pact.extraNodes);
    const B = def.benefits;
    const m = BUILD.pact.benefitMult;
    gameState.build.curse = c;
    // 즉시 이득
    if (B.goldNow) this.g.economy.addGold(Math.round(scaledBenefit(B.goldNow, pact, m)));
    if (B.personalityNow) this.g.progress.gainGrowth(Math.round(scaledBenefit(B.personalityNow, pact, m)));
    for (const [t, v] of Object.entries(B.permanentTag ?? {})) {
      const k = t as TagId;
      gameState.build.permanentTags[k] =
        (gameState.build.permanentTags[k] ?? 0) + Math.round(scaledBenefit(v ?? 0, pact, m));
    }
    if (B.permanentBurnChance) gameState.build.permanentBurnChance += scaledBenefit(B.permanentBurnChance, pact, m);
    if (B.permanentResourceMax) gameState.build.resourceMaxBonus += scaledBenefit(B.permanentResourceMax, pact, m);
    // 대가: 최대 HP (끝나면 복구)
    const hpCut = def.penalties.maxHpAdd ?? 0;
    if (hpCut < 0) {
      const before = gameState.maxHp;
      gameState.maxHp = Math.max(1, gameState.maxHp + hpCut);
      gameState.hp = Math.min(gameState.hp, gameState.maxHp);
      c.maxHpTaken = before - gameState.maxHp;
    }
    gameState.build.touch();
    if (B.drunkAlways) this.drink('counter', true);
    __system.emit(UI_EVENTS.CURSE_GAINED, uiCurse(c));
    EventBus.emit(Events.CURSE_GAINED, {
      id,
      source: pact ? 'bloodPact' : (opts.source ?? 'other'),
    } satisfies CurseGainedPayload);
    this.g.ui.story('notice', `${def.name} — ${def.benefit} / ${def.penalty}`);
    this.record('curse', { id, pact });
    // 패시브 고르기 이득 (맨손 맹세 영웅 3지선다 · 저주 궤짝 희귀 이상 2택)
    if (B.passivePick)
      this.g.buildMenus.openPassiveMenu('curse', { choices: B.passivePick.choices, rarities: B.passivePick.rarities });
    return true;
  }

  /** 피의 계약 칸: 계약 풀에서 무작위 저주 하나 (pact). 61라운드: pool = 이 층에서 나오는 것 (BuildMenus) */
  grantPactCurse(pool: readonly string[] = CURSES.pactPool): boolean {
    const id = pickPactCurse(pool, this.g.rng.next());
    return id ? this.grantCurse(id, { pact: true }) : false;
  }

  endCurse(): void {
    const c = gameState.build.curse;
    if (!c) return;
    gameState.build.curse = null;
    if (c.maxHpTaken > 0) {
      gameState.maxHp += c.maxHpTaken;
      this.g.player.heal(0);
    }
    gameState.build.touch();
    __system.emit(UI_EVENTS.CURSE_ENDED, { id: c.id, name: c.def.name } satisfies UiCurseEnded);
    EventBus.emit(Events.CURSE_ENDED, { id: c.id });
    this.record('curseEnd', c.id);
  }

  /** 처치 (BuildCombat.onKill 이 부른다) — 저주 궤짝 처치 수 */
  curseKill(): void {
    const c = gameState.build.curse;
    if (c && c.onKill()) this.endCurse();
    else if (c?.killsLeft !== null) gameState.build.touch();
  }

  // --- 매 프레임 ---

  /**
   * 60라운드 계약 art §21 fx 교체 표 (FxPool): 각성 런의 각성 궤적(`AwakenFlow.aliases`) 위에 갈래 런 교체 규칙(경로 노드
   * art.replaceFx)을 덮는다 — 경로·각성이 바뀔 때만. Q33: 갈래 + 각성이면 합친 그림(`<갈래 그림>_awaken`)이 있을 때 그것 (`fxSwapTable`)
   */
  private aliasSig: string | null = null;

  private syncFxAliases(): void {
    const w = gameState.weapon;
    const sig = `${w.id}:${w.path.join('/')}`;
    if (sig === this.aliasSig) return;
    this.aliasSig = sig;
    const replace: Record<string, string> = {};
    for (const n of w.nodes) Object.assign(replace, n.art?.replaceFx ?? {});
    this.g.fx.setAliases(fxSwapTable(this.awaken.aliases(), replace));
  }

  update(time: number): void {
    this.syncFxAliases();
    this.syncStages();
    if (this.mods.flags.drunkAlways && !this.drunk.active(time)) this.drink('counter', true);
    this.combat.update(time);
    this.perfect.update(time);
    this.branch.update(time);
    this.traits.update(time);
    this.art.update(time);
    this.flushAfterMenu();
    // 플레이어 속도·공속 배율 (Player·MeleeDriver 가 읽는다)
    const pl = this.g.player;
    if (pl) {
      pl.buildSpeedMult = this.combat.moveSpeedMult(time);
      pl.buildAttackSpeed = this.combat.attackSpeedMult(time);
      pl.buildNoFlinch = this.drunkActive || this.defense.uninterruptible() || this.traits.noFlinch();
    }
  }

  /** 세트 단계가 바뀌면 TAG_SET_CHANGED (오른 단계 효과 이름) */
  private syncStages(): void {
    const st = this.mods.stages;
    for (const t of TAG_IDS) {
      if (st[t] === this.stages[t]) continue;
      const prev = this.stages[t];
      const up = st[t] > prev;
      this.stages[t] = st[t];
      const eff = BUILD.sets[t].find((s) => s.threshold === st[t]);
      const payload: UiTagSetChanged = {
        tag: t,
        name: tagName(t),
        stage: st[t] as 0 | 2 | 4 | 6,
        effectName: eff?.name ?? '',
      };
      __system.emit(UI_EVENTS.TAG_SET_CHANGED, payload);
      EventBus.emit(Events.TAG_SET_CHANGED, {
        tag: t,
        stage: st[t],
        prev,
        delta: st[t] - prev,
      } satisfies TagSetChangedPayload);
      // set_flash (행 = 단계 2·4·6): 오른 단계만, 보상 화면을 닫고 전투로 돌아온 뒤
      if (up && st[t] > 0) {
        const row = String(st[t]);
        this.afterMenu(() => this.art.onPlayer(BUILD_ART.SET_FLASH, { dir: row }));
      }
      if (up && eff) this.g.ui.story('notice', `${eff.name} — ${eff.description}`);
      this.record('set', { tag: t, stage: st[t] });
    }
  }

  // --- 메뉴가 닫힌 뒤 연출 (보상 화면 → 전투 복귀) ---

  private pendingAfterMenu: (() => void)[] = [];

  /** 메뉴가 닫힌 뒤(전투 복귀) 실행 — 보상 화면 위에서 연출이 묻히지 않게 */
  afterMenu(fn: () => void): void {
    this.pendingAfterMenu.push(fn);
  }

  private flushAfterMenu(): void {
    if (this.pendingAfterMenu.length === 0 || this.g.frozen || this.g.menu.isOpen) return;
    const list = this.pendingAfterMenu;
    this.pendingAfterMenu = [];
    for (const fn of list) fn();
  }

  /** 계약 §14.1 스냅샷 */
  toUi(): UiBuildState {
    return uiBuild(this.mods, gameState.build);
  }

  /**
   * HUD 상태 (계약 §9.2) — 취기 QC-0: 카운터 '취기 n단'과 취기 태그의 취기 상태를 `drunk` 하나로. 취기 상태 타이머가 돌면
   * remainMs/durationMs 를 채운다 (§14.12 메모). 카운터 취기가 없으면 취기 상태만으로 한 줄
   */
  statuses(base: UiStatus[]): UiStatus[] {
    const t = this.drunkStatusMs();
    if (!t) return base;
    const set2 = BUILD.sets.drunk[0];
    const i = base.findIndex((st) => st.id === 'drunk');
    if (i >= 0) {
      const out = [...base];
      out[i] = { ...out[i], remainMs: t.remainMs, durationMs: t.durationMs };
      return out;
    }
    const line: UiStatus = {
      id: 'drunk',
      kind: 'buff',
      label: tagName('drunk'),
      value: `${Math.ceil(t.remainMs / 1000)}초`,
      remainMs: t.remainMs,
      durationMs: t.durationMs,
      detail: `${set2.name} — ${set2.description}`,
    };
    const at = base.findIndex((st) => st.id !== 'debt');
    return at < 0 ? [...base, line] : [...base.slice(0, at), line, ...base.slice(at)];
  }

  /** HUD 상태 '취기' (QC-0: 카운터 취기와 하나 — 카운터가 없을 때 세트 취기 상태 타이머만) */
  drunkStatusMs(): { remainMs: number; durationMs: number } | null {
    if (!this.drunkActive) return null;
    return { remainMs: Math.round(this.drunk.remainMs(this.now)), durationMs: this.drunk.durationMs };
  }

  /** 디버그 요약 (`__lopad.build()`) */
  debug(): Record<string, unknown> {
    const m = this.mods;
    return {
      scores: Object.fromEntries(TAG_IDS.filter((t) => m.scores[t] > 0).map((t) => [t, m.scores[t]])),
      stages: Object.fromEntries(TAG_IDS.filter((t) => m.stages[t] > 0).map((t) => [t, m.stages[t]])),
      stats: Object.fromEntries(Object.entries(m.stats).filter(([, v]) => v !== 0)),
      rules: m.rules.map((r) => `${r.source}:${r.id}:${r.kind}`),
      flags: m.flags,
      drunk: this.drunkActive ? Math.round(this.drunk.remainMs(this.now)) : 0,
      marks: this.marks.list().map(([mob, n]) => ({ id: mob.spriteId, marks: n })),
      dots: this.dots.list().length,
      traits: [...gameState.weapon.traits],
      curse: gameState.build.curse ? uiCurse(gameState.build.curse) : null,
      awakenFx: this.awaken.last,
      traitRules: this.traits.debug(),
      bossFloorCleared: gameState.build.bossFloorCleared,
      log: [...this.log],
      combat: this.combat.debug(),
      branch: this.branch.debug(),
      input: this.g.player?.branchMoves.debug() ?? null,
      perfect: this.perfect.debug(),
    };
  }

  destroy(): void {
    for (const [ev, fn] of this.subs) EventBus.off(ev, fn, this);
    this.subs = [];
    this.perfect.destroy();
    this.branch.destroy();
    this.traits.destroy();
    this.art.destroy();
    this.pendingAfterMenu = [];
    this.g.fx.setAliases({});
    this.combat.destroy();
    this.marks.clear();
    this.dots.clear();
  }
}
