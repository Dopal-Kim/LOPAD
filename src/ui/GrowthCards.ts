import Phaser from 'phaser';
import { UI_SCREEN, type UiMenu, type UiSnapshot } from '../contract/ui';
import { buildOf } from './buildView';
import { debugExpose } from './debug';
import { cardPage, cardShell, type ShellSlot } from './cardShell';
import { choiceHint } from './choiceCardView';
import { GlowText } from './glow';
import { diamond, lookImage, lookText, scaledKey } from './growthArt';
import { growthCardW, growthCards, guideText, type GrowthCardData, type GuideKind } from './growthView';
import { KIT, paperPage } from './kit';
import { takeKey } from './keyGate';
import type { CardPage, CardPageCtx } from './MenuCards';
import { swatch } from './StructureHud';
import { fill, growthText, r60Text } from './text';
import { SEPIA, hexToNum } from './theme';
import { GROWTH_CARD as C, GROWTH_GUIDE as GD } from './themeGrowth';

/** 카드 안 줄 사이 */
const GAP = { afterTab: 8, afterLook: 6, afterKey: 6, afterName: 6, afterRule: 8, afterLine: 6 } as const;

/**
 * 61 단계 4 P12 무기 성장 선택 화면 (계약 §18, 메뉴 `evolve` 의 줄 kind `trait`·`awaken1`·`awaken2`·`temper`).
 * 일기장 한 쪽 위 잉크 깔개 + 종이 카드 2~3장(cardShell — 고르기·들림·흔들림은 3지선다 카드와 같다).
 *  - 개성 발현: 바뀌는 키 그림 2배(강조 밑줄) · 그 칸의 지금 동작 이름 · 이름 2배 · 괘선 · 한 문장 · 이 층에서 켜진 태그
 *  - 1차 각성: 무기 1차 모양 그림(없으면 무기 이름 글자) · 이름 2배 · [키] '… 바뀜' · 한 줄 양상 · 괘선 · 2차 각성 길 2개(이름·한 줄)
 *  - 2차 각성: 길 그림(빛 색 포함) · 이름 2배 · 한 줄
 *  - 단련: 이름 2배 · 괘선 · 설명 · 단련 눈금(마름모 n/최대)
 * 수치·내부 용어는 그리지 않는다(시스템 라벨 그대로). 화면을 넘으면 null(MenuScene 이 목록으로).
 */
export function showGrowthCards(
  scene: Phaser.Scene,
  m: UiMenu,
  snap: UiSnapshot,
  ctx: CardPageCtx,
  maxPageH: number,
): CardPage | null {
  const data = growthCards(m, {
    growth: snap.growth,
    verbs: snap.weaponVerbs,
    stageIndex: Math.max(0, snap.stageIndex),
    build: buildOf(snap),
    tx: growthText,
  });
  if (data.length < 2) return null;
  const n = data.length;
  const cw = growthCardW(n);
  const matW = n * cw + (n - 1) * C.gap + C.matPad * 2;
  // 화면에 들 때까지 조인다: 0 = 그대로 → 1 = 그림 칸 낮게·괘선·'2차 각성 길' 머리글 뺌 → 2 = 길 한 줄·태그도 뺌 (그래도 넘치면 목록)
  const tried: number[] = [];
  for (const lv of [0, 1, 2] as const) {
    const before = new Set(scene.children.list);
    const faces = data.map((d) => cardFace(scene, d, cw, lv));
    const ch = Math.max(C.minH, ...faces.map((f) => f.h));
    const page = cardPage(
      scene,
      m,
      ctx,
      { w: matW, h: ch + C.matPad * 2, pad: C.matPad },
      choiceHint(m, r60Text),
      maxPageH,
    );
    tried.push(ch);
    if (page) {
      debugExpose('growthCardFit', { level: lv, tried });
      return finishCards(scene, page, faces, cw, ch);
    }
    for (const o of scene.children.list.filter((x) => !before.has(x))) o.destroy();
    for (const f of faces) for (const o of f.parts) o.destroy();
  }
  debugExpose('growthCardFit', { level: -1, tried });
  return null;
}

