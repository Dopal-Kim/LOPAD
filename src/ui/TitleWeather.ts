import Phaser from 'phaser';
import { ART_H, ART_W, TITLE_UI, titleKey, type CrowSpec, type RainSpec, type TitleSpec } from './themeTitle';
import { crowFlightY } from './titleView';

/**
 * P21 타이틀 날씨 (아트 A title.json `rain`·`crows`): 비 두 겹(먼·가까운 — 오른쪽 아래로 흐르는 반복 그림)과
 * 7~15초마다 화면을 가로지르는 까마귀 1~3마리. 층 컨테이너는 TitleArt 가 만들어 넘긴다(가운데 원점, 아트 px).
 * 모션 줄이기: 먼 비만 멈춘 채 옅게, 가까운 비·까마귀 끔.
 */
const CX = ART_W / 2;
const CY = ART_H / 2;
const CROW_ANIM = 'ui-title-crow-fly';

interface Crow {
  s: Phaser.GameObjects.Sprite;
  x: number;
  y: number;
  vx: number;
  ph: number;
}

const rand = (a: number, b: number): number => a + Math.random() * (b - a);

export class TitleWeather {
  private rains: { t: Phaser.GameObjects.TileSprite; r: RainSpec }[] = [];
  private crows: Crow[] = [];
  private nextFlight = 0;

  constructor(
    scene: Phaser.Scene,
    private spec: TitleSpec,
    /** 깊이·패럴랙스로 층 컨테이너 만들기 (TitleArt.layer) */
    layer: (depth: number, factor: number) => Phaser.GameObjects.Container,
    private reduced: () => boolean,
  ) {
    const rainKey = titleKey('title_fx_rain');
    if (scene.textures.exists(rainKey))
      for (const r of spec.rain) {
        const pad = 64;
        const c = layer(r.depth, r.layer === 'far' ? TITLE_UI.parallax.fogFar : 1);
        const t = scene.add
          .tileSprite(-CX - pad, -CY - pad, ART_W + pad * 2, ART_H + pad * 2, rainKey)
          .setOrigin(0, 0)
          .setTileScale(r.scale)
          .setAlpha(r.alpha);
        c.add(t);
        this.rains.push({ t, r });
      }
    const cs = spec.crows;
    const crowKey = titleKey('title_fx_crow');
    if (cs && scene.textures.exists(crowKey)) {
      sliceSheet(scene, crowKey, cs.frameW, cs.frameH);
      if (!scene.anims.exists(CROW_ANIM))
        scene.anims.create({
          key: CROW_ANIM,
          frames: Array.from({ length: cs.frames }, (_, i) => ({ key: crowKey, frame: i })),
          frameRate: cs.fps,
          repeat: -1,
        });
      const far = layer(cs.depthFar, TITLE_UI.parallax.cityEmbers);
      const near = layer(cs.depthNear, 1);
      const max = Math.max(1, Math.round(cs.count[1]));
      for (let i = 0; i < max * 2; i++) {
        const s = scene.add
          .sprite(0, 0, crowKey, 0)
          .setOrigin(cs.pivot[0] / cs.frameW, cs.pivot[1] / cs.frameH)
          .setVisible(false);
        (i < max ? far : near).add(s);
        this.crows.push({ s, x: 0, y: 0, vx: 0, ph: 0 });
      }
      this.nextFlight = TITLE_UI.dark.crowStartMs;
    }
  }

  update(t: number, dtMs: number): void {
    const reduced = this.reduced();
    const dt = Math.min(dtMs, TITLE_UI.emberMaxDtMs) / 1000;
    for (const { t: ts, r } of this.rains) {
      if (reduced) {
        ts.setVisible(r.layer === 'far').setAlpha(TITLE_UI.dark.reducedRainAlpha);
        continue;
      }
      ts.setVisible(true).setAlpha(r.alpha);
      ts.tilePositionX -= (r.vx * dt) / r.scale;
      ts.tilePositionY -= (r.vy * dt) / r.scale;
    }
    const cs = this.spec.crows;
    if (!cs || !this.crows.length) return;
    if (reduced) {
      for (const c of this.crows) c.s.setVisible(false).stop();
      return;
    }
    if (t >= this.nextFlight && !this.crows.some((c) => c.s.visible)) this.launch(cs);
    if (t >= this.nextFlight) this.nextFlight = t + rand(cs.intervalMs[0], cs.intervalMs[1]);
    for (const c of this.crows) {
      if (!c.s.visible) continue;
      c.x += c.vx * dt;
      c.ph += (2 * Math.PI * dtMs) / cs.swayMs;
      c.s.setPosition(Math.round(c.x - CX), Math.round(c.y + Math.sin(c.ph) * cs.swayPx - CY));
      if ((c.vx > 0 && c.x > ART_W + 120) || (c.vx < 0 && c.x < -120)) c.s.setVisible(false).stop();
    }
  }

  /** 한 떼: 같은 방향·같은 높이 근처, 몸 크기에 따라 먼 층/가까운 층 */
  private launch(cs: CrowSpec): void {
    const lg = this.spec.logo;
    const box = this.spec.logoBox;
    const y0 = crowFlightY(
      Math.random(),
      cs.y,
      box ? [lg.x + box[0], lg.y + box[1], lg.x + box[2], lg.y + box[3]] : null,
      cs.swayPx,
      cs.frameH,
    );
    if (y0 === null) return;
    const dir = Math.random() < 0.5 ? 1 : -1;
    const n = Math.round(rand(cs.count[0], cs.count[1]));
    const half = this.crows.length / 2;
    let farUsed = 0;
    let nearUsed = 0;
    for (let i = 0; i < n; i++) {
      const sc = rand(cs.scale[0], cs.scale[1]);
      const near = sc >= cs.nearScale;
      const idx = near ? half + nearUsed++ : farUsed++;
      const c = this.crows[idx];
      if (!c || (near ? nearUsed : farUsed) > half) continue;
      const lag = i * rand(cs.spread[0], cs.spread[1]);
      c.x = dir > 0 ? -80 - lag : ART_W + 80 + lag;
      // 떼는 아래쪽으로만 흩어진다 (로고 상자 쪽으로 올라가지 않게)
      c.y = Math.min(cs.y[1], y0 + i * rand(0, cs.spread[0] / 2));
      c.vx = dir * rand(cs.speed[0], cs.speed[1]);
      c.ph = Math.random() * Math.PI * 2;
      c.s
        .setScale(sc)
        .setFlipX(dir < 0)
        .setVisible(true)
        .play({ key: CROW_ANIM, startFrame: i % cs.frames });
    }
  }

  /** 디버그 */
  count(): number {
    return this.crows.filter((c) => c.s.visible).length;
  }

  destroy(): void {
    for (const r of this.rains) r.t.destroy();
    for (const c of this.crows) c.s.destroy();
    this.rains = [];
    this.crows = [];
  }
}

/** 그림 한 장을 번호 프레임(왼→오, 위→아래)으로 나눈다 — 스프라이트시트로 읽지 않은 그림(JSON 이 크기를 알려 준다) */
export function sliceSheet(scene: Phaser.Scene, key: string, fw: number, fh: number): void {
  const tex = scene.textures.get(key);
  const img = tex.getSourceImage();
  const cols = Math.max(1, Math.floor(img.width / fw));
  const rows = Math.max(1, Math.floor(img.height / fh));
  for (let i = 0; i < cols * rows; i++)
    if (!tex.has(String(i))) tex.add(i, 0, (i % cols) * fw, Math.floor(i / cols) * fh, fw, fh);
}
