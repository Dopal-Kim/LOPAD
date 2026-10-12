import Phaser from 'phaser';
import type { UiWorldSign } from '../contract/ui';
import { signLines } from './eventView';
import { GlowText } from './glow';
import { GRAY, SEPIA, hexToNum } from './theme';
import { WORLD_SIGN as S } from './themeLoop2F';

/**
 * 62 루프 2 UI F (계약 D P1-17 `UiSnapshot.signs`): 수련장·시험장 허수아비 머리 위 나무 팻말 — 옛 디버그 글자 대신.
 * 판자(가죽 S1 바탕 · S2 나뭇결 두 줄 · 먹 외곽 · 못 두 점) + 말뚝 하나가 머리 위 끝을 가리킨다. 이름(흐림) · 값(밝게) 두 줄, Galmuri.
 * 팻말마다 id 로 지키고 글이 바뀔 때만 다시 그린다. 위치는 매 프레임 월드를 따라간다.
 */
export class WorldSigns {
  private items = new Map<string, { box: Phaser.GameObjects.Container; sig: string; w: number; h: number }>();

  constructor(private scene: Phaser.Scene) {}

  update(signs: readonly UiWorldSign[] | null | undefined, show: boolean): void {
    const list = show && Array.isArray(signs) ? signs : [];
    const seen = new Set<string>();
    for (const s of list) {
      if (!s || typeof s.id !== 'string' || !s.screen) continue;
      seen.add(s.id);
      const L = signLines(s);
      let it = this.items.get(s.id);
      if (!it || it.sig !== L.sig) {
        it?.box.destroy(true);
        it = this.build(L.title, L.value, L.sig);
        this.items.set(s.id, it);
      }
      it.box.setPosition(Math.round(s.screen.x - it.w / 2), Math.round(s.screen.y - S.post - it.h)).setVisible(true);
    }
    for (const [id, it] of this.items)
      if (!seen.has(id)) {
        it.box.destroy(true);
        this.items.delete(id);
      }
  }

  destroy(): void {
    for (const it of this.items.values()) it.box.destroy(true);
    this.items.clear();
  }

  private build(
    title: string,
    value: string,
    sig: string,
  ): { box: Phaser.GameObjects.Container; sig: string; w: number; h: number } {
    const sc = this.scene;
    const pad = S.pad;
    const t = title ? new GlowText(sc, 0, 0, title, 'page_faint') : null;
    const v = value ? new GlowText(sc, 0, 0, value, 'page_selected') : null;
    const textW = Math.max(t?.displayWidth ?? 0, v?.displayWidth ?? 0);
    const w = Math.max(S.minW, textW + pad * 2);
    let y = pad - 2;
    if (t) {
      t.placeCenter(w / 2, y);
      y += t.displayHeight - 1;
    }
    if (v) {
      v.placeCenter(w / 2, y);
      y += v.displayHeight;
    }
    const h = y + pad - 2;
    const g = sc.add.graphics();
    const ink = hexToNum(GRAY[0]);
    // 말뚝 (판자 아래 가운데 → 머리 위)
    const px = Math.round(w / 2 - S.postW / 2);
    g.fillStyle(ink, 1).fillRect(px - 1, h, S.postW + 2, S.post + 1);
    g.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(px, h, S.postW, S.post);
    // 그늘 · 먹 외곽 · 판자 · 나뭇결 · 아랫면 그늘 · 못
    g.fillStyle(ink, 0.4).fillRect(2, 2, w, h);
    g.fillStyle(ink, 1).fillRect(-1, -1, w + 2, h + 2);
    g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(0, 0, w, h);
    g.fillStyle(hexToNum(SEPIA[2]), 1)
      .fillRect(3, Math.round(h * 0.33), w - 9, 1)
      .fillRect(6, Math.round(h * 0.7), w - 10, 1);
    g.fillStyle(hexToNum(SEPIA[3]), 1).fillRect(0, 0, w, 1);
    g.fillStyle(hexToNum(SEPIA[0]), 1).fillRect(0, h - 1, w, 1);
    g.fillStyle(hexToNum(SEPIA[4]), 1)
      .fillRect(2, 2, 1, 1)
      .fillRect(w - 3, 2, 1, 1);
    const parts: Phaser.GameObjects.GameObject[] = [g];
    if (t) parts.push(t);
    if (v) parts.push(v);
    const box = sc.add.container(0, 0, parts).setDepth(S.depth);
    return { box, sig, w, h };
  }
}
