import Phaser from 'phaser';
import { ART_H, ART_W, TITLE_UI, type EmitterSpec, type SheetSpec } from './themeTitle';
import { emberAlpha, pickWeighted } from './titleView';

/**
 * 62 타이틀 불티 (아트 `title_fx_embers.json` 방출기 제안). Phaser 파티클 대신 작은 Image 풀 — 사인 흔들림·무기별 켜짐·
 * 수 상한을 직접 다룬다. 좌표는 아트 px(레이어 컨테이너 안, 가운데 원점 = 화면 (960,540)).
 * 같은 텍스처·같은 블렌드라 WebGL 한 묶음으로 그려진다. 상한은 모든 방출기 합(`TITLE_UI.emberCap`).
 */
interface Ember {
  img: Phaser.GameObjects.Image;
  alive: boolean;
  row: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  age: number;
  life: number;
  amp: number;
  period: number;
  ph: number;
  alphaMax: number;
  frame0: number;
}

const rand = (a: number, b: number): number => a + Math.random() * (b - a);

export class EmberField {
  private pool: Ember[] = [];
  private acc = new Map<string, number>();
  private nextAt = new Map<string, number>();

  constructor(
    private scene: Phaser.Scene,
    private container: Phaser.GameObjects.Container,
    private texKey: string,
    private sheet: SheetSpec,
    private emitters: EmitterSpec[],
    private cap: number,
    /** P21: 속도 배율 · 크기 범위 · 알파 들어옴/나감 ms (젖은 재는 따로) */
    private look: { speedK: number; scale: [number, number]; inMs: number; outMs: number } = {
      speedK: TITLE_UI.dark.emberSpeedK,
      scale: [1, 1],
      inMs: 300,
      outMs: 1200,
    },
  ) {}

  /** 지금 살아 있는 불티 수 */
  count(): number {
    let n = 0;
    for (const e of this.pool) if (e.alive) n++;
    return n;
  }

  /**
   * dt 만큼 진행. `voiceOn(i)` = i 번째 목소리(무기)가 지금 켜져 있는가, `origin(i)` = 그 무기의 불티 원점(아트 px).
   * `scale` 은 레이어 배율(가운데 원점 변환은 컨테이너가 한다).
   */
  update(
    dtMs: number,
    voiceOn: (i: number) => boolean,
    voiceRow: (i: number) => number,
    origin: (i: number) => [number, number],
    voices: number,
  ): void {
    const dt = Math.min(dtMs, TITLE_UI.emberMaxDtMs);
    for (const em of this.emitters) {
      if (em.voice) {
        for (let i = 0; i < voices; i++) {
          const k = `${em.name}#${i}`;
          if (!voiceOn(i)) {
            this.acc.set(k, 0);
            continue;
          }
          this.emitOver(k, em, dt, () => {
            const [ox, oy] = origin(i);
            return { x: ox + rand(-10, 10), y: oy + rand(-6, 6), row: voiceRow(i) };
          });
        }
      } else if (em.area) {
        const a = em.area;
        this.emitOver(em.name, em, dt, () => ({
          x: a.x + Math.random() * a.w,
          y: a.y + Math.random() * a.h,
          row: em.rows[pickWeighted(em.weights, Math.random())],
        }));
      }
    }
    const perFrame = 1000 / this.sheet.fps;
    const perRow = this.sheet.perRow;
    for (const e of this.pool) {
      if (!e.alive) continue;
      e.age += dt;
      if (e.age >= e.life) {
        e.alive = false;
        e.img.setVisible(false);
        continue;
      }
      e.x += (e.vx * dt) / 1000;
      e.y += (e.vy * dt) / 1000;
      const sway = Math.sin(e.ph + (2 * Math.PI * e.age) / e.period) * e.amp;
      e.img
        .setPosition(Math.round(e.x + sway), Math.round(e.y))
        .setAlpha(emberAlpha(e.age, e.life, e.alphaMax, this.look.inMs, this.look.outMs))
        .setFrame(e.row * perRow + ((e.frame0 + Math.floor(e.age / perFrame)) % perRow));
    }
  }

  /** 방출 속도(초당 a~b)에 맞춰 dt 동안 낼 만큼 낸다 */
  private emitOver(key: string, em: EmitterSpec, dt: number, at: () => { x: number; y: number; row: number }): void {
    let rate = this.nextAt.get(key);
    if (rate === undefined) {
      rate = rand(em.rate[0], em.rate[1]);
      this.nextAt.set(key, rate);
    }
    let acc = (this.acc.get(key) ?? 0) + (rate * dt) / 1000;
    while (acc >= 1) {
      acc -= 1;
      const p = at();
      this.spawn(em, p.x, p.y, p.row);
      this.nextAt.set(key, rand(em.rate[0], em.rate[1]));
    }
    this.acc.set(key, acc);
  }

  private spawn(em: EmitterSpec, x: number, y: number, row: number): void {
    let e = this.pool.find((p) => !p.alive);
    if (!e) {
      if (this.pool.length >= this.cap) return;
      const [px, py] = this.sheet.pivot;
      const img = this.scene.add
        .image(0, 0, this.texKey, 0)
        .setOrigin(px / this.sheet.frameW, py / this.sheet.frameH)
        .setBlendMode(Phaser.BlendModes.ADD)
        .setVisible(false);
      this.container.add(img);
      e = {
        img,
        alive: false,
        row: 0,
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        age: 0,
        life: 1,
        amp: 0,
        period: 1,
        ph: 0,
        alphaMax: 1,
        frame0: 0,
      };
      this.pool.push(e);
    }
    e.alive = true;
    e.row = row;
    // 컨테이너 원점 = 화면 가운데
    e.x = x - ART_W / 2;
    e.y = y - ART_H / 2;
    // P21: 불티는 재처럼 느리게 (look.speedK)
    e.vx = rand(em.vx[0], em.vx[1]) * this.look.speedK;
    e.vy = rand(em.vy[0], em.vy[1]) * this.look.speedK;
    e.age = 0;
    e.life = rand(em.life[0], em.life[1]);
    e.amp = rand(em.driftAmp[0], em.driftAmp[1]);
    e.period = rand(em.driftMs[0], em.driftMs[1]);
    e.ph = Math.random() * Math.PI * 2;
    e.alphaMax = em.alphaMax;
    e.frame0 = Math.floor(Math.random() * this.sheet.perRow);
    e.img.setVisible(true).setAlpha(0).setScale(rand(this.look.scale[0], this.look.scale[1]));
  }

  destroy(): void {
    for (const e of this.pool) e.img.destroy();
    this.pool = [];
  }
}
