import Phaser from 'phaser';
import { UI_SCREEN, type UiSnapshot } from '../contract/ui';
import { consumableView } from './buildView';
import { CarryChip } from './CarryHud';
import { carryView } from './carryView';
import { bossLeft, combatRows, hpLow, personalityRatio, pickResources, type CombatRows } from './combatView';
import { ConsumableChip } from './ConsumableHud';
import { WeaponGaugeChip, gaugeLabelText } from './GaugeHud';
import { gaugeView, groggyShake, groggyView } from './gaugeView';
import { GlowText, RING } from './glow';
import { Gauge, ICON, NinePanel, WEAPON_ICON_IDS, icon, inkPanel, weaponIconKey } from './kit';
import { KeyCap } from './keycap';
import { ResourceGauge } from './ResourceHud';
import { swatch } from './StructureHud';
import { r60Text } from './text';
import { GROGGY, WGAUGE } from './theme';
import { COMBAT_HUD as C } from './themeR61';

/** 체력 막대(보스 틀) 높이 */
const HP_BAR_H = 14;
/** 아이콘 칸 (16) + 간격 */
const ICON_COL = 16 + C.iconGap;
/** 고유 자원 눈금 칩 안쪽 원점 (GaugeHud: 칸 시작 x = RING, 칸 위 y = WGAUGE.cellTop) */
const CHIP_ORIGIN = { x: RING, y: WGAUGE.cellTop } as const;

/**
 * 61라운드 P10 전투 HUD 다이어트 — 왼쪽 아래 전투 묶음 + 아래 가운데 보스 막대.
 * 처음 하는 사람이 한눈에 읽게 크게 보이는 것은 넷뿐: 체력 · 무기 고유 자원 하나 · 소모품(독주 Q · 소모품 칸 C) · 전표.
 *  1행 체력: 하트 + 굵은 막대(보스 틀 14px, 200) + 'n / m' (30% 이하면 강조색 깜빡임)
 *  2행 무기: 아이콘 + 고유 자원(라벨 + 눈금 2배) — 고유 자원이 없으면 무기 자원(기력·화살·열기) 막대. 오른쪽 끝 F 넣기/뽑기
 *  (보조 줄: 시스템 개편 중 자원이 둘 다 오면 무기 자원을 작게)
 *  아래 행: 독주 '2/3' [Q] · 소모품 병 [C] · 전표
 *  맨 아래 2px 개성 진행선 (수치는 Tab 빌드 보기·일기장)
 * 무기 이름·갈래·개성 수치·'우클릭 …' 은 HUD 에서 뺐다(Tab·일기장·키캡 안내). 무기 아이콘이 없는 무기만 이름을 흐리게.
 * 그로기(계약 §13)는 무기 아이콘·눈금 1px 떨림 + 기력 막대 남은 시간선(ResourceGauge).
 */
export class CombatHud {
  private glows: GlowText[] = [];
  private si: number;
  private panel: NinePanel;
  private w: number = C.minW;
  private h = 0;
  private top = 0;
  private rows!: CombatRows;
  private layoutSig = '';
  // 1행
  private hpIcon: Phaser.GameObjects.Image;
  private hpGauge: Gauge;
  private hpText: GlowText;
  // 2행
  private weaponIcon: Phaser.GameObjects.Image;
  private weaponName: GlowText;
  private gaugeLabel: GlowText;
  private gaugeChip: WeaponGaugeChip;
  private resource: ResourceGauge;
  private carry: CarryChip;
  // 아래 행
  private potionIcon: Phaser.GameObjects.Image;
  private potionText: GlowText;
  private potionKey: KeyCap;
  private consumable: ConsumableChip;
  private goldIcon: Phaser.GameObjects.Image;
  private goldText: GlowText;
  private line: Phaser.GameObjects.Graphics;
  // 보스
  private bossGauge: Gauge;
  private bossIcon: Phaser.GameObjects.Image;
  private bossName: GlowText;
  private bossX = 0;
  /** 이번 그로기의 전체 시간 (시작 때 본 가장 큰 leftMs, 끝나면 0) */
  private groggyTotal = 0;
  private lineSig = '';

