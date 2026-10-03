/**
 * E형 상호작용 (계약 §9.1·9.3): 1.5칸 안 가장 가까운 것 하나를 안내 · 막힌 사유 · 비용 표시 · 실행(종류별 핸들러로) ·
 * 묘 길게 누르기 · 화면 위치. 메뉴 동안 입력 잠금은 StructureSystem.inputLocked.
 */
import Phaser from 'phaser';
import { TILE } from '../../core/Constants';
import { worldToLogicalScreen } from '../display';
import { gameState } from '../../core/GameState';
import type { UiCost, UiInteractBlockReason, UiInteractable } from '../../contract/ui';
import type { InputState } from '../InputSystem';
import { INTERACT_KINDS, STRUCTURE_RULES, STRUCTURE_TEXT, num, txt } from './data';
import { cardStake } from './rules';
import type { Inst, StructureCore } from './core';
import type { GambleKinds } from './kinds/gambleKinds';
import type { ServiceKinds } from './kinds/serviceKinds';

/** 묘 길게 누르기 기본 시간 (데이터 holdMs 가 없을 때) */
const DEFAULT_HOLD_MS = 2000;

export class Interaction {
  private nearest: Inst | null = null;
  private reason: UiInteractBlockReason | null = null;
  holdMs = 0;
  /** 다음 update 에서 E 를 누른 것으로 친다 (디버그) */
  debugPress = false;

  constructor(
    private readonly c: StructureCore,
    private readonly service: ServiceKinds,
    private readonly gamble: GambleKinds,
  ) {}

  get nearestId(): string | null {
    return this.nearest?.id ?? null;
  }

  get nearestReason(): UiInteractBlockReason | null {
    return this.reason;
  }

  update(input: InputState, delta: number): void {
    const pc = this.c.host.player.body.center;
    const range = STRUCTURE_RULES.interactRangePx;
    let best: Inst | null = null;
    let bestD = Infinity;
    for (const s of this.c.list) {
      if (!INTERACT_KINDS.includes(s.kind) || this.exhausted(s)) continue;
      const r = this.rectOf(s);
      const nx = Phaser.Math.Clamp(pc.x, r.left, r.right);
      const ny = Phaser.Math.Clamp(pc.y, r.top, r.bottom);
      const d = Math.hypot(pc.x - nx, pc.y - ny);
      if (d <= range && d < bestD) {
        bestD = d;
        best = s;
      }
    }
    if (best !== this.nearest) this.holdMs = 0;
    this.nearest = best;
    this.reason = best ? this.reasonFor(best) : null;
    const pressed = input.interactPressed || this.debugPress;
    this.debugPress = false;
    if (!best) return;
    // C3 묘: 길게 누르기 (이동하면 0)
    if (best.kind === 'grave') {
      const moving = input.moveX !== 0 || input.moveY !== 0;
      const held = input.interactHeld || pressed;
      const need = best.def.holdMs ?? DEFAULT_HOLD_MS;
      if (this.reason === null && held && !moving) {
        this.holdMs += pressed && !input.interactHeld ? need : delta;
        if (this.holdMs >= need) {
          this.holdMs = 0;
          this.service.openGraveMenu(best);
        }
      } else this.holdMs = 0;
      return;
    }
    if (!pressed || this.reason !== null) return;
    this.activate(best);
  }

  /** E 판정 영역: 투견 링은 판돈 깃대(시트 flagpost) 둘레, 그 외 발판 */
  rectOf(s: Inst): Phaser.Geom.Rectangle {
    if (s.kind === 'dogRing') {
      const v = s.views[0];
      const fp = v.def?.flagpost;
      const w = fp ? v.frameToWorld(fp.x, fp.y) : null;
      if (w) return new Phaser.Geom.Rectangle(w.x - TILE / 2, w.y - TILE / 2, TILE, TILE);
      return new Phaser.Geom.Rectangle(s.rect.centerX - TILE / 2, s.rect.y, TILE, TILE);
    }
    return s.rect;
  }

  /** 더 할 수 있는 행동이 없음 → 안내·미니맵 점에서 빠진다 */
  exhausted(s: Inst): boolean {
    if (s.state === 'used' || s.state === 'broken') return true;
    const d = s.def;
    switch (s.kind) {
      case 'ledger':
        return s.loans >= num(d, 'loansPerFloor') && this.c.debt <= 0;
      case 'counter':
        return s.cups >= num(d, 'cups');
      case 'cardTable':
        return s.round >= num(d, 'maxRounds');
      case 'exchange':
        return s.bloodUses >= num(d, 'bloodLimit') && s.lifeUses >= num(d, 'lifeLimit');
      default:
        return false;
    }
  }

