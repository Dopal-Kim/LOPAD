import Phaser from 'phaser';
import { UI_SCREEN, type UiBuildState, type UiTagState } from '../contract/ui';
import { curseLeft, hudTags, stagePips, tagChipValue } from './buildView';
import { GlowText } from './glow';
import { NinePanel, accentHex, inkPanel } from './kit';
import { pixelDiamond, diamondRing } from './routeGlyph';
import { r60Text } from './text';
import { GRAY, STRUCT, hexToNum } from './theme';
import { BUILD_HUD, PERFECT } from './themeBuild';

interface Chip {
  id: string;
  panel: NinePanel;
  objs: Phaser.GameObjects.GameObject[];
  h: number;
}

/**
 * 57라운드 계약 §14.1·§14.3 HUD 빌드 칩 — 좌상단, 구조물 상태 칩(StatusChips) 아래 세로 목록.
 * - 저주 칩(있으면 맨 위): 손실 띠(층 강조 19) + '저주'(흐림) + 이름(강조) + 남은 기간('3노드 남음' / '12처치 남음')
 * - 태그 칩(점수 높은 순 최대 4): 임시 글리프(이름 첫 글자 상자 — 태그 아이콘 10종 대기) + 이름(흐림) + '점수 · n단' +
 *   세트 임계 2·4·6 마름모 3칸(켜짐 = 층 강조 22, 꺼짐 = G05 고리)
 * 값이 바뀔 때만 다시 만든다. 완벽 성공(§14.11)이면 간파 칩을 한 번 깜빡인다.
 */
export class BuildChips {
  private chips: Chip[] = [];
  private sig = '';
  private top = 0;

  constructor(
    private scene: Phaser.Scene,
    private x: number,
  ) {}

  render(build: UiBuildState, stageIndex: number, top: number): void {
    const tags = hudTags(build, BUILD_HUD.maxTags);
    const c = build.curse;
    const sig = [
      stageIndex,
      c ? `${c.id}|${c.name}|${c.nodesLeft}|${c.killsLeft}` : '',
      ...tags.map((t) => `${t.id}|${t.name}|${t.score}|${t.stage}`),
    ].join('\u0001');
    if (sig !== this.sig) {
      this.sig = sig;
      this.top = top;
      this.rebuild(build, tags, stageIndex);
    } else if (top !== this.top) {
      const dy = top - this.top;
      this.top = top;
      for (const ch of this.chips) for (const o of [ch.panel, ...ch.objs]) (o as unknown as { y: number }).y += dy;
    }
  }

  /** 아래 끝 y */
  bottom(): number {
    return this.top + this.chips.reduce((h, c) => h + c.h + BUILD_HUD.chipGap, 0);
  }

  /** 완벽 성공: 그 태그 칩을 한 번 깜빡인다 (없으면 아무것도) */
  flash(tagId: string): void {
    const ch = this.chips.find((c) => c.id === tagId);
    if (!ch) return;
    const targets = [ch.panel, ...ch.objs];
    this.scene.tweens.killTweensOf(targets);
    for (const o of targets) (o as unknown as Phaser.GameObjects.Components.Alpha).setAlpha(1);
    this.scene.tweens.add({ targets, alpha: 0.35, duration: BUILD_HUD.flashMs / 2, yoyo: true });
  }

  setVisible(v: boolean): void {
    for (const c of this.chips)
      for (const o of [c.panel, ...c.objs]) (o as unknown as Phaser.GameObjects.Components.Visible).setVisible(v);
  }

  destroy(): void {
    this.clear();
  }

  private clear(): void {
    for (const c of this.chips) {
      this.scene.tweens.killTweensOf([c.panel, ...c.objs]);
      c.panel.destroy();
      for (const o of c.objs) o.destroy();
    }
    this.chips = [];
  }

  private rebuild(build: UiBuildState, tags: UiTagState[], si: number): void {
    this.clear();
    let y = this.top;
    if (build.curse) {
      this.chips.push(this.curseChip(build.curse.name, curseLeft(build.curse, r60Text), y, si));
      y += BUILD_HUD.chipH + BUILD_HUD.chipGap;
    }
    for (const t of tags) {
      this.chips.push(this.tagChip(t, y, si));
      y += BUILD_HUD.chipH + BUILD_HUD.chipGap;
    }
  }

  private curseChip(name: string, left: string, y: number, si: number): Chip {
    const scene = this.scene;
    const x = this.x;
    const tx = x + 5 + STRUCT.chipStripe + 4;
    const head = new GlowText(scene, tx - 2, y + 3, r60Text('curseHead'), 'ink_faint', { stageIndex: si });
    const nm = new GlowText(scene, tx - 2 + head.textW + 6, y + 3, name, 'ink_accent', { stageIndex: si });
    const lt = new GlowText(scene, nm.x + nm.textW + 6, y + 3, left, 'ink_faint', { stageIndex: si });
    const w = lt.x + (left ? lt.textW : -6) + 4 + 8 - x;
    const panel = inkPanel(scene, x, y, w, BUILD_HUD.chipH);
    const stripe = scene.add.graphics();
    stripe
      .fillStyle(hexToNum(accentHex(scene, si, BUILD_HUD.curseSlot)), 1)
      .fillRect(x + 5, y + 5, STRUCT.chipStripe, BUILD_HUD.chipH - 10);
    return this.finish('curse', panel, [stripe, head, nm, lt]);
  }

