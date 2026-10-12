import Phaser from 'phaser';
import { UI_SCREEN, uiCommands } from '../contract/ui';
import { debugExpose, setMutedCmd, withDebug } from './debug';
import { fullscreenSupported, isFullscreen, onFullscreenChange, requestFullscreen } from './fullscreen';
import { GlowText } from './glow';
import { DEFAULT_KEYS, assignKey, codeToKeyName, keyLabel, type KeyActionId } from './keyBindView';
import { takeKey } from './keyGate';
import { accentHex, book, cursor as makeCursor, inkPanel, rule } from './kit';
import { commitSettings, currentSettings, defaultSettings } from './settingsStore';
import {
  ARROW_L,
  ARROW_R,
  PCT_X,
  TRACK_W,
  TRACK_X,
  buildRows,
  drawRows,
  rowLabel,
  rowsHeight,
  tabLabel,
  type RowState,
  type RowView,
} from './SettingsRows';
import {
  END_ROWS,
  SETTINGS_TABS,
  changeSetting,
  cycleTab,
  moveCursor,
  rowsFor,
  sameSettings,
  setKeys,
  setSlider,
  sliderFromRatio,
  toggleSetting,
  type SettingRow,
  type SettingsTab,
  type SettingsValues,
} from './settingsView';
import { fill, r61Text, r62Text } from './text';
import { GRAY, ROUTE, SEPIA, hexToNum } from './theme';
import { SETTINGS_UI as U } from './themeR61';
import { setTextSize, systemTextScale, textSize } from './uiPrefs';
import { playUiSound } from './uiSound';

export interface SettingsPanelOptions {
  stageIndex: number;
  /** 덮었을 때 (Esc·'덮는다') — 부른 화면이 목록 입력을 다시 켠다 */
  onClose: () => void;
  /** 처음 열 탭 (기본 화면) */
  tab?: SettingsTab;
}

interface TabView {
  tab: SettingsTab;
  box: Phaser.GameObjects.Container;
  g: Phaser.GameObjects.Graphics;
  t: GlowText;
  x: number;
  w: number;
}

/**
 * 설정 화면 (계약 §15) — 일시정지 일기장의 '설정' 항목, 타이틀의 '설정' 에서 연다. 일기장 한 쪽(책 틀 + 종이).
 * 62 루프 2 (P1-16): 위 탭 넷 — 화면(전체화면 F11 · 피해 숫자) / 소리(전체 · 배경음 · 효과음 · 소리 끄기) /
 * 조작(이동 넷 · 대쉬 · 상호작용 · 물약 키 재설정 · 기본 키로) / 접근성(글자 크기 보통·크게 · 화면 흔들림 · 섬광 · 화면 기울기 · 타격 멈춤),
 * 아래 공통 '처음 값으로 되돌린다 · 덮는다'. 값이 바뀌는 즉시 `setSettings`(settingsStore) — 전체화면은 브라우저, 소리 끄기는 `setMuted`,
 * 글자 크기는 UI 보기 설정(uiPrefs).
 * 조작: 탭 줄에서 ←→ 탭 바꾸기 · ↑↓(W·S) 고르기 · ←→(A·D) 바꾸기 · Enter·스페이스 켜고 끄기·실행·키 기다리기 · 마우스.
 * 키 줄: Enter·클릭 → '쓸 키를 누른다' 상자 → 다음 키(자판 자리 `code`)를 그 동작에 — 다른 동작이 쓰던 키면 맞바꾼다.
 * 바꿀 수 없는 키(Esc·Tab·M·Enter·F11·Shift·R·C)는 한 줄 알림. Esc 는 부른 화면이 받아 `back()` 한다(기다림 그만두기 → 덮기).
 */
