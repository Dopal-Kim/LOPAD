import Phaser from 'phaser';
import { UI_SCREEN, uiCommands, type UiRouteNode, type UiSnapshot } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { ensureImage, keyartKey, keyartUrl } from './kit';
import { RegionCard } from './RegionCard';
import { regionArtKey, regionChanged } from './regionView';
import { regionText } from './text';

/** 가운데 배너 차례: 글자 배너(층 제목·노드 이름·진화·이중 개성) 또는 50라운드 지역 카드 */
export type BannerItem =
  { kind: 'text'; text: string } | { kind: 'region'; region: string; art: string | null; desc: string };
/** 글자 배너 대기 상한 (지역 카드는 상한과 관계없이 넣는다) */
const BANNER_QUEUE_MAX = 3;

/**
 * HUD 가운데 배너 차례 (48·50라운드, HudScene 에서 분리 — 60라운드 정리). 층 제목 → 지역 카드 → 노드 이름 배너가
 * 같은 때 오면 겹치지 않게 차례로. `canRun()` 이 false 면(글꼴 전·탄생 연출 중) 쌓아 두었다가 `next()` 때 띄운다.
 */
export class BannerQueue {
  private queue: BannerItem[] = [];
  private busy = false;
  private banner?: GlowText;
  private card?: RegionCard;
  private cardItem?: BannerItem;
  /** 마지막으로 카드를 띄운 지역 */
  private lastRegion: string | null = null;

  constructor(
    private scene: Phaser.Scene,
    private canRun: () => boolean,
    private depth: number,
  ) {}

  /** 배너·카드가 없고 쌓인 것도 없다 */
  get idle(): boolean {
    return !this.busy && this.queue.length === 0 && !this.card;
  }

  /** 지역 카드가 떠 있다 (아무 키로 넘긴다 — Esc 도 이미 받았다) */
  get regionOpen(): boolean {
    return Boolean(this.card);
  }

  /** 층 시작·개성 변화 배너: 화면 가운데 발광 큰 글자 (Galmuri11 2배 — 한자 포함 가능) */
  text(text: string): void {
    this.enqueue({ kind: 'text', text });
  }

  /**
   * 50라운드 지역 카드 (계약 §12): 들어온 노드의 지역이 마지막으로 카드를 띄운 지역과 다르면 차례에 넣는다.
   * 키아트는 지금부터 읽기 시작한다 (카드 차례가 오면 대개 다 읽혀 있다). 무기 시험장에서는 띄우지 않는다.
   */
  region(node: UiRouteNode | null, s: UiSnapshot): void {
    if (!node || s.lab || !regionChanged(node.region, this.lastRegion)) return;
    const region = (node.region ?? '').trim();
    this.lastRegion = region;
    const art = regionArtKey(region);
    if (art) ensureImage(this.scene, keyartKey(art), keyartUrl(art));
    this.enqueue({ kind: 'region', region, art, desc: regionText(art, node.desc) });
  }

  /** 탄생 연출 시작: 같은 프레임에 먼저 온 진입 이벤트로 지역 카드가 떴으면 거두고 맨 앞으로 되돌린다 */
  holdRegion(): void {
    if (!this.card || !this.cardItem) return;
    this.card.cancel();
    this.queue.unshift(this.cardItem);
    this.card = undefined;
    this.cardItem = undefined;
    this.busy = false;
  }

  /** 런 끝: 지역 카드를 치우고 마지막 지역을 잊는다 (글자 배너는 남긴다) */
  endRun(): void {
    this.lastRegion = null;
    this.queue = this.queue.filter((b) => b.kind === 'text');
    if (this.card) {
      this.card.cancel();
      this.card = undefined;
      this.cardItem = undefined;
      this.busy = false;
    }
  }

  next(): void {
    if (!this.canRun() || this.busy) {
      this.expose();
      return;
    }
    const n = this.queue.shift();
    if (n !== undefined) this.run(n);
    this.expose();
  }

  destroy(): void {
    this.card?.cancel();
    this.card = undefined;
    this.cardItem = undefined;
    this.queue = [];
    this.busy = false;
    this.lastRegion = null;
  }

  private enqueue(item: BannerItem): void {
    if (!this.canRun() || this.busy) {
      const texts = this.queue.filter((b) => b.kind === 'text').length;
      if (item.kind === 'region' || texts < BANNER_QUEUE_MAX) this.queue.push(item);
      this.expose();
      return;
    }
    this.run(item);
    this.expose();
  }

  private run(item: BannerItem): void {
    this.busy = true;
    const scene = this.scene;
    const stageIndex = Math.max(0, uiCommands.getUiSnapshot().stageIndex);
    if (item.kind === 'region') {
      this.cardItem = item;
      const card = new RegionCard(scene, {
        region: item.region,
        desc: item.desc,
        art: item.art,
        stageIndex,
        onDone: () => {
          if (this.card !== card) return;
          this.card = undefined;
          this.cardItem = undefined;
          this.busy = false;
          this.next();
        },
      });
      this.card = card;
      return;
    }
    this.banner?.destroy();
    const b = new GlowText(scene, 0, 0, item.text, 'ink_body', { scale: 2, stageIndex })
      .setDepth(this.depth)
      .setAlpha(0);
    b.placeCenter(UI_SCREEN.WIDTH / 2, Math.round(UI_SCREEN.HEIGHT / 2 - 70));
    this.banner = b;
    scene.tweens.add({
      targets: b,
      alpha: 1,
      duration: 200,
      yoyo: true,
      hold: 1200,
      onComplete: () => {
        b.destroy();
        if (this.banner === b) this.banner = undefined;
        this.busy = false;
        this.next();
      },
    });
  }

  /** 헤드리스 확인용: 배너 차례 상태 (`uidebug=1` 일 때만) */
  private expose(): void {
    debugExpose('banners', {
      busy: this.busy,
      queued: this.queue.map((b) => (b.kind === 'text' ? b.text : `[${b.region}]`)),
    });
  }
}
