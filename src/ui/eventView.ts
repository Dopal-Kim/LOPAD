import type {
  UiEventIcon,
  UiEventScene,
  UiMenu,
  UiMenuLine,
  UiShopOffer,
  UiWaveSide,
  UiWorldSign,
} from '../contract/ui';
import { fill } from './fmt';
import { cleanLabel, menuHotkeys } from './menuView';
import { LOOP2F_TEXT, type Loop2FTextKey } from './textLoop2F';

/**
 * 62 루프 2 UI F (시스템 D 계약 P1-12·13·17, P2-10) — 사연 메뉴 · 결과 컷 · 장터 노점 카드 · 팻말 · 무리 방향의 순수 계산 (Phaser 없음).
 * 그리기는 MenuEvent.ts(메뉴) · HudLoop2F.ts(HUD).
 */

/** 아이콘 그림 — 키트 icons.png 의 프레임(`kit`) 또는 UI F 시트 event_icons.png 의 프레임(`event`) */
export type EventIconArt = { sheet: 'kit'; frame: string } | { sheet: 'event'; frame: string };

const KIT_FRAMES: Readonly<Record<string, string>> = {
  gold: 'icon_gold',
  potion: 'icon_potion',
  hp: 'icon_hp',
};
const EVENT_FRAMES: ReadonlySet<string> = new Set([
  'maxHp',
  'growth',
  'passive',
  'curse',
  'discount',
  'enemies',
  'diary',
  'unknown',
]);

/** 아이콘 종류 → 그림 (숨은 보상은 늘 '?' · 'sense' 는 1층 화면에 없는 말이라 '?' · 모르는 종류도 '?') */
export function eventIconArt(icon: Pick<UiEventIcon, 'kind' | 'hidden'>): EventIconArt {
  if (icon.hidden) return { sheet: 'event', frame: 'unknown' };
  const kit = KIT_FRAMES[icon.kind];
  if (kit) return { sheet: 'kit', frame: kit };
  if (EVENT_FRAMES.has(icon.kind)) return { sheet: 'event', frame: icon.kind };
  return { sheet: 'event', frame: 'unknown' };
}

/** 아이콘 옆 글 (숨은 보상은 그림이 이미 '?' 라 글 없음) */
export function eventIconText(icon: Pick<UiEventIcon, 'label' | 'hidden'>): string {
  return icon.hidden ? '' : (icon.label ?? '').trim();
}

/** 계약 값이 배열이면 쓸 수 있는 아이콘만 (모양이 틀린 것은 버린다) */
export function readIcons(v: unknown): UiEventIcon[] {
  if (!Array.isArray(v)) return [];
  return v.filter(
    (x): x is UiEventIcon => Boolean(x) && typeof x === 'object' && typeof (x as UiEventIcon).kind === 'string',
  );
}

export type Tx2F = (k: Loop2FTextKey) => string;
const defaultTx: Tx2F = (k) => LOOP2F_TEXT[k];

/** 사연·상인 메뉴 한 줄 */
export interface EventRow {
  key: string;
  hotkey: string;
  label: string;
  enabled: boolean;
  costs: UiEventIcon[];
  rewards: UiEventIcon[];
  /** 이름 아래 흐린 한 줄 — 아이콘이 없을 때의 설명 · 못 고르는 까닭 (아이콘을 그리면 detail 은 숨긴다) */
  note: string;
}

/** 사연·상인 메뉴 한 쪽 */
export interface EventPage {
  title: string;
  /** 초상 옆 이름표 (제목과 같으면 '') */
  speaker: string;
  portrait: { key: string; frame: string | number } | null;
  /** 첫 마디 — speech 면 말하는 이의 말(따옴표), narration 이면 지문 */
  greet: string;
  greetKind: 'speech' | 'narration';
  intro: string[];
  /** footer 중 intro 에 없는 줄 (다음 각성 미리보기 등) */
  extra: string[];
  pick: string;
  costHead: string;
  gainHead: string;
  /** 어느 줄이라도 대가·보상 아이콘이 있나 (없으면 아이콘 칸을 그리지 않는다) */
  hasIcons: boolean;
  rows: EventRow[];
  hint: string;
}

