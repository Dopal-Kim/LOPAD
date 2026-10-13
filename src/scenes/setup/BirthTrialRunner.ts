/**
 * 탄생 전장 회피 시험 (화면 쪽, 62 루프 1 — P0-2 · 계약 UI §20 trial): 첫 생 3획 뒤, 황폐한 탄생지 타일(route 탄생 노드와 같은 타일셋)
 * 위에서 사수(적 그림 archer)가 실제로 겨누고 쏜다. 과제 `RITUAL_DATA.trial.tasks` 를 차례로:
 * 이름 카드(card — 움직일 수 있고 사격 없음) → 사격(run — volleys 번, 쏘기 전 겨눔 선) → 남은 화살이 다 사라지면 끝(clear) → 다음 과제.
 * 맞으면 밀려난다(피격 수). 옛 허공 무대·떨어짐·갉아먹힘(51라운드 dodgeTrial)은 폐지. 과제 목록은 UI 가 그린다(스냅샷 ritual.trial).
 * 좌표는 월드 px (Setup 이 메인 카메라를 zoom 배로 전투장 가운데에 맞춘다).
 */
import Phaser from 'phaser';
import { DEPTH, RITUAL_TRIAL_FEEL, TILE } from '../../core/Constants';
import { PALETTE } from '../../data';
import type { RitualTrialData, TrialTaskDef } from '../../data/ritual';
import { EntityVisual } from '../../objects/EntityVisual';
import { generateArena } from '../../systems/mapgen/arena';
import { TileWorld } from '../../world/TileWorld';
import { propSkinFor, skinFor } from '../../world/tileskin';
import { FxPool } from '../../systems/fx/fx';
import { hexToInt, rampFor } from '../../systems/palette';
import { audio } from '../../systems/audio/audio';
import { SFX } from '../../systems/audio/audioMap';
import { facing8Of, facingOf } from '../../systems/sprites/spriteDirs';
import { fanAngles, shooterFor, spotAt } from '../../systems/ritual/ritual';
import { TrialArrows } from './trialArrows';
import { TrialPlayer, type TrialGround, type TrialInput } from './trialPlayer';
import { placeTrialProps, propTiles } from './trialProps';
import type { StructureView } from '../../world/StructureView';
import { Lighting } from '../../systems/lighting/Lighting';
import { lightingAmbientFor } from '../../systems/lighting/lightMath';
import { LIGHTING } from '../../data';

export type { TrialInput } from './trialPlayer';
export type BirthTrialState = 'card' | 'run' | 'clear' | 'done';

export interface BirthTrialTaskResult {
  id: string;
  hits: number;
  done: boolean;
}

export interface BirthTrialStatus {
  state: BirthTrialState;
  index: number;
  tasks: BirthTrialTaskResult[];
  hits: number;
}

interface Shooter {
  sprite: Phaser.Physics.Arcade.Sprite;
  visual: EntityVisual;
  x: number;
  y: number;
}

/** 쏘기 예약: 겨눔(telegraph) 시작 → fireAt 에 쏜다 (겨눔 방향은 시작 때 고정 — 읽으면 피할 수 있게) */
interface Volley {
  shooter: number;
  aim: number;
  fireAt: number;
}

const ARENA_SEED = 62_001;
/** 사수·주인공 자리 둘레 비우는 칸 (소품이 덮지 않게) */
const CLEAR_TILES = 1;

