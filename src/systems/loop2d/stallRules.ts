/**
 * 62 루프 2 시스템 D (P1-13) 장터 노점 순수 규칙 (Phaser 의존 없음 — 테스트): 줄 → 물건 카드 id · 물건 그림 · 노점 자리.
 */
import { SHOP_STALL, TILE } from '../../core/Constants';
import type { UiMenuLine } from '../../contract/ui';
import { SHOP_GOODS_SHEET } from '../bundle2/bundleSheets';

/** 줄 → 물건 카드 id (63 팩 shop.items 키) — 시스템 C 품목 id 를 이 표로 잇는다 */
export function cardIdOf(
  line: Pick<UiMenuLine, 'key' | 'group'>,
  fixedIds: readonly string[],
  displayId?: string,
): string {
  if (line.key === 'chest') return 'chest';
  // 시스템 C 품목 줄 (ShopMenu `g:<id>` — 먹물 한 병 · 풀무질 한 번)
  if (line.key.startsWith('g:')) return line.key.slice(2);
  const id = line.group === 'display' ? (displayId ?? '') : (fixedIds[Number(line.key) - 1] ?? line.key);
  if (/reroll/i.test(id)) return 'inkBottle';
  if (/temper/i.test(id)) return 'bellows';
  if (/fire/i.test(id)) return 'fireBottle';
  return id;
}

/** 물건 그림 (시트 이름 · 행) — 카드 id 로 */
export function goodsArtOf(cardId: string, passive: boolean): { sheet: string; row: string | null } | null {
  if (passive || cardId === 'chest') return { sheet: SHOP_GOODS_SHEET, row: 'relic_bundle' };
  if (cardId === 'bellows') return { sheet: SHOP_GOODS_SHEET, row: 'temper' };
  if (cardId === 'inkBottle') return { sheet: SHOP_GOODS_SHEET, row: 'reroll' };
  // 62 루프 2 F (art §31-11): 국밥 = shop_goods heal 행 (프레임 12~15 — 시트에 그 행이 없으면 ShopStalls 가 첫 행으로)
  if (cardId === 'heal') return { sheet: SHOP_GOODS_SHEET, row: 'heal' };
  if (cardId === 'potion') return { sheet: 'potion', row: null };
  if (cardId === 'fireBottle') return { sheet: 'fire_bottle', row: null };
  return null;
}

/** 노점 자리 (상점 칸 왼쪽 위 타일 기준 — 칸 아래 한 줄, 넘치면 두 줄) */
export function stallPositions(shop: { x: number; y: number }, n: number): { x: number; y: number }[] {
  const S = SHOP_STALL;
  const out: { x: number; y: number }[] = [];
  const perRow = Math.max(1, S.PER_ROW);
  for (let i = 0; i < n; i++) {
    const row = Math.floor(i / perRow);
    const inRow = Math.min(perRow, n - row * perRow);
    const col = i % perRow;
    const cx = (shop.x + 1) * TILE + (col - (inRow - 1) / 2) * S.GAP_TILES * TILE;
    const cy = (shop.y + 2 + S.ROW_TILES + row * S.ROW_GAP_TILES) * TILE;
    out.push({ x: Math.round(cx), y: Math.round(cy) });
  }
  return out;
}
