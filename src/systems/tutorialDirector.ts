/**
 * 49라운드 3: 탄생 전장 조작 안내 — 자기 완결 연결부. 단계 머신(tutorial.ts)에 EventBus 의 주인공 행동을 넣고,
 * 결과를 호스트 콜백(안내 문구·약한 적 전투·표식 강조·허수아비 흔들림·완료)으로 내보낸다.
 * 안내 문구는 계약 내 기존 경로(STORY notice)로 — 호스트가 `notice(text)` 를 `story('notice', text)` 로 잇는다.
 * shutdown 에서 `destroy()` 필수 (EventBus 구독 해제).
 */
import { TILE } from '../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type PlayerSecondaryPayload } from '../core/EventBus';
import { TutorialMachine, type TutorialDef, type TutorialEvent, type TutorialFightDef, type Pt } from './tutorial';

export interface TutorialHost {
  /** 안내 문구 (STORY notice) */
  notice(text: string): void;
  /**
   * 약한 적 전투 시작 (RoomDirector.startChallenge). at = 중심 px. 지금 못 하면 false → 다음 update 에 다시 시도.
   * 전멸하면 onDone 을 불러야 한다
   */
  startFight(spawns: TutorialFightDef['spawns'], at: Pt & { radiusTiles: number }, onDone: () => void): boolean;
  /** 지금 표식 강조 (null = 끔) */
  highlightSign?(index: number | null): void;
  /** 허수아비 흔들림 */
  pokeDummy?(index: number): void;
  /** 53라운드: 단계 안내 (UI_EVENTS.TUTORIAL_STEP) — 안내 문구가 뜰 때 */
  step?(info: { index: number; total: number; text: string; keys: string[] }): void;
  /** 모든 단계 끝 (출구 열기 허용) */
  onDone?(): void;
}

export interface TutorialLayout {
  /** 전장 중앙 (타일) */
  center: Pt;
  /** 표식·허수아비 (타일 좌표, setpiece.ts 결과) */
  signs: readonly Pt[];
  dummies: readonly Pt[];
}

export interface TutorialOptions {
  /** 원거리 무기 (활) — 조준 원뿔로 허수아비 맞힘 판정 */
  ranged: boolean;
  /** 문구 치환 ({name}·{description} = 보조 동작) */
  vars?: Record<string, string>;
}

const tileCenter = (p: Pt): Pt => ({ x: (p.x + 0.5) * TILE, y: (p.y + 0.5) * TILE });

export class TutorialDirector {
  readonly machine: TutorialMachine;
  private player: Pt = { x: 0, y: 0 };
  private pendingFight: TutorialFightDef | null = null;
  private destroyed = false;
  /** 단계별 안내 키 (TUTORIAL_STEP) */
  private readonly stepKeys: string[][];

  private readonly onAttack = (p: PlayerAttackPayload) => {
    if (!this.machine.started) return;
    this.apply(this.machine.attack(p, this.player, this.opts.ranged));
  };
  private readonly onDash = () => this.act('dash');
  private readonly onSecondary = (p: PlayerSecondaryPayload) => {
    if (p.phase === 'start' || p.phase === 'ready' || p.phase === 'block') this.act('secondary');
  };
  private readonly onSecondaryAny = () => this.act('secondary');

  constructor(
    def: TutorialDef,
    private readonly layout: TutorialLayout,
    private readonly host: TutorialHost,
    private readonly opts: TutorialOptions,
  ) {
    this.stepKeys = def.steps.map((s) => s.keys ?? []);
    this.machine = new TutorialMachine(
      def,
      layout.signs.map(tileCenter),
      layout.dummies.map(tileCenter),
      TILE,
      opts.vars ?? {},
    );
    EventBus.on(Events.PLAYER_ATTACKED, this.onAttack, this);
    EventBus.on(Events.PLAYER_DASHED, this.onDash, this);
    EventBus.on(Events.PLAYER_SECONDARY, this.onSecondary, this);
    EventBus.on(Events.PLAYER_SHADOW_STEP, this.onSecondaryAny, this);
    EventBus.on(Events.PLAYER_PARRIED, this.onSecondaryAny, this);
    EventBus.on(Events.PLAYER_PARRY_FAILED, this.onSecondaryAny, this);
    EventBus.on(Events.PLAYER_GUARD_RELEASED, this.onSecondaryAny, this);
  }

  get done(): boolean {
    return this.machine.done;
  }

  /** 매 프레임 (탄생 연출 중에는 부르지 않는다). 처음 부를 때 첫 단계를 켠다 */
  update(playerX: number, playerY: number): void {
    if (this.destroyed) return;
    this.player = { x: playerX, y: playerY };
    if (!this.machine.started) this.apply(this.machine.start());
    if (this.pendingFight) this.tryFight(this.pendingFight);
    this.apply(this.machine.update(this.player));
  }

  /** 디버그: 안내 전부 건너뛰기 */
  skip(): void {
    this.pendingFight = null;
    this.apply(this.machine.skip());
  }

  private act(kind: 'dash' | 'secondary'): void {
    if (!this.machine.started) return;
    this.apply(this.machine.action(kind));
  }

  private tryFight(f: TutorialFightDef): void {
    const c = this.layout.center;
    const at = { ...tileCenter({ x: c.x + f.at[0], y: c.y + f.at[1] }), radiusTiles: f.radiusTiles };
    const ok = this.host.startFight(f.spawns, at, () => {
      if (!this.destroyed) this.apply(this.machine.fightCleared());
    });
    this.pendingFight = ok ? null : f;
  }

  private apply(events: TutorialEvent[]): void {
    for (const e of events) {
      switch (e.type) {
        case 'step':
          this.host.highlightSign?.(e.sign);
          break;
        case 'prompt':
          this.host.notice(e.text);
          this.host.step?.({
            index: e.step,
            total: this.stepKeys.length,
            text: e.text,
            keys: [...(this.stepKeys[e.step] ?? [])],
          });
          break;
        case 'fight':
          this.tryFight(e.fight);
          break;
        case 'dummyHit':
          this.host.pokeDummy?.(e.index);
          break;
        case 'done':
          this.host.highlightSign?.(null);
          this.host.notice(e.text);
          this.host.onDone?.();
          break;
      }
    }
  }

  destroy(): void {
    this.destroyed = true;
    EventBus.off(Events.PLAYER_ATTACKED, this.onAttack, this);
    EventBus.off(Events.PLAYER_DASHED, this.onDash, this);
    EventBus.off(Events.PLAYER_SECONDARY, this.onSecondary, this);
    EventBus.off(Events.PLAYER_SHADOW_STEP, this.onSecondaryAny, this);
    EventBus.off(Events.PLAYER_PARRIED, this.onSecondaryAny, this);
    EventBus.off(Events.PLAYER_PARRY_FAILED, this.onSecondaryAny, this);
    EventBus.off(Events.PLAYER_GUARD_RELEASED, this.onSecondaryAny, this);
  }
}
