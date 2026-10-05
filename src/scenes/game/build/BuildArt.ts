/**
 * 60라운드 계약 art §21 빌드 축 시트 연결 (씬 쪽, BuildRuntime 의 일부): 상태·세트·저주 표시 루프와 일회성 fx 배치.
 * - 적 머리 위·몸 중심에 붙는 상태 루프(표식 `status_mark` 행 = 스택 · 화상 `status_burn` · 감속 `status_slowed` · 경직 `status_stagger`)는
 *   매 프레임 장부(MarkBook·DotBook·Mob.statusSlowUntil)를 읽어 맞춘다 (`rowsAre` stacks 는 같은 프레임 번호로 행만 바꿈 대신 새로 찍음).
 * - 주인공 루프: 취기 `status_drunk`(그로기면 끔) · 저주 `curse_mark`(행 = 저주 종류, 데이터 `markRow`) · 살기 `chain_bloodlust` 등.
 *   머리 꼭대기 앵커가 없으면 피벗 위 124 도트 × 렌더 배율.
 * - 시트가 없으면 아무것도 하지 않는다 (호출 쪽 플레이스홀더 윤곽이 그대로).
 */
import { BUILD_ART, DEPTH, FEEDBACK } from '../../../core/Constants';
import { gameState } from '../../../core/GameState';
import { curseDef } from '../../../data/build';
import type { Mob } from '../../../objects/Mob';
import type { FxHandle, FxPlayOptions } from '../../../systems/fx/fx';
import { fxDrawScale } from '../../../systems/sprites/spriteDefs';
import { PLAYER_RENDER_SCALE } from '../../../systems/weapon/playerScale';
import type { Game } from '../../Game';
import type { BuildRuntime } from './BuildRuntime';

type Anchor = 'head' | 'center';

interface Loop {
  handle: FxHandle | null;
  key: string;
}

/** 시트 JSON 의 `loopRange` (형식이 틀리면 없음) */
export function sheetLoopRange(def: unknown): [number, number] | undefined {
  const r = (def as { loopRange?: unknown } | null)?.loopRange;
  return Array.isArray(r) && r.length === 2 && r.every((v) => typeof v === 'number') ? [r[0], r[1]] : undefined;
}

export class BuildArt {
  private readonly mobLoops = new Map<Mob, Map<string, Loop>>();
  private readonly playerLoops = new Map<string, Loop>();
  /** 경직 표시 끝 시각 (적마다) */
  private readonly staggerUntil = new Map<Mob, number>();
  /** 살기 루프 끝 */
  bloodlustUntil = -Infinity;

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {}

  private get now(): number {
    return this.g.time.now;
  }

  has(id: string): boolean {
    return this.g.fx.has(id);
  }

  /** 적 기준 위치 오프셋 (머리 위 — 낙인 표식과 같은 규칙 / 몸 중심) */
  private mobOffset(mob: Mob, anchor: Anchor, up = 0): { x: number; y: number } {
    if (anchor === 'center') return { x: mob.body.center.x - mob.x, y: mob.body.center.y - mob.y - up };
    const top = mob.getTopCenter().y ?? mob.y;
    return { x: 0, y: top - mob.y - FEEDBACK.BRAND.HEAD_GAP_PX - up };
  }

  /** 주인공 머리 꼭대기 오프셋 (피벗 위 124 도트 × 렌더 배율) */
  private headTop(up = 0): { x: number; y: number } {
    return { x: 0, y: -BUILD_ART.HEAD_TOP_PX * PLAYER_RENDER_SCALE - up };
  }

  // --- 일회성 ---

  /** 월드 한 자리 1회 (시트 없으면 false) */
  once(id: string, x: number, y: number, opts: FxPlayOptions = {}): boolean {
    if (!this.has(id)) return false;
    return this.g.fx.play(id, x, y, { depth: DEPTH.HIT_FX, ...opts }) !== null;
  }

  /** 적 몸에 1회 (따라가지 않음 — hitbox_center) */
  onceAtMob(id: string, mob: Mob, opts: FxPlayOptions = {}): boolean {
    const c = mob.body.center;
    return this.once(id, c.x, c.y, opts);
  }

