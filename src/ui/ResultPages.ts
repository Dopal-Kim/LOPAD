import Phaser from 'phaser';
import type { UiBuildIcon, UiFloorEnd, UiResult, UiRunSummary } from '../contract/ui';
import { GlowText } from './glow';
import { traitIconBox, weaponFrameColor } from './growthArt';
import { ICON, accentHex, icon, rule } from './kit';
import { drawResultMap } from './ResultMap';
import {
  buildRows,
  deathStats,
  floorEndLines,
  floorEndStats,
  labelOf,
  weaponOfBuild,
  type StatCell,
} from './resultView';
import { l2eText } from './textLoop2E';
import { GRAY, SEPIA, hexToNum } from './theme';
import { RESULT_UI as R } from './themeLoop2E';
import type { VoiceWeaponId } from './themeStory';

/**
 * 62 루프 2 UI E (계약 C P1-6·P1-7): 결산 일기장 두 쪽의 그림 (ResultScene 이 버튼·입력을 붙인다).
 *  - 사망: 왼쪽 = '이 생의 기록' · 이름(번짐) · 쓰러진 곳 · 마지막 상대(초상 · 이름 · 한 줄) · 시간·처치·받은 피해 · 지닌 것 아이콘 줄
 *          오른쪽 = 지나온 길 미니맵(망령 표식) · 이야기 한 줄 · 영혼 +n · 다음 기억 한 줄 → (버튼)
 *  - 층 끝: 왼쪽 = '1층 끝' · 층 제목 · 일기장 문장 · 칸(시간·처치·받은 피해·단서·영혼) · 지닌 것
 *          오른쪽 = 지나온 길 · 빈 괘선 장 위에 맺음 한 줄을 한 글자씩 쓴다('다음 장은 아직 그려지지 않았다') → (버튼)
 */
export interface Page {
  x: number;
  y: number;
}

export interface PagesOut {
  /** 이름 글 (사망 번짐용) */
  name: GlowText | null;
  /** 버튼 줄 위 괘선 y (오른쪽 장) */
  buttonsY: number;
  /** 버튼이 뜨기까지 (층 끝 맺음 쓰기) ms */
  buttonsAt: number;
  /** 결산 아래 흐린 한 줄 (영혼 줄 — 기억을 떠올린 뒤 바꾼다) */
  soulsLine: GlowText | null;
}

const WEAPONS: readonly string[] = ['katana', 'greatsword', 'dagger', 'bow'];