export class SettingsPanel {
  private box: Phaser.GameObjects.Container;
  private content: Phaser.GameObjects.Container;
  private rowsBox: Phaser.GameObjects.Container;
  private g: Phaser.GameObjects.Graphics;
  private cursorSprite: Phaser.GameObjects.Sprite;
  private tabs: TabView[] = [];
  private rows: RowView[] = [];
  private tab: SettingsTab;
  private values: SettingsValues;
  private muted: boolean;
  private potionName: string;
  /** 0 = 탭 줄, 1.. = 줄 */
  private cursorIdx = 1;
  private dragRow: number | null = null;
  private waiting: KeyActionId | null = null;
  private waitBox?: Phaser.GameObjects.Container;
  private notice: GlowText;
  private noticeText = '';
  private noticeTimer?: Phaser.Time.TimerEvent;
  private preview?: GlowText;
  private blinkTimer: Phaser.Time.TimerEvent;
  private blink = true;
  private offFs: () => void;
  private closed = false;
  private si: number;
  private rowsY = 0;
  /** 끝줄 앞 괘선 자리 (가장 긴 탭 기준 — 탭마다 같은 자리) */
  private endTop = 0;
  private noticeY = 0;

  constructor(
    private scene: Phaser.Scene,
    private opts: SettingsPanelOptions,
  ) {
    this.si = opts.stageIndex;
    this.tab = opts.tab ?? 'screen';
    this.values = currentSettings();
    const snap = withDebug(uiCommands.getUiSnapshot());
    this.muted = Boolean(snap.muted);
    this.potionName = snap.names?.potion ?? '';
    const block = scene.add
      .rectangle(0, 0, UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT, hexToNum(GRAY[0]), ROUTE.dimAlpha)
      .setOrigin(0)
      .setInteractive();
    this.content = scene.add.container(0, 0);
    this.g = scene.add.graphics();
    this.rowsBox = scene.add.container(0, 0);
    this.content.add([this.g, this.rowsBox]);
    this.notice = new GlowText(scene, U.pad, 0, '', 'page_faint', { wrap: U.pageW - U.pad * 2 });
    const pageH = this.buildFrame();
    this.cursorSprite = makeCursor(scene, false);
    this.content.add(this.cursorSprite);
    const before = new Set(scene.children.list);
    const bk = book(
      scene,
      Math.round(UI_SCREEN.WIDTH / 2),
      Math.round(UI_SCREEN.HEIGHT / 2),
      U.pageW,
      pageH,
      1,
      'settings',
    );
    const paper = scene.children.list.filter((o) => !before.has(o));
    this.content.setPosition(bk.pages[0].x, bk.pages[0].y);
    this.box = scene.add.container(0, 0, [block, ...paper, this.content]).setDepth(U.depth);
    this.buildTabRows();
    scene.input.keyboard?.on('keydown', this.onKey);
    scene.input.on('pointermove', this.onMove);
    scene.input.on('pointerup', this.onUp);
    this.blinkTimer = scene.time.addEvent({
      delay: 420,
      loop: true,
      callback: () => {
        this.blink = !this.blink;
        if (this.waiting) this.refresh();
      },
    });
    this.offFs = onFullscreenChange(() => this.refresh());
    this.refresh();
  }

  /** Esc (부른 화면이 받아 넘긴다): 키 기다리는 중이면 그만두기만, 아니면 덮는다. 덮었으면 true */
  back(): boolean {
    if (this.closed) return true;
    if (this.waiting) {
      this.stopWaiting();
      playUiSound(this.scene, 'back');
      return false;
    }
    this.close();
    return true;
  }

  /** 덮기 (Esc·'덮는다'). 두 번 불러도 한 번만 */
  close(): void {
    if (this.closed) return;
    playUiSound(this.scene, 'back');
    this.destroy();
    this.opts.onClose();
  }

  destroy(): void {
    if (this.closed) return;
    this.closed = true;
    this.scene.input.keyboard?.off('keydown', this.onKey);
    this.scene.input.off('pointermove', this.onMove);
    this.scene.input.off('pointerup', this.onUp);
    this.blinkTimer.remove();
    this.noticeTimer?.remove();
    this.offFs();
    this.box.destroy();
    debugExpose('settings', { open: false });
  }

  // ---- 만들기

