/**
 * 61라운드 P9 런 로그 기록기: EventBus 사건 → `RunLog`(순수). 게임 수명 동안 하나(main.ts 가 attach).
 * - 시작 `RUN_STARTED`(새 런·이어하기, 시험장은 없음) · 노드 `NODE_ENTERED` · 끝 `RUN_ENDED`(사망·클리어).
 * - 런 도중 타이틀로 나가거나 새 런·시험장으로 가면 host 가 `abandon()` → 결과 'abandon' 으로 저장.
 * - 끝난 요약은 메타 세이브 `runLogs` 에 최근 `RUNLOG.KEEP_RUNS` 개.
 * - 디버그 `__lopad.runlog.dump()` = { current(진행 중), last(마지막 끝난 런), saved(메타 목록), byKind(노드 종류별 평균) }.
 */
import {
  EventBus,
  Events,
  type BossAttackPayload,
  type CurseGainedPayload,
  type EnemyAttackPayload,
  type EnemyDiedPayload,
  type MenuEventPayload,
  type NodeEnteredPayload,
  type PlayerDamagedPayload,
  type RunEndedPayload,
  type RunStartedPayload,
  type TraitGainedPayload,
  type WeaponAwakenPayload,
  type WeaponTemperedPayload,
} from '../../core/EventBus';
import { UI_EVENTS, uiBus } from '../../contract/ui';
import { metaStore } from '../meta';
import type { MetaRW } from '../settings';
import { RunLog, aggregateByKind, appendRunLog, type RunLogSummary } from './runLog';

export interface RunLogDebug {
  current: RunLogSummary | null;
  last: RunLogSummary | null;
  saved: RunLogSummary[];
  byKind: ReturnType<typeof aggregateByKind>;
}

type Clock = { getTime(): number };

export class RunLogRecorder {
  private log: RunLog | null = null;
  /** 61 단계 6: 수련장에 간 동안 맡겨 둔 기록 */
  private held: RunLog | null = null;
  private last: RunLogSummary | null = null;
  private clock: Clock | null = null;
  private readonly pauseReasons = new Set<string>();
  private meta: MetaRW = metaStore;
  private readonly subs: { event: string; fn: (p: never) => void; bus: 'game' | 'ui' }[] = [];

  attach(clock: Clock, meta: MetaRW = metaStore): void {
    if (this.clock) return;
    this.clock = clock;
    this.meta = meta;
    const on = <P>(event: string, fn: (p: P) => void, bus: 'game' | 'ui' = 'game') => {
      this.subs.push({ event, fn: fn as (p: never) => void, bus });
      (bus === 'game' ? EventBus : uiBus).on(event, fn);
    };
    on<RunStartedPayload>(Events.RUN_STARTED, (p) => this.begin(p));
    on<NodeEnteredPayload>(Events.NODE_ENTERED, (p) => this.log?.enterNode(p, this.now()));
    on<{ stageIndex: number }>(Events.STAGE_STARTED, (p) => this.log?.stage(p.stageIndex));
    on(Events.EXIT_OPENED, () => this.log?.cleared(this.now()));
    on<EnemyDiedPayload>(Events.ENEMY_DIED, (p) => this.log?.kill(p.id, Boolean(p.elite)));
    on<{ id: string }>(Events.BOSS_DIED, (p) => this.log?.kill(p.id, false));
    on<EnemyAttackPayload>(Events.ENEMY_ATTACK, (p) => this.log?.threat(`enemy:${p.id}:${p.kind}`, this.now()));
    on<BossAttackPayload>(Events.BOSS_ATTACK, (p) => this.log?.threat(`boss:${p.id}:${p.attack}`, this.now()));
    on<PlayerDamagedPayload>(Events.PLAYER_DAMAGED, (p) => this.log?.hit(p.amount, p.hp, p.maxHp));
    on(Events.PLAYER_DIED, () => this.log?.died(this.now()));
    on<MenuEventPayload>(Events.MENU_OPENED, (p) => this.log?.menu(p.id, Boolean(p.reopen)));
    // 61 G 무기 성장: 1차·2차 각성 (갈래·길 id) · 개성 · 단련
    on<WeaponAwakenPayload>(Events.WEAPON_AWAKEN, (p) =>
      this.log?.choice(
        p.stage === 1 ? 'awaken1' : 'awaken2',
        p.stage === 1 ? p.branch : (p.path ?? ''),
        p.name,
        this.now(),
      ),
    );
    on<WeaponTemperedPayload>(Events.WEAPON_TEMPERED, (p) =>
      this.log?.choice('temper', p.weapon, p.temper, this.now()),
    );
    on<TraitGainedPayload>(Events.TRAIT_GAINED, (p) => this.log?.choice('trait', p.id, p.verb, this.now()));
    on<{ id: string; level: number }>(Events.PASSIVE_GAINED, (p) =>
      this.log?.choice('passive', p.id, p.level, this.now()),
    );
    on<CurseGainedPayload>(Events.CURSE_GAINED, (p) => this.log?.choice('curse', p.id, p.source, this.now()));
    on<{ id: string }>(Events.STAT_REWARD, (p) => this.log?.choice('stat', p.id, undefined, this.now()));
    on<RunEndedPayload>(Events.RUN_ENDED, (p) => this.finish(p.cleared ? 'clear' : 'death'));
    on(UI_EVENTS.PAUSED, () => this.setPaused('menu', true), 'ui');
    on(UI_EVENTS.RESUMED, () => this.setPaused('menu', false), 'ui');
  }

