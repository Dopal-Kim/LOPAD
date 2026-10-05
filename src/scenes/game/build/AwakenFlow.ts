/**
 * 61라운드 단계 4 P12 각성 연출·외형 (계약 art §26 · UI §18 · sound §10 — 60라운드 최종 각성 연출을 1차·2차로 대체):
 * - 1차 각성: 게임 0.8초 정지 + `fx/v4/awaken1_crack`(무기가 금 가며 깨어남) → 1차 모양 오버레이 `<갈래>_a1_*`.
 *   2차 각성: 1.0초 정지 + `fx/v4/awaken2_bloom` → 덧붙임 `<갈래>_a2_*` + 길 강조색(pathTint)·휘두름 궤적 길 색.
 *   새 시트가 없으면 옛 각성 순간 fx `<무기>_awaken_in` · 옛 `_awaken` 오버레이로 폴백 (셋째 갈래는 옛 모양이 곧 1차 모양).
 * - 그림은 고른 갈래·길만 지연 로드 (`sheetLoader.loadGrowthSheets` — 갈래 수단 그림 + 각성 외형). 메뉴가 열릴 때 연출 fx 를 미리 받는다.
 * - 셋째 갈래 런: 기본 fx 를 옛 각성 궤적 `<fx>_awaken` 으로 1:1 교체 (FxPool 교체 표 — 갈래 replaceFx 가 우선).
 */
import { gameState } from '../../../core/GameState';
import { GROWTH } from '../../../data/growth';
import { growthLookOf } from '../../../systems/growth/growth';
import {
  loadGrowthSheets,
  queueRequests,
  sheetListed,
  type WeaponLoadScope,
} from '../../../systems/sprites/sheetLoader';
import { FX_ACTION } from '../../../systems/sprites/spriteActions';
import {
  awakenFxAliases,
  awakenInFxId,
  growthFxId,
  growthOverlayAction,
  weaponOverlayActions,
} from '../../../systems/sprites/sheetSets';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { fxDrawScale } from '../../../systems/sprites/spriteDefs';
import { PLAYER_RENDER_SCALE } from '../../../systems/weapon/playerScale';
import { DEPTH } from '../../../core/Constants';
import type { Game } from '../../Game';
import type { BuildRuntime } from './BuildRuntime';

export class AwakenFlow {
  /** 디버그: 마지막 각성 연출 (단계 · 연출 fx id · 폴백 여부 · 정지 ms) */
  last: { stage: 1 | 2; fx: string | null; fallback: boolean; pauseMs: number; t: number } | null = null;
  /** 각성 정지 중 (GrowthFlow 가 다음 메뉴를 미룬다) */
  playing = false;

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {}

  /** 지금 무기의 로드 범위 (경로 노드 · 각성 외형) */
  scope(): WeaponLoadScope {
    const w = gameState.weapon;
    const look = growthLookOf(w);
    return {
      lab: this.g.lab,
      path: [...w.path],
      growth: look ? { branch: look.branch, stage: look.stage, legacy: look.legacy } : null,
    };
  }

  /** 씬 시작: 외형·궤적 색 맞추기 (preload 에서 못 읽은 것은 지금) */
  onSceneStart(): void {
    this.sync(false);
  }

  /** 외형 오버레이·궤적 색을 지금 경로에 맞춘다 (시험장 갈래 바꾸기 · 복원). load 면 그림도 지연 로드 */
  sync(load = true): void {
    const g = this.g;
    const w = gameState.weapon;
    const look = growthLookOf(w);
    g.player?.overlay.setGrowth(look);
    this.syncTrail();
    if (load || look) loadGrowthSheets(g, w.id, this.scope(), () => this.syncTrail());
  }

  /** 2차 휘두름 궤적 길 색 (a2 시트 JSON trailTint[길] — 아직 없으면 데이터 폴백) */
  private syncTrail(): void {
    const g = this.g;
    if (!g.scene.isActive()) return;
    const w = gameState.weapon;
    const look = growthLookOf(w);
    let tint = look?.stage === 2 ? look.tint : null;
    if (look?.stage === 2 && look.path) {
      const def = weaponOverlayActions(w.id, [...w.path])
        .map((a) => spriteLibrary.sheet(w.id, growthOverlayAction(look.branch, 2, a)))
        .find((d) => d) as { trailTint?: Record<string, number[]> } | undefined;
      const c = def?.trailTint?.[look.path];
      if (c && c.length >= 3) tint = (c[0] << 16) | (c[1] << 8) | c[2];
    }
    g.fx.setTrailTint(tint !== null ? `${w.id}_` : null, tint);
  }

