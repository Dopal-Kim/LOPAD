import Phaser from 'phaser';
import { GlowText, RING } from './glow';
import { type GaugeView, gaugeKey, maskEdges, partialPx } from './gaugeView';
import { swatch } from './StructureHud';
import { type R56TextKey, r56Text } from './text';
import { GRAY, WGAUGE, hexToNum } from './theme';

const DEFAULT_LABEL: Record<GaugeView['kind'], R56TextKey> = {
  kenki: 'gaugeKenki',
  grudge: 'gaugeGrudge',
  brand: 'gaugeBrand',
  breath: 'gaugeBreath',
};

/** 눈금 라벨: 시스템 `gauge.label`, 비면 기본 이름 (61라운드 전투 묶음도 쓴다) */
export function gaugeLabelText(v: Pick<GaugeView, 'kind' | 'label'>): string {
  return v.label || r56Text(DEFAULT_LABEL[v.kind]);
}

const EDGES = {
  kenki: maskEdges(WGAUGE.kenki.mask),
  brand: maskEdges(WGAUGE.brand.mask),
  breath: maskEdges(WGAUGE.breath.mask),
};

/**
 * 56라운드 무기 고유 자원 눈금 (계약 §13, 결정 Q13~Q20·Q58). HUD 2행 무기 이름 바로 오른쪽에 라벨 + 칸.
 * - 검기(kenki): 칼날 마름모 3칸, 아래에서 위로 차오름. 칸 색 재 → 호박 → 백열 (단마다 밝아짐)
 * - 울분(grudge): 이어진 3칸 막대, 왼쪽부터 차오름. 채움 색 = 지금 구간(1~33/34~66/67~100%)
 * - 낙인(brand): 셈 획 5개(가장 많이 쌓인 적의 스택). 최대면 전부 밝게
 * - 숨(breath): 방울 3칸, 아래에서 위로. 정밀 조준 중이면 밝은 강조 + '집중' 깜빡임
 * 가득이면 라벨이 ink_accent. Container 하나라 하단 묶음과 함께 setY 로 움직이고, 그로기 떨림은 setX 로.
 */
export class WeaponGaugeChip extends Phaser.GameObjects.Container {
  private label: GlowText;
  private stateText: GlowText;
  private g: Phaser.GameObjects.Graphics;
  private lastSig = '#init';
  /** 지금 보이는 폭: 라벨(줄였으면 생략)~마지막 칸·글 (보이지 않으면 0) */
  boxW = 0;
  /** 라벨까지 넣었을 때의 폭 (줄인 상태에서도 다시 펼칠지 판단용) */
  fullW = 0;

  constructor(scene: Phaser.Scene, x: number, y: number, stageIndex: number) {
    super(scene, x, y);
    this.label = new GlowText(scene, 0, 0, '', 'ink_faint', { stageIndex });
    this.stateText = new GlowText(scene, 0, 0, '', 'ink_accent', { stageIndex });
    this.g = scene.add.graphics();
    this.add([this.g, this.label, this.stateText]);
    scene.add.existing(this);
    this.setVisible(false);
  }

  setStageIndex(i: number): void {
    this.label.setStageIndex(i);
    this.stateText.setStageIndex(i);
    this.lastSig = '#stage';
  }

