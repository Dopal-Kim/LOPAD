/**
 * UI 계약 연결 (계약 ui-system-interface): 스냅샷 · 스토리 자막 · 내부 이벤트 → UI 이벤트 중계 ·
 * 워프 요청 거부(48라운드 §10.2: 워프 비활성 — 늘 거부, 사유만 알린다).
 */
import { gameState } from '../../core/GameState';
import { BOSSES, STORY } from '../../data';
import {
  UI_EVENTS,
  __system,
  type StoryKind,
  type UiBossRoar,
  type UiEnemyIncoming,
  type UiStoryLine,
  type UiGroggy,
  type UiTutorialStep,
  type UiWarpState,
} from '../../contract/ui';
import type { BossActionPayload, BossBreakPayload, EnemyIncomingPayload } from '../../core/EventBus';
import { bossSnapshotExtra, uiBossBreak } from './bossUi';
import { buildSnapshot } from '../../contract/snapshot';
import { audio } from '../../systems/audio/audio';
import { settings } from '../../systems/settings';
import { floorText } from '../../systems/story';
import type { WarpDenyReason } from '../../systems/traversal';
import type { Game } from '../Game';

/** 디버그용으로 남기는 최근 자막 수 */
const UI_RELAY_STORY_KEEP = 24;

export class UiRelay {
  bossName: string | null = null;
  /** 61라운드: BOSS_DIED 는 그 프레임 끝(emitState)에 낸다 — 같은 프레임 뒤에 오는 결정타(BOSS_BREAK finisher)를 싣기 위해 */
  private bossDiedPending = false;
  /** 61 단계 4 §17.1: 이번 보스전에 포효(이름 카드)를 냈는가 */
  private roared = true;

  constructor(private readonly g: Game) {}

  /**
   * 스토리 자막 (계약 STORY 이벤트). 61라운드 P8: extra = speech 화자(speaker) · voice 무기(weapon) · clue 줄(lines) · 표시 시간(holdMs).
   * 보스 대사는 `speech(speaker, text)`, 무기 한마디·단서는 `scenes/game/story/StoryBeats`
   */
  story(kind: StoryKind, text: string, extra: Omit<UiStoryLine, 'kind' | 'text'> = {}): void {
    if (!text) return;
    const line: UiStoryLine = { kind, text, ...extra };
    __system.emit(UI_EVENTS.STORY, line);
    this.recentStory.push(line);
    if (this.recentStory.length > UI_RELAY_STORY_KEEP) this.recentStory.shift();
  }

  /** 디버그: 최근 자막 (`__lopad.bundle.story().recent`) */
  readonly recentStory: UiStoryLine[] = [];

  /** 61라운드 P8: 군주의 말 (계약 STORY kind 'speech') — 예 `speech(STORY_NARRATIVE.boss1.speaker, …intro)` */
  speech(speaker: string, text: string): void {
    this.story('speech', text, { speaker });
  }

  snapshot() {
    const g = this.g;
    const now = g.time.now;
    return buildSnapshot({
      layout: g.layout ?? null,
      visited: g.visitedRooms,
      cleared: g.clearedRooms,
      bossName: this.bossName,
      bossExtra: bossSnapshotExtra(g),
      paused: false,
      menu: g.menu.menu,
      inCombat: g.director.inCombat,
      sprinting: g.player.sprinting,
      warp: this.warpState(),
      interactable: g.structures?.interactable() ?? g.economy?.keeperInteractable() ?? g.bundle?.interactable() ?? null,
      statuses: g.build ? g.build.statuses(g.structures?.statuses() ?? []) : (g.structures?.statuses() ?? []),
      structureRooms: g.structures?.structureRooms(),
      route: gameState.route?.toUi() ?? null,
      // 49라운드 (계약 §11): 무기 자원 · 음소거 · 시험장
      resource: g.player?.resource?.toUi(now) ?? null,
      muted: audio.isMuted,
      lab: g.lab,
      // 61라운드: F 넣기/뽑기 삭제 — 칼 발도는 좌 홀드 (스냅샷 weaponVerbs)
      carry: null,
      // 56라운드 (계약 §13): 무기 고유 자원 · 그로기
      gauge: g.player?.gauges.toUi(now) ?? g.strikes?.brands.toUi() ?? null,
      groggy: this.groggy(now),
      // 57라운드 (계약 §14.1): 태그·세트 · 이중 개성 · 저주
      build: g.build?.toUi() ?? null,
      // 61 G 계약 §18: 무기 성장
      growth: g.growth?.toUi() ?? null,
      // 60라운드 (계약 §14.8~§14.10): 소모품 칸 · 엘리트 이름표 · 노드 성과 진행
      consumable: g.bundle?.consumableUi() ?? null,
      elites: g.bundle?.elitesUi() ?? [],
      nodeTrial: g.bundle?.nodeTrialUi() ?? null,
      // 61라운드 (계약 §15): 설정
      settings: settings.current(),
    });
  }

  /** 계약 §13: 그로기 규칙(기력 groggyMs)이 있는 무기(칼·대검)만, 그 밖은 null */
  private groggy(now: number): UiGroggy | null {
    const res = this.g.player?.resource;
    if (!res?.groggyRule) return null;
    return { active: res.isGroggy, leftMs: Math.round(res.groggyLeftMs(now)) };
  }

