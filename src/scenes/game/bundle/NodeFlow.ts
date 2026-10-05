/**
 * 60라운드 2차 묶음 — 전투 노드 흐름 (data/bundle2.json): 노드 클리어 보상(a) · 위험 노드(b: 저주 길 진입 2택 / 엘리트 길 웨이브마다 1) ·
 * 도전 성소(f: 첫 웨이브 전 preTrialMs 동안 E 로 깃발 → 엘리트 1 + 마지막 웨이브 +1 → 전표 +25 · 보상 한 번 더) ·
 * 성과 등급(f: 완 = 무피격 + 제한 시간 / 양 = 하나 — 잔 전투·위험 노드) · 이벤트 예약(E3 다음 전투 끝 전표 · 웨이브 +1).
 * 씬마다 새로 (현재 노드 하나).
 */
import { BUNDLE_FX, TILE } from '../../../core/Constants';
import { EventBus, Events, type ChallengeEventPayload, type NodeGradedPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUNDLE2, byStage } from '../../../data/bundle2';
import {
  UI_EVENTS,
  __system,
  type UiChallengeCleared,
  type UiChallengeStarted,
  type UiNodeGraded,
  type UiNodeTrial,
} from '../../../contract/ui';
import type { Enemy } from '../../../objects/Enemy';
import { laneStartCol, type NodeExtra } from '../../../systems/bundle2/routeExtras';
import { gradeOf, gradeReward } from '../../../systems/bundle2/shopStock';
import { SHRINE_SHEET } from '../../../systems/bundle2/bundleSheets';
import type { Room } from '../../../systems/mapgen';
import type { WaveMods } from '../../../systems/RoomDirector';
import type { Game } from '../../Game';
import type { BundleProps } from './BundleProps';
import type { EliteSystem } from './EliteSystem';
import { chain, rewardSteps, type Step } from './bundleRewards';

const SHRINE_ID = 'bundle:shrine';
/** 깃발 올림 → 펄럭임 (raise 5프레임 ≈ 0.5초) */
const RAISE_MS = 520;

export class NodeFlow {
  private readonly ex: NodeExtra | null;
  /** 잔 구간 전투·위험 노드 (성과 등급 대상) */
  private readonly graded: boolean;
  private trialStart = -1;
  private hits = 0;
  private trialDone = false;
  /** 저주 길: 진입 저주를 고를 때까지 시련을 미룬다 */
  private cursePending = false;
  /** 성소: 깃발을 세웠나 · 시련 시작을 기다리는 끝 시각 */
  private raised = false;
  private shrineUntil = 0;
  /** 이번 노드에서 쓴 E3 웨이브 +1 */
  private readonly extraWave: number;

  constructor(
    private readonly g: Game,
    private readonly props: BundleProps,
    private readonly elites: EliteSystem,
  ) {
    const node = g.node;
    const floor = gameState.bundle.floor;
    const route = gameState.route;
    this.ex = node && floor ? (floor.nodes[node.id] ?? null) : null;
    this.graded = Boolean(
      node && route && (node.kind === 'battle' || this.ex?.risk) && node.col >= laneStartCol(route.graph),
    );
    const trial = node?.kind === 'battle' || node?.kind === 'road';
    // E3 '앙갚음': 다음 전투 노드 웨이브 +1 (이 노드에서 쓴다)
    this.extraWave = trial ? gameState.bundle.extraWave : 0;
    if (this.extraWave > 0) gameState.bundle.extraWave = 0;
  }

  get extra(): NodeExtra | null {
    return this.ex;
  }

  /** 노드 진입 직후 (RouteFlow.enterNode 뒤): 저주 길 2택 · 성소 깃발 */
  onEnter(enterLockUntil: number): void {
    const ex = this.ex;
    if (!ex) return;
    if (ex.risk === 'curse' && !gameState.build.curse) {
      this.cursePending = true;
      this.g.time.delayedCall(Math.max(0, enterLockUntil - this.g.time.now) + BUNDLE_FX.MENU_AFTER_ENTER_MS, () => {
        if (!this.g.scene.isActive()) return;
        this.g.buildMenus.openCurseMenu(undefined, () => (this.cursePending = false), 'riskNode');
      });
    }
    if (ex.shrine) this.placeShrine(enterLockUntil);
  }

