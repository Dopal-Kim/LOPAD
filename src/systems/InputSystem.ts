import Phaser from 'phaser';
import { KEYS } from '../core/Constants';

/** 게임 로직이 입력 소스를 모르게 하는 추상화. 조작키 확정은 UI 파트 개시 인터뷰에서. */
export interface InputState {
  moveX: number; // -1..1
  moveY: number; // -1..1
  /** 이 프레임에 공격 입력이 시작됨 (좌클릭) */
  attackPressed: boolean;
  /** 이 프레임에 보조 동작 입력이 시작됨 (우클릭: 패링·가드·그림자 걸음·조준 사격) */
  secondaryPressed: boolean;
  /** 우클릭을 누르고 있음 (가드·조준 유지) */
  secondaryHeld: boolean;
  /** 이 프레임에 우클릭을 뗌 */
  secondaryReleased: boolean;
  /** 이 프레임에 대쉬 입력이 시작됨 (스페이스바) */
  dashPressed: boolean;
  /** 이 프레임에 물약 사용 (Q) */
  potionPressed: boolean;
  /** 공격 조준 지점 (월드 좌표) */
  aimX: number;
  aimY: number;
  restartPressed: boolean;
  /** 달리기 키(Shift)를 누르고 있음 — 45라운드, 비전투에서만 효과 */
  sprintHeld: boolean;
  /** 47라운드: 이 프레임에 상호작용 키(E)를 누름 */
  interactPressed: boolean;
  /** 47라운드: 상호작용 키를 누르고 있음 (묘 2초 누르기) */
  interactHeld: boolean;
  /** 49라운드: 이 프레임에 수동 장전 키(R)를 누름 — 활 탄창 */
  reloadPressed: boolean;
}

/** 입력 잠금(워프 연출 등): 조준만 남기고 이동·동작 입력을 비운 사본 */
export function neutralInput(s: InputState): InputState {
  return {
    ...s,
    moveX: 0,
    moveY: 0,
    attackPressed: false,
    secondaryPressed: false,
    secondaryReleased: false,
    dashPressed: false,
    potionPressed: false,
    restartPressed: false,
    sprintHeld: false,
    interactPressed: false,
    interactHeld: false,
    reloadPressed: false,
  };
}

export class InputSystem {
  private keys: Record<string, Phaser.Input.Keyboard.Key>;
  private attackQueued = false;
  private secondaryQueued = false;
  private secondaryReleaseQueued = false;
  private secondaryHeld = false;
  private readonly onPointerDown: (p: Phaser.Input.Pointer) => void;
  private readonly onPointerUp: (p: Phaser.Input.Pointer) => void;

  constructor(private scene: Phaser.Scene) {
    const kb = scene.input.keyboard!;
    this.keys = {
      up: kb.addKey(KEYS.UP),
      down: kb.addKey(KEYS.DOWN),
      left: kb.addKey(KEYS.LEFT),
      right: kb.addKey(KEYS.RIGHT),
      dash: kb.addKey(KEYS.DASH),
      potion: kb.addKey(KEYS.POTION),
      sprint: kb.addKey(KEYS.SPRINT),
      interact: kb.addKey(KEYS.INTERACT),
      reload: kb.addKey(KEYS.RELOAD),
    };
    scene.input.mouse?.disableContextMenu();
    this.onPointerDown = (p) => {
      if (p.leftButtonDown()) this.attackQueued = true;
      if (p.rightButtonDown() && !this.secondaryHeld) {
        this.secondaryQueued = true;
        this.secondaryHeld = true;
      }
    };
    this.onPointerUp = (p) => {
      if (!p.rightButtonDown() && this.secondaryHeld) {
        this.secondaryHeld = false;
        this.secondaryReleaseQueued = true;
      }
    };
    scene.input.on('pointerdown', this.onPointerDown);
    scene.input.on('pointerup', this.onPointerUp);
  }

  read(): InputState {
    const x = (this.keys.right.isDown ? 1 : 0) - (this.keys.left.isDown ? 1 : 0);
    const y = (this.keys.down.isDown ? 1 : 0) - (this.keys.up.isDown ? 1 : 0);
    const pointer = this.scene.input.activePointer;
    // pointer.worldX 는 포인터 이벤트 시점의 카메라로 계산되어 방 전환 직후 어긋날 수 있다.
    // 항상 현재 카메라 기준으로 월드 좌표를 다시 구한다.
    const aim = this.scene.cameras.main.getWorldPoint(pointer.x, pointer.y);
    // 49라운드: 장전(R)은 재시작(KEYS.RESTART, 결과 화면 전용)과 같은 키 — JustDown 은 한 번만 읽고 둘 다에 쓴다
    const reload = Phaser.Input.Keyboard.JustDown(this.keys.reload);
    const state: InputState = {
      moveX: x,
      moveY: y,
      attackPressed: this.attackQueued,
      secondaryPressed: this.secondaryQueued,
      secondaryHeld: this.secondaryHeld,
      secondaryReleased: this.secondaryReleaseQueued,
      dashPressed: Phaser.Input.Keyboard.JustDown(this.keys.dash),
      potionPressed: Phaser.Input.Keyboard.JustDown(this.keys.potion),
      aimX: aim.x,
      aimY: aim.y,
      restartPressed: reload,
      sprintHeld: this.keys.sprint.isDown,
      interactPressed: Phaser.Input.Keyboard.JustDown(this.keys.interact),
      interactHeld: this.keys.interact.isDown,
      reloadPressed: reload,
    };
    this.attackQueued = false;
    this.secondaryQueued = false;
    this.secondaryReleaseQueued = false;
    return state;
  }

  destroy(): void {
    this.scene.input.off('pointerdown', this.onPointerDown);
    this.scene.input.off('pointerup', this.onPointerUp);
  }
}