function finishCards(
  scene: Phaser.Scene,
  page: NonNullable<ReturnType<typeof cardPage>>,
  faces: Face[],
  cw: number,
  ch: number,
): CardPage {
  const slots: ShellSlot[] = faces.map((f, i) =>
    cardShell(
      scene,
      C,
      page.left + i * (cw + C.gap),
      page.top,
      cw,
      ch,
      {
        key: f.d.key,
        hotkey: f.d.hotkey,
        enabled: f.d.enabled,
        head: f.d.head,
        headSlot: f.d.headSlot,
        onPaint: (sel) => f.name.setGlowStyle(!f.d.enabled ? 'page_faint' : sel ? 'page_selected' : 'page_unsel'),
      },
      f.parts,
    ),
  );
  return page.done(slots);
}

interface Face {
  d: GrowthCardData;
  name: GlowText;
  parts: Phaser.GameObjects.GameObject[];
  /** 내용 아래 끝 + 안쪽 여백 = 카드 높이 */
  h: number;
}

/** 카드 내용 (카드 왼쪽 위 기준 지역 좌표) */
function cardFace(scene: Phaser.Scene, d: GrowthCardData, cw: number, lv: 0 | 1 | 2): Face {
  const lookH = lv === 0 ? C.lookH : C.lookHCompact;
  const inner = cw - C.pad * 2;
  const cx = Math.round(cw / 2);
  const parts: Phaser.GameObjects.GameObject[] = [];
  const g = scene.add.graphics();
  parts.push(g);
  let y = C.tabTop + C.tabH + GAP.afterTab;
  const add = (t: GlowText, gap: number): void => {
    t.placeCenter(cx, y);
    parts.push(t);
    y += t.displayHeight + gap;
  };
  // ---- 위: 그림 (각성) 또는 큰 키 그림 (개성)
  if (d.kind === 'awaken1' || d.kind === 'awaken2') {
    g.fillStyle(hexToNum(SEPIA[1]), 0.55).fillRect(C.pad, y, inner, lookH);
    const img = lookImage(scene, d.look, cx, y, inner - 8, lookH);
    parts.push(img ?? lookText(scene, d.lookText || d.name, cx, y, lookH));
    y += lookH + GAP.afterLook;
  } else if (d.kind === 'trait' && d.verb) {
    y = bigKey(scene, g, parts, d.verb, cx, y);
  }
  // ---- 이름
  const name = new GlowText(scene, 0, 0, d.name, 'page_unsel', {
    scale: 2,
    wrap: Math.floor(inner / 2),
    align: 'center',
  });
  add(name, GAP.afterName);
  // 각성 카드: 바뀌는 키 한 줄 ([키] '… 바뀜')
  if ((d.kind === 'awaken1' || d.kind === 'awaken2') && d.verb) y = keyRow(scene, g, parts, d.verb, cx, y);
  // ---- 괘선 · 한 줄
  // (조인 단계에서는 괘선을 빼고 한 줄 아래 틈을 줄인다)
  if (lv === 0) {
    const rule = scene.add.tileSprite(C.pad, y, inner, 4, KIT.rule).setOrigin(0, 0);
    parts.push(rule);
    y += 4 + GAP.afterRule;
  }
  if (d.line)
    add(new GlowText(scene, 0, 0, d.line, 'page_body', { wrap: inner, align: 'center' }), lv === 0 ? GAP.afterLine : 2);
  if (d.tags.length && lv < 2)
    add(new GlowText(scene, 0, 0, d.tags.join(' · '), 'page_faint', { wrap: inner, align: 'center' }), GAP.afterLine);
  // ---- 1차 각성: 2차 길 미리보기
  if (d.kind === 'awaken1' && d.paths.length) {
    if (lv === 0) add(new GlowText(scene, 0, 0, growthText('pathsHead'), 'page_faint'), 2);
    else y += 2;
    for (const p of d.paths) {
      const pn = new GlowText(scene, C.pad + 10, y, p.name, 'page_body');
      diamond(g, C.pad + 4, y + Math.round(pn.displayHeight / 2), 3, swatch(scene, 0, { slot: C.pathDotSlot }), true);
      parts.push(pn);
      y += pn.displayHeight;
      if (p.line && lv < 2) {
        const pl = new GlowText(scene, C.pad + 10, y, p.line, 'page_faint', { wrap: inner - 10 });
        parts.push(pl);
        y += pl.displayHeight;
      }
      y += 2;
    }
  }
  // ---- 단련 눈금
  if (d.temper && d.temper.max > 0) {
    const r = C.pipR;
    const step = r * 2 + C.pipGap;
    const x0 = Math.round(cx - (d.temper.max * step - C.pipGap) / 2) + r;
    for (let k = 0; k < d.temper.max; k++) {
      const on = k < d.temper.n;
      diamond(g, x0 + k * step, y + r, r, on ? swatch(scene, 0, { slot: C.pipSlot }) : hexToNum(SEPIA[4]), on);
    }
    y += r * 2 + 1 + GAP.afterLine;
  }
  return { d, name, parts, h: y + C.pad };
}

