import Phaser from 'phaser';
import { LogoReveal } from './TitleLogoReveal';
import { EmberField } from './TitleEmbers';
import { TitleWeather, sliceSheet } from './TitleWeather';
import { DARK } from './themeP21';
import { vignetteImage } from './vignette';
import {
  ART_H,
  ART_TO_LOGIC,
  ART_W,
  TITLE_EMBERS,
  TITLE_UI,
  TITLE_WEAPONS,
  titleKey,
  type TitleImage,
  type TitleSpec,
} from './themeTitle';
import {
  VOICE_EMIT_LEVEL,
  breathPhase,
  clamp01,
  diveOrigin,
  diveZoom,
  emberFlicker,
  layerOffset,
  lerpStep,
  parallaxInput,
  voiceAlpha,
  voiceLevel,
} from './titleView';

/**
 * 62 타이틀 그림 층 (아트 §29 `title.json` 층 순서): far → 먼 안개 → 도시 불티 → mid → 들판 안개 → near(주인공·발광·
 * 무기 목소리·불티) → 발목 안개 → 로고. 배경 층은 가운데 기준 scale(cover) 로 깔아 패럴랙스 끝에서도 가장자리가 비지 않는다.
 * 각 층은 Container(가운데 원점 = 화면 (960,540) 아트 px, 배율 0.5×cover) 하나 — 자식 좌표는 아트 px 그대로 (x-960, y-540).
 */
interface Layer {
  c: Phaser.GameObjects.Container;
  factor: number;
}

const CX = ART_W / 2;
const CY = ART_H / 2;

export class TitleArt {
  private layers: Layer[] = [];
  private hero?: Phaser.GameObjects.Image;
  private glow?: Phaser.GameObjects.Image;
  private voices: Phaser.GameObjects.Image[] = [];
  private fogs: { t: Phaser.GameObjects.TileSprite; speed: number }[] = [];
  /** P21: title.json 새 층 중 일렁이는 것 (기본 알파) */
  private flickers: { im: Phaser.GameObjects.Image | Phaser.GameObjects.TileSprite; alpha: number }[] = [];
  private vignette?: Phaser.GameObjects.Image;
  /** P21: 비·까마귀 · 젖은 재 */
  private weather?: TitleWeather;
  private ash?: EmberField;
  private logoTop?: Phaser.GameObjects.Image;
  private logoSub?: Phaser.GameObjects.Image;
  private dots: Phaser.GameObjects.Image[] = [];
  private nearEmbers?: EmberField;
  private cityEmbers?: EmberField;
  private off = { x: 0, y: 0 };
  private levels: number[] = [];
  /** 등장 연출이 정하는 값 (0~1) */
  intro = { logo: 1, sub: 1, dots: [1, 1, 1, 1] as number[] };
  reduced = false;
  /** 첫 생으로 파고들기 0~1 (0 = 없음) */
  dive = 0;
  /** art §30 로고 쓰기 진행도 (씬이 매 프레임 넣는다) — 1 이면 끝 */
  revealP = 0;
  private reveal?: LogoReveal;
  private farLayer?: Phaser.GameObjects.Container;
  private midLayer?: Phaser.GameObjects.Container;
  private nearLayer?: Phaser.GameObjects.Container;