  detach(): void {
    for (const s of this.subs) (s.bus === 'game' ? EventBus : uiBus).off(s.event, s.fn);
    this.subs.length = 0;
    this.clock = null;
    this.log = null;
  }

  /** 일시정지 이유(메뉴 · 안내 패널 멈춤)별로 — 하나라도 있으면 플레이 시간에서 뺀다 */
  setPaused(reason: string, on: boolean): void {
    const before = this.pauseReasons.size > 0;
    if (on) this.pauseReasons.add(reason);
    else this.pauseReasons.delete(reason);
    const after = this.pauseReasons.size > 0;
    if (!before && after) this.log?.pause(this.now());
    else if (before && !after) this.log?.resume(this.now());
  }

  /**
   * 61 단계 6 수련장: 런을 맡겨 둔 동안 기록을 멈춘다 (수련장 처치·피격이 런 로그에 들어가지 않게 — 플레이 시간도 뺀다).
   * off = 맡긴 런으로 돌아옴
   */
  hold(on: boolean): void {
    if (on) {
      if (this.held || !this.log || this.log.isEnded) return;
      this.setPaused('training', true);
      this.held = this.log;
      this.log = null;
    } else if (this.held) {
      this.log = this.held;
      this.held = null;
      this.setPaused('training', false);
    }
  }

  /** 진행 중인 런을 '그만둠'으로 닫는다 (타이틀·새 런·시험장). 노드를 하나라도 밟았으면 저장 */
  abandon(): void {
    if (!this.log || this.log.isEnded) return;
    this.finish('abandon');
  }

  dump(): RunLogDebug {
    const saved = this.meta.read().runLogs ?? [];
    return {
      current: this.log && !this.log.isEnded ? this.log.peek(this.now()) : null,
      last: this.last,
      saved,
      byKind: aggregateByKind(saved),
    };
  }

  /** 디버그: 메타의 런 로그 비우기 */
  clearSaved(): void {
    const m = this.meta.read();
    this.meta.write({ ...m, runLogs: [] });
  }

  private begin(p: RunStartedPayload): void {
    this.abandon();
    this.log = new RunLog({ ...p, startedAt: Date.now() }, this.now());
    if (this.pauseReasons.size > 0) this.log.pause(this.now());
  }

  private finish(result: RunLogSummary['result']): void {
    const log = this.log;
    if (!log || log.isEnded) return;
    const s = log.end(result, this.now());
    this.log = null;
    this.last = s;
    if (result === 'abandon' && s.totals.nodes === 0) return;
    const m = this.meta.read();
    this.meta.write({ ...m, runLogs: appendRunLog(m.runLogs, s) });
  }

  private now(): number {
    return this.clock?.getTime() ?? 0;
  }
}

export const runLogRecorder = new RunLogRecorder();
