import Phaser from 'phaser';
import { KEYS } from '../core/Constants';

/** 게임 로직이 입력 소스를 모르게 하는 추상화. 조작키 확정은 UI 파트 개시 인터뷰에서. */
export interface InputState {
  moveX: number; // -1..1
  moveY: number; // -1..1
  /** 이 프레임에 공격 입력이 시작됨 (좌클릭) */
  attackPressed: boolean;
  /** 이 프레임에 패링 입력이 시작됨 (우클릭) */
  parryPressed: boolean;
  /** 이 프레임에 대쉬 입력이 시작됨 (스페이스바) */
  dashPressed: boolean;
  /** 이 프레임에 물약 사용 (Q) */
  potionPressed: boolean;
  /** 공격 조준 지점 (월드 좌표) */
  aimX: number;
  aimY: number;
  restartPressed: boolean;
}

export class InputSystem {
  private keys: Record<string, Phaser.Input.Keyboard.Key>;
  private attackQueued = false;
  private parryQueued = false;
  private readonly onPointerDown: (p: Phaser.Input.Pointer) => void;

  constructor(private scene: Phaser.Scene) {
    const kb = scene.input.keyboard!;
    this.keys = {
      up: kb.addKey(KEYS.UP),
      down: kb.addKey(KEYS.DOWN),
      left: kb.addKey(KEYS.LEFT),
      right: kb.addKey(KEYS.RIGHT),
      restart: kb.addKey(KEYS.RESTART),
      dash: kb.addKey(KEYS.DASH),
      potion: kb.addKey(KEYS.POTION),
    };
    scene.input.mouse?.disableContextMenu();
    this.onPointerDown = (p) => {
      if (p.leftButtonDown()) this.attackQueued = true;
      if (p.rightButtonDown()) this.parryQueued = true;
    };
    scene.input.on('pointerdown', this.onPointerDown);
  }

  read(): InputState {
    const x = (this.keys.right.isDown ? 1 : 0) - (this.keys.left.isDown ? 1 : 0);
    const y = (this.keys.down.isDown ? 1 : 0) - (this.keys.up.isDown ? 1 : 0);
    const pointer = this.scene.input.activePointer;
    // pointer.worldX 는 포인터 이벤트 시점의 카메라로 계산되어 방 전환 직후 어긋날 수 있다.
    // 항상 현재 카메라 기준으로 월드 좌표를 다시 구한다.
    const aim = this.scene.cameras.main.getWorldPoint(pointer.x, pointer.y);
    const state: InputState = {
      moveX: x,
      moveY: y,
      attackPressed: this.attackQueued,
      parryPressed: this.parryQueued,
      dashPressed: Phaser.Input.Keyboard.JustDown(this.keys.dash),
      potionPressed: Phaser.Input.Keyboard.JustDown(this.keys.potion),
      aimX: aim.x,
      aimY: aim.y,
      restartPressed: Phaser.Input.Keyboard.JustDown(this.keys.restart),
    };
    this.attackQueued = false;
    this.parryQueued = false;
    return state;
  }

  destroy(): void {
    this.scene.input.off('pointerdown', this.onPointerDown);
  }
}
