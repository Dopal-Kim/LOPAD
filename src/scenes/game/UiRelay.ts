/**
 * UI 계약 연결 (계약 ui-system-interface): 스냅샷 · 스토리 자막 · 내부 이벤트 → UI 이벤트 중계 ·
 * 워프 요청 거부(48라운드 §10.2: 워프 비활성 — 늘 거부, 사유만 알린다).
 */
import { gameState } from '../../core/GameState';
import { BOSSES, STORY } from '../../data';
import { UI_EVENTS, __system, type StoryKind, type UiWarpState } from '../../contract/ui';
import { buildSnapshot } from '../../contract/snapshot';
import { audio } from '../../systems/audio';
import { floorText } from '../../systems/story';
import type { WarpDenyReason } from '../../systems/traversal';
import type { Game } from '../Game';

export class UiRelay {
  bossName: string | null = null;

  constructor(private readonly g: Game) {}

  /** 스토리 자막 (계약 STORY 이벤트) */
  story(kind: StoryKind, text: string): void {
    if (text) __system.emit(UI_EVENTS.STORY, { kind, text });
  }

  snapshot() {
    const g = this.g;
    const now = g.time.now;
    return buildSnapshot({
      layout: g.layout ?? null,
      visited: g.visitedRooms,
      cleared: g.clearedRooms,
      bossName: this.bossName,
      paused: false,
      menu: g.menu.menu,
      inCombat: g.director.inCombat,
      sprinting: g.player.sprinting,
      warp: this.warpState(),
      interactable: g.structures?.interactable() ?? null,
      statuses: g.structures?.statuses() ?? [],
      structureRooms: g.structures?.structureRooms(),
      route: gameState.route?.toUi() ?? null,
      // 49라운드 (계약 §11): 무기 자원 · 음소거 · 시험장
      resource: g.player?.resource?.toUi(now) ?? null,
      muted: audio.isMuted,
      lab: g.lab,
    });
  }

  /** 매 프레임 UI 상태 */
  emitState(): void {
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

  relayGold(p: unknown): void {
    __system.emit(UI_EVENTS.GOLD_CHANGED, p);
  }

  relayEvolved(p: { name: string }): void {
    __system.emit(UI_EVENTS.WEAPON_EVOLVED, { name: p.name });
  }

  relayBossStarted(p: { boss: string }): void {
    this.bossName = BOSSES[p.boss]?.name ?? '보스';
    this.story('boss', floorText(gameState.stageId)?.bossIntro ?? '');
    __system.emit(UI_EVENTS.BOSS_STARTED, {
      name: this.bossName,
      hp: gameState.bossHp,
      maxHp: gameState.bossMaxHp,
      phase: gameState.bossPhase,
    });
  }

  relayBossPhase(p: { phase: number; hp: number; maxHp: number }): void {
    this.g.screenFx.bossPhase();
    __system.emit(UI_EVENTS.BOSS_PHASE, { name: this.bossName ?? '보스', ...p });
  }

  relayBossDied(): void {
    __system.emit(UI_EVENTS.BOSS_DIED, {
      name: this.bossName ?? '보스',
      hp: 0,
      maxHp: gameState.bossMaxHp,
      phase: gameState.bossPhase,
    });
  }
}