/** 사연(`event` 머리가 있는 메뉴) · 상인과 말하기(`shopTalk`) 를 이 틀로 그리나 */
export function isEventPageMenu(m: Pick<UiMenu, 'id'> & { event?: unknown; speaker?: unknown }): boolean {
  if (m.id === 'event') return Boolean(m.event && typeof m.event === 'object');
  return m.id === 'shopTalk';
}

/** 라벨 끝 ' · 전표 15' 처럼 가격을 적은 마디를 뗀다 (가격은 전표 아이콘으로 따로 그린다) */
export function stripPrice(label: string, amount: number): string {
  const parts = label.split(' · ');
  if (parts.length < 2) return label;
  const n = String(amount);
  const last = parts[parts.length - 1];
  if (!new RegExp(`(^|\\D)${n}(\\D|$)`).test(last)) return label;
  return parts.slice(0, -1).join(' · ');
}

/** 줄 하나 → 표 한 줄 */
function rowOf(l: UiMenuLine, hotkey: string): EventRow {
  const costs = readIcons(l.costs);
  const rewards = readIcons(l.rewards);
  let label = cleanLabel(l.label);
  // 상인 줄(다시 진열 등): 가격을 대가 칸 전표 아이콘으로
  if (l.price && l.price.kind === 'gold' && l.price.amount > 0 && !costs.some((c) => c.kind === 'gold')) {
    label = stripPrice(label, l.price.amount);
    costs.unshift({ kind: 'gold', amount: l.price.amount, label: l.price.label });
  }
  const enabled = l.enabled && !l.soldOut && !l.locked;
  const icons = costs.length + rewards.length > 0;
  const detail = (l.detail ?? '').trim();
  const note = !enabled ? detail : icons ? '' : detail;
  return { key: l.key, hotkey, label, enabled, costs, rewards, note };
}

/** 메뉴 → 쪽 (event 머리가 없으면 상인 꼴: 제목 = 말하는 이 · 첫 마디 = footer) */
export function eventPage(m: UiMenu, tx: Tx2F = defaultTx): EventPage {
  const ev = (m.event ?? null) as UiEventScene | null;
  const heads = ev?.heads ?? {};
  const head = (k: 'costHead' | 'gainHead' | 'pick'): string => heads[k] || tx(k);
  const hk = menuHotkeys(m.lines.map((l) => l.key));
  const rows = m.lines.map((l, i) => rowOf(l, hk[i] || l.key));
  const title = ev?.name || m.title || '';
  const speakerRaw = (ev?.speaker ?? m.speaker ?? '').trim();
  const speaker = speakerRaw && speakerRaw !== title ? speakerRaw : '';
  const intro = ev ? ev.intro.filter((s) => s.trim().length > 0) : [];
  const footerLines = (m.footer ?? '')
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean);
  // 사연: footer 는 설명을 다시 담아 온다 — 설명에 없는 줄만 덧붙인다. 상인: footer 가 첫 마디
  const extra = ev ? footerLines.filter((s) => !intro.includes(s)) : [];
  const greet = ev ? (ev.greet ?? '').trim() : footerLines.join(' ');
  const greetKind: 'speech' | 'narration' = ev ? (ev.speaker ? 'speech' : 'narration') : 'speech';
  const portrait = ev?.portrait && typeof ev.portrait.key === 'string' && ev.portrait.key ? ev.portrait : null;
  const cancel = m.cancelKey ? m.lines.find((l) => l.key === m.cancelKey) : undefined;
  const keys = rows.filter((r) => r.key !== m.cancelKey).map((r) => r.hotkey);
  if (cancel) keys.push(hk[m.lines.indexOf(cancel)] || cancel.key);
  let hint = fill(tx('eventHint'), { keys: keys.join('·') });
  if (cancel) hint += fill(tx('eventHintCancel'), { label: cleanLabel(cancel.label) });
  return {
    title,
    speaker,
    portrait,
    greet,
    greetKind,
    intro,
    extra,
    pick: head('pick'),
    costHead: head('costHead'),
    gainHead: head('gainHead'),
    hasIcons: rows.some((r) => r.costs.length + r.rewards.length > 0),
    rows,
    hint,
  };
}

