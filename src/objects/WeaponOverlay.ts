/**
 * 손에 든 무기 오버레이 (계약 art-assets.md §3.1, 48라운드 §6.1·6.2, 49라운드 §7.1·7.2).
 * 주인공 시트는 맨손이고, 무기를 드는 동작(attack · <무기>_combo<n> · <무기>_special · <무기>_aim ·
 * 49라운드 <무기>_draw·sheathe·slam·dashslash·reload)이 보이는 동안 `weapons/<무기id>_<동작>` 시트의 **같은 프레임 번호**를
 * 플레이어 피벗에 겹쳐 보인다(무기 연격 시트가 없으면 attack 시트).
 * 49라운드 휴대: 그 밖의 동작(대기·걷기·대쉬·피격)에서는 휴대 시트 `weapons/<무기>_carry_<idle|walk|dash>` 를 같은 열로
 * 겹친다(칼 = 허리 칼집, 대검 = 등, 단검·활 = 손). 칼·대검을 뽑아 든 동안(공격 뒤 넣기 전)은 `<무기>_carry_drawn_<동작>`.
 * 시트가 없으면 기존 attack 무기 시트 0프레임을 휴대 위치(Constants CARRY)에 작게 겹치는 폴백.
 * 깊이는 JSON `depth`(방향별, 방향·프레임별 배열 허용). 팔레트 스왑 변형(`@f<n>`)은 spriteLibrary 의 현재 텍스처 키를 그대로 쓴다.
 * 52라운드 v3 (계약 §11, Q13): 원점 = 몸 피벗 + `playerFrameOffset` · `occlusionBaked` 면 늘 몸 위 · `carryHidden` 연격 시트가 보이는
 * 동안 휴대 시트를 숨긴다 · 달리기 휴대 `carry_run`(없으면 walk). 손·칼 앵커는 `spriteMeta`(디버그 `?anchors`).
 */
import Phaser from 'phaser';
import { CARRY, DEPTH } from '../core/Constants';
import { anchorOffset, bladeAt, gripAt, handAt, overlayPivot, type BladeLocal } from '../systems/spriteMeta';
import { gameState } from '../core/GameState';
import { spriteLibrary } from '../systems/sprites';
import {
  artScale,
  carryAction,
  carryActionFor,
  carryDrawnAction,
  frameAt,
  overlayActionsFor,
  overlayDepthAt,
  parseAnimKey,
  type CarryAction,
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
  /** 디버그 (52라운드): 지금 보이는 무기 시트가 연격 중 휴대 숨김(carryHidden)인지 */
  carryHidden = false;
  /** 현재 몸 시트 (원점 정렬·손 앵커) */
  private body: SheetDef | undefined;
  /** 지금 보이는 무기 시트·방향·열 (앵커 조회) */
  private shown: { def: SheetDef; dir: Facing; column: number; pivot: { x: number; y: number } } | null = null;
  private bodyAt: { dir: Facing; column: number } | null = null;

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
    const body = spriteLibrary.sheet('player', parsed.action);
    this.body = body;
    this.bodyAt = null;
    if (playing) {
      const cur = this.host.anims.currentFrame;
      if (!cur) return this.hide();
      // 파생 애니(구간 재생·반복)도 맞도록 텍스처 프레임 번호(row × frames + col)에서 열을 꺼낸다
      const fi = Number(cur.frame.name);
      column = body && Number.isFinite(fi) ? fi % body.frames : cur.index - 1;
    } else {
      const m = /#hold(\d+)/.exec(key!);
      column = m ? Number(m[1]) : 0;
    }
    this.bodyAt = { dir: parsed.dir, column };
    const id = gameState.weapon.id;
    for (const a of overlayActionsFor(parsed.action, id)) {
      const def = this.sheetOf(id, a);
      if (def) {
        // 무기 시트 하나가 휴대 모습을 대신한다 — v3 연격(carryHidden)은 빈 칼집까지 시트에 들어 있다
        this.carry = null;
        this.carryHidden = Boolean(def.carryHidden);
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
    const col0 = ca === 'idle' && bodyAction !== 'idle' ? 0 : column;
    const def = this.pickCarry(id, ca, drawn);
    this.carryHidden = false;
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

  /**
   * 휴대 시트 고르기: (뽑아 든 상태면 carry_drawn_* 먼저) 동작 → (달리기면 걷기) → idle.
   * 52라운드 임시 규칙: 먼저 **몸 시트와 도트 배율이 같은 것**만 찾고, 없을 때만 다른 배율 — v3 몸에 구 시트 '뽑아 든 칼'(4배 도트)이
   * 겹쳐 보이는 대신 v3 칼집 휴대를 보인다 (v3 carry_drawn 이 오면 자동으로 그것)
   */
  private pickCarry(id: string, ca: CarryAction, drawn: boolean): SheetDef | undefined {
    const names = drawn ? [carryDrawnAction, carryAction] : [carryAction];
    const acts: CarryAction[] = ca === 'run' ? ['run', 'walk', 'idle'] : ca === 'idle' ? ['idle'] : [ca, 'idle'];
    const tier = this.body ? artScale(this.body) : null;
    for (const strict of [true, false]) {
      if (!strict && tier === null) break;
      for (const name of names)
        for (const a of acts) {
          const def = this.sheetOf(id, name(a));
          if (def && (!strict || tier === null || artScale(def) === tier)) return def;
        }
    }
    return undefined;
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
    // 52라운드 v3: 무기 시트 좌표 = 몸 좌표 + playerFrameOffset → 원점 = 몸 피벗 + 오프셋 (휴대 폴백은 자기 피벗)
    const pv = place ? def.pivot : overlayPivot(def, this.body);
    this.shown = place ? null : { def, dir, column, pivot: pv };
    this.sprite.setOrigin(pv.x / def.frameWidth, pv.y / def.frameHeight);
    this.frame = frameAt(def, dir, column);
    this.action = action;
    this.sprite.setFrame(this.frame);
    // 50라운드: 새 2배 도트 무기 시트(pixelScale 1)는 0.5 배 — 몸 시트와 같은 화면 크기
    const k = artScale(def);
    if (place) {
      this.sprite.setScale(place.scale * k).setAngle(place.angle);
      this.sprite.setPosition(this.host.x + place.x, this.host.y + place.y);
    } else {
      this.sprite.setScale(k).setAngle(0);
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
    this.carryHidden = false;
    this.shown = null;
  }

  /**
   * 52라운드 v3 앵커 (월드 좌표): 몸 handAnchors 양손 · 무기 gripAnchors(없으면 무기 handAnchors 오른손) · bladeLocal.
   * 디버그·연출 정렬용 (판정에는 쓰지 않는다). 시트에 메모가 없으면 null
   */
  anchors(): {
    handR: { x: number; y: number } | null;
    handL: { x: number; y: number } | null;
    grip: { x: number; y: number } | null;
    blade: BladeLocal | null;
  } {
    const h = this.host;
    const at = (o: { x: number; y: number } | null) => (o ? { x: h.x + o.x, y: h.y + o.y } : null);
    const ba = this.bodyAt;
    const hands = this.body && ba ? handAt(this.body, ba.dir, ba.column) : null;
    const s = this.shown;
    const g = s ? gripAt(s.def, s.dir, s.column) : null;
    return {
      handR: at(hands && this.body ? anchorOffset(this.body, hands.handR) : null),
      handL: at(hands && this.body ? anchorOffset(this.body, hands.handL) : null),
      grip: at(g && s ? anchorOffset(s.def, g, s.pivot) : null),
      blade: s ? bladeAt(s.def, s.column) : null,
    };
  }
}
