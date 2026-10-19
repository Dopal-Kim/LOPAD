/**
 * 62라운드 전투 감각 연결 (이벤트 → 연출):
 * - P2-13 무피격 보상: 완벽 성공(`PERFECT_SUCCESS` — 패링·퍼펙트 가드·완벽 놓기·완벽 회피) → 화면 가장자리 섬광(ScreenFx.edge).
 * - P1-1 처치 손맛: 전투 방의 마지막 적을 쓰러뜨린 순간(시련 끝 `TRIAL_CLEARED`) 짧은 슬로모 (하데스 마지막 일격).
 * 물리(Arcade timeScale 은 클수록 느림)·씬 트윈만 늦춘다 — 시체 튕김(트윈)·넉백이 같이 느려진다. 실시간 FEEL.KILL.SLOW.MS 뒤 되돌린다.
 * 보스 처치는 BossFlow 의 처치 연출이 따로 한다. 씬 종료 때 되돌리고 구독을 푼다.
 */
import Phaser from 'phaser';
import { FEEL } from '../../core/Constants';
import { EventBus, Events, type FeelSlowmoPayload, type PerfectSuccessPayload } from '../../core/EventBus';
import { feelSettings } from '../../systems/feel';
import type { Game } from '../Game';

export class CombatFeel {
  private saved: { world: number; tweens: number } | null = null;
  private timer: ReturnType<typeof setTimeout> | null = null;
  /** 디버그: 슬로모 횟수 */
  count = 0;

  constructor(private readonly g: Game) {
    EventBus.on(Events.TRIAL_CLEARED, this.onCleared, this);
    EventBus.on(Events.PERFECT_SUCCESS, this.onPerfect, this);
    g.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  /** 디버그: 가장자리 섬광 횟수 */
  perfects = 0;

  private onPerfect(p: PerfectSuccessPayload): void {
    const E = FEEL.SCREEN.EDGE;
    const c = p.kind === 'perfectEvade' ? E.COOL : E.WARM;
    this.g.screenFx.edge(c.COLOR, c.MS, c.ALPHA);
    this.perfects += 1;
  }

  private onCleared(): void {
    // 흔들림·히트스톱을 끈 설정(접근성)이면 슬로모도 끈다
    if (feelSettings.hitstop <= 0 || this.g.bossFlow?.current) return;
    this.slow(FEEL.KILL.SLOW.SCALE, FEEL.KILL.SLOW.MS);
    // 62 D (음향 sound §13 last_kill_slow): 슬로모를 실제로 걸 때만
    EventBus.emit(Events.FEEL_SLOWMO, { kind: 'lastKill' } satisfies FeelSlowmoPayload);
  }

  /** P21 처형 슬로 (dark-brutal §4) — 흔들림·히트스톱을 끈 설정이면 끈다 */
  slowmo(scale: number, ms: number): void {
    if (feelSettings.hitstop > 0) this.slow(scale, ms);
  }

  private slow(scale: number, ms: number): void {
    const g = this.g;
    const world = g.physics.world;
    if (!this.saved) {
      this.saved = { world: world?.timeScale ?? 1, tweens: g.tweens.timeScale };
      if (world) world.timeScale = this.saved.world / scale;
      g.tweens.timeScale = this.saved.tweens * scale;
    }
    this.count += 1;
    if (this.timer) clearTimeout(this.timer);
    // 실시간 (씬 시계는 히트스톱에 멈춘다 — 처치 히트스톱이 끝난 뒤에도 슬로모가 보이도록 히트스톱 남은 시간을 더한다)
    const extra = g.hitStop.remaining(g.time.now);
    this.timer = setTimeout(() => this.restore(), ms + extra);
  }

  private restore(): void {
    this.timer = null;
    const s = this.saved;
    if (!s) return;
    this.saved = null;
    const world = this.g.physics?.world;
    if (world) world.timeScale = s.world;
    if (this.g.tweens) this.g.tweens.timeScale = s.tweens;
  }

  /** 디버그 */
  get active(): boolean {
    return this.saved !== null;
  }

  destroy(): void {
    EventBus.off(Events.TRIAL_CLEARED, this.onCleared, this);
    EventBus.off(Events.PERFECT_SUCCESS, this.onPerfect, this);
    if (this.timer) clearTimeout(this.timer);
    this.restore();
  }
}