  /** compact = 자리가 모자라 라벨을 뺀다 (긴 무기·갈래 이름일 때 HUD 가 정한다) */
  render(v: GaugeView | null, si: number, now: number, compact = false): void {
    const blinkOn = Math.floor(now / WGAUGE.blinkMs) % 2 === 0;
    const sig = v ? `${si}|${gaugeKey(v)}|${v.focusing ? blinkOn : ''}|${compact ? 1 : 0}` : '';
    if (sig === this.lastSig) return;
    this.lastSig = sig;
    this.g.clear();
    if (!v) {
      this.setVisible(false);
      this.boxW = 0;
      this.fullW = 0;
      return;
    }
    this.setVisible(true);
    const text = gaugeLabelText(v);
    this.label.setText(text).setGlowStyle(v.full && WGAUGE.fullAccent ? 'ink_accent' : 'ink_faint');
    const labelW = this.label.textW > 0 ? this.label.textW + WGAUGE.gapLabel : 0;
    this.label.setVisible(!compact);
    let x = RING + (compact ? 0 : labelW);
    x = v.kind === 'grudge' ? this.drawGrudge(v, x, si) : this.drawMasks(v, x, si);
    if (v.focusing) {
      this.stateText
        .setVisible(true)
        .setText(r56Text('breathFocus'))
        .setX(x + WGAUGE.gapState - RING)
        .setAlpha(blinkOn ? 1 : 0.55);
      x = this.stateText.x + RING + this.stateText.textW;
    } else this.stateText.setVisible(false);
    this.boxW = x;
    this.fullW = x + (compact ? labelW : 0);
  }

  /** 꺼진 칸·켜진 칸 색 (마스크형) */
  private colors(v: GaugeView, k: number, si: number): number {
    if (v.kind === 'kenki') {
      const ref = WGAUGE.kenki.colors[Math.min(k, WGAUGE.kenki.colors.length - 1)];
      return swatch(this.scene, si, ref);
    }
    if (v.kind === 'brand') return swatch(this.scene, si, v.full ? WGAUGE.brand.full : WGAUGE.brand.on);
    return swatch(this.scene, si, v.focusing ? WGAUGE.breath.focus : WGAUGE.breath.on);
  }

  /** 마스크 칸 (검기 마름모·낙인 획·숨 방울). 부분 채움은 아래에서 위로. 끝 x 를 돌려준다 */
  private drawMasks(v: GaugeView, x0: number, si: number): number {
    const spec = v.kind === 'kenki' ? WGAUGE.kenki : v.kind === 'brand' ? WGAUGE.brand : WGAUGE.breath;
    const edges = EDGES[v.kind as keyof typeof EDGES];
    const mask = spec.mask;
    const h = mask.length;
    const w = mask[0].length;
    const top = WGAUGE.cellTop;
    const offEdge = hexToNum(GRAY[6]);
    const offIn = hexToNum(GRAY[3]);
    let x = x0;
    v.cells.forEach((fill, k) => {
      const litRows = partialPx(h, fill);
      const on = litRows > 0 ? this.colors(v, k, si) : 0;
      for (let yy = 0; yy < h; yy++) {
        const lit = yy >= h - litRows;
        for (let xx = 0; xx < w; xx++) {
          if (mask[yy][xx] === '.') continue;
          const c = lit ? on : edges[yy][xx] ? offEdge : offIn;
          this.g.fillStyle(c, 1).fillRect(x + xx, top + yy, 1, 1);
        }
      }
      x += w + spec.gap;
    });
    return x - spec.gap;
  }

  /** 울분: 이어진 3칸 막대, 왼쪽부터 채움. 끝 x 를 돌려준다 */
  private drawGrudge(v: GaugeView, x0: number, si: number): number {
    const s = WGAUGE.grudge;
    const ref = s.stageColors[Math.max(0, Math.min(s.stageColors.length - 1, Math.max(1, v.stage) - 1))];
    const on = swatch(this.scene, si, ref);
    const top = s.top;
    let x = x0;
    for (const fill of v.cells) {
      // 꺼진 칸: G06 테두리 + G03 안쪽
      this.g.fillStyle(hexToNum(GRAY[6]), 1).fillRect(x, top, s.w, s.h);
      this.g.fillStyle(hexToNum(GRAY[3]), 1).fillRect(x + 1, top + 1, s.w - 2, s.h - 2);
      const lw = partialPx(s.w, fill);
      if (lw > 0) this.g.fillStyle(on, 1).fillRect(x, top, lw, s.h);
      x += s.w + s.gap;
    }
    return x - s.gap;
  }
}
