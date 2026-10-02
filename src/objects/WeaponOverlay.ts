/**
 * 손에 든 무기 오버레이 (계약 art-assets.md §3.1, 48라운드 §6.1·6.2, 49라운드 §7.1·7.2).
 * 주인공 시트는 맨손이고, 무기를 드는 동작(attack · <무기>_combo<n> · <무기>_special · <무기>_aim ·
 * 49라운드 <무기>_draw·sheathe·slam·dashslash·reload)이 보이는 동안 `weapons/<무기id>_<동작>` 시트의 **같은 프레임 번호**를
 * 플레이어 피벗에 겹쳐 보인다(무기 연격 시트가 없으면 attack 시트).
 * 49라운드 휴대: 그 밖의 동작(대기·걷기·대쉬·피격)에서는 휴대 시트 `weapons/<무기>_carry_<idle|walk|dash>` 를 같은 열로
 * 겹친다(칼 = 허리 칼집, 대검 = 등, 단검·활 = 손). 칼·대검을 뽑아 든 동안(공격 뒤 넣기 전)은 `<무기>_carry_drawn_<동작>`.
 * 시트가 없으면 기존 attack 무기 시트 0프레임을 휴대 위치(Constants CARRY)에 작게 겹치는 폴백.
 * 깊이는 JSON `depth`(방향별, 방향·프레임별 배열 허용). 팔레트 스왑 변형(`@f<n>`)은 spriteLibrary 의 현재 텍스처 키를 그대로 쓴다.
 */
import Phaser from 'phaser';
import { CARRY, DEPTH } from '../core/Constants';
import { gameState } from '../core/GameState';
import { spriteLibrary } from '../systems/sprites';
import {
  carryAction,
  carryActionFor,
  carryDrawnAction,
  frameAt,
  overlayActionsFor,
  overlayDepthAt,
  parseAnimKey,
  type Facing,
  type SheetDef,
} from '../systems/spriteDefs';

/** 휴대 상태: hand = 늘 손(단검·활) · stowed = 칼집·등에 넣음 · drawn = 칼·대검을 뽑아 든 상태 */
export interface CarryInfo {
  mode: 'sheath' | 'back' | 'hand';
  drawn: boolean;
}

export class WeaponOverlay {
  private readonly sprite: Phaser.GameObjects.Sprite;
  private texture: string | null = null;
  /** 디버그: 현재 보이는 시트·프레임 */
  frame = -1;
  /** 디버그: 현재 겹친 무기 시트 동작 */
  action: string | null = null;
  /** 디버그 (49라운드): 휴대 표시 방식 — sheet(휴대 시트) · fallback(attack 0프레임) · null(숨김·공격 오버레이) */
  carry: 'sheet' | 'fallback' | null = null;

  constructor(
    private readonly host: Phaser.GameObjects.Sprite,
    /** 현재 애니 키 (EntityVisual.current — 프레임 유지 `#hold<c>` 포함) */
    private readonly currentKey: () => string | null = () => null,
    /** 49라운드: 휴대 상태 (없으면 휴대 표시 안 함) */
    private readonly carryInfo: () => CarryInfo | null = () => null,
  ) {
    this.sprite = host.scene.add.sprite(host.x, host.y, '__DEFAULT').setVisible(false);
    host.once(Phaser.GameObjects.Events.DESTROY, () => this.sprite.destroy());
  }

  get visible(): boolean {
    return this.sprite.visible;
  }

