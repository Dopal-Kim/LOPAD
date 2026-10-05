import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';
import { GlowText } from './glow';
import { routeText } from './text';
import { ROUTE } from './theme';

/**
 * 탄생 연출 중 HUD (48라운드 Q6, 계약 §10.3 — HudScene 에서 분리, 60라운드 정리): HUD 를 숨기고 하단에
 * '아무 키나 눌러 건너뛰기' 안내만 작게. 건너뛰기 입력은 시스템이 받는다. BIRTH_DONE 이 오지 않아도 HUD 가 영영 숨지 않게
 * `ROUTE.birthFailsafeMs` 뒤 스스로 끝난다.
 */
export class BirthOverlay {
  active = false;
  private cam?: Phaser.Cameras.Scene2D.Camera;
  private hint?: GlowText;
  private failsafe?: Phaser.Time.TimerEvent;

  constructor(
    private scene: Phaser.Scene,
    private hooks: {
      /** 처음 시작할 때 (지도 닫기·지역 카드 미루기) */
      onStart: () => void;
      /** 끝날 때 (미뤄 둔 자막·배너) */
      onEnd: () => void;
    },
  ) {}

  /** 시작. 글꼴 전(`built` false)이면 숨기기만 하고, 글꼴이 오면 다시 불러 안내를 띄운다 */
  start(built: boolean, stageIndex: number): void {
    const scene = this.scene;
    if (!this.active) {
      this.active = true;
      this.hooks.onStart();
      scene.cameras.main.setVisible(false);
      this.failsafe = scene.time.delayedCall(ROUTE.birthFailsafeMs, () => this.end());
    }
    if (!built || this.hint) return;
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const hint = new GlowText(scene, 0, 0, routeText('birthSkip'), 'ink_faint', {
      stageIndex: Math.max(0, stageIndex),
    });
    hint.placeCenter(W / 2, H - ROUTE.birthHintBottom - hint.displayHeight).setAlpha(0);
    // 지연(delay) 을 준 트윈은 이 이벤트 경로에서 진행되지 않았다 (헤드리스 확인) — 바로 서서히 나타나게
    scene.tweens.add({ targets: hint, alpha: 1, duration: 300 });
    // 안내만 그리는 카메라: 지금 있는 것과 연출 중 새로 생기는 것은 모두 무시한다
    // 53라운드 1920 렌더: main 카메라(시스템이 zoom·원점을 맞춤)와 같은 뷰포트·배율로 (UI 는 main 을 바꾸지 않는다)
    const main = scene.cameras.main;
    const cam = scene.cameras.add(main.x, main.y, main.width, main.height);
    cam.setZoom(main.zoom).setOrigin(main.originX, main.originY).setScroll(main.scrollX, main.scrollY);
    cam.ignore(scene.children.list.filter((o) => o !== hint));
    scene.events.on(Phaser.Scenes.Events.ADDED_TO_SCENE, this.ignoreNew);
    this.cam = cam;
    this.hint = hint;
  }

  end(): void {
    if (!this.active) return;
    const scene = this.scene;
    this.active = false;
    this.failsafe?.remove();
    this.failsafe = undefined;
    scene.events.off(Phaser.Scenes.Events.ADDED_TO_SCENE, this.ignoreNew);
    if (this.cam) {
      // 무시 표시를 지운다 (같은 카메라 id 가 나중에 다시 쓰일 수 있다)
      const bit = this.cam.id;
      const clear = (list: Phaser.GameObjects.GameObject[]) => {
        for (const o of list) {
          o.cameraFilter &= ~bit;
          if (o instanceof Phaser.GameObjects.Container) clear(o.list);
        }
      };
      clear(scene.children.list);
      scene.cameras.remove(this.cam);
      this.cam = undefined;
    }
    this.hint?.destroy();
    this.hint = undefined;
    if (scene.sys.isActive()) scene.cameras.main.setVisible(true);
    this.hooks.onEnd();
  }

  private ignoreNew = (o: Phaser.GameObjects.GameObject): void => {
    this.cam?.ignore(o);
  };
}
