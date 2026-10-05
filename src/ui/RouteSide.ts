import Phaser from 'phaser';
import type { UiNodeType, UiRoute, UiRouteNode } from '../contract/ui';
import { intelLine, nodeInfoLines, rewardLegend } from './bundleView';
import { GlowText } from './glow';
import { NODE_ICON_SHEET, derivedTexture, ensureImage, keyartKey, keyartUrl, nodeIconKey, rule } from './kit';
import { regionArtKey } from './regionView';
import { makeGlyph, nodeStateName, nodeTypeName } from './routeGlyph';
import type { LateInsert } from './routeSheet';
import type { Area } from './routeView';
import { routeText } from './text';
import { r60Text } from './text';
import { SEPIA, SIDE_ART, hexToNum } from './theme';

export interface RouteSideOptions {
  stageIndex: number;
  shopName?: string;
  mode: 'choose' | 'view';
  late: LateInsert;
  alive: () => boolean;
  route: UiRoute;
}

/**
 * 노드 지도 오른쪽 위치 정보 칸 (49·50라운드, RouteMap 에서 분리 — 60라운드). 위에서부터:
 * 지금 있는 곳(지역·이름·종류·설명) / 괘선 / 살펴보는(고른) 곳(이름·'지역 · 종류 · 상태'·설명 + §14.5 보상·위험·접두어·
 * 이벤트 내용·도장·숨은 길 줄) / (60라운드) 보상 글리프 범례·산 지도 정보 / 범례 2열 × 3줄.
 * 뒤에는 지금 지역 키아트를 어둡게(50라운드).
 */
export class RouteSide {
  private lookTitle: GlowText;
  private selName: GlowText;
  private selMeta: GlowText;
  private selDesc: GlowText;
  private selInfo: GlowText;
  /** '살펴보는 곳' 줄이 넘지 말아야 할 아래 끝 (보상 범례·지도 정보·범례 위) */
  private infoBottom: number;

  constructor(
    private scene: Phaser.Scene,
    x: number,
    top: number,
    w: number,
    bottom: number,
    here: UiRouteNode | null,
    private opts: RouteSideOptions,
  ) {
    const si = opts.stageIndex;
    const useSheet = NODE_ICON_SHEET.available && scene.textures.exists(NODE_ICON_SHEET.key);
    const rowH = useSheet ? 34 : 22;
    // 60라운드: 범례 위 두 줄 (보상 글리프 범례 · 산 지도 정보) — 있을 때만
    const extras = [rewardLegend(opts.route.nodes), intelLine(opts.route.intel, r60Text)].filter(Boolean);
    const extraTexts = extras.map((t) => new GlowText(scene, x, 0, t, 'page_faint', { wrap: w }));
    const extraH = extraTexts.reduce((h, t) => h + t.displayHeight, 0);
    const ly0 = bottom - rowH * 3;
    const legendTop = ly0 - 8 - (extraH ? extraH + 6 : 0);
    this.infoBottom = legendTop - 4;
    // 50라운드: 범례 위까지 지금 지역 키아트를 어둡게 (글자보다 먼저 = 아래)
    this.drawSideArt(
      {
        x: x - SIDE_ART.padX,
        y: top - SIDE_ART.padY,
        w: w + SIDE_ART.padX * 2,
        h: legendTop - SIDE_ART.padY - (top - SIDE_ART.padY),
      },
      here?.region,
    );
    let y = top;
    const head = new GlowText(scene, x, y, routeText('hereTitle'), 'page_faint');
    y += head.displayHeight + 2;
    if (here) {
      if (here.region) {
        const reg = new GlowText(scene, x, y, here.region, 'page_title', { scale: 2, stageIndex: si });
        y += reg.displayHeight + 2;
      }
      const nm = new GlowText(
        scene,
        x,
        y,
        `${here.name} · ${nodeTypeName(here.type, opts.shopName)}`,
        here.region ? 'page_body' : 'page_title',
        { wrap: w, stageIndex: si },
      );
      y += nm.displayHeight + 2;
      if (here.desc) {
        const d = new GlowText(scene, x, y, here.desc, 'page_body', { wrap: w, stageIndex: si });
        y += d.displayHeight;
      }
    } else {
      const none = new GlowText(scene, x, y, '―', 'page_body', { stageIndex: si });
      y += none.displayHeight;
    }
    y += 6;
    rule(scene, x, y, w);
    y += 4 + 8;
    this.lookTitle = new GlowText(scene, x, y, '', 'page_faint');
    y += 16;
    this.selName = new GlowText(scene, x, y, '', 'page_selected', { wrap: w, stageIndex: si });
    this.selMeta = new GlowText(scene, x, y, '', 'page_body', { wrap: w, stageIndex: si });
    this.selDesc = new GlowText(scene, x, y, '', 'page_faint', { wrap: w });
    this.selInfo = new GlowText(scene, x, y, '', 'page_body', { wrap: w, stageIndex: si });

    // 보상 범례·지도 정보 (범례 괘선 위)
    let ey = ly0 - 8 - 6 - extraH;
    for (const t of extraTexts) {
      t.setY(ey);
      ey += t.displayHeight;
    }
    // 범례 (아래에 붙임): 2열 × 3줄, 아이콘 + 종류 이름
    const legend: UiNodeType[] = ['journey', 'battle', 'shop', 'rest', 'event', 'boss'];
    rule(scene, x, ly0 - 8, w);
    legend.forEach((t, i) => {
      const lx = x + (i % 2) * Math.floor(w / 2);
      const ly = ly0 + Math.floor(i / 2) * rowH;
      const iw = useSheet ? 32 : 16;
      if (useSheet) {
        const col = Math.max(0, NODE_ICON_SHEET.order.indexOf(t));
        scene.add.image(lx, ly, nodeIconKey(scene, si), col).setOrigin(0, 0);
      } else {
        const glyph = makeGlyph(scene, t, si) as Phaser.GameObjects.GameObject &
          Phaser.GameObjects.Components.Transform;
        glyph.setPosition(glyph.x + lx + 8, glyph.y + ly + 8);
      }
      new GlowText(scene, lx + iw + 4, ly + Math.round(iw / 2) - 8, nodeTypeName(t, opts.shopName), 'page_body', {
        stageIndex: si,
      });
    });
  }