/** 개성 카드 위: 키 그림 2배 + 강조 밑줄 + 그 칸의 지금 동작 이름(흐림). 아래 끝 y */
function bigKey(
  scene: Phaser.Scene,
  g: Phaser.GameObjects.Graphics,
  parts: Phaser.GameObjects.GameObject[],
  verb: { key: string; name: string },
  cx: number,
  y: number,
): number {
  const k = scaledKey(scene, verb.key, C.keyScale);
  k.obj.setPosition(Math.round(cx - k.width / 2), y);
  parts.push(k.obj);
  y += k.height + 2;
  g.fillStyle(swatch(scene, 0, { slot: C.keyLineSlot }), 1).fillRect(Math.round(cx - k.width / 2), y, k.width, 2);
  y += 2 + 2;
  if (verb.name) {
    const t = new GlowText(scene, 0, 0, verb.name, 'page_faint').placeCenter(cx, y);
    parts.push(t);
    y += t.displayHeight;
  }
  return y + GAP.afterKey;
}

/** 각성 카드: [키] '{동작} 바뀜' 한 줄 (키 아래 강조 밑줄). 아래 끝 y */
function keyRow(
  scene: Phaser.Scene,
  g: Phaser.GameObjects.Graphics,
  parts: Phaser.GameObjects.GameObject[],
  verb: { key: string; name: string },
  cx: number,
  y: number,
): number {
  const k = scaledKey(scene, verb.key, 1);
  const label = verb.name ? fill(growthText('changes'), { verb: verb.name }) : '';
  const t = label ? new GlowText(scene, 0, 0, label, 'page_body') : null;
  const w = k.width + (t ? 5 + t.displayWidth : 0);
  const x0 = Math.round(cx - w / 2);
  k.obj.setPosition(x0, y);
  parts.push(k.obj);
  g.fillStyle(swatch(scene, 0, { slot: C.keyLineSlot }), 1).fillRect(x0, y + k.height + 1, k.width, 2);
  if (t) {
    t.setPosition(x0 + k.width + 5, y);
    parts.push(t);
  }
  return y + k.height + 3 + GAP.afterKey;
}

/**
 * 처음 안내 카드 (계약 §18 `growth.firstTime` — 메타 기준 처음 개성 발현·1차·2차 각성 메뉴 앞에 한 장):
 * 종이 한 장 · 제목 · 그림(무기 모양, 없으면 큰 마름모 — ◇ 발현 / ◆ 각성) · 두 줄 · 'Enter · 클릭 — 고르러 간다'.
 * Enter·Space·클릭으로 닫고 `onDone`. 본 기록은 시스템 메타(메뉴가 닫힐 때 시스템이 적는다).
 */
