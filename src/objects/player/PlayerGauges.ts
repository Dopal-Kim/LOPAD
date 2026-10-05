/**
 * 56라운드 Q13~Q20 무기 고유 자원 (칼 검기 · 대검 울분 · 활 숨) — 무기가 바뀌면 새로 시작한다. 단검 낙인은 적마다라 씬(BrandMarks).
 * 변화는 WEAPON_GAUGE 로 알린다(음향·월드 연출·디버그). HUD 는 계약 §13 `UiSnapshot.gauge`(`toUi`, 단검 낙인은 BrandMarks.toUi).
 * 61라운드 SY-2: 활 숨은 저격 갈래에서만(`gauge.branch`) · 칼 검기는 좌 홀드 발도만 소모 · 2단 명경이면 검기 규칙 전환(상한 5단 등).
 */
import { FEEDBACK } from '../../core/Constants';
import { EventBus, Events, type WeaponGaugePayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { ComboFollowUpDef } from '../../data/types';
import type { UiWeaponGauge } from '../../contract/ui';
import {
  BreathGauge,
  GrudgeGauge,
  KenkiGauge,
  makeGauge,
  type GuardBlockMode,
  type WeaponGauge,
} from '../../systems/weapon/weaponGauge';

export class PlayerGauges {
  private current: WeaponGauge | null = null;
  private currentWeapon = '';
  /** 디버그: 마지막 이벤트 */
  lastEvent: WeaponGaugePayload | null = null;
  /** 숨 집중 중이었는가 (끝 알림 경계) */
  private focusOn = false;

  /** 현재 무기의 고유 자원 (없으면 null). 갈래 조건(`gauge.branch`)·명경 규칙이 바뀌면 다시 맞춘다 */
  get gauge(): WeaponGauge | null {
    const w = gameState.weapon;
    const def = w.def.gauge;
    const open = !(def?.kind === 'breath' && def.branch !== undefined && !w.path.includes(def.branch));
    const mk = this.meikyoParams();
    const key = `${w.id}|${open ? 1 : 0}|${mk ? 'meikyo' : ''}`;
    if (this.currentWeapon !== key) {
      const sameWeapon = this.currentWeapon.split('|')[0] === w.id;
      const prev = this.current;
      this.currentWeapon = key;
      this.current = open ? makeGauge(def) : null;
      if (this.current instanceof KenkiGauge) {
        this.current.setRule(mk ? { stages: mk.stages, parryGainStages: mk.parryGainStages, hitGain: false } : null);
        // 같은 무기에서 규칙만 바뀌면 쌓인 검기를 잇는다
        if (sameWeapon && prev instanceof KenkiGauge) this.current.value = Math.min(prev.value, this.current.max);
      }
    }
    return this.current;
  }

  /** 2단 명경 규칙 값 (경로에 없으면 null) */
  private meikyoParams(): {
    stages: number;
    parryGainStages: number;
    clones: number;
    delayMs: number;
    mult: number;
  } | null {
    const r = gameState.weapon.nodes.find((n) => n.rule?.kind === 'meikyo')?.rule;
    if (!r) return null;
    const n = (k: string, d: number) => (typeof r.params?.[k] === 'number' ? (r.params[k] as number) : d);
    return {
      stages: n('stages', 5),
      parryGainStages: n('parryGainStages', 2),
      clones: n('clones', 0),
      delayMs: n('cloneDelayMs', 150),
      mult: n('cloneMult', 0.5),
    };
  }

  /** 명경: 상한까지 모은 발도에 붙는 분신 잔상 베기 (아니면 빈 배열) */
  meikyoClones(stages: number): ComboFollowUpDef[] {
    const mk = this.meikyoParams();
    if (!mk || stages < mk.stages) return [];
    return Array.from({ length: mk.clones }, (_, i) => ({
      id: 'echo',
      delayMs: mk.delayMs * (i + 1),
      damageMult: mk.mult,
    }));
  }

  get kenki(): KenkiGauge | null {
    const g = this.gauge;
    return g instanceof KenkiGauge ? g : null;
  }

  get grudge(): GrudgeGauge | null {
    const g = this.gauge;
    return g instanceof GrudgeGauge ? g : null;
  }

  get breath(): BreathGauge | null {
    const g = this.gauge;
    return g instanceof BreathGauge ? g : null;
  }

  /** 근접 적중 1회 (한 휘두름에 한 번) — 검기 */
  onStrikeHit(): void {
    const k = this.kenki;
    const st = k?.gainHit();
    if (k && st !== null && st !== undefined) this.emit({ gauge: 'kenki', event: 'stage', stage: st });
  }

  /** 패링 성공 — 검기 1단 즉시 */
  onParried(): void {
    const k = this.kenki;
    const st = k?.gainParry();
    if (k && st !== null && st !== undefined) this.emit({ gauge: 'kenki', event: 'stage', stage: st });
  }

  /** 발도: 검기 전부 소모 (칼이 아니면 단 0) */
  consumeKenki(): { stages: number; damageMult: number; crit: boolean } {
    const k = this.kenki;
    if (!k) return { stages: 0, damageMult: 1, crit: false };
    const c = k.consume();
    if (c.stages > 0) this.emit({ gauge: 'kenki', event: 'consume', stage: c.stages });
    return c;
  }

  /** 가드로 막음 — 울분 */
  onGuardBlock(blocked: number, mode: GuardBlockMode): void {
    const g = this.grudge;
    if (g?.addBlocked(blocked, mode)) this.emit({ gauge: 'grudge', event: 'full' });
  }

  /** 차지 내려찍기·꽂아내리기: 울분 전부 소모 */
  consumeGrudge(): { ratio: number; damageMult: number; rangeMult: number } {
    const g = this.grudge;
    if (!g) return { ratio: 0, damageMult: 1, rangeMult: 1 };
    const c = g.consume();
    if (c.ratio > 0) this.emit({ gauge: 'grudge', event: 'consume' });
    return c;
  }

  /** 완벽 놓기 — 숨 */
  onPerfectRelease(): void {
    const b = this.breath;
    if (b?.addPerfect()) this.emit({ gauge: 'breath', event: 'full' });
  }

  /** 가득 당긴 순간: 숨이 가득이면 집중 시작 */
  tryFocus(time: number): boolean {
    const b = this.breath;
    if (!b?.startFocus(time)) return false;
    this.emit({ gauge: 'breath', event: 'focusStart' });
    return true;
  }

  focusing(time: number): boolean {
    return Boolean(this.breath?.focusing(time));
  }

  /** 놓기·취소·시간 끝 → 집중 끝 */
  endFocus(time: number): void {
    if (this.breath?.endFocus(time)) this.emit({ gauge: 'breath', event: 'focusEnd' });
  }

  /** 매 프레임: 집중 시간이 다 되면 끝 알림 */
  tick(time: number): void {
    const b = this.breath;
    if (b && b.focusLeftMs(time) === 0 && this.focusOn) this.endFocus(time);
    this.focusOn = Boolean(b?.focusing(time));
  }

  /**
   * 무기 위 자원 오버레이 (아트 `weapons/v3/<무기 동작>_ki1~3`·`_grudge1~3`, 같은 프레임 번호로 무기 위에): 검기 단 · 울분 단계
   * (비율 → 1~3, 0 이면 null). 시트가 없으면 WeaponOverlay 가 칼날 곱 틴트(bladeTint)로 대신
   */
  get overlay(): { suffix: string; level: number } | null {
    const k = this.kenki;
    if (k) return k.stage > 0 ? { suffix: 'ki', level: k.stage } : null;
    const g = this.grudge;
    if (g && g.ratio > 0) return { suffix: 'grudge', level: PlayerGauges.grudgeStage(g.ratio) };
    return null;
  }

  /** 칼날 빛 (검기 단 → 재·호박·백열 곱 틴트, 0 이면 null) — 오버레이 시트가 없을 때 임시 */
  get bladeTint(): number | null {
    const st = this.kenki?.stage ?? 0;
    return st > 0 ? (FEEDBACK.KENKI_TINT[Math.min(st, FEEDBACK.KENKI_TINT.length) - 1] ?? null) : null;
  }

  /** 울분 단계 0~3 (계약 §13: 구간 1~33 / 34~66 / 67~100%) */
  static grudgeStage(ratio: number): number {
    return ratio > 0 ? Math.min(3, Math.max(1, Math.ceil(ratio * 3 - 1e-9))) : 0;
  }

  /** 계약 §13 `UiSnapshot.gauge` — 칼 검기 · 대검 울분 · 활 숨 (단검 낙인은 BrandMarks.toUi) */
  toUi(time: number): UiWeaponGauge | null {
    const g = this.gauge;
    const label = gameState.weapon.def.gauge?.label ?? '';
    if (g instanceof KenkiGauge) return { kind: 'kenki', label, value: round1(g.value), max: g.max, stage: g.stage };
    if (g instanceof GrudgeGauge)
      return { kind: 'grudge', label, value: round1(g.value), max: g.max, stage: PlayerGauges.grudgeStage(g.ratio) };
    if (g instanceof BreathGauge)
      return { kind: 'breath', label, value: round1(g.value), max: g.max, focusing: g.focusing(time) };
    return null;
  }

  debug(time: number): Record<string, unknown> | null {
    const g = this.gauge;
    if (!g) return null;
    const base = { kind: gameState.weapon.def.gauge?.kind, value: g.value, max: g.max, last: this.lastEvent };
    if (g instanceof KenkiGauge) return { ...base, stage: g.stage };
    if (g instanceof GrudgeGauge) return { ...base, ratio: g.ratio, full: g.full };
    return { ...base, full: g.full, focusing: g.focusing(time), focusLeftMs: g.focusLeftMs(time) };
  }

  private emit(p: Omit<WeaponGaugePayload, 'weapon'>): void {
    const payload: WeaponGaugePayload = { weapon: gameState.weapon.id, ...p };
    this.lastEvent = payload;
    EventBus.emit(Events.WEAPON_GAUGE, payload);
  }
}

function round1(v: number): number {
  return Math.round(v * 10) / 10;
}