  /** 각성 메뉴가 열림 — 연출 fx(+ 옛 각성 순간 fx 폴백)를 미리 받아 둔다 */
  prefetch(stage: 1 | 2): void {
    const g = this.g;
    const ids = [growthFxId(stage), awakenInFxId(gameState.weapon.id)];
    const reqs = ids
      .map((name) => ({ category: 'fx' as const, name, action: FX_ACTION }))
      .filter((r) => sheetListed(r) && !g.fx.has(r.name));
    if (reqs.length === 0) return;
    if (queueRequests(g, reqs, () => {}) && !g.load.isLoading()) g.load.start();
  }

  /**
   * 각성 순간 (메뉴가 닫히고 경로가 바뀐 뒤): 게임 정지 → 연출 fx → 정지 끝에 새 외형을 드러낸다. 정지 길이 ms
   */
  begin(stage: 1 | 2): number {
    const g = this.g;
    const w = gameState.weapon;
    const pauseMs = GROWTH.awaken.pauseMs[stage === 1 ? '1' : '2'];
    const look = growthLookOf(w);
    g.player.overlay.setGrowth(look);
    g.player.overlay.holdGrowth(true);
    loadGrowthSheets(g, w.id, this.scope());
    this.playing = true;
    g.setFrozen(true);
    g.player.body?.setVelocity(0, 0);
    const want = growthFxId(stage);
    const fallbackId = awakenInFxId(w.id);
    let fx: string | null = null;
    let swapMs = pauseMs;
    if (this.playAwakenFx(want, stage === 2 ? (look?.tint ?? null) : null)) {
      fx = want;
      swapMs = this.swapAtMs(want, pauseMs);
    } else if (this.rt.art.onPlayer(fallbackId)) fx = fallbackId;
    g.screenFx.evolve();
    this.last = { stage, fx, fallback: fx !== want, pauseMs, t: Math.round(g.time.now) };
    // art §26: 연출 fx 의 swapFrame 시작에 새 외형을 켠다 (fx 가 없으면 정지 끝에)
    g.time.delayedCall(swapMs, () => g.scene.isActive() && g.player.overlay.holdGrowth(false));
    g.time.delayedCall(pauseMs, () => this.reveal());
    return pauseMs;
  }

  /** 연출 fx (art §26: 앵커 주인공 발 + offsetDots, 주인공을 따라감, 2차는 길 색 tint) — 없으면 false */
  private playAwakenFx(id: string, tint: number | null): boolean {
    const g = this.g;
    const pl = g.player;
    const def = g.fx.sheet(id) as (ReturnType<typeof g.fx.sheet> & { offsetDots?: { x: number; y: number } }) | null;
    if (!def || !g.fx.has(id) || !pl) return false;
    const k = fxDrawScale(def) * PLAYER_RENDER_SCALE;
    const off = def.offsetDots ?? { x: 0, y: 0 };
    return (
      g.fx.play(id, pl.x, pl.y, {
        follow: pl,
        followOffset: { x: off.x * k, y: off.y * k },
        depthOffset: DEPTH.OVERLAY_STEP * 3,
        scaleMult: PLAYER_RENDER_SCALE,
        ...(tint !== null ? { tint } : {}),
      }) !== null
    );
  }

  /** 연출 fx 의 swapFrame 시작 ms (메타 없으면 정지 끝) */
  private swapAtMs(id: string, fallback: number): number {
    const def = this.g.fx.sheet(id) as { swapFrame?: number; frameDurationsMs?: number[] } | null;
    const f = def?.swapFrame;
    const d = def?.frameDurationsMs;
    if (typeof f !== 'number' || !d) return fallback;
    return d.slice(0, f).reduce((a, b) => a + b, 0);
  }

  private reveal(): void {
    const g = this.g;
    this.playing = false;
    if (!g.scene.isActive()) return;
    g.player.overlay.holdGrowth(false);
    this.sync(false);
    this.syncTrail();
    if (!g.menu.isOpen) g.setFrozen(false);
  }

  /** 셋째 갈래 런의 fx 교체 표 (옛 각성 궤적) — 아니면 빈 표 */
  aliases(): Record<string, string> {
    const look = growthLookOf(gameState.weapon);
    return look?.legacy ? awakenFxAliases(gameState.weapon.id) : {};
  }
}
