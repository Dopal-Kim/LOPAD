/**
 * 48라운드 §6.2 무기를 든 자세 (몸 시트 구간 재생). 시트가 없으면 아무것도 하지 않는다 (기존 틴트만).
 * - 특수 자세 `player_<무기>_special` 구간(JSON `phases`): 패링 창 ready+window → 성공 riposte+recover / 실패 recover,
 *   가드 enter → (누르는 동안 loopFrames 반복) → 떼면 release+recover, 그림자 걸음 arrive+primed
 * - 활 조준 `player_bow_aim`: 진행도 프레임 유지, 발사 = releaseFrame
 * - 이동: 이동 중엔 이동 방향, 멈춰 있으면 마우스 조준 방향으로 idle/walk
 */
import type Phaser from 'phaser';
import { FEEL, SPRITES } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import type { InputState } from '../../systems/InputSystem';
import {
  aimAction,
  bodyBaseAction,
  GROGGY_ACTION,
  facingOf,
  frameDurations,
  progressFrame,
  specialAction,
  type Facing,
} from '../../systems/sprites/spriteDefs';
import { bodyActionFor, strideRate } from '../../systems/sprites/spriteMeta';
import { drawFrame } from '../../systems/weapon/bowDraw';
import type { Player } from '../Player';

/** 48라운드 특수 자세 구간 */
export type SpecialStep = 'parryStart' | 'parrySuccess' | 'parryFail' | 'guardStart' | 'guardRelease' | 'shadowArrive';

/** 유지형 보조 동작 자세를 매 프레임 이만큼 유지 (다음 프레임에 갱신) */
const SECONDARY_HOLD_MS = 80;

export class PlayerPoses {
  /** 디버그 (52라운드 Q10): 지난 프레임 걷기·달리기 재생 배속 */
  strideRate = 1;

  constructor(private readonly p: Player) {}

  /**
   * 53라운드 Q19: 무기별 이동 몸 동작 (idle·walk·run·dash → 아트 규칙 bodySheetByWeapon → `<동작>_<무기>` → 기본).
   * 칼은 칼집을 쥔 기본 몸, 대검·단검·활은 왼손이 빈 `_free` (아트 규칙). 시트가 없으면 기본 동작 그대로
   */
  bodyAction(base: string): string {
    const visual = this.p.visual;
    return bodyActionFor(base, gameState.weapon.id, (a) => (visual.hasAction(a) ? visual.sheet(a) : undefined));
  }

  /** 커서 방향 (커서가 없으면 지금 방향) */
  private aimFacing(input?: InputState): Facing {
    const p = this.p;
    return input ? facingOf(input.aimX - p.x, input.aimY - p.y, p.visual.facing) : p.visual.facing;
  }

  /** 보조 동작 순간 무기를 든 자세 (`player_<무기>_special`) */
  playSpecial(time: number, step: SpecialStep, fitMs?: number, input?: InputState): void {
    const visual = this.p.visual;
    const action = specialAction(gameState.weapon.id);
    if (!visual.hasAction(action)) return;
    const def = visual.sheet(action)!;
    const ph = (name: string, fallback: number[]) => {
      const v = (def.phases as Record<string, number[]> | undefined)?.[name];
      return Array.isArray(v) && v.length > 0 ? v : fallback;
    };
    const cols: Record<SpecialStep, number[]> = {
      parryStart: [...ph('ready', [0]), ...ph('window', [1, 2])],
      parrySuccess: [...ph('riposte', [3]), ...ph('recover', [4])],
      parryFail: ph('recover', [def.frames - 1]),
      guardStart: ph('enter', [0]),
      guardRelease: [...ph('release', [3, 4]), ...ph('recover', [5])],
      shadowArrive: [...ph('arrive', [2, 3]), ...ph('primed', [4])],
    };
    visual.playFrames(action, this.aimFacing(input), cols[step], time, fitMs);
  }

  /**
   * 유지형 보조 동작 자세: 가드 = 특수 자세 loopFrames 반복, 활 = 56라운드 당김 유지 시트(`<무기>_draw_hold` — 진행 → 유지 반복 →
   * 흔들림 반복, `bowDraw.drawFrame`), 없으면 조준 시트의 진행도 프레임 (min(5, floor(p×5)))
   */
  holdSecondary(input: InputState, time: number): void {
    const p = this.p;
    const visual = p.visual;
    const id = gameState.weapon.id;
    const dir = this.aimFacing(input);
    if (p.action === 'aim') {
      const hold = `${id}_draw_hold`;
      const st = p.secondaryDriver.drawStateAt(time);
      if (st && visual.hasAction(hold)) {
        visual.hold(hold, dir, drawFrame(st, visual.sheet(hold)!), time, SECONDARY_HOLD_MS);
        return;
      }
      const action = aimAction(id);
      if (!visual.hasAction(action)) return;
      const def = visual.sheet(action)!;
      const prog = def.progressFrames ?? [0, 1, 2, 3, 4, 5];
      const f = prog[progressFrame(p.aimProgress(time), prog.length, FEEL.SECONDARY.AIM_CHARGE_DIVISOR)] ?? 0;
      visual.hold(action, dir, f, time, SECONDARY_HOLD_MS);
    } else if (p.action === 'guard') {
      const action = specialAction(id);
      if (!visual.hasAction(action) || visual.isBusy(time)) return;
      const def = visual.sheet(action)!;
      // 56라운드 Q48 칼 가드: 반복 열이 없는 패링 자세는 창 끝 열(holdFrame) 유지
      if (!def.loopFrames && typeof def.holdFrame === 'number') {
        visual.hold(action, dir, def.holdFrame, time, SECONDARY_HOLD_MS);
        return;
      }
      const loop = def.loopFrames ?? [1, 2];
      const d = frameDurations(def);
      if (!visual.current?.includes(`#p${loop.join('-')}`) || visual.facing !== dir)
        visual.loopFrames(action, dir, loop, d[loop[0]] ?? 160);
    }
  }

