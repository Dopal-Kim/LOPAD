import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, uiBus, uiCommands, type UiMenu } from '../contract/ui';
import { buildOf } from './buildView';
import { debugExpose, debugSelect, isDebugMenu, withDebug } from './debug';
import { GlowText } from './glow';
import { book, fontsReady, preloadKit, rule, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { resolveMenuEsc } from './escNav';
import { menuLines, wideMenu } from './menuView';
import { choiceLines, isChoiceCardMenu } from './choiceCardView';
import { menuCloseButton, showFaceDownCards, type CardPage, type CardRow } from './MenuCards';
import { showChoiceCards } from './MenuChoiceCards';
import { guideLook, guideShown, markGuideShown, showGrowthCards, showGrowthGuide } from './GrowthCards';
import { guideKind, isGrowthMenu } from './growthView';
import { r53Text, r60Text } from './text';
import { SelectList } from './widgets';
import { menuWaitMs } from './uiSequence';
import { artTex } from './paintArt';
import { ensureTrainingArt, showTrainingChoice, showTrainingMap } from './TrainingMap';
import { transitionBusy, transitionOpening } from './transitionState';

/** 카드 메뉴로 그릴 수 있는 카드 장수 (그 밖이면 일반 목록) */
const CARD_MIN = 2;
const CARD_MAX = 4;
/** 60라운드: 페이지(책 틀 안) 높이 상한 — 넘으면 설명을 접는다 (화면 540 - 틀 32 - 여백) */
const MENU_MAX_PAGE_H = UI_SCREEN.HEIGHT - 32 - 24;
/** 접은 설명 한 칸 높이 (3줄) */
const COMPACT_DETAIL_H = 3 * 16 + 6;
/** 61 단계 6: 수련장 지도에서 방을 고른 뒤 전환 시작을 기다리는 시간 · 덮일 때까지 지도를 남기는 최대 시간 (ms) */
const TRAINING_HOLD_WAIT_MS = 300;
const TRAINING_HOLD_MAX_MS = 3000;
/** 수련장 지도 그림을 시스템이 읽기를 기다리는 시간 (ms) — 그 뒤에도 없으면 UI 가 읽는다 */
const TRAINING_ART_WAIT_MS = 700;
/** Esc 머무름 안내가 떠 있는 시간 (임시값) */
const ESC_STAY_HOLD_MS = 1400;

/**
 * 보상·패시브·상점·메타·개성 3지선다(evolve)·엔딩 2지선다(ending)·47라운드 구조물 메뉴 공용 일기장 한 페이지.
 * MENU_OPEN 으로 열리고 MENU_CLOSE 로 닫힌다. 제목 page_title(Galmuri11 2배 — 한자 포함 가능) + 괘선,
 * 항목은 SelectList(page_selected/unsel, 커서), detail 은 page_faint, footer 는 page_faint 하단.
 * evolve·ending 은 페이지 최소 폭 520.
 * 47라운드(계약 §9.4): `cancelKey` 가 있으면 Esc·오른쪽 위 닫기 버튼이 `select(id, cancelKey)`.
 * 같은 메뉴(id·structureId)가 다시 오면 커서 자리를 지킨 채 다시 그린다. `cards`(패 탁자)는 엎어진 패 n장으로 그린다(MenuCards.ts).
 * 60라운드 Q38: 보상·패시브 3지선다(그만두기를 뺀 칸이 3)는 카드 3장(MenuChoiceCards.ts) — 화면을 넘으면 목록.
 * 61 단계 4 P12(§18): evolve 의 성장 칸(개성 발현·1차/2차 각성·단련)은 GrowthCards.ts — 처음이면 안내 카드 한 장 먼저.
 * 60라운드(계약 §14.4·§14.6·§14.7): 줄 만들기는 menuView.ts — 칸 종류(〔개성 발현〕·〔단련〕 …)·희귀도·태그·
 * 잠김 조건, 상점 묶음 머리글·가격·팔림. 새 메뉴 id `curse`(필수)·`event`('0')·`mapInfo`('0')·`consumableSwap`(필수)도 같은 목록.
 * 줄이 많아 페이지가 화면을 넘으면 설명을 접고 커서 줄 설명만 목록 아래에 보인다.
 */
export class MenuScene extends Phaser.Scene {
  private menu?: UiMenu;
  private list?: SelectList;
  private pendingClose = false;
  private alive = false;
  /** 카드 화면 (패 탁자·3지선다 카드)의 고르기 */
  private cardRow?: CardRow;
  /** 61 단계 4 P12: 무기 성장 처음 안내 카드를 치우는 함수 (떠 있을 때만) */
  private guideCancel?: () => void;
  private onOpen = (m: UiMenu) => {
    this.pendingClose = false;
    this.show(m);
  };
  private onClose = (p: { id: string }) => {
    // 같은 프레임에 다음 메뉴가 열릴 수 있으므로 다음 update 에서 닫는다
    if (this.menu?.id === p.id) this.pendingClose = true;
  };
  /**
   * 51라운드 §6: Esc = 한 단계 뒤로 (`resolveMenuEsc`). 앞 단계가 없는 메뉴는 머무르고 안내 한 줄.
   * cancelKey 는 지금 열린 메뉴(`this.menu` = 마지막 MENU_OPEN)의 값. 같은 Esc 이벤트가 다시 넘어오면 무시한다
   * (53라운드: 갈래 '9' 로 lab 이 다시 열린 뒤 같은 Esc 가 lab 의 '0' 으로 처리돼 메뉴 전체가 닫혔다 — keyGate.ts)
   */
  private onEsc = (e?: KeyboardEvent) => {
    const m = this.menu;
    const a = resolveMenuEsc(m, e, this.pendingClose);
    if (!m || !a) return;
    if (a.kind === 'select') this.send(m, a.key);
    else if (a.kind === 'title') uiCommands.toTitle();
    else this.flashStayHint();
  };
  /** 페이지 아래 가운데 (Esc 머무름 안내 자리) */
  private pageBottom = { x: UI_SCREEN.WIDTH / 2, y: UI_SCREEN.HEIGHT - 40 };
  private stayHint?: GlowText;

  private flashStayHint(): void {
    this.stayHint?.destroy();
    const t = new GlowText(this, 0, 0, r53Text('escStay'), 'ink_faint').setDepth(3);
    t.placeCenter(this.pageBottom.x, this.pageBottom.y + 8);
    this.stayHint = t;
    this.tweens.add({
      targets: t,
      alpha: 0,
      delay: ESC_STAY_HOLD_MS,
      duration: 300,
      onComplete: () => {
        t.destroy();
        if (this.stayHint === t) this.stayHint = undefined;
      },
    });
  }

  constructor() {
    super(UI_SCENE_KEYS.MENU);
  }

  preload(): void {
    preloadKit(this);
  }

  update(): void {
    if (this.pendingClose) {
      // 61 단계 6: 수련장 지도에서 방을 골랐으면 그림 속 입구 전환이 지도를 덮을 때까지 남긴다 (그 입구로 파고든다)
      if (this.holdForTransition()) return;
      this.pendingClose = false;
      this.scene.stop();
    }
  }

  create(data: UiMenu): void {
    this.pendingClose = false;
    this.alive = true;
    this.menu = undefined;
    this.drawn = undefined;
    setupKit(this);
    uiBus.on(UI_EVENTS.MENU_OPEN, this.onOpen);
    uiBus.on(UI_EVENTS.MENU_CLOSE, this.onClose);
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.events.once('shutdown', () => {
      this.alive = false;
      uiBus.off(UI_EVENTS.MENU_OPEN, this.onOpen);
      uiBus.off(UI_EVENTS.MENU_CLOSE, this.onClose);
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.clearCards();
      this.list?.destroy();
      this.list = undefined;
    });
    const first = data;
    // 61라운드 플레이 점검 #11: 성과 도장 카드가 떠 있으면 그것이 끝난 뒤에 (uiSequence.ts — 최대 1.2초)
    // 61 단계 3: 보스 처치 카드도 (처치에서 최대 4.5초, 보스 대사가 이어지면 늘임)
    const wait = menuWaitMs();
    debugExpose('menuWait', { id: first?.id, wait });
    fontsReady().then(() => {
      const go = (): void => {
        if (this.alive && (this.menu ?? first)) {
          debugExpose('menuShown', { id: (this.menu ?? first).id, at: Math.round(performance.now()) });
          this.show(this.menu ?? first);
        }
      };
      if (wait > 0) this.time.delayedCall(wait, go);
      else go();
    });
    this.menu = first;
  }

  /** 61 단계 6: 수련장 지도에서 방을 보낸 시각 (같은 지도에서 두 번 보내지 않게, 전환이 덮을 때까지 지도를 남기게) */
  private trainingSentAt = 0;

  private holdForTransition(): boolean {
    if (this.drawn?.id !== 'training' || !this.trainingSentAt) return false;
    const since = this.time.now - this.trainingSentAt;
    if (since < TRAINING_HOLD_WAIT_MS && !transitionBusy()) return true;
    return transitionOpening() && since < TRAINING_HOLD_MAX_MS;
  }

  /** 선택 전달 (UI 디버그 가짜 메뉴는 시스템으로 보내지 않는다) */
  private send(m: UiMenu, key: string): void {
    if (m.id === 'training' && key !== m.cancelKey) {
      if (this.trainingSentAt && this.time.now - this.trainingSentAt < TRAINING_HOLD_MAX_MS) return;
      this.trainingSentAt = this.time.now;
    }
    if (isDebugMenu(m)) debugSelect(m, key);
    else uiCommands.select(m.id, key);
  }

  private show(m: UiMenu): void {
    const prev = this.drawn;
    const same = Boolean(prev) && prev!.id === m.id && (prev!.structureId ?? '') === (m.structureId ?? '');
    // 61 단계 4: 처음 안내가 떠 있는 동안 같은 메뉴가 다시 오면(시스템이 다시 띄움·MENU_OPEN 재전송) 안내를 지킨다
    if (same && this.guideCancel && isGrowthMenu(m)) {
      this.menu = m;
      this.drawn = m;
      return;
    }
    const keepCursor = same ? (this.list?.cursorIndex() ?? this.cardRow?.focusIndex() ?? 0) : 0;
    this.menu = m;
    this.drawn = m;
    this.trainingSentAt = 0;
    this.stayHint = undefined;
    this.children.removeAll(true);
    this.list?.destroy();
    this.list = undefined;
    this.clearCards();
    const cardLines = choiceLines(m);
    const snap = withDebug(uiCommands.getUiSnapshot());
    const ctx = { stageIndex: Math.max(0, snap.stageIndex), keepCursor, send: (key: string) => this.send(m, key) };
    let page: CardPage | null = null;
    if (isGrowthMenu(m)) {
      // 61 단계 4 P12: 무기 성장 카드 — 메타 기준 처음이면 안내 카드 한 장 뒤에
      const gk = guideKind(m, snap.growth);
      debugExpose('growthMenu', {
        guide: gk,
        firstTime: snap.growth?.firstTime ?? null,
        shown: gk ? guideShown(gk) : null,
      });
      if (gk && !guideShown(gk)) {
        // 본 것으로 치는 것은 닫았을 때 (씬이 다시 떠도 아직 안 닫았으면 다시 띄운다)
        this.guideCancel = showGrowthGuide(this, gk, guideLook(gk, snap), () => {
          markGuideShown(gk);
          this.guideCancel = undefined;
          if (this.alive && this.drawn) this.show(this.drawn);
        });
        return;
      }
      page = showGrowthCards(this, m, snap, ctx, MENU_MAX_PAGE_H);
      debugExpose('growthCards', { id: m.id, drawn: Boolean(page) });
      if (!page) this.children.removeAll(true);
    } else if (m.id === 'training') {
      // 61 단계 6 P14: 수련장 지도 두루마리 (TrainingMap.ts)
      page = showTrainingMap(this, m, snap, ctx);
      if (!page) this.children.removeAll(true);
      // 그림 지도가 아직 안 읽혔으면 읽은 뒤 같은 메뉴를 다시 그린다 (그동안은 코드 두루마리)
      // (시스템이 막 읽는 중일 수 있어 조금 기다렸다가 그래도 없을 때만 UI 사본으로)
      const key = snap.training?.mapKey || 'paint/map_training';
      const drewArt = Boolean(artTex(this, key));
      this.time.delayedCall(TRAINING_ART_WAIT_MS, () => {
        if (!this.alive || this.drawn !== m) return;
        const started = ensureTrainingArt(this, key, (ok) => {
          if (ok && this.alive && this.drawn === m) this.show(m);
        });
        // 그 사이 시스템이 읽었으면 그림으로 다시 그린다
        if (!started && !drewArt) this.show(m);
      });
    } else if (m.id === 'trainingChoice') {
      page = showTrainingChoice(this, m, ctx);
      if (!page) this.children.removeAll(true);
    } else if (m.id === 'cards' && cardLines.length >= CARD_MIN && cardLines.length <= CARD_MAX) {
      page = showFaceDownCards(this, m, cardLines, ctx);
    } else if (isChoiceCardMenu(m)) {
      page = showChoiceCards(this, m, buildOf(snap), ctx, MENU_MAX_PAGE_H);
      // 카드가 화면에 들지 않으면 목록으로 (그리다 만 것은 지운다)
      if (!page) this.children.removeAll(true);
    }
    if (page) {
      this.cardRow = page.row;
      this.pageBottom = page.bottom;
    } else this.showList(m, keepCursor);
  }
  /** 지금 화면에 그린 메뉴 (show 전에 this.menu 는 create 데이터일 수 있어 따로 둔다) */
  private drawn?: UiMenu;

  private showList(m: UiMenu, keepCursor: number): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const snap = withDebug(uiCommands.getUiSnapshot());
    const stageIndex = Math.max(0, snap.stageIndex);
    // 줄 만들기(evolve 설명 중복 제거·시험장 들여쓰기·§14.4 칸 종류·잠김·§14.6 가격·팔림·묶음 머리글)는 menuView.ts
    const lines = menuLines(m, buildOf(snap), r60Text);
    const wide = wideMenu(m);
    const minW = wide ? 520 : 420;
    const maxW = W - 64;
    const padX = 24;
    // 항목·제목·푸터를 먼저 그려 폭을 재고, 페이지는 그 뒤에 깔아(depth 0) 글이 잘리지 않게 한다
    this.list = new SelectList(this, 0, 0, (key) => this.send(m, key), {
      stageIndex,
      detailWrap: maxW - padX * 2 - 40,
    });
    this.list.setLines(lines);
    this.list.setCursorIndex(keepCursor);
    const title = new GlowText(this, 0, 0, m.title, 'page_title', { scale: 2, stageIndex }).setDepth(1);
    const footer = m.footer
      ? new GlowText(this, 0, 0, m.footer, 'page_faint', { wrap: maxW - padX * 2, align: 'center' }).setDepth(1)
      : null;
    const close = m.cancelKey ? menuCloseButton(this, stageIndex, () => this.send(m, m.cancelKey!)) : null;
    const closeRoom = close ? (close.width + 8) * 2 : 0;
    const contentW = Math.max(this.list.maxWidth() + 8, title.displayWidth + closeRoom, footer?.displayWidth ?? 0);
    const pageW = Math.min(maxW, Math.max(minW, contentW + padX * 2));
    const titleH = title.displayHeight;
    const footerH = footer ? footer.displayHeight + 10 : 0;
    let listH = this.list.height();
    // 60라운드 §14.6: 상점처럼 줄이 많아 페이지가 화면을 넘으면 설명을 접고, 커서 줄의 설명만 목록 아래 한 칸에 보인다
    let focusDetail: GlowText | null = null;
    let focusH = 0;
    const baseH = 16 + titleH + 8 + 4 + 14 + 10 + footerH + 16;
    if (baseH + listH > MENU_MAX_PAGE_H && lines.some((l) => l.detail)) {
      this.list.setLines(lines.map((l) => ({ ...l, detail: undefined })));
      this.list.setCursorIndex(keepCursor);
      listH = this.list.height();
      focusDetail = new GlowText(this, 0, 0, '', 'page_faint', { wrap: maxW - padX * 2 - 16 }).setDepth(1);
      focusH = COMPACT_DETAIL_H;
    }
    const pageH = baseH + listH + focusH;
    const bk = book(this, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
    const pg = bk.pages[0];
    let y = pg.y + 16;
    title.placeCenter(pg.x + pageW / 2, y);
    close?.setPosition(pg.x + pageW - 12 - close.width, pg.y + 12);
    y += titleH + 8;
    rule(this, pg.x + padX, y, pageW - padX * 2).setDepth(1);
    y += 4 + 14;
    this.list.setPosition(pg.x + padX, y).setDepth(1);
    y += listH + 10;
    if (focusDetail) {
      const fd = focusDetail;
      fd.setPosition(pg.x + padX + 16, y - 4);
      this.list.setOnCursor((i) => fd.setText(lines[i]?.detail ?? ''));
      y += focusH;
    }
    footer?.placeCenter(pg.x + pageW / 2, y);
    this.pageBottom = { x: pg.x + pageW / 2, y: pg.y + pageH };
    if (m.id === 'meta') this.input.keyboard?.once('keydown-ENTER', () => uiCommands.select('meta', 'enter'));
  }

  private clearCards(): void {
    this.guideCancel?.();
    this.guideCancel = undefined;
    this.cardRow?.destroy();
    this.cardRow = undefined;
  }
}
