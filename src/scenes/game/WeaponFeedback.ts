/**
 * 56라운드 무기 피드백 연출 (씬 쪽, EventBus 구독): Q7·Q8 월드 문구(PERFECT GUARD · PARRY) + `guard_perfect_fx`(행 guard·parry,
 * 공격자 방향) · 대검 울분 가득 번쩍임 · 활 숨 집중(감속 정밀 조준 — 물리 배속) · 단검 과열 100% → 낙인 일괄 폭발·식는 동안 루프 ·
 * 그로기 머리 위 소용돌이. 판정·자원 규칙은 Player 쪽.
 */
import { DEPTH, FEEDBACK, FEEL } from '../../core/Constants';
import type {
  PerfectGuardPayload,
  PlayerParriedPayload,
  WeaponGaugePayload,
  WeaponResourcePayload,
} from '../../core/EventBus';
import type { FxHandle } from '../../systems/fx/fx';
import { artScale } from '../../systems/sprites/spriteDefs';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { HIT_ORIGIN_UP_PX } from './shared';
import { gameState } from '../../core/GameState';
import { WorldCallouts } from '../../systems/fx/worldCallouts';
import type { Game } from '../Game';

/** 문구 (결정 Q8: 영문) */
const TEXT = { PERFECT_GUARD: 'PERFECT GUARD', PARRY: 'PARRY' } as const;

export class WeaponFeedback {
  readonly callouts: WorldCallouts;
  /** 디버그: 숨 집중 물리 배속 적용 중 */
  focusScale = 1;
  /** 과열 식는 동안 루프 · 그로기 소용돌이 */
  private coolFx: FxHandle | null = null;
  private swirlFx: FxHandle | null = null;
  /** 디버그: 마지막 가드 fx */
  lastGuardFx: { kind: string; ok: boolean } | null = null;

  constructor(private readonly g: Game) {
    this.callouts = new WorldCallouts(g);
  }

  /** 몸 위 문구 */
  private callout(text: string): void {
    const p = this.g.player;
    this.callouts.show(p.x, p.body.top, text);
  }

  onPerfectGuard(p: PerfectGuardPayload): void {
    const g = this.g;
    this.callout(TEXT.PERFECT_GUARD);
    this.guardFx('guard', p.dirX, p.dirY);
    g.hitStop.request(g.time.now, FEEL.SECONDARY.PARRY_HITSTOP_MS);
  }

  onParried(p: PlayerParriedPayload): void {
    this.callout(TEXT.PARRY);
    this.guardFx('parry', p?.dirX, p?.dirY);
  }

  /** 맞닿은 점(판정 원점에서 공격자 쪽) · 공격자 방향 회전 · 행 guard/parry. 방향이 없으면 바라보는 방향 */
  private guardFx(kind: 'guard' | 'parry', dirX?: number, dirY?: number): void {
    const g = this.g;
    const G = FEEDBACK.GUARD_FX;
    const pl = g.player;
    let dx = dirX ?? 0;
    let dy = dirY ?? 0;
    if (dx === 0 && dy === 0) {
      dx = Math.cos(pl.aimAngle);
      dy = Math.sin(pl.aimAngle);
    }
    const x = pl.x + dx * G.CONTACT_PX;
    const y = pl.y - HIT_ORIGIN_UP_PX + dy * G.CONTACT_PX;
    const ok = g.fx.has(G.SHEET)
      ? g.fx.play(G.SHEET, x, y, {
          dir: kind,
          angle: Math.atan2(dy, dx),
          flipY: dx < 0,
          depth: DEPTH.HIT_FX,
          hitstopFrame: g.fx.sheet(G.SHEET)?.holdFrame,
        }) !== null
      : false;
    this.lastGuardFx = { kind, ok };
  }

  onGauge(p: WeaponGaugePayload): void {
    const g = this.g;
    if (p.gauge === 'grudge' && p.event === 'full') g.player.flashColor(FEEDBACK.GRUDGE_FULL_TINT);
    if (p.gauge === 'breath' && p.event === 'focusStart') this.setFocus(true);
    if (p.gauge === 'breath' && p.event === 'focusEnd') this.setFocus(false);
  }

  onResource(p: WeaponResourcePayload): void {
    const g = this.g;
    if (p.weapon !== gameState.weapon.id) return;
    const O = FEEDBACK.OVERHEAT;
    if (p.event === 'overheat') {
      g.strikes.brands.onOverheat();
      if (gameState.weapon.def.gauge?.kind === 'brand' && g.fx.has(O.COOL_SHEET)) {
        g.fx.stop(this.coolFx, 0, false);
        this.coolFx = g.fx.play(O.COOL_SHEET, g.player.x, g.player.y, {
          follow: g.player,
          depthOffset: DEPTH.OVERLAY_STEP * 3,
        });
      }
    }
    if (p.event === 'cooled') {
      g.fx.stop(this.coolFx, 0, false);
      this.coolFx = null;
    }
    if (p.event === 'groggy') this.startSwirl();
    if (p.event === 'recovered') {
      g.fx.stop(this.swirlFx, 0, false);
      this.swirlFx = null;
    }
  }

  /** 그로기 머리 위 소용돌이 (몸 JSON headTopAnchors 첫 열 + swirlOffsetY — 없으면 고정 오프셋) */
  private startSwirl(): void {
    const g = this.g;
    const G = FEEDBACK.GROGGY;
    if (!g.fx.has(G.SWIRL_SHEET)) return;
    const body = spriteLibrary.sheet('player', 'groggy') as
      | (ReturnType<typeof spriteLibrary.sheet> & {
          headTopAnchors?: Record<string, [number, number][]>;
          swirlOffsetY?: number;
        })
      | undefined;
    const head = body?.headTopAnchors?.down?.[0];
    const k = body ? artScale(body) : 0;
    const off =
      body && head
        ? { x: (head[0] - body.pivot.x) * k, y: (head[1] + (body.swirlOffsetY ?? 0) - body.pivot.y) * k }
        : { x: 0, y: G.SWIRL_FALLBACK_Y };
    g.fx.stop(this.swirlFx, 0, false);
    this.swirlFx = g.fx.play(G.SWIRL_SHEET, g.player.x, g.player.y, {
      follow: g.player,
      followOffset: off,
      depthOffset: DEPTH.OVERLAY_STEP * 3,
    });
  }

  /**
   * 숨 집중: 물리 배속을 낮춘다 (Arcade timeScale > 1 = 느림) — 적 이동·탄이 느려진다. 끝나면 1.
   * 56라운드 Q57: 주인공은 제 속도 (Player.timeComp 로 속도를 되돌려 곱한다 — 조준·놓기는 원래 씬 시계라 그대로)
   */
  private setFocus(on: boolean): void {
    const gd = gameState.weapon.def.gauge;
    const scale = on && gd?.kind === 'breath' ? gd.focusTimeScale : 1;
    this.focusScale = scale;
    const world = this.g.physics.world;
    const ts = scale > 0 ? 1 / scale : 1;
    if (world) world.timeScale = ts;
    if (this.g.player) this.g.player.timeComp = ts;
    if (on) this.g.screenFx.flash(FEEDBACK.FOCUS_FLASH.COLOR, FEEDBACK.FOCUS_FLASH.MS, FEEDBACK.FOCUS_FLASH.ALPHA);
  }

  destroy(): void {
    if (this.focusScale !== 1) this.setFocus(false);
    this.callouts.destroy();
  }
}
