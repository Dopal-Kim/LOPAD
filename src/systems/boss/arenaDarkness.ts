/**
 * 보스방 소등 (61 단계 4 — BossArena 에서 분리, CLAUDE.md 6-1): 3국면 '등불 끄기'(주변광 · 촛대 쓰러뜨리기 · 최소 광원 · 림라이트 ·
 * 예고를 어둠 위로 · 저절로 복구)와 처치 때 '방 불 끄기'(서 있는 촛대 끄기 대상·끄기).
 * BossArena 가 만들고 lightsOut·dark·snuff 를 그대로 넘긴다 (BossArenaApi 는 BossArena 쪽).
 */
import type Phaser from 'phaser';
import { EventBus, Events, type BossActionPayload, type BossScreenPayload } from '../../core/EventBus';
import type { BossArenaParams } from '../../data/types';
import type { Mob } from '../../objects/Mob';
import type { Vec } from '../../objects/boss/types';
import type { Lighting } from '../lighting/Lighting';
import { lightRegistryOf, type LightSource } from '../lighting/lightRegistry';
import { BossRim } from './bossRim';
import type { RimKind } from './bossSheets';
import type { Candle, CandleSet } from './candles';

export interface ArenaDarknessHost {
  scene: Phaser.Scene;
  player: Phaser.GameObjects.Sprite;
  candles: CandleSet;
  lighting(): Lighting | null;
  boss(): Mob | null;
  action(action: BossActionPayload['action'], index?: number): void;
  /** 61라운드 점검 #6: 등불 끄기 동안 예고를 어둠 위로 (TelegraphFx.setAboveDark) */
  telegraphAboveDark?(on: boolean): void;
}

/** 처치 때 끌 촛대 하나: 불꽃 자리(거리 정렬) · 서 있는 초 심지들(끄는 fx 자리) */
export interface SnuffTarget {
  candle: Candle;
  at: Vec;
  wicks: Vec[];
}

export class ArenaDarkness {
  /** 61 E: 소등 동안 보스 림라이트 */
  readonly rim: BossRim;
  private darkUntil = 0;
  /** 61라운드 점검 #6: 어둠 동안 주인공·보스 최소 광원 */
  private darkLights: LightSource[] = [];
  private timers: Phaser.Time.TimerEvent[] = [];

  constructor(
    private readonly host: ArenaDarknessHost,
    private readonly A: Pick<BossArenaParams, 'darkTelegraphLightMult' | 'darkLights'>,
    bossId: string,
    rimKind: () => RimKind | null,
  ) {
    this.rim = new BossRim(host.scene, bossId, rimKind);
  }

  get dark(): boolean {
    return this.darkUntil > 0;
  }

  /** 등불 끄기: 주변광을 어둡게 · 촛대를 차례로 쓰러뜨림 · durationMs 뒤 저절로 복구 */
  lightsOut(p: { fadeMs: number; durationMs: number; darkAmbient: string; toppleGapMs: number }): void {
    if (this.dark) return;
    const H = this.host;
    const now = H.scene.time.now;
    this.darkUntil = now + p.durationMs;
    const L = H.lighting();
    L?.setAmbient(p.darkAmbient, p.fadeMs);
    if (L) L.telegraphGain = this.A.darkTelegraphLightMult;
    H.candles.list.forEach((c, i) => {
      this.timers.push(
        H.scene.time.delayedCall(i * p.toppleGapMs, () => {
          H.candles.set(c, 'fallen');
          H.action('candleTopple', i);
        }),
      );
    });
    this.timers.push(H.scene.time.delayedCall(p.durationMs, () => this.restore(p.fadeMs)));
    this.addDarkLights();
    this.rim.setOn(true);
    H.telegraphAboveDark?.(true);
    EventBus.emit(Events.BOSS_SCREEN, { effect: 'dark', on: true } satisfies BossScreenPayload);
  }

  /** 복구: 주변광 · 촛대를 다시 세운다 (시간이 다 되었거나 보스가 쓰러짐) */
  restore(fadeMs: number): void {
    const H = this.host;
    this.darkUntil = 0;
    this.removeDarkLights();
    this.rim.setOn(false);
    H.telegraphAboveDark?.(false);
    const L = H.lighting();
    L?.setAmbient(null, fadeMs);
    if (L) L.telegraphGain = 1;
    for (const c of H.candles.list) H.candles.set(c, 'lit');
    EventBus.emit(Events.BOSS_SCREEN, { effect: 'dark', on: false } satisfies BossScreenPayload);
  }

  /** 보스가 쓰러짐: 예약(촛대 쓰러뜨리기·복구)을 거두고 어두우면 복구 */
  onBossDied(restoreMs: number): void {
    this.clearTimers();
    if (this.dark) this.restore(restoreMs);
  }

  /** 61라운드 점검 #6: 어둠 속에서도 주인공·보스 실루엣이 읽히게 최소 광원 (data arena.darkLights) */
  private addDarkLights(): void {
    this.removeDarkLights();
    const D = this.A.darkLights;
    if (!D) return;
    const reg = lightRegistryOf(this.host.scene);
    const p = this.host.player;
    if (D.player) this.darkLights.push(reg.add(D.player, { x: p.x, y: p.y, anchor: p }));
    const b = this.host.boss();
    if (D.boss && b) this.darkLights.push(reg.add(D.boss, { x: b.x, y: b.y, anchor: b }));
  }

  private removeDarkLights(): void {
    const reg = lightRegistryOf(this.host.scene);
    for (const l of this.darkLights) reg.remove(l);
    this.darkLights = [];
  }

  private clearTimers(): void {
    for (const t of this.timers) t.remove(false);
    this.timers = [];
  }

  /** 61 E 처치 때 방 불 끄기 대상: 켜진 촛대(서 있음·다시 켬) — 보스에서 먼 순서 */
  snuffTargets(from: Vec): SnuffTarget[] {
    const C = this.host.candles;
    return C.list
      .filter((c) => c.state === 'lit' || c.state === 'relit')
      .map((candle) => ({
        candle,
        at: C.flamePoint(candle),
        // 61 단계 4: 서 있는 촛대는 초 심지마다(wickAnchors.standing), 누운 채 켜진 촛대는 불꽃 자리 하나
        wicks: candle.state === 'lit' ? C.wickPoints(candle) : [C.flamePoint(candle)],
      }))
      .sort((a, b) => Math.hypot(b.at.x - from.x, b.at.y - from.y) - Math.hypot(a.at.x - from.x, a.at.y - from.y));
  }

  /** 촛대 하나 끄기 (광원 없음 · 서 있으면 unlit_standing) */
  snuff(c: Candle): void {
    this.host.candles.set(c, 'out');
    this.host.action('flameSnuff', c.id);
  }

  update(boss: Mob | null): void {
    this.rim.update(boss);
  }

  summary(now: number): Record<string, unknown> {
    return {
      dark: this.dark,
      darkLights: this.darkLights.length,
      darkRemainingMs: this.dark ? Math.max(0, Math.round(this.darkUntil - now)) : 0,
    };
  }

  destroy(): void {
    this.clearTimers();
    if (this.dark) this.host.lighting()?.setAmbient(null, 0);
    this.removeDarkLights();
    this.host.telegraphAboveDark?.(false);
    this.rim.destroy();
  }
}