  constructor(
    private scene: Phaser.Scene,
    private spec: TitleSpec,
  ) {
    const has = (n: TitleImage | typeof TITLE_EMBERS): boolean => scene.textures.exists(titleKey(n));
    const D = TITLE_UI.depth;
    const P = TITLE_UI.parallax;
    const far = this.layer(D.far, spec.layers.far);
    this.farLayer = far;
    if (has('title_bg_far')) far.add(this.img('title_bg_far', 0, 0));
    const fogFar = this.layer(D.fogFar, P.fogFar);
    const city = this.layer(D.city, P.cityEmbers);
    const mid = this.layer(D.mid, spec.layers.mid);
    this.midLayer = mid;
    if (has('title_bg_mid')) mid.add(this.img('title_bg_mid', 0, 0));
    const fogMid = this.layer(D.fogMid, P.fogMid);
    const near = this.layer(D.near, spec.layers.near);
    this.nearLayer = near;
    if (has('title_bg_near')) near.add(this.img('title_bg_near', 0, 0));
    const fogNear = this.layer(D.fogNear, P.fogNear);
    // 주인공 호흡 덧그림: 원점 = 발
    const h = spec.hero;
    if (has('title_hero')) {
      const oy = Phaser.Math.Clamp((h.feetY - h.y) / h.h, 0, 1);
      this.hero = scene.add.image(h.x + h.w / 2 - CX, h.feetY - CY, titleKey('title_hero')).setOrigin(0.5, oy);
      near.add(this.hero);
    }
    if (has('title_fx_glow_hero')) {
      this.glow = this.img('title_fx_glow_hero', spec.glow.x, spec.glow.y).setBlendMode(Phaser.BlendModes.ADD);
      near.add(this.glow);
    }
    for (const v of spec.voices) {
      const n = `title_fx_voice_${v.weapon}` as TitleImage;
      if (!has(n)) continue;
      const im = this.img(n, v.x, v.y).setBlendMode(Phaser.BlendModes.ADD).setAlpha(v.alpha[0]);
      im.setData('weapon', v.weapon);
      near.add(im);
      this.voices.push(im);
    }
    // 안개 3겹 (가로 반복, 좌→우)
    const fogLayers = [fogFar, fogMid, fogNear];
    if (has('title_fx_fog')) {
      spec.fog.forEach((f, i) => {
        const pad = 64;
        const t = scene.add
          .tileSprite(-CX - pad, f.y - CY, ART_W + pad * 2, 321, titleKey('title_fx_fog'))
          .setOrigin(0, 0)
          .setScale(1, f.scaleY)
          .setAlpha(f.alpha);
        fogLayers[Math.min(i, fogLayers.length - 1)].add(t);
        this.fogs.push({ t, speed: f.speed });
      });
    }
    // P21: title.json 에 새로 들어온 그림 층 (비·재·까마귀 등 — 읽힌 것만)
    for (const ex of spec.extras) {
      if (!scene.textures.exists(titleKey(ex.image))) continue;
      const c = this.layer(ex.depth, ex.parallax);
      const blend = Phaser.BlendModes[ex.blend];
      let im: Phaser.GameObjects.Image | Phaser.GameObjects.TileSprite;
      if (ex.speed !== 0) {
        const pad = 64;
        const h = scene.textures.get(titleKey(ex.image)).getSourceImage().height;
        const t = scene.add.tileSprite(-CX - pad, ex.y - CY, ART_W + pad * 2, h, titleKey(ex.image)).setOrigin(0, 0);
        this.fogs.push({ t, speed: ex.speed });
        im = t;
      } else im = scene.add.image(ex.x - CX, ex.y - CY, titleKey(ex.image)).setOrigin(0, 0);
      im.setBlendMode(blend).setAlpha(ex.alpha);
      c.add(im);
      if (ex.flicker) this.flickers.push({ im, alpha: ex.alpha });
    }
    // P21: 가장자리 먹 비네트 (발목 안개 앞 · 로고 뒤 — 패럴랙스 없음)
    this.vignette = vignetteImage(scene, DARK.ink, TITLE_UI.dark.vignette.depth).setAlpha(TITLE_UI.dark.vignette.alpha);
    // P21 날씨: 비 두 겹 · 까마귀 떼 (title.json rain·crows) · 젖은 재 (ash)
    this.weather = new TitleWeather(
      scene,
      spec,
      (d, f) => this.layer(d, f),
      () => this.reduced,
    );
    const ash = spec.ash;
    if (ash && scene.textures.exists(titleKey('title_fx_ash'))) {
      sliceSheet(scene, titleKey('title_fx_ash'), ash.sheet.frameW, ash.sheet.frameH);
      this.ash = new EmberField(
        scene,
        this.layer(ash.depth, 1),
        titleKey('title_fx_ash'),
        ash.sheet,
        ash.emitters,
        60,
        {
          speedK: 1,
          scale: ash.scale,
          inMs: ash.inMs,
          outMs: ash.outMs,
        },
      );
    }
    // 불티 (도시 = far 와 mid 사이, 그 밖 = 주인공 층 위)
    if (has(TITLE_EMBERS)) {
      const cityCap = 12;
      this.cityEmbers = new EmberField(
        scene,
        city,
        titleKey(TITLE_EMBERS),
        spec.embers,
        spec.emitters.filter((e) => e.layer === 'city'),
        cityCap,
      );
      this.nearEmbers = new EmberField(
        scene,
        near,
        titleKey(TITLE_EMBERS),
        spec.embers,
        spec.emitters.filter((e) => e.layer === 'near'),
        TITLE_UI.emberCap - cityCap,
      );
    }
    // 로고 (패럴랙스 0, 1:1) — 글자와 부제를 따로 나타나게 두 조각으로
    const lg = spec.logo;
    if (has('title_logo')) {
      const tex = scene.textures.get(titleKey('title_logo'));
      if (!tex.has('top')) tex.add('top', 0, 0, 0, lg.w, lg.splitY);
      if (!tex.has('sub')) tex.add('sub', 0, 0, lg.splitY, lg.w, lg.h - lg.splitY);
      const s = ART_TO_LOGIC;
      this.logoTop = scene.add
        .image(lg.x * s, lg.y * s, titleKey('title_logo'), 'top')
        .setOrigin(0, 0)
        .setScale(s)
        .setDepth(D.logo);
      this.logoSub = scene.add
        .image(lg.x * s, (lg.y + lg.splitY) * s, titleKey('title_logo'), 'sub')
        .setOrigin(0, 0)
        .setScale(s)
        .setDepth(D.logo);
      // art §30 로고 쓰기: 마스크가 있으면 붓 순서대로 써 내려간다 (끝나면 위 두 조각으로)
      if (has('title_logo_reveal') && spec.logoReveal)
        this.reveal = new LogoReveal(
          scene,
          titleKey('title_logo'),
          titleKey('title_logo_reveal'),
          titleKey('title_logo_reveal_canvas'),
          lg.x * s,
          lg.y * s,
          s,
          D.logo,
          spec.logoReveal.softBand,
        );
      // 무기 불씨 4개: 목소리와 같은 순서·같은 색으로 밝아지는 덧불
      if (has(TITLE_EMBERS)) {
        const rows = spec.embers.rowNames;
        const [px, py] = spec.embers.pivot;
        for (const w of TITLE_WEAPONS) {
          const [dx, dy] = lg.dots[w];
          const row = Math.max(0, rows.indexOf(w));
          const d = scene.add
            .image(dx * s, dy * s, titleKey(TITLE_EMBERS), row * spec.embers.perRow)
            .setOrigin(px / spec.embers.frameW, py / spec.embers.frameH)
            .setScale(s)
            .setBlendMode(Phaser.BlendModes.ADD)
            .setDepth(D.logo + 0.5)
            .setAlpha(0);
          d.setData('row', row);
          this.dots.push(d);
        }
      }
    }
    this.levels = spec.voices.map(() => 0);
  }