  /** 제목·괘선·탭 줄·알림·안내 (탭 줄 아래는 `buildTabRows`). 쪽 높이를 돌려준다 (탭마다 같은 높이) */
  private buildFrame(): number {
    const sc = this.scene;
    const x0 = U.pad;
    const innerW = U.pageW - U.pad * 2;
    let y = U.top;
    const title = new GlowText(sc, 0, y, r61Text('settingsTitle'), 'page_title', {
      font: 'title',
      stageIndex: this.si,
    });
    title.placeCenter(U.pageW / 2, y);
    this.content.add(title);
    y += title.displayHeight + 6;
    this.content.add(rule(sc, x0, y, innerW));
    y += 4 + 8;
    // 탭: Container → Graphics → 글자 (버튼 규약)
    const n = SETTINGS_TABS.length;
    const tw = Math.floor((innerW - U.tabGap * (n - 1)) / n);
    SETTINGS_TABS.forEach((tab, i) => {
      const x = x0 + i * (tw + U.tabGap);
      const g = sc.add.graphics();
      const t = new GlowText(sc, 0, 0, tabLabel(tab), 'page_unsel', { stageIndex: this.si });
      t.setPosition(Math.round(tw / 2 - t.displayWidth / 2), Math.round((U.tabH - t.displayHeight) / 2));
      const box = sc.add.container(x, y, [g, t]).setSize(tw, U.tabH);
      box.setInteractive(new Phaser.Geom.Rectangle(tw / 2, U.tabH / 2, tw, U.tabH), Phaser.Geom.Rectangle.Contains);
      if (box.input) box.input.cursor = 'pointer';
      box.on('pointerdown', () => {
        if (this.closed || this.waiting) return;
        this.cursorIdx = 0;
        this.setTab(tab);
      });
      this.content.add(box);
      this.tabs.push({ tab, box, g, t, x, w: tw });
    });
    y += U.tabH + U.tabBelow;
    this.rowsY = y;
    const rowsH = Math.max(...SETTINGS_TABS.map((t) => rowsHeight(rowsFor(t))));
    this.endTop = y + rowsH - rowsHeight(END_ROWS);
    y += rowsH;
    y += 8;
    this.noticeY = y;
    this.notice.setY(y);
    this.content.add(this.notice);
    y += 16 * 1.5 + 6;
    const hint = new GlowText(sc, x0, y, r62Text('settingsHintTabs'), 'page_faint', { wrap: innerW });
    this.content.add(hint);
    y += hint.displayHeight + U.top;
    return y;
  }

  /** 지금 탭의 줄을 (다시) 만든다 */
  private buildTabRows(): void {
    this.rowsBox.removeAll(true);
    this.dragRow = null;
    const { views, zones } = buildRows(
      this.scene,
      this.rowsBox,
      rowsFor(this.tab),
      this.rowsY,
      this.si,
      this.potionName,
      this.endTop,
    );
    this.rows = views;
    zones.forEach((zone, i) => {
      zone.on('pointerover', () => {
        if (this.dragRow === null && !this.waiting) this.setCursor(i + 1, false);
      });
      zone.on('pointerdown', (p: Phaser.Input.Pointer) => this.pointerDown(i, p));
    });
    this.cursorIdx = Math.min(this.cursorIdx, this.rows.length);
  }

  private setTab(tab: SettingsTab): void {
    if (tab === this.tab) return;
    this.tab = tab;
    this.buildTabRows();
    this.showNotice('');
    playUiSound(this.scene, 'move');
    this.refresh();
  }

  // ---- 입력

  private onKey = (e: KeyboardEvent): void => {
    if (this.closed) return;
    if (this.waiting) {
      // Esc 는 부른 화면이 back() 으로 (keydown-ESC 가 이 처리기보다 먼저 온다)
      if (e.key === 'Escape' || e.repeat) return;
      if (takeKey(e)) {
        e.preventDefault();
        this.captureKey(e.code);
      }
      return;
    }
    const k = e.key;
    const onTabs = this.cursorIdx === 0;
    if (k === 'ArrowUp' || k === 'w' || k === 'W') {
      if (takeKey(e)) this.setCursor(moveCursor(this.cursorIdx, -1, this.rows.length + 1), true);
    } else if (k === 'ArrowDown' || k === 's' || k === 'S') {
      if (takeKey(e)) this.setCursor(moveCursor(this.cursorIdx, 1, this.rows.length + 1), true);
    } else if (k === 'ArrowLeft' || k === 'a' || k === 'A' || k === 'ArrowRight' || k === 'd' || k === 'D') {
      if (!takeKey(e)) return;
      const dir = k === 'ArrowLeft' || k === 'a' || k === 'A' ? -1 : 1;
      if (onTabs) this.setTab(cycleTab(this.tab, dir));
      else this.change(dir);
    } else if (k === 'Enter' || k === ' ') {
      if (takeKey(e)) {
        if (onTabs) this.setTab(cycleTab(this.tab, 1));
        else this.activate(this.cursorIdx - 1);
      }
    }
  };

