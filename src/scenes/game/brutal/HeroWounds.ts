/**
 * P21 주인공 상흔 (계약 dark-brutal §3·§7): HP 비율로 단계 0~3 (회복하면 내려간다), 원거리 피격마다 박힌 화살(최대 5, 노드가 바뀌면 사라짐 —
 * 씬 재시작), 피격 때 붉은 피가 아니라 검은 타르 + 불씨 + 재, 단계 2·3 은 몸에서 불씨가 샌다, HP ≤ 25% 진입·이탈 LOW_HP.
 * 그림: 상흔 오버레이 `hero_wound<n>_<본 시트>`(본 시트와 같은 프레임 — 몸 위에 같은 변환으로 겹침). 없으면 몸 곱 틴트만(단계별).
 * 박힌 화살 `stuck_arrow`(앵커별 프레임 5) 없으면 짧은 막대. 타르 `tar_ember_hit` 없으면 점. 불씨는 보정 없는 층(원래 색).
 */
import Phaser from 'phaser';
import { BRUTAL, DEPTH, TEXTURES } from '../../../core/Constants';
import {
  EventBus,
  Events,
  type LowHpPayload,
  type PlayerDamagedPayload,
  type PlayerWoundedPayload,
} from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { heroWoundStage } from '../../../systems/gore/rules';
import { ungradedOf } from '../../../systems/fx/colorGrade';
import { settings } from '../../../systems/settings';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { GORE_FX, heroWoundName } from './brutalArt';
import { fxSheet, type GoreSheet } from './goreArt';
import type { Game } from '../../Game';

const TEX_DOT = 'gore_dot';
const TEX_STICK = 'gore_stamp';
const PLAYER_KEY = `${TEXTURES.SHEET_PREFIX}player_`;
/** 상흔 단계별 숯 부스러기 간격 [최소, 최대] ms (art §37 ash_chips suggestIntervalMs) */
const ASH_EVERY: Record<number, [number, number]> = { 1: [1200, 2000], 2: [800, 1200], 3: [500, 800] };

export class HeroWounds {
  stage: 0 | 1 | 2 | 3;
  arrows = 0;
  lowHp = false;
  private readonly overlay: Phaser.GameObjects.Sprite;
  private readonly stuck: { img: Phaser.GameObjects.Image; anchor: string }[] = [];
  private emberAt = 0;
  private ashAt = 0;
  private started = false;
  /** 디버그: 오버레이를 그렸는가 · 틴트 대체 */
  mode: 'overlay' | 'tint' | 'hidden' | 'none' = 'none';

