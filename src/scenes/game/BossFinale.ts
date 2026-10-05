/**
 * 61라운드 E 보스 결정타·쓰러짐·방 불 끄기 (아트 2 fx — 3국면 진입 때 지연 로드, `systems/boss/bossVram`). BossFlow 가 부른다.
 * - 결정타(BOSS_BREAK finisher — 파훼 창 안 처치): 일섬(boss1_finisher_slash, 각도 = 주인공 → 보스)과 충격(boss1_finisher_burst)을
 *   같은 점(보스 피벗 위 FINISHER_LIFT_DOTS)에 동시에 + 섬광·흔들림·확대 (아트 systemHints → BOSS_ART.FINISHER; 설정 섬광 끔·흔들림 0 존중).
 * - 쓰러짐 0 프레임(처치 연출 hit): boss1_defeat_shatter 를 보스 피벗에 — 마지막 칸은 보상 메뉴까지 유지 후 그냥 끈다(반투명 없음).
 * - snuffAtMs 부터 방의 켜진 촛대를 보스에서 먼 순서로 SNUFF_GAP_MS 간격으로 끈다 (불꽃 자리 boss1_flame_snuff + 촛대 광원 끔).
 * fx 가 아직 없으면(로드 전) 그 그림만 빠진다.
 */
import Phaser from 'phaser';
import { BOSS_ART, CAMERA, DEPTH } from '../../core/Constants';
import type { Boss } from '../../objects/Boss';
import type { Candle } from '../../systems/boss/candles';
import { feelSettings } from '../../systems/feel';
import type { FxHandle } from '../../systems/fx/fx';
import { worldZoom } from '../../systems/display';
import type { Game } from '../Game';

export class BossFinale {
  /** 보스 피벗 · 일섬 중심 (처치 순간에 잰다 — 결정타 이벤트는 보스가 사라진 뒤 온다) */
  private pivot = { x: 0, y: 0 };
  private center = { x: 0, y: 0 };
  private flipX = false;
  private shatter: FxHandle | null = null;
  private snuffQueue: { atMs: number; candle: Candle; wicks: { x: number; y: number }[] }[] = [];
  /** 불 끄기 시작 시각 (처치 연출 ms) — 그때 켜진 촛대를 고른다 (처치 순간엔 소등이 아직 풀리기 전일 수 있다) */
  private snuffAtMs: number | null = null;
  private zoomTween: Phaser.Tweens.Tween | null = null;
  /** 디버그 */
  readonly log: string[] = [];

  constructor(private readonly g: Game) {}

  /** 처치 순간 (BossFlow hit): 자리 기억 · 쓰러짐 파편 · 불 끄기 예약 */
  onDefeat(boss: Boss | null, snuffAtMs: number | undefined): void {
    const g = this.g;
    if (boss) {
      const def = boss.visual.sheet('idle');
      const lift = def ? BOSS_ART.FINISHER_LIFT_DOTS * boss.scaleY : boss.body.height;
      this.pivot = { x: boss.x, y: boss.y };
      this.center = { x: boss.x, y: boss.y - lift };
      this.flipX = boss.visual.facing === 'left';
    }
    const id = BOSS_ART.SHEETS.DEFEAT_SHATTER;
    if (boss && g.fx.has(id)) {
      // 마지막 칸 유지: holdLastMs 를 넉넉히 주고 보상 때 페이드 없이 끈다
      this.shatter = g.fx.play(id, this.pivot.x, this.pivot.y, {
        flipX: this.flipX,
        holdLastMs: 60_000,
        hooks: false,
      });
      this.log.push('shatter');
    }
    this.snuffQueue = [];
    this.snuffAtMs = snuffAtMs ?? null;
  }

