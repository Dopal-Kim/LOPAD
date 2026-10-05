/**
 * 57라운드 갈래 재설계 — 수단·2단 규칙 실행 (씬 쪽, BuildRuntime 의 일부). 입력은 Player `BranchMoves`(PLAYER_BRANCH_MOVE).
 * 60라운드 6-1 정리: 무기별로 나눴다 — 공용 도우미 `branch/BranchKit`, 칼 `KatanaBranch` · 대검 `GreatswordBranch` ·
 * 단검 `DaggerBranch` · 활 `BowBranch`. 이 파일은 사건을 지금 무기 갈래로 나눠 보내는 창구(바깥 API 그대로).
 * 그림은 계약 art §20·§21 시트 (없으면 윤곽 플레이스홀더). 그림 배율 = 판정 배율(55 Q15).
 */
import {
  EventBus,
  Events,
  type PlayerAttackPayload,
  type PlayerBranchMovePayload,
  type PlayerSecondaryPayload,
} from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import type { Mob } from '../../../objects/Mob';
import type { Projectile } from '../../../objects/Projectile';
import { param } from '../../../systems/build/buildMods';
import type { Game } from '../../Game';
import type { BuildRuntime } from './BuildRuntime';
import type { PerfectKind } from './BuildPerfect';
import { BowBranch } from './branch/BowBranch';
import { BranchKit, type Dir } from './branch/BranchKit';
import { DaggerBranch } from './branch/DaggerBranch';
import { GreatswordBranch } from './branch/GreatswordBranch';
import { KatanaBranch } from './branch/KatanaBranch';

export class BranchStrikes {
  private readonly kit: BranchKit;
  readonly katana: KatanaBranch;
  readonly greatsword: GreatswordBranch;
  readonly dagger: DaggerBranch;
  readonly bow: BowBranch;

  constructor(g: Game, rt: BuildRuntime) {
    this.kit = new BranchKit(g, rt);
    this.katana = new KatanaBranch(this.kit);
    this.greatsword = new GreatswordBranch(this.kit);
    this.dagger = new DaggerBranch(this.kit);
    this.bow = new BowBranch(this.kit);
    EventBus.on(Events.PLAYER_BRANCH_MOVE, this.onMove, this);
    EventBus.on(Events.PLAYER_SECONDARY, this.onSecondary, this);
  }

  /** 갈래 동작 중 (강공 — 중량 6 감소·끊기지 않음) */
  get busy(): boolean {
    return this.kit.busy;
  }

  private get weapon(): string {
    return gameState.weapon.id;
  }

  // --- 입력 사건 (Player BranchMoves) ---

  private onMove(e: PlayerBranchMovePayload): void {
    const dir: Dir = { x: e.dirX, y: e.dirY };
    if (e.phase === 'ready') {
      this.katana.onReady(e.move, dir);
      return;
    }
    if (e.move === 'spin' && e.phase === 'release') this.katana.spin(dir);
    else if (e.move === 'spin' && e.phase === 'sustain') this.katana.vortexStart();
    else if (e.move === 'spin' && e.phase === 'end') this.katana.vortexEnd();
    else if (e.move === 'unblockable' && e.phase === 'release') this.katana.unblockable(dir);
    else if (e.move === 'fanThrow' && e.phase === 'release') this.dagger.fanThrow(dir);
  }

  private onSecondary(p: PlayerSecondaryPayload): void {
    if (p.kind === 'guard' && p.phase === 'block') this.greatsword.onGuardBlock();
    if (this.weapon === 'bow') this.bow.onSecondary(p);
  }

  /** 공격 페이로드 (BuildCombat.onAttack 에서) */
  onAttack(p: PlayerAttackPayload): void {
    const w = this.weapon;
    if (w === 'greatsword') this.greatsword.onAttack(p);
    if (w === 'bow') this.bow.onAttack(p);
    if (w === 'dagger') this.dagger.onAttack(p);
  }