  constructor(private readonly g: Game) {
    this.stage = heroWoundStage(gameState.hp, gameState.maxHp);
    this.overlay = g.add.sprite(0, 0, '__DEFAULT').setVisible(false);
    EventBus.on(Events.PLAYER_DAMAGED, this.onDamaged, this);
    EventBus.on(Events.PLAYER_HEALED, this.refresh, this);
    g.events.on(Phaser.Scenes.Events.POST_UPDATE, this.sync, this);
    g.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  /** 계약 `UiSnapshot.player.wound` */
  toUi(): PlayerWoundedPayload {
    return { stage: this.stage, arrows: this.arrows };
  }

  /** 원거리 피격 (GameCombat.onProjectileHit — 맞았을 때만) */
  addArrow(dirX: number, dirY: number): void {
    if (this.arrows >= BRUTAL.HERO.MAX_ARROWS) return;
    const anchor = BRUTAL.HERO.ARROW_ANCHORS[this.arrows];
    this.arrows += 1;
    this.stuck.push({ img: this.arrowImage(Math.atan2(dirY, dirX)), anchor });
    this.emit({ arrowAdded: true });
  }

  private onDamaged(p: PlayerDamagedPayload): void {
    if (!p.guarded && p.amount > 0) this.splash(p.source);
    this.refresh();
  }

  /** HP 로 단계·저HP 다시 (PLAYER_DAMAGED·HEALED · 첫 프레임) */
  private refresh(): void {
    const stage = heroWoundStage(gameState.hp, gameState.maxHp);
    if (stage !== this.stage) {
      const rose = stage > this.stage;
      this.stage = stage;
      this.emit({ rose });
    }
    const ratio = gameState.maxHp > 0 ? gameState.hp / gameState.maxHp : 1;
    const low = gameState.hp > 0 && ratio <= BRUTAL.HERO.LOW_HP_RATIO;
    if (low !== this.lowHp) {
      this.lowHp = low;
      EventBus.emit(Events.LOW_HP, { on: low, ratio: +ratio.toFixed(3) } satisfies LowHpPayload);
      this.g.brutal?.grade?.setLowHp(low);
    }
  }

  private emit(extra: Pick<PlayerWoundedPayload, 'rose' | 'arrowAdded'>): void {
    EventBus.emit(Events.PLAYER_WOUNDED, { ...this.toUi(), ...extra } satisfies PlayerWoundedPayload);
  }

  /** 매 프레임 (Game.update) — 첫 프레임에 이전 노드의 저HP 를 다시 알리고, 불씨를 흘린다 */
  update(time: number): void {
    if (!this.started) {
      this.started = true;
      // 노드가 바뀌어 씬이 다시 시작했다 — 저HP 신호(심장 박동)를 다시 켠다
      this.lowHp = false;
      this.refresh();
    }
    if (this.stage < 1 || !this.g.player?.visible) return;
    // art §37 ash_chips: 1단 1.2~2초 · 2단 0.8~1.2초 · 3단 0.5~0.8초마다 가슴에서 숯 부스러기
    if (time >= this.ashAt) {
      const [a, b] = ASH_EVERY[this.stage];
      this.ashAt = time + a + Math.random() * (b - a);
      this.ashChips();
    }
    if (this.stage < 2) return;
    const every = this.stage === 3 ? 140 : 320;
    if (time < this.emberAt) return;
    this.emberAt = time + every;
    const p = this.g.player;
    this.ember(p.x + (Math.random() - 0.5) * 10, p.y - 10 - Math.random() * 22, -0.2 - Math.random() * 0.4);
  }

  /** 숯 부스러기 (ash_chips — 시트가 없으면 없음) */
  private ashChips(): void {
    const p = this.g.player;
    if (!p || !this.g.fx.has(GORE_FX.ASH_CHIPS)) return;
    this.g.fx.play(GORE_FX.ASH_CHIPS, p.x + (Math.random() - 0.5) * 6, p.y - p.visual.hitLiftPx - 6, {
      depth: p.depth + DEPTH.OVERLAY_STEP * 0.6,
      hooks: false,
    });
  }

  /**
   * 몸 프레임이 정해진 뒤 (POST_UPDATE): 상흔 오버레이 `hero_wound<단계>_<몸 시트>` 를 몸과 같은 프레임·변환으로 (art §37 — 누적 그림이라
   * 현재 단계 하나만, 몸 바로 위·무기 오버레이 아래). 그 몸 시트에 오버레이가 없으면(특수기·처형·죽음 등) 숨김. 상흔 시트가 하나도 없으면
   * 몸 곱 틴트로 대신. 박힌 화살은 오버레이 json `arrowAnchors`(방향·프레임별 앵커) 자리에
   */
  private sync(): void {
    const host = this.g.player;
    if (!host?.active) {
      this.overlay.setVisible(false);
      return;
    }
    const key = host.texture.key;
    const action = key.startsWith(PLAYER_KEY) ? key.slice(PLAYER_KEY.length).split(/[@#]/)[0] : null;
    const frame = host.frame.name;
    const stage = this.stage > 0 ? this.stage : 1;
    const wdef = action ? (spriteLibrary.sheet(heroWoundName(stage), action) as GoreSheet | undefined) : undefined;
    const wkey = action ? spriteLibrary.textureKey(heroWoundName(stage), action) : null;
    const has = Boolean(wkey && this.g.textures.exists(wkey) && this.g.textures.get(wkey!).has(frame));
    if (this.stage > 0 && has) {
      this.mode = 'overlay';
      this.overlay
        .setTexture(wkey!, frame)
        .setPosition(host.x, host.y)
        .setOrigin(host.originX, host.originY)
        .setScale(host.scaleX, host.scaleY)
        .setFlipX(host.flipX)
        .setRotation(host.rotation)
        .setAlpha(host.alpha)
        .setDepth(host.depth + DEPTH.OVERLAY_STEP * 0.3)
        .setVisible(host.visible);
    } else {
      this.overlay.setVisible(false);
      const anySheet = spriteLibrary.has(heroWoundName(1), 'idle');
      this.mode = this.stage === 0 ? 'none' : anySheet ? 'hidden' : 'tint';
      // 상흔 시트가 아예 없을 때만: 몸이 재처럼 바랜다 (다른 상태 색이 없을 때만)
      if (this.mode === 'tint' && host.visual.animated && !host.isTinted)
        host.setTint(BRUTAL.HERO.STAGE_TINT[this.stage]);
    }
    this.placeArrows(host, wdef, has ? Number(frame) : NaN);
  }

  /** 박힌 화살: 앵커가 있으면 그 자리·프레임·좌우·앞뒤, 오버레이가 없는 몸 시트면 숨김. 앵커 시트가 없으면 임시 자리 */
  private placeArrows(host: Game['player'], wdef: GoreSheet | undefined, frameIndex: number): void {
    if (this.stuck.length === 0) return;
    const anchors = wdef?.arrowAnchors;
    const sheet = anchors ? fxSheet(this.g, GORE_FX.STUCK_ARROW) : null;
    if (anchors && sheet && wdef && Number.isFinite(frameIndex)) {
      const row = Math.floor(frameIndex / wdef.frames);
      const col = frameIndex % wdef.frames;
      const at = anchors[wdef.directions[row]]?.[col] ?? null;
      const k = Math.abs(host.scaleX);
      for (const s of this.stuck) {
        const a = at?.[s.anchor];
        if (!a || !host.visible) {
          s.img.setVisible(false);
          continue;
        }
        const dx = (a.x - wdef.pivot.x) * k * (host.flipX ? -1 : 1);
        s.img
          .setTexture(sheet.key, a.frame)
          .setOrigin(sheet.def.pivot.x / sheet.def.frameWidth, sheet.def.pivot.y / sheet.def.frameHeight)
          .setScale(sheet.scale)
          .setPosition(host.x + dx, host.y + (a.y - wdef.pivot.y) * Math.abs(host.scaleY))
          .setFlipX(a.flipX !== host.flipX)
          .setDepth(host.depth + DEPTH.OVERLAY_STEP * (a.depth === 'above' ? 0.35 : -0.5))
          .setVisible(true);
      }
      return;
    }
    if (anchors || spriteLibrary.has(heroWoundName(1), 'idle')) {
      // 상흔 시트는 있는데 이 몸 시트엔 없다 (특수기 등) — 숨김
      for (const s of this.stuck) s.img.setVisible(false);
      return;
    }
    const left = host.flipX || host.facingDir.includes('left');
    for (const s of this.stuck) {
      const o = BRUTAL.HERO.ARROW_OFFSETS[s.anchor] ?? [0, -20, 1];
      s.img
        .setPosition(host.x + (left ? -o[0] : o[0]), host.y + o[1])
        .setDepth(host.depth + DEPTH.OVERLAY_STEP * o[2] * 0.3)
        .setFlipX(left)
        .setVisible(host.visible);
    }
  }

  private arrowImage(angle: number): Phaser.GameObjects.Image {
    // 앵커 시트가 있으면 sync 가 텍스처·프레임을 정한다 — 여기서는 임시 막대 (화살이 날아온 반대쪽으로 꽂힌 꼬리)
    const H = BRUTAL.HERO;
    return this.g.add
      .image(0, 0, TEX_STICK)
      .setOrigin(0, 0.5)
      .setTint(H.ARROW_COLOR)
      .setScale(H.ARROW_LEN_PX / 8, 0.5)
      .setRotation(angle + Math.PI);
  }

  /** 피격: 검은 타르 + 불씨 + 재 (고어 0 은 재만) */
  private splash(source?: { dirX: number; dirY: number }): void {
    const g = this.g;
    const p = g.player;
    if (!p) return;
    const c = p.getCenter();
    const len = Math.hypot(source?.dirX ?? 0, source?.dirY ?? 0);
    const nx = len > 0 ? source!.dirX / len : 0;
    const ny = len > 0 ? source!.dirY / len : -1;
    const gore = settings.current().gore;
    if (gore > 0 && g.fx.has(GORE_FX.TAR_EMBER)) {
      // art §37: 오른쪽 기준 → 맞은 방향으로 회전 · flipY 허용 · 재 부스러기 한 번
      g.fx
        .play(GORE_FX.TAR_EMBER, c.x, c.y, { angle: Math.atan2(ny, nx), depth: DEPTH.HIT_FX, hooks: false })
        ?.sprite.setFlipY(Math.random() < 0.5);
      this.ashChips();
      return;
    }
    const H = BRUTAL.HERO;
    const n = gore === 0 ? 0 : H.TAR_DOTS;
    for (let i = 0; i < n + 3; i++) {
      const tar = i < n;
      const a = Math.atan2(ny, nx) + (Math.random() - 0.5) * 1.6;
      const d = H.SPLASH_PX * (0.4 + Math.random() * 0.6);
      const dot = g.add
        .image(c.x, c.y, TEX_DOT)
        .setTint(tar ? H.TAR_COLOR : H.ASH_COLOR)
        .setScale(tar ? 0.35 + Math.random() * 0.35 : 0.25)
        .setDepth(DEPTH.HIT_FX);
      g.tweens.add({
        targets: dot,
        x: c.x + Math.cos(a) * d,
        y: c.y + Math.sin(a) * d + (tar ? 8 : -6),
        alpha: 0,
        duration: H.SPLASH_MS * (0.7 + Math.random() * 0.6),
        ease: Phaser.Math.Easing.Quadratic.Out,
        onComplete: () => dot.destroy(),
      });
    }
    for (let i = 0; i < H.EMBER_DOTS; i++) this.ember(c.x, c.y, -0.6 - Math.random());
  }

  /** 불씨 한 점 (가산 · 보정 없는 층 — 어둠·색 보정에 묻히지 않는다) */
  private ember(x: number, y: number, vy: number): void {
    const g = this.g;
    const dot = g.add
      .image(x, y, TEX_DOT)
      .setTint(BRUTAL.HERO.EMBER_COLOR)
      .setScale(0.18 + Math.random() * 0.15)
      .setBlendMode(Phaser.BlendModes.ADD)
      .setDepth(DEPTH.HIT_FX + 0.01);
    ungradedOf(g)?.add(dot);
    g.tweens.add({
      targets: dot,
      x: x + (Math.random() - 0.5) * 10,
      y: y + vy * 26,
      alpha: 0,
      duration: 500 + Math.random() * 400,
      onComplete: () => dot.destroy(),
    });
  }

  destroy(): void {
    EventBus.off(Events.PLAYER_DAMAGED, this.onDamaged, this);
    EventBus.off(Events.PLAYER_HEALED, this.refresh, this);
    this.g.events.off(Phaser.Scenes.Events.POST_UPDATE, this.sync, this);
  }
}
