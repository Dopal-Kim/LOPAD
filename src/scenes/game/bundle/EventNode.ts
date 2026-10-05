/**
 * 60라운드 2차 묶음 — 이벤트 노드(c) · 숨은 노드(d) · 단서 · 지도 장수 (data/bundle2.json):
 * - 이벤트 노드: 층 생성 때 고른 내용(E1~E9). 소품이 있으면 가까이 가면, 없으면 진입 직후 메뉴 'event' (마지막 줄 '0' 지나간다).
 *   진입 시 EVENT_NODE_ENTERED · 런 안 사용 기록.
 * - 숨은 노드: 보물(전표 + 희귀 이상 2택) · 행상(E1) · 술잔(E8).
 * - 단서: 숨은 노드의 갈라지는 전투 노드에서 시련이 끝나면 단서 소품 → 살펴보면 숨은 길 (HIDDEN_NODE_FOUND).
 * - 지도 장수: 국경 초소(post) 노드에 소품 → 메뉴 'mapInfo' (지도 정보 3품목).
 */
import Phaser from 'phaser';
import { BUNDLE_FX, TILE } from '../../../core/Constants';
import { EventBus, Events } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { ECONOMY, STORY } from '../../../data';
import { BUNDLE2, consumableDef, eventDef, eventIntro } from '../../../data/bundle2';
import { onFloor } from '../../../data/floorScope';
import { optionLabel } from '../../../systems/bundle2/eventText';
import { bossKilledBefore, diaryNow, diaryReadLine, hasPastLife } from '../../../systems/narrative/diary';
import type { ConsumableId, EventDef, EventOption, MapInfoId } from '../../../data/bundle2Types';
import { UI_EVENTS, __system, type UiHiddenNodeFound, type UiMenuLine } from '../../../contract/ui';
import { curseDef } from '../../../data/build';
import { revealHidden } from '../../../systems/bundle2/routeExtras';
import { goldCost, shopPrice } from '../../../systems/economy';
import { StructureView } from '../../../world/StructureView';
import type { Game } from '../../Game';
import type { BundleProps } from './BundleProps';
import type { NodeFlow } from './NodeFlow';
import type { ShopMenu } from './ShopMenu';
import { chain, effectSteps, randomConsumable } from './bundleRewards';

const PASS = '0';
const EVENT_PROP = 'bundle:event';
const CLUE_PROP = 'bundle:clue';
const SELLER_PROP = 'bundle:seller';

interface Cask {
  view: StructureView;
  x: number;
  y: number;
  broken: boolean;
}

export class EventNode {
  private readonly def: EventDef | null;
  private done = false;
  /** E1 행상 진열 (이 노드 안) */
  private stock: { kind: 'consumable' | 'potion'; id: string; price: number; sold: boolean }[] = [];
  /** E6 술독 깨기 */
  private casks: Cask[] = [];
  private caskUntil = 0;
  private caskTimer: Phaser.Time.TimerEvent | null = null;

  constructor(
    private readonly g: Game,
    private readonly props: BundleProps,
    private readonly flow: NodeFlow,
    private readonly shop: ShopMenu,
  ) {
    const id = flow.extra?.eventId ?? null;
    this.def = id ? (eventDef(id) ?? null) : null;
  }

  private get hiddenContent() {
    return this.flow.extra?.hiddenContent ?? null;
  }

  private at(off: { x: number; y: number }): { x: number; y: number } {
    const c = this.flow.center();
    return { x: c.x + off.x * TILE, y: c.y + off.y * TILE };
  }

