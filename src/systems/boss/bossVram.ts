/**
 * 61라운드 E 보스방 VRAM 지연 로드·해제 (목표 런 최고 500MB — 결정 61 P9). Game 이 보스방(arena 가 있는 보스 노드)에서 만든다.
 * - 등장 동작(intro): 보스 묶음으로 올라와 있다 → 전투 시작(BOSS_FIGHT) 뒤 보스가 그 텍스처를 더는 그리지 않으면 내린다.
 * - 국면 전환 들이켜기(phase_drink): 보스 묶음에서 빠져 있다 → 등장 동작을 내린 뒤 올린다 (두 시트가 함께 올라가지 않게).
 * - 결정타·쓰러짐·불 끄기 fx: 마지막 국면(HP 30%)의 소등 시작 때 phase_drink 를 내린 뒤 올린다 — 소등이 없으면 마지막 국면 진입
 *   FINALE_DELAY_MS 뒤, 처치 때 아직 없으면 그때.
 * - 국면 전환 들이켜기(phase_drink): 마지막 국면의 소등이 시작되면 다시 쓰지 않으므로 내린다.
 * - 림라이트: 소등 시작에 지금 VRAM + 추정치가 예산 안이면 올리고(없는 동안은 tintFill 대체), 소등이 끝나면 내린다.
 * 내리기는 '그리는 스프라이트가 없을 때'까지 매 프레임 미룬다 (사용 중인 텍스처를 지우면 그리기가 깨진다).
 */