  private pointerDown(i: number, p: Phaser.Input.Pointer): void {
    if (this.closed || this.waiting) return;
    this.setCursor(i + 1, false);
    const v = this.rows[i];
    const lx = p.worldX - this.content.x - U.pad;
    const row = v.row;
    if (row.kind === 'slider') {
      if (lx < TRACK_X - 1) this.apply(changeSetting(this.values, row.id, -1));
      else if (lx > TRACK_X + TRACK_W + 1) {
        if (lx < PCT_X) this.apply(changeSetting(this.values, row.id, 1));
      } else {
        this.dragRow = i;
        this.dragTo(p);
      }
    } else if (v.opts) {
      const [a, b] = v.opts;
      const mid = b.x - U.pad - U.toggleGap / 2;
      const ax = a.x - U.pad;
      if (lx >= ax - 2 && lx < mid) this.setOption(row, 0);
      else if (lx >= mid && lx <= b.x - U.pad + b.displayWidth + 2) this.setOption(row, 1);
      else this.activate(i);
    } else this.activate(i);
  }

  private onMove = (p: Phaser.Input.Pointer): void => {
    if (this.dragRow === null || this.closed) return;
    if (!p.isDown) {
      this.dragRow = null;
      return;
    }
    this.dragTo(p);
  };

  private onUp = (): void => {
    this.dragRow = null;
  };

  /** 막대 위 마우스 x → 값 (칸 가운데 기준으로 반올림) */
  private dragTo(p: Phaser.Input.Pointer): void {
    const v = this.rows[this.dragRow ?? -1];
    if (!v || v.row.kind !== 'slider') return;
    const lx = p.worldX - this.content.x - U.pad - TRACK_X;
    this.apply(setSlider(this.values, v.row.id, sliderFromRatio(lx / TRACK_W)));
  }

  /** ←→ (줄) */
  private change(dir: -1 | 1): void {
    const v = this.rows[this.cursorIdx - 1];
    if (!v) return;
    const row = v.row;
    if (row.kind === 'slider' || row.kind === 'toggle') this.apply(changeSetting(this.values, row.id, dir));
    else if (row.kind === 'local' || row.kind === 'choice') this.setOption(row, dir < 0 ? 0 : 1);
  }

  /** Enter·스페이스·클릭 */
  private activate(i: number): void {
    const v = this.rows[i];
    if (!v) return;
    const row = v.row;
    if (row.kind === 'toggle') this.apply(toggleSetting(this.values, row.id));
    else if (row.kind === 'local' || row.kind === 'choice') {
      const cur = this.optionOf(row);
      this.setOption(row, cur === 0 ? 1 : 0);
    } else if (row.kind === 'key') this.startWaiting(row.id);
    else if (row.id === 'resetKeys') this.apply(setKeys(this.values, { ...DEFAULT_KEYS }));
    else if (row.id === 'reset') {
      this.apply(defaultSettings());
      if (textSize() !== 'normal') this.setOption({ id: 'textSize', kind: 'choice' }, 0);
    } else if (row.id === 'close') this.close();
  }

  /** 두 갈래 줄: 0 = 왼쪽(켬·보통) · 1 = 오른쪽(끔·크게) */
  private setOption(row: SettingRow, o: 0 | 1): void {
    if (row.kind === 'toggle') {
      this.apply({ ...this.values, [row.id]: o === 0 });
      return;
    }
    if (this.optionOf(row) === o) return;
    if (row.kind === 'choice') {
      const size = o === 1 ? 'large' : 'normal';
      setTextSize(size);
      // 시스템 월드 글자(피해 숫자 등)도 따라오게 설정에 싣는다 (계약 D textScale)
      this.apply({ ...this.values, textScale: systemTextScale(size) } as SettingsValues);
      this.showPreview();
    } else if (row.id === 'muted') {
      this.muted = o === 0;
      setMutedCmd(this.muted);
    } else if (row.id === 'fullscreen') {
      if (!fullscreenSupported()) {
        this.showNotice(r62Text('fullscreenNo'));
        return;
      }
      requestFullscreen(o === 0);
    }
    playUiSound(this.scene, 'select');
    this.refresh();
  }

