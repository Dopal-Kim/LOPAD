import Phaser from 'phaser';
import { UI_SCREEN, type UiBuildState, type UiTagState } from '../contract/ui';
import { hudTags } from './buildView';
import { curseShort } from './combatView';
import { GlowText } from './glow';
import { NinePanel, accentHex, inkPanel } from './kit';
import { KEYCAP, KeyCap } from './keycap';
import { fill, r60Text, r61Text } from './text';
import { GRAY, STRUCT, hexToNum } from './theme';
import { BUILD_HUD, PERFECT } from './themeBuild';
import { BUILD_STRIP } from './themeR61';

/**
 * 57라운드 계약 §14.1·§14.3 HUD 빌드 칩 → 61라운드 P10 다이어트: **한 줄 띠**로 접는다 (좌상단, 구조물 상태 칩 아래).
 * - 저주(있으면 맨 앞): 손실 띠(층 강조 19) + '저주 3노드'(강조)
 * - 태그(점수 높은 순 최대 4): 임시 글리프(이름 첫 글자 상자, 세트가 켜지면 테 강조 22) + 점수(세트 켜짐 = 강조)
 * - 끝에 [Tab] 빌드 (Tab 빌드 보기를 쓸 수 있는 층·시험장에서만)
 * 이름·세트 단계·남은 효과는 Tab 빌드 보기·일기장에. 값이 바뀔 때만 다시 만든다. 완벽 성공이면 간파 글리프를 한 번 깜빡인다.
 */
export class BuildChips {
  private panel?: NinePanel;
  private objs: Phaser.GameObjects.GameObject[] = [];
  /** 태그별 깜빡일 것 */
  private tagObjs = new Map<string, Phaser.GameObjects.GameObject[]>();
  private sig = '';
  private top = 0;
  private h = 0;

  constructor(
    private scene: Phaser.Scene,
    private x: number,
  ) {}

  render(build: UiBuildState, stageIndex: number, top: number, tabHint = false): void {
    const tags = hudTags(build, BUILD_HUD.maxTags);
    const c = build.curse;
    const sig = [
      stageIndex,
      tabHint ? 'tab' : '',
      c ? `${c.id}|${c.nodesLeft}|${c.killsLeft}` : '',
      ...tags.map((t) => `${t.id}|${t.name}|${t.score}|${t.stage}`),
    ].join('\u0001');
    if (sig !== this.sig) {
      this.sig = sig;
      this.top = top;
      this.rebuild(build, tags, stageIndex, tabHint);
    } else if (top !== this.top) {
      const dy = top - this.top;
      this.top = top;
      for (const o of this.all()) (o as unknown as { y: number }).y += dy;
    }
  }

  /** 아래 끝 y (띠가 없으면 top) */
  bottom(): number {
    return this.top + (this.h ? this.h + BUILD_HUD.chipGap : 0);
  }

  /** 완벽 성공: 그 태그 글리프를 한 번 깜빡인다 (없으면 아무것도) */
  flash(tagId: string): void {
    const targets = this.tagObjs.get(tagId);
    if (!targets) return;
    this.scene.tweens.killTweensOf(targets);
    for (const o of targets) (o as unknown as Phaser.GameObjects.Components.Alpha).setAlpha(1);
    this.scene.tweens.add({ targets, alpha: 0.35, duration: BUILD_HUD.flashMs / 2, yoyo: true });
  }

  setVisible(v: boolean): void {
    for (const o of this.all()) (o as unknown as Phaser.GameObjects.Components.Visible).setVisible(v);
  }

  destroy(): void {
    this.clear();
  }

  private all(): Phaser.GameObjects.GameObject[] {
    return this.panel ? [this.panel, ...this.objs] : [...this.objs];
  }

  private clear(): void {
    const all = this.all();
    this.scene.tweens.killTweensOf(all);
    for (const o of all) o.destroy();
    this.panel = undefined;
    this.objs = [];
    this.tagObjs.clear();
    this.h = 0;
  }

  private rebuild(build: UiBuildState, tags: UiTagState[], si: number, tabHint: boolean): void {
    this.clear();
    if (!build.curse && !tags.length && !tabHint) return;
    const scene = this.scene;
    const S = BUILD_STRIP;
    const y = this.top;
    const g = scene.add.graphics();
    this.objs.push(g);
    let x = this.x + S.padX;
    const textY = y + Math.round((S.h - 16) / 2);
    const curse = curseShort(build.curse);
    if (build.curse) {
      g.fillStyle(hexToNum(accentHex(scene, si, BUILD_HUD.curseSlot)), 1).fillRect(
        x,
        y + 5,
        STRUCT.chipStripe,
        S.h - 10,
      );
      x += STRUCT.chipStripe + 2;
      const text = curse
        ? fill(r61Text('curseShort'), {
            n: curse.n,
            unit: r61Text(curse.unit === 'node' ? 'curseUnitNode' : 'curseUnitKill'),
          })
        : r60Text('curseHead');
      const t = new GlowText(scene, x, textY, text, 'ink_accent', { stageIndex: si });
      this.objs.push(t);
      x += t.displayWidth + S.gap;
    }
    const gs = S.glyph;
    for (const tag of tags) {
      const gy = y + Math.round((S.h - gs) / 2);
      // 임시 글리프: 이름 첫 글자 상자 (태그 아이콘 10종이 오면 바꾼다)
      const box = scene.add.graphics();
      box.fillStyle(hexToNum(GRAY[2]), 1).fillRect(x, gy, gs, gs);
      box
        .lineStyle(1, hexToNum(tag.stage > 0 ? accentHex(scene, si, 22) : GRAY[6]), 1)
        .strokeRect(x + 0.5, gy + 0.5, gs - 1, gs - 1);
      const ch = new GlowText(scene, 0, 0, (tag.name || tag.id).slice(0, 1), 'ink_body', { stageIndex: si });
      ch.setPosition(Math.round(x + gs / 2 - ch.displayWidth / 2), Math.round(gy + gs / 2 - ch.displayHeight / 2));
      const val = new GlowText(
        scene,
        x + gs + S.scoreGap - 2,
        textY,
        String(tag.score),
        tag.stage > 0 ? 'ink_accent' : 'ink_faint',
        {
          stageIndex: si,
        },
      );
      this.objs.push(box, ch, val);
      this.tagObjs.set(tag.id, [box, ch, val]);
      x = val.x + val.displayWidth + S.gap - 2;
    }
    if (tabHint) {
      const cap = new KeyCap(scene, x, y + Math.round((S.h - KEYCAP.h) / 2), 'Tab', true);
      const t = new GlowText(scene, x + cap.width + 3, textY, r61Text('stripTab'), 'ink_faint', { stageIndex: si });
      this.objs.push(cap, t);
      x = t.x + t.displayWidth + S.gap;
    }
    const w = x - S.gap + S.padX - this.x;
    this.panel = inkPanel(scene, this.x, y, Math.max(24, w), Math.max(24, S.h));
    this.h = Math.max(24, S.h);
    // 글자를 패널보다 먼저 만들었으므로 depth 로 순서를 잡는다: 패널 → 띠·그림 → 글자
    this.panel.setDepth(STRUCT.hudDepth);
    for (const o of this.objs) {
      const d = o instanceof GlowText ? STRUCT.hudDepth + 2 : STRUCT.hudDepth + 1;
      (o as unknown as Phaser.GameObjects.Components.Depth).setDepth(d);
    }
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