  constructor(
    private scene: Phaser.Scene,
    stageIndex: number,
  ) {
    this.si = stageIndex;
    const x = C.left;
    this.panel = inkPanel(scene, x, 0, C.minW, 64);
    this.hpIcon = icon(scene, 0, 0, ICON.hp);
    this.hpGauge = new Gauge(scene, 0, 0, C.hpW, 'boss', stageIndex);
    this.hpText = this.glow('', 'ink_body');
    this.weaponIcon = scene.add.image(0, 0, '__DEFAULT').setOrigin(0, 0).setVisible(false);
    this.weaponName = this.glow('', 'ink_faint');
    this.gaugeLabel = this.glow('', 'ink_faint');
    this.gaugeChip = new WeaponGaugeChip(scene, 0, 0, stageIndex).setScale(C.gaugeScale);
    this.resource = new ResourceGauge(scene, x + C.padX + ICON_COL, 0);
    this.carry = new CarryChip(scene, 0, 0, stageIndex);
    this.potionIcon = icon(scene, 0, 0, ICON.potion);
    this.potionText = this.glow('', 'ink_body');
    this.potionKey = new KeyCap(scene, 0, 0, 'Q');
    this.consumable = new ConsumableChip(scene, 0, 0, stageIndex);
    this.goldIcon = icon(scene, 0, 0, ICON.gold);
    this.goldText = this.glow('', 'ink_body');
    this.line = scene.add.graphics();
    this.bossGauge = new Gauge(scene, 0, 0, C.bossW, 'boss', stageIndex).setVisible(false);
    this.bossIcon = icon(scene, 0, 0, ICON.boss).setVisible(false);
    this.bossName = this.glow('', 'ink_accent').setVisible(false);
    this.relayout({ big: false, sub: false });
  }

  /** 묶음 위 끝 y */
  get bundleTop(): number {
    return this.top;
  }

  /** 묶음 오른쪽 끝 x */
  get bundleRight(): number {
    return C.left + this.w;
  }

  /**
   * 가운데 아래 글(자막·완벽 성공 문구)을 놓을 아래 끝: 보스 이름 위, 그리고 왼쪽 묶음 위
   * (가운데 글이 넓으면 왼쪽 묶음과 가로로 겹칠 수 있어 묶음 위 끝보다 위에 둔다)
   */
  centerBottom(): number {
    const boss = this.bossName.visible ? this.bossName.y - 4 : UI_SCREEN.HEIGHT - C.bottom;
    return Math.min(boss, this.top - 6);
  }

  /** 보스 막대가 보이는가 (자막 위치) */
  get bossOn(): boolean {
    return this.bossName.visible;
  }

  setStageIndex(si: number): void {
    if (si === this.si) return;
    this.si = si;
    for (const t of this.glows) t.setStageIndex(si);
    this.hpGauge.setStage(this.scene, si);
    this.bossGauge.setStage(this.scene, si);
    this.gaugeChip.setStageIndex(si);
    this.carry.setStageIndex(si);
    this.consumable.setStageIndex(si);
    this.lineSig = '';
  }

