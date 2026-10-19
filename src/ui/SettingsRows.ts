import Phaser from 'phaser';
import { GlowText } from './glow';
import { keyLabel, type KeyActionId } from './keyBindView';
import { rule } from './kit';
import { swatch } from './StructureHud';
import { fill, p21Text, r61Text, r62Text } from './text';
import { SEPIA, hexToNum } from './theme';
import { SETTINGS_UI as U } from './themeR61';
import {
  SLIDER_STEPS,
  percentText,
  sliderCells,
  type GoreLevel,
  type SettingRow,
  type SettingsTab,
} from './settingsView';

/** 줄마다 그린 것 (쪽 원점 기준 좌표) */
export interface RowView {
  row: SettingRow;
  y: number;
  h: number;
  label: GlowText;
  pct?: GlowText;
  /** 갈래 (켬·끔 / 보통·크게 / P21 고어 전체·줄임·끔) — 왼쪽이 [0] */
  opts?: GlowText[];
  /** 키 칸 */
  key?: GlowText;
}

/** 막대 칸 전체 폭 */
export const TRACK_W = SLIDER_STEPS * U.cellW + (SLIDER_STEPS - 1) * U.cellGap;
/** 쪽 안쪽 왼쪽에서: 왼 화살표 · 칸 · 오른 화살표 · '70%' */
export const ARROW_L = U.ctrlX;
export const TRACK_X = ARROW_L + U.arrowW + U.arrowGap;
export const ARROW_R = TRACK_X + TRACK_W + U.arrowGap;
export const PCT_X = ARROW_R + U.arrowW + U.pctGap;

const KEY_LABEL: Record<KeyActionId, Parameters<typeof r62Text>[0]> = {
  up: 'keyUp',
  down: 'keyDown',
  left: 'keyLeft',
  right: 'keyRight',
  dash: 'keyDash',
  interact: 'keyInteract',
  potion: 'keyPotion',
};

/** 줄 이름 (potion = 스냅샷 `names.potion`) */
export function rowLabel(row: SettingRow, potionName: string): string {
  switch (row.kind) {
    case 'key':
      return fill(r62Text(KEY_LABEL[row.id]), { potion: potionName || '독주' });
    case 'local':
      return r62Text(row.id === 'fullscreen' ? 'fullscreen' : 'muted');
    case 'choice':
      return row.id === 'gore' ? p21Text('gore') : r62Text('textSize');
    case 'toggle':
      return row.id === 'hitstop' ? r62Text('hitstop') : r61Text(row.id);
    case 'slider':
      return r61Text(row.id);
    default:
      return row.id === 'resetKeys' ? r62Text('resetKeys') : r61Text(row.id);
  }
}

export function tabLabel(t: SettingsTab): string {
  return r62Text(
    t === 'screen' ? 'tabScreen' : t === 'sound' ? 'tabSound' : t === 'controls' ? 'tabControls' : 'tabAccess',
  );
}

/** 갈래 글 (왼쪽부터) */
export function optionTexts(row: SettingRow): string[] {
  if (row.kind === 'choice' && row.id === 'gore')
    return [p21Text('goreFull'), p21Text('goreReduced'), p21Text('goreOff')];
  return row.kind === 'choice' ? [r62Text('textNormal'), r62Text('textLarge')] : [r61Text('on'), r61Text('off')];
}

/** P21 고어 단계 설명 한 줄 (설정 아래 알림 · 첫 실행 안내 카드) */
export function goreDesc(g: GoreLevel): string {
  return p21Text(g === 2 ? 'goreFullDesc' : g === 1 ? 'goreReducedDesc' : 'goreOffDesc');
}

/** 줄 높이 */
export function rowHeight(row: SettingRow): number {
  return row.kind === 'action' ? U.actionRowH : U.rowH;
}

/** 탭 줄들의 높이 (탭 줄 + 끝줄 앞 괘선) — 쪽 높이 계산용 */
export function rowsHeight(rows: readonly SettingRow[]): number {
  let h = 0;
  let endSeen = false;
  for (const r of rows) {
    if (!endSeen && (r.id === 'reset' || r.id === 'close')) {
      endSeen = true;
      h += 6 + 4 + 6;
    }
    h += rowHeight(r);
  }
  return h;
}

/**
 * 한 탭의 줄들을 `box`(쪽 원점 기준) 안에 만든다 — 글만 만들고 칸·화살·밑줄은 `drawRows` 가 매번 그린다.
 * 줄마다 판정 칸(zone)을 돌려준다(부른 쪽이 마우스를 건다).
 */
