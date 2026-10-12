import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';
import { GlowText } from './glow';
import { accentHex, ensureImage, keyartKey, keyartUrl } from './kit';
import { parseTips, pickTip } from './loadingView';
import { r62Text } from './text';
import { GRAY, SEPIA, hexToNum } from './theme';
import { LOADING } from './themeTransition';

/** 이번 실행에서 몇 번째 로딩인가 (팁을 돌려 가며) */
let shownCount = Math.floor(Math.random() * 1000);

/**
 * 62 루프 2 (P2-6) 로딩 카드 — 지역 키아트(액자처럼 세피아 테) · 위 흐린 제목 '다음 장을 펼치는 중' · 아래 단서 팁 한 줄(읽는 글 배율) ·
 * 진행 막대. 그림 속 입구 전환이 덮인 채 READY 가 늦을 때, 또는 시스템 로드 진행이 올 때 `TransitionScene` 이 띄운다.
 * `backdrop` = 화면 전체를 어둡게 덮을지 (전환 덮개가 없을 때).
 */
export class LoadingCard {
  private box: Phaser.GameObjects.Container;
  private bar: Phaser.GameObjects.Graphics;
  private progress = 0;
  private gone = false;
  private barY = 0;

  constructor(
    private scene: Phaser.Scene,
    region: string | null,
    depth: number,
    backdrop: boolean,
  ) {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const L = LOADING;
    const objs: Phaser.GameObjects.GameObject[] = [];
    if (backdrop) objs.push(scene.add.rectangle(0, 0, W, H, hexToNum(GRAY[1]), 1).setOrigin(0));
    const artX = Math.round(W / 2 - L.artW / 2);
    const artY = L.artTop;
    // 액자 테 (세피아 S3 바깥 · S1 안쪽) — 그림이 늦게 와도 자리는 그대로
    const frame = scene.add.graphics();
    frame.fillStyle(hexToNum(SEPIA[3]), 1).fillRect(artX - 3, artY - 3, L.artW + 6, L.artH + 6);
    frame.fillStyle(hexToNum(SEPIA[0]), 1).fillRect(artX - 1, artY - 1, L.artW + 2, L.artH + 2);
    objs.push(frame);
    const title = new GlowText(scene, 0, artY - 22, r62Text('loadingTitle'), 'ink_faint');
    title.placeCenter(W / 2, artY - 22);
    objs.push(title);
    const tips = parseTips(r62Text('loadingTips'));
    const tip = new GlowText(scene, 0, 0, pickTip(tips, shownCount++), 'ink_body', {
      wrap: L.tipWrap,
      align: 'center',
      readable: true,
    });
    const tipY = artY + L.artH + L.tipGap;
    tip.placeCenter(W / 2, tipY);
    objs.push(tip);
    this.barY = Math.round(tipY + tip.displayHeight + L.barGap);
    this.bar = scene.add.graphics();
    objs.push(this.bar);
    this.box = scene.add.container(0, 0, objs).setDepth(depth).setAlpha(0);
    scene.tweens.add({ targets: this.box, alpha: 1, duration: L.inMs });
    const key = region;
    if (key) {
      const tex = keyartKey(key);
      ensureImage(scene, tex, keyartUrl(key), (ok) => {
        if (!ok || this.gone) return;
        const img = scene.add.image(artX, artY, tex).setOrigin(0).setDisplaySize(L.artW, L.artH);
        this.box.addAt(img, objs.indexOf(frame) + 1);
      });
    }
    this.draw();
  }

  /** 진행 0~1 (뒤로 가지 않는다) */
  set(p: number): void {
    const v = Math.max(this.progress, Math.max(0, Math.min(1, p)));
    if (v === this.progress) return;
    this.progress = v;
    this.draw();
  }

  get value(): number {
    return this.progress;
  }

  /** 끝까지 채우고 사라진다 (두 번 불러도 한 번) */
  finish(): void {
    if (this.gone) return;
    this.gone = true;
    this.progress = 1;
    this.draw();
    this.scene.tweens.killTweensOf(this.box);
    this.scene.tweens.add({
      targets: this.box,
      alpha: 0,
      delay: LOADING.fullHoldMs,
      duration: LOADING.outMs,
      onComplete: () => this.box.destroy(),
    });
  }

  destroy(): void {
    this.gone = true;
    this.scene.tweens.killTweensOf(this.box);
    this.box.destroy();
  }

  private draw(): void {
    const L = LOADING;
    const g = this.bar.clear();
    const x = Math.round(UI_SCREEN.WIDTH / 2 - L.barW / 2);
    const y = this.barY;
    g.fillStyle(hexToNum(GRAY[0]), 1).fillRect(x - 1, y - 1, L.barW + 2, L.barH + 2);
    g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(x, y, L.barW, L.barH);
    const w = Math.round(L.barW * this.progress);
    if (w > 0) g.fillStyle(hexToNum(accentHex(this.scene, 0, L.barSlot)), 1).fillRect(x, y, w, L.barH);
  }
}
