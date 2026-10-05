/**
 * 판정 뒤에 이어지는 지연 판정 스케줄 (55라운드 6-1 — PlayerStrikes 에서 분리).
 * - §17 후속 판정 `followUps[]`: 칼 잔상 베기(150ms 뒤 같은 호 50%) · 대검 차지 3단 충격파 링(끝점). 전용 이펙트는 그 정지 프레임이
 *   후속 판정 시각에 오게 먼저 띄운다. 판정 시각에 `PLAYER_FOLLOW_UP`(시스템 내부 — 음향 katana_echo)
 * - 쌍격·난무 추가 타 (시트 hitFrames 간격, 없으면 TWIN_DELAY_MS)
 * - 지진 충격파 2단 (마무리 타만)
 * 모두 씬 시계(`time.delayedCall`)라 히트스톱 동안 멈춘다. 판정 한 번 자체는 PlayerStrikes.meleeSwing.
 */
import { PROTOTYPE } from '../../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type PlayerFollowUpPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { ComboFollowUpDef } from '../../data/types';
import type { Pt } from '../../systems/weapon/hitShapes';
import type { Game } from '../Game';
import type { SwingFx } from './SwingFx';

/** 판정 한 번의 옵션: 지진 2단 · 55라운드 후속 판정(원점·모양 덮어쓰기) */
export interface SwingOpts {
  secondWave?: boolean;
  follow?: ComboFollowUpDef;
  origin?: Pt;
  /** 후속 판정 전용 이펙트를 이미 띄웠다 (플레이스홀더 없음) */
  followFx?: boolean;
}

/** 판정 한 번 (반환 = 끝점 — 후속 판정 'impact' 원점) */
export type SwingFn = (p: PlayerAttackPayload, opts?: SwingOpts) => { impact: Pt | null };

export class StrikeSchedule {
  constructor(
    private readonly g: Game,
    private readonly swing: SwingFx,
    private readonly swingOnce: SwingFn,
  ) {}

  /** 씬 진행 중(정지·사망 아님)인지 — 지연 실행 콜백 공통 확인 */
  get live(): boolean {
    return this.g.scene.isActive() && !this.g.frozen && !gameState.gameOver;
  }

  /** 본 판정 직후: 후속 판정 · 추가 타 · 지진 2단을 예약한다. at = 본 판정 페이로드, impact = 본 판정 끝점 */
  after(at: PlayerAttackPayload, impact: Pt | null, finisher: boolean): void {
    for (const fu of at.followUps ?? []) this.followUp(at, fu, impact);
    this.extraHits(at);
    if (finisher) this.secondWave(at);
  }

  /** 그 순간 몸 위치에서 다시 판정하는 페이로드 */
  private here(at: PlayerAttackPayload): PlayerAttackPayload {
    return { ...at, x: this.g.player.x, y: this.g.player.y };
  }

  private followUp(at: PlayerAttackPayload, fu: ComboFollowUpDef, impact: Pt | null): void {
    const g = this.g;
    const lead = this.swing.followUpLeadMs(fu.art);
    const origin = fu.at === 'impact' ? (impact ?? undefined) : undefined;
    // 전용 이펙트는 그 판정(정지) 프레임이 후속 판정 시각에 오게 먼저 띄운다 (칼 잔상: 320ms 띄움 → 350ms 판정)
    if (lead !== null)
      g.time.delayedCall(Math.max(0, fu.delayMs - lead), () => {
        if (this.live) this.swing.playFollowUpFx(fu.art, at.dirX, at.dirY, origin);
      });
    g.time.delayedCall(fu.delayMs, () => {
      if (!this.live) return;
      const payload: PlayerFollowUpPayload = {
        weapon: gameState.weapon.id,
        id: fu.id,
        ...(fu.art ? { art: fu.art } : {}),
      };
      EventBus.emit(Events.PLAYER_FOLLOW_UP, payload);
      this.swingOnce(
        {
          ...this.here(at),
          damageMult: at.damageMult * fu.damageMult,
          activeMs: fu.activeMs ?? at.activeMs,
          hitShape: fu.hitShape ?? at.hitShape,
          followUps: undefined,
        },
        { follow: fu, origin, followFx: lead !== null },
      );
    });
  }

  /** 옛 mods.hits 추가 타격: TWIN_DELAY_MS 간격 (60라운드 — 57 Q42 옛 쌍격·난무 진화 시트 시각은 끔) */
  private extraHits(at: PlayerAttackPayload): void {
    const g = this.g;
    const hits = Math.max(1, gameState.weapon.mods.hits ?? 1);
    if (hits <= 1) return;
    for (let i = 1; i < hits; i++) {
      g.time.delayedCall(PROTOTYPE.TWIN_DELAY_MS * i, () => {
        if (this.live) this.swingOnce(this.here(at));
      });
    }
  }

  /** 지진: 충격파 2단 (quake 시트는 1단에서 한 번만 — 3프레임 시작이 2단 판정 시점) */
  private secondWave(at: PlayerAttackPayload): void {
    const mods = gameState.weapon.mods;
    const second = mods.shockwaveSecond;
    if (!mods.shockwave || !second) return;
    this.g.time.delayedCall(second.delayMs, () => {
      if (!this.live) return;
      this.swingOnce(
        {
          ...this.here(at),
          sizeMult: at.sizeMult * second.sizeMult,
          damageMult: at.damageMult * second.damageMult,
        },
        { secondWave: true },
      );
    });
  }
}