  /** 켜진 촛대를 보스에서 먼 순서로 SNUFF_GAP_MS 간격 예약 */
  private planSnuff(fromMs: number): void {
    const arena = this.g.bossArena;
    if (!arena) return;
    const gaps = BOSS_ART.SNUFF_GAP_MS;
    let at = fromMs;
    this.snuffQueue = arena.snuffTargets(this.pivot).map((t, i) => {
      const e = { atMs: at, candle: t.candle, wicks: t.wicks };
      at += gaps[i % gaps.length];
      return e;
    });
    this.log.push(`snuffPlan:${this.snuffQueue.length}`);
  }

  /** 결정타 (BOSS_BREAK finisher) */
  onFinisher(): void {
    const g = this.g;
    const F = BOSS_ART.FINISHER;
    const S = BOSS_ART.SHEETS;
    const p = g.player;
    const angle = Math.atan2(this.center.y - p.y, this.center.x - p.x);
    let shown = false;
    if (g.fx.has(S.FINISHER_SLASH)) {
      g.fx.play(S.FINISHER_SLASH, this.center.x, this.center.y, {
        angle,
        flipY: Math.abs(angle) > Math.PI / 2,
        depth: DEPTH.HIT_FX,
        hooks: false,
      });
      shown = true;
    }
    if (g.fx.has(S.FINISHER_BURST)) {
      g.fx.play(S.FINISHER_BURST, this.center.x, this.center.y, { depth: DEPTH.HIT_FX + 0.01, hooks: false });
      shown = true;
    }
    const now = g.time.now;
    g.screenFx.flash(F.FLASH, F.FLASH_MS, F.FLASH_ALPHA);
    g.shake.add(now, F.SHAKE_PX, F.SHAKE_MS);
    this.zoomPulse(F.ZOOM, F.ZOOM_MS);
    this.log.push(shown ? 'finisher' : 'finisher:noArt');
  }

  /** 짧은 확대 후 원래 배율 (설정 흔들림 0 이면 생략 — 화면 움직임 묶음) */
  private zoomPulse(to: number, ms: number): void {
    const k = Math.min(1, feelSettings.shake);
    if (k <= 0 || ms <= 0) return;
    const cam = this.g.cameras.main;
    const base = worldZoom(CAMERA.ZOOM);
    this.zoomTween?.stop();
    cam.setZoom(base * (1 + (to - 1) * k));
    this.zoomTween = this.g.tweens.add({
      targets: cam,
      zoom: base,
      duration: ms,
      ease: 'Quad.easeOut',
      onComplete: () => (this.zoomTween = null),
    });
  }

  /** 처치 연출 경과 ms (BossFlow delta 누적) */
  update(elapsed: number): void {
    if (this.snuffAtMs !== null && elapsed >= this.snuffAtMs) {
      this.planSnuff(this.snuffAtMs);
      this.snuffAtMs = null;
    }
    while (this.snuffQueue.length > 0 && this.snuffQueue[0].atMs <= elapsed) {
      const e = this.snuffQueue.shift()!;
      const arena = this.g.bossArena;
      if (!arena) continue;
      // 61 단계 4: 서 있는 촛대는 초 심지마다 (아트 wickAnchors.standing) — 촛대는 unlit_standing 으로
      if (this.g.fx.has(BOSS_ART.SHEETS.FLAME_SNUFF))
        for (const w of e.wicks) this.g.fx.play(BOSS_ART.SHEETS.FLAME_SNUFF, w.x, w.y, { hooks: false });
      arena.snuff(e.candle);
      this.log.push(`snuff:${e.candle.id}`);
    }
  }

  /** 보상 메뉴: 쓰러짐 파편을 끈다 (페이드 없이) */
  onReward(): void {
    if (this.shatter) this.g.fx.stop(this.shatter, 0, false);
    this.shatter = null;
  }

  summary(): Record<string, unknown> {
    return { log: [...this.log], snuffLeft: this.snuffQueue.length, shatter: this.g.fx.isActive(this.shatter) };
  }

  destroy(): void {
    this.zoomTween?.stop();
    this.zoomTween = null;
    this.snuffQueue = [];
    this.shatter = null;
  }
}