import type Phaser from 'phaser';
import { BOSS_ART, VRAM } from '../../core/Constants';
import { EventBus, Events, type BossPhasePayload, type BossScreenPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { BOSSES } from '../../data';
import { loadSheetsNow, releaseSheets } from '../sprites/lazySheets';
import { sheetTextureKey, type SheetRequest } from '../sprites/sheetPaths';
import { vramOfTextures } from '../vram';
import { rimFits } from './bossArtRules';
import { bossDeferredRequests, bossFinaleRequests, bossIntroRequests, bossRimRequests } from './bossSheets';

export interface BossVramHost {
  scene: Phaser.Scene;
  /** 지금 보스 텍스처를 그리는 스프라이트들 (보스 몸 · 시체 · 림 · 대체 사본) */
  users(): readonly (Phaser.GameObjects.Sprite | null | undefined)[];
}

type Group = 'intro' | 'phaseDrink' | 'rim';

export class BossVram {
  /** 림 시트가 올라와 있다 (로드 끝) */
  rimReady = false;
  /** 결정타 fx 가 올라와 있다 */
  finaleReady = false;
  /** 디버그: 결정 기록 · 측정 최고 MB */
  readonly log: { e: string; mb?: number; n?: number }[] = [];
  peakMb = 0;
  private readonly pending = new Map<Group, SheetRequest[]>();
  private rimWanted = false;
  /** 소등을 한 번 지났다 (phase_drink 를 다시 올리지 않는다) */
  private darkSeen = false;
  private finaleAsked = false;
  /** 마지막 국면 진입 뒤 결정타 fx 를 올릴 시각 (소등이 먼저 오면 그때) */
  private finaleDueAt = 0;
  private readonly lastPhase: number;
  private readonly subs: [string, (p: never) => void][] = [
    [Events.BOSS_FIGHT, () => this.onFight()],
    [Events.BOSS_PHASE, (p: BossPhasePayload) => this.onPhase(p)],
    [Events.BOSS_SCREEN, (p: BossScreenPayload) => this.onScreen(p)],
    [Events.BOSS_DIED, () => this.loadFinale('died')],
  ];

  constructor(
    private readonly host: BossVramHost,
    private readonly bossId: string,
  ) {
    this.lastPhase = BOSSES[bossId]?.phases.length ?? 0;
    for (const [e, fn] of this.subs) EventBus.on(e, fn, this);
    this.measure('enter');
  }

  /** 디버그·로그: 지금 VRAM 추정 MB (최고값 갱신) */
  measure(tag: string): number {
    const mb = vramOfTextures(this.host.scene.textures).mb;
    this.peakMb = Math.max(this.peakMb, mb);
    this.log.push({ e: tag, mb });
    return mb;
  }

  private onFight(): void {
    this.pending.set('intro', bossIntroRequests([this.bossId]));
    // 마지막 국면에서 바로 시작한 싸움(디버그 ?bossPhase)도 결정타 fx 를 올린다
    if (this.lastPhase > 0 && gameState.bossPhase >= this.lastPhase)
      this.onPhase({ phase: gameState.bossPhase, hp: 0, maxHp: 0 });
  }

  /** 전투 뒤 올리는 몸 동작 (phase_drink) — 이미 마지막 국면 소등을 지났으면 올리지 않는다 */
  private loadDeferred(): void {
    if (this.darkSeen) return;
    loadSheetsNow(this.host.scene, bossDeferredRequests([this.bossId]), () => this.measure('deferredLoaded'));
  }

  private onPhase(p: BossPhasePayload): void {
    if (this.lastPhase > 0 && p.phase >= this.lastPhase && this.finaleDueAt === 0)
      this.finaleDueAt = this.host.scene.time.now + BOSS_ART.FINALE_DELAY_MS;
  }

  private loadFinale(why: string): void {
    if (this.finaleAsked) return;
    this.finaleAsked = true;
    this.log.push({ e: `finale:${why}` });
    loadSheetsNow(this.host.scene, bossFinaleRequests(), () => {
      this.finaleReady = true;
      this.measure('finaleLoaded');
    });
  }

  private onScreen(p: BossScreenPayload): void {
    if (p.effect !== 'dark') return;
    if (p.on) {
      this.darkSeen = true;
      this.pending.set('phaseDrink', [{ category: 'bosses', name: this.bossId, action: 'phase_drink' }]);
      this.rimWanted = true;
      this.pending.delete('rim');
      this.tryRim();
    } else {
      this.rimWanted = false;
      this.rimReady = false;
      this.pending.set('rim', bossRimRequests([this.bossId]));
    }
  }

  /** 소등 시작: phase_drink 를 내린 뒤의 VRAM 으로 림을 올릴지 정한다 (phase_drink 가 아직 그려지는 중이면 다음 프레임에 다시) */
  private tryRim(): void {
    if (!this.rimWanted || this.rimReady) return;
    if (this.pending.has('phaseDrink')) return;
    const finaleMb = this.finaleAsked ? 0 : BOSS_ART.FINALE_EST_MB;
    this.loadFinale('dark');
    const mb = this.measure('dark');
    const budget = VRAM.BUDGET_BYTES / (1024 * 1024);
    if (!rimFits(mb + finaleMb, BOSS_ART.RIM_EST_MB, budget)) {
      this.rimWanted = false;
      this.log.push({ e: 'rim:tintFill', mb });
      return;
    }
    this.rimWanted = false;
    this.log.push({ e: 'rim:load', mb });
    loadSheetsNow(this.host.scene, bossRimRequests([this.bossId]), () => {
      // 로드 사이에 소등이 끝났으면 바로 내린다
      if (this.pending.has('rim')) return;
      this.rimReady = true;
      this.measure('rimLoaded');
    });
  }

  /** 매 프레임: 미뤄 둔 해제 (그리는 스프라이트가 없을 때) */
  update(): void {
    if (this.finaleDueAt > 0 && !this.finaleAsked && this.host.scene.time.now >= this.finaleDueAt)
      this.loadFinale('phaseTimer');
    if (this.pending.size === 0) return;
    const used = new Set<string>();
    for (const s of this.host.users()) if (s?.active && s.texture) used.add(s.texture.key);
    for (const [g, reqs] of [...this.pending]) {
      if (reqs.some((r) => used.has(sheetTextureKey(r.name, r.action)))) continue;
      this.pending.delete(g);
      const n = releaseSheets(this.host.scene, reqs);
      this.log.push({ e: `release:${g}`, n });
      if (g === 'intro') this.loadDeferred();
      if (g === 'phaseDrink') this.tryRim();
    }
  }

  summary(): Record<string, unknown> {
    return {
      rimReady: this.rimReady,
      finaleReady: this.finaleReady,
      pending: [...this.pending.keys()],
      peakMb: this.peakMb,
      loader: (() => {
        const l = this.host.scene.load as unknown as { list: { size: number }; inflight: { size: number } };
        return { loading: this.host.scene.load.isLoading(), list: l.list.size, inflight: l.inflight.size };
      })(),
      log: [...this.log],
    };
  }

  destroy(): void {
    for (const [e, fn] of this.subs) EventBus.off(e, fn, this);
    this.pending.clear();
  }
}
