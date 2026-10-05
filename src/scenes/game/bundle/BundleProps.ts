/**
 * 60라운드 2차 묶음 전투장 소품 (계약 art §22 `structures/v3/*` — challenge_banner · event_* · clue_*): 그림(StructureView —
 * 상태 프레임·광원)과 가까이 가면 여는 메뉴(이벤트·단서·지도 장수) / E 로 쓰는 소품(도전 성소 깃발 — 계약 §14.10 warFlag).
 * 구조물 시스템(47라운드)과는 따로 둔다 — 계약 UiStructureKind 에 없는 소품(이벤트·단서·지도 장수)은 상호작용 안내 대신
 * '가까이 가면 메뉴'(상점 칸과 같은 방식)로 연다. 시트가 없으면 플레이스홀더 도형(StructureView 기본).
 */
import Phaser from 'phaser';
import { BUNDLE_FX, TILE } from '../../../core/Constants';
import type { UiInteractable } from '../../../contract/ui';
import { worldToLogicalScreen } from '../../../systems/display';
import { StructureView } from '../../../world/StructureView';
import type { Game } from '../../Game';

export interface PropSpec {
  id: string;
  /** structures/v3 시트 id (없으면 플레이스홀더) */
  sheet: string | null;
  label: string;
  /** 월드 발 위치 (px) */
  x: number;
  y: number;
  /** 가까이 가면 (메뉴 소품) — E 소품이면 null */
  onNear?: () => void;
  /** E 소품: 계약 UiInteractable (지금은 warFlag 만) */
  interact?: {
    kind: 'warFlag';
    name: string;
    action: string;
    actionKey: string;
    usable: () => boolean;
    use: () => void;
  };
  /** 상태 (시트 states) */
  state?: string;
}

interface Prop {
  spec: PropSpec;
  view: StructureView;
  /** 메뉴 소품: 멀어졌다 다시 들어와야 다시 연다 */
  armed: boolean;
  gone: boolean;
}

export class BundleProps {
  private readonly list: Prop[] = [];

  constructor(private readonly g: Game) {}

  add(spec: PropSpec): void {
    const half = TILE / 2;
    const view = new StructureView(this.g, {
      sheet: spec.sheet ?? '',
      rect: new Phaser.Geom.Rectangle(spec.x - half, spec.y - TILE, TILE, TILE),
      color: BUNDLE_FX.PROP_COLOR,
      label: spec.label,
      floor: false,
    });
    if (spec.state) view.setState(spec.state);
    this.list.push({ spec, view, armed: true, gone: false });
  }

  setState(id: string, state: string): void {
    this.find(id)?.view.setState(state);
  }

  remove(id: string): void {
    const p = this.find(id);
    if (!p) return;
    p.gone = true;
    p.view.destroy();
  }

  has(id: string): boolean {
    return Boolean(this.find(id));
  }

  private find(id: string): Prop | undefined {
    return this.list.find((p) => p.spec.id === id && !p.gone);
  }

  private dist(p: Prop): number {
    const pl = this.g.player;
    return Math.hypot(pl.x - p.spec.x, pl.y - p.spec.y);
  }

  /** 가장 가까운 E 소품 (반경 안) */
  private nearestInteract(): Prop | null {
    let best: Prop | null = null;
    let bd = BUNDLE_FX.INTERACT_TILES * TILE;
    for (const p of this.list) {
      if (p.gone || !p.spec.interact) continue;
      const d = this.dist(p);
      if (d <= bd) {
        bd = d;
        best = p;
      }
    }
    return best;
  }

  /** 매 프레임: 메뉴 소품 가까이 가면 열기 · E 소품 E 키. busy = 메뉴·연출 중 */
  update(interactPressed: boolean, busy: boolean): void {
    const near = BUNDLE_FX.NEAR_TILES * TILE;
    for (const p of this.list) {
      if (p.gone || !p.spec.onNear) continue;
      const inside = this.dist(p) <= near;
      if (!inside) p.armed = true;
      else if (p.armed && !busy) {
        p.armed = false;
        p.spec.onNear();
      }
    }
    const it = this.nearestInteract();
    if (it && interactPressed && !busy && it.spec.interact!.usable()) it.spec.interact!.use();
  }

  /** 계약 §9.1·§14.10 상호작용 안내 (E 소품만) */
  interactable(roomId: string): UiInteractable | null {
    const p = this.nearestInteract();
    if (!p?.spec.interact) return null;
    const I = p.spec.interact;
    const usable = I.usable();
    const s = worldToLogicalScreen(this.g.cameras.main, p.spec.x, Math.min(p.view.topY, p.spec.y - TILE));
    return {
      id: p.spec.id,
      kind: I.kind,
      name: I.name,
      roomId,
      key: 'E',
      actionKey: I.actionKey,
      action: I.action,
      cost: null,
      hold: null,
      usable,
      reason: usable ? null : 'notReady',
      reasonText: usable ? '' : BUNDLE_FX.NOT_READY_TEXT,
      screen: { x: Math.round(s.x), y: Math.round(s.y) },
    };
  }

  destroy(): void {
    for (const p of this.list) if (!p.gone) p.view.destroy();
    this.list.length = 0;
  }
}
