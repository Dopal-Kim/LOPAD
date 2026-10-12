/**
 * 62 루프 2 시스템 E — 문 나가기 (도영 님 피드백 '맵 넘어갈 때 이상한 발판 그만 밟고 자연스럽게'):
 * 바닥 안 2×2 출구 발판을 없애고, 방을 비우면 **외벽의 문**(진행 방향 = 동쪽)이 열린다.
 * - 열림: 막힘 판이 걷히고 문 빛이 켜지고 문턱 앞 바닥에 '오르는 길' 갈매기 (DoorView)
 * - 나가기: 주인공 발이 문턱(벽 안쪽 1칸 띠)에 들어서면 조작을 잠그고 문 쪽으로 2~3걸음 자동으로 걸어 들어가며 몸이 문 어둠에
 *   흐려진다(카메라는 따라감) → 끝에서 owner 의 onThrough (그림 속 입구 전환 · 지도 고르기 · 층 전환 · 수련장 지도)
 * - 들어오기: 새 노드는 반대편(서쪽) 문 안에서 시작해 0.6초 걸어 들어온 뒤 조작 해제 (탄생 전장은 없음 — 가운데에서 태어난다)
 * - 지도 고르기 취소: 문 안에서 문턱 안쪽으로 걸어 나온다
 * 자동 걸음 동안 주인공 바디의 타일 충돌을 끈다 (벽 칸을 지나 문 안으로). 배치 계산은 `systems/doors/doorPlan`.
 */
import { DOORS, TILE } from '../../../core/Constants';
import { EventBus, Events, type DoorOpenedPayload, type DoorWalkPayload } from '../../../core/EventBus';
import type { UiDoor, UiDoorPhase } from '../../../contract/ui';
import { neutralInput, type InputState } from '../../../systems/InputSystem';
import {
  alongDoor,
  arenaDoors,
  entryWalk,
  inThreshold,
  pastMouth,
  type DoorPoint,
  type DoorSpot,
} from '../../../systems/doors/doorPlan';
import type { FloorLayout } from '../../../systems/mapgen';
import { DoorView, type DoorLeafControl } from '../../../world/DoorView';
import type { SideDoorHost } from '../../../world/SideDoorArt';
import type { Game } from '../../Game';
import { worldToLogicalScreen } from '../../../systems/display';

export type DoorKind = DoorOpenedPayload['kind'];
type WalkPhase = DoorWalkPayload['phase'];

interface Walk {
  phase: WalkPhase;
  spot: DoorSpot;
  to: DoorPoint;
  /** 걸음 방향 (단위) */
  dir: DoorPoint;
  until: number;
  done: () => void;
}

/**
 * 이 씬의 문 자리 (WorldSetup — 테두리 문 그림 · ArenaDoors 가 같이 쓴다). 노드 전투장(노드 지도)·수련장 방에만,
 * 탄생 전장은 입구 문 없음
 */
export function doorSpotsFor(
  layout: FloorLayout | undefined,
  o: { routeMode: boolean; trainingRoom: boolean; birth: boolean },
): { exit: DoorSpot | null; entry: DoorSpot | null } {
  if (!layout?.arena || !(o.routeMode || o.trainingRoom)) return { exit: null, entry: null };
  return arenaDoors(layout, TILE, DOORS.OPEN_TILES, !o.birth);
}

export class ArenaDoors {
  readonly exit: DoorSpot | null;
  readonly entry: DoorSpot | null;
  private exitView: DoorView | null = null;
  private entryView: DoorView | null = null;
  private kind: DoorKind = 'node';
  private onThrough: (() => void) | null = null;
  private canLeave: () => boolean = () => true;
  /** 문턱을 벗어났다 다시 들어와야 나간다 (열린 순간 이미 서 있었거나 지도 취소 뒤) */
  private armed = true;
  private walk: Walk | null = null;
  /** 문 안 (지도 고르기·전환 대기 — 주인공 숨김) */
  private inside = false;
  /** 디버그 */
  readonly log: { t: number; ev: string; info?: unknown }[] = [];

