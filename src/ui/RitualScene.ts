import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands, type UiRitual } from '../contract/ui';
import { debugExpose } from './debug';
import { KIT, fontsReady, preloadKit, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { loadRitualArt } from './ritualArt';
import { RitualFatePage, RitualTrialPage, loadLook, uiLookKey } from './RitualFate';
import { RitualNamePage } from './RitualName';
import { RitualStrokesPage } from './RitualStrokes';
import { readRitual, ritualRebuild } from './ritualView';

/** 의식 한 장 (단계마다 하나) */
export interface RitualPage {
  /** 같은 단계 안에서 상태가 바뀜 (과제 체크·획 수·영혼 귀퉁이) */
  update(r: UiRitual): void;
  /** 장면 키 (처리했으면 true) */
  key?(e: KeyboardEvent): boolean;
  /** 다른 화면(영혼 강화 메뉴)이 떠 있다 */
  setBlocked?(b: boolean): void;
  tick?(now: number): void;
  /** RITUAL_STROKE_JUDGED */
  judged?(p: unknown): void;
  destroy(): void;
}

/**
 * 62 루프 1 P0-2 첫 생 의식 UI 씬 `UiRitual` (계약 §20 — UI 가 그리고 시스템 Setup 은 흐름·판정). Setup 이 이 씬을 Setup 위에
 * 띄우고(`UI_SCENES.RITUAL`) 끝나면 멈춘다. 상태는 `RITUAL` 이벤트(+ `getUiSnapshot().ritual`), 명령은 `uiCommands.ritual.*`.
 * 장: name·rewrite = 일기장 첫 장 이름 칸(RitualName) · strokes = 등 그림 위 먹 붓 세 획(RitualStrokes) ·
 * trial = 과제 목록만(RitualFate.RitualTrialPage, 무대는 시스템) · fate = 액자 속 무기와 '왜' 한 줄(RitualFatePage).
 * 일기장 종이 키트·Galmuri 만 쓴다(옛 고정폭 자리표시 글꼴·브라우저 입력칸 없음).
 */
export class RitualScene extends Phaser.Scene {
  private page?: RitualPage;
  private state: UiRitual | null = null;
  private built = false;
  private menuOnTop = false;
  private alive = false;
  private handlers: [string, (p: never) => void][] = [];

  constructor() {
    super(UI_SCENE_KEYS.RITUAL);
    // Setup 은 띄우기 전에 '렌더러 등록됨'을 본다 — 타이틀을 건너뛴 시작(?new)에도 UI 의식 씬을 쓰게 부팅 때 등록한다
    // (타이틀·HUD 가 create 에서 하는 것과 같은 선언)
    uiCommands.registerRenderer();
  }

  /**
   * 키트는 create 에서 (`kitReady`). 의식 씬은 메뉴 씬(첫 생 선택)과 같은 순간 뜨기도 해서, 둘이 한꺼번에 같은 키트를 읽으면
   * Phaser 가 'Texture key already in use' 를 낸다 — 다른 씬이 읽는 중이면 끝나기를 기다린다.
   */
  preload(): void {}

  create(): void {
    uiCommands.registerRenderer();
    this.alive = true;
    this.built = false;
    this.page = undefined;
    this.state = null;
    this.on(UI_EVENTS.RITUAL, (p: unknown) => this.apply(readRitual(p)));
    this.on(UI_EVENTS.RITUAL_STROKE_JUDGED, (p: unknown) => this.page?.judged?.(p));
    this.input.keyboard?.on('keydown', this.onKey);
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      this.alive = false;
      this.input.keyboard?.off('keydown', this.onKey);
      for (const [e, h] of this.handlers) uiBus.off(e, h);
      this.handlers = [];
      this.page?.destroy();
      this.page = undefined;
      this.state = null;
      debugExpose('ritual', null);
    });
    // 키트·글꼴·아트 그림(있으면)을 기다린 뒤 지금 상태로 그린다
    this.kitReady(() =>
      fontsReady().then(() => {
        if (!this.alive) return;
        setupKit(this);
        loadRitualArt(this, () => {
          if (!this.alive) return;
          this.built = true;
          this.apply(readRitual(uiCommands.getUiSnapshot().ritual), true);
        });
      }),
    );
  }

  update(time: number): void {
    if (!this.page) return;
    const menu = this.menuOpen();
    // 영혼 강화 메뉴(메뉴 씬)는 의식 장 위에 — Setup 이 의식 씬을 맨 위로 올려 두므로 메뉴가 뜨면 메뉴를 다시 위로
    if (menu && !this.menuOnTop) this.scene.bringToTop(UI_SCENE_KEYS.MENU);
    this.menuOnTop = menu;
    this.page.setBlocked?.(menu);
    this.page.tick?.(time);
  }

  /** 키트 텍스처가 있으면 바로, 다른 씬이 읽는 중이면 그 끝을 기다려 다시, 아무도 안 읽으면 이 씬이 읽는다 */
  private kitReady(done: () => void, tries = 0): void {
    if (!this.alive) return;
    // 이미 있거나, 이 씬이 읽고도 없으면(파일 실패) 있는 것으로 그린다 (무한 반복 방지)
    if ((this.textures.exists(KIT.panelPaper) && this.textures.exists(KIT.icons)) || tries >= 99) {
      done();
      return;
    }
    // (preload 중인 씬은 RUNNING 이 아니라 getScenes(true) 에 없다 — 전부 본다)
    const busy = this.scene.manager
      .getScenes(false)
      .find((sc) => sc !== this && sc.sys.settings.status > 0 && sc.load && sc.load.isLoading());
    if (busy && tries < 20) {
      busy.load.once(Phaser.Loader.Events.COMPLETE, () => this.kitReady(done, tries + 1));
      return;
    }
    preloadKit(this);
    this.load.once(Phaser.Loader.Events.COMPLETE, () => this.kitReady(done, 99));
    if (!this.load.isLoading()) this.load.start();
  }

  /** 새 상태: 단계가 바뀌었으면 장을 새로, 아니면 부분 갱신 */
  private apply(r: UiRitual | null, force = false): void {
    if (!this.built) return;
    const prev = this.state;
    this.state = r;
    if (force || ritualRebuild(prev, r)) {
      this.page?.destroy();
      this.page = this.makePage(r);
    } else if (r) this.page?.update(r);
    debugExpose('ritual', r ? { phase: r.phase, lives: r.lives } : null);
  }

  private makePage(r: UiRitual | null): RitualPage | undefined {
    if (!r) return undefined;
    switch (r.phase) {
      case 'name':
      case 'rewrite':
        return new RitualNamePage(this, r);
      case 'strokes':
        return new RitualStrokesPage(this, r);
      case 'trial':
        return new RitualTrialPage(this, r);
      case 'fate': {
        // 무기 미리보기를 먼저 읽고(시스템이 lookKey 를 안 줬을 때) 그 뒤에 액자를 연다
        const f = r.fate;
        if (f && !(f.lookKey && this.textures.exists(f.lookKey)) && !uiLookKey(this, f.weapon)) {
          loadLook(this, f.weapon, () => {
            const now = this.state;
            if (this.alive && now?.phase === 'fate' && !this.page) this.page = new RitualFatePage(this, now);
          });
          return undefined;
        }
        return new RitualFatePage(this, r);
      }
      default:
        return undefined;
    }
  }

  private onKey = (e: KeyboardEvent): void => {
    if (e.repeat || !this.page || this.menuOpen()) return;
    if (this.page.key?.(e)) e.preventDefault();
  };

  private menuOpen(): boolean {
    return this.scene.isActive(UI_SCENE_KEYS.MENU);
  }

  private on<T>(event: string, handler: (p: T) => void): void {
    uiBus.on(event, handler);
    this.handlers.push([event, handler as (p: never) => void]);
  }
}
