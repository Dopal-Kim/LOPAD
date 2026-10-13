import Phaser from 'phaser';
import { UI_SCREEN, uiCommands } from '../contract/ui';
import { debugExpose, installUiDebug, uiDebugEnabled } from './debug';
import { GlowText } from './glow';
import { keyTaken, takeKey } from './keyGate';
import { DARK_BG, ensureImage, fontsReady, preloadKit, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { artTex, paintUrl, uiCopy } from './paintArt';
import { brushOrderFrom, type Img } from './paintFx';
import { SettingsPanel } from './SettingsPanel';
import { MemoryBookView } from './MemoryBook';
import { openGate } from './choiceArm';
import { l2eText } from './textLoop2E';
import { currentSettings } from './settingsStore';
import { r49Text, r61Text, trainingText, uiText } from './text';
import { hexToNum } from './theme';
import { TitleArt } from './TitleArt';
import { TitleMenu } from './TitleMenu';
import {
  TITLE_EMBERS,
  TITLE_IMAGES,
  TITLE_JSONS,
  TITLE_UI,
  TITLE_URL,
  titleJsonKey,
  titleKey,
  type TitleSpec,
} from './themeTitle';
import {
  clamp01,
  defaultIndex,
  introState,
  isWakeKey,
  logoDoneMs,
  logoProgress,
  metaMemo,
  readTitleSpec,
  reducedMotion,
  titleItems,
  type TitleItem,
  type TitleMetaInfo,
} from './titleView';
import { ensureTransitionScene } from './TransitionScene';
import { revealAlpha } from './transitionView';

/** 이번 페이지에서 첫 입력을 받았는가 (오디오를 깨웠는가) — 타이틀로 돌아와도 '아무 키' 화면을 다시 띄우지 않는다 */
let woken = false;

const MASK_KEY = 'paint/brush_reveal_2';
const VEIL_KEY = 'ui-title-veil';

type Phase = 'load' | 'intro' | 'prompt' | 'menu' | 'dive' | 'gone';

/**
 * 62라운드 타이틀 (아트 §29 · 경쟁력 점검 T1~T8). 키아트 3층 패럴랙스 · 주인공 호흡·발광 · 무기 목소리 빛 9.6초 순환 · 불티 ·
 * 안개 3겹 · 로고 'LOPAD — 바깥의 적' · 왼쪽 아래 족자 메뉴.
 * 흐름: 검은 화면(그림 지연 로드) → 먹 붓질(`paint/brush_reveal_2`)로 걷힘 → 로고 → 무기 불씨 점등 → (첫 방문) '아무 키나 누른다'
 * — 첫 입력에서 오디오를 깨우고 메뉴 / (돌아옴) 바로 메뉴. 3초 안, 아무 키·클릭이면 바로.
 * 새로 태어나기·이어 하기는 그림 속 성문으로 파고들며 먹이 덮은 뒤 시스템 명령(점검 T8, 시스템 전환 흐름은 시스템 → UI 라
 * 타이틀이 같은 문법으로 스스로 그린다). 설정 '흔들림 0'(모션 줄이기) 또는 브라우저 동작 줄이기면 패럴랙스·안개 흐름·붓질을 끄고
 * 호흡·불티만. 떠날 때 타이틀 그림 텍스처를 내려놓는다.
 */
export class TitleScene extends Phaser.Scene {
  private alive = false;
  private phase: Phase = 'load';
  private spec?: TitleSpec;
  private art?: TitleArt;
  private menu?: TitleMenu;
  private settings?: SettingsPanel;
  /** 62 루프 2 UI E: 일기장 '기억' 장 (계약 C `memory.book()` — MemoryBook) */
  private memoryView?: MemoryBookView;
  private items: TitleItem[] = [];
  private fallbackLogo?: GlowText;
  private prompt?: GlowText;
  private version?: GlowText;
  private memo?: GlowText;
  private veil?: Phaser.GameObjects.Image;
  private veilTex?: Phaser.Textures.CanvasTexture;
  private veilData?: ImageData;
  private order?: Float32Array;
  private orderSoft: number = TITLE_UI.maskSoft;
  private glowDot?: Phaser.GameObjects.Graphics;
  private t0 = 0;
  /** 등장 경과 (ms, 디버그 느림 배율 적용) */
  private introT = 0;
  /** 62 루프 3 UI H: 로고·부제·불씨를 완성 상태로 (넘김 · 같은 세션에서 돌아옴) */
  private logoComplete = false;
  private menuT = 0;
  private diveT = 0;
  private diveAction?: () => void;
  private reduced = false;
  private slow = 1;
  private pointer: { x: number; y: number } | null = null;

  constructor() {
    super(UI_SCENE_KEYS.TITLE);
  }

  preload(): void {
    preloadKit(this);
  }

  create(): void {
    uiCommands.registerRenderer();
    setupKit(this);
    installUiDebug(this);
    this.cameras.main.setBackgroundColor(DARK_BG);
    this.alive = true;
    this.phase = 'load';
    this.settings = undefined;
    this.memoryView = undefined;
    this.menu = undefined;
    this.art = undefined;
    this.introT = 0;
    // 같은 세션에서 돌아온 타이틀은 로고를 다시 쓰지 않는다 (점검 P0-N1)
    this.logoComplete = woken;
    this.menuT = 0;
    this.diveT = 0;
    this.slow = this.debugSlow();
    this.reduced = this.readReduced();
    // 61 단계 6 (§19): 타이틀 → 수련장도 그림 속 입구로 들어간다
    ensureTransitionScene(this);
    this.input.keyboard?.on('keydown', this.onKey);
    this.input.on('pointerdown', this.onPointerDown);
    this.input.on('pointermove', this.onPointerMove);
    this.events.once('shutdown', this.onShutdown);
    this.expose();
    // 그림·글꼴·붓 마스크를 다 받은 뒤 시작 (검은 화면)
    let pending = 3;
    const done = (): void => {
      pending -= 1;
      if (pending === 0 && this.alive) this.build();
    };
    this.loadTitleArt(done);
    fontsReady().then(done);
    this.loadMask(done);
  }

  private onShutdown = (): void => {
    this.alive = false;
    this.phase = 'gone';
    this.input.keyboard?.off('keydown', this.onKey);
    this.input.off('pointerdown', this.onPointerDown);
    this.input.off('pointermove', this.onPointerMove);
    this.settings?.destroy();
    this.settings = undefined;
    this.memoryView?.destroy();
    this.memoryView = undefined;
    this.menu?.destroy();
    this.menu = undefined;
    this.art?.destroy();
    this.art = undefined;
    // 성능: 큰 타이틀 그림은 타이틀에서만 쓴다 — 씬이 다 내려간 뒤 텍스처를 놓는다 (다시 오면 다시 읽는다, 브라우저 캐시)
    const textures = this.textures;
    const sys = this.sys;
    setTimeout(() => {
      if (sys.isActive()) return;
      for (const n of [...TITLE_IMAGES, TITLE_EMBERS]) if (textures.exists(titleKey(n))) textures.remove(titleKey(n));
      if (textures.exists(VEIL_KEY)) textures.remove(VEIL_KEY);
    }, 0);
  };

  // ---------------------------------------------------------------------------------------------
  // 읽기 (지연 로드 — 타이틀이 열릴 때만)

  private loadTitleArt(done: () => void): void {
    const load = this.load;
    for (const n of TITLE_IMAGES)
      if (!this.textures.exists(titleKey(n))) load.image(titleKey(n), `${TITLE_URL}${n}.png`);
    if (!this.textures.exists(titleKey(TITLE_EMBERS)))
      load.spritesheet(titleKey(TITLE_EMBERS), `${TITLE_URL}${TITLE_EMBERS}.png`, { frameWidth: 24, frameHeight: 24 });
    for (const j of TITLE_JSONS)
      if (!this.cache.json.exists(titleJsonKey(j))) load.json(titleJsonKey(j), `${TITLE_URL}${j}.json`);
    load.once(Phaser.Loader.Events.COMPLETE, () => done());
    if (!load.isLoading()) load.start();
  }

  /** 붓 마스크 (시스템 키 → UI 사본). 오래 걸리면 코드 붓질로 */
  private loadMask(done: () => void): void {
    let called = false;
    const once = (): void => {
      if (called) return;
      called = true;
      done();
    };
    if (artTex(this, MASK_KEY)) return once();
    ensureImage(this, uiCopy(MASK_KEY), `${paintUrl(MASK_KEY)}.png`, once);
    this.time.delayedCall(TITLE_UI.maskWaitMs, once);
  }

  // ---------------------------------------------------------------------------------------------
  // 만들기

  private build(): void {
    const json = (k: string): unknown =>
      this.cache.json.exists(titleJsonKey(k)) ? this.cache.json.get(titleJsonKey(k)) : null;
    this.spec = readTitleSpec(json('title'), json('title_fx_embers'), json('title_fx_fog'), json('title_menu_frame'));
    this.art = new TitleArt(this, this.spec);
    this.art.reduced = this.reduced;
    if (!this.art.hasLogo()) {
      // 그림이 없을 때: 글자 로고
      this.fallbackLogo = new GlowText(this, 0, 0, 'LOPAD', 'title_prompt', { font: 'title', scale: 2 }).setDepth(
        TITLE_UI.depth.logo,
      );
      this.fallbackLogo.setPosition(40, 40);
    }
    // 메뉴
    const hasSave = uiCommands.hasSave();
    const meta = titleMeta();
    this.items = titleItems({
      memory: Boolean(uiCommands.memory.book()) && Boolean(meta && (meta.lives > 0 || meta.souls > 0)),
      hasSave,
      desktop: isDesktopShell(),
      dev: devMenu(),
      labels: {
        continue: uiText('title', 'continue', '이어 쓴다'),
        newRun: uiText('title', 'newRun', '다시 태어난다'),
        newRunDeleteSave: uiText('title', 'newRunDeleteSave', '다시 태어난다 (일기장을 찢는다)'),
        training: trainingText('titleItem'),
        memory: l2eText('titleItem'),
        memoryHint: l2eText('titleItemHint'),
        lab: r49Text('titleLab'),
        settings: r61Text('settingsItem'),
        quit: uiText('title', 'quit', '끝내기'),
      },
    });
    this.menu = new TitleMenu(this, this.spec, this.items, defaultIndex(this.items), (it) => this.onChoose(it));
    // '아무 키나 누른다' — 로고 가운데 아래, 들판 위
    const sp = this.spec;
    this.prompt = new GlowText(this, 0, 0, uiText('title', 'pressAny', '아무 키나 누른다'), 'title_prompt', {
      font: 'title',
    }).setDepth(TITLE_UI.depth.menu + 3);
    this.prompt
      .placeCenter(
        (sp.logo.x + sp.logo.w / 2) / 2,
        Math.round((sp.menu.y + sp.menu.h / 2) / 2 - this.prompt.displayHeight / 2),
      )
      .setAlpha(0);
    // 버전 (오른쪽 아래) · 귀퉁이 메타 메모 (오른쪽 위 — 값이 있을 때만)
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    this.version = new GlowText(this, 0, 0, TITLE_UI.version, 'title_version').setDepth(TITLE_UI.depth.menu);
    this.version.placeRight(W - 8, H - this.version.displayHeight - 4).setAlpha(0);
    const memo = metaMemo(meta, uiCommands.getUiSnapshot().names?.souls ?? '영혼');
    if (memo) {
      this.memo = new GlowText(this, 0, 0, memo, 'title_version').setDepth(TITLE_UI.depth.menu);
      this.memo.placeRight(W - 10, 8).setAlpha(0);
    }
    this.buildVeil();
    this.t0 = this.time.now;
    this.phase = 'intro';
    this.expose();
  }

  /** 붓질 덮개 (480×270 캔버스, 선형 필터) */
  private buildVeil(): void {
    const PW = TITLE_UI.veilW;
    const PH = TITLE_UI.veilH;
    const tex = this.textures.exists(VEIL_KEY)
      ? (this.textures.get(VEIL_KEY) as Phaser.Textures.CanvasTexture)
      : this.textures.createCanvas(VEIL_KEY, PW, PH);
    if (!tex) return;
    tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
    this.veilTex = tex;
    this.veilData = tex.getContext().createImageData(PW, PH);
    const key = artTex(this, MASK_KEY);
    this.order = brushOrderFrom(key ? (this.textures.get(key).getSourceImage() as Img) : null, PW, PH, 1023);
    this.orderSoft = key ? TITLE_UI.maskSoft : 0.14;
    this.veil = this.add
      .image(0, 0, VEIL_KEY)
      .setOrigin(0, 0)
      .setScale(UI_SCREEN.WIDTH / PW, UI_SCREEN.HEIGHT / PH)
      .setDepth(TITLE_UI.depth.veil);
    this.writeVeil(() => 255);
    this.glowDot = this.add
      .graphics()
      .setDepth(TITLE_UI.depth.veil + 1)
      .setVisible(false);
  }

  private writeVeil(alpha: (i: number) => number): void {
    const tex = this.veilTex;
    const data = this.veilData;
    if (!tex || !data) return;
    const d = data.data;
    for (let i = 0, n = TITLE_UI.veilW * TITLE_UI.veilH; i < n; i++) {
      const p = i * 4;
      d[p] = 0;
      d[p + 1] = 0;
      d[p + 2] = 0;
      d[p + 3] = alpha(i);
    }
    tex.getContext().putImageData(data, 0, 0);
    tex.refresh();
  }

  // ---------------------------------------------------------------------------------------------
  // 매 프레임

  update(_time: number, delta: number): void {
    if (!this.art || this.phase === 'load' || this.phase === 'gone') return;
    const now = this.time.now - this.t0;
    // 62 루프 3 UI H (P0-N1): 등장 시계는 메뉴가 열려도 계속 간다 — 로고 쓰기·부제·불씨가 메뉴 단계에서 멈추지 않게
    this.introT += delta / this.slow;
    const it = introState(this.introT, this.reduced);
    // 덮개 (붓질 또는 모션 줄이기면 페이드)
    if (this.phase !== 'dive') this.updateRevealVeil(it.reveal);
    // art §30 로고 쓰기 (logoAt 부터 logoReveal.ms 동안, 모션 줄이기·파고들기·넘김·돌아옴이면 완성)
    const lp = logoProgress(this.introT, {
      complete: this.logoComplete || this.reduced || this.phase === 'dive',
      revealMs: this.spec?.logoReveal?.ms,
    });
    this.art.intro.logo = this.phase === 'dive' ? this.art.intro.logo : lp.logo;
    this.art.intro.sub = this.phase === 'dive' ? this.art.intro.sub : lp.sub;
    this.art.intro.dots = lp.dots;
    this.art.revealP = lp.revealP;
    if (this.phase !== 'dive') this.fallbackLogo?.setAlpha(lp.logo);
    // 등장 끝 → '아무 키' 또는 메뉴
    if (this.phase === 'intro' && this.introT >= TITLE_UI.intro.menuAt) {
      if (woken) this.showMenu();
      else this.phase = 'prompt';
    }
    if (this.phase === 'prompt' && this.prompt) {
      const a = clamp01((this.introT - TITLE_UI.intro.menuAt) / TITLE_UI.intro.menuMs);
      const blink = this.reduced
        ? 1
        : 0.55 + 0.45 * (0.5 + 0.5 * Math.cos((2 * Math.PI * now) / TITLE_UI.promptBlinkMs));
      this.prompt.setAlpha(a * blink);
      this.version?.setAlpha(a);
      this.memo?.setAlpha(a);
    }
    if (this.phase === 'menu' && this.menu) {
      this.menuT += delta / this.slow;
      const p = clamp01(this.menuT / TITLE_UI.intro.menuMs);
      this.menu.setAppear(1 - Math.pow(1 - p, 3));
      this.prompt?.setAlpha(Math.max(0, (this.prompt.alpha ?? 0) - delta / 160));
      this.version?.setAlpha(1);
      this.memo?.setAlpha(1);
    }
    if (this.phase === 'dive') this.updateDive(delta);
    // 파고들기 끝의 시스템 명령으로 이 씬이 이미 내려갔을 수 있다
    if (!this.alive || !this.art) return;
    this.menu?.update(this.time.now);
    this.art.update(now, delta, this.phase === 'dive' ? null : this.pointer);
    if (uiDebugEnabled()) this.expose();
  }

  private lastReveal = -1;
  private updateRevealVeil(reveal: number): void {
    if (!this.veil) return;
    if (reveal === this.lastReveal) return;
    this.lastReveal = reveal;
    if (reveal >= 1) {
      this.veil.setVisible(false);
      return;
    }
    this.veil.setVisible(true);
    if (this.reduced || !this.order) {
      this.veil.setAlpha(1);
      const a = Math.round((1 - reveal) * 255);
      this.writeVeil(() => a);
      return;
    }
    const order = this.order;
    const soft = this.orderSoft;
    this.writeVeil((i) => Math.round(revealAlpha(order[i] ?? 1, reveal, soft) * 255));
  }

  // ---------------------------------------------------------------------------------------------
  // 입력

  private onKey = (e: KeyboardEvent): void => {
    if (this.settings || this.memoryView) return; // 설정·기억 장이 받는다 (Esc 는 아래)
    if (this.phase === 'load' || this.phase === 'dive' || this.phase === 'gone') return;
    if (this.phase === 'intro' || this.phase === 'prompt') {
      if (!isWakeKey(e.key) || e.repeat || keyTaken(e)) return;
      takeKey(e);
      this.wake();
      return;
    }
    this.menu?.handleKey(e);
  };

  private onPointerDown = (p: Phaser.Input.Pointer): void => {
    this.trackPointer(p);
    if (this.settings || this.memoryView) return;
    if (this.phase === 'intro' || this.phase === 'prompt') this.wake();
  };

  private onPointerMove = (p: Phaser.Input.Pointer): void => this.trackPointer(p);

  private trackPointer(p: Phaser.Input.Pointer): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    this.pointer = {
      x: Phaser.Math.Clamp((p.x - W / 2) / (W / 2), -1, 1),
      y: Phaser.Math.Clamp((p.y - H / 2) / (H / 2), -1, 1),
    };
  }

  /** 첫 입력: 등장을 끝까지 넘기고, 오디오를 깨우고(점검 T3), 메뉴를 띄운다 */
  private wake(): void {
    woken = true;
    wakeAudio(this);
    this.logoComplete = true;
    this.introT = Math.max(this.introT, logoDoneMs(this.spec?.logoReveal?.ms));
    this.updateRevealVeil(1);
    this.showMenu();
  }

  private showMenu(): void {
    if (this.phase === 'menu' || !this.menu) return;
    this.phase = 'menu';
    this.menuT = 0;
    this.menu.setInput(true);
    this.expose();
  }

  // ---------------------------------------------------------------------------------------------
  // 메뉴 동작 (61 TitleScene 동작 보존)

  private onChoose(item: TitleItem): void {
    if (!this.alive) return;
    switch (item.id) {
      case 'continue':
        this.beginDive(() => uiCommands.continueRun());
        break;
      case 'newRun':
        this.beginDive(() => uiCommands.startNewRun());
        break;
      case 'training':
        this.startTraining();
        break;
      case 'lab':
        uiCommands.startWeaponLab();
        break;
      case 'settings':
        this.openSettings();
        break;
      case 'memory':
        this.openMemory();
        break;
      case 'quit':
        window.close();
        this.menu?.unlock();
        break;
    }
  }

  /** 61 단계 6 (§19): 수련장 — 시스템이 그림 속 입구 전환으로 데려간다. 받아들여지지 않으면 틀 아래 한 줄 */
  private startTraining(): void {
    const r = uiCommands.startTraining();
    if (r === 'ok') return;
    const why = r === 'combat' ? 'denyCombat' : r === 'boss' ? 'denyBoss' : 'denyBusy';
    this.menu?.notice(trainingText(why));
    this.menu?.unlock();
  }

  /** 62 루프 2 UI E: 일기장 '기억' 장 (덮으면 메뉴로) */
  private openMemory(): void {
    if (this.memoryView || this.settings) return;
    this.menu?.setInput(false);
    this.memoryView = new MemoryBookView(this, {
      stageIndex: 0,
      gate: openGate(),
      depth: TITLE_UI.depth.veil - 2,
      book: () => uiCommands.memory.book(),
      recall: (id) => uiCommands.memory.unlock(id),
      setKeepsake: (id) => uiCommands.memory.setKeepsake(id),
      close: () => {
        this.memoryView?.destroy();
        this.memoryView = undefined;
        this.time.delayedCall(0, () => {
          this.menu?.unlock();
          this.menu?.setInput(true);
        });
      },
      handleEsc: true,
      live: true,
      backdrop: true,
    });
    this.expose();
  }

  private openSettings(): void {
    if (this.settings) return;
    this.menu?.setInput(false);
    this.settings = new SettingsPanel(this, {
      stageIndex: 0,
      onClose: () => {
        this.settings = undefined;
        // 설정에서 흔들림을 0 으로 바꾸면 곧바로 모션 줄이기
        this.reduced = this.readReduced();
        if (this.art) this.art.reduced = this.reduced;
        this.menu?.unlock();
        this.menu?.setInput(true);
        this.expose();
      },
    });
    this.input.keyboard?.once('keydown-ESC', this.onEsc);
  }

  /** Esc: 설정 쪽이 떠 있으면 덮는다 */
  private onEsc = (e?: KeyboardEvent): void => {
    if (!this.settings) return;
    if (e?.repeat || keyTaken(e)) {
      this.input.keyboard?.once('keydown-ESC', this.onEsc);
      return;
    }
    takeKey(e);
    // 62 루프 2: 키 기다리는 중이면 그만두기만 (쪽은 그대로 — 다음 Esc 를 다시 기다린다)
    if (!this.settings.back()) this.input.keyboard?.once('keydown-ESC', this.onEsc);
  };

  /**
   * 점검 T8: 그림 속 성문으로 파고들며(가까운 층일수록 빨리 커짐) 가장자리부터 먹이 덮고, 성문 빛이 마지막에 꺼진다 →
   * 시스템 명령. 모션 줄이기면 짧은 페이드만.
   */
  private beginDive(action: () => void): void {
    if (this.phase === 'dive') return;
    this.phase = 'dive';
    this.diveT = 0;
    this.diveAction = action;
    this.menu?.setInput(false);
    this.expose();
  }

  private updateDive(delta: number): void {
    const ms = this.reduced ? TITLE_UI.intro.fadeMs : TITLE_UI.dive.ms;
    this.diveT += delta / this.slow;
    const p = clamp01(this.diveT / ms);
    if (this.art) {
      if (!this.reduced) this.art.dive = p;
      this.art.intro.logo = 1 - clamp01(p * 2.5);
      this.art.intro.sub = this.art.intro.logo;
      this.fallbackLogo?.setAlpha(this.art.intro.logo);
    }
    this.menu?.setAppear(1 - clamp01(p * 3));
    this.version?.setAlpha(1 - clamp01(p * 3));
    this.memo?.setAlpha(1 - clamp01(p * 3));
    // 먹 덮개: 가장자리(마스크 늦은 쪽)부터 가운데로 — 걷힘을 거꾸로
    if (this.veil) {
      this.veil.setVisible(true);
      const cover = clamp01((p - 0.25) / 0.75);
      if (this.reduced || !this.order) {
        const a = Math.round(clamp01(p) * 255);
        this.writeVeil(() => a);
      } else {
        const order = this.order;
        const soft = this.orderSoft;
        this.writeVeil((i) => Math.round((1 - revealAlpha(1 - (order[i] ?? 1), cover, soft)) * 255));
      }
    }
    // 성문 안 빛: 덮이기 직전 가운데에서 한 번 번졌다 사라진다
    if (this.glowDot && !this.reduced) {
      const g = this.glowDot;
      const k = Math.sin(clamp01((p - 0.55) / 0.45) * Math.PI);
      g.clear().setVisible(k > 0.01);
      if (k > 0.01) {
        const gate = this.art?.gateScreen() ?? { x: UI_SCREEN.WIDTH / 2, y: UI_SCREEN.HEIGHT / 2 };
        const cx = gate.x;
        const cy = gate.y;
        for (let r = 5; r >= 1; r--) {
          g.fillStyle(hexToNum(TITLE_UI.dive.lightHex), 0.12 * k).fillCircle(cx, cy, r * 9 * (0.6 + 0.4 * k));
        }
      }
    }
    if (p >= 1 && this.diveAction) {
      const act = this.diveAction;
      this.diveAction = undefined;
      this.glowDot?.clear();
      this.writeVeil(() => 255);
      this.expose();
      act();
    }
  }

  // ---------------------------------------------------------------------------------------------

  private readReduced(): boolean {
    const prefers =
      typeof window !== 'undefined' && typeof window.matchMedia === 'function'
        ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
        : false;
    return reducedMotion(currentSettings(), prefers);
  }

  /** 디버그(uidebug=1): 주소 `titleslow=n` 이면 등장·파고들기를 n 배 느리게 (단계별 캡처용) */
  private debugSlow(): number {
    if (!uiDebugEnabled()) return 1;
    const v = Number(new URLSearchParams(location.search).get('titleslow'));
    return Number.isFinite(v) && v > 0 ? v : 1;
  }

  private expose(): void {
    debugExpose('title', {
      phase: this.phase,
      reduced: this.reduced,
      woken,
      introT: Math.round(this.introT),
      logoComplete: this.logoComplete,
      logoP: this.art?.revealP ?? 0,
      items: this.items.map((i) => ({ id: i.id, label: i.label, enabled: i.enabled })),
      selected: this.menu?.selected().id ?? null,
      rows: this.menu?.rowCenters() ?? [],
      art: this.art?.stats() ?? null,
      settingsOpen: Boolean(this.settings),
    });
  }
}