  constructor(private readonly g: Game) {
    const spots = doorSpotsFor(g.layout, {
      routeMode: g.routeMode,
      trainingRoom: Boolean(g.training?.room),
      birth: g.nodeKind === 'birth',
    });
    this.exit = spots.exit;
    this.entry = spots.entry;
    // 62 루프 2 F (art §31-10): 문 그림 = 외벽 테두리 문 조각 또는 (테두리 없는 수련장 방) 문틀만 · 널문 그림(닫힘·열림 시트)이
    // 있으면 도형 막힘 판 대신
    const host: SideDoorHost | null = g.border ?? g.doorArt;
    const art = (side: DoorSpot['side']) =>
      side === 'east' || side === 'west' ? Boolean(host?.hasSideDoorArt(side)) : false;
    const leaf = (side: DoorSpot['side']): DoorLeafControl | null => {
      const b = host;
      if (!b || (side !== 'east' && side !== 'west') || !b.hasDoorLeaf(side)) return null;
      return { setOpen: (open, animate) => b.setDoorOpen(side, open, animate) };
    };
    if (this.exit) this.exitView = new DoorView(g, this.exit, art(this.exit.side), false, leaf(this.exit.side));
    if (this.entry) this.entryView = new DoorView(g, this.entry, art(this.entry.side), false, leaf(this.entry.side));
  }

  get hasExit(): boolean {
    return this.exit !== null;
  }

  get exitOpen(): boolean {
    return Boolean(this.exitView?.isOpen);
  }

  /** 자동 걸음 중 (입력 잠금) */
  get walking(): boolean {
    return this.walk !== null;
  }

  /** 걷는 중이거나 문 안 — 게임 입력을 잠근다 */
  get busy(): boolean {
    return this.walk !== null || this.inside;
  }

  get isInside(): boolean {
    return this.inside;
  }

  private note(ev: string, info?: unknown): void {
    this.log.push({ t: Math.round(this.g.time.now), ev, ...(info !== undefined ? { info } : {}) });
    if (this.log.length > 30) this.log.shift();
  }

  // --- 들어오기 ---

  /**
   * 새 노드·방에 들어올 때: 반대편 문 안에서 시작해 걸어 들어온다. 걸음 ms (입구 문이 없으면 0 — 그 자리에서 시작)
   */
  enter(): number {
    const g = this.g;
    const spot = this.entry;
    const A = g.layout?.arena;
    if (!spot || !A) return 0;
    const speed = g.player.speedPx;
    const spawn = { x: g.player.x, y: g.player.y };
    const w = entryWalk(spot, spawn, {
      walkDist: (speed * DOORS.ENTER_WALK_MS) / 1000,
      maxSpawnDist: DOORS.ENTER_SPAWN_MAX_TILES * TILE,
      stopDist: DOORS.ENTER_STOP_TILES * TILE,
      minOut: TILE * 0.75,
    });
    g.player.haltForWarp();
    g.player.body.reset(w.from.x, w.from.y);
    g.player.setAlpha(0);
    this.entryView?.open(false);
    const ms = (Math.hypot(w.to.x - w.from.x, w.to.y - w.from.y) / Math.max(1, speed)) * 1000;
    this.startWalk('in', spot, w.to, () => {
      g.player.setAlpha(1);
      this.entryView?.close();
    });
    this.note('enter', { from: w.from, to: w.to, ms: Math.round(ms) });
    return ms;
  }

  // --- 열기 · 나가기 ---