  /** 노드 진입 직후 */
  onEnter(enterLockUntil: number): void {
    const g = this.g;
    const node = g.node;
    if (!node) return;
    const after = (fn: () => void) =>
      g.time.delayedCall(Math.max(0, enterLockUntil - g.time.now) + BUNDLE_FX.MENU_AFTER_ENTER_MS, () => {
        if (g.scene.isActive()) fn();
      });
    // 61라운드 P5: 지도 정보는 1층에서 끔 (국경 초소 탁자에는 서사 소품 성문 출입 장부 — StoryBeats)
    if (BUNDLE2.mapInfo.sellerKinds.includes(node.kind) && onFloor(BUNDLE2.mapInfo, gameState.build.floor))
      this.placeSeller();
    if (this.hiddenContent === 'treasure') return void after(() => this.treasure());
    const def = this.def;
    if (!def) return;
    if (!this.hiddenContent) {
      gameState.bundle.useEvent(def.id);
      EventBus.emit(Events.EVENT_NODE_ENTERED, { id: def.id });
    }
    if (def.prop) {
      const p = this.at(BUNDLE_FX.EVENT_OFFSET);
      // 60라운드 Q32: 이벤트 소품은 E 로 조사 (UI 계약 §14.10 eventProp)
      this.props.add({
        id: EVENT_PROP,
        sheet: def.prop,
        label: def.name,
        x: p.x,
        y: p.y,
        interact: {
          kind: 'eventProp',
          name: def.name,
          action: BUNDLE_FX.EVENT_ACTION,
          actionKey: 'eventProp.inspect',
          usable: () => true,
          use: () => this.open(),
        },
      });
    } else after(() => this.open());
  }

  /** 시련 끝 (전투 노드): 단서 소품 */
  onTrialCleared(): void {
    const h = gameState.bundle.floor?.hidden;
    if (!h || h.state === 'found' || h.sourceId !== this.g.node?.id) return;
    const p = this.at(BUNDLE_FX.CLUE_OFFSET);
    this.props.add({
      id: CLUE_PROP,
      sheet: h.clue,
      label: BUNDLE2.hidden.name,
      x: p.x,
      y: p.y,
      state: 'idle',
      // 60라운드 Q32: 단서는 E 로 살펴보기 (UI 계약 §14.10 clue) — 길을 연 뒤에는 쓸 수 없다
      interact: {
        kind: 'clue',
        name: BUNDLE2.hidden.name,
        action: BUNDLE_FX.CLUE_LABEL,
        actionKey: 'clue.inspect',
        usable: () => gameState.bundle.floor?.hidden?.state !== 'found',
        use: () => this.openClue(),
      },
    });
  }

  private openClue(): void {
    const g = this.g;
    g.menu.open(
      'event',
      BUNDLE2.hidden.name,
      [
        { key: '1', label: BUNDLE_FX.CLUE_LABEL, enabled: true },
        { key: PASS, label: BUNDLE2.events.passLabel, enabled: true },
      ],
      (key) => {
        g.menu.close();
        if (key !== '1') return;
        const ex = gameState.bundle.floor;
        const route = gameState.route;
        if (!ex || !route || !revealHidden(route.graph, ex)) return;
        this.props.setState(CLUE_PROP, 'found');
        EventBus.emit(Events.HIDDEN_NODE_FOUND, { nodeId: ex.hidden!.nodeId });
        __system.emit(UI_EVENTS.HIDDEN_NODE_FOUND, { nodeId: ex.hidden!.nodeId } satisfies UiHiddenNodeFound);
      },
      BUNDLE_FX.CLUE_TEXT,
      { cancelKey: PASS },
    );
  }

  // --- 지도 장수 ---

  private placeSeller(): void {
    const p = this.at(BUNDLE_FX.SELLER_OFFSET);
    this.props.add({
      id: SELLER_PROP,
      sheet: null,
      label: BUNDLE2.mapInfo.sellerName,
      x: p.x,
      y: p.y,
      // 60라운드 Q32: 지도 장수는 E 로 말 걸기 (UI 계약 §14.10 mapSeller)
      interact: {
        kind: 'mapSeller',
        name: BUNDLE2.mapInfo.sellerName,
        action: BUNDLE_FX.SELLER_ACTION,
        actionKey: 'mapSeller.talk',
        usable: () => true,
        use: () => this.openSeller(),
      },
    });
  }

  private openSeller(): void {
    const g = this.g;
    const render = () => {
      const lines: UiMenuLine[] = [
        ...this.shop.mapInfoLines(''),
        { key: PASS, label: BUNDLE2.events.passLabel, enabled: true },
      ];
      g.menu.open(
        'mapInfo',
        `${BUNDLE2.mapInfo.sellerName}  (${STORY.names.gold} ${gameState.gold})`,
        lines,
        (key) => {
          if (key === PASS) return g.menu.close();
          if (this.shop.buyMapInfo(key as MapInfoId)) render();
        },
        '',
        { cancelKey: PASS },
      );
    };
    render();
  }