  render(s: UiSnapshot, now: number): void {
    const si = this.si;
    const pick = pickResources(s.gauge, s.resource);
    const gv = pick.main === 'gauge' ? gaugeView(s.gauge) : null;
    this.relayout({ big: Boolean(gv), sub: pick.sub });
    const x = C.left + C.padX;
    const t = this.top;
    const r = this.rows;
    // ---- 1행 체력
    this.hpGauge.set(s.maxHp > 0 ? s.hp / s.maxHp : 0);
    const low = hpLow(s.hp, s.maxHp, C.hpLowRatio);
    const blinkOn = Math.floor(now / C.hpBlinkMs) % 2 === 0;
    this.hpText
      .setText(`${s.hp} / ${s.maxHp}`)
      .setGlowStyle(low ? 'ink_accent' : 'ink_body')
      .setAlpha(low && !blinkOn ? 0.55 : 1);
    let right = this.hpText.x + this.hpText.displayWidth;
    // ---- 2행 무기 + 고유 자원 하나
    const grog = this.groggyOf(s);
    const shake = grog ? groggyShake(now, GROGGY.shakeMs, GROGGY.shakeAmp) : 0;
    const wy = t + r.weapon + (gv ? 1 : 0);
    const hasIcon = this.renderWeaponIcon(s.weapon.name, x + shake, wy);
    let wx = x + ICON_COL;
    // 아이콘이 없는 무기만 이름 (흐림)
    this.weaponName.setVisible(!hasIcon).setText(hasIcon ? '' : s.weapon.name);
    if (!hasIcon && s.weapon.name) {
      this.weaponName.setPosition(x, wy + 1);
      wx = x + this.weaponName.displayWidth + 4;
    }
    let weaponEnd = wx;
    this.gaugeChip.render(gv, si, now, true);
    if (gv) {
      const label = gaugeLabelText(gv);
      this.gaugeLabel
        .setVisible(true)
        .setText(label)
        .setGlowStyle(gv.full ? 'ink_accent' : 'ink_faint')
        .setPosition(wx, wy + 1);
      const cx = this.gaugeLabel.x + this.gaugeLabel.displayWidth + 2;
      this.gaugeChip.setPosition(cx - CHIP_ORIGIN.x * C.gaugeScale + shake, wy - CHIP_ORIGIN.y * C.gaugeScale);
      weaponEnd = cx + this.gaugeChip.boxW * C.gaugeScale - CHIP_ORIGIN.x * C.gaugeScale;
    } else this.gaugeLabel.setVisible(false);
    // 무기 자원: 주인공 자원이면 2행, 고유 자원과 함께 오면 보조 줄
    const res = s.resource && s.resource.kind ? s.resource : null;
    const resRow = pick.main === 'resource' ? r.weapon : r.sub;
    if (res && resRow !== null) {
      this.resource.moveToY(t + resRow + 3);
      this.resource.render(res, si, now, grog);
      if (pick.main === 'resource') weaponEnd = this.resource.right;
      else right = Math.max(right, this.resource.right);
    } else this.resource.render(null, si, now);
    // F 넣기/뽑기: 무기 줄 오른쪽 끝
    const cv = carryView(s.carry);
    this.carry.render(cv);
    right = Math.max(right, weaponEnd + (cv ? C.slotGap + this.carry.boxW : 0));
    // ---- 아래 행: 독주 · 소모품 · 전표
    const sy = t + r.slots;
    this.potionIcon.setPosition(x, sy);
    this.potionText.setText(`${s.potions}/${s.potionMax}`).setPosition(x + ICON_COL, sy + 1);
    let px = this.potionText.x + this.potionText.displayWidth + 2;
    this.potionKey.setPosition(px, sy);
    px += this.potionKey.width + C.slotGap;
    const cview = consumableView(s.consumable, r60Text);
    this.consumable.render(cview, si);
    if (cview) {
      this.consumable.setPosition(px, sy);
      px += this.consumable.boxW + C.slotGap;
    }
    this.goldIcon.setPosition(px, sy);
    this.goldText.setText(String(s.gold)).setPosition(px + ICON_COL, sy + 1);
    right = Math.max(right, this.goldText.x + this.goldText.displayWidth);
    // ---- 폭: 가장 긴 줄 + 오른쪽 여백 (넣기/뽑기는 무기 줄 오른쪽 끝에 붙인다)
    const w = Math.max(C.minW, Math.ceil(right - C.left + C.padX));
    if (w !== this.w) {
      this.w = w;
      this.panel.resize(w, this.h);
      this.lineSig = '';
    }
    if (cv) this.carry.setPosition(C.left + this.w - C.padX - this.carry.boxW, t + r.weapon + (gv ? 1 : 0));
    this.drawPersonality(personalityRatio(s.weapon));
    this.renderBoss(s);
  }

