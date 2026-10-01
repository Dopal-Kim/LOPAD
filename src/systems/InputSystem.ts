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
    const state: InputState = {
      moveX: x,
      moveY: y,
      attackPressed: this.attackQueued,
      parryPressed: this.parryQueued,
      dashPressed: Phaser.Input.Keyboard.JustDown(this.keys.dash),
      aimX: pointer.worldX,
      aimY: pointer.worldY,
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