  // --- 이벤트 메뉴 ---

  private open(): void {
    const def = this.def;
    if (!def || this.done) return;
    if (def.kind === 'merchant') return this.openMerchant(def);
    if (def.kind === 'curse') return this.openCurseEvent(def);
    if (def.kind === 'challenge') return this.openChallenge(def);
    if (def.kind === 'ambush') return this.openAmbush(def);
    if (def.holdMs) return this.openPray(def);
    this.openOptions(def);
  }

  /** 이벤트 메뉴 (마지막 줄 '0' = 지나간다 — 61라운드: pass 선택지가 있으면 그 문구, 고르면 결과 문장과 함께 끝) */
  private menu(
    def: EventDef,
    lines: UiMenuLine[],
    onPick: (key: string) => void,
    footer = eventIntro(def),
    pass?: EventOption,
  ): void {
    const g = this.g;
    g.menu.open(
      'event',
      def.name,
      [...lines, { key: PASS, label: pass?.label ?? BUNDLE2.events.passLabel, enabled: true }],
      (key) => {
        if (key !== PASS) return onPick(key);
        g.menu.close();
        if (!pass) return;
        this.finish();
        g.ui.story('event', pass.result ?? '');
      },
      footer,
      { cancelKey: PASS },
    );
  }

  private finish(state?: string): void {
    this.done = true;
    if (state) this.props.setState(EVENT_PROP, state);
  }

  /** 고를 수 있나 (독주가 필요한 선택지 · 저주를 주는 선택지는 저주가 없을 때만) */
  private optionOk(o: EventOption): boolean {
    if (o.needPotion && gameState.potions <= 0) return false;
    if (o.effects.some((e) => e.kind === 'curse') && gameState.build.curse !== null) return false;
    return true;
  }

  private optionLine(o: EventOption): UiMenuLine {
    return { key: o.key, label: optionLabel(o), enabled: this.optionOk(o) };
  }

  /** 선택지형 (61라운드 1층 5종: E3·E4·E5·E8·E9) — 고르면 결과 문장(STORY event) → 효과 */
  private openOptions(def: EventDef): void {
    const intro = eventIntro(def);
    // E4: 다음 갈래 미리보기 (이 층 런에서 고를 수 있는 단까지만)
    const tree = def.showTree
      ? this.g.buildMenus
          .runOptions()
          .map((n) => n.name)
          .join(' · ')
      : '';
    const opts = def.options ?? [];
    this.menu(
      def,
      opts.filter((o) => !o.pass).map((o) => this.optionLine(o)),
      (key) => {
        const o = opts.find((x) => x.key === key && !x.pass);
        if (o && this.optionOk(o)) this.pick(def, o);
      },
      tree ? `${intro}\n${tree}` : intro,
      opts.find((o) => o.pass),
    );
  }

  /** 선택지 고름: 소품 상태 → (기도 holdMs) → 결과 문장 → 효과 차례대로 */
  private pick(def: EventDef, o: EventOption): void {
    const g = this.g;
    g.menu.close();
    if (o.propState === 'remove') {
      this.done = true;
      this.props.remove(EVENT_PROP);
    } else this.finish(o.propState ?? 'used');
    const lore = o.effects.some((e) => e.kind === 'diaryRead') ? this.diaryLine(def) : (def.lore ?? '');
    const run = () => {
      if (o.afterState) this.props.setState(EVENT_PROP, o.afterState);
      g.ui.story('event', o.result ?? '');
      chain(effectSteps(g, o.effects, lore));
    };
    if (o.holdMs) g.time.delayedCall(o.holdMs, () => g.scene.isActive() && run());
    else run();
  }

