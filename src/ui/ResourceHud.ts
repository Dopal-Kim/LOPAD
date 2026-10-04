import Phaser from 'phaser';
import type { UiWeaponResource } from '../contract/ui';
import { GlowText } from './glow';
import { Gauge, accentHex } from './kit';
import type { GroggyView } from './gaugeView';
import { ammoCells, heatStage, resourceRatio, ringLit, ringPoints, shownValue } from './resourceView';
import { fill, r49Text, r56Text } from './text';
import { GRAY, GROGGY, RES, hexToNum } from './theme';

/** 화살 한 칸 5×11 (1 = 촉, 2 = 대, 3 = 깃) */
const ARROW = ['..1..', '.111.', '11111', '..2..', '..2..', '..2..', '..2..', '..2..', '.323.', '3.2.3', '3...3'];

/**
 * 49라운드 무기 자원 게이지 (계약 §11.1). HUD 하단 묶음 3행(무기 줄 아래)에 종류별 모양으로 그린다.
 * - stamina(칼·대검 기력): 막대. ok 층 강조 23 · low 강조 20 · exhausted 회색 띠 + '지침' 깜빡임
 * - ammo(활 화살): 화살 칸(찬 칸 촉 강조 22·대 G13·깃 G11, 빈 칸 G04). 장전 중이면 오른쪽 진행 링 + '장전'
 * - heat(단검 열기): 막대(1/3·2/3 눈금) + 단계 눈금 3칸(강조 20·22·25, 달아오를수록 밝게). overheat 면 막대 맥동 + 아래 냉각 진행선 + '과열'
 * 값이 null 이면 아무것도 그리지 않는다. 글은 Galmuri11 발광 규칙(ink_faint·ink_accent).
 * 56라운드 그로기(계약 §13, 칼·대검): 기력 막대 아래 2px 남은 시간선(강조 22, 오른쪽부터 줄어듦) + 상태 글 '그로기 1.2초' 깜빡임.
 */
export class ResourceGauge {
  private label: GlowText;
  private bar: Gauge;
  private heat: Gauge;
  private g: Phaser.GameObjects.Graphics;
  private valueText: GlowText;
  private stateText: GlowText;
  private lastKey = '';
  private ring = ringPoints(RES.ringR);

  constructor(
    private scene: Phaser.Scene,
    private x: number,
    private y: number,
  ) {
    this.label = new GlowText(scene, x, y - 3, '', 'ink_faint');
    this.bar = new Gauge(scene, x + RES.gaugeX - RES.labelX, y, RES.barW, 'gray');
    this.heat = new Gauge(scene, x + RES.gaugeX - RES.labelX, y, RES.heatW, 'gray');
    this.g = scene.add.graphics();
    this.valueText = new GlowText(scene, 0, y - 3, '', 'ink_faint');
    this.stateText = new GlowText(scene, 0, y - 3, '', 'ink_accent');
    this.hideAll();
  }

  /** 하단 묶음이 위아래로 움직일 때 */
  shiftY(dy: number): void {
    if (!dy) return;
    this.y += dy;
    this.label.setY(this.label.y + dy);
    this.valueText.setY(this.valueText.y + dy);
    this.stateText.setY(this.stateText.y + dy);
    this.bar.setPositionY(this.y);
    this.heat.setPositionY(this.y);
    // 다음 render 에서 다시 그리게 (Graphics 는 절대 좌표). null 이면 숨김으로 간다
    this.lastKey = '#moved';
  }

  private hideAll(): void {
    this.label.setVisible(false);
    this.bar.setVisible(false);
    this.heat.setVisible(false);
    this.g.clear();
    this.valueText.setVisible(false);
    this.stateText.setVisible(false);
  }