  private optionOf(row: SettingRow): 0 | 1 | null {
    switch (row.kind) {
      case 'toggle':
        return this.values[row.id] ? 0 : 1;
      case 'choice':
        return textSize() === 'large' ? 1 : 0;
      case 'local':
        if (row.id === 'muted') return this.muted ? 0 : 1;
        return fullscreenSupported() ? (isFullscreen() ? 0 : 1) : null;
      default:
        return null;
    }
  }

  // ---- 키 재설정

  private startWaiting(action: KeyActionId): void {
    this.waiting = action;
    this.blink = true;
    playUiSound(this.scene, 'select');
    const sc = this.scene;
    const W = U.waitW;
    const title = new GlowText(
      sc,
      0,
      0,
      fill(r62Text('keyWaitTitle'), { action: this.actionName(action) }),
      'ink_accent',
      {
        stageIndex: this.si,
      },
    );
    const body = new GlowText(sc, 0, 0, r62Text('keyWaitBody'), 'ink_body', { stageIndex: this.si });
    const foot = new GlowText(sc, 0, 0, r62Text('keyWaitFoot'), 'ink_faint', { stageIndex: this.si });
    let y = U.waitPad;
    for (const t of [title, body, foot]) {
      t.placeCenter(W / 2, y);
      y += t.displayHeight + 2;
    }
    const h = y + U.waitPad - 2;
    const panel = inkPanel(sc, 0, 0, W, h);
    const cx = Math.round(U.pageW / 2 - W / 2);
    // 키 줄을 가리지 않게 끝줄(되돌리기·덮기) 자리에
    const cy = Math.round(this.endTop + 2);
    this.waitBox = sc.add.container(cx, cy, [panel, title, body, foot]);
    this.content.add(this.waitBox);
    this.refresh();
  }

  private stopWaiting(): void {
    this.waiting = null;
    this.waitBox?.destroy();
    this.waitBox = undefined;
    this.refresh();
  }

  private captureKey(code: string): void {
    const action = this.waiting;
    if (!action) return;
    const r = assignKey(this.values.keys, action, codeToKeyName(code));
    if (!r.ok) {
      this.showNotice(r.reason === 'reserved' ? fill(r62Text('keyReserved'), { key: r.label }) : r62Text('keyUnknown'));
      playUiSound(this.scene, 'back');
      return;
    }
    this.stopWaiting();
    this.apply(setKeys(this.values, r.binds));
    this.showNotice(r.swapped ? fill(r62Text('keySwapped'), { other: this.actionName(r.swapped) }) : '');
  }

  private actionName(a: KeyActionId): string {
    return rowLabel({ id: a, kind: 'key' }, this.potionName);
  }

  // ---- 값

  /** 값이 바뀌었으면 곧바로 시스템으로 보내고 다시 그린다 */
  private apply(next: SettingsValues): void {
    if (next === this.values || sameSettings(next, this.values)) return;
    this.values = next;
    commitSettings(next);
    playUiSound(this.scene, 'select');
    this.refresh();
  }

  private setCursor(i: number, byKey: boolean): void {
    if (i === this.cursorIdx) return;
    this.cursorIdx = i;
    if (byKey) playUiSound(this.scene, 'move');
    const row = this.rows[i - 1]?.row;
    if (row?.kind === 'choice') this.showPreview();
    else if (this.preview) this.showNotice('');
    this.refresh();
  }

  /** 아래 한 줄 알림 (빈 글이면 지움) */
  private showNotice(text: string): void {
    this.preview?.destroy();
    this.preview = undefined;
    this.noticeTimer?.remove();
    this.noticeText = text;
    this.notice.setText(text).setVisible(Boolean(text));
    if (text)
      this.noticeTimer = this.scene.time.delayedCall(U.noticeMs, () => {
        if (this.closed) return;
        this.noticeText = '';
        this.notice.setText('');
      });
  }