  /** 매 프레임: 호스트가 무기를 드는 동작이면 같은 열의 무기 프레임을, 아니면 휴대 모습을 보인다 */
  update(): void {
    const playing = this.host.anims.isPlaying ? this.host.anims.currentAnim?.key : undefined;
    const current = this.currentKey();
    const key = playing ?? (current && current.includes('#hold') ? current : undefined);
    const parsed = key ? parseAnimKey(key, 'player') : null;
    if (!parsed) {
      // 일회성 동작이 끝나 멈춘 사이(다음 프레임에 idle·walk): 마지막 방향으로 휴대 모습
      const last = current ? parseAnimKey(current, 'player') : null;
      return last ? this.updateCarry('idle', last.dir, 0) : this.hide();
    }
    let column: number;
    if (playing) {
      const cur = this.host.anims.currentFrame;
      if (!cur) return this.hide();
      // 파생 애니(구간 재생·반복)도 맞도록 텍스처 프레임 번호(row × frames + col)에서 열을 꺼낸다
      const body = spriteLibrary.sheet('player', parsed.action);
      const fi = Number(cur.frame.name);
      column = body && Number.isFinite(fi) ? fi % body.frames : cur.index - 1;
    } else {
      const m = /#hold(\d+)/.exec(key!);
      column = m ? Number(m[1]) : 0;
    }
    const id = gameState.weapon.id;
    for (const a of overlayActionsFor(parsed.action, id)) {
      const def = this.sheetOf(id, a);
      if (def) {
        this.carry = null;
        this.show(def, a, parsed.dir, column, overlayDepthAt(def, parsed.dir, column) === 'below');
        return;
      }
    }
    this.updateCarry(parsed.action, parsed.dir, column);
  }

  /** 49라운드 휴대: 휴대 시트(같은 열) → 없으면(또는 뽑아 든 상태면) attack 0프레임 폴백 */
  private updateCarry(bodyAction: string, dir: Facing, column: number): void {
    const info = this.carryInfo();
    const ca = carryActionFor(bodyAction);
    if (!info || !ca) return this.hide();
    const id = gameState.weapon.id;
    const stowed = info.mode !== 'hand' && !info.drawn;
    // 뽑아 든 칼·대검은 carry_drawn_* (아트 49라운드 임시 추가), 그 밖은 carry_*. 피격 등 휴대 동작이 아닌 몸 동작은 idle 0열
    const drawn = info.mode !== 'hand' && info.drawn;
    const name = drawn ? carryDrawnAction : carryAction;
    const col0 = ca === 'idle' && bodyAction !== 'idle' ? 0 : column;
    const def = this.sheetOf(id, name(ca)) ?? this.sheetOf(id, name('idle'));
    if (def) {
      this.carry = 'sheet';
      const col = col0 % def.frames;
      this.show(def, def.action, dir, col, overlayDepthAt(def, dir, col) === 'below');
      return;
    }
    const attack = this.sheetOf(id, 'attack');
    if (!attack) return this.hide();
    const table = stowed ? (info.mode === 'back' ? CARRY.BACK : CARRY.SHEATH) : CARRY.HAND;
    const at = table[dir];
    this.carry = 'fallback';
    this.show(attack, 'attack', dir, 0, at.below, {
      x: at.x,
      y: at.y,
      angle: at.angle,
      scale: stowed ? CARRY.STOWED_SCALE : CARRY.HAND_SCALE,
    });
  }

  private sheetOf(id: string, action: string): SheetDef | undefined {
    const def = spriteLibrary.sheet(id, action);
    const texture = spriteLibrary.textureKey(id, action);
    return def && texture && this.host.scene.textures.exists(texture) ? def : undefined;
  }

  private show(
    def: SheetDef,
    action: string,
    dir: Facing,
    column: number,
    below: boolean,
    place: { x: number; y: number; angle: number; scale: number } | null = null,
  ): void {
    const texture = spriteLibrary.textureKey(gameState.weapon.id, action)!;
    if (this.texture !== texture) {
      this.sprite.setTexture(texture, 0);
      this.texture = texture;
    }
    this.sprite.setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight);
    this.frame = frameAt(def, dir, column);
    this.action = action;
    this.sprite.setFrame(this.frame);
    if (place) {
      this.sprite.setScale(place.scale).setAngle(place.angle);
      this.sprite.setPosition(this.host.x + place.x, this.host.y + place.y);
    } else {
      this.sprite.setScale(1).setAngle(0);
      this.sprite.setPosition(this.host.x, this.host.y);
    }
    this.sprite
      .setAlpha(this.host.alpha)
      .setDepth(this.host.depth + (below ? -DEPTH.OVERLAY_STEP : DEPTH.OVERLAY_STEP))
      .setVisible(this.host.visible);
  }

  hide(): void {
    if (this.sprite.visible) this.sprite.setVisible(false);
    this.frame = -1;
    this.action = null;
    this.carry = null;
  }
}
