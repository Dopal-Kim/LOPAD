import Phaser from 'phaser';
import type { UiMenu, UiMenuLine } from '../contract/ui';
import { cardPage, cardShell, type ShellSlot } from './cardShell';
import { choiceHint, choiceLines } from './choiceCardView';
import { CARD_ZOOM, cardIcon, cardIconH, cardZoom } from './cardZoom';
import { GlowText } from './glow';
import { weaponFrameColor } from './growthArt';
import { KIT, weaponIconKey } from './kit';
import type { CardPage, CardPageCtx } from './MenuCards';
import { menuHotkeys, splitLabel } from './menuView';
import { r60Text } from './text';
import { l2eText } from './textLoop2E';
import { GRAY, SEPIA, hexToNum } from './theme';
import { CHOICE_CARD } from './themeBuild';
import type { VoiceWeaponId } from './themeStory';

/** 카드 폭 (장 수별 — 다섯 장도 화면 안에) */
const PICK_W: Readonly<Record<number, number>> = { 1: 212, 2: 212, 3: 212, 4: 188, 5: 150 };
const PICK_GAP: Readonly<Record<number, number>> = { 1: 22, 2: 22, 3: 22, 4: 14, 5: 12 };
const GAP = { afterTab: 10, afterIcon: 0, afterName: 6, afterRule: 10 } as const;
const WEAPONS: readonly string[] = ['katana', 'greatsword', 'dagger', 'bow'];

/**
 * 62 루프 2 UI E (계약 C P1-8): 운명 공개 뒤 고르기 — 'aspect' 손이 기억한 모양(처음 모양 / 떠올린 모양) ·
 * 'keepsake' 지니고 태어날 소품(소품들 / 빈손). 메뉴 줄 `line.memory`(그림 `iconKey` · 이름 · 한 문장 · 수치 · 흐린 한 줄).
 * 개성 카드와 같은 껍데기(cardShell) · 고르기(CardRow — 입력은 UI D 몫 그대로). 수치·흐린 한 줄은 깔개 안 상세 칸에서만.
 * 그림이 없는 '처음 모양'은 무기 아이콘, '빈손'은 빈 칸. 화면을 넘으면 null(목록으로).
 */
export function showMemoryPicks(
  scene: Phaser.Scene,
  m: UiMenu,
  ctx: CardPageCtx,
  maxPageH: number,
  weapon?: string,
): CardPage | null {
  const C = CHOICE_CARD;
  const lines = choiceLines(m);
  const n = lines.length;
  if (n < 1 || n > 5) return null;
  const cw = PICK_W[n];
  const gap = PICK_GAP[n];
  const inner = cw - C.pad * 2;
  const rowW = n * cw + (n - 1) * gap;
  const hk = menuHotkeys(m.lines.map((l) => l.key));
  const hotkeyOf = (key: string): string => hk[m.lines.findIndex((l) => l.key === key)] || key;
  const nameScale: 1 | 2 = n >= 5 ? 1 : 2;
  const faces = lines.map((l) => face(scene, l, inner, nameScale, ctx.stageIndex));
  const iconH = cardIconH();
  const nameH = Math.max(...faces.map((f) => f.name.displayHeight));
  const ruleY = C.tabTop + C.tabH + GAP.afterTab + iconH + nameH + GAP.afterName;
  const lineY = ruleY + 4 + GAP.afterRule;
  const lineH = Math.max(0, ...faces.map((f) => f.line?.displayHeight ?? 0));
  const ch = Math.max(C.minH - 20, lineY + lineH + C.pad);
  const zoomH = CARD_ZOOM.gap + CARD_ZOOM.h;
  const page = cardPage(
    scene,
    m,
    ctx,
    { w: rowW + C.matPad * 2, h: ch + C.matPad * 2 + zoomH, pad: C.matPad },
    choiceHint(m, r60Text),
    maxPageH,
  );
  if (!page) {
    for (const f of faces) for (const o of [f.name, f.line]) o?.destroy();
    return null;
  }
  const zoom = cardZoom(scene, page.left + rowW / 2, page.top + ch + CARD_ZOOM.gap, rowW - C.pad * 2);
  const slots: ShellSlot[] = faces.map((f, i) => {
    const x = page.left + i * (cw + gap);
    const parts: Phaser.GameObjects.GameObject[] = [];
    const iy = C.tabTop + C.tabH + GAP.afterTab;
    parts.push(...pickArt(scene, f.l, cw / 2, iy, m.id, weapon));
    f.name.placeCenter(cw / 2, iy + iconH + Math.round((nameH - f.name.displayHeight) / 2));
    parts.push(f.name, scene.add.tileSprite(C.pad, ruleY, inner, 4, KIT.rule).setOrigin(0, 0));
    if (f.line) {
      f.line.placeCenter(cw / 2, lineY);
      parts.push(f.line);
    }
    const mem = f.l.memory;
    const z = { detail: mem?.detail ?? '', flavor: mem?.flavor ?? '' };
    return cardShell(
      scene,
      { ...C },
      x,
      page.top,
      cw,
      ch,
      {
        key: f.l.key,
        hotkey: hotkeyOf(f.l.key),
        enabled: f.l.enabled,
        head: headOf(m.id, f.l),
        headSlot: mem ? (m.id === 'aspect' ? 21 : 25) : C.kindSlotDefault,
        onPaint: (sel) => {
          f.name.setGlowStyle(!f.l.enabled ? 'page_faint' : sel ? 'page_selected' : 'page_unsel');
          if (sel) zoom.show(z);
        },
      },
      parts,
    );
  });
  return page.done(slots);
}