  /** 주인공 발에 따라가며 1회 (above / below_player) */
  onPlayer(id: string, opts: { below?: boolean; dir?: string } = {}): boolean {
    const pl = this.g.player;
    if (!this.has(id) || !pl) return false;
    return (
      this.g.fx.play(id, pl.x, pl.y, {
        follow: pl,
        depthOffset: DEPTH.OVERLAY_STEP * (opts.below ? -1 : 3),
        scaleMult: PLAYER_RENDER_SCALE,
        ...(opts.dir ? { dir: opts.dir } : {}),
      }) !== null
    );
  }

  /**
   * 선 모양 fx (계약 art §21 — 시작점 기준, 오른쪽을 향해 그린 시트를 진행 각도로 회전): `tile: true` 반복 시트는 이어 깔고
   * (`BuildEffects.tileLine`), JSON `lengthPx`(그린 길이 도트)가 있으면 판정 길이에 맞춰 늘린다. 시트가 없으면 false
   */
  lineFx(id: string, x: number, y: number, dirX: number, dirY: number, len: number): boolean {
    const g = this.g;
    if (!this.has(id)) return false;
    const def = g.fx.sheet(id);
    const meta = def as unknown as { tile?: boolean; lengthPx?: number } | null;
    if (meta?.tile) return this.rt.fx.tileLine(id, x, y, dirX, dirY, len);
    const drawnLen =
      def && typeof meta?.lengthPx === 'number' && meta.lengthPx > 0 ? meta.lengthPx * fxDrawScale(def) : 0;
    return (
      g.fx.play(id, x, y, {
        angle: Math.atan2(dirY, dirX),
        depth: DEPTH.FX_GROUND,
        scaleMult: drawnLen > 0 ? len / drawnLen : PLAYER_RENDER_SCALE,
      }) !== null
    );
  }

  /** 경직 표시 (`status_stagger` — 경직 동안 f2~f3, 끝나면 f4) */
  stagger(mob: Mob, ms: number): void {
    if (!this.has(BUILD_ART.STAGGER) || !mob.active) return;
    this.staggerUntil.set(mob, this.now + ms);
    this.mobLoop('stagger', BUILD_ART.STAGGER, mob, 'any', 'head', this.brandUp(mob, BUILD_ART.STAGGER));
  }

  /** 적에 붙는 일정 시간 루프 (출혈 dagger_brand_bleed 4초 등 — 몸 중심) */
  timedOnMob(slot: string, id: string, mob: Mob, ms: number): void {
    if (!this.has(id) || !mob.active) return;
    this.mobLoop(slot, id, mob, 'any', 'center');
    const h = this.mobLoops.get(mob)?.get(slot)?.handle ?? null;
    this.g.time.delayedCall(ms, () => {
      const cur = this.mobLoops.get(mob)?.get(slot);
      if (cur && cur.handle === h) this.stopMobLoop(mob, slot);
    });
  }

  // --- 루프 ---

  /** 적에 붙는 루프 (slot 마다 하나 — key 가 바뀌면 새로 찍는다) */
  private mobLoop(slot: string, id: string, mob: Mob, row: string, anchor: Anchor, up = 0): void {
    let slots = this.mobLoops.get(mob);
    if (!slots) {
      slots = new Map();
      this.mobLoops.set(mob, slots);
    }
    const key = `${id}#${row}`;
    const cur = slots.get(slot);
    if (cur && cur.key === key && this.g.fx.isActive(cur.handle)) return;
    if (cur) this.g.fx.stop(cur.handle, 0, false);
    const range = sheetLoopRange(this.g.fx.sheet(id));
    const handle = this.g.fx.play(id, mob.x, mob.y, {
      dir: row,
      follow: mob,
      followOffset: this.mobOffset(mob, anchor, up),
      depthOffset: DEPTH.OVERLAY_STEP * 4,
      hooks: false,
      ...(range ? { loopRange: range } : {}),
    });
    slots.set(slot, { handle, key });
  }

  private stopMobLoop(mob: Mob, slot: string): void {
    const cur = this.mobLoops.get(mob)?.get(slot);
    if (!cur) return;
    this.g.fx.finish(cur.handle);
    this.mobLoops.get(mob)!.delete(slot);
  }

  /** 낙인 표식과 겹치면 위로 (아트: 표식 18 도트·경직 20 도트) */
  private brandUp(mob: Mob, id: string): number {
    if (this.g.strikes.brands.marksOf(mob) <= 0) return 0;
    return id === BUILD_ART.STAGGER ? BUILD_ART.MARK_ABOVE_BRAND_PX * (20 / 18) : BUILD_ART.MARK_ABOVE_BRAND_PX;
  }

