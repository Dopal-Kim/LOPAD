import Phaser from 'phaser';
import { bodyFrame, dirIndex, inPolygon } from './ritualView';
import { RITUAL_UI as R } from './themeRitual';

/** 스탬프 하나 (도트 좌표) */
interface Stamp {
  frame: string;
  x: number;
  y: number;
}

interface StrokeRec {
  stamps: Stamp[];
  ember: boolean;
}

/**
 * 62 P0-2 3획 먹 화폭 (art §30 ink_brush 권장대로): 640×360 도트 RenderTexture 에 정수 도트 좌표로 스탬프를 찍고 논리 1.5배로 보인다.
 * 긋는 중 = 먹 #141516, 판정 난 획 = 불씨 먹 #e8b858 로 다시 찍고 아래 빛무리 화폭(ADD)에 #d67a11 큰 붓끝.
 * 획 시작 = press, 몸통 = 속도별 tip/dry, 끝 = flick(진행 방향)·빠르면 splat. 등 다각형(strokeClip) 밖은 찍지 않는다.
 * 붓 아틀라스가 없으면 같은 자리에 네모 점(rt.fill)으로.
 */
export class StrokeInk {
  readonly rt: Phaser.GameObjects.RenderTexture;
  readonly glow: Phaser.GameObjects.RenderTexture;
  private strokes: StrokeRec[] = [];
  private cur: Stamp[] | null = null;
  private last = { x: 0, y: 0 };
  private hasBrush: boolean;

  constructor(
    scene: Phaser.Scene,
    /** 도트 좌표 다각형 (없으면 자르지 않음) */
    private clip: (readonly [number, number])[] | null,
  ) {
    const C = R.canvas;
    this.glow = scene.add
      .renderTexture(0, 0, C.dotW, C.dotH)
      .setOrigin(0, 0)
      .setScale(C.dotScale)
      .setBlendMode(Phaser.BlendModes.ADD);
    this.rt = scene.add.renderTexture(0, 0, C.dotW, C.dotH).setOrigin(0, 0).setScale(C.dotScale);
    this.hasBrush = scene.textures.exists(R.art.brush);
  }

  /** 도트 좌표 (논리 → 도트) */
  static dot(lx: number, ly: number): { x: number; y: number } {
    return { x: Math.round(lx / R.canvas.dotScale), y: Math.round(ly / R.canvas.dotScale) };
  }

  /** 이 논리 자리에서 획을 시작할 수 있는가 */
  canStart(lx: number, ly: number): boolean {
    const d = StrokeInk.dot(lx, ly);
    return !this.clip || inPolygon(d.x, d.y, this.clip);
  }

  begin(lx: number, ly: number): void {
    const d = StrokeInk.dot(lx, ly);
    this.cur = [];
    this.last = d;
    this.put({ frame: 'press_d8', x: d.x, y: d.y });
  }

  /** 앞 점에서 이 점까지 몸통을 찍는다 */
  move(lx: number, ly: number, speed: number): void {
    if (!this.cur) return;
    const d = StrokeInk.dot(lx, ly);
    const dx = d.x - this.last.x;
    const dy = d.y - this.last.y;
    const len = Math.hypot(dx, dy);
    if (len < 0.5) return;
    const frame = bodyFrame(speed, dirIndex(dx, dy));
    const n = Math.max(1, Math.ceil(len / R.stamp.step));
    for (let i = 1; i <= n; i++)
      this.put({ frame, x: Math.round(this.last.x + (dx * i) / n), y: Math.round(this.last.y + (dy * i) / n) });
    this.last = d;
  }

  /** 획 끝: 삐침 (+ 빠르면 먹 튐). 남긴 획 번호 */
  end(endDir: { dx: number; dy: number }, speed: number): number {
    if (!this.cur) return -1;
    if (this.cur.length > 6)
      this.put({ frame: `flick_r${dirIndex(endDir.dx, endDir.dy)}`, x: this.last.x, y: this.last.y });
    if (speed >= R.stamp.fast) this.put({ frame: `splat_${this.strokes.length % 4}`, x: this.last.x, y: this.last.y });
    this.strokes.push({ stamps: this.cur, ember: false });
    this.cur = null;
    return this.strokes.length - 1;
  }

  /** 획으로 치지 않았다: 마지막으로 남긴 획을 지운다 (화폭을 다시 찍는다) */
  dropLast(): void {
    this.cur = null;
    this.strokes.pop();
    this.redraw();
  }

  /** 판정 난 획: 불씨 먹 + 빛무리 */
  ember(index: number): void {
    const s = this.strokes[index];
    if (!s || s.ember) return;
    s.ember = true;
    this.stampList(s.stamps, R.stamp.ember);
    this.haloList(s.stamps);
  }

  get count(): number {
    return this.strokes.length;
  }

  destroy(): void {
    this.rt.destroy();
    this.glow.destroy();
  }

  private put(st: Stamp): void {
    if (this.clip && !inPolygon(st.x, st.y, this.clip)) return;
    this.cur?.push(st);
    this.stampList([st], R.stamp.ink);
  }

  private redraw(): void {
    this.rt.clear();
    this.glow.clear();
    for (const s of this.strokes) {
      this.stampList(s.stamps, s.ember ? R.stamp.ember : R.stamp.ink);
      if (s.ember) this.haloList(s.stamps);
    }
  }

  private stampList(list: Stamp[], tint: number): void {
    if (this.hasBrush) {
      for (const st of list) this.rt.stamp(R.art.brush, st.frame, st.x, st.y, { tint });
      return;
    }
    for (const st of list) {
      const m = /d(\d+)/.exec(st.frame);
      const d = m ? Number(m[1]) : 4;
      this.rt.fill(tint, 1, st.x - Math.floor(d / 2), st.y - Math.floor(d / 2), d, d);
    }
  }

  private haloList(list: Stamp[]): void {
    for (let i = 0; i < list.length; i += 3) {
      const st = list[i];
      if (this.hasBrush)
        this.glow.stamp(R.art.brush, 'tip_d10', st.x, st.y, { tint: R.stamp.halo, alpha: R.stamp.haloAlpha });
      else this.glow.fill(R.stamp.halo, R.stamp.haloAlpha, st.x - 5, st.y - 5, 10, 10);
    }
  }
}
