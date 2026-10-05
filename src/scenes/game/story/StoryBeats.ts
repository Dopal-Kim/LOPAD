/**
 * 61라운드 P8 서사 연결 (씬 쪽 — 노드 씬마다 새로, BundleRuntime 이 만든다). 문장은 `data/story.json`(스토리 팩 사본), 배치·수치는
 * `data/narrative.json`, 런 상태는 `gameState.narrative`, 영구 이력은 메타 세이브 일기장(`systems/narrative/diary`).
 * - 서사 소품 3종 (계약 art §23, E 조사 → STORY kind 'clue' 줄들 · 소품 found · 일기장에 기록): 탄생지 가면 시체 · 국경 초소 출입 장부 ·
 *   보스방 외상 장부(보스를 쓰러뜨린 뒤 — 자리는 보스 담당이 `setClueSpot` 으로 줄 수 있다, 없으면 데이터 기본 자리).
 *   두 번째 생부터(일기장에 그 단서를 본 기록이 있으면) 마지막 줄 = repeatLast. 외상 장부는 '지난 생에 만취를 쓰러뜨린 기록'.
 * - 무기 한마디 (STORY kind 'voice', 런당 장면 1회): firstKill 첫 처치 · crisis 첫 HP 30% 이하(튜토리얼 중 제외) ·
 *   bossBefore 보스 등장(BOSS_INTRO) · bossKill 쓰러짐 대사 뒤(BOSS_FALLEN). pickup 은 시작 의식(Setup)이 운명 직후에.
 * - 보스 처치 → 일기장 보스 처치 수 (단서 repeat · E4 '지난 생의 기록').
 * 시험장에서는 아무것도 하지 않는다.
 */
