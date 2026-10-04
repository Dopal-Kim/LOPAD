/**
 * 58라운드 Q3 대검 차지 균열 (씬 쪽 — 56라운드 꽂아내리기 대체): 휘둘러 내리찍은 판정 순간, 내리찍은 자리(몸 시트 앵커 — 없으면
 * 쐐기 끝점 충격원 중심)에서 조준 방향으로 균열이 커서까지 이어진다. 길이 = min(최대(차지 단계 칸 수 × 울분), 커서까지, 벽까지).
 * 앞머리가 지나간 칸만 판정(적마다 1회). 그림 = fx `greatsword_charge_crack_line`(그림 표 `crack_line` fx — 회전 시트면 길이에 맞춰
 * 배율), 없으면 앞머리가 지나간 칸마다 땅 균열(crackFx 행 s)을 작게. 시각은 플레이 시계(히트스톱 동안 멈춤).
 * 앞머리 시간표·판정은 `systems/weapon/plungeWave`(충격파와 같은 앞머리 규칙).
 */
import { COLORS, DEPTH } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { ComboCrackLineDef } from '../../data/types';
import type { Mob } from '../../objects/Mob';
import { artCandidates, pickArt } from '../../systems/weapon/comboArt';
import type { Pt } from '../../systems/weapon/hitShapes';
import { predictTravel } from '../../systems/weapon/issenPath';
import {
  crackTiles,
  waveEndMs,
  waveFrontRatio,
  waveHit,
  waveTimeline,
  type WaveTimeline,
} from '../../systems/weapon/plungeWave';
import { artScale, rowDirFor } from '../../systems/sprites/spriteDefs';
import type { Game } from '../Game';
import type { MobStrike } from './IssenStrikes';
import { HIT_ORIGIN_UP_PX } from './shared';

/** 벽 확인 간격 (월드 px) */
const WALL_STEP_PX = 2;
/** 찍은 자리 (월드): 몸 시트 slamAnchors 오프셋(발 피벗 기준) — 없으면 쐐기 끝점 충격원 중심 */
export function crackOrigin(p: PlayerAttackPayload, player: Pt, impact: Pt | null): Pt | null {
  const o = p.crackLine?.startOffset;
  return o ? { x: player.x + o.x, y: player.y + o.y } : impact;
}

/** 대체 그림 칸 균열 기본 행 (그림 표 crackRow 가 없을 때) */
const TILE_CRACK_ROW = 's';
/** 플레이스홀더 윤곽 유지 ms */
const PLACEHOLDER_MS = 260;

interface CrackRun {
  p: PlayerAttackPayload;
  def: ComboCrackLineDef;
  origin: Pt;
  dir: Pt;
  lengthPx: number;
  halfWidthPx: number;
  timeline: WaveTimeline;
  bornAt: number;
  hit: Set<Mob>;
  /** 대체 그림: 이미 균열을 놓은 칸 수 */
  tilesShown: number;
  /** 대체 그림 fx id (그림 선 시트가 있으면 null) · 행 (그림 표 crackRow) */
  tileFx: string | null;
  tileRow: string;
}

export class CrackLineStrikes {
  debugLast: Record<string, unknown> | null = null;
  private run: CrackRun | null = null;

  constructor(
    private readonly g: Game,
    private readonly strike: MobStrike,
  ) {}

  /** 그림 표 키의 로드된 첫 fx (`<무기>_<이름>`) */
  private fxOf(art: string, cat: 'fx' | 'crackFx'): string | null {
    const w = gameState.weapon;
    const name = pickArt(artCandidates(w.def.combo, art, cat), (n) => this.g.fx.has(`${w.id}_${n}`));
    return name ? `${w.id}_${name}` : null;
  }

