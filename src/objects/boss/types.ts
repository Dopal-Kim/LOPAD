/**
 * 54라운드 Q4 보스 패턴 모듈 형식. 패턴 모듈은 Phaser 를 직접 쓰지 않고 이 인터페이스(보스 = BossHost, 방 = BossArenaApi)만 본다
 * → node 단위 테스트에서 가짜 보스·가짜 방으로 상태 흐름을 검증할 수 있다.
 */
import type { BossActionKind, BossLoopKind } from '../../core/EventBus';
import type { BossDef } from '../../data/types';
import type { BossPatternName, PatternParams } from '../../data/bossPatterns';
import type { MobContext } from '../Mob';
import type { Facing } from '../../systems/sprites/spriteDefs';

export interface Vec {
  x: number;
  y: number;
}

/** 패턴 끝 신호 */
export interface PatternEnd {
  /** false 면 쿨타임 기록·다음 예약을 하지 않는다 (35라운드 돌진 벽 경직 뒤 — 예약은 부딪힌 순간에 이미 했다). 기본 true */
  finish?: boolean;
  /** 이어서 바로 시작할 패턴 (돌진 → 부채꼴, 한 잔 더 → 화면 패턴, 화면 패턴 → 3연 취권) */
  next?: BossPatternName;
  /** 1층 얼큰: 다음 패턴 강화 */
  empower?: boolean;
  /** 끝나며 경직 ms (잔 깨짐) — 보스 경직(Mob.stun 'hit')으로 */
  stunMs?: number;
  /** 경직 동안 자세 (동작·국면·이어서 반복할 국면) */
  stunPose?: { action: string; phase: string; thenLoop?: string };
}

/** 진행 중인 패턴 한 판 */
export interface PatternRun {
  /** 매 프레임. 끝나면 PatternEnd, 진행 중이면 null */
  update(ctx: MobContext): PatternEnd | null;
  /** 끊김 (패링 경직·페이즈 진입 연출·사망): 마커·방 효과 정리 */
  cancel(): void;
  /** 지금 접촉 공격력 (null = 보스 기본 contactAttack). 0 이면 접촉 피해 없음 */
  contactAttack?(): number | null;
  /** 디버그 상태 이름 (35라운드 patternState 와 같은 값: telegraph·dash·stun·…) */
  readonly state: string;
}

export interface BossPatternModule {
  readonly name: BossPatternName;
  /** 쿨타임·pick 외 조건 (소환 상한 등). 없으면 늘 가능 */
  isReady?(host: BossHost, ctx: MobContext): boolean;
  /** 시작. 바로 끝나는 패턴(예고 없는 부채꼴·화면 패턴 방아쇠)은 PatternEnd 를 돌려준다 */
  start(host: BossHost, ctx: MobContext): PatternRun | PatternEnd;
}

/** 보스 몸 연출 (시트가 없으면 임시 연출: 기울기·색). 구현은 objects/boss/bossPose.ts */
export interface BossPoseApi {
  /** 35라운드 돌진 예고 자세: attack phaseFrames telegraph[0] 유지, 없으면 첫 예고만 attack 을 fitMs 에 맞춰 재생 */
  dashTelegraph(time: number, target: Vec, fitMs: number, first: boolean): void;
  /** 돌진 중 frame 1↔2 반복 */
  dashLoop(dirX: number, dirY: number): void;
  /** 멈춤·벽 경직·부채꼴·내리찍기 frame 3 유지 */
  recover(time: number, ms?: number): void;
  /** 플레이어를 보며 frame 3 유지 (없으면 attack 재생) */
  holdFacing(time: number, target: Vec, ms?: number): void;
  release(): void;
  /**
   * 54라운드 v3 동작 국면: `action` 시트의 phaseFrames[phase] 를 한 번 재생(loop 면 반복)·fitMs 에 맞춤.
   * 시트·국면이 없으면 임시 연출(tint·lean)만 하고 false
   */
  phase(
    action: string,
    phase: string,
    time: number,
    opts?: { loop?: boolean; fitMs?: number; target?: Vec; thenLoop?: string },
  ): boolean;
  /** 동작 전체를 fitMs 에 맞춰 1회 (impactFrame·releaseFrame 이 atMs 에 오도록 keyFrame 지정 가능) */
  play(action: string, time: number, opts?: { fitMs?: number; keyAtMs?: number; target?: Vec }): boolean;
  /** 동작 시트의 이벤트 프레임 시작 ms (impactFrame·releaseFrame — 없으면 null) */
  keyFrameMs(action: string, key: 'impactFrame' | 'releaseFrame'): number | null;
  /** 임시 연출: 몸 기울기 (rad, 0 = 바로) */
  lean(rad: number): void;
  /** 임시 연출: 쓰러짐 (true) · 일어남 */
  lie(on: boolean): void;
  /** 잔 약점 사각형 (월드). drink 시트 cupAnchors 가 있으면 현재 프레임, 없으면 머리 위 임시 사각형 */
  cupRect(fallback: { w: number; h: number; lift: number }): { x: number; y: number; w: number; h: number };
  /**
   * 시트 앵커 (footAnchors·handAnchors) 월드 좌표. `at` 이 없으면 현재 프레임, 있으면 그 이벤트 프레임(impactFrame·releaseFrame —
   * 그 프레임 점이 null 이면 바로 앞 점, 방향은 재생 중인 행 또는 지금 방향). 없으면 null
   */
  anchor(action: string, key: 'footAnchors' | 'handAnchors', at?: 'impactFrame' | 'releaseFrame'): Vec | null;
  /** 61 E: 지금 프레임의 잔이 보이는지 (drink 시트 cupAnchors visible — 앵커가 없으면 true) */
  cupVisible(): boolean;
  /** drink 시트에 cupAnchors 가 있는지 (없으면 방이 임시 잔을 그린다) */
  readonly cupArt: boolean;
  /** 35라운드 소환 뒤 멈춤: attack frame 3 길이 (없으면 0) */
  recoverHoldMs(): number;
  /** 지금 보는 방향 */
  readonly facing: Facing;
}