/** 사망 결산 두 쪽 */
export function deathPages(sc: Phaser.Scene, r: UiResult, s: UiRunSummary, L: Page, Rp: Page, si: number): PagesOut {
  const W = R.pageW;
  const innerW = W - R.pad * 2;
  const x0 = L.x + R.pad;
  // ---- 왼쪽 장
  let y = L.y + 14;
  const title = new GlowText(sc, 0, 0, s.title || l2eText('diedTitle'), 'page_title', {
    scale: 2,
    font: 'title',
    stageIndex: si,
  });
  title.placeCenter(L.x + W / 2, y);
  y += title.displayHeight + 6;
  const name = new GlowText(sc, x0, y, r.playerName || '―', 'page_body', { stageIndex: si });
  if (s.where)
    new GlowText(sc, x0 + name.displayWidth + 10, y, s.where, 'page_faint', { wrap: innerW - name.displayWidth - 10 });
  y += 18;
  rule(sc, x0, y, innerW);
  y += 4 + 10;
  // 마지막 상대
  y = killerBlock(sc, s, x0, y, innerW, si) + 8;
  rule(sc, x0, y, innerW);
  y += 4 + 10;
  y = statRow(sc, deathStats(s), x0, y, innerW, si) + 10;
  buildBlock(sc, s.build, labelOf(s.labels, 'build'), x0, y, innerW, weaponOfBuild(s.build), si);
  // ---- 오른쪽 장
  const rx = Rp.x + R.pad;
  let ry = Rp.y + 14;
  ry = mapBlock(sc, s, labelOf(s.labels, 'path'), rx, ry, innerW, R.mapH, si) + 10;
  if (r.line) {
    const t = new GlowText(sc, rx, ry, r.line, 'page_body', { wrap: innerW, stageIndex: si });
    ry += t.displayHeight + 6;
  }
  const smudge = (r as { smudgeLine?: unknown }).smudgeLine;
  let smudgeT: GlowText | null = null;
  if (typeof smudge === 'string' && smudge.trim()) {
    smudgeT = new GlowText(sc, rx, ry, smudge.trim(), 'page_faint', { wrap: innerW, stageIndex: si }).setAlpha(0);
    ry += smudgeT.displayHeight + 6;
    sc.time.delayedCall(R.smudgeDelayMs, () => {
      if (!smudgeT?.active) return;
      sc.tweens.add({ targets: smudgeT, alpha: 1, duration: R.smudgeInMs });
      smudgeName(sc, name, r.playerName || '―', si);
    });
  }
  ry += 4;
  icon(sc, rx, ry, ICON.souls);
  const soulsT = new GlowText(sc, rx + 22, ry, s.soulsText, 'page_title', { stageIndex: si });
  ry += Math.max(18, soulsT.displayHeight) + 2;
  const ready = Boolean(s.souls.next && s.souls.next.left <= 0);
  const soulsLine = s.soulsLine
    ? new GlowText(sc, rx, ry, s.soulsLine, ready ? 'page_selected' : 'page_faint', { wrap: innerW, stageIndex: si })
    : null;
  ry += (soulsLine?.displayHeight ?? 0) + 8;
  return { name, buttonsY: ry, buttonsAt: 0, soulsLine };
}