  /**
   * 출구 문을 연다. onThrough = 문 안까지 걸어 들어간 뒤 (그림 속 입구 전환·지도 고르기 등), canLeave = 지금 나가도 되는가
   * (싸움·메뉴·정지·전환 중이 아님). 출구 문이 없으면 false
   */
  openExit(kind: DoorKind, onThrough: () => void, canLeave: () => boolean, animate = true): boolean {
    if (!this.exit || !this.exitView) return false;
    this.kind = kind;
    this.onThrough = onThrough;
    this.canLeave = canLeave;
    if (this.exitView.isOpen) return true;
    this.exitView.open(animate);
    // 열린 순간 이미 문턱에 서 있으면 한 번 벗어났다 들어와야 (갑자기 빨려 들어가지 않게)
    this.armed = !inThreshold(this.exit, this.g.player.x, this.g.player.y, TILE);
    EventBus.emit(Events.DOOR_OPENED, { side: this.exit.side, kind } satisfies DoorOpenedPayload);
    this.note('open', kind);
    return true;
  }

  /** 매 프레임 (Game.update — 입력 처리 뒤): 걸음 진행 · 문턱 판정 */
  update(time: number): void {
    const g = this.g;
    const w = this.walk;
    if (w) {
      this.fade(w.spot);
      const left = (w.to.x - g.player.x) * w.dir.x + (w.to.y - g.player.y) * w.dir.y;
      // 시간 안에 못 닿으면 (프레임이 크게 끊김 등) 목표에 놓는다 — 벽 칸 안에 끼인 채 충돌이 켜지지 않게
      if (left > DOORS.ARRIVE_PX && time >= w.until) g.player.body.reset(w.to.x, w.to.y);
      if (left <= DOORS.ARRIVE_PX || time >= w.until) this.finishWalk();
      return;
    }
    const spot = this.exit;
    if (!spot || !this.exitView?.isOpen || this.inside) return;
    const on = inThreshold(spot, g.player.x, g.player.y, TILE);
    if (!on) {
      this.armed = true;
      return;
    }
    if (!this.armed || !this.canLeave()) return;
    this.armed = false;
    this.goOut();
  }

  /** 문턱 → 문 안으로 걸어 들어간다 (끝에 onThrough) */
  private goOut(): void {
    const spot = this.exit!;
    const g = this.g;
    g.player.haltForWarp();
    this.exitView?.setChevrons(false);
    const to = alongDoor(spot, DOORS.OUT_WALK_TILES * TILE);
    this.startWalk('out', spot, to, () => {
      this.inside = true;
      g.player.setAlpha(0);
      this.note('through', this.kind);
      this.onThrough?.();
    });
  }

  /**
   * 지도 고르기 취소 (계약 §10.2 cancelChoose): 문 안에서 문턱 안쪽으로 걸어 나온다. 문 안이 아니면 (UI 없이 곧장 고르기 등)
   * 그 자리에서 한 걸음 물러난다
   */
  stepBack(): void {
    const spot = this.exit;
    const g = this.g;
    if (!spot) return;
    this.inside = false;
    this.armed = false;
    const to = alongDoor(spot, -DOORS.STEP_BACK_TILES * TILE);
    // 문 안에 있지 않았으면 (고르기가 문 밖에서 열렸다) 지금 자리에서 문 반대쪽으로
    if (pastMouth(spot, g.player.x, g.player.y) < -TILE) {
      g.player.setAlpha(1);
      this.exitView?.setChevrons(true);
      return;
    }
    this.startWalk('back', spot, to, () => {
      g.player.setAlpha(1);
      this.exitView?.setChevrons(true);
    });
  }

  /** 걷는 동안 게임 입력 대신 (문 쪽으로 걷기 — 공격·대쉬 등은 비움). 문 안이면 가만히 */
  drive(input: InputState): InputState {
    const w = this.walk;
    if (!w && !this.inside) return input;
    const n = neutralInput(input);
    if (!w) return n;
    const g = this.g;
    const dx = w.to.x - g.player.x;
    const dy = w.to.y - g.player.y;
    const len = Math.hypot(dx, dy) || 1;
    // 거의 닿으면 가로지르는 방향은 버리고 문 방향만 (끝에서 흔들리지 않게)
    return { ...n, moveX: dx / len, moveY: dy / len, aimX: w.to.x, aimY: w.to.y };
  }