export function showGrowthGuide(
  scene: Phaser.Scene,
  kind: GuideKind,
  look: string | null,
  onDone: () => void,
): () => void {
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const text = guideText(kind, growthText);
  const inner = GD.w - GD.pad * 2;
  const before = new Set(scene.children.list);
  const title = new GlowText(scene, 0, 0, text.title, 'page_title', { scale: 2 });
  const lines = text.lines.map((l) => new GlowText(scene, 0, 0, l, 'page_body', { wrap: inner, align: 'center' }));
  const foot = new GlowText(scene, 0, 0, growthText('guideNext'), 'page_faint');
  const h =
    GD.pad +
    title.displayHeight +
    8 +
    GD.artH +
    8 +
    lines.reduce((s, l) => s + l.displayHeight + GD.lineGap, 0) +
    6 +
    foot.displayHeight +
    GD.pad;
  const x = Math.round(W / 2 - GD.w / 2);
  const top = Math.round(H / 2 - h / 2);
  // 어둡게 덮고 종이 한 장
  const dim = scene.add.graphics();
  dim.fillStyle(0x000000, 0.55).fillRect(0, 0, W, H);
  paperPage(scene, x, top, GD.w, h, `guide:${kind}`);
  let y = top + GD.pad;
  title.placeCenter(W / 2, y);
  y += title.displayHeight + 8;
  const art = scene.add.graphics();
  art.fillStyle(hexToNum(SEPIA[1]), 0.55).fillRect(x + GD.pad, y, inner, GD.artH);
  const img = lookImage(scene, look, W / 2, y, inner - 16, GD.artH);
  if (!img) {
    const r = GD.artR;
    const cy = y + Math.round(GD.artH / 2);
    diamond(art, W / 2, cy, r, swatch(scene, 0, { slot: kind === 'trait' ? 22 : 25 }), kind !== 'trait');
    diamond(art, W / 2, cy, r + 3, swatch(scene, 0, { slot: 20 }), false);
  }
  y += GD.artH + 8;
  for (const l of lines) {
    l.placeCenter(W / 2, y);
    y += l.displayHeight + GD.lineGap;
  }
  foot.placeCenter(W / 2, y + 6);
  // 글은 종이·그림 위에 (글을 먼저 만들어 높이를 쟀으므로 그릇 안 순서를 다시 맞춘다)
  const texts: Phaser.GameObjects.GameObject[] = [title, ...lines, foot];
  const rest = scene.children.list.filter((o) => !before.has(o) && o !== dim && !texts.includes(o));
  const box = scene.add.container(0, 0, [dim, ...rest, ...texts]).setDepth(GD.depth);
  box.setAlpha(0);
  scene.tweens.add({ targets: box, alpha: 1, duration: 160 });
  let closed = false;
  const close = (): void => {
    if (closed) return;
    closed = true;
    scene.input.keyboard?.off('keydown', onKey);
    scene.input.off('pointerdown', onClick);
    box.destroy();
    onDone();
  };
  const onKey = (e: KeyboardEvent): void => {
    if (e.repeat) return;
    if ((e.key === 'Enter' || e.key === ' ') && takeKey(e)) close();
  };
  const onClick = (): void => close();
  // 메뉴를 연 클릭·키가 그대로 넘어오지 않게 한 박자 뒤부터 받는다
  scene.time.delayedCall(200, () => {
    if (closed) return;
    scene.input.keyboard?.on('keydown', onKey);
    scene.input.on('pointerdown', onClick);
  });
  // 바깥에서 치울 때 (메뉴가 바뀌거나 닫힘) — onDone 없이
  return () => {
    if (closed) return;
    closed = true;
    scene.input.keyboard?.off('keydown', onKey);
    scene.input.off('pointerdown', onClick);
    box.destroy();
  };
}

/** 안내 카드 그림: 1차 각성은 무기 기본 모양, 2차 각성은 고른 갈래 모양, 개성은 없음(마름모) */
export function guideLook(kind: GuideKind, snap: UiSnapshot): string | null {
  const g = snap.growth;
  if (!g) return null;
  if (kind === 'awaken1') return g.baseLookKey ?? null;
  if (kind === 'awaken2') return g.branches?.find((b) => b.id === g.branch)?.lookKey ?? g.baseLookKey ?? null;
  return null;
}

/** 이번 실행에서 이미 띄운 안내 (같은 메뉴가 다시 와도 두 번 띄우지 않는다 — 기록은 시스템 메타) */
const shownGuides = new Set<GuideKind>();
export function guideShown(kind: GuideKind): boolean {
  return shownGuides.has(kind);
}
export function markGuideShown(kind: GuideKind): void {
  shownGuides.add(kind);
}