  /** 글자 크기 줄: 고른 크기로 쓴 보기 한 줄 (읽는 글과 같은 배율) */
  private showPreview(): void {
    this.showNotice('');
    const t = new GlowText(this.scene, U.pad, this.noticeY, r62Text('textPreview'), 'page_body', {
      wrap: U.pageW - U.pad * 2,
      readable: true,
      stageIndex: this.si,
    });
    this.content.add(t);
    this.preview = t;
  }

  // ---- 그리기

  private rowState = (row: SettingRow): RowState => {
    switch (row.kind) {
      case 'slider':
        return { slider: this.values[row.id] };
      case 'key':
        return { key: this.values.keys[row.id], waiting: this.waiting === row.id };
      case 'toggle':
      case 'local':
      case 'choice':
        return { option: this.optionOf(row) };
      default:
        return {};
    }
  };

  private refresh(): void {
    if (this.closed) return;
    const g = this.g.clear();
    this.drawTabs();
    drawRows(this.scene, g, this.rows, this.cursorIdx - 1, this.si, this.rowState, this.blink);
    if (this.cursorIdx === 0) {
      const tv = this.tabs.find((t) => t.tab === this.tab);
      if (tv) this.cursorSprite.setPosition(tv.x + tv.t.x - 6, tv.box.y + tv.t.y + 8);
    } else {
      const v = this.rows[this.cursorIdx - 1];
      if (v) this.cursorSprite.setPosition(v.label.x - 6, v.label.y + 8);
    }
    debugExpose('settings', {
      open: true,
      tab: this.tab,
      cursor: this.cursorIdx,
      waiting: this.waiting,
      textSize: textSize(),
      muted: this.muted,
      fullscreen: isFullscreen(),
      values: { ...this.values, keys: { ...this.values.keys } },
      keys: Object.fromEntries(Object.entries(this.values.keys).map(([k, v]) => [k, keyLabel(v)])),
      notice: this.noticeText,
      geom: this.geometry(),
    });
  }

  private drawTabs(): void {
    for (const tv of this.tabs) {
      const sel = tv.tab === this.tab;
      const focus = sel && this.cursorIdx === 0;
      const g = tv.g.clear();
      g.fillStyle(hexToNum(sel ? SEPIA[2] : SEPIA[1]), 1).fillRect(0, 0, tv.w, U.tabH);
      g.fillStyle(hexToNum(sel ? SEPIA[4] : SEPIA[3]), 1).fillRect(0, U.tabH - 1, tv.w, 1);
      if (sel)
        g.fillStyle(hexToNum(accentHex(this.scene, this.si, focus ? 22 : 20)), 1).fillRect(
          2,
          U.tabH - U.tabLineH,
          tv.w - 4,
          U.tabLineH,
        );
      if (focus)
        g.lineStyle(1, hexToNum(accentHex(this.scene, this.si, 22)), 1).strokeRect(0.5, 0.5, tv.w - 1, U.tabH - 1);
      tv.t.setGlowStyle(sel ? 'page_selected' : 'page_unsel');
    }
  }

  /** 헤드리스 확인용 화면 좌표 (논리 960×540) */
  private geometry(): Record<string, unknown> {
    const ox = this.content.x + U.pad;
    const oy = this.content.y;
    return {
      tabs: Object.fromEntries(
        this.tabs.map((t) => [t.tab, { x: this.content.x + t.x + Math.round(t.w / 2), y: oy + t.box.y + U.tabH / 2 }]),
      ),
      rows: Object.fromEntries(
        this.rows.map((v) => [
          v.row.id,
          {
            y: oy + v.y + Math.round(v.h / 2),
            labelX: this.content.x + v.label.x + 4,
            ...(v.row.kind === 'slider'
              ? { trackX: ox + TRACK_X, trackW: TRACK_W, leftX: ox + ARROW_L + 2, rightX: ox + ARROW_R + 2 }
              : {}),
            ...(v.opts ? { onX: this.content.x + v.opts[0].x + 6, offX: this.content.x + v.opts[1].x + 6 } : {}),
            ...(v.key ? { keyX: ox + U.ctrlX + 10 } : {}),
          },
        ]),
      ),
    };
  }
}
