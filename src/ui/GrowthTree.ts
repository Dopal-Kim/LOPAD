import Phaser from 'phaser';
import type { UiBuildState, UiGrowth, UiWeaponVerbs } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { diamond, pairPips, scaledKey, traitIconBox, traitIconOuter, weaponFrameColor } from './growthArt';
import {
  gaugeLayout,
  iconWeapon,
  remainText,
  resonanceProgress,
  resonanceRows,
  traitIcon,
  treeNodes,
  verbKey,
  type TreeState,
} from './growthView';
import { swatch } from './StructureHud';
import { fill, growthText } from './text';
import { GRAY, hexToNum } from './theme';
import { GROWTH_TREE as T, RESONANCE_UI as RS, TRAIT_ICON as TI } from './themeGrowth';
import { WEAPON_HUE } from './themeWeapon';
import { voiceWeapon } from './storyView';

/**
 * 61 단계 4 P12 Tab 성장도 (빌드 보기 왼쪽 장 안, 옛 '개성 n/m' 막대 대체):
 * '각성 게이지 124 · 1차 각성까지 40' / 나무(기본 → 갈래 3 → 길 6 — 지나온 길 강조, 다음에 고를 것 또렷, 닫힌 것 흐림) /
 * '얻은 개성' — 키 그림 + 이름 (넘치면 '외 n'; §18.1 카드 그림이 있는 개성은 그림 32 · 무기 빛 테두리 + 이름 / 키) /
 * '공명' — 짝 마름모 · 이름 · 진행('연쇄 1/2', 켜진 것은 '켜짐' + 한 문장, 켜진 것 먼저).
 * (x, y) 왼쪽 위, 폭 w. 만든 것과 높이를 돌려준다 (BuildPeek 이 그릇에 담는다).
 */
/** 목록 그림 칸 바깥 테두리 두께 (테두리 + G00 한 줄) */
const T_ICON_O = TI.thumbFrame + 1;

export interface GrowthTreeOpts {
  weaponName?: string;
  build?: UiBuildState | null;
  /**
   * 높이 상한 — 넘치면 접는다: 1 = 켜진 공명의 한 문장 뺌 → 2 = 공명 그림 대신 마름모 → 3 = 개성 그림 대신 키캡 줄
   * (그래도 넘치면 그대로)
   */
  maxH?: number;
}

export function growthTree(
  scene: Phaser.Scene,
  g: UiGrowth,
  verbs: UiWeaponVerbs | null | undefined,
  x: number,
  y: number,
  w: number,
  opts: GrowthTreeOpts = {},
): { objects: Phaser.GameObjects.GameObject[]; h: number } {
  let out = drawTree(scene, g, verbs, x, y, w, opts, 0);
  let used = 0;
  for (const lv of [1, 2, 3] as const) {
    if (opts.maxH === undefined || out.h <= opts.maxH) break;
    for (const o of out.objects) o.destroy();
    out = drawTree(scene, g, verbs, x, y, w, opts, lv);
    used = lv;
  }
  debugExpose('growthTreeFit', { level: used, h: out.h, maxH: opts.maxH ?? null });
  return out;
}