/** 층 끝 결산 두 쪽 — 일기장 마지막 장 */
export function floorEndPages(
  sc: Phaser.Scene,
  f: UiFloorEnd,
  s: UiRunSummary | undefined,
  L: Page,
  Rp: Page,
  si: number,
): PagesOut {
  const W = R.pageW;
  const innerW = W - R.pad * 2;
  const x0 = L.x + R.pad;
  // ---- 왼쪽 장
  let y = L.y + 14;
  const title = new GlowText(sc, 0, 0, f.title, 'page_title', { scale: 2, font: 'title', stageIndex: si });
  title.placeCenter(L.x + W / 2, y);
  y += title.displayHeight + 2;
  if (f.floorTitle) {
    const ft = new GlowText(sc, 0, 0, f.floorTitle, 'page_faint', { stageIndex: si });
    ft.placeCenter(L.x + W / 2, y);
    y += ft.displayHeight + 4;
  }
  rule(sc, x0, y, innerW);
  y += 4 + 10;
  const { body, closing } = floorEndLines(f, l2eText('closingFallback'));
  for (const line of body) {
    const t = new GlowText(sc, x0, y, line, 'page_body', { wrap: innerW, stageIndex: si });
    y += t.displayHeight + 5;
  }
  y += 6;
  y = statGrid(sc, floorEndStats(f), x0, y, innerW, si) + 8;
  buildBlock(sc, f.build, f.labels.build || labelOf(undefined, 'build'), x0, y, innerW, weaponOfBuild(f.build), si);
  // ---- 오른쪽 장: 지나온 길 · 빈 괘선 장 · 맺음 한 줄
  const rx = Rp.x + R.pad;
  let ry = Rp.y + 14;
  if (s && (s.route || s.path.length))
    ry = mapBlock(sc, s, labelOf(s.labels, 'path'), rx, ry, innerW, Math.round(R.mapH * 0.72), si) + 12;
  const blankTop = ry;
  const blankBottom = Rp.y + R.pageH - 128;
  const g = sc.add.graphics();
  g.lineStyle(1, hexToNum(SEPIA[4]), 0.9);
  for (let ly = blankTop + R.blankRuleGap; ly < blankBottom; ly += R.blankRuleGap)
    g.lineBetween(rx, ly, rx + innerW, ly);
  // 맺음: 빈 장 가운데에 문장마다 2배 글씨로 차례로 적힌다 (먹이 번지듯 흐림 → 진함, 살짝 내려앉음)
  const sentences = closingSentences(closing);
  const texts = sentences.map(
    (t) =>
      new GlowText(sc, 0, 0, t, 'page_title', {
        scale: 2,
        font: 'title',
        wrap: Math.floor((innerW - 8) / 2),
        align: 'center',
        stageIndex: si,
      }),
  );
  const blockH = texts.reduce((h, t) => h + t.displayHeight + 6, -6);
  let ty = Math.round((blankTop + blankBottom) / 2 - blockH / 2) - 6;
  let at = R.closingDelayMs;
  let maxW = 0;
  for (const t of texts) {
    t.placeCenter(Rp.x + W / 2, ty).setAlpha(0);
    maxW = Math.max(maxW, t.displayWidth);
    const y0 = ty;
    t.setY(y0 - 4);
    sc.tweens.add({ targets: t, alpha: 1, y: y0, delay: at, duration: R.closingLineMs, ease: 'Quad.easeOut' });
    at += R.closingLineMs + R.closingGapMs;
    ty += t.displayHeight + 6;
  }
  // 맺음 밑 붓 한 획 (다 적힌 뒤 왼 → 오)
  const brush = sc.add.graphics();
  const by = ty + 4;
  const bw = Math.min(innerW - 40, maxW + 24);
  const bx = Math.round(Rp.x + W / 2 - bw / 2);
  const p = { t: 0 };
  sc.tweens.add({
    targets: p,
    t: 1,
    delay: at,
    duration: 420,
    ease: 'Quad.easeOut',
    onUpdate: () => {
      brush.clear();
      brush.fillStyle(hexToNum(accentHex(sc, si, 20)), 0.9);
      const w = Math.round(bw * p.t);
      brush.fillRect(bx, by, w, 2);
      brush.fillRect(bx + 4, by + 2, Math.max(0, w - 10), 1);
    },
  });
  const typeMs = at - R.closingDelayMs;
  let fy = Math.max(by + 14, blankBottom + 6);
  for (const line of [f.footer, s?.soulsLine]) {
    if (!line) continue;
    const ft = new GlowText(sc, 0, 0, line, 'page_faint', { wrap: innerW, align: 'center', stageIndex: si });
    ft.placeCenter(Rp.x + W / 2, fy).setAlpha(0);
    sc.tweens.add({ targets: ft, alpha: 1, delay: R.closingDelayMs + typeMs + 300, duration: 400 });
    fy += ft.displayHeight + 2;
  }
  return { name: null, buttonsY: fy + 4, buttonsAt: R.closingDelayMs + typeMs + R.buttonsDelayMs, soulsLine: null };
}

/** 맺음 한 줄을 문장으로 ('여기까지 적었다. 다음 장은 …' → 두 문장) */
function closingSentences(text: string): string[] {
  const out = text.split(/(?<=[.。])\s+/).filter(Boolean);
  return out.length ? out : [text];
}

// ---------------------------------------------------------------------------------------------