  /** 매 프레임 UI 상태 */
  emitState(): void {
    if (this.bossDiedPending) this.flushBossDied();
    __system.emit(UI_EVENTS.STATE, this.snapshot());
  }

  // --- 워프 (48라운드 비활성) ---

  /** 씬 상태로 본 공통 거부 사유: 연출·메뉴·전환은 busy, 활성 전투 방이 있으면 combat */
  private warpBlock(): 'combat' | 'busy' | null {
    const g = this.g;
    if (!g.director || gameState.gameOver || gameState.cleared || g.transitioning) return 'busy';
    if (g.director.inCombat) return 'combat';
    if (g.frozen || gameState.rewardPending || (g.menu.isOpen && !g.economy.shopOpen)) return 'busy';
    return null;
  }

  /** 계약 §10.2: targets 는 항상 [], ready=false (Tab 은 노드 지도 보기) */
  warpState(): UiWarpState {
    return { ready: false, blocked: this.warpBlock() ?? 'busy', targets: [], warping: false };
  }

  /** uiCommands.warpTo: 늘 거부 (사유 = 전투·연출, 그 밖에는 busy) */
  warpDeny(): WarpDenyReason {
    return this.warpBlock() ?? 'busy';
  }

  // --- 내부 이벤트 → UI 중계 ---

  onRoomEntered(p: { roomId: string; type: string }): void {
    const g = this.g;
    const firstVisit = !g.visitedRooms.has(p.roomId);
    g.visitedRooms.add(p.roomId);
    __system.emit(UI_EVENTS.ROOM_ENTERED, p);
    if (firstVisit && p.type === 'rest') this.story('rest', floorText(gameState.stageId)?.restNote ?? '');
    if (firstVisit && p.type === 'trial') this.story('notice', STORY.notices.trialStart);
  }

  relayHealed(p: unknown): void {
    __system.emit(UI_EVENTS.PLAYER_HEALED, p);
  }

  /** 53라운드 Q49: 적 소환 예고 (UI 경고는 튜토리얼에서만) */
  relayEnemyIncoming(p: EnemyIncomingPayload): void {
    __system.emit(UI_EVENTS.ENEMY_INCOMING, { ...p } satisfies UiEnemyIncoming);
  }

  /** 53라운드: 튜토리얼 단계 안내 */
  tutorialStep(info: UiTutorialStep): void {
    __system.emit(UI_EVENTS.TUTORIAL_STEP, info);
  }

  relayGold(p: unknown): void {
    __system.emit(UI_EVENTS.GOLD_CHANGED, p);
  }

  /** 보스 이름표·체력줄 (61라운드: 층 등장 자막은 BossFlow 가 등장 연출 시간표에 맞춰 낸다) */
  relayBossStarted(p: { boss: string }): void {
    this.bossName = BOSSES[p.boss]?.name ?? '보스';
    __system.emit(UI_EVENTS.BOSS_STARTED, {
      name: this.bossName,
      hp: gameState.bossHp,
      maxHp: gameState.bossMaxHp,
      phase: gameState.bossPhase,
      // 61라운드 §17: 등장 연출 길이 (BossFlow 가 같은 BOSS_STARTED 를 먼저 받아 정해 둔다)
      introMs: this.g.bossFlow?.introMs ?? 0,
    });
    // §17.1: 등장 연출이 없으면 이름 카드(포효)를 바로
    this.roared = false;
    if (!(this.g.bossFlow?.introMs ?? 0)) this.relayBossRoar();
  }

  /** §17.1: 등장 동작의 포효 프레임 (BOSS_ACTION introRoar) → 이름 카드 */
  relayBossAction(p: BossActionPayload): void {
    if (p.action === 'introRoar') this.relayBossRoar();
  }

  /** §17.1: 포효 그림이 없는 보스(등장 시트 없음)도 전투 시작까지는 이름 카드를 한 번 낸다 */
  relayBossFight(): void {
    this.relayBossRoar();
  }

  private relayBossRoar(): void {
    if (this.roared) return;
    this.roared = true;
    __system.emit(UI_EVENTS.BOSS_ROAR, { name: this.bossName ?? '보스' } satisfies UiBossRoar);
  }

  relayBossPhase(p: { phase: number; hp: number; maxHp: number }): void {
    this.g.screenFx.bossPhase();
    __system.emit(UI_EVENTS.BOSS_PHASE, { name: this.bossName ?? '보스', ...p });
  }

  relayBossDied(): void {
    this.bossDiedPending = true;
  }

  private flushBossDied(): void {
    this.bossDiedPending = false;
    __system.emit(UI_EVENTS.BOSS_DIED, {
      name: this.bossName ?? '보스',
      hp: 0,
      maxHp: gameState.bossMaxHp,
      phase: gameState.bossPhase,
      finisher: this.g.bossFlow?.finished ?? false,
    });
  }

  /** 61라운드 §17: 파훼·결정타 → UI (파훼는 매번, 결정타는 처치 때 1회) */
  relayBossBreak(p: BossBreakPayload): void {
    const b = uiBossBreak(p.kind);
    if (b) __system.emit(UI_EVENTS.BOSS_BREAK, b);
  }
}