  render(res: UiWeaponResource | null, stageIndex: number, now: number, groggy: GroggyView | null = null): void {
    if (!res || !res.kind) {
      if (this.lastKey !== '') {
        this.lastKey = '';
        this.hideAll();
      }
      return;
    }
    const blinkOn = Math.floor(now / RES.blinkMs) % 2 === 0;
    // 56라운드: 그로기는 기력 막대에만 (칼·대검). 남은 시간선 폭이 바뀔 때만 다시 그린다
    const grog = res.kind === 'stamina' ? groggy : null;
    const needsBlink = res.state === 'overheat' || res.state === 'exhausted' || Boolean(grog);
    const key = [
      stageIndex,
      res.kind,
      res.label,
      res.value,
      res.max,
      res.state,
      res.progress ?? '',
      res.stage ?? '',
      needsBlink ? blinkOn : '',
      grog ? `${grog.seconds}:${Math.round(grog.ratio * (RES.barW - 4))}` : '',
    ].join('|');
    if (key === this.lastKey) return;
    this.lastKey = key;
    const si = stageIndex;
    for (const t of [this.label, this.valueText, this.stateText]) t.setStageIndex(si);
    this.label.setVisible(true).setText(res.label);
    const gx = this.x + RES.gaugeX - RES.labelX;
    this.g.clear();
    this.bar.setVisible(false);
    this.heat.setVisible(false);
    let endX: number;
    let state = '';
    if (res.kind === 'stamina') {
      const slot = res.state === 'exhausted' ? null : res.state === 'low' ? RES.staminaLow : RES.staminaOk;
      this.bar.setVisible(true).setFillSlot(this.scene, si, slot).set(resourceRatio(res));
      endX = gx + RES.barW;
      if (res.state === 'exhausted' || grog) {
        state = grog ? fill(r56Text('groggyLeft'), { s: grog.seconds }) : r49Text('resExhausted');
        this.bar.setAlpha(blinkOn ? 1 : 0.55);
      } else this.bar.setAlpha(1);
      if (grog) this.drawGroggyLine(gx, grog.ratio, si);
    } else if (res.kind === 'ammo') {
      endX = this.drawAmmo(res, gx, si);
      if (res.state === 'reloading') {
        endX = this.drawRing(endX + 6 + RES.ringR, this.y + 5, res.progress ?? 0, si) + 2;
        state = r49Text('resReloading');
      }
    } else {
      endX = this.drawHeat(res, gx, si, blinkOn);
      if (res.state === 'overheat') state = r49Text('resOverheat');
    }
    // 값 'n/m' (ink_faint) → 상태 글 (ink_accent, exhausted·overheat 는 깜빡임)
    this.valueText
      .setVisible(true)
      .setText(`${shownValue(res.value)}/${shownValue(res.max)}`)
      .setX(endX + 6);
    this.stateText
      .setVisible(Boolean(state))
      .setText(state)
      .setX(this.valueText.x + this.valueText.displayWidth + 4)
      .setAlpha(needsBlink && !blinkOn ? 0.55 : 1);
  }

  /** 56라운드 그로기 남은 시간선: 기력 막대 아래 2px, G03 바탕 위에 남은 만큼 강조 22 (왼쪽 고정, 오른쪽부터 줄어듦) */
  private drawGroggyLine(gx: number, ratio: number, si: number): void {
    const innerX = gx + 2;
    const innerW = RES.barW - 4;
    const y = this.y + GROGGY.lineDy;
    this.g.fillStyle(hexToNum(GRAY[3]), 1).fillRect(innerX, y, innerW, GROGGY.lineH);
    const w = Math.round(innerW * Math.max(0, Math.min(1, ratio)));
    if (w > 0)
      this.g.fillStyle(hexToNum(accentHex(this.scene, si, GROGGY.lineSlot)), 1).fillRect(innerX, y, w, GROGGY.lineH);
  }

