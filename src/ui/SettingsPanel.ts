import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { takeKey } from './keyGate';
import { book, cursor as makeCursor, rule } from './kit';
import { commitSettings, currentSettings, defaultSettings } from './settingsStore';
import {
  SETTING_ROWS,
  SLIDER_STEPS,
  type SettingRow,
  type SettingsValues,
  changeSetting,
  moveCursor,
  percentText,
  sameSettings,
  setSlider,
  sliderCells,
  sliderFromRatio,
  toggleSetting,
} from './settingsView';
import { swatch } from './StructureHud';
import { r61Text } from './text';
import type { R61TextKey } from './textR61';
import { GRAY, ROUTE, SEPIA, hexToNum } from './theme';
import { SETTINGS_UI as U } from './themeR61';

/** 줄마다 그린 것 (쪽 원점 기준 좌표) */
interface RowView {
  row: SettingRow;
  y: number;
  h: number;
  label: GlowText;
  pct?: GlowText;
  on?: GlowText;
  off?: GlowText;
}

const LABEL_KEY: Record<SettingRow['id'], R61TextKey> = {
  shake: 'shake',
  flash: 'flash',
  tilt: 'tilt',
  damageNumbers: 'damageNumbers',
  master: 'master',
  bgm: 'bgm',
  sfx: 'sfx',
  reset: 'reset',
  close: 'close',
};

/** 막대 칸 전체 폭 */
const TRACK_W = SLIDER_STEPS * U.cellW + (SLIDER_STEPS - 1) * U.cellGap;
/** 쪽 안쪽 왼쪽에서: 왼 화살표 · 칸 · 오른 화살표 · '70%' */
const ARROW_L = U.ctrlX;
const TRACK_X = ARROW_L + U.arrowW + U.arrowGap;
const ARROW_R = TRACK_X + TRACK_W + U.arrowGap;
const PCT_X = ARROW_R + U.arrowW + U.pctGap;

export interface SettingsPanelOptions {
  stageIndex: number;
  /** 덮었을 때 (Esc·'덮는다') — 부른 화면이 목록 입력을 다시 켠다 */
  onClose: () => void;
}

/**
 * 61라운드 P10 설정 화면 (계약 §15) — 일시정지 일기장의 '설정' 항목, 타이틀의 '설정' 에서 연다.
 * 일기장 한 쪽(책 틀 + 종이) 위에: 화면(흔들림 막대 · 섬광 · 화면 기울기 · 피해 숫자) / 소리(전체 · 배경음 · 효과음 막대) /
 * 처음 값으로 되돌린다 · 덮는다. 값이 바뀌는 즉시 `setSettings`(settingsStore).
 * 조작: ↑↓(W·S) 고르기 · ←→(A·D) 바꾸기(막대 10%, 켜고 끄기는 ← 켬 · → 끔) · Enter·스페이스 켜고 끄기·실행 ·
 * 마우스(올리면 고름, 막대 누르고 끌기·화살표 누르기, 켬/끔 누르기). Esc 는 부른 화면이 받아 `close()` 한다(한 단계 뒤로).
 * 화면 전체를 G00 α0.55 로 덮어 아래 목록이 눌리지 않게 한다(바깥 누르기로는 닫지 않는다 — 막대를 끌다 놓쳐도 그대로).
 */
export class SettingsPanel {
  private box: Phaser.GameObjects.Container;
  private content: Phaser.GameObjects.Container;
  private g: Phaser.GameObjects.Graphics;
  private cursorSprite: Phaser.GameObjects.Sprite;
  private rows: RowView[] = [];
  private values: SettingsValues;
  private cursorIdx = 0;
  private dragRow: number | null = null;
  private closed = false;
  private si: number;

  constructor(
    private scene: Phaser.Scene,
    private opts: SettingsPanelOptions,
  ) {
    this.si = opts.stageIndex;
    this.values = currentSettings();
    const block = scene.add
      .rectangle(0, 0, UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT, hexToNum(GRAY[0]), ROUTE.dimAlpha)
      .setOrigin(0)
      .setInteractive();
    // 쪽 안 글·그림 (쪽 원점 0,0 기준으로 만들고 높이를 잰 뒤 책을 깐다)
    this.content = scene.add.container(0, 0);
    this.g = scene.add.graphics();
    this.content.add(this.g);
    const pageH = this.buildContent();
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
    scene.input.keyboard?.on('keydown', this.onKey);
    scene.input.on('pointermove', this.onMove);
    scene.input.on('pointerup', this.onUp);
    this.refresh();
  }

  /** 덮기 (Esc·'덮는다'). 두 번 불러도 한 번만 */
  close(): void {
    if (this.closed) return;
    this.destroy();
    this.opts.onClose();
  }

