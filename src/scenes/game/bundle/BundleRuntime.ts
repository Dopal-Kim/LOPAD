/**
 * 60라운드 2차 묶음 씬 층 (57 Q38 확정안 — 1층 범위, 데이터 data/bundle2.json · 런 상태 gameState.bundle · 층 노드 정보 systems/bundle2):
 * 소품(BundleProps) · 엘리트(EliteSystem) · 소모품(Consumables) · 상점 진열(ShopMenu) · 전투 노드 흐름(NodeFlow) ·
 * 이벤트·숨은 노드·단서·지도 장수(EventNode) · 보스 파훼(BossBreaks). Game.create 에서 구조물 다음에 만들고 cleanup 에서 정리한다.
 */
import { EventBus, Events } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUNDLE2 } from '../../../data/bundle2';
import type { UiConsumableSlot, UiElite, UiInteractable, UiNodeTrial } from '../../../contract/ui';
import type { Enemy } from '../../../objects/Enemy';
import type { Mob } from '../../../objects/Mob';
import type { InputState } from '../../../systems/InputSystem';
import type { Room } from '../../../systems/mapgen';
import type { WaveMods } from '../../../systems/RoomDirector';
import type { Game } from '../../Game';
import { BossBreaks } from './BossBreaks';
import { BundleProps } from './BundleProps';
import { Consumables } from './Consumables';
import { EliteSystem } from './EliteSystem';
import { EventNode } from './EventNode';
import { NodeFlow } from './NodeFlow';
import { ShopMenu } from './ShopMenu';
import { randomConsumable } from './bundleRewards';
import { StoryBeats } from '../story/StoryBeats';

type Sub = [event: string, fn: (p: never) => void];

export class BundleRuntime {
  readonly props: BundleProps;
  readonly elites: EliteSystem;
  readonly consumables: Consumables;
  readonly shop: ShopMenu;
  readonly flow: NodeFlow;
  readonly events: EventNode;
  readonly breaks: BossBreaks;
  /** 61라운드 P8 서사 연결 (서사 소품·무기 한마디·일기장) — 보스 담당은 `story.setClueSpot` */
  readonly story: StoryBeats;
  private readonly subs: Sub[];

  constructor(private readonly g: Game) {
    this.props = new BundleProps(g);
    this.elites = new EliteSystem(g);
    this.consumables = new Consumables(g);
    this.shop = new ShopMenu(g);
    this.flow = new NodeFlow(g, this.props, this.elites);
    this.events = new EventNode(g, this.props, this.flow, this.shop);
    this.breaks = new BossBreaks(g);
    this.story = new StoryBeats(g, this.props);
    this.subs = [
      [Events.TRIAL_STARTED, () => this.flow.onTrialStarted(g.time.now)],
      [Events.PLAYER_DAMAGED, () => this.flow.onPlayerDamaged()],
      [
        Events.TRIAL_CLEARED,
        () => {
          this.flow.onTrialCleared(g.time.now);
          this.events.onTrialCleared();
        },
      ],
    ];
    for (const [e, fn] of this.subs) EventBus.on(e, fn, this);
  }

  /** 노드 진입 (RouteFlow.enterNode 뒤 — 진입 잠금 끝 시각) */
  onEnter(enterLockUntil: number): void {
    this.flow.onEnter(enterLockUntil);
    this.events.onEnter(enterLockUntil);
    this.story.onEnter();
  }

  /** 메뉴·연출·전환 중 */
  private busy(): boolean {
    const g = this.g;
    return (
      g.frozen ||
      g.transitioning ||
      g.menu.isOpen ||
      gameState.rewardPending ||
      gameState.gameOver ||
      gameState.cleared ||
      Boolean(gameState.route?.choosing)
    );
  }

  /** 매 프레임 (입력 잠금 반영된 input) */
  update(input: InputState, now: number): void {
    this.consumables.update(input.consumablePressed, now);
    this.props.update(input.interactPressed, this.busy());
  }

  /** 개체 갱신 뒤 (엘리트 외곽선·문장·접두어 규칙) */
  lateUpdate(now: number): void {
    this.elites.lateUpdate(now);
  }

  // --- 방 상태 머신 훅 (RoomDirectorHost) ---

  holdTrial(_room: Room): boolean {
    return this.flow.holdTrial(this.g.time.now);
  }

  extraWaves(): number {
    return this.flow.extraWaves();
  }

  waveMods(index: number, total: number): WaveMods {
    return this.flow.waveMods(index, total);
  }

  onWaveSpawned(room: Room, index: number, _total: number, enemies: Enemy[]): void {
    this.flow.onWaveSpawned(room, index, enemies);
  }

  // --- 처치 ---

  /** 처치 보상 배율 (엘리트 개성·전표 ×rewardMult) */
  rewardMult(mob: Mob): number {
    return mob.elite ? BUNDLE2.elite.rewardMult : 1;
  }

  /** Progression.onKill (방 상태 머신에 알리기 전): 엘리트 독주·소모품 드롭 · 접두어 사망 규칙 · 보스 결정타 */
  onKill(mob: Mob): void {
    if (mob.isBoss) this.breaks.onBossKilled(mob);
    if (mob.elite) {
      const E = BUNDLE2.elite;
      if (this.g.rng.chance(E.potionChance)) {
        if (this.g.rng.chance(E.consumableShare)) this.consumables.spawnDrop(mob.x, mob.y, randomConsumable(this.g));
        else this.g.economy.spawnPickup(mob.x + 10, mob.y, 'potion', 1);
      }
    }
    this.elites.onKill(mob);
  }

  // --- UI 스냅샷 ---

  /** 상호작용 안내: 소품(성소 깃발)이 가까우면 그것 */
  interactable(): UiInteractable | null {
    return this.props.interactable(this.g.layout?.rooms[0]?.id ?? '');
  }

  consumableUi(): UiConsumableSlot {
    return this.consumables.toUi();
  }

  elitesUi(): UiElite[] {
    return this.elites.toUi();
  }

  nodeTrialUi(): UiNodeTrial | null {
    return this.flow.toUi(this.g.time.now);
  }

  debug(): Record<string, unknown> {
    const now = this.g.time.now;
    return {
      floor: gameState.bundle.floor,
      state: gameState.bundle.toSave(),
      flow: this.flow.debug(),
      event: this.events.debug(),
      breaks: this.breaks.debug(),
      elites: this.elites.debug(),
      consumables: this.consumables.debug(now),
      story: this.story.debug(),
    };
  }

  destroy(): void {
    for (const [e, fn] of this.subs) EventBus.off(e, fn, this);
    this.events.destroy();
    this.story.destroy();
    this.breaks.destroy();
    this.elites.destroy();
    this.consumables.destroy();
    this.props.destroy();
  }
}
