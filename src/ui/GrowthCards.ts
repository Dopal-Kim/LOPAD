import Phaser from 'phaser';
import { UI_SCREEN, type UiMenu, type UiSnapshot } from '../contract/ui';
import { buildOf, tagFloor } from './buildView';
import { debugExpose } from './debug';
import { cardPage, cardShell, type ShellSlot } from './cardShell';
import { choiceHint } from './choiceCardView';
import { GlowText } from './glow';
import { diamond, lookImage, lookText, pairPips, scaledKey, traitIconCard, traitIconOuter } from './growthArt';
import {
  growthCardGap,
  growthCardW,
  growthCards,
  growthNameScale,
  guideText,
  iconWeapon,
  type GrowthCardData,
  type GuideKind,
} from './growthView';
import { KIT, paperPage } from './kit';
import { takeKey } from './keyGate';
import type { ChoiceGate } from './choiceGate';
import { keyTime, leftButton, pointerTime } from './choiceArm';
import type { CardPage, CardPageCtx } from './MenuCards';
import { swatch } from './StructureHud';
import { fill, growthText, r60Text } from './text';
import { GRAY, SEPIA, hexToNum } from './theme';
import { GROWTH_CARD as C, GROWTH_GUIDE as GD, RESONANCE_UI as RS, TRAIT_ICON as TI } from './themeGrowth';
import type { VoiceWeaponId } from './themeStory';
import { WEAPON_HUE } from './themeWeapon';

