import Phaser from 'phaser';
import type { UiGrowth, UiWeaponVerbs } from '../contract/ui';
import { GlowText } from './glow';
import { diamond, scaledKey } from './growthArt';
import { gaugeLayout, remainText, treeNodes, verbKey, type TreeState } from './growthView';
import { swatch } from './StructureHud';
import { fill, growthText } from './text';
import { GROWTH_TREE as T } from './themeGrowth';

/**
 * 61 단계 4 P12 Tab 성장도 (빌드 보기 왼쪽 장 안, 옛 '개성 n/m' 막대 대체):
 * '각성 게이지 124 · 1차 각성까지 40' / 나무(기본 → 갈래 3 → 길 6 — 지나온 길 강조, 다음에 고를 것 또렷, 닫힌 것 흐림) /
 * '얻은 개성' — 키 그림 + 이름 (넘치면 '외 n').
 * (x, y) 왼쪽 위, 폭 w. 만든 것과 높이를 돌려준다 (BuildPeek 이 그릇에 담는다).
 */
export function growthTree(
  scene: Phaser.Scene,
  g: UiGrowth,
  verbs: UiWeaponVerbs | null | undefined,
  x: number,
  y: number,
  w: number,
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
  const color = (st: TreeState): number =>
    st === 'lit'
      ? swatch(scene, 0, { slot: T.litSlot })
      : swatch(scene, 0, { sepia: st === 'open' ? T.openSepia : T.shutSepia });
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
  const shown = traits.length > T.traitMax ? traits.slice(0, T.traitMax - 1) : traits;
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
  return { objects: objs, h: y - y0 };
}