export function buildRows(
  scene: Phaser.Scene,
  box: Phaser.GameObjects.Container,
  rows: readonly SettingRow[],
  y0: number,
  si: number,
  potionName: string,
  /** 끝줄(되돌리기·덮기) 앞 괘선 자리 — 탭마다 같은 자리에 두려고 (없으면 탭 줄 바로 밑) */
  endTop?: number,
): { views: RowView[]; zones: Phaser.GameObjects.Zone[] } {
  const x0 = U.pad;
  const innerW = U.pageW - U.pad * 2;
  const views: RowView[] = [];
  const zones: Phaser.GameObjects.Zone[] = [];
  let y = y0;
  let endSeen = false;
  for (const row of rows) {
    if (!endSeen && (row.id === 'reset' || row.id === 'close')) {
      endSeen = true;
      if (endTop !== undefined) y = Math.max(y, endTop);
      y += 6;
      box.add(rule(scene, x0, y, innerW));
      y += 4 + 6;
    }
    const h = rowHeight(row);
    const ty = y + Math.round((h - 16) / 2);
    const label = new GlowText(scene, x0 + 14, ty, rowLabel(row, potionName), 'page_unsel', { stageIndex: si });
    const view: RowView = { row, y, h, label };
    box.add(label);
    if (row.kind === 'slider') {
      view.pct = new GlowText(scene, x0 + PCT_X, ty, '', 'page_body', { stageIndex: si });
      box.add(view.pct);
    } else if (row.kind === 'toggle' || row.kind === 'local' || row.kind === 'choice') {
      let ox = x0 + TRACK_X;
      view.opts = optionTexts(row).map((t) => {
        const o = new GlowText(scene, ox, ty, t, 'page_faint', { stageIndex: si });
        ox += o.displayWidth + U.toggleGap;
        return o;
      });
      box.add(view.opts);
    } else if (row.kind === 'key') {
      view.key = new GlowText(scene, x0 + U.ctrlX + U.keyPadX, ty, '', 'page_body', { stageIndex: si });
      box.add(view.key);
    }
    const zone = scene.add.zone(x0, y, innerW, h).setOrigin(0).setInteractive({ cursor: 'pointer' });
    box.add(zone);
    zones.push(zone);
    views.push(view);
    y += h;
  }
  return { views, zones };
}

/** 그릴 때 줄마다 필요한 값 */
export interface RowState {
  slider?: number;
  /** 갈래: 고른 쪽 번호(0 = 왼쪽) · null(쓸 수 없음) */
  option?: number | null;
  key?: string;
  /** 키 기다리는 중 */
  waiting?: boolean;
}

/** 칸·화살·밑줄·키 상자 (매번 다시) */
export function drawRows(
  scene: Phaser.Scene,
  g: Phaser.GameObjects.Graphics,
  views: readonly RowView[],
  cursorRow: number,
  si: number,
  state: (row: SettingRow) => RowState,
  blink: boolean,
): void {
  const x0 = U.pad;
  const lit = (sel: boolean): number => (sel ? swatch(scene, si, { slot: U.litSlot }) : hexToNum(SEPIA[5]));
  views.forEach((v, i) => {
    const sel = i === cursorRow;
    v.label.setGlowStyle(sel ? 'page_selected' : 'page_unsel');
    const st = state(v.row);
    const cy = v.y + Math.round((v.h - U.cellH) / 2);
    if (v.row.kind === 'slider' && v.pct) {
      const val = st.slider ?? 0;
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
      pixelArrow(g, x0 + ARROW_L, ay, -1, arrow(val > 0));
      pixelArrow(g, x0 + ARROW_R, ay, 1, arrow(val < 1));
      v.pct.setText(percentText(val)).setGlowStyle(sel ? 'page_selected' : 'page_body');
    } else if (v.opts) {
      const o = st.option ?? null;
      v.opts.forEach((t) => t.setGlowStyle('page_faint'));
      const chosen = o === null ? undefined : v.opts[o];
      if (chosen) {
        chosen.setGlowStyle(sel ? 'page_selected' : 'page_body');
        g.fillStyle(lit(sel), 1).fillRect(
          chosen.x + 2,
          chosen.y + chosen.displayHeight - 1,
          chosen.textW,
          U.underlineH,
        );
      }
    } else if (v.key) {
      const t = v.key;
      t.setText(st.waiting ? (blink ? '…' : ' ') : keyLabel(st.key ?? '')).setGlowStyle(
        sel ? 'page_selected' : 'page_body',
      );
      // 키캡 상자: 세피아 테 + 안쪽 종이 (고른 줄은 층 강조 테)
      const w = Math.max(U.keyMinW, t.textW + U.keyPadX * 2 + 4);
      const kx = x0 + U.ctrlX;
      const ky = v.y + Math.round((v.h - U.keyH) / 2);
      g.fillStyle(sel || st.waiting ? lit(true) : hexToNum(SEPIA[4]), 1).fillRect(kx, ky, w, U.keyH);
      g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(kx + 1, ky + 1, w - 2, U.keyH - 2);
      g.fillStyle(hexToNum(SEPIA[3]), 1).fillRect(kx + 1, ky + U.keyH - 3, w - 2, 1);
      t.setX(Math.round(kx + w / 2 - t.displayWidth / 2));
    }
  });
}

/** 픽셀 삼각 화살표 (높이 7, 폭 4). dir -1 = 왼쪽 */
export function pixelArrow(g: Phaser.GameObjects.Graphics, x: number, y: number, dir: -1 | 1, color: number): void {
  const mid = (U.arrowH - 1) / 2;
  for (let r = 0; r < U.arrowH; r++) {
    const len = U.arrowW - Math.abs(r - mid) * ((U.arrowW - 1) / mid);
    const w = Math.max(1, Math.round(len));
    g.fillStyle(color, 1).fillRect(dir < 0 ? x + U.arrowW - w : x, y + r, w, 1);
  }
}