interface Face {
  l: UiMenuLine;
  name: GlowText;
  line: GlowText | null;
}

function face(scene: Phaser.Scene, l: UiMenuLine, inner: number, scale: 1 | 2, si: number): Face {
  const mem = l.memory;
  const name = new GlowText(scene, 0, 0, mem?.name || splitLabel(l).label, 'page_unsel', {
    scale,
    wrap: Math.floor(inner / scale),
    align: 'center',
    stageIndex: si,
  });
  const text = mem?.line || l.detail || '';
  const line = text
    ? new GlowText(scene, 0, 0, text, 'page_body', { wrap: inner, align: 'center', stageIndex: si })
    : null;
  return { l, name, line };
}

/** 머리표: 떠올린 기억 = 그 장 이름, 처음 모양 = '손이 기억한 모양', 빈손 = '빈손' */
function headOf(id: string, l: UiMenuLine): string {
  if (id === 'keepsake') return l.memory ? l2eText('keepsakeHead') : l2eText('emptyHand');
  return l2eText('aspectHead');
}

/** 카드 그림: 기억 그림 → (처음 모양) 무기 아이콘 → (빈손) 빈 칸 */
function pickArt(
  scene: Phaser.Scene,
  l: UiMenuLine,
  cx: number,
  y: number,
  menuId: string,
  weapon?: string,
): Phaser.GameObjects.GameObject[] {
  const mem = l.memory;
  const w = (mem?.weapon ?? weapon ?? '') as VoiceWeaponId;
  const color = WEAPONS.includes(w) ? weaponFrameColor(scene, w) : hexToNum(SEPIA[5]);
  const art = cardIcon(scene, mem?.iconKey, cx, y, mem?.kind === 'keepsake' ? hexToNum(SEPIA[5]) : color);
  if (art) return art;
  const g = scene.add.graphics();
  const s = CARD_ZOOM.icon;
  const o = CARD_ZOOM.iconFrame + 1;
  const x0 = Math.round(cx - s / 2);
  const y0 = y + o;
  g.fillStyle(hexToNum(GRAY[1]), 1).fillRect(x0, y0, s, s);
  if (menuId === 'keepsake' && !mem) {
    // 빈손: 점선 테
    g.fillStyle(hexToNum(SEPIA[4]), 1);
    for (let k = 0; k < s; k += 6) {
      g.fillRect(x0 + k, y0 - 2, 3, 1).fillRect(x0 + k, y0 + s + 1, 3, 1);
      g.fillRect(x0 - 2, y0 + k, 1, 3).fillRect(x0 + s + 1, y0 + k, 1, 3);
    }
    return [g];
  }
  g.lineStyle(2, color, 1).strokeRect(x0 - 1, y0 - 1, s + 2, s + 2);
  const key = WEAPONS.includes(w) ? weaponIconKey(w) : '';
  if (key && scene.textures.exists(key)) {
    const img = scene.add.image(cx, y0 + s / 2, key).setOrigin(0.5, 0.5);
    img.setScale(Math.max(1, Math.floor(s / Math.max(1, img.width, img.height))));
    return [g, img];
  }
  return [g];
}
