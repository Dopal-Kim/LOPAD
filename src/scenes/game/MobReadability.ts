/**
 * 62라운드 P1-4 적 가독성 (시스템 몫 — 점검 '어두운 흙바닥 위 회갈색 징집병이 묻힌다'):
 * - 차가운 림: 일반 적(보스·엘리트 제외 — 엘리트는 호박 외곽선이 있다) 둘레에 아트 외곽선 시트(`enemies/v3/<적>_<동작>_elite`,
 *   같은 프레임·피벗·배율 — 부팅 묶음에 이미 있다)를 차가운 색 채움으로 적 바로 아래에 겹친다. 주인공 빛(따뜻함)과 반대 색이라
 *   어둠 속에서도 실루엣이 읽힌다. 외곽선 시트가 없는 동작이면 그 프레임만 생략.
 * - HP 막대: 피해를 입은 일반 적 머리 위에 얇은 막대(바탕·남은 HP·방금 깎인 몫이 천천히 줄어듦). 라이트맵 위 깊이.
 *   엘리트·보스 HP 는 UI(이름표·보스 막대)가 그린다.
 * 매 프레임 POST_UPDATE (적 애니·피격 반응이 정해진 뒤). 씬 종료 때 스스로 정리. 끄기: ENEMY_READABILITY.RIM.ON / HP_BAR.ON
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_READABILITY } from '../../core/Constants';
import type { Mob } from '../../objects/Mob';
import { eliteAction, rimAction } from '../../systems/bundle2/bundleSheets';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { parseAnimKey } from '../../systems/sprites/spriteDefs';
import type { Game } from '../Game';

interface MobMark {
  rim: Phaser.GameObjects.Sprite | null;
  /** 막대에 보이는 HP 비율 (방금 깎인 몫이 천천히 따라 내려온다) */
  shown: number;
}

export class MobReadability {
  private readonly marks = new Map<Mob, MobMark>();
  private readonly bars: Phaser.GameObjects.Graphics;
  /** 디버그: 지난 프레임 림·막대 수 */
  rims = 0;
  barCount = 0;

  constructor(private readonly g: Game) {
    this.bars = g.add.graphics().setDepth(DEPTH.DAMAGE_TEXT - 0.3);
    g.events.on(Phaser.Scenes.Events.POST_UPDATE, this.update, this);
    g.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  private update(_time: number, delta: number): void {
    const R = ENEMY_READABILITY;
    this.bars.clear();
    let rims = 0;
    let bars = 0;
    const seen = new Set<Mob>();
    for (const child of this.g.mobs.getChildren()) {
      const m = child as Mob;
      if (!m.active || m.isBoss) continue;
      seen.add(m);
      let mk = this.marks.get(m);
      if (!mk) {
        mk = { rim: null, shown: 1 };
        this.marks.set(m, mk);
      }
      if (R.RIM.ON && !m.elite && this.drawRim(m, mk)) rims++;
      else mk.rim?.setVisible(false);
      if (R.HP_BAR.ON && !m.elite && this.drawBar(m, mk, delta)) bars++;
    }
    for (const [m, mk] of this.marks)
      if (!seen.has(m)) {
        mk.rim?.destroy();
        this.marks.delete(m);
      }
    this.rims = rims;
    this.barCount = bars;
  }

  /** 림: 지금 몸 동작의 외곽선 시트 같은 프레임 (없으면 false) */
  private drawRim(m: Mob, mk: MobMark): boolean {
    const v = m.visual;
    const parsed = v.current ? parseAnimKey(v.current, v.sheetName) : null;
    // 62 D (art §31.3): 아트 1도트 림 시트 `<적>_<동작>_rim`(같은 틀·프레임 — 색 그대로) → 없으면 엘리트 외곽선 시트를 차가운 채움으로
    const own = parsed ? spriteLibrary.textureKey(v.sheetName, rimAction(parsed.action)) : null;
    const sheetRim = Boolean(own && this.g.textures.exists(own));
    const tex = sheetRim ? own : parsed ? spriteLibrary.textureKey(v.sheetName, eliteAction(parsed.action)) : null;
    if (!tex || !this.g.textures.exists(tex) || !m.visible) {
      mk.rim?.setVisible(false);
      return false;
    }
    const R = ENEMY_READABILITY.RIM;
    let rim = mk.rim;
    if (!rim) {
      rim = this.g.add.sprite(m.x, m.y, tex);
      mk.rim = rim;
    }
    if (rim.texture.key !== tex) rim.setTexture(tex);
    if (sheetRim) rim.clearTint();
    else rim.setTintFill(R.COLOR);
    const frame = rim.texture.has(m.frame.name) ? m.frame.name : undefined;
    if (frame === undefined) {
      rim.setVisible(false);
      return false;
    }
    rim
      .setFrame(frame)
      .setOrigin(m.originX, m.originY)
      .setScale(m.scaleX, m.scaleY)
      .setRotation(m.rotation)
      .setFlipX(m.flipX)
      .setPosition(m.x, m.y)
      .setDepth(m.depth - DEPTH.OVERLAY_STEP * 0.5)
      .setAlpha((sheetRim ? 1 : R.ALPHA) * m.alpha)
      .setVisible(true);
    return true;
  }

  /** HP 막대: 피해를 입은 적만, 머리 위 (일어서는 중이면 생략) */
  private drawBar(m: Mob, mk: MobMark, delta: number): boolean {
    const B = ENEMY_READABILITY.HP_BAR;
    const ratio = m.maxHp > 0 ? Math.max(0, Math.min(1, m.hp / m.maxHp)) : 1;
    // 방금 깎인 몫: 비율이 내려가면 shown 이 TRAIL_PER_S 속도로 따라 내려온다
    mk.shown = ratio >= mk.shown ? ratio : Math.max(ratio, mk.shown - (B.TRAIL_PER_S * delta) / 1000);
    if (ratio >= 1 || !m.visible || m.isArriving(this.g.time.now)) return false;
    const w = B.W;
    const x = Math.round(m.x - w / 2);
    const y = m.y - m.visual.headTopPx - B.GAP;
    const gr = this.bars;
    gr.fillStyle(B.BACK, B.BACK_ALPHA);
    gr.fillRect(x - B.PAD, y - B.PAD, w + B.PAD * 2, B.H + B.PAD * 2);
    if (mk.shown > ratio) {
      gr.fillStyle(B.TRAIL, 1);
      gr.fillRect(x, y, w * mk.shown, B.H);
    }
    gr.fillStyle(B.FILL, 1);
    gr.fillRect(x, y, Math.max(B.MIN_FILL, w * ratio), B.H);
    return true;
  }

  summary(): Record<string, unknown> {
    return { rims: this.rims, bars: this.barCount, tracked: this.marks.size };
  }

  destroy(): void {
    this.g.events.off(Phaser.Scenes.Events.POST_UPDATE, this.update, this);
    for (const mk of this.marks.values()) mk.rim?.destroy();
    this.marks.clear();
    this.bars.destroy();
  }
}