  /** 대검 차지 균열 — GreatswordBranch.onCrackLine */
  onCrackLine(
    p: PlayerAttackPayload,
    origin: { x: number; y: number },
    dir: Dir,
    tiles: number,
    lengthPx: number,
  ): { skip: boolean; sheet: string | null } {
    const out = this.greatsword.onCrackLine(p, origin, dir, tiles, lengthPx);
    // 61 G 개성 '빨아들이는 균열'
    if (!out.skip && p.crackLine) this.kit.rt.traits.onCrackLine(origin, dir, lengthPx, p.crackLine.halfWidthPx);
    return out;
  }

  /** 완벽 성공: 반향(퍼펙트 가드) · 천공(완벽 놓기) · 명경(패링) */
  onPerfect(kind: PerfectKind, _attack: number, dx: number, dy: number): void {
    if (kind === 'perfectGuard') this.greatsword.resonance(dx, dy, 1);
    if (kind === 'perfectRelease') this.bow.onPerfectRelease();
    if (kind === 'parry') this.katana.onParry(dx, dy);
  }

  onResource(event: string): void {
    this.greatsword.onResource(event);
  }

  // --- 단검 ---

  takeStuckKnife(): { x: number; y: number } | null {
    return this.dagger.takeStuckKnife();
  }

  brandBurstMult(): number {
    return this.dagger.brandBurstMult();
  }

  brandImmediateRatio(): number {
    return this.dagger.brandImmediateRatio();
  }

  onBrandBurst(mob: Mob, marks: number, dmg: number, died: boolean): void {
    this.dagger.onBrandBurst(mob, marks, dmg, died);
    // 61 G 귀화·분신 방패
    this.kit.rt.traits.onBrandBurst(mob, marks, died);
  }

  // --- 투사체 ---

  onShotHit(shot: Projectile, mob: Mob, died: boolean): void {
    this.dagger.onShotHit(shot, mob, died);
  }

  arrowBonus(p: PlayerAttackPayload): { mult: number; forceCrit: boolean; wallPierce: boolean; sizeMult: number } {
    return this.bow.arrowBonus(p);
  }

  onArrowSpawn(shot: Projectile, p: PlayerAttackPayload): void {
    this.bow.onArrowSpawn(shot, p);
  }

  onArrowHit(shot: Projectile, mob: Mob): void {
    this.bow.onShotHit(shot, mob);
  }

  longPerfectCrit(shot: Projectile, mob: Mob): boolean {
    return this.bow.longPerfectCrit(shot, mob);
  }

  // --- 처치 · 이동기 · 배율 ---

  onKill(mob: Mob, _kind: string, info: { marks: number; brands: number; hadDot: boolean }): void {
    this.katana.onKill();
    this.bow.onKill(mob);
    // 번지는 피: 출혈 적 처치 시 과열 −25%
    const rt = this.kit.rt;
    const sb = rt.rule('bleedKillCool');
    if (sb && info.hadDot) rt.combat.restoreResource({ heat: param(sb, 'heat') });
  }

  onPlayerMove(_kind: 'dash' | 'shadowstep'): void {
    this.dagger.onPlayerMove();
  }

  moveSpeedMult(_now: number): number {
    return this.dagger.heatwaveMult();
  }

  attackSpeedMult(_now: number): number {
    return this.dagger.heatwaveMult();
  }

  update(now: number): void {
    this.kit.tickBusy(now);
    this.katana.update(now);
    this.dagger.update(now);
    this.bow.update(now);
  }

  debug(): Record<string, unknown> {
    return {
      ...this.kit.last,
      busy: this.kit.busy,
      ...this.katana.debug(),
      ...this.dagger.debug(),
      ...this.bow.debug(),
    };
  }

  destroy(): void {
    EventBus.off(Events.PLAYER_BRANCH_MOVE, this.onMove, this);
    EventBus.off(Events.PLAYER_SECONDARY, this.onSecondary, this);
    this.katana.destroy();
    this.greatsword.destroy();
    this.dagger.destroy();
    this.bow.destroy();
  }
}