/** 62 P2-7 태그 칩 (높이·안 여백·칩 사이) */
const TAG_CHIP = { h: 16, padX: 4, gap: 6 } as const;

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
    floor: tagFloor(snap),
    build: buildOf(snap),
    tx: growthText,
  });
  if (data.length < 2) return null;
  const n = data.length;
  const cw = growthCardW(n);
  const gap = growthCardGap(n);
  const matW = n * cw + (n - 1) * gap + C.matPad * 2;
  // 화면에 들 때까지 조인다: 0 = 그대로 → 1 = 그림 칸 낮게·괘선·'2차 각성 길' 머리글 뺌 → 2 = 길 한 줄·태그도 뺌 (그래도 넘치면 목록)
  const tried: number[] = [];
  for (const lv of [0, 1, 2] as const) {
    const before = new Set(scene.children.list);
    const faces = data.map((d) =>
      cardFace(scene, d, cw, lv, iconWeapon(d.icon, snap.weapon?.name, snap.growth?.weaponName), growthNameScale(n)),
    );
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
      return finishCards(scene, page, faces, cw, ch, gap);
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
  gap: number,
): CardPage {
  const slots: ShellSlot[] = faces.map((f, i) =>
    cardShell(
      scene,
      C,
      page.left + i * (cw + gap),
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
function cardFace(
  scene: Phaser.Scene,
  d: GrowthCardData,
  cw: number,
  lv: 0 | 1 | 2,
  weapon: VoiceWeaponId,
  nameScale: 1 | 2 = 2,
): Face {
  const lookH = lv === 0 ? C.lookH : C.lookHCompact;
  const inner = cw - C.pad * 2;
  // 61 단계 6 (P14 §2): 키 밑줄·길 점·단련 눈금은 무기 색
  const hue = hexToNum(WEAPON_HUE[weapon].main);
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
  } else if (d.kind === 'trait') {
    // §18.1 카드 그림(64, 무기 빛 테두리) + 바뀌는 키 한 줄 — 그림이 없으면 지금처럼 큰 키 그림
    const outer = traitIconOuter(TI.size, TI.frame);
    const icon = traitIconCard(scene, d.icon, Math.round(cx - TI.size / 2), y + TI.frame + 1, weapon);
    if (icon) {
      parts.push(...icon);
      y += outer + TI.gapBelow;
      if (d.verb) y = keyRow(scene, g, parts, d.verb, cx, y, hue, inner);
    } else if (d.verb) y = bigKey(scene, g, parts, d.verb, cx, y, hue);
  }
  // ---- 이름
  const name = new GlowText(scene, 0, 0, d.name, 'page_unsel', {
    scale: nameScale,
    wrap: Math.floor(inner / nameScale),
    align: 'center',
  });
  add(name, GAP.afterName);
  // 각성 카드: 바뀌는 키 한 줄 ([키] '… 바뀜')
  if ((d.kind === 'awaken1' || d.kind === 'awaken2') && d.verb) y = keyRow(scene, g, parts, d.verb, cx, y, hue, inner);
  // ---- 괘선 · 한 줄
  // (조인 단계에서는 괘선을 빼고 한 줄 아래 틈을 줄인다)
  if (lv === 0) {
    const rule = scene.add.tileSprite(C.pad, y, inner, 4, KIT.rule).setOrigin(0, 0);
    parts.push(rule);
    y += 4 + GAP.afterRule;
  }
  if (d.line)
    add(new GlowText(scene, 0, 0, d.line, 'page_body', { wrap: inner, align: 'center' }), lv === 0 ? GAP.afterLine : 2);
  // (공명 힌트가 있는 카드는 태그를 힌트 둘째 줄 '돌파 짝 카드' 로 보이므로 태그 줄을 따로 두지 않는다)
  // 62 P2-7: 태그는 흐린 글 대신 잉크 칩(강조 글) + '공명까지 n장'
  if (d.tags.length && lv < 2 && !d.resonance)
    y = tagChips(scene, parts, d.tags, d.tagNeed, cx, y, inner) + GAP.afterLine;
  // ---- §18.1 공명 힌트: 이 카드가 같은 태그 짝을 맞춘다
  if (d.resonance) y = resonanceHint(scene, g, parts, d.resonance, cx, y, inner, lv);
  // ---- 1차 각성: 2차 길 미리보기
  if (d.kind === 'awaken1' && d.paths.length) {
    if (lv === 0) add(new GlowText(scene, 0, 0, growthText('pathsHead'), 'page_faint'), 2);
    else y += 2;
    for (const p of d.paths) {
      const pn = new GlowText(scene, C.pad + 10, y, p.name, 'page_body');
      diamond(g, C.pad + 4, y + Math.round(pn.displayHeight / 2), 3, hue, true);
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
      diamond(g, x0 + k * step, y + r, r, on ? hue : hexToNum(SEPIA[4]), on);
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
  hue: number,
): number {
  const k = scaledKey(scene, verb.key, C.keyScale);
  k.obj.setPosition(Math.round(cx - k.width / 2), y);
  parts.push(k.obj);
  y += k.height + 2;
  g.fillStyle(hue, 1).fillRect(Math.round(cx - k.width / 2), y, k.width, 2);
  y += 2 + 2;
  if (verb.name) {
    const t = new GlowText(scene, 0, 0, verb.name, 'page_faint').placeCenter(cx, y);
    parts.push(t);
    y += t.displayHeight;
  }
  return y + GAP.afterKey;
}

/**
 * 개성 카드 공명 힌트: 옅은 바탕 띠 안에 [◆◆] '이 카드로 「이름」 공명'(강조) / '연쇄 짝 카드'(흐림 — 태그 줄 대신이라
 * 조인 단계에서도 남긴다). 아래 끝 y
 */
function resonanceHint(
  scene: Phaser.Scene,
  g: Phaser.GameObjects.Graphics,
  parts: Phaser.GameObjects.GameObject[],
  r: { name: string; tag: string },
  cx: number,
  y: number,
  inner: number,
  lv: 0 | 1 | 2,
): number {
  const after = lv === 0 ? GAP.afterLine : 2;
  const pipsW = RS.pipR * 4 + RS.pipGap;
  const head = new GlowText(scene, 0, 0, fill(growthText('resHint'), { name: r.name }), 'page_selected', {
    wrap: inner - pipsW - 6 - RS.hintPad * 2,
    align: 'center',
  });
  const sub = r.tag ? new GlowText(scene, 0, 0, fill(growthText('resHintTag'), { tag: r.tag }), 'page_faint') : null;
  const h = RS.hintPad * 2 + head.displayHeight + (sub ? sub.displayHeight : 0);
  g.fillStyle(hexToNum(SEPIA[1]), 0.55).fillRect(C.pad, y, inner, h);
  const rowW = pipsW + 6 + head.displayWidth;
  const x0 = Math.round(cx - rowW / 2);
  const ty = y + RS.hintPad;
  pairPips(
    g,
    x0 + RS.pipR,
    ty + Math.round(Math.min(head.displayHeight, 16) / 2),
    2,
    2,
    RS.pipR,
    RS.pipGap,
    swatch(scene, 0, { slot: RS.onSlot }),
    swatch(scene, 0, { sepia: RS.offSepia }),
  );
  head.setPosition(x0 + pipsW + 6, ty);
  parts.push(head);
  if (sub) {
    sub.placeCenter(cx, ty + head.displayHeight);
    parts.push(sub);
  }
  return y + h + after;
}

/** 각성 카드: [키] '{동작} 바뀜' 한 줄 (키 아래 강조 밑줄). 아래 끝 y */
function keyRow(
  scene: Phaser.Scene,
  g: Phaser.GameObjects.Graphics,
  parts: Phaser.GameObjects.GameObject[],
  verb: { key: string; name: string },
  cx: number,
  y: number,
  hue: number,
  maxW = Infinity,
): number {
  const k = scaledKey(scene, verb.key, 1);
  const label = verb.name ? fill(growthText('changes'), { verb: verb.name }) : '';
  let t = label ? new GlowText(scene, 0, 0, label, 'page_body') : null;
  const w = k.width + (t ? 5 + t.displayWidth : 0);
  // 62 루프 2 UI E: 좁은 카드(4·5장)에서 한 줄에 안 들면 키 아래 줄에 가운데로 (넘침 방지)
  if (t && w > maxW) {
    t.destroy();
    t = new GlowText(scene, 0, 0, label, 'page_body', { wrap: maxW, align: 'center' });
    const x0 = Math.round(cx - k.width / 2);
    k.obj.setPosition(x0, y);
    parts.push(k.obj);
    g.fillStyle(hue, 1).fillRect(x0, y + k.height + 1, k.width, 2);
    t.placeCenter(cx, y + k.height + 4);
    parts.push(t);
    return y + k.height + 4 + t.displayHeight + GAP.afterKey;
  }
  const x0 = Math.round(cx - w / 2);
  k.obj.setPosition(x0, y);
  parts.push(k.obj);
  g.fillStyle(hue, 1).fillRect(x0, y + k.height + 1, k.width, 2);
  if (t) {
    t.setPosition(x0 + k.width + 5, y);
    parts.push(t);
  }
  return y + k.height + 3 + GAP.afterKey;
}

/**
 * 62 P2-7 태그 칩 줄: 태그마다 어두운 잉크 칩 + 강조 글, 그 뒤에 '공명까지 n장'(가장 적게 남은 태그 기준, 0 이면 생략).
 * 한 줄에 안 들면 '공명까지' 글은 다음 줄. 아래 끝 y 를 돌려준다.
 */
function tagChips(
  scene: Phaser.Scene,
  parts: Phaser.GameObjects.GameObject[],
  tags: string[],
  need: number[],
  cx: number,
  y: number,
  inner: number,
): number {
  const T = TAG_CHIP;
  const g = scene.add.graphics();
  parts.push(g);
  const texts = tags.map((t) => new GlowText(scene, 0, 0, t, 'ink_accent'));
  const left = need.filter((n) => n > 0);
  const needT = left.length
    ? new GlowText(scene, 0, 0, fill(growthText('tagNeed'), { n: Math.min(...left) }), 'page_body')
    : null;
  const chipsW = texts.reduce((w, t) => w + t.displayWidth + T.padX * 2, 0) + (texts.length - 1) * T.gap;
  const oneLine = needT ? chipsW + T.gap + needT.displayWidth <= inner : true;
  const rowW = oneLine && needT ? chipsW + T.gap + needT.displayWidth : chipsW;
  let x = Math.round(cx - rowW / 2);
  for (const t of texts) {
    const w = t.displayWidth + T.padX * 2;
    g.fillStyle(hexToNum(SEPIA[0]), 1).fillRect(x, y, w, T.h);
    g.fillStyle(hexToNum(GRAY[1]), 1).fillRect(x + 1, y + 1, w - 2, T.h - 2);
    g.fillStyle(swatch(scene, 0, { slot: 20 }), 1).fillRect(x + 1, y + T.h - 2, w - 2, 1);
    t.setPosition(x + T.padX, y + Math.round((T.h - t.displayHeight) / 2));
    parts.push(t);
    x += w + T.gap;
  }
  let bottom = y + T.h;
  if (needT) {
    if (oneLine) needT.setPosition(x, y + Math.round((T.h - needT.displayHeight) / 2));
    else {
      needT.placeCenter(cx, bottom + 2);
      bottom += 2 + needT.displayHeight;
    }
    parts.push(needT);
  }
  return bottom;
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
  /** 62 P2-8: 개성 발현 안내 그림 — 이번에 고를 개성 카드 그림(메뉴 줄 `trait.iconKey`)과 무기 (없으면 옛 마름모) */
  traitArt?: { icons: string[]; weapon: VoiceWeaponId },
  /** 62 루프 2 UI D: 무장 게이트 — 있으면 무장 전·열기 전부터 누르던 키·클릭으로는 닫지 않는다 (없으면 예전처럼 0.2초 뒤부터) */
  gate?: ChoiceGate,
): () => void {
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const text = guideText(kind, growthText);
  const inner = GD.w - GD.pad * 2;
  const before = new Set(scene.children.list);
  const title = new GlowText(scene, 0, 0, text.title, 'page_title', { scale: 2 });
  const lines = text.lines.map((l) => new GlowText(scene, 0, 0, l, 'page_body', { wrap: inner, align: 'center' }));
  const foot = new GlowText(scene, 0, 0, growthText('guideNext'), 'page_faint');
  const icons = kind === 'trait' ? (traitArt?.icons ?? []).filter((k) => scene.textures.exists(k)).slice(0, 3) : [];
  const outer = traitIconOuter(TI.size, TI.frame);
  // 62 P2-8: 개성 그림이 있으면 그림 칸을 카드 그림 줄 + 게이지 눈금 도해 높이로
  const artH = icons.length ? outer + GUIDE_ART.gaugeGap + GUIDE_ART.gaugeH : GD.artH;
  const h =
    GD.pad +
    title.displayHeight +
    8 +
    artH +
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
  art.fillStyle(hexToNum(SEPIA[1]), 0.55).fillRect(x + GD.pad, y, inner, artH);
  if (icons.length && traitArt) drawGuideTraitArt(scene, art, icons, traitArt.weapon, W / 2, y, outer);
  else {
    const img = lookImage(scene, look, W / 2, y, inner - 16, GD.artH);
    if (!img) {
      const r = GD.artR;
      const cy = y + Math.round(GD.artH / 2);
      diamond(art, W / 2, cy, r, swatch(scene, 0, { slot: kind === 'trait' ? 22 : 25 }), kind !== 'trait');
      diamond(art, W / 2, cy, r + 3, swatch(scene, 0, { slot: 20 }), false);
    }
  }
  y += artH + 8;
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
  const unhook = (): void => {
    scene.input.keyboard?.off('keydown', onKey);
    scene.input.off('pointerdown', onDown);
    scene.input.off('pointerup', onUp);
  };
  const close = (): void => {
    if (closed) return;
    closed = true;
    unhook();
    box.destroy();
    onDone();
  };
  const onKey = (e: KeyboardEvent): void => {
    if (e.repeat) return;
    if ((e.key === 'Enter' || e.key === ' ') && takeKey(e) && (!gate || gate.keyOk(e.code, keyTime(e), e.repeat)))
      close();
  };
  // 62 루프 2 UI D: 눌렀다 뗀 클릭만 (누름이 무장 뒤 새로 누른 것이어야)
  let pressed = false;
  const onDown = (p: Phaser.Input.Pointer): void => {
    pressed = leftButton(p) && (!gate || gate.pressOk(pointerTime(p)));
  };
  const onUp = (p: Phaser.Input.Pointer): void => {
    if (!leftButton(p)) return;
    const ok = pressed && (!gate || gate.releaseOk());
    pressed = false;
    gate?.pointerUp();
    if (ok) close();
  };
  const hook = (): void => {
    if (closed) return;
    scene.input.keyboard?.on('keydown', onKey);
    scene.input.on('pointerdown', onDown);
    scene.input.on('pointerup', onUp);
  };
  // 메뉴를 연 클릭·키가 그대로 넘어오지 않게: 게이트가 있으면 게이트가, 없으면 한 박자 뒤부터 받는다
  if (gate) hook();
  else scene.time.delayedCall(200, hook);
  // 바깥에서 치울 때 (메뉴가 바뀌거나 닫힘) — onDone 없이
  return () => {
    if (closed) return;
    closed = true;
    unhook();
    box.destroy();
  };
}

/** 62 P2-8 개성 안내 그림 배치 */
const GUIDE_ART = { gap: 10, gaugeGap: 6, gaugeH: 12, gaugeW: 200, tickR: 3 } as const;

/**
 * 62 P2-8 개성 발현 안내 그림: 이번에 고를 개성 카드 그림 줄(무기 빛 테두리) + 그 아래 각성 띠 도해
 * (띠가 첫 작은 눈금 ◇ 에 닿아 강조 — '여기서 고른다'). 빈 마름모 대신.
 */
function drawGuideTraitArt(
  scene: Phaser.Scene,
  g: Phaser.GameObjects.Graphics,
  icons: string[],
  weapon: VoiceWeaponId,
  cx: number,
  top: number,
  outer: number,
): void {
  const A = GUIDE_ART;
  const rowW = icons.length * outer + (icons.length - 1) * A.gap;
  let x = Math.round(cx - rowW / 2);
  for (const k of icons) {
    traitIconCard(scene, k, x + TI.frame + 1, top + TI.frame + 1, weapon);
    x += outer + A.gap;
  }
  const hue = hexToNum(WEAPON_HUE[weapon].main);
  const by = top + outer + A.gaugeGap + Math.round(A.gaugeH / 2) - 1;
  const bx = Math.round(cx - A.gaugeW / 2);
  const ticks = [0.3, 0.6, 1];
  g.fillStyle(hexToNum(GRAY[0]), 1).fillRect(bx - 1, by - 1, A.gaugeW + 2, 5);
  g.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(bx, by, A.gaugeW, 3);
  g.fillStyle(hue, 1).fillRect(bx, by, Math.round(A.gaugeW * ticks[0]), 3);
  ticks.forEach((t, i) => {
    const tx = bx + Math.round(A.gaugeW * t);
    const r = i === ticks.length - 1 ? A.tickR + 1 : A.tickR;
    diamond(g, tx, by + 1, r + 1, hexToNum(GRAY[0]), true);
    if (i === 0) diamond(g, tx, by + 1, r, swatch(scene, 0, { slot: 25 }), true);
    else diamond(g, tx, by + 1, r, hexToNum(SEPIA[4]), false);
  });
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

/** 62 P2-8: 개성 발현 안내에 넣을 그림 — 이 메뉴의 개성 카드 그림 키와 무기 */
export function guideTraitArt(m: UiMenu, snap: UiSnapshot): { icons: string[]; weapon: VoiceWeaponId } {
  const icons = m.lines
    .map((l) => (typeof l.trait?.iconKey === 'string' ? l.trait.iconKey : ''))
    .filter((k) => k.length > 0);
  return { icons, weapon: iconWeapon(icons[0] ?? null, snap.weapon?.name, snap.growth?.weaponName) };
}