  /** '살펴보는(고른) 곳': 지금 있는 곳과 같으면 비운다 */
  show(n: UiRouteNode | null, isCurrent: boolean): void {
    const showSel = Boolean(n) && !isCurrent;
    this.lookTitle.setText(showSel ? routeText(this.opts.mode === 'choose' ? 'pickTitle' : 'lookTitle') : '');
    if (n && showSel) {
      this.selName.setText(n.name);
      const meta = [n.region, nodeTypeName(n.type, this.opts.shopName), nodeStateName(n.state)].filter(Boolean);
      this.selMeta.setText(meta.join(' · ')).setY(this.selName.y + this.selName.displayHeight + 2);
      this.selDesc.setText(n.desc ?? '').setY(this.selMeta.y + this.selMeta.displayHeight + 2);
      const below = this.selDesc.y + (n.desc ? this.selDesc.displayHeight + 2 : 0);
      // §14.5 줄 — 범례 위를 넘으면 뒤에서부터 줄이고 '…'
      const lines = nodeInfoLines(n, r60Text);
      this.selInfo.setText(lines.join('\n')).setY(below);
      while (lines.length > 0 && below + this.selInfo.displayHeight > this.infoBottom) {
        lines.pop();
        this.selInfo.setText([...lines, '…'].join('\n'));
      }
    } else {
      this.selName.setText('');
      this.selMeta.setText('');
      this.selDesc.setText('');
      this.selInfo.setText('');
    }
  }

  /**
   * 50라운드: 칸 뒤 지금 지역 키아트 (가운데를 잘라 덮고 G00 α0.55 로 두 번 어둡게) + 테두리 S1.
   * 키아트가 없는 지역이면 그리지 않는다. 아직 안 읽었으면 읽기 시작하고 오면 테두리 아래에 끼운다.
   */
  private drawSideArt(rect: Area, region: string | undefined): void {
    const art = regionArtKey(region);
    if (!art) return;
    const scene = this.scene;
    const frame = scene.add.graphics();
    frame.lineStyle(1, hexToNum(SEPIA[1]), 1).strokeRect(rect.x + 0.5, rect.y + 0.5, rect.w - 1, rect.h - 1);
    const src = keyartKey(art);
    const place = (): void => {
      if (!this.opts.alive()) return;
      const key = derivedTexture(scene, src, rect.w, rect.h, 'cover', SIDE_ART.darken);
      if (!key) return;
      this.opts.late(scene.add.image(rect.x, rect.y, key).setOrigin(0, 0), frame, 'below');
    };
    if (scene.textures.exists(src)) place();
    else ensureImage(scene, src, keyartUrl(art), (ok) => ok && place());
  }
}
