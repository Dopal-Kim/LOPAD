/**
 * 48라운드 Q6 탄생 연출 연결 (계약 §10.3): 조작 잠금 · 카메라 배율은 연출이 정한다 · 아무 키·클릭 = 건너뛰기.
 * 연출 자체(시트·폴백·단계)는 systems/birth.ts.
 */
import Phaser from 'phaser';
import { BIRTH, CAMERA } from '../../core/Constants';
import { worldZoom } from '../../systems/display';
import { gameState } from '../../core/GameState';
import { UI_EVENTS, __system } from '../../contract/ui';
import { BirthSequence } from '../../systems/birth';
import { oncePerKeyEvent } from '../../systems/keyEvents';
import { UI_SCENES } from '../../ui';
import type { Game } from '../Game';

export class BirthFlow {
  seq: BirthSequence | null = null;
  private startedAt = 0;
  private readonly onKey = () => this.skip();
  /** 키는 같은 keydown 객체 재전달을 무시 (keyEvents). 포인터는 같은 Pointer 객체를 계속 쓰므로 거르지 않는다 */
  private readonly onKeyDown = oncePerKeyEvent<KeyboardEvent>(this.onKey);

  constructor(private readonly g: Game) {}

  get active(): boolean {
    return Boolean(this.seq?.active);
  }

  start(): void {
    const g = this.g;
    gameState.birthPending = false;
    const now = g.time.now;
    g.player.body.setVelocity(0, 0);
    this.seq = new BirthSequence({
      scene: g,
      x: g.player.x,
      y: g.player.y,
      hidePlayer: (on) => g.player.visual.setHidden(on),
      setPlayerAlpha: (a) => g.player.setAlpha(a),
      burst: () => {
        const B = BIRTH;
        g.screenFx.flash(B.BURST_FLASH.COLOR, B.BURST_FLASH.MS, B.BURST_FLASH.ALPHA);
        g.shake.add(g.time.now, B.BURST_SHAKE.PX, B.BURST_SHAKE.MS);
      },
      done: (skipped) => this.finish(skipped),
    });
    this.startedAt = now;
    this.seq.start(now);
    // HUD 는 같은 create 안에서 launch 되어 아직 구독 전일 수 있다 → HUD 생성이 끝난 뒤에 알린다
    const hud = g.scene.manager.keys[UI_SCENES.HUD] ? g.scene.get(UI_SCENES.HUD) : null;
    if (hud && !hud.sys.isActive()) {
      hud.sys.events.once(Phaser.Scenes.Events.CREATE, () => {
        if (this.seq?.active) __system.emit(UI_EVENTS.BIRTH_STARTED);
      });
    } else {
      __system.emit(UI_EVENTS.BIRTH_STARTED);
    }
    g.input.keyboard?.on('keydown', this.onKeyDown);
    g.input.on('pointerdown', this.onKey);
  }

  /** 연출 중 매 프레임: 입력 큐 비우기 · 연출이 정한 배율로 카메라 */
  update(time: number): void {
    const g = this.g;
    g.inputSystem.read(); // 큐 비우기
    this.seq!.update(time);
    g.cameras.main.setZoom(worldZoom(this.seq!.zoom));
    g.cam.update(true);
  }

  /** 아무 키: 건너뛰기 (씬 진입 직후 눌려 있던 입력은 무시) */
  private skip(): void {
    if (!this.seq?.active) return;
    if (this.g.time.now - this.startedAt < BIRTH.SKIP_GRACE_MS) return;
    this.seq.skip();
  }

  /** 디버그: 유예 없이 건너뛰기 */
  forceSkip(): void {
    if (this.seq?.active) this.seq.skip();
  }

  private finish(skipped: boolean): void {
    const g = this.g;
    this.unbind();
    g.cameras.main.setZoom(worldZoom(CAMERA.ZOOM));
    g.player.setAlpha(1);
    g.cam.update(true);
    // 조작 해제: 건너뛴 키가 바로 공격·대쉬로 새지 않게 아주 짧게 잠근다
    g.route.enterLockUntil = Math.max(g.route.enterLockUntil, g.time.now + (skipped ? BIRTH.SKIP_GRACE_MS : 0));
    g.inputSystem.read();
    __system.emit(UI_EVENTS.BIRTH_DONE);
  }

  private unbind(): void {
    this.g.input.keyboard?.off('keydown', this.onKeyDown);
    this.g.input.off('pointerdown', this.onKey);
  }

  destroy(): void {
    this.unbind();
    this.seq?.destroy();
    this.seq = null;
  }
}
