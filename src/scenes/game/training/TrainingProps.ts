/**
 * 61 단계 6 (계약 art §28) 수련장 소품 — `structures/v3/training_*` (무기 걸이 4 · 과제 표지판 · 도장 판 · 연습 깃발).
 * 수련장 방에서만 지연 로드(작은 시트 7장)하고 StructureView 로 그린다. 상태: 걸이 idle·active·taken · 표지판 active → done ·
 * 도장 판 blank → stamp(1회) → stamped · 깃발 wave → reached. 판정 없음(장식 — 과제 판정은 TrainingMode).
 */
import Phaser from 'phaser';
import { TILE } from '../../../core/Constants';
import type { TrainingRoomDef } from '../../../data/training';
import { queueRequests, sheetListed } from '../../../systems/sprites/sheetLoader';
import { STRUCTURE_ACTION } from '../../../systems/sprites/spriteActions';
import { StructureView } from '../../../world/StructureView';
import type { Game } from '../../Game';

/** 방 가운데 기준 자리 (칸) — 표지판·도장 판은 위쪽 벽 앞, 걸이는 왼쪽 위 */
const AT = {
  sign: [-2, -4] as const,
  board: [1, -4] as const,
  rack: [-6, -4] as const,
};
/** 도장 찍힘 한 번(stamp) 뒤 stamped 로 */
const STAMP_MS = 600;

type PropKey = 'sign' | 'board' | 'rack' | 'flag';

export class TrainingProps {
  private views = new Map<PropKey, StructureView>();
  private pending: Partial<Record<PropKey, string>> = {};
  private alive = true;

  constructor(
    private readonly g: Game,
    private readonly room: TrainingRoomDef,
    private readonly center: () => { x: number; y: number },
  ) {}

  /** 시트를 받아 소품을 놓는다. flagAt = 표식 자리(걸음과 숨) */
  load(opts: { stamped: boolean; flagAt: { x: number; y: number } | null }): void {
    const sheets: Record<PropKey, string | null> = {
      sign: 'training_task_sign',
      board: 'training_stamp_board',
      rack: this.room.weapon ? `training_rack_${this.room.weapon}` : null,
      flag: opts.flagAt ? 'training_flag' : null,
    };
    const reqs = Object.values(sheets)
      .filter((n): n is string => Boolean(n))
      .map((name) => ({ category: 'structures' as const, name, action: STRUCTURE_ACTION }))
      .filter((r) => sheetListed(r));
    const place = () => {
      if (!this.alive || !this.g.scene.isActive()) return;
      const c = this.center();
      const at = (t: readonly [number, number]) => ({ x: c.x + t[0] * TILE, y: c.y + t[1] * TILE });
      if (sheets.sign) this.put('sign', sheets.sign, at(AT.sign), 2, opts.stamped ? 'done' : 'active');
      if (sheets.board) this.put('board', sheets.board, at(AT.board), 1, opts.stamped ? 'stamped' : 'blank');
      if (sheets.rack) this.put('rack', sheets.rack, at(AT.rack), 2, 'taken');
      if (sheets.flag && opts.flagAt) this.put('flag', sheets.flag, opts.flagAt, 1, 'wave', true);
      for (const [k, s] of Object.entries(this.pending)) this.views.get(k as PropKey)?.setState(s);
      this.pending = {};
    };
    if (reqs.length === 0) return;
    if (queueRequests(this.g, reqs, place) && !this.g.load.isLoading()) this.g.load.start();
  }

  private put(
    key: PropKey,
    sheet: string,
    at: { x: number; y: number },
    w: number,
    state: string,
    floor = false,
  ): void {
    const rect = new Phaser.Geom.Rectangle(at.x - (w * TILE) / 2, at.y - TILE / 2, w * TILE, TILE);
    const view = new StructureView(this.g, { sheet, rect, color: '#8a6a40', label: '', floor, unlit: true });
    view.setState(state);
    this.views.set(key, view);
  }

  /** 상태 바꾸기 (아직 안 놓였으면 놓일 때) */
  set(key: PropKey, state: string): void {
    const v = this.views.get(key);
    if (v) v.setState(state);
    else this.pending[key] = state;
  }

  /** 도장: 표지판 done · 도장 판 stamp → stamped */
  stamp(): void {
    this.set('sign', 'done');
    this.set('board', 'stamp');
    this.g.time.delayedCall(STAMP_MS, () => this.alive && this.set('board', 'stamped'));
  }

  destroy(): void {
    this.alive = false;
    for (const v of this.views.values()) v.destroy();
    this.views.clear();
  }
}