import { BUNDLE_FX, TILE } from '../../../core/Constants';
import { EventBus, Events, type BossFallenPayload, type BossIntroPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { NARRATIVE, NARRATIVE_STORY, voiceLine, type NarrativePropDef, type VoiceScene } from '../../../data/narrative';
import {
  bossKilledBefore,
  clueLines,
  diaryNow,
  recordBossKill,
  recordClue,
  updateDiary,
} from '../../../systems/narrative/diary';
import type { Game } from '../../Game';
import type { BundleProps } from '../bundle/BundleProps';

type Sub = [event: string, fn: (p: never) => void];

const PROP_PREFIX = 'story:';

interface PlacedClue {
  def: NarrativePropDef;
  /** 이 씬에서 처음 펼칠 때 정한 '지난 생에 본 기록' (같은 씬 안에서 다시 읽어도 같은 줄) */
  repeat: boolean;
}

export class StoryBeats {
  private readonly subs: Sub[] = [];
  private readonly placed = new Map<string, PlacedClue>();
  /** 보스 담당이 준 단서 자리 (월드 px) */
  private readonly spots = new Map<string, { x: number; y: number }>();

  constructor(
    private readonly g: Game,
    private readonly props: BundleProps,
  ) {
    if (g.lab) return;
    this.subs = [
      [Events.ENEMY_DIED, () => this.voice('firstKill')],
      [Events.PLAYER_DAMAGED, () => this.onDamaged()],
      [Events.BOSS_INTRO, (p: BossIntroPayload) => this.voice('bossBefore', p.lineGapMs > 0 ? p.lineGapMs : undefined)],
      [Events.BOSS_FALLEN, (p: BossFallenPayload) => this.onBossFallen(p.rewardInMs)],
      [Events.BOSS_DIED, () => this.onBossDied()],
    ];
    for (const [e, fn] of this.subs) EventBus.on(e, fn, this);
  }

  /** 노드 진입 직후 (BundleRuntime.onEnter): 이 노드 종류의 서사 소품 (보스 처치 뒤 것은 빼고) */
  onEnter(): void {
    if (this.g.lab || !this.g.routeMode) return;
    for (const def of NARRATIVE.props)
      if (def.node === this.g.nodeKind && def.after !== 'bossDied') this.placeClue(def.clue);
  }

  /**
   * 보스 담당 API: 단서 자리(월드 px)를 정해 둔다 — 예 보스방 외상 장부는 기둥 뒤 구석. 보스를 쓰러뜨리면 그 자리에 놓인다.
   * 이미 놓였으면 그대로.
   */
  setClueSpot(clue: string, x: number, y: number): void {
    this.spots.set(clue, { x, y });
  }

  /** 단서 소품 놓기 (이미 있으면 false). 자리 = setClueSpot 이 준 곳, 없으면 데이터 기준점 + 칸 오프셋(걸을 수 있는 곳으로 당김) */
  placeClue(clue: string, at?: { x: number; y: number }): boolean {
    const def = NARRATIVE.props.find((p) => p.clue === clue);
    if (!def || this.placed.has(clue) || this.g.lab) return false;
    const p = at ?? this.spots.get(clue) ?? this.defaultSpot(def);
    if (!p) return false;
    const d = diaryNow();
    const stage = gameState.stageId;
    const repeat =
      def.after === 'bossDied'
        ? bossKilledBefore(d, stage, gameState.narrative.bossKilled.has(stage))
        : d.clues.includes(clue) && !gameState.narrative.cluesRead.has(clue);
    this.placed.set(clue, { def, repeat });
    const id = PROP_PREFIX + clue;
    this.props.add({
      id,
      sheet: def.sheet,
      label: def.name,
      x: p.x,
      y: p.y,
      state: 'idle',
      interact: {
        kind: 'clue',
        name: def.name,
        action: BUNDLE_FX.EVENT_ACTION,
        actionKey: 'clue.read',
        usable: () => true,
        use: () => void this.read(clue),
      },
    });
    return true;
  }

  /** E 조사: 줄들을 STORY 'clue' 로 · 소품 found · 일기장 기록. 놓인 단서가 아니면 false */
  read(clue: string): boolean {
    const placed = this.placed.get(clue);
    const text = NARRATIVE_STORY.clues[clue];
    if (!placed || !text) return false;
    const lines = clueLines(text, placed.repeat);
    this.g.ui.story('clue', lines.join('\n'), { lines });
    this.props.setState(PROP_PREFIX + clue, 'found');
    gameState.narrative.cluesRead.add(clue);
    updateDiary((d) => recordClue(d, clue));
    return true;
  }

  private defaultSpot(def: NarrativePropDef): { x: number; y: number } | null {
    const a = this.g.layout?.arena;
    const base = def.anchor === 'spawn' ? a?.spawn : (a?.center ?? a?.spawn);
    if (!base) return null;
    const tx = base.x + def.offset[0];
    const ty = base.y + def.offset[1];
    // 걸을 수 있는 칸으로 (바깥으로 한 칸씩 넓혀 가며)
    for (let r = 0; r <= BUNDLE_FX.STORY_SPOT_SEARCH_TILES; r++)
      for (let dy = -r; dy <= r; dy++)
        for (let dx = -r; dx <= r; dx++) {
          if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
          const x = (tx + dx + 0.5) * TILE;
          const y = (ty + dy + 0.5) * TILE;
          if (this.g.world.isWalkableAt(x, y)) return { x, y };
        }
    return { x: (tx + 0.5) * TILE, y: (ty + 0.5) * TILE };
  }

  // --- 무기 한마디 ---

  /** 런당 장면 1회 (STORY kind 'voice' — weapon 은 무기 빛 색) */
  voice(scene: VoiceScene, holdMs?: number): boolean {
    if (this.g.lab || gameState.gameOver) return false;
    const w = gameState.weapon.id;
    const text = voiceLine(w, scene);
    if (!text || !gameState.narrative.takeVoice(scene)) return false;
    this.g.ui.story('voice', text, { weapon: w, ...(holdMs !== undefined ? { holdMs } : {}) });
    return true;
  }

  private onDamaged(): void {
    const hp = gameState.hp;
    if (hp <= 0 || hp > gameState.maxHp * NARRATIVE.voice.crisisHpRatio) return;
    // 튜토리얼(탄생 노드 안내) 중에는 세지 않는다
    if (this.g.tutorial && !this.g.tutorial.done) return;
    this.voice('crisis', NARRATIVE.voice.crisisHoldMs);
  }

  /** 쓰러짐 대사 뒤 — 보상 메뉴(rewardInMs)보다 먼저 */
  private onBossFallen(rewardInMs: number): void {
    const ms = Math.min(NARRATIVE.voice.bossKillDelayMs, Math.max(0, rewardInMs));
    if (ms <= 0) this.voice('bossKill');
    else this.g.time.delayedCall(ms, () => this.g.scene.isActive() && this.voice('bossKill'));
  }

  /** 보스 사망: 일기장 처치 수 · 보스방 외상 장부 */
  private onBossDied(): void {
    if (this.g.nodeKind !== 'boss' && !gameState.bossUnlocked) return;
    const stage = gameState.stageId;
    if (!gameState.narrative.bossKilled.has(stage)) {
      gameState.narrative.bossKilled.add(stage);
      updateDiary((d) => recordBossKill(d, stage));
    }
    for (const def of NARRATIVE.props)
      if (def.after === 'bossDied' && def.node === this.g.nodeKind) this.placeClue(def.clue);
  }

  debug(): Record<string, unknown> {
    return {
      run: gameState.narrative.debug(),
      placed: [...this.placed.entries()].map(([k, v]) => ({ clue: k, repeat: v.repeat })),
      diary: diaryNow(),
      recent: [...this.g.ui.recentStory],
    };
  }

  destroy(): void {
    for (const [e, fn] of this.subs) EventBus.off(e, fn, this);
    this.subs.length = 0;
    this.placed.clear();
    this.spots.clear();
  }
}