  /** 주인공 루프 (slot 마다 하나): headTop 이면 머리 꼭대기 위, 아니면 발 */
  playerLoop(slot: string, id: string, row: string, opts: { headTop?: number; below?: boolean } = {}): void {
    const pl = this.g.player;
    if (!pl || !this.has(id)) return;
    const key = `${id}#${row}#${opts.headTop ?? ''}`;
    const cur = this.playerLoops.get(slot);
    if (cur && cur.key === key && this.g.fx.isActive(cur.handle)) return;
    if (cur) this.g.fx.stop(cur.handle, 0, false);
    const handle = this.g.fx.play(id, pl.x, pl.y, {
      dir: row,
      follow: pl,
      ...(opts.headTop !== undefined ? { followOffset: this.headTop(opts.headTop) } : {}),
      depthOffset: DEPTH.OVERLAY_STEP * (opts.below ? -1 : 4),
      scaleMult: PLAYER_RENDER_SCALE,
      hooks: false,
    });
    this.playerLoops.set(slot, { handle, key });
  }

  stopPlayerLoop(slot: string, fade = true): void {
    const cur = this.playerLoops.get(slot);
    if (!cur) return;
    this.g.fx.stop(cur.handle, 0, fade);
    this.playerLoops.delete(slot);
  }

  playerLoopActive(slot: string): boolean {
    return this.g.fx.isActive(this.playerLoops.get(slot)?.handle ?? null);
  }

  // --- 매 프레임 동기화 ---

  update(now: number): void {
    this.syncMobs(now);
    this.syncPlayer(now);
  }

  private syncMobs(now: number): void {
    const marks = new Map(this.rt.marks.list());
    for (const mob of this.rt.fx.mobs()) {
      const n = marks.get(mob) ?? 0;
      if (n > 0 && this.has(BUILD_ART.MARK))
        this.mobLoop('mark', BUILD_ART.MARK, mob, String(Math.min(3, n)), 'head', this.brandUp(mob, BUILD_ART.MARK));
      else this.stopMobLoop(mob, 'mark');
      if (this.rt.dots.has(mob, 'burn', now) && this.has(BUILD_ART.BURN))
        this.mobLoop('burn', BUILD_ART.BURN, mob, 'any', 'center');
      else this.stopMobLoop(mob, 'burn');
      if (now < mob.statusSlowUntil && this.has(BUILD_ART.SLOWED))
        this.mobLoop('slowed', BUILD_ART.SLOWED, mob, 'any', 'center');
      else this.stopMobLoop(mob, 'slowed');
      const st = this.staggerUntil.get(mob);
      if (st !== undefined && now >= st) {
        this.staggerUntil.delete(mob);
        this.stopMobLoop(mob, 'stagger');
      }
    }
    // 죽은 적 정리
    for (const [mob, slots] of this.mobLoops) {
      if (mob.active) continue;
      for (const l of slots.values()) this.g.fx.stop(l.handle, 0, false);
      this.mobLoops.delete(mob);
      this.staggerUntil.delete(mob);
    }
  }

  private syncPlayer(now: number): void {
    const pl = this.g.player;
    if (!pl) return;
    // 취기 (그로기 우선 — 겹치면 끔)
    const drunk = this.rt.drunkActive && !pl.groggy;
    if (drunk) this.playerLoop('drunk', BUILD_ART.DRUNK, 'any', { headTop: 0 });
    else this.stopPlayerLoop('drunk');
    // 저주 표시 (행 = 저주 종류 — 데이터 markRow). 취기와 겹치면 위로
    const c = gameState.build.curse;
    const row = c ? curseDef(c.id)?.markRow : undefined;
    if (row)
      this.playerLoop('curse', BUILD_ART.CURSE_MARK, row, { headTop: drunk ? BUILD_ART.CURSE_ABOVE_DRUNK_PX : 0 });
    else this.stopPlayerLoop('curse');
    if (now < this.bloodlustUntil) this.playerLoop('bloodlust', BUILD_ART.BLOODLUST, 'any', { below: true });
    else this.stopPlayerLoop('bloodlust');
  }

  destroy(): void {
    for (const slots of this.mobLoops.values()) for (const l of slots.values()) this.g.fx.stop(l.handle, 0, false);
    this.mobLoops.clear();
    for (const l of this.playerLoops.values()) this.g.fx.stop(l.handle, 0, false);
    this.playerLoops.clear();
    this.staggerUntil.clear();
  }
}