export class BirthTrialRunner {
  state: BirthTrialState = 'card';
  readonly results: BirthTrialTaskResult[];
  readonly world: TileWorld;
  /** 전투장 내부 (월드 px) */
  readonly area: { x: number; y: number; w: number; h: number };
  private readonly fx: FxPool;
  private readonly player: TrialPlayer;
  private readonly ground: TrialGround;
  private readonly arrows: TrialArrows;
  private readonly shooters: Shooter[] = [];
  private readonly aimLine: Phaser.GameObjects.Graphics;
  /** art §30 탄생 전장 소품 (엄폐·장식) */
  private readonly props: StructureView[];
  private index = 0;
  private phaseEnd = 0;
  private fired = 0;
  private nextVolleyAt = 0;
  private pending: Volley[] = [];
  /** 62 I (P1-N8): 탄생 전장과 같은 어둠·주인공 빛·비네팅 (평평하게 밝던 무대) */
  private readonly lighting: Lighting;
  private readonly lightTarget = { x: 0, y: 0, visible: true };

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly data: RitualTrialData,
    /** 과제·상태가 바뀔 때 (UI 스냅샷 갱신) */
    private readonly onChange: () => void,
    /** 전부 끝 (맞은 수 합계) */
    private readonly onDone: (hits: number) => void,
  ) {
    this.results = data.tasks.map((t) => ({ id: t.id, hits: 0, done: false }));
    const [w, h] = data.arenaTiles;
    const layout = generateArena({
      roomId: 'birth-trial',
      type: 'start',
      floor: 'start',
      w,
      h,
      margin: 0,
      spawnInset: 2,
      exitInset: 2,
      spawnExactCenter: true,
      seed: ARENA_SEED,
    });
    const I = layout.rooms[0].interior;
    this.area = { x: I.x * TILE, y: I.y * TILE, w: I.w * TILE, h: I.h * TILE };
    const keep = new Set<string>();
    for (const r of [...data.spots, data.start]) {
      const p = spotAt(r, this.area);
      const tx = Math.floor(p.x / TILE);
      const ty = Math.floor(p.y / TILE);
      for (let dy = -CLEAR_TILES; dy <= CLEAR_TILES; dy++)
        for (let dx = -CLEAR_TILES; dx <= CLEAR_TILES; dx++) keep.add(`${tx + dx},${ty + dy}`);
    }
    // 소품 자리도 무작위 바닥 소품이 피한다
    for (const p of data.props) {
      const t = propTiles(p, this.area);
      for (let y = t.ty; y < t.ty + t.h; y++) for (let x = t.tx; x < t.tx + t.w; x++) keep.add(`${x},${y}`);
    }
    this.world = new TileWorld(scene, layout, skinFor(1, data.tileset), ARENA_SEED, keep, {
      boundaryWalls: true,
      propSkin: propSkinFor(data.tileset),
    });
    // 엄폐: 칸을 막아 걷기·화살(걸을 수 없는 칸에서 부서짐)을 막는다
    const placed = placeTrialProps(scene, data.props, this.area);
    this.props = placed.views;
    for (const c of placed.solid) this.world.setBlocked(c.tx, c.ty, true);
    const ramp = (rampFor(PALETTE, 1) ?? []).map(hexToInt);
    this.fx = new FxPool(scene);
    this.player = new TrialPlayer(scene, this.fx, ramp[8] ?? 0xffffff, ramp[6] ?? 0xffffff);
    const R = RITUAL_TRIAL_FEEL.PLAYER.FOOT_RADIUS_PX;
    const foot = RITUAL_TRIAL_FEEL.PLAYER.FOOT_OFFSET_PX;
    const open = (x: number, y: number) => this.world.isWalkableAt(x, y);
    // 주인공 발: 벽·단단한 소품 + 보이는 사수 몸에 막힌다
    const stand = (x: number, y: number) => open(x, y) && !this.shooterAt(x, y);
    this.ground = {
      standScore: (x, y) =>
        [
          [R, 0],
          [-R, 0],
          [0, R],
          [0, -R],
        ].filter(([dx, dy]) => stand(x + dx, y + foot + dy)).length,
      pushOut: (x, y) => (stand(x, y + foot) ? { x, y } : { x: this.player.pos.x, y: this.player.pos.y }),
    };
    this.arrows = new TrialArrows(scene, this.fx, open);
    this.aimLine = scene.add.graphics().setDepth(DEPTH.PROJECTILE - DEPTH.OVERLAY_STEP);
    data.spots.forEach((r) => this.shooters.push(this.makeShooter(spotAt(r, this.area))));
    // 소품 불(StructureView 광원)·벽 횃불(타일 광원)은 장면 광원 목록에 이미 있다 — 조명이 그것을 그린다
    const ambient = data.region ? lightingAmbientFor(data.region, null, true, () => true, LIGHTING) : null;
    this.lighting = new Lighting(scene, { ambient, player: this.lightTarget });
  }

  /** 전투장 가운데 (카메라) */
  get center(): { x: number; y: number } {
    // 62 I (P1-N8): 그려진 무대(바닥 + 둘레 벽 + 북쪽 벽 앞면 높이) 가운데 — 위·아래 여백이 같게
    const up = (this.world.skin.quarter?.heightTiles ?? 0) * TILE;
    const top = this.area.y - TILE - up;
    const bottom = this.area.y + this.area.h + TILE;
    return { x: this.area.x + this.area.w / 2, y: (top + bottom) / 2 };
  }

  get task(): TrialTaskDef {
    return this.data.tasks[Math.min(this.index, this.data.tasks.length - 1)];
  }

  /** 디버그: 맞지 않음 */
  get god(): boolean {
    return this.player.god;
  }

  set god(on: boolean) {
    this.player.god = on;
  }

  start(time: number): void {
    const s = spotAt(this.data.start, this.area);
    this.player.reset(s.x, s.y, time);
    this.beginCard(0, time);
  }

  status(): BirthTrialStatus {
    return {
      state: this.state,
      index: this.index,
      tasks: this.results.map((r) => ({ ...r })),
      hits: this.results.reduce((n, r) => n + r.hits, 0),
    };
  }

  /** 디버그 요약 */
  snapshot(): Record<string, unknown> {
    return {
      ...this.status(),
      player: { x: Math.round(this.player.pos.x), y: Math.round(this.player.pos.y) },
      arrows: { alive: this.arrows.alive, fired: this.arrows.fired, broken: this.arrows.broken },
      props: this.props.length,
      // art §30: stage1_waste 13~16 은 바닥 변주 — 바닥 타일셋 소품 표에 남아 있으면 안 된다 (쿼터뷰는 v3 소품 시트를 쓴다)
      tileset: {
        quarter: Boolean(this.world.skin.quarter),
        floorPropIdx: this.world.skin.props.map((p) => p.index).filter((i) => i >= 13 && i <= 16),
        floorVariants: this.world.layer.layer.data.flat().filter((t) => t.index >= 13 && t.index <= 16).length,
        propsLayer: Boolean(this.world.propsLayer),
      },
      shooters: this.shooters.filter((s) => s.sprite.visible).length,
      animated: this.shooters.map((s) => s.visual.animated),
    };
  }

  /** 이름 카드를 넘긴다 (card 일 때만) */
  skipCard(time: number): boolean {
    if (this.state !== 'card') return false;
    this.beginRun(time);
    return true;
  }

  /** 디버그: 지금 과제를 끝낸다 (hits 를 덮어쓰면 그 수로) */
  skipTask(time: number, hits?: number): boolean {
    if (this.state === 'done') return false;
    if (hits !== undefined) this.results[this.index].hits = hits;
    this.arrows.clear();
    this.pending = [];
    this.endTask(time);
    return true;
  }

  /** 디버그·건너뛰기: 전부 끝 (hitsEach 를 주면 과제마다 그 수) */
  forceEnd(hitsEach?: number): void {
    if (this.state === 'done') return;
    for (const r of this.results) {
      if (hitsEach !== undefined) r.hits = hitsEach;
      r.done = true;
    }
    this.finish();
  }

  update(time: number, delta: number, input: TrialInput): void {
    if (this.state === 'done') return;
    const dt = Math.min(delta, 50) / 1000;
    if (this.state === 'card' && time >= this.phaseEnd) this.beginRun(time);
    else if (this.state === 'clear' && time >= this.phaseEnd) this.next(time);
    this.player.update(time, dt, input, this.ground, true);
    if (this.state === 'run') this.updateRun(time);
    const P = this.player;
    const hit = this.arrows.update(time, dt, { x: P.pos.x, y: P.pos.y, vulnerable: P.vulnerable(time) });
    if (hit) {
      P.hit(time, hit.dx, hit.dy);
      this.results[this.index].hits += 1;
      this.onChange();
    }
    this.drawAim(time);
    this.updateShooters(time);
    this.fx.update(time);
    P.sync(time, true);
    this.lightTarget.x = P.pos.x;
    this.lightTarget.y = P.pos.y;
    this.lighting.update(time);
  }

  destroy(): void {
    this.lighting.destroy();
    this.arrows.destroy();
    this.player.destroy();
    this.aimLine.destroy();
    for (const s of this.shooters) s.sprite.destroy();
    this.shooters.length = 0;
    for (const v of this.props) v.destroy();
  }

  /** 보이는 사수 몸 (발 기준 사각형) 안인가 */
  private shooterAt(x: number, y: number): boolean {
    const [w, h] = RITUAL_TRIAL_FEEL.SHOOTER_BODY;
    return this.shooters.some(
      (s) => s.sprite.visible && Math.abs(x - s.x) <= w / 2 && y <= s.y + h / 2 && y >= s.y - h / 2,
    );
  }

  private makeShooter(p: { x: number; y: number }): Shooter {
    const F = RITUAL_TRIAL_FEEL;
    const sprite = this.scene.physics.add.sprite(p.x, p.y, '__DEFAULT');
    sprite.body!.setImmovable(true);
    const visual = new EntityVisual(
      sprite as unknown as ConstructorParameters<typeof EntityVisual>[0],
      F.SHOOTER_SHEET,
      F.SHOOTER_BODY[0],
      F.SHOOTER_BODY[1],
      F.SHOOTER_PLACEHOLDER,
    );
    sprite.setVisible(false);
    return { sprite, visual, x: p.x, y: p.y };
  }

  private beginCard(i: number, time: number): void {
    this.index = i;
    this.state = 'card';
    this.phaseEnd = time + (i === 0 ? this.data.firstCardMs : this.data.cardMs);
    this.fired = 0;
    this.pending = [];
    const n = this.task.shooters;
    this.shooters.forEach((s, k) => {
      s.sprite.setVisible(k < n);
      s.visual.setHidden(k >= n);
    });
    this.onChange();
  }

  private beginRun(time: number): void {
    this.state = 'run';
    this.nextVolleyAt = time;
    this.onChange();
  }

  /** 사격 박자: 간격마다 겨눔 시작 → telegraphMs 뒤 쏜다. 다 쏘고 화살이 사라지면 과제 끝 */
  private updateRun(time: number): void {
    const t = this.task;
    if (this.fired < t.volleys && time >= this.nextVolleyAt) {
      const k = shooterFor(this.fired, t.shooters);
      const s = this.shooters[k];
      const P = this.player.pos;
      const aim = Math.atan2(P.y - this.muzzleY(s), P.x - s.x);
      this.pending.push({ shooter: k, aim, fireAt: time + this.data.telegraphMs });
      s.visual.oneShot('attack', facing8Of(Math.cos(aim), Math.sin(aim), 'down'), time, this.data.telegraphMs + 120);
      this.fired += 1;
      this.nextVolleyAt = time + t.intervalMs;
    }
    const due = this.pending.filter((v) => time >= v.fireAt);
    if (due.length > 0) {
      this.pending = this.pending.filter((v) => time < v.fireAt);
      for (const v of due) this.shoot(v);
    }
    if (this.fired >= t.volleys && this.pending.length === 0 && !this.arrows.anyAlive) this.endTask(time);
  }

  private shoot(v: Volley): void {
    const t = this.task;
    const s = this.shooters[v.shooter];
    const speed = this.data.shotSpeedTiles * TILE;
    const angles = t.pattern === 'fan' ? fanAngles(v.aim, t.fanCount ?? 1, t.fanDeg ?? 0) : [v.aim];
    for (const a of angles) this.arrows.fire(s.x, this.muzzleY(s), a, speed, this.data.bulletLifeMs);
    audio.playSfx(SFX.enemyShot(RITUAL_TRIAL_FEEL.SHOOTER_SHEET));
  }

  private muzzleY(s: Shooter): number {
    return s.y - RITUAL_TRIAL_FEEL.MUZZLE_UP_PX;
  }

  private endTask(time: number): void {
    this.results[this.index].done = true;
    this.state = 'clear';
    this.phaseEnd = time + this.data.clearMs;
    this.onChange();
  }

  private next(time: number): void {
    if (this.index + 1 < this.data.tasks.length) this.beginCard(this.index + 1, time);
    else this.finish();
  }

  private finish(): void {
    this.state = 'done';
    this.arrows.clear();
    this.pending = [];
    this.aimLine.clear();
    this.onChange();
    this.onDone(this.results.reduce((n, r) => n + r.hits, 0));
  }

  /** 겨눔 선: 쏘기 전까지 사수에서 겨눈 쪽으로 (끝으로 갈수록 옅게, 쏠 때가 가까울수록 진하게) */
  private drawAim(time: number): void {
    const g = this.aimLine;
    g.clear();
    const F = RITUAL_TRIAL_FEEL;
    const t = this.task;
    const len = F.AIM_TILES * TILE;
    for (const v of this.pending) {
      const s = this.shooters[v.shooter];
      const k = 1 - Math.max(0, Math.min(1, (v.fireAt - time) / this.data.telegraphMs));
      const angles = t.pattern === 'fan' ? fanAngles(v.aim, t.fanCount ?? 1, t.fanDeg ?? 0) : [v.aim];
      for (const a of angles) {
        const x0 = s.x;
        const y0 = this.muzzleY(s);
        const steps = 4;
        for (let i = 0; i < steps; i++) {
          const f0 = i / steps;
          const f1 = (i + 1) / steps;
          g.lineStyle(F.AIM_LINE_PX, F.AIM_COLOR, F.AIM_ALPHA * (0.35 + 0.65 * k) * (1 - f0 * 0.8));
          g.lineBetween(
            x0 + Math.cos(a) * len * f0,
            y0 + Math.sin(a) * len * f0,
            x0 + Math.cos(a) * len * f1,
            y0 + Math.sin(a) * len * f1,
          );
        }
      }
    }
  }

  /** 사수는 주인공 쪽을 본다 */
  private updateShooters(time: number): void {
    const P = this.player.pos;
    for (const s of this.shooters) {
      if (!s.sprite.visible) continue;
      s.visual.loop('idle', facingOf(P.x - s.x, P.y - s.y, 'down'), time);
      s.visual.sync();
    }
  }
}
