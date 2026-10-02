import Phaser from 'phaser';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { ensureImage, keyartKey, keyartUrl } from './kit';
import { cardAlpha } from './regionView';
import { GRAY, REGION_CARD, hexToNum } from './theme';

export interface RegionCardOptions {
  /** 지역 표시 이름 (UiRouteNode.region) */
  region: string;
  /** 짧은 설명 한 줄 (비면 그리지 않음) */
  desc: string;
  /** 키아트 키 (waste·gate·…). null 이면 그림 없이 어두운 바탕 */
  art: string | null;
  stageIndex: number;
  /** 다 사라졌다 (넘김 포함). cancel() 로 멈추면 부르지 않는다 */
  onDone: () => void;
}

/**
 * 50라운드 지역 카드 (계약 §12): 노드 진입으로 지역이 바뀌면 화면 전체에 그 지역 키아트 →
 * 아래쪽 띠 위에 지역 이름(발광 큰 글자)·짧은 설명이 조금 늦게 나타남 → 사라짐 (합 1.9초).
 * 아무 키·클릭으로 넘긴다(입력은 게임에도 그대로 간다 — 카드는 보기만 가린다). 키아트를 아직 안 읽었으면 읽고
 * 최대 `loadWaitMs` 기다린 뒤 시작한다(못 읽으면 그림 없이). 화면 좌표는 캔버스 960×540 그대로(키아트 1:1).
 */
export class RegionCard {
  private objs: Phaser.GameObjects.GameObject[] = [];
  private bg?: Phaser.GameObjects.Rectangle;
  private img?: Phaser.GameObjects.Image;
  private band?: Phaser.GameObjects.Rectangle;
  private texts: GlowText[] = [];
  private startAt = -1;
  private skip?: { at: number; fadeMs: number; from: number };
  private lastBg = 0;
  private waitTimer?: Phaser.Time.TimerEvent;
  private finished = false;

  constructor(
    private scene: Phaser.Scene,
    private opts: RegionCardOptions,
  ) {
    const art = opts.art;
    if (!art || scene.textures.exists(keyartKey(art))) {
      this.show();
      return;
    }
    // 그림을 기다린다 (오면 바로, 늦으면 그림 없이)
    let started = false;
    const go = (): void => {
      if (started || this.finished) return;
      started = true;
      this.waitTimer?.remove();
      this.waitTimer = undefined;
      this.show();
    };
    ensureImage(scene, keyartKey(art), keyartUrl(art), go);
    this.waitTimer = scene.time.delayedCall(REGION_CARD.loadWaitMs, go);
  }

  get active(): boolean {
    return !this.finished;
  }

  /** 넘김: 지금 밝기에서 짧게 사라진다 */
  requestSkip(): void {
    if (this.finished || this.startAt < 0 || this.skip) return;
    const t = this.scene.time.now - this.startAt;
    if (t < REGION_CARD.skipGuardMs) return;
    this.skip = { at: t, fadeMs: REGION_CARD.skipFadeMs, from: this.lastBg };
  }

  /** 끝내지 않고 치운다 (탄생 연출이 끼어들 때 등). onDone 을 부르지 않는다 */
  cancel(): void {
    this.cleanup();
  }

  private show(): void {
    if (this.finished) return;
    const scene = this.scene;
    const W = scene.scale.width;
    const H = scene.scale.height;
    const D = REGION_CARD.depth;
    const add = <T extends Phaser.GameObjects.GameObject & { setDepth(d: number): unknown }>(o: T): T => {
      o.setDepth(D);
      this.objs.push(o);
      return o;
    };
    this.bg = add(scene.add.rectangle(0, 0, W, H, hexToNum(GRAY[0]), 1).setOrigin(0, 0).setAlpha(0));
    const key = this.opts.art ? keyartKey(this.opts.art) : '';
    if (key && scene.textures.exists(key)) {
      this.img = add(scene.add.image(0, 0, key).setOrigin(0, 0).setDisplaySize(W, H).setAlpha(0));
    }
    const cy = REGION_CARD.bandY;
    this.band = add(
      scene.add
        .rectangle(0, Math.round(cy - REGION_CARD.bandH / 2), W, REGION_CARD.bandH, hexToNum(GRAY[0]), 0.55)
        .setOrigin(0, 0)
        .setAlpha(0),
    );
    // 지역 이름: 잉크 발광 큰 글자 (Galmuri11 2배 — 한자가 섞여도 된다), 그 아래 설명
    const si = this.opts.stageIndex;
    const name = new GlowText(scene, 0, 0, this.opts.region, 'ink_body', { scale: 2, stageIndex: si });
    const desc = this.opts.desc ? new GlowText(scene, 0, 0, this.opts.desc, 'ink_accent', { stageIndex: si }) : null;
    const total = name.displayHeight + (desc ? REGION_CARD.lineGap + desc.displayHeight : 0);
    let y = Math.round(cy - total / 2);
    name.placeCenter(W / 2, y);
    y += name.displayHeight + REGION_CARD.lineGap;
    desc?.placeCenter(W / 2, y);
    for (const t of desc ? [name, desc] : [name]) {
      add(t);
      t.setAlpha(0);
      this.texts.push(t);
    }
    this.startAt = scene.time.now;
    scene.events.on(Phaser.Scenes.Events.UPDATE, this.tick);
    scene.input.keyboard?.on('keydown', this.onKey);
    scene.input.on('pointerdown', this.onPointer);
    debugExpose('regionCard', { region: this.opts.region, art: this.opts.art, image: Boolean(this.img) });
  }

  private onKey = (e: KeyboardEvent): void => {
    if (!e.repeat) this.requestSkip();
  };

  private onPointer = (): void => this.requestSkip();

  private tick = (): void => {
    if (this.finished || this.startAt < 0) return;
    const a = cardAlpha(this.scene.time.now - this.startAt, REGION_CARD, this.skip);
    this.lastBg = a.bg;
    this.bg?.setAlpha(a.bg);
    this.img?.setAlpha(a.bg);
    this.band?.setAlpha(a.text);
    for (const t of this.texts) t.setAlpha(a.text);
    if (a.done) {
      this.cleanup();
      this.opts.onDone();
    }
  };

  private cleanup(): void {
    if (this.finished) return;
    this.finished = true;
    this.waitTimer?.remove();
    this.waitTimer = undefined;
    this.scene.events.off(Phaser.Scenes.Events.UPDATE, this.tick);
    this.scene.input?.keyboard?.off('keydown', this.onKey);
    this.scene.input?.off('pointerdown', this.onPointer);
    for (const o of this.objs) o.destroy();
    this.objs = [];
    this.texts = [];
    debugExpose('regionCard', null);
  }
}