/** 약점 잔 등록 내용 (setWeakPoint) */
export interface WeakPointSpec {
  rect: () => { x: number; y: number; w: number; h: number };
  onHit: () => void;
  drawCup?: boolean;
  /** 깨지기까지 맞혀야 하는 수 (기본 1) */
  hits?: number;
  visible?: () => boolean;
}

/** 보스 본체가 패턴에 열어 주는 창구 */
export interface BossHost {
  readonly id: string;
  readonly def: BossDef;
  readonly phaseIndex: number;
  readonly rng: { pick<T>(list: readonly T[]): T; next(): number };
  /** 발 피벗 (sprite x, y) */
  readonly pos: Vec;
  /** 물리 바디 중심 */
  readonly center: Vec;
  readonly halfWidth: number;
  readonly pose: BossPoseApi;
  /** 현재 페이즈 + 이 판의 강화 여부로 해석한 수치 */
  params<T = PatternParams>(name: BossPatternName): T;
  /** 이 페이즈 pick 에 있는지 */
  inPick(name: BossPatternName): boolean;
  /** 쿨타임이 끝났고 조건이 맞는지 */
  isReady(name: BossPatternName, ctx: MobContext): boolean;
  readyAt(name: BossPatternName): number;
  setReadyAt(name: BossPatternName, at: number): void;
  scheduleNext(time: number): void;
  setVelocity(vx: number, vy: number): void;
  /** 벽·기둥 등 단단한 것에 막혔는지 (Arcade body.blocked) */
  readonly blocked: boolean;
  angleTo(x: number, y: number): number;
  paint(color: number): void;
  restoreColor(): void;
  setInvulnerable(until: number): void;
  /** 61라운드 P6: 파훼로 무너짐 — ms 동안 받는 피해 × breakDamageMult (잔 깨짐·기둥 충돌·취권 넘어짐·술통 되치기) */
  markBroken(ms: number): void;
  /** 소환한 수 (디버그) */
  addSummoned(n: number): void;
  emitTelegraph(name: BossPatternName): void;
  emitAttack(name: BossPatternName): void;
  emitAction(action: BossActionKind, index?: number): void;
  emitLoop(loop: BossLoopKind, on: boolean): void;
  emitWallHit(): void;
}

/** 보스방 환경 (기둥·촛대·술통·술 웅덩이·화면 효과). 구현은 systems/boss/BossArena.ts — 보스방이 아니면 ctx.arena 없음 */
export interface BossArenaApi {
  /** 세상이 돈다: 카메라 기울기 (feelSettings.tilt 가 0 이면 기울기·흐림 생략, 패턴은 그대로) */
  startTilt(p: { durationMs: number; tiltDeg: number; periodMs: number; rampMs: number; blur?: number }): void;
  readonly tilting: boolean;
  /** 등불 끄기: 촛대를 차례로 쓰러뜨리고(gapMs) 주변광을 낮춘다. durationMs 뒤 저절로 복구 */
  lightsOut(p: { fadeMs: number; durationMs: number; darkAmbient: string; toppleGapMs: number }): void;
  readonly dark: boolean;
  /** 술통 경로 미리 보기: from 에서 dir 로, 벽·기둥에 bounces 번 튕기며 maxPx 까지 (꺾이는 점 목록) */
  traceCask(from: Vec, dirX: number, dirY: number, bounces: number, maxPx: number, radiusPx: number): Vec[];
  /** 술통 걷어차기 */
  kickCask(
    from: Vec,
    dirX: number,
    dirY: number,
    p: {
      speedTiles: number;
      bounces: number;
      maxTiles: number;
      attack: number;
      radiusPx: number;
      puddleEveryTiles: number;
      puddleMs: number;
      bossHitDamage: number;
      bossHitStunMs: number;
    },
  ): void;
  /** 술 뿌리기: 점 목록을 따라 웅덩이 칸 (술 방울 그림은 from 에서 — 없으면 첫 점) */
  spill(
    points: readonly Vec[],
    p: { puddleMs: number; fireMs: number; fireTickMs: number; firePlayerAttack: number; spreadMsPerCell: number },
    from?: Vec,
  ): void;
  /** 54라운드 Q21: 굴러가는 술통 판정 반경 = 그림 굴림 둘레 / 2π × ratio (그림이 없으면 fallbackPx) */
  caskRadiusPx(fallbackPx: number, ratio: number): number;
  /** 횃불 던지기: flightMs 뒤 to 에 떨어져 그 자리 웅덩이에 불 (웅덩이가 없으면 꺼짐) */
  throwTorch(from: Vec, to: Vec, flightMs: number): void;
  /**
   * 약점(잔) 등록: 근접 판정·화살이 rect() 에 닿을 때마다 1회 — hits 번(기본 1) 맞으면 onHit (깨짐). 그 전 맞음은 struck 표시.
   * visible = 지금 프레임에 잔이 보이는지 (61 E 파훼 표시 cup_glint — 없으면 늘 보임). null 이면 해제
   */
  setWeakPoint(wp: WeakPointSpec | null): void;
}