  /** 로고 그림이 있는가 (없으면 씬이 글자 로고로 대신) */
  hasLogo(): boolean {
    return Boolean(this.logoTop);
  }

  private layer(depth: number, factor: number): Phaser.GameObjects.Container {
    const s = ART_TO_LOGIC * this.spec.parallax.cover;
    const c = this.scene.add
      .container(CX * ART_TO_LOGIC, CY * ART_TO_LOGIC)
      .setScale(s)
      .setDepth(depth);
    this.layers.push({ c, factor });
    return c;
  }

  /** 아트 좌표 (x,y) 왼쪽 위에 놓는 그림 (가운데 원점 컨테이너 기준) */
  private img(name: TitleImage, x: number, y: number): Phaser.GameObjects.Image {
    return this.scene.add.image(x - CX, y - CY, titleKey(name)).setOrigin(0, 0);
  }

  /** 매 프레임. t = 씬 시작 뒤 ms, pointer = 화면 가운데 기준 -1..1 (없으면 null) */
  update(t: number, dtMs: number, pointer: { x: number; y: number } | null): void {
    const sp = this.spec;
    // 패럴랙스
    const input = parallaxInput(pointer, t, sp.parallax, this.reduced);
    if (this.reduced) this.off = { x: 0, y: 0 };
    else {
      this.off.x = lerpStep(this.off.x, input.x, sp.parallax.lerp, dtMs);
      this.off.y = lerpStep(this.off.y, input.y, sp.parallax.lerp, dtMs);
    }
    const base = ART_TO_LOGIC * sp.parallax.cover;
    const { x: gx, y: gy } = this.spec.gate;
    const focus = {
      x: (CX + (base * (gx - CX)) / ART_TO_LOGIC) * ART_TO_LOGIC,
      y: (CY + (base * (gy - CY)) / ART_TO_LOGIC) * ART_TO_LOGIC,
    };
    const center = { x: CX * ART_TO_LOGIC, y: CY * ART_TO_LOGIC };
    for (const l of this.layers) {
      const ox = layerOffset(this.off.x, l.factor, sp.parallax.maxX);
      const oy = layerOffset(this.off.y, l.factor, sp.parallax.maxY);
      const pos = { x: (CX + ox) * ART_TO_LOGIC, y: (CY + oy) * ART_TO_LOGIC };
      if (this.dive > 0) {
        const z = diveZoom(this.dive, l.factor, TITLE_UI.dive.zoom);
        const o = diveOrigin(pos, focus, z, center, this.dive * TITLE_UI.dive.pull);
        l.c.setPosition(o.x, o.y).setScale(base * z);
      } else l.c.setPosition(pos.x, pos.y).setScale(base);
    }
    // 호흡 (주인공 scaleY + 빛무리 알파, 같은 위상)
    const b = breathPhase(t, sp.hero.breathMs);
    this.hero?.setScale(1, sp.hero.scaleY[0] + (sp.hero.scaleY[1] - sp.hero.scaleY[0]) * b);
    // P21: 불씨처럼 일렁인다 (모션 줄이기면 고정)
    const fl = (seed: number): number => (this.reduced ? 1 : emberFlicker(t, seed, TITLE_UI.dark.flicker));
    this.glow?.setAlpha((sp.glow.alpha[0] + (sp.glow.alpha[1] - sp.glow.alpha[0]) * b) * fl(0));
    this.flickers.forEach((f, i) => f.im.setAlpha(f.alpha * fl(11 + i)));
    // 무기 목소리 (9.6초 한 바퀴)
    sp.voices.forEach((v, i) => {
      this.levels[i] = voiceLevel(t, v);
    });
    for (const im of this.voices) {
      const i = sp.voices.findIndex((v) => v.weapon === im.getData('weapon'));
      if (i >= 0) im.setAlpha(voiceAlpha(this.levels[i], sp.voices[i].alpha) * fl(5 + i));
    }
    // 로고 불씨: 등장 점등 × (기본 0.35 + 목소리 세기)
    const perFrame = 1000 / sp.embers.fps;
    this.dots.forEach((d, i) => {
      const w = TITLE_WEAPONS[i];
      const vi = sp.voices.findIndex((v) => v.weapon === w);
      const lv = vi >= 0 ? this.levels[vi] : 0;
      // 로고 쓰기 중에는 마스크의 불씨 구간(embersAt) 전까지 꺼 둔다
      const lr = this.spec.logoReveal;
      const lit = this.reveal && lr && this.revealP < lr.embersAt ? 0 : (this.intro.dots[i] ?? 1);
      // 점등 순간 한 번 반짝 (0→1 구간 가운데에서 최고)
      const pop = lit > 0 && lit < 1 ? Math.sin(lit * Math.PI) * TITLE_UI.dark.dotPop : 0;
      d.setAlpha(clamp01(lit * (0.35 + 0.65 * lv) * fl(1 + i) + pop));
      d.setFrame(
        (d.getData('row') as number) * sp.embers.perRow + (Math.floor(t / perFrame + i * 2) % sp.embers.perRow),
      );
    });
    // 로고: 쓰는 동안은 마스크 그림, 끝나면 원래 두 조각 (dive 의 알파 줄이기는 원래 조각에)
    if (this.reveal) {
      this.reveal.set(this.revealP);
      if (this.reveal.finished) {
        this.reveal.destroy();
        this.reveal = undefined;
      }
    }
    const writing = Boolean(this.reveal);
    this.logoTop?.setAlpha(writing ? 0 : this.intro.logo);
    this.logoSub?.setAlpha(writing ? 0 : this.intro.sub);
    // 안개·재 (P21: 느리게 · 모션 줄이기면 멈춤)
    const fk = TITLE_UI.dark.fogSpeedK;
    if (!this.reduced) for (const f of this.fogs) f.t.tilePositionX -= (f.speed * fk * dtMs) / 1000;
    // 불티
    const rows = sp.embers.rowNames;
    const vOn = (i: number): boolean => (this.levels[i] ?? 0) >= VOICE_EMIT_LEVEL;
    const vRow = (i: number): number => Math.max(0, rows.indexOf(sp.voices[i].weapon));
    const vOrigin = (i: number): [number, number] => sp.voices[i].ember;
    this.cityEmbers?.update(dtMs, vOn, vRow, vOrigin, sp.voices.length);
    this.nearEmbers?.update(dtMs, vOn, vRow, vOrigin, sp.voices.length);
    this.weather?.update(t, dtMs);
    // 젖은 재: 모션 줄이기면 초당 1 — shortcut: dt 를 줄여 방출과 낙하가 함께 느려진다, 방출만 줄여야 하면 EmberField 에 rate 배율
    const ashRate = this.spec.ash?.emitters[0]?.rate[1] ?? 1;
    const ashK = this.reduced ? Math.min(1, TITLE_UI.dark.reducedAshRate / ashRate) : 1;
    this.ash?.update(dtMs * ashK, vOn, vRow, vOrigin, 0);
  }