  private startWalk(phase: WalkPhase, spot: DoorSpot, to: DoorPoint, done: () => void): void {
    const g = this.g;
    const dx = to.x - g.player.x;
    const dy = to.y - g.player.y;
    const len = Math.hypot(dx, dy) || 1;
    const ms = (len / Math.max(1, g.player.speedPx)) * 1000;
    this.walk = {
      phase,
      spot,
      to,
      dir: { x: dx / len, y: dy / len },
      until: g.time.now + Math.min(DOORS.WALK_TIMEOUT_MS, ms * 1.6 + 200),
      done,
    };
    this.setBodyCollision(false);
    EventBus.emit(Events.DOOR_WALK, { phase, side: spot.side, ms: Math.round(ms) } satisfies DoorWalkPayload);
    this.note(`walk:${phase}`, { to, ms: Math.round(ms) });
  }

  private finishWalk(): void {
    const w = this.walk;
    if (!w) return;
    this.walk = null;
    const g = this.g;
    g.player.body.setVelocity(0, 0);
    // 문 안에서 기다릴 때만 충돌을 끈 채로 (바닥으로 돌아오면 켠다)
    if (w.phase !== 'out') this.setBodyCollision(true);
    w.done();
  }

  /** 문 쪽으로 갈수록 흐려진다 (바닥 끝 선에서 FADE_TILES 에 다 사라짐) */
  private fade(spot: DoorSpot): void {
    const g = this.g;
    const past = pastMouth(spot, g.player.x, g.player.y);
    g.player.setAlpha(Math.max(0, Math.min(1, 1 - past / (DOORS.FADE_TILES * TILE))));
  }

  private setBodyCollision(on: boolean): void {
    const c = this.g.player.body.checkCollision;
    c.up = on;
    c.down = on;
    c.left = on;
    c.right = on;
  }

  // --- 계약 · 디버그 ---

  /** 출구 문 가운데 (월드) */
  exitPoint(): DoorPoint | null {
    return this.exit ? { ...this.exit.mouth } : null;
  }

  get phase(): UiDoorPhase {
    if (this.walk) return this.walk.phase === 'out' ? 'walkOut' : 'walkIn';
    if (this.inside) return 'inside';
    return this.exitView?.isOpen ? 'open' : 'closed';
  }

  toUi(): UiDoor | null {
    const spot = this.exit;
    if (!spot) return null;
    const p = worldToLogicalScreen(this.g.cameras.main, spot.mouth.x, spot.mouth.y);
    return {
      side: spot.side,
      phase: this.phase,
      kind: this.kind,
      screen: { x: Math.round(p.x), y: Math.round(p.y) },
    };
  }

  /** 디버그: 문턱 가운데 (월드 — 헤드리스가 주인공을 옮길 자리) */
  sillPoint(): DoorPoint | null {
    return this.exit ? { ...this.exit.sill } : null;
  }

  debug(): Record<string, unknown> {
    return {
      exit: this.exit
        ? { side: this.exit.side, mouth: this.exit.mouth, sill: this.exit.sill, threshold: this.exit.threshold }
        : null,
      entry: this.entry ? { side: this.entry.side, mouth: this.entry.mouth } : null,
      phase: this.phase,
      kind: this.kind,
      open: this.exitOpen,
      armed: this.armed,
      inside: this.inside,
      walk: this.walk ? { phase: this.walk.phase, to: this.walk.to } : null,
      light: this.exitView?.lightOn ?? false,
      alpha: +this.g.player.alpha.toFixed(2),
      log: [...this.log],
    };
  }

  destroy(): void {
    this.exitView?.destroy();
    this.entryView?.destroy();
    this.exitView = null;
    this.entryView = null;
    this.walk = null;
  }
}