  /** 막대·눈금이 2배인지, 보조 줄이 있는지로 행 높이가 바뀌면 묶음을 다시 놓는다 (아래 여백 고정, 위로 늘어난다) */
  private relayout(opts: { big: boolean; sub: boolean }): void {
    const sig = `${opts.big}|${opts.sub}`;
    if (sig === this.layoutSig) return;
    this.layoutSig = sig;
    this.rows = combatRows(C, opts);
    this.h = this.rows.h;
    this.top = UI_SCREEN.HEIGHT - C.bottom - this.h;
    const x = C.left + C.padX;
    const t = this.top;
    this.panel.resize(this.w, this.h).setPosition(C.left, t);
    this.hpIcon.setPosition(x, t + this.rows.hp);
    this.hpGauge.setPositionX(x + ICON_COL).setPositionY(t + this.rows.hp + 1);
    this.hpText.setPosition(x + ICON_COL + C.hpW + 6, t + this.rows.hp);
    this.lineSig = '';
  }

  /** 무기 아이콘 (이름 매핑 + 텍스처가 있을 때만). 있으면 true */
  private renderWeaponIcon(weaponName: string, x: number, y: number): boolean {
    const id = WEAPON_ICON_IDS[weaponName];
    const key = id ? weaponIconKey(id) : '';
    const has = Boolean(key) && this.scene.textures.exists(key);
    if (has && this.weaponIcon.texture.key !== key) this.weaponIcon.setTexture(key);
    this.weaponIcon.setVisible(has).setPosition(x, y);
    return has;
  }

  /** 그로기 표시 (계약 §13). 전체 시간은 이번 그로기에서 본 가장 큰 leftMs (끝나면 잊는다) */
  private groggyOf(s: UiSnapshot): ReturnType<typeof groggyView> {
    const g = s.groggy;
    if (!g || g.active !== true) {
      this.groggyTotal = 0;
      return null;
    }
    const left = Number.isFinite(g.leftMs) ? g.leftMs : 0;
    this.groggyTotal = Math.max(this.groggyTotal, left);
    return groggyView(g, this.groggyTotal || GROGGY.defaultMs);
  }

  /** 개성 진행선: 묶음 아래 안쪽 2px (G03 바탕 + 진행 G09, 가득이면 강조 22). 글 없음 */
  private drawPersonality(ratio: number): void {
    const x0 = C.left + C.padX;
    const iw = this.w - C.padX * 2;
    const fw = Math.round(iw * ratio);
    const sig = `${this.top}|${this.w}|${fw}|${this.si}`;
    if (sig === this.lineSig) return;
    this.lineSig = sig;
    const y = this.top + this.h - C.personalityInset - C.personalityH;
    const g = this.line.clear();
    g.fillStyle(swatch(this.scene, this.si, C.personalityOff), 1).fillRect(x0, y, iw, C.personalityH);
    if (fw > 0)
      g.fillStyle(swatch(this.scene, this.si, ratio >= 1 ? C.personalityFull : C.personalityOn), 1).fillRect(
        x0,
        y,
        fw,
        C.personalityH,
      );
  }

  /** 보스 막대: 아래 가운데(왼쪽 묶음과 겹치면 비킴), 이름 · 페이즈는 위 (처치 뒤 hp 0 으로 남는 동안 숨김) */
  private renderBoss(s: UiSnapshot): void {
    const on = Boolean(s.boss && s.boss.hp > 0);
    this.bossGauge.setVisible(on);
    this.bossIcon.setVisible(on);
    this.bossName.setVisible(on);
    if (!on || !s.boss) return;
    const bx = bossLeft(UI_SCREEN.WIDTH, C.bossW, this.bundleRight, C.bossGap);
    const by = UI_SCREEN.HEIGHT - C.bottom - HP_BAR_H;
    if (bx !== this.bossX) {
      this.bossX = bx;
      this.bossGauge.setPositionX(bx);
    }
    this.bossGauge.setPositionY(by).set(s.boss.maxHp > 0 ? s.boss.hp / s.boss.maxHp : 0);
    this.bossIcon.setPosition(bx - 22, by - 1);
    this.bossName.setText(`${s.boss.name}  페이즈 ${s.boss.phase}`).placeCenter(bx + C.bossW / 2, by - 18);
  }

  private glow(text: string, style: Parameters<GlowText['setGlowStyle']>[0]): GlowText {
    const t = new GlowText(this.scene, 0, 0, text, style, { stageIndex: this.si });
    this.glows.push(t);
    return t;
  }
}
