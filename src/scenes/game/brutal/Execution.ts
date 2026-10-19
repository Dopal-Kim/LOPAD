/**
 * P21 처형 (계약 dark-brutal §4): 버팀이 깨졌거나(stagger) HP ≤ 15% 인 적이 주인공 앞 부채꼴 1.2칸 안에 있으면 공격 키가 처형으로 바뀐다
 * (따로 키 없음 · 군주 제외 · 엘리트는 HP ≤ 15% 일 때만). 처형 = 0.45초 무적 · 결정타 프레임에 슬로 0.3배 120ms · 줌 펀치 · 무기별 마무리(사망 변형) ·
 * 처치 각성 게이지 ×2. 동작 그림 = `hero_execute_<무기>`(주인공 동작 `<무기>_execute` + 무기 오버레이 `execute`, json timingMs), 없으면 그 무기의 마지막 연격 시트.
 * 이벤트: ENEMY_EXECUTABLE(대상이 바뀔 때 on/off) · PLAYER_EXECUTE(시작 — 결정타는 impactMs 뒤, 그때 일반 처치 이벤트).
 */
import { BRUTAL, TILE } from '../../../core/Constants';
import {
  EventBus,
  Events,
  type EnemyExecutablePayload,
  type GoreWeapon,
  type PlayerExecutePayload,
} from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { neutralInput, type InputState } from '../../../systems/InputSystem';
import type { Mob } from '../../../objects/Mob';
import { execDistance, isGoreWeapon } from '../../../systems/gore/rules';
import { mobUid } from '../../../systems/offscreen';
import { COMBO_HITS, comboAction } from '../../../systems/sprites/spriteActions';
import { facing8Of } from '../../../systems/sprites/spriteDefs';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { executeAction } from './brutalArt';
import type { GoreSheet } from './goreArt';
import type { Game } from '../../Game';

export class Execution {
  /** 지금 처형 가능한 적 (표식) */
  target: Mob | null = null;
  /** 처형 중 (이 시각까지 입력을 막는다) */
  private busyUntil = 0;
  /** 이 시각부터 이동·대쉬로 회복을 끊을 수 있다 (결정타 + RECOVER_CANCEL_MS) */
  private cancelFrom = 0;
  /** 디버그·봇: 회복을 끊은 횟수 */
  cancels = 0;
  /** 디버그·봇 */
  count = 0;
  lastAction: string | null = null;

  constructor(private readonly g: Game) {}

  get active(): boolean {
    return this.g.time.now < this.busyUntil;
  }

  /** Player.update 전에: 처형 중이면 입력을 비우고, 공격 키 + 대상이 있으면 그 공격을 처형으로 바꾼다 */
  filterInput(input: InputState, time: number): InputState {
    if (time < this.busyUntil) {
      // 결정타 뒤 회복은 이동·대쉬로 끊을 수 있다 (P19 캔슬 기둥 — 무적 0.45초는 그대로). 그 전까지는 입력을 막는다
      const moving = input.moveX !== 0 || input.moveY !== 0 || input.dashPressed;
      if (!(moving && time >= this.cancelFrom)) return neutralInput(input);
      this.busyUntil = time;
      if (this.g.player.action === 'skill') this.g.player.setAction('normal', 0);
      this.g.player.visual.endOneShot();
      this.cancels += 1;
      return input;
    }
    const t = this.target;
    if (!input.attackPressed || !t?.active || this.g.player.action !== 'normal') return input;
    const w = gameState.weapon.id;
    if (!isGoreWeapon(w)) return input;
    this.start(t, w, time);
    return neutralInput(input);
  }

  /** 매 프레임 (적 update 뒤): 처형 대상 고르기 · 표식 이벤트 */
  update(time: number): void {
    const next = time < this.busyUntil ? this.target : this.pick(time);
    if (next === this.target) return;
    if (this.target) this.emit(this.target, false);
    this.target = next;
    if (next) this.emit(next, true);
  }

  /** 계약 `UiSnapshot.executable` (처형 가능한 적 전부 — 발밑 월드 좌표). 처형 중이면 [] */
  toUi(): { uid: number; x: number; y: number }[] {
    return this.active ? [] : this.eligible.map((m) => ({ uid: mobUid(m), x: m.x, y: m.y }));
  }

  /** 지난 update 의 처형 가능한 적 (가까운 순 아님) */
  private eligible: Mob[] = [];