/** 첫 마디 글 (말이면 「」로 감싼다 — 이미 감쌌으면 그대로) */
export function greetText(p: Pick<EventPage, 'greet' | 'greetKind'>): string {
  const g = p.greet.trim();
  if (!g) return '';
  if (p.greetKind === 'narration' || /^[「“"']/.test(g)) return g;
  return `「${g}」`;
}

// ---- 장터 노점 카드

export interface ShopCardView {
  name: string;
  /** 한 줄 (조건 → 행동, 수치 없음) */
  line: string;
  /** 희귀도 칸 수 (유품만, 0 = 없음) · 단계·태그 글 */
  rarityRank: number;
  meta: string;
  /** 값 (전표 아이콘 옆 수치, 0 = 값 없음) · 낼 수 있나 */
  price: number;
  affordable: boolean;
  /** 아래 줄: '[E] 산다' 또는 못 사는 까닭 · 팔렸다 */
  action: string;
  usable: boolean;
  sold: boolean;
  /** 그림: 유품 그림 키(128) · 물건 시트 키·프레임(80×96) · 없음 */
  art: { kind: 'relic'; key: string } | { kind: 'item'; key: string; frame: string | number } | null;
}

const RANK: Readonly<Record<string, number>> = { common: 1, rare: 2, epic: 3, legendary: 4 };

export function shopCardView(
  o: UiShopOffer,
  tagName: (t: string) => string = (t) => t,
  tx: Tx2F = defaultTx,
): ShopCardView {
  const l = o.line;
  const r = l.relic;
  const sold = Boolean(l.soldOut);
  const price = l.price && l.price.kind === 'gold' ? Math.max(0, Math.round(l.price.amount)) : 0;
  const name = r?.name || cleanLabel(l.label);
  const line = (r?.line || l.detail || '').trim();
  const meta = r ? [r.levelText, r.tag ? tagName(r.tag) : ''].filter(Boolean).join(' · ') : '';
  const rarity = r?.rarity ?? l.rarity;
  const action = sold
    ? tx('stallSold')
    : o.usable
      ? fill(tx('stallBuy'), { key: o.buyKey || 'E' })
      : (o.reasonText || '').trim();
  const art: ShopCardView['art'] = r?.iconKey
    ? { kind: 'relic', key: r.iconKey }
    : o.icon && o.icon.key
      ? { kind: 'item', key: o.icon.key, frame: o.icon.frame }
      : null;
  return {
    name,
    line,
    rarityRank: rarity ? (RANK[rarity] ?? 0) : 0,
    meta,
    price,
    affordable: l.price ? l.price.affordable !== false : true,
    action,
    usable: o.usable && !sold,
    sold,
    art,
  };
}

/** 카드 상자 자리 (물건 윗변 가운데 위 · 화면 밖으로 나가지 않게). 꼬리 x 는 물건 쪽을 가리킨다 */
export function shopCardPos(
  anchor: { x: number; y: number },
  w: number,
  h: number,
  screenW: number,
  screenH: number,
  margin: number,
  gap: number,
): { x: number; y: number; tailX: number; below: boolean } {
  const x = Math.round(Math.min(Math.max(anchor.x - w / 2, margin), screenW - margin - w));
  let y = Math.round(anchor.y - gap - h);
  let below = false;
  // 위에 자리가 없으면 물건 아래로
  if (y < margin) {
    y = Math.round(Math.min(anchor.y + gap, screenH - margin - h));
    below = true;
  }
  const tailX = Math.round(Math.min(Math.max(anchor.x, x + 8), x + w - 8));
  return { x, y, tailX, below };
}

// ---- 팻말

/** 팻말 글 두 줄 (값이 없으면 이름만) · 다시 그릴 때를 알리는 표지 */
export function signLines(s: Pick<UiWorldSign, 'title' | 'value'>): { title: string; value: string; sig: string } {
  const title = (s.title ?? '').trim();
  const value = (s.value ?? '').trim();
  return { title, value, sig: `${title}\u0001${value}` };
}

// ---- 무리 들어오는 쪽

export type EdgeSide = 'north' | 'south' | 'east' | 'west';

/** 들어오는 쪽 → 화살표를 그릴 가장자리 (flank = 양옆 · around = 사방 · 모르면 없음) */
export function waveEdges(side: UiWaveSide | string | null | undefined): EdgeSide[] {
  switch (side) {
    case 'north':
    case 'south':
    case 'east':
    case 'west':
      return [side];
    case 'flank':
      return ['west', 'east'];
    case 'around':
      return ['north', 'east', 'south', 'west'];
    default:
      return [];
  }
}

/** 가장자리 화살표 자리·방향 (밖을 가리킨다 — 그쪽에서 온다). 위쪽은 알림 줄 위 끝보다 위 */
export function edgeArrow(
  side: EdgeSide,
  screenW: number,
  screenH: number,
  inset: number,
  topY: number,
  bottomInset: number,
): { x: number; y: number; angle: number } {
  switch (side) {
    case 'north':
      return { x: Math.round(screenW / 2), y: topY, angle: -Math.PI / 2 };
    case 'south':
      return { x: Math.round(screenW / 2), y: screenH - bottomInset, angle: Math.PI / 2 };
    case 'east':
      return { x: screenW - inset, y: Math.round(screenH / 2), angle: 0 };
    case 'west':
      return { x: inset, y: Math.round(screenH / 2), angle: Math.PI };
  }
}

/** 세로 표 고름 자리 옮기기 (↑↓·W·S, 끝에서 돌아간다 — ←→ 는 움직이지 않는다). CardRow 의 nav 로 넘긴다 */
export function listFocusMove(idx: number, n: number, key: string): number {
  if (n <= 0) return idx;
  const up = key === 'ArrowUp' || key === 'w' || key === 'W';
  const down = key === 'ArrowDown' || key === 's' || key === 'S';
  if (up) return (Math.min(idx, n - 1) - 1 + n) % n;
  if (down) return (Math.min(idx, n - 1) + 1) % n;
  return idx;
}

/** 초상 그림 프레임 (잘라 낸 아틀라스면 trim = 실제 칸 안 그림 자리) */
export interface PortraitFrame {
  realW: number;
  realH: number;
  trimX: number;
  trimY: number;
  w: number;
  h: number;
}

/**
 * 초상 놓기: 그림(잘린 부분) 가로 가운데 · 칸에 다 들면 아래 맞춤, 넘치면 머리를 위에 맞추고 아래(발)를 자른다.
 * 반환 = 이미지 왼쪽 위(origin 0) · 칸 밖을 자르는 crop (프레임 실제 크기 좌표 — Phaser setCrop)
 */
export function portraitFit(
  f: PortraitFrame,
  box: { x: number; y: number; w: number; h: number },
  scale: number,
  pad: number,
): { x: number; y: number; crop: { x: number; y: number; w: number; h: number } } {
  const x = Math.round(box.x + box.w / 2 - (f.trimX + f.w / 2) * scale);
  const fits = f.h * scale <= box.h - pad * 2;
  const y = fits
    ? Math.round(box.y + box.h - pad - (f.trimY + f.h) * scale)
    : Math.round(box.y + pad - f.trimY * scale);
  const cx0 = Math.max(0, Math.ceil((box.x - x) / scale));
  const cy0 = Math.max(0, Math.ceil((box.y - y) / scale));
  const cx1 = Math.min(f.realW, Math.floor((box.x + box.w - x) / scale));
  const cy1 = Math.min(f.realH, Math.floor((box.y + box.h - y) / scale));
  return { x, y, crop: { x: cx0, y: cy0, w: Math.max(0, cx1 - cx0), h: Math.max(0, cy1 - cy0) } };
}