  private reasonFor(s: Inst): UiInteractBlockReason | null {
    const c = this.c;
    if (c.host.isBusy() || c.ring || c.cardFight) return 'busy';
    if (c.host.director.inCombat) return 'combat';
    const d = s.def;
    switch (s.kind) {
      case 'chest':
        return gameState.gold < this.service.chestCost(s) ? 'gold' : null;
      case 'campfire':
        return c.embers <= 0 ? 'notReady' : gameState.hp >= gameState.maxHp ? 'full' : null;
      case 'agingBarrel': {
        if (s.agingAt === null) return gameState.potions < num(d, 'potionIn') ? 'potion' : null;
        return this.service.agingReady(s) ? null : 'notReady';
      }
      case 'counter':
        return gameState.gold < num(d, 'cupPrice') ? 'gold' : c.drunk >= num(d, 'maxLevel') ? 'full' : null;
      case 'cardTable':
        return gameState.gold < cardStake(s.round + 1, this.gamble.cardParams(d)) ? 'gold' : null;
      case 'dogRing':
        return gameState.gold < num(d, 'stake') ? 'gold' : null;
      case 'pawn':
        return this.gamble.pawnLines(s).length === 0 ? 'limit' : null;
      default:
        return null;
    }
  }

  private costFor(s: Inst): UiCost | null {
    const c = this.c;
    const d = s.def;
    const gold = (n: number): UiCost => ({
      kind: 'gold',
      amount: n,
      label: `${n}${STRUCTURE_TEXT.goldUnit}`,
      affordable: gameState.gold >= n,
    });
    switch (s.kind) {
      case 'chest':
        return gold(this.service.chestCost(s));
      case 'counter':
        return gold(num(d, 'cupPrice'));
      case 'cardTable':
        return gold(cardStake(s.round + 1, this.gamble.cardParams(d)));
      case 'dogRing':
        return gold(num(d, 'stake'));
      case 'agingBarrel':
        if (s.agingAt !== null) return null;
        return {
          kind: 'potion',
          amount: num(d, 'potionIn'),
          label: `잔의 독주 ${num(d, 'potionIn')}`,
          affordable: gameState.potions >= num(d, 'potionIn'),
        };
      case 'campfire':
        return c.embers > 0
          ? { kind: 'none', amount: c.embers, label: txt(d, 'costLabel', { n: c.embers }), affordable: true }
          : null;
      default:
        return null;
    }
  }

  private actionOf(s: Inst): { key: string; text: string } {
    const d = s.def;
    if (s.kind === 'agingBarrel') {
      if (s.agingAt === null) return { key: d.text.putActionKey, text: d.text.putAction };
      if (this.service.agingReady(s)) return { key: d.text.takeActionKey, text: d.text.takeAction };
      return { key: d.text.putActionKey, text: d.text.waitAction };
    }
    return { key: d.text.actionKey ?? `${s.kind}.use`, text: d.text.action ?? '' };
  }

  /** E 즉시 실행 또는 메뉴 */
  private activate(s: Inst): void {
    const sv = this.service;
    const gb = this.gamble;
    switch (s.kind) {
      case 'chest':
        return sv.openChest(s);
      case 'campfire':
        return sv.useCampfire(s);
      case 'agingBarrel':
        return sv.useAging(s);
      case 'ledger':
        return sv.openLedger(s);
      case 'counter':
        return sv.openCounter(s);
      case 'dogRing':
        return gb.startRing(s);
      case 'cardTable':
        return gb.openCards(s);
      case 'exchange':
        return gb.openExchange(s, (x) => this.exhausted(x));
      case 'pawn':
        return gb.openPawn(s);
    }
  }

  /** 스냅샷 안내 (계약 §9.1): 이름·행동·비용·막힌 사유·길게 누르기 진행·게임 캔버스 위치 */
  interactable(): UiInteractable | null {
    const s = this.nearest;
    if (!s || !s.views[0]) return null;
    const reason = this.reason;
    const cam = this.c.host.scene.cameras.main;
    const ir = this.rectOf(s);
    const wx = ir.centerX;
    const wy = s.kind === 'dogRing' ? ir.top : Math.min(s.views[0].topY, s.rect.top);
    // 게임 화면 논리 픽셀 (카메라 스크롤·배율 반영, 960×540 기준 — 52라운드 캔버스 1920×1080 이어도 논리 좌표)
    const { x: sx, y: sy } = worldToLogicalScreen(cam, wx, wy);
    const action = this.actionOf(s);
    const hold = s.kind === 'grave' ? (s.def.holdMs ?? DEFAULT_HOLD_MS) : 0;
    return {
      id: s.id,
      kind: s.kind,
      name: s.def.name,
      roomId: s.roomId,
      key: STRUCTURE_RULES.interactKey,
      actionKey: action.key,
      action: action.text,
      cost: this.costFor(s),
      hold: hold > 0 ? { durationMs: hold, progress: Phaser.Math.Clamp(this.holdMs / hold, 0, 1) } : null,
      usable: reason === null,
      reason,
      reasonText: reason ? STRUCTURE_TEXT.reasons[reason] : '',
      screen: { x: Math.round(sx), y: Math.round(sy) },
    };
  }
}