  private pick(time: number): Mob | null {
    const g = this.g;
    const p = g.player;
    if (!p?.active || p.action !== 'normal' || gameState.gameOver) {
      this.eligible = [];
      return null;
    }
    const c = p.body.center;
    this.eligible = [];
    let best: Mob | null = null;
    let bestD = Infinity;
    for (const child of g.mobs.getChildren()) {
      const m = child as Mob;
      if (!m.active || !m.body || m.isImmune(time)) continue;
      const mc = m.body.center;
      const d = execDistance(
        {
          boss: m.isBoss,
          elite: m.elite !== null,
          hp: m.hp,
          maxHp: m.maxHp,
          broken: time < m.poiseBrokenUntil,
          dx: mc.x - c.x,
          dy: mc.y - c.y,
          radius: Math.min(m.body.halfWidth, m.body.halfHeight),
        },
        p.aimAngle,
        TILE,
      );
      if (d !== null) this.eligible.push(m);
      if (d !== null && d < bestD) {
        bestD = d;
        best = m;
      }
    }
    return best;
  }

  private emit(m: Mob, on: boolean): void {
    const p: EnemyExecutablePayload = { id: m.spriteId, uid: mobUid(m), x: m.x, y: m.y, on };
    EventBus.emit(Events.ENEMY_EXECUTABLE, p);
  }

  /** 처형 동작 그림: 처형 시트 → 마지막 연격 시트 → 공격 */
  private bodyAction(w: GoreWeapon): string {
    if (spriteLibrary.has('player', executeAction(w))) return executeAction(w);
    for (let n = COMBO_HITS; n >= 1; n--) if (spriteLibrary.has('player', comboAction(w, n))) return comboAction(w, n);
    return 'attack';
  }

  private start(t: Mob, w: GoreWeapon, time: number): void {
    const g = this.g;
    const p = g.player;
    const E = BRUTAL.EXEC;
    const action = this.bodyAction(w);
    // art §37 처형 시트: timingMs{hitAt,total} (칼 90 · 대검 180 · 단검 155 · 활 130 / 450). 연격 시트로 대신하면 1차 값
    const timing = (spriteLibrary.sheet('player', action) as GoreSheet | undefined)?.timingMs;
    const ms = timing?.total ?? E.MS;
    const impactMs = Math.round(timing?.hitAt ?? ms * E.IMPACT_AT);
    this.busyUntil = time + ms;
    this.cancelFrom = time + impactMs + BRUTAL.EXEC.RECOVER_CANCEL_MS;
    this.count += 1;
    this.lastAction = action;
    const dx = t.x - p.x;
    const dy = t.y - p.y;
    const len = Math.hypot(dx, dy) || 1;
    p.setAction('skill', time + ms);
    p.body.setVelocity(0, 0);
    p.grantInvulnerable(time + E.INVULN_MS);
    p.visual.oneShot(action, facing8Of(dx, dy, p.visual.facing), time, ms);
    // 대상은 처형이 끝날 때까지 굳는다
    t.stagger(ms + 200);
    t.body.setVelocity(0, 0);
    const payload: PlayerExecutePayload = { target: t.spriteId, x: t.x, y: t.y, weapon: w, ms, impactMs };
    EventBus.emit(Events.PLAYER_EXECUTE, payload);
    g.time.delayedCall(impactMs, () => this.impact(t, dx / len, dy / len));
    if (this.target) this.emit(this.target, false);
    this.target = null;
  }

  /** 결정타: 남은 HP + 넘친 피해 (사망 변형 = 무기별 처형) · 각성 게이지 ×2 */
  private impact(t: Mob, nx: number, ny: number): void {
    const g = this.g;
    if (!t.active || !g.scene.isActive()) return;
    // 결정타 프레임: 슬로 0.3배 120ms · 줌 펀치 (art §37 execute.slowmo.atMs = 타격 시각)
    g.combatFeel.slowmo(BRUTAL.EXEC.SLOW.SCALE, BRUTAL.EXEC.SLOW.MS);
    g.cam.punch(BRUTAL.EXEC.PUNCH.AMOUNT, BRUTAL.EXEC.PUNCH.MS);
    const dmg = Math.max(1, t.hp) + Math.round(t.maxHp * BRUTAL.EXEC.OVERKILL_RATIO);
    const died = g.combat.hitMob(t, dmg, {
      crit: false,
      dirX: nx,
      dirY: ny,
      heavy: true,
      knock: false,
      ignoreGuard: true,
      execute: true,
      from: { x: g.player.x, y: g.player.y },
    });
    if (died) g.progress.onKill(t, 'attack', BRUTAL.EXEC.GROWTH_MULT);
  }
}