  /** E4 지난 생의 기록: 만취를 쓰러뜨린 생 → 지난 생 한 줄 → 첫 생 */
  private diaryLine(def: EventDef): string {
    const t = def.diaryRead;
    if (!t) return '';
    const d = diaryNow();
    const stage = gameState.stageId;
    return diaryReadLine(
      t,
      {
        bossKilledBefore: bossKilledBefore(d, stage, gameState.narrative.bossKilled.has(stage)),
        hasPastLife: hasPastLife(d),
      },
      this.g.rng.next(),
    );
  }

  /** E8: 손을 모은다(holdMs) → 선택지 */
  private openPray(def: EventDef): void {
    this.menu(def, [{ key: '1', label: BUNDLE_FX.PRAY_LABEL, enabled: true }], () => {
      this.g.menu.close();
      this.props.setState(EVENT_PROP, 'pray');
      this.g.time.delayedCall(def.holdMs ?? 0, () => {
        if (this.g.scene.isActive()) this.openOptions(def);
      });
    });
  }

  /** E2: 미리 보이는 저주 하나를 마신다 */
  private openCurseEvent(def: EventDef): void {
    const busy = gameState.build.curse !== null;
    const lines = (def.curses ?? []).map((id, i) => {
      const c = curseDef(id);
      return {
        key: String(i + 1),
        kind: 'curse' as const,
        label: c?.name ?? id,
        enabled: !busy && Boolean(c),
        detail: c ? `${c.benefit} / ${c.penalty}` : '',
      };
    });
    this.menu(def, lines, (key) => {
      const id = def.curses?.[Number(key) - 1];
      if (!id || busy) return;
      this.g.menu.close();
      this.finish('used');
      this.g.build.grantCurse(id, { source: 'event' });
    });
  }

  /** E1 · 숨은 행상: 소모품 2 + 독주 1 (할인) */
  private openMerchant(def: EventDef): void {
    const g = this.g;
    if (this.stock.length === 0) {
      const d = 1 - (def.discount ?? 0);
      for (let i = 0; i < (def.stock?.consumable ?? 0); i++) {
        const id = randomConsumable(g);
        this.stock.push({
          kind: 'consumable',
          id,
          price: Math.round((consumableDef(id)?.price ?? 0) * d),
          sold: false,
        });
      }
      const potion = ECONOMY.shop.items.find((it) => it.id === 'potion');
      for (let i = 0; i < (def.stock?.potion ?? 0) && potion; i++)
        this.stock.push({
          kind: 'potion',
          id: 'potion',
          price: Math.round(shopPrice(potion, gameState.stageIndex) * d),
          sold: false,
        });
    }
    const render = () => {
      const lines = this.stock.map((s, i) => {
        const name = s.kind === 'potion' ? STORY.names.potion : (consumableDef(s.id)?.name ?? s.id);
        const full = s.kind === 'potion' && gameState.potions >= g.economy.potionCarry;
        return {
          key: String(i + 1),
          label: s.sold ? `${name}  ${String(BUNDLE2.shop.labels.soldOut)}` : name,
          enabled: !s.sold && !full && gameState.gold >= s.price,
          price: goldCost(s.price, gameState.gold, STORY.names.gold),
          group: 'display' as const,
          soldOut: s.sold,
        };
      });
      this.menu(def, lines, (key) => {
        const s = this.stock[Number(key) - 1];
        if (!s || s.sold || gameState.gold < s.price) return;
        g.economy.spendGold(s.price);
        EventBus.emit(Events.SHOP_BOUGHT, { id: s.id, price: s.price, group: 'display' });
        s.sold = true;
        if (s.kind === 'potion') {
          gameState.potions = Math.min(g.economy.potionCarry, gameState.potions + 1);
          EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
          render();
        } else {
          g.menu.close();
          g.bundle?.consumables.gain(s.id as ConsumableId);
        }
      });
    };
    render();
  }

  /** E7: 부수면 매복 → 전멸하면 저장고 보상 */
  private openAmbush(def: EventDef): void {
    this.menu(def, [{ key: '1', label: '부순다', enabled: !this.g.director.inCombat }], () => {
      const g = this.g;
      const room = g.layout?.rooms[0];
      if (!room) return;
      const spawns = (def.ambush ?? []).map((a) => ({ enemy: a.enemy, count: a.count, hpMult: 1, attackMult: 1 }));
      const p = this.at(BUNDLE_FX.EVENT_OFFSET);
      const ok = g.director.startChallenge(
        room.id,
        spawns,
        () => {
          this.props.setState(EVENT_PROP, 'used');
          chain(effectSteps(g, def.reward));
        },
        { x: p.x, y: p.y, radiusTiles: 4 },
      );
      if (!ok) return;
      g.menu.close();
      this.finish('open');
    });
  }