  destroy(): void {
    if (this.closed) return;
    this.closed = true;
    this.scene.input.keyboard?.off('keydown', this.onKey);
    this.scene.input.off('pointermove', this.onMove);
    this.scene.input.off('pointerup', this.onUp);
    this.box.destroy();
    debugExpose('settings', { open: false });
  }

  // ---- 만들기

  /** 쪽 안 글·줄을 만들고 쪽 높이를 돌려준다 */
  private buildContent(): number {
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
    let group: SettingRow['group'] | '' = '';
    SETTING_ROWS.forEach((row) => {
      if (row.group !== group) {
        if (group) y += 6;
        group = row.group;
        if (row.group === 'end') {
          this.content.add(rule(sc, x0, y, innerW));
          y += 4 + 6;
        } else {
          const head = new GlowText(
            sc,
            x0,
            y,
            r61Text(row.group === 'screen' ? 'groupScreen' : 'groupSound'),
            'page_faint',
          );
          this.content.add(head);
          y += U.headH;
        }
      }
      const h = row.kind === 'action' ? U.actionRowH : U.rowH;
      const ty = y + Math.round((h - 16) / 2);
      const label = new GlowText(sc, x0 + 14, ty, r61Text(LABEL_KEY[row.id]), 'page_unsel', { stageIndex: this.si });
      const view: RowView = { row, y, h, label };
      this.content.add(label);
      if (row.kind === 'slider') {
        view.pct = new GlowText(sc, x0 + PCT_X, ty, '', 'page_body', { stageIndex: this.si });
        this.content.add(view.pct);
      } else if (row.kind === 'toggle') {
        view.on = new GlowText(sc, x0 + TRACK_X, ty, r61Text('on'), 'page_faint', { stageIndex: this.si });
        view.off = new GlowText(sc, view.on.x + view.on.displayWidth + U.toggleGap, ty, r61Text('off'), 'page_faint', {
          stageIndex: this.si,
        });
        this.content.add([view.on, view.off]);
      }
      // 줄 전체 판정 칸 (올리면 고름, 누르면 그 자리 동작)
      const zone = sc.add.zone(x0, y, innerW, h).setOrigin(0).setInteractive({ cursor: 'pointer' });
      const i = this.rows.length;
      zone.on('pointerover', () => {
        if (this.dragRow === null) this.setCursor(i);
      });
      zone.on('pointerdown', (p: Phaser.Input.Pointer) => this.pointerDown(i, p));
      this.content.add(zone);
      this.rows.push(view);
      y += h;
    });
    y += 8;
    const hint = new GlowText(sc, x0, y, r61Text('settingsHint'), 'page_faint', { wrap: innerW });
    this.content.add(hint);
    y += hint.displayHeight + U.top;
    return y;
  }

  // ---- 입력

  private onKey = (e: KeyboardEvent): void => {
    if (this.closed) return;
    const k = e.key;
    if (k === 'ArrowUp' || k === 'w' || k === 'W') {
      if (takeKey(e)) this.setCursor(moveCursor(this.cursorIdx, -1, this.rows.length));
    } else if (k === 'ArrowDown' || k === 's' || k === 'S') {
      if (takeKey(e)) this.setCursor(moveCursor(this.cursorIdx, 1, this.rows.length));
    } else if (k === 'ArrowLeft' || k === 'a' || k === 'A') {
      if (takeKey(e)) this.change(-1);
    } else if (k === 'ArrowRight' || k === 'd' || k === 'D') {
      if (takeKey(e)) this.change(1);
    } else if (k === 'Enter' || k === ' ') {
      if (takeKey(e)) this.activate(this.cursorIdx);
    }
  };