  /** 성문(파고들 자리)의 지금 화면 좌표 (논리 px) — art §30 `gate.layer` 층 기준 (패럴랙스·cover 배율 반영) */
  gateScreen(): { x: number; y: number } {
    const g = this.spec.gate;
    const c = g.layer === 'mid' ? this.midLayer : g.layer === 'near' ? this.nearLayer : this.farLayer;
    if (!c) return { x: g.x * ART_TO_LOGIC, y: g.y * ART_TO_LOGIC };
    return { x: c.x + c.scaleX * (g.x - CX), y: c.y + c.scaleY * (g.y - CY) };
  }

  /** 디버그: 지금 값 */
  stats(): { embers: number; ash: number; crows: number; offset: { x: number; y: number }; levels: number[] } {
    return {
      embers: (this.cityEmbers?.count() ?? 0) + (this.nearEmbers?.count() ?? 0),
      ash: this.ash?.count() ?? 0,
      crows: this.weather?.count() ?? 0,
      offset: { x: Math.round(this.off.x * 100) / 100, y: Math.round(this.off.y * 100) / 100 },
      levels: this.levels.map((l) => Math.round(l * 100) / 100),
    };
  }

  destroy(): void {
    this.cityEmbers?.destroy();
    this.nearEmbers?.destroy();
    this.ash?.destroy();
    this.weather?.destroy();
    for (const l of this.layers) l.c.destroy();
    this.layers = [];
    this.reveal?.destroy();
    this.reveal = undefined;
    this.vignette?.destroy();
    this.flickers = [];
    this.logoTop?.destroy();
    this.logoSub?.destroy();
    for (const d of this.dots) d.destroy();
  }
}