  private placeShrine(enterLockUntil: number): void {
    const c = this.center();
    const S = BUNDLE2.shrine;
    this.shrineUntil = enterLockUntil + S.preTrialMs;
    this.props.add({
      id: SHRINE_ID,
      sheet: SHRINE_SHEET,
      label: S.name,
      x: c.x + BUNDLE_FX.SHRINE_OFFSET.x * TILE,
      y: c.y + BUNDLE_FX.SHRINE_OFFSET.y * TILE,
      state: 'idle',
      interact: {
        kind: 'warFlag',
        name: S.name,
        action: BUNDLE_FX.SHRINE_ACTION,
        actionKey: 'raise',
        usable: () => !this.raised && this.trialStart < 0,
        use: () => this.raise(),
      },
    });
  }

  /** 전투장 가운데 (월드 px) */
  center(): { x: number; y: number } {
    const a = this.g.layout?.arena;
    const c = a?.center ?? a?.spawn ?? { x: 0, y: 0 };
    return { x: (c.x + 0.5) * TILE, y: (c.y + 0.5) * TILE };
  }

  private raise(): void {
    if (this.raised) return;
    this.raised = true;
    this.props.setState(SHRINE_ID, 'raise');
    this.g.time.delayedCall(RAISE_MS, () => this.props.setState(SHRINE_ID, 'active'));
    this.g.ui.story('notice', BUNDLE_FX.SHRINE_RAISED_TEXT);
    const room = this.g.layout?.rooms[0];
    EventBus.emit(Events.CHALLENGE_STARTED, { id: SHRINE_ID, kind: 'warFlag' } satisfies ChallengeEventPayload);
    __system.emit(UI_EVENTS.CHALLENGE_STARTED, {
      id: SHRINE_ID,
      kind: 'warFlag',
      roomId: room?.id ?? '',
      label: BUNDLE2.shrine.name,
      goal: BUNDLE_FX.SHRINE_GOAL,
      timeLimitMs: null,
    } satisfies UiChallengeStarted);
  }

  // --- 방 상태 머신 훅 ---

  /** 시련 시작을 미루나 (저주 고르는 중 · 성소 깃발 대기) */
  holdTrial(now: number): boolean {
    if (this.cursePending) return true;
    return Boolean(this.ex?.shrine) && !this.raised && now < this.shrineUntil;
  }

  extraWaves(): number {
    return this.extraWave;
  }

  /** 성소: 마지막 웨이브 +1 */
  waveMods(index: number, total: number): WaveMods {
    const extra = this.raised && index === total - 1 ? BUNDLE2.shrine.lastWaveExtra : 0;
    return { hpMult: 1, countMult: 1, extra };
  }

  /** 엘리트 길: 웨이브마다 1 (미리 굴린 접두어) · 성소: 첫 웨이브에 엘리트 1 추가 */
  onWaveSpawned(_room: Room, index: number, enemies: Enemy[]): void {
    const ex = this.ex;
    if (!ex) return;
    if (ex.risk === 'elite') {
      for (let i = 0; i < BUNDLE2.risk.elitePerWave; i++) {
        const cands = enemies.filter((e) => e.active && !e.elite);
        const m = cands[Math.floor(this.g.rng.next() * cands.length)];
        if (m) this.elites.makeElite(m, ex.prefixes[index] ?? null);
      }
    }
    if (ex.shrine && this.raised && index === 0) {
      for (let i = 0; i < BUNDLE2.shrine.eliteExtra; i++) {
        const base = enemies[Math.floor(this.g.rng.next() * enemies.length)];
        if (!base) break;
        const e = this.g.director.spawnExtra(base.spriteId, base.x, base.y);
        if (e) this.elites.makeElite(e, ex.prefixes[i] ?? null);
      }
    }
  }

  // --- 이벤트 ---

  onTrialStarted(now: number): void {
    this.trialStart = now;
    this.hits = 0;
  }

  onPlayerDamaged(): void {
    if (this.trialStart >= 0 && !this.trialDone) this.hits += 1;
  }