  /** E6: 술통 n개를 제한 시간 안에 (공격 지점 근처 술통이 깨진다) */
  private openChallenge(def: EventDef): void {
    const C = def.challenge!;
    this.menu(def, [{ key: '1', label: BUNDLE_FX.CASK_GOAL.replace('{n}', String(C.casks)), enabled: true }], () => {
      const g = this.g;
      g.menu.close();
      this.finish();
      const c = this.flow.center();
      for (let i = 0; i < C.casks; i++) {
        let pt = { x: c.x, y: c.y };
        for (let t = 0; t < 20; t++) {
          const a = g.rng.next() * Math.PI * 2;
          const r = (0.3 + g.rng.next() * 0.7) * C.radiusTiles * TILE;
          const q = { x: c.x + Math.cos(a) * r, y: c.y + Math.sin(a) * r };
          if (g.world.isWalkableAt(q.x, q.y)) {
            pt = q;
            break;
          }
        }
        const view = new StructureView(g, {
          sheet: BUNDLE_FX.CASK_SHEET,
          rect: new Phaser.Geom.Rectangle(pt.x - TILE / 2, pt.y - TILE, TILE, TILE),
          color: BUNDLE_FX.PROP_COLOR,
          label: '',
          floor: false,
        });
        this.casks.push({ view, x: pt.x, y: pt.y, broken: false });
      }
      this.caskUntil = g.time.now + C.ms;
      this.caskTimer = g.time.delayedCall(C.ms, () => this.endCasks(false));
      EventBus.on(Events.PLAYER_ATTACKED, this.onAttack, this);
    });
  }

  private onAttack(p: { x: number; y: number }): void {
    if (this.casks.length === 0 || this.g.time.now > this.caskUntil) return;
    const pl = this.g.player;
    const r = BUNDLE_FX.CASK_HIT_TILES * TILE;
    for (const c of this.casks) {
      if (c.broken) continue;
      if (Math.hypot(c.x - p.x, c.y - p.y) > r && Math.hypot(c.x - pl.x, c.y - pl.y) > r) continue;
      c.broken = true;
      if (c.view.hasState('broken')) c.view.setState('broken');
      else c.view.destroy();
    }
    if (this.casks.every((c) => c.broken)) this.endCasks(true);
  }

  private endCasks(success: boolean): void {
    EventBus.off(Events.PLAYER_ATTACKED, this.onAttack, this);
    this.caskTimer?.remove();
    this.caskTimer = null;
    if (this.casks.length === 0) return;
    for (const c of this.casks) if (!c.broken) c.view.destroy();
    this.casks = [];
    if (success && this.def) chain(effectSteps(this.g, this.def.success));
    else this.g.ui.story('notice', BUNDLE_FX.CASK_FAIL_TEXT);
  }

  /** 숨은 보물: 전표 + 희귀 이상 2택 */
  private treasure(): void {
    if (this.done) return;
    this.done = true;
    const T = BUNDLE2.hidden.treasure;
    chain([
      (next) => {
        this.g.economy.addGold(T.gold);
        next();
      },
      (next) =>
        void this.g.buildMenus.openPassiveMenu(
          'node',
          { choices: T.passive.choices, rarities: T.passive.rarities },
          next,
        ),
    ]);
  }

  debug(): Record<string, unknown> {
    return {
      event: this.def?.id ?? null,
      hidden: this.hiddenContent,
      done: this.done,
      casks: this.casks.filter((c) => !c.broken).length,
    };
  }

  destroy(): void {
    EventBus.off(Events.PLAYER_ATTACKED, this.onAttack, this);
    this.caskTimer?.remove();
    for (const c of this.casks) c.view.destroy();
    this.casks = [];
  }
}