  private tagChip(t: UiTagState, y: number, si: number): Chip {
    const scene = this.scene;
    const x = this.x;
    const gs = BUILD_HUD.glyph;
    const gx = x + 6;
    const gy = y + Math.round((BUILD_HUD.chipH - gs) / 2);
    // 임시 글리프: 이름 첫 글자 상자 (태그 아이콘 10종이 오면 바꾼다)
    const box = scene.add.graphics();
    box.fillStyle(hexToNum(GRAY[2]), 1).fillRect(gx, gy, gs, gs);
    box
      .lineStyle(1, hexToNum(t.stage > 0 ? accentHex(scene, si, 22) : GRAY[6]), 1)
      .strokeRect(gx + 0.5, gy + 0.5, gs - 1, gs - 1);
    const ch = new GlowText(scene, 0, 0, (t.name || t.id).slice(0, 1), 'ink_body', { stageIndex: si });
    ch.setPosition(Math.round(gx + gs / 2 - ch.displayWidth / 2), Math.round(gy + gs / 2 - ch.displayHeight / 2));
    const tx = gx + gs + 6;
    const nm = new GlowText(scene, tx - 2, y + 3, t.name || t.id, 'ink_faint', { stageIndex: si });
    const val = new GlowText(
      scene,
      nm.x + nm.textW + 6,
      y + 3,
      tagChipValue(t, r60Text),
      t.stage > 0 ? 'ink_accent' : 'ink_body',
      {
        stageIndex: si,
      },
    );
    // 세트 임계 2·4·6
    const pips = scene.add.graphics();
    const r = BUILD_HUD.pipR;
    const px0 = val.x + val.textW + 6 + r;
    const py = y + Math.round(BUILD_HUD.chipH / 2);
    stagePips(t.stage).forEach((on, i) => {
      const cx = px0 + i * (r * 2 + 1 + BUILD_HUD.pipGap);
      if (on) pixelDiamond(pips, r, hexToNum(accentHex(scene, si, 22)), 1, cx, py);
      else diamondRing(pips, r, 1, hexToNum(GRAY[5]), 1, cx, py);
    });
    const w = px0 + 2 * (r * 2 + 1 + BUILD_HUD.pipGap) + r + 8 - x;
    const panel = inkPanel(scene, x, y, w, BUILD_HUD.chipH);
    return this.finish(t.id, panel, [box, ch, nm, val, pips]);
  }

  /** 글자를 패널보다 먼저 만들었으므로 depth 로 순서를 잡는다: 패널 → 띠·그림 → 글자 */
  private finish(id: string, panel: NinePanel, objs: Phaser.GameObjects.GameObject[]): Chip {
    panel.setDepth(STRUCT.hudDepth);
    for (const o of objs) {
      const d = o instanceof GlowText ? STRUCT.hudDepth + 2 : STRUCT.hudDepth + 1;
      (o as unknown as Phaser.GameObjects.Components.Depth).setDepth(d);
    }
    return { id, panel, objs, h: BUILD_HUD.chipH };
  }
}

/**
 * §14.11 완벽 성공 HUD 문구 — 하단 묶음 위 가운데에 잠깐 떠올랐다 사라진다 (ink_accent).
 * 띄우는 종류는 `PERFECT.hudKinds` (패링·퍼펙트 가드는 시스템 월드 문구가 있어 기본 제외 — 인터뷰 대상).
 */
export class PerfectPop {
  private t?: GlowText;

  constructor(private scene: Phaser.Scene) {}

  show(text: string, bundleTop: number, stageIndex: number): void {
    if (!text) return;
    if (this.t) {
      this.scene.tweens.killTweensOf(this.t);
      this.t.destroy();
    }
    const t = new GlowText(this.scene, 0, 0, text, 'ink_accent', { stageIndex }).setDepth(STRUCT.hudDepth + 3);
    const y = bundleTop - PERFECT.aboveBundle - t.displayHeight;
    t.placeCenter(UI_SCREEN.WIDTH / 2, y);
    this.t = t;
    this.scene.tweens.add({
      targets: t,
      y: y - PERFECT.rise,
      alpha: 0,
      delay: PERFECT.holdMs,
      duration: PERFECT.fadeMs,
      onComplete: () => {
        t.destroy();
        if (this.t === t) this.t = undefined;
      },
    });
  }

  destroy(): void {
    if (this.t) this.scene.tweens.killTweensOf(this.t);
    this.t?.destroy();
    this.t = undefined;
  }
}