/** 첫 입력 안에서 오디오 컨텍스트를 깨운다 (브라우저 자동재생 정책 — 점검 T3) */
function wakeAudio(scene: Phaser.Scene): void {
  const snd = scene.sound as unknown as { context?: AudioContext; locked?: boolean; unlock?: () => void };
  try {
    if (snd.context && snd.context.state === 'suspended') void snd.context.resume();
    if (snd.locked) snd.unlock?.();
  } catch {
    // 소리가 없는 환경 — 무시
  }
}

/** 데스크톱 껍데기(Electron·Tauri)에서만 '끝내기' — 웹은 창을 닫을 수 없어 숨긴다 */
function isDesktopShell(): boolean {
  if (typeof window === 'undefined') return false;
  const w = window as unknown as { process?: { versions?: { electron?: string } }; __TAURI__?: unknown };
  return typeof w.process?.versions?.electron === 'string' || typeof w.__TAURI__ !== 'undefined';
}

/** 개발용 메뉴(무기 시험장): 주소 `#lab` 또는 uidebug 일 때만 (점검 T5 — 시스템 `?lab` 주소는 그대로) */
function devMenu(): boolean {
  if (typeof location === 'undefined') return false;
  return location.hash === '#lab' || uiDebugEnabled();
}

/** 귀퉁이 메타 메모 값 (점검 T7) — 계약 `UiSnapshot.meta`(62 시스템 추가: 지난 생 수·영혼·가장 깊이 간 층, 타이틀에서도 온다) */
function titleMeta(): TitleMetaInfo | null {
  const m = uiCommands.getUiSnapshot().meta;
  return m ? { lives: m.lives, souls: m.souls, bestFloor: m.bestFloor } : null;
}