/** 마지막 상대: 초상 96 (테 2) · 이름 · 한 줄. 아래 끝 y */
function killerBlock(sc: Phaser.Scene, s: UiRunSummary, x: number, y: number, w: number, si: number): number {
  const P = R.portrait;
  const f = R.portraitFrame;
  const g = sc.add.graphics();
  g.fillStyle(hexToNum(GRAY[0]), 1).fillRect(x, y, P + f * 2 + 2, P + f * 2 + 2);
  g.fillStyle(hexToNum(SEPIA[4]), 1).fillRect(x + 1, y + 1, P + f * 2, P + f * 2);
  g.fillStyle(hexToNum(GRAY[1]), 1).fillRect(x + 1 + f, y + 1 + f, P, P);
  const px = x + 1 + f;
  const py = y + 1 + f;
  const p = s.killer?.portrait;
  if (p && sc.textures.exists(p.key)) {
    const img = sc.add.image(px + P / 2, py + P / 2, p.key, p.frame).setOrigin(0.5, 0.5);
    const k = P / Math.max(1, img.width, img.height);
    img.setScale(k >= 1 ? Math.floor(k) : Math.max(0.25, Math.floor(k * 4) / 4));
  } else {
    const q = new GlowText(sc, 0, 0, '?', 'page_faint', { scale: 2 });
    q.setPosition(Math.round(px + P / 2 - q.displayWidth / 2), Math.round(py + P / 2 - q.displayHeight / 2));
  }
  const tx = x + P + f * 2 + 2 + 12;
  const tw = w - (tx - x);
  let ty = y + 2;
  const lb = new GlowText(sc, tx, ty, labelOf(s.labels, 'killer'), 'page_faint');
  ty += lb.displayHeight + 2;
  const killerName = s.killer?.name || (s.killer ? l2eText('killerUnknown') : '');
  if (killerName) {
    const nm = new GlowText(sc, tx, ty, killerName, 'page_title', { wrap: tw, stageIndex: si });
    ty += nm.displayHeight + 4;
  }
  if (s.killerLine) new GlowText(sc, tx, ty, s.killerLine, 'page_body', { wrap: tw, stageIndex: si });
  return y + P + f * 2 + 2;
}

/** 칸 한 줄 (같은 폭으로 나눔) — 이름 흐림 · 값 제목. 아래 끝 y */
function statRow(sc: Phaser.Scene, cells: StatCell[], x: number, y: number, w: number, si: number): number {
  if (!cells.length) return y;
  const cw = Math.floor(w / cells.length);
  let h = 0;
  cells.forEach((c, i) => {
    const cx = x + i * cw;
    const lb = new GlowText(sc, cx, y, c.label, 'page_faint', { wrap: cw - 6 });
    const v = new GlowText(sc, cx, y + lb.displayHeight + 2, c.value, 'page_title', { stageIndex: si });
    h = Math.max(h, lb.displayHeight + 2 + v.displayHeight);
  });
  return y + h;
}

/** 칸 두 줄 격자 (층 끝) */
function statGrid(sc: Phaser.Scene, cells: StatCell[], x: number, y: number, w: number, si: number): number {
  const cols = 2;
  const cw = Math.floor(w / cols);
  let yy = y;
  for (let i = 0; i < cells.length; i += cols) {
    let h = 0;
    for (let k = 0; k < cols && i + k < cells.length; k++) {
      const c = cells[i + k];
      const cx = x + k * cw;
      const lb = new GlowText(sc, cx, yy, c.label, 'page_faint', { wrap: cw - 6 });
      const v = new GlowText(sc, cx, yy + lb.displayHeight + 1, c.value, 'page_title', { stageIndex: si });
      h = Math.max(h, lb.displayHeight + 1 + v.displayHeight);
    }
    yy += h + 6;
  }
  return yy;
}

