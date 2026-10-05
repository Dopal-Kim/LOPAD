import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, uiCommands, type UiSnapshot } from '../contract/ui';
import { BossHud } from './BossHud';
import type { CombatHud } from './CombatHud';
import { withDebug } from './debug';
import { R61_EVENTS } from './eventsR61';
import { StoryHud } from './StoryHud';
import { LAYOUT } from './theme';

export interface HudNarrativeDeps {
  /** 글꼴 준비 · 탄생 연출 아님 */
  canRun: () => boolean;
  /** 메뉴 씬이 떠 있다 */
  menuOpen: () => boolean;
  combat: () => CombatHud | undefined;
  stageIndex: () => number;
  /** 튜토리얼 노드의 공지를 단계 카드가 가져갔으면 true (53라운드) */
  takeTutorialNotice: (text: string) => boolean;
}

type On = <T>(event: string, handler: (p: T) => void) => void;

/**
 * 61라운드 단계 2·3 HUD 서사·보스 층 — HudScene 이 커지지 않게(6-1) STORY 자막 차례(`StoryHud`)와 보스 UI(`BossHud`)의
 * 이벤트 배선·자리 계산을 한 곳에 둔다. HudScene 은 만들고(`build`) 매 STATE 에 `render`, Esc·Enter 에 `noteOpen`·`closeNote`.
 */
export class HudNarrative {
  readonly story: StoryHud;
  private boss?: BossHud;
  /** BOSS_BREAK 결정타를 이번 보스전에 보았다 (처치 카드 문구) */
  private finisherSeen = false;

  constructor(
    private scene: Phaser.Scene,
    private deps: HudNarrativeDeps,
  ) {
    // 자막 차례는 글꼴 전·탄생 연출 중 쌓아 두었다가 그 뒤에 (예전: 탄생 중 마지막 한 줄만)
    this.story = new StoryHud(scene, {
      canRun: deps.canRun,
      menuOpen: deps.menuOpen,
      centerBottom: () => this.centerBottom(),
      voiceAnchor: () => ({
        x: deps.combat()?.weaponRowLeft ?? LAYOUT.edge,
        bottom: deps.combat()?.bundleTop ?? UI_SCREEN.HEIGHT,
      }),
      weaponName: () => withDebug(uiCommands.getUiSnapshot()).weapon?.name ?? '',
      stageIndex: deps.stageIndex,
      onShown: (channel, ms) => {
        if (channel === 'speech' || channel === 'voice') this.boss?.storyShown(ms);
      },
    });
  }

  /** 이벤트 구독 (HudScene 의 on — 정리도 HudScene 이 한다) */
  subscribe(on: On): void {
    const snap = (): UiSnapshot => withDebug(uiCommands.getUiSnapshot());
    on(UI_EVENTS.STORY, (p: unknown) => this.onStory(p));
    on(UI_EVENTS.BOSS_STARTED, (p: unknown) => {
      this.finisherSeen = false;
      this.boss?.started(p, snap());
    });
    on(UI_EVENTS.BOSS_PHASE, (p: unknown) => this.boss?.phase(p, snap()));
    on(R61_EVENTS.BOSS_BREAK, (p: unknown) => {
      if ((p as { kind?: unknown } | null)?.kind === 'finisher') this.finisherSeen = true;
      this.boss?.broke(p);
    });
    on(UI_EVENTS.BOSS_DIED, (p: unknown) => this.boss?.died(p, snap(), this.finisherSeen));
    on(R61_EVENTS.ENEMY_INTRO, (p: unknown) => this.story.enemyIntro(p));
    // 조사 쪽지는 메뉴·런 끝·층 전환에 덮는다, 보스 카드는 런 끝·층 전환에 치운다
    for (const e of [UI_EVENTS.MENU_OPEN, UI_EVENTS.RUN_ENDED, UI_EVENTS.STAGE_STARTED])
      on(e, () => this.story.closeNote());
    for (const e of [UI_EVENTS.RUN_ENDED, UI_EVENTS.STAGE_STARTED]) on(e, () => this.boss?.reset());
  }

  /** HUD build: 보스 막대·카드 */
  build(stageIndex: number): void {
    this.boss = new BossHud(this.scene, stageIndex);
  }

  setStageIndex(si: number): void {
    this.boss?.setStageIndex(si);
  }

  /** 매 STATE: 보스 막대(국면 눈금·무너짐)·촛대 안내, 자막 차례 (막혀 있던 줄을 풀고, 전투가 시작되면 쪽지를 덮는다) */
  render(s: UiSnapshot, now: number, overlay: boolean): void {
    this.boss?.render(s, now, this.deps.combat()?.bundleRight ?? 0, overlay);
    this.story.tick(Boolean(s.inCombat));
  }

  /**
   * 가운데 아래 글(자막·완벽 성공 문구)의 아래 끝: 전투 묶음 위, 보스 막대가 있으면 그 이름 줄 위.
   * BOSS_STARTED·STAGE_STARTED 와 같은 프레임에 오는 자막(STATE 보다 먼저)은 스냅샷으로 보스전을 보고 막대 자리만큼 미리 비킨다.
   */
  centerBottom(): number {
    const base = this.deps.combat()?.centerBottom() ?? UI_SCREEN.HEIGHT - 12;
    if (this.boss?.on) return Math.min(base, this.boss.top);
    const s = uiCommands.getUiSnapshot();
    const bossSoon = Boolean(s.boss && s.boss.hp > 0);
    return bossSoon ? Math.min(base, UI_SCREEN.HEIGHT - 12 - BossHud.reserveH) : base;
  }

  destroy(): void {
    this.boss?.destroy();
    this.boss = undefined;
    this.story.destroy();
  }

  /** STORY: 튜토리얼 노드의 공지는 위쪽 가운데 단계 카드로(53라운드), 그 밖은 자막 차례 */
  private onStory(p: unknown): void {
    const l = p as { kind?: unknown; text?: unknown } | null;
    if (l && l.kind === 'notice' && typeof l.text === 'string' && this.deps.takeTutorialNotice(l.text)) return;
    this.story.push(p);
  }
}