function drawTree(
  scene: Phaser.Scene,
  g: UiGrowth,
  verbs: UiWeaponVerbs | null | undefined,
  x: number,
  y: number,
  w: number,
  opts: GrowthTreeOpts,
  lv: 0 | 1 | 2 | 3,
): { objects: Phaser.GameObjects.GameObject[]; h: number } {
  const objs: Phaser.GameObjects.GameObject[] = [];
  const y0 = y;
  // ---- 머리글 · 게이지 한 줄
  const title = new GlowText(scene, x, y, growthText('treeTitle'), 'page_faint');
  objs.push(title);
  y += title.displayHeight;
  const remain = gaugeLayout(g, 100).remain;
  const head = new GlowText(
    scene,
    x,
    y,
    `${fill(growthText('treeGauge'), { n: Math.floor(g.gauge) })} · ${remainText(remain, growthText)}`,
    'page_body',
    { wrap: w },
  );
  objs.push(head);
  y += head.displayHeight + 6;
  // ---- 나무
  const tree = treeNodes(g, T.rowH, growthText('treeBase'));
  const lines = scene.add.graphics();
  const dots = scene.add.graphics();
  objs.push(lines, dots);
  // 61 단계 6 (P14 §2): 지나온 길(밝힌 줄·점)은 무기 색
  const litHue = hexToNum(WEAPON_HUE[voiceWeapon(opts.weaponName, g.weaponName)].main);
  const color = (st: TreeState): number =>
    st === 'lit' ? litHue : swatch(scene, 0, { sepia: st === 'open' ? T.openSepia : T.shutSepia });
  const byId = new Map(tree.nodes.map((n) => [n.id, n]));
  const nx = (col: number): number => x + T.dotR + (T.colX[col] ?? 0);
  for (const n of tree.nodes) {
    const p = n.parent ? byId.get(n.parent) : undefined;
    if (!p) continue;
    // 꺾은 선: 부모 점 오른쪽 → 자식 열 바로 앞 세로 → 자식 점 왼쪽 (부모 이름 글을 가로지르지 않게)
    const lit = n.state === 'lit' && p.state === 'lit';
    const c = lit ? color('lit') : color(n.state === 'open' ? 'open' : 'shut');
    const midX = nx(n.col) - T.elbow;
    lines.lineStyle(lit ? 2 : 1, c, 1);
    lines.lineBetween(nx(p.col) + T.dotR + 1, y + p.y, midX, y + p.y);
    lines.lineBetween(midX, y + p.y, midX, y + n.y);
    lines.lineBetween(midX, y + n.y, nx(n.col) - T.dotR - 1, y + n.y);
  }
  for (const n of tree.nodes) {
    const cx = nx(n.col);
    const cy = y + n.y;
    diamond(dots, cx, cy, T.dotR + (n.col === 0 ? 1 : 0), color(n.state), n.state === 'lit');
    const style = n.state === 'lit' ? 'page_selected' : n.state === 'open' ? 'page_body' : 'page_faint';
    const label = new GlowText(scene, cx + T.dotR + 3, 0, n.name, style);
    label.setY(Math.round(cy - label.displayHeight / 2));
    objs.push(label);
  }
  y += tree.h + 8;
  // ---- 얻은 개성
  const th = new GlowText(scene, x, y, growthText('traitsHead'), 'page_faint');
  objs.push(th);
  y += th.displayHeight + 2;
  const traits = g.traits ?? [];
  if (!traits.length) {
    const none = new GlowText(scene, x + 4, y, growthText('traitsNone'), 'page_faint');
    objs.push(none);
    y += none.displayHeight;
  }
  const icons = traits.map((t) => {
    const k = traitIcon(t);
    return lv < 3 && k && scene.textures.exists(k) ? k : null;
  });
  const max = icons.some(Boolean) ? T.traitIconMax : T.traitMax;
  const shown = traits.length > max ? traits.slice(0, max - 1) : traits;
  if (icons.some(Boolean)) y = traitGrid(scene, objs, shown, icons, verbs, x, y, w, opts, g.weaponName);
  else
    for (const t of shown) {
      const vk = verbKey(t.verb, verbs);
      let tx = x + 4;
      if (vk) {
        const k = scaledKey(scene, vk.key, 1);
        k.obj.setPosition(tx, y);
        objs.push(k.obj);
        tx += k.width + 5;
      }
      const name = new GlowText(scene, tx, y, t.name, 'page_body', { wrap: Math.max(40, x + w - tx) });
      objs.push(name);
      y += Math.max(T.traitRowH, name.displayHeight + 2);
    }
  if (shown.length < traits.length) {
    const more = new GlowText(
      scene,
      x + 4,
      y,
      fill(growthText('traitsMore'), { n: traits.length - shown.length }),
      'page_faint',
    );
    objs.push(more);
    y += more.displayHeight;
  }
  // ---- §18.1 공명 (이 무기의 공명 2~3개 — 켜진 것 강조, 꺼진 것은 진행)
  const res = resonanceRows(g, opts.build);
  if (res.length) {
    y += 6;
    const rh = new GlowText(scene, x, y, growthText('resHead'), 'page_faint');
    objs.push(rh);
    y += rh.displayHeight + 2;
    const pips = scene.add.graphics();
    objs.push(pips);
    const on = swatch(scene, 0, { slot: RS.onSlot });
    const have = swatch(scene, 0, { slot: RS.haveSlot });
    const off = swatch(scene, 0, { sepia: RS.offSepia });
    for (const r of res) {
      // 켜진 공명은 그림(32 · 무기 빛 테두리)이 있으면 마름모 대신 그림 — 오른쪽에 이름 · 켜짐 / 한 문장
      const art = r.active && lv < 2 && r.icon && scene.textures.exists(r.icon) ? r.icon : null;
      const y1 = y;
      let tx: number;
      if (art) {
        const box = traitIconBox(
          scene,
          art,
          x + 4 + T_ICON_O,
          y + T_ICON_O,
          TI.thumb,
          weaponFrameColor(scene, iconWeapon(art, opts.weaponName, g.weaponName)),
          TI.thumbFrame,
          hexToNum(GRAY[TI.backGray]),
        );
        if (box) objs.push(...box);
        tx = x + 4 + traitIconOuter(TI.thumb, TI.thumbFrame) + 5;
        y += 1;
      } else {
        const endX = pairPips(
          pips,
          x + 4 + RS.pipR,
          y + 8,
          r.have,
          r.need,
          RS.pipR,
          RS.pipGap,
          r.active ? on : have,
          off,
        );
        tx = endX + RS.pipR + 4;
      }
      const style = r.active ? 'page_selected' : r.have > 0 ? 'page_body' : 'page_faint';
      const name = new GlowText(scene, tx, y, r.name, style);
      const prog = new GlowText(scene, tx + name.displayWidth + 6, y, resonanceProgress(r, growthText), 'page_faint');
      objs.push(name, prog);
      y += Math.max(RS.rowH, name.displayHeight);
      if (r.active && r.line && lv < 1) {
        const line = new GlowText(scene, tx, y, r.line, 'page_body', { wrap: Math.max(40, x + w - tx) });
        objs.push(line);
        y += line.displayHeight + 2;
      }
      if (art) y = Math.max(y, y1 + T.traitIconRowH);
    }
  }
  return { objects: objs, h: y - y0 };
}