/** 지닌 것: 이름 흐림 + 아이콘 줄(32, 그림 없으면 이름 한 자) · 마우스를 올리면 아래에 이름 */
function buildBlock(
  sc: Phaser.Scene,
  icons: readonly UiBuildIcon[],
  label: string,
  x: number,
  y: number,
  w: number,
  weapon: string | undefined,
  si: number,
): number {
  if (!icons.length) return y;
  new GlowText(sc, x, y, label, 'page_faint');
  y += 16;
  const per = Math.max(1, Math.floor((w + R.buildGap) / (R.buildCell + R.buildGap)));
  const { rows, more } = buildRows(icons, per, R.buildRows);
  const nameT = new GlowText(sc, x, 0, '', 'page_faint', { wrap: w });
  const wpn = (weapon && WEAPONS.includes(weapon) ? weapon : 'katana') as VoiceWeaponId;
  rows.forEach((row, ri) => {
    row.forEach((ic, ci) => {
      const cx = x + ci * (R.buildCell + R.buildGap);
      const cy = y + ri * (R.buildCell + R.buildGap);
      const color = ic.kind === 'trait' || ic.kind === 'aspect' ? weaponFrameColor(sc, wpn) : hexToNum(SEPIA[5]);
      const o = Math.round((R.buildCell - R.buildIcon) / 2);
      const art = traitIconBox(sc, ic.iconKey, cx + o, cy + o, R.buildIcon, color, 1, hexToNum(GRAY[1]));
      if (!art) {
        const g = sc.add.graphics();
        g.fillStyle(hexToNum(GRAY[1]), 1).fillRect(cx + o, cy + o, R.buildIcon, R.buildIcon);
        g.lineStyle(1, color, 1).strokeRect(cx + o - 0.5, cy + o - 0.5, R.buildIcon + 1, R.buildIcon + 1);
        const t = new GlowText(sc, 0, 0, [...ic.name][0] ?? '?', 'page_body', { stageIndex: si });
        t.setPosition(
          Math.round(cx + R.buildCell / 2 - t.displayWidth / 2),
          Math.round(cy + R.buildCell / 2 - t.displayHeight / 2),
        );
      }
      // 이름 보기 (버튼 규약: 투명 판이 입력을 받는다)
      const hit = sc.add.zone(cx, cy, R.buildCell, R.buildCell).setOrigin(0, 0).setInteractive();
      hit.on('pointerover', () => nameT.setText(ic.name));
      hit.on('pointerout', () => nameT.setText(''));
    });
  });
  let bottom = y + rows.length * (R.buildCell + R.buildGap);
  if (more > 0) {
    const last = rows[rows.length - 1];
    new GlowText(
      sc,
      x + last.length * (R.buildCell + R.buildGap) + 2,
      bottom - R.buildCell + 8,
      `+${more}`,
      'page_body',
      {
        stageIndex: si,
      },
    );
  }
  nameT.setY(bottom);
  bottom += 16;
  return bottom;
}

/** 지나온 길: 이름 흐림 + 미니맵 (종이 위 얇은 테). 아래 끝 y */
function mapBlock(
  sc: Phaser.Scene,
  s: UiRunSummary,
  label: string,
  x: number,
  y: number,
  w: number,
  h: number,
  si: number,
): number {
  new GlowText(sc, x, y, label, 'page_faint');
  y += 16;
  const g = sc.add.graphics();
  g.fillStyle(hexToNum(SEPIA[1]), 0.45).fillRect(x, y, w, h);
  g.lineStyle(1, hexToNum(SEPIA[3]), 1).strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  drawResultMap(sc, s.route, s.path, x, y, w, h, si);
  if (s.pathEmpty) {
    const t = new GlowText(sc, 0, 0, s.pathEmpty, 'page_faint', { wrap: w - 16, align: 'center' });
    t.placeCenter(x + w / 2, y + h - t.displayHeight - 6);
  }
  return y + h;
}

/** 61 P7 이름 번짐: 이름을 흐리게(허용 알파) 하고 오른쪽 아래로 흐린 사본을 겹친다 */
function smudgeName(sc: Phaser.Scene, name: GlowText, text: string, si: number): void {
  sc.tweens.add({ targets: name, alpha: R.smudgeAlpha, duration: R.smudgeInMs });
  for (const [dx, dy] of [
    [1, 1],
    [2, 2],
    [3, 1],
  ]) {
    const ghost = new GlowText(sc, name.x + dx, name.y + dy, text, 'page_faint', { stageIndex: si }).setAlpha(0);
    sc.tweens.add({ targets: ghost, alpha: 1, duration: R.smudgeInMs });
  }
}