  /**
   * 조준 사격 발사 순간: 56라운드 놓기 시트(`<무기>_release`, 화살 = f0 시작) 1회 → 없으면 활 조준 시트의 발사 프레임(releaseFrame).
   * 시트가 없으면 false
   */
  playAimRelease(dir: Facing, time: number): boolean {
    const visual = this.p.visual;
    const release = `${gameState.weapon.id}_release`;
    if (visual.hasAction(release)) {
      visual.release();
      return visual.oneShot(release, dir, time) > 0;
    }
    const action = aimAction(gameState.weapon.id);
    if (!visual.hasAction(action)) return false;
    const def = visual.sheet(action)!;
    visual.release();
    return visual.playFrames(action, dir, [def.releaseFrame ?? def.frames - 1], time) > 0;
  }

  /**
   * 51라운드 Q3 템포: 두 구간 맞춤 기준 프레임. 연격 = 몸 시트 hitFrames[0] 시작을 hitAtMs(가열 배속 반영)에,
   * 활 = releaseFrame 시작을 drawMs(시위 당김)에. 맞출 값이 없으면 null (균일 맞춤)
   */
  keyFrame(
    action: string,
    combo: { hit: { hitAtMs?: number; durationMs: number }; durationMs: number } | null,
    shot: { drawMs: number; releaseFrame: number } | null,
  ): { frame: number; atMs: number } | null {
    const def = this.p.visual.sheet(action);
    if (!def) return null;
    if (combo) {
      const at = combo.hit.hitAtMs;
      // 55라운드: 판정 프레임 = hitFrames[0], 없으면 impactFrame (내리찍기 몸을 대검 V·차지 내려찍기 대체 그림으로)
      const hf = def.hitFrames?.[0] ?? (typeof def.impactFrame === 'number' ? def.impactFrame : undefined);
      if (!at || hf === undefined || combo.durationMs <= 0) return null;
      return { frame: hf, atMs: (at * combo.durationMs) / combo.hit.durationMs };
    }
    if (shot && shot.drawMs > 0 && shot.releaseFrame < def.frames)
      return { frame: shot.releaseFrame, atMs: shot.drawMs };
    return null;
  }

  /** 연격 시트 activeFrames 구간 길이 ms (첫 열 시작 ~ 마지막 열 끝, 재생 배속 반영). 없으면 0 */
  activeWindowMs(sheet: { activeFrames?: number[]; frames: number } | undefined): number {
    const visual = this.p.visual;
    const af = sheet?.activeFrames;
    if (!af || af.length === 0) return 0;
    const first = Math.min(...af);
    const last = Math.max(...af);
    const starts = visual.lastFrameStarts;
    const end = last + 1 < sheet.frames ? starts[last + 1] : visual.lastDurationMs;
    return Math.max(0, (end ?? 0) - (starts[first] ?? 0));
  }

  /**
   * 이동 중엔 이동 방향, 멈춰 있으면 마우스 조준 방향으로 idle/walk/run. 반환 = 움직이는 중.
   * 52라운드 Q13: 달리는 중(Shift)이면 `run` 시트(없으면 walk). Q10: 시트 stride 가 있으면 실제 이동 속도에 맞춘 배속
   */
  locomotion(input: InputState, dir: Phaser.Math.Vector2, time: number): boolean {
    const p = this.p;
    const moving = dir.lengthSq() > 0 && p.action !== 'dash';
    const facing = moving ? facingOf(dir.x, dir.y, p.visual.facing) : this.aimFacing(input);
    if (!moving) {
      // 56라운드 Q7: 그로기 중 서 있으면 그로기 몸(칼·대검 공용 루프, 시트가 없으면 대기)
      const groggy = p.groggy && p.action === 'normal' && p.visual.hasAction(GROGGY_ACTION);
      p.visual.loop(groggy ? GROGGY_ACTION : this.bodyAction('idle'), facing, time);
      return false;
    }
    // 53라운드 Q10: 기본 이동 = run 그림, 감속 상태(조준·충전·당김·가드·기력 바닥 등)만 walk. Shift 달리기 = run 을 더 빠르게
    const slow = p.moveSlowMult < SPRITES.WALK_BELOW_MULT;
    const action = this.bodyAction(!slow && p.visual.hasAction('run') ? 'run' : 'walk');
    const def = p.visual.sheet(action);
    const v = p.body.velocity;
    const speed = Math.hypot(v.x, v.y);
    this.strideRate = def ? strideRate(def, speed, bodyBaseAction(action) === 'run' ? p.speedPx : undefined) : 1;
    p.visual.loop(action, facing, time, this.strideRate);
    return true;
  }
}