/**
 * §18.1 그림이 있는 얻은 개성: 두 칸 격자 — 칸마다 그림 32(무기 빛 테두리 1, 그림이 없는 개성은 키캡) · 오른쪽에 이름 /
 * (이름이 한 줄이면) [키]. 아래 끝 y
 */
function traitGrid(
  scene: Phaser.Scene,
  objs: Phaser.GameObjects.GameObject[],
  traits: readonly UiGrowth['traits'][number][],
  icons: readonly (string | null)[],
  verbs: UiWeaponVerbs | null | undefined,
  x: number,
  y: number,
  w: number,
  opts: GrowthTreeOpts,
  weaponName: string,
): number {
  const colW = Math.floor((w - 4) / 2);
  const outer = traitIconOuter(TI.thumb, TI.thumbFrame);
  let rowH = 0;
  traits.forEach((t, i) => {
    const col = i % 2;
    if (col === 0 && i > 0) {
      y += rowH + T.traitGridGap;
      rowH = 0;
    }
    const cx = x + 4 + col * colW;
    const vk = verbKey(t.verb, verbs);
    const icon = icons[i];
    let tx = cx + outer + 5;
    let showKey = Boolean(vk);
    if (icon) {
      const box = traitIconBox(
        scene,
        icon,
        cx + T_ICON_O,
        y + T_ICON_O,
        TI.thumb,
        weaponFrameColor(scene, iconWeapon(icon, opts.weaponName, weaponName)),
        TI.thumbFrame,
        hexToNum(GRAY[TI.backGray]),
      );
      if (box) objs.push(...box);
    } else if (vk) {
      // 그림이 없는 개성: 그림 칸 자리에 키캡
      const k = scaledKey(scene, vk.key, 1);
      k.obj.setPosition(cx, y + Math.round((outer - k.height) / 2));
      objs.push(k.obj);
      tx = cx + Math.max(outer, k.width) + 5;
      showKey = false;
    }
    const name = new GlowText(scene, tx, y + 1, t.name, 'page_body', { wrap: Math.max(40, cx + colW - 4 - tx) });
    objs.push(name);
    let h = 1 + name.displayHeight;
    if (showKey && vk && name.displayHeight <= 18) {
      const k = scaledKey(scene, vk.key, 1);
      k.obj.setPosition(tx, y + h);
      objs.push(k.obj);
      h += k.height;
    }
    rowH = Math.max(rowH, outer, h);
  });
  return y + rowH + 2;
}