  private pointerDown(i: number, p: Phaser.Input.Pointer): void {
    if (this.closed) return;
    this.setCursor(i);
    const v = this.rows[i];
    const lx = p.worldX - this.content.x - U.pad;
    if (v.row.kind === 'slider') {
      const id = v.row.id;
      if (lx < TRACK_X - 1) this.apply(changeSetting(this.values, id, -1));
      else if (lx > TRACK_X + TRACK_W + 1) {
        if (lx < PCT_X) this.apply(changeSetting(this.values, id, 1));
      } else {
        this.dragRow = i;
        this.dragTo(p);
      }
    } else if (v.row.kind === 'toggle' && v.on && v.off) {
      const id = v.row.id;
      const onX = v.on.x - U.pad;
      const offX = v.off.x - U.pad;
      if (lx >= onX - 2 && lx < offX - U.toggleGap / 2) this.apply({ ...this.values, [id]: true });
      else if (lx >= offX - U.toggleGap / 2 && lx <= offX + v.off.displayWidth + 2)
        this.apply({ ...this.values, [id]: false });
      else this.apply(toggleSetting(this.values, id));
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

  private change(dir: -1 | 1): void {
    const v = this.rows[this.cursorIdx];
    if (!v || v.row.kind === 'action') return;
    this.apply(changeSetting(this.values, v.row.id, dir));
  }

  private activate(i: number): void {
    const v = this.rows[i];
    if (!v) return;
    if (v.row.kind === 'toggle') this.apply(toggleSetting(this.values, v.row.id));
    else if (v.row.id === 'reset') this.apply(defaultSettings());
    else if (v.row.id === 'close') this.close();
  }

  /** 값이 바뀌었으면 곧바로 시스템으로 보내고 다시 그린다 */
  private apply(next: SettingsValues): void {
    if (next === this.values || sameSettings(next, this.values)) return;
    this.values = next;
    commitSettings(next);
    this.refresh();
  }

  private setCursor(i: number): void {
    if (i === this.cursorIdx) return;
    this.cursorIdx = i;
    this.refresh();
  }

  // ---- 그리기

  private refresh(): void {
    const g = this.g.clear();
    const x0 = U.pad;
    const lit = (sel: boolean): number => (sel ? swatch(this.scene, this.si, { slot: U.litSlot }) : hexToNum(SEPIA[5]));
    this.rows.forEach((v, i) => {
      const sel = i === this.cursorIdx;
      v.label.setGlowStyle(sel ? 'page_selected' : 'page_unsel');
      if (sel) this.cursorSprite.setPosition(v.label.x - 6, v.label.y + 8);
      const cy = v.y + Math.round((v.h - U.cellH) / 2);
      if (v.row.kind === 'slider' && v.pct) {
        const val = this.values[v.row.id];
        const n = sliderCells(val);
        for (let k = 0; k < SLIDER_STEPS; k++) {
          const cx = x0 + TRACK_X + k * (U.cellW + U.cellGap);
          if (k < n) g.fillStyle(lit(sel), 1).fillRect(cx, cy, U.cellW, U.cellH);
          else {
            g.fillStyle(hexToNum(SEPIA[3]), 1).fillRect(cx, cy, U.cellW, U.cellH);
            g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(cx + 1, cy + 1, U.cellW - 2, U.cellH - 2);
          }
        }
        const ay = v.y + Math.round((v.h - U.arrowH) / 2);
        const arrow = (on: boolean): number => hexToNum(on ? (sel ? SEPIA[5] : SEPIA[4]) : SEPIA[2]);
        this.arrow(x0 + ARROW_L, ay, -1, arrow(val > 0));
        this.arrow(x0 + ARROW_R, ay, 1, arrow(val < 1));
        v.pct.setText(percentText(val)).setGlowStyle(sel ? 'page_selected' : 'page_body');
      } else if (v.row.kind === 'toggle' && v.on && v.off) {
        const on = this.values[v.row.id];
        const chosen = on ? v.on : v.off;
        const other = on ? v.off : v.on;
        chosen.setGlowStyle(sel ? 'page_selected' : 'page_body');
        other.setGlowStyle('page_faint');
        g.fillStyle(lit(sel), 1).fillRect(
          chosen.x + 2,
          chosen.y + chosen.displayHeight - 1,
          chosen.textW,
          U.underlineH,
        );
      }
    });
    debugExpose('settings', { open: true, cursor: this.cursorIdx, values: { ...this.values }, geom: this.geometry() });
  }

  /** 픽셀 삼각 화살표 (높이 7, 폭 4). dir -1 = 왼쪽 */
  private arrow(x: number, y: number, dir: -1 | 1, color: number): void {
    const mid = (U.arrowH - 1) / 2;
    for (let r = 0; r < U.arrowH; r++) {
      const len = U.arrowW - Math.abs(r - mid) * ((U.arrowW - 1) / mid);
      const w = Math.max(1, Math.round(len));
      this.g.fillStyle(color, 1).fillRect(dir < 0 ? x + U.arrowW - w : x, y + r, w, 1);
    }
  }

  /** 헤드리스 확인용 화면 좌표 (논리 960×540) */
  private geometry(): Record<string, unknown> {
    const ox = this.content.x + U.pad;
    const oy = this.content.y;
    return Object.fromEntries(
      this.rows.map((v) => [
        v.row.id,
        {
          y: oy + v.y + Math.round(v.h / 2),
          labelX: this.content.x + v.label.x + 4,
          ...(v.row.kind === 'slider'
            ? { trackX: ox + TRACK_X, trackW: TRACK_W, leftX: ox + ARROW_L + 2, rightX: ox + ARROW_R + 2 }
            : {}),
          ...(v.on && v.off ? { onX: this.content.x + v.on.x + 6, offX: this.content.x + v.off.x + 6 } : {}),
        },
      ]),
    );
  }
}