  /** 판정 순간 (PlayerStrikes — 본 타 판정 직후). impact = 쐐기 끝점 충격원 중심 (찍은 자리 앵커가 없을 때) */
  start(p: PlayerAttackPayload, impact: Pt | null): void {
    const g = this.g;
    const cl = p.crackLine;
    const def = gameState.weapon.def.combo?.charge?.crackLine;
    if (!cl || !def) return;
    const origin = crackOrigin(p, g.player, impact);
    if (!origin) return;
    const len = Math.hypot(p.dirX, p.dirY) || 1;
    const dir = { x: p.dirX / len, y: p.dirY / len };
    const cursorAlong = (cl.cursorX - origin.x) * dir.x + (cl.cursorY - origin.y) * dir.y;
    // 벽에서 멈춤 (찍은 자리 = 바닥, 쐐기 끝점이면 판정 원점 높이만큼 아래가 바닥)
    const wall = predictTravel(
      origin.x,
      origin.y + (cl.startOffset ? 0 : HIT_ORIGIN_UP_PX),
      dir,
      cl.maxTiles * def.tilePx,
      (x, y) => g.world.isWalkableAt(x, y),
      WALL_STEP_PX,
    );
    const tiles = crackTiles(cl.maxTiles, cursorAlong, wall, def.tilePx);
    const lengthPx = tiles * def.tilePx;
    this.debugLast = {
      time: g.time.now,
      stage: cl.stage,
      origin,
      dir,
      maxTiles: cl.maxTiles,
      cursorPx: Math.round(cursorAlong * 10) / 10,
      wallPx: wall,
      tiles,
      lengthPx,
      fx: null,
      hits: 0,
    };
    if (tiles <= 0) {
      this.run = null;
      return;
    }
    // 57라운드 갈래 (시스템 B BranchStrikes): 중압 = 균열 대신 원형 진동 · 파쇄 = 같은 tN 그림 교체
    const branch = g.build.branch.onCrackLine(p, origin, dir, tiles, lengthPx);
    if (branch.skip) {
      this.run = null;
      return;
    }
    // 그림: 그림 표 fx[칸 수 − 1] (t1~t5 — 로드된 것만)
    const names = artCandidates(gameState.weapon.def.combo, def.art, 'fx');
    const pick = names[Math.min(tiles, names.length) - 1];
    const lineFx =
      branch.sheet ?? (pick && g.fx.has(`${gameState.weapon.id}_${pick}`) ? `${gameState.weapon.id}_${pick}` : null);
    const sheet = lineFx ? g.fx.sheet(lineFx) : undefined;
    const fallbackMs = tiles * def.msPerTile;
    const timeline = sheet ? waveTimeline(sheet, fallbackMs) : { times: [0, fallbackMs], ratios: [0, 1] };
    if (lineFx && sheet) this.playLine(lineFx, origin, dir, lengthPx);
    this.run = {
      p: { ...p, damageMult: p.damageMult * cl.damageMult },
      def,
      origin,
      dir,
      lengthPx,
      halfWidthPx: cl.halfWidthPx,
      timeline,
      bornAt: g.playNow(),
      hit: new Set(),
      tilesShown: 0,
      tileFx: lineFx ? null : this.fxOf(def.art, 'crackFx'),
      tileRow: gameState.weapon.def.combo?.art?.[def.art]?.crackRow ?? TILE_CRACK_ROW,
    };
    if (!lineFx && !this.run.tileFx) this.placeholder(origin, dir, lengthPx, cl.halfWidthPx);
    this.debugLast.fx = lineFx ?? this.run.tileFx;
  }

  /** 균열 선 시트: 회전 시트(`rotate`·`drawnFacing`)는 조준 각도로 돌리고 길이에 맞춰 배율, 방향 행 시트는 행만 */
  private playLine(id: string, origin: Pt, dir: Pt, lengthPx: number): void {
    const g = this.g;
    const def = g.fx.sheet(id);
    if (!def) return;
    const memo = def as { rotate?: boolean; drawnFacing?: string; hitShape?: { lengthPx?: number } };
    const rotates = memo.rotate === true || typeof memo.drawnFacing === 'string';
    if (rotates) {
      const drawn =
        (typeof memo.hitShape?.lengthPx === 'number' ? memo.hitShape.lengthPx : def.frameWidth) * artScale(def);
      const sh = (def as { shakeHint?: { px?: number; ms?: number } }).shakeHint;
      if (sh?.px && sh.ms) g.shake.add(g.time.now, sh.px, sh.ms);
      g.fx.play(id, origin.x, origin.y, {
        angle: Math.atan2(dir.y, dir.x),
        flipY: dir.x < 0,
        depth: DEPTH.FX_GROUND,
        scaleMult: drawn > 0 ? lengthPx / drawn : 1,
      });
      return;
    }
    g.fx.play(id, origin.x, origin.y, {
      dir: rowDirFor(def, dir.x, dir.y, g.player.facingDir),
      depth: DEPTH.FX_GROUND,
    });
  }

  /** 그림이 하나도 없을 때: 균열 사각형 윤곽 */
  private placeholder(origin: Pt, dir: Pt, length: number, half: number): void {
    const g = this.g;
    const gfx = g.add.graphics().setDepth(DEPTH.ATTACK);
    gfx.lineStyle(2, COLORS.SHOCKWAVE, 0.9);
    gfx.setPosition(origin.x, origin.y).setRotation(Math.atan2(dir.y, dir.x));
    gfx.strokeRect(0, -half, length, half * 2);
    g.tweens.add({ targets: gfx, alpha: 0, duration: PLACEHOLDER_MS, onComplete: () => gfx.destroy() });
  }

  /** 매 프레임: 앞머리가 지나간 칸의 적 (적마다 1회) · 대체 그림 칸 균열 */
  update(): void {
    const r = this.run;
    if (!r) return;
    const g = this.g;
    const e = g.playNow() - r.bornAt;
    const front = r.lengthPx * waveFrontRatio(r.timeline, e);
    if (r.tileFx) {
      const tile = r.def.tilePx;
      const passed = Math.min(Math.ceil(r.lengthPx / tile), Math.floor(front / tile + 0.5));
      for (; r.tilesShown < passed; r.tilesShown += 1) {
        const d = Math.min(r.lengthPx, (r.tilesShown + 0.5) * tile);
        g.fx.play(r.tileFx, r.origin.x + r.dir.x * d, r.origin.y + r.dir.y * d, {
          dir: r.tileRow,
          depth: DEPTH.FX_GROUND,
          scaleMult: r.def.tileCrackScale,
        });
      }
    }
    for (const child of [...g.mobs.getChildren()]) {
      const mob = child as Mob;
      if (!mob.active || r.hit.has(mob)) continue;
      const b = mob.body;
      if (
        !waveHit(r.origin, r.dir, front, r.halfWidthPx, {
          x: b.center.x,
          y: b.center.y,
          r: Math.min(b.halfWidth, b.halfHeight),
        })
      )
        continue;
      r.hit.add(mob);
      this.strike(mob, r.p, false);
    }
    if (this.debugLast) this.debugLast.hits = r.hit.size;
    if (e >= waveEndMs(r.timeline)) this.run = null;
  }
}