  /** 화살 칸. 칸이 너무 많으면 막대로. 끝 x 를 돌려준다 */
  private drawAmmo(res: UiWeaponResource, gx: number, si: number): number {
    const cells = ammoCells(res.value, res.max, RES.arrowCap);
    if (cells.compact || cells.total === 0) {
      this.bar.setVisible(true).setFillSlot(this.scene, si, RES.arrowFull).setAlpha(1).set(resourceRatio(res));
      return gx + RES.barW;
    }
    const head = hexToNum(accentHex(this.scene, si, RES.arrowFull));
    const shaft = hexToNum(GRAY[13]);
    const fletch = hexToNum(GRAY[11]);
    const empty = hexToNum(GRAY[4]);
    const top = this.y - 1;
    for (let i = 0; i < cells.total; i++) {
      const ox = gx + i * (RES.arrowW + RES.arrowGap);
      const full = i < cells.filled;
      ARROW.forEach((row, yy) => {
        for (let xx = 0; xx < row.length; xx++) {
          const c = row[xx];
          if (c === '.') continue;
          const color = !full ? empty : c === '1' ? head : c === '2' ? shaft : fletch;
          this.g.fillStyle(color, 1).fillRect(ox + xx, top + yy, 1, 1);
        }
      });
    }
    return gx + cells.total * (RES.arrowW + RES.arrowGap) - RES.arrowGap;
  }

  /** 진행 링 (픽셀 원, 12시부터 시계 방향으로 켜짐). 끝 x 를 돌려준다 */
  private drawRing(cx: number, cy: number, progress: number, si: number): number {
    const lit = ringLit(this.ring.length, progress);
    const on = hexToNum(accentHex(this.scene, si, RES.ring));
    const off = hexToNum(GRAY[4]);
    this.ring.forEach((p, i) => this.g.fillStyle(i < lit ? on : off, 1).fillRect(cx + p.x, cy + p.y, 1, 1));
    return cx + RES.ringR;
  }

  /** 열기 막대 + 1/3·2/3 눈금 + 단계 눈금 3칸 (+ 과열 냉각선). 끝 x 를 돌려준다 */
  private drawHeat(res: UiWeaponResource, gx: number, si: number, blinkOn: boolean): number {
    const stage = heatStage(res, RES.heatStages);
    const over = res.state === 'overheat';
    const slot =
      stage <= 0 && !over
        ? null
        : RES.heatSlots[Math.max(0, Math.min(RES.heatSlots.length - 1, (over ? RES.heatStages : stage) - 1))];
    this.heat
      .setVisible(true)
      .setFillSlot(this.scene, si, slot)
      .set(over ? 1 : resourceRatio(res))
      .setAlpha(over && !blinkOn ? 0.55 : 1);
    // 막대 위 단계 눈금 (안쪽 1/3·2/3 지점, 1px G00)
    const innerX = gx + 2;
    const innerW = RES.heatW - 4;
    this.g.fillStyle(hexToNum(GRAY[0]), 1);
    for (let k = 1; k < RES.heatStages; k++)
      this.g.fillRect(innerX + Math.round((innerW * k) / RES.heatStages), this.y + 1, 1, 8);
    // 과열 냉각 진행선 (막대 아래 2px, 진행만큼 G11)
    if (over) {
      const p = Math.max(0, Math.min(1, res.progress ?? 0));
      this.g.fillStyle(hexToNum(GRAY[3]), 1).fillRect(innerX, this.y + 11, innerW, 2);
      const w = Math.round(innerW * p);
      if (w > 0) this.g.fillStyle(hexToNum(GRAY[11]), 1).fillRect(innerX, this.y + 11, w, 2);
    }
    // 단계 눈금 칸: 켜진 칸 = 그 단계 색, 꺼진 칸 = G03 바탕 + G06 테두리
    let x = gx + RES.heatW + 6;
    for (let k = 0; k < RES.heatStages; k++) {
      const lit = over || k < stage;
      const py = this.y + 2;
      if (lit)
        this.g.fillStyle(hexToNum(accentHex(this.scene, si, RES.heatSlots[k])), 1).fillRect(x, py, RES.pip, RES.pip);
      else {
        this.g.fillStyle(hexToNum(GRAY[6]), 1).fillRect(x, py, RES.pip, RES.pip);
        this.g.fillStyle(hexToNum(GRAY[3]), 1).fillRect(x + 1, py + 1, RES.pip - 2, RES.pip - 2);
      }
      x += RES.pip + RES.pipGap;
    }
    return x - RES.pipGap;
  }
}