  /** 시련 클리어: 등급 → E3 예약 전표 → 노드 보상(위험 ×2) → 성소 덤 */
  onTrialCleared(now: number): void {
    if (this.trialDone || !this.g.routeMode) return;
    this.trialDone = true;
    const ex = this.ex;
    const steps: Step[] = [];
    if (this.graded && this.trialStart >= 0) this.grade(now);
    const B = gameState.bundle;
    if (B.laterGold > 0) {
      this.g.economy.addGold(B.laterGold);
      B.laterGold = 0;
    }
    if (ex) {
      const mult = ex.risk ? BUNDLE2.risk.rewardMult : 1;
      if (ex.risk === 'curse') steps.push((next) => this.curseReward(next));
      else if (ex.reward) {
        const rarities = ex.risk === 'elite' ? BUNDLE2.risk.eliteRewardRarities : undefined;
        steps.push(...rewardSteps(this.g, ex.reward, mult, { rarities }));
      }
      if (ex.shrine && this.raised) {
        this.g.economy.addGold(BUNDLE2.shrine.gold);
        this.props.setState(SHRINE_ID, 'cleared');
        const outcome = this.hits === 0 ? 'flawless' : 'clear';
        EventBus.emit(Events.CHALLENGE_CLEARED, {
          id: SHRINE_ID,
          kind: 'warFlag',
          outcome,
        } satisfies ChallengeEventPayload);
        __system.emit(UI_EVENTS.CHALLENGE_CLEARED, {
          id: SHRINE_ID,
          kind: 'warFlag',
          roomId: this.g.layout?.rooms[0]?.id ?? '',
          outcome,
          text: BUNDLE2.shrine.name,
        } satisfies UiChallengeCleared);
        if (ex.reward) steps.push(...rewardSteps(this.g, ex.reward, 1));
      }
    }
    chain(steps);
  }

  /** 저주 길 보상: 영웅 이상 패시브 3택 또는 전표 100 (고르기) */
  private curseReward(next: () => void): void {
    const g = this.g;
    const C = BUNDLE2.risk.curse;
    const goldLabel = `전표 ${C.gold}`;
    g.menu.open(
      'event',
      String(BUNDLE2.rewards.names.curse ?? ''),
      [
        { key: '1', label: `영웅 이상 패시브 ${C.passiveChoices}택`, enabled: true },
        { key: '2', label: goldLabel, enabled: true },
      ],
      (key) => {
        if (key === '1') {
          g.menu.close();
          g.buildMenus.openPassiveMenu('node', { choices: C.passiveChoices, rarities: C.passiveRarities }, next);
        } else if (key === '2') {
          g.menu.close();
          g.economy.addGold(C.gold);
          next();
        }
      },
    );
  }

  private grade(now: number): void {
    const G = BUNDLE2.grade;
    const limit = byStage(G.timeLimitMs, gameState.stageId);
    const elapsed = now - this.trialStart;
    const grade = gradeOf(this.hits, elapsed, limit, G.hitAllowance);
    const r = gradeReward(grade, Boolean(this.ex?.risk));
    if (r.gold > 0) this.g.economy.addGold(r.gold);
    if (r.personality > 0) this.g.progress.gainPersonality(r.personality);
    if (this.ex) this.ex.grade = grade;
    const text = G.text[grade ?? 'none'];
    EventBus.emit(Events.NODE_GRADED, { grade } satisfies NodeGradedPayload);
    __system.emit(UI_EVENTS.NODE_GRADED, {
      nodeId: this.g.node?.id ?? '',
      grade,
      noHit: this.hits <= G.hitAllowance,
      inTime: elapsed <= limit,
      deltas: { ...(r.gold > 0 ? { gold: r.gold } : {}), ...(r.personality > 0 ? { personality: r.personality } : {}) },
      text: typeof text === 'string' ? text : '',
    } satisfies UiNodeGraded);
  }

  /** 계약 §14.10 진행 (등급 노드의 시련 중에만) */
  toUi(now: number): UiNodeTrial | null {
    if (!this.graded || this.trialStart < 0 || this.trialDone) return null;
    return {
      timeLimitMs: byStage(BUNDLE2.grade.timeLimitMs, gameState.stageId),
      elapsedMs: Math.round(now - this.trialStart),
      hitTaken: this.hits > BUNDLE2.grade.hitAllowance,
    };
  }

  debug(): Record<string, unknown> {
    return {
      extra: this.ex,
      graded: this.graded,
      hits: this.hits,
      trialStart: this.trialStart,
      raised: this.raised,
      cursePending: this.cursePending,
      extraWave: this.extraWave,
    };
  }
}
