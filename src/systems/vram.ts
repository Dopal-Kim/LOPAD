/**
 * 61라운드 P9 VRAM 실측 (디버그 `__lopad.vram()`). 순수 계산 `measureVram` + Phaser 텍스처 관리자 어댑터 `vramOfTextures`.
 * - 추정 바이트 = 고유 GPU 텍스처(소스)마다 폭 × 높이 × 4 (RGBA8, 밉맵 없음). 같은 GL 텍스처를 가리키는 키는 한 번만 센다.
 * - 같은 그림(이미지·캔버스)이 서로 다른 GL 텍스처로 두 번 올라간 경우는 `dupImages` 로 따로 보여 준다 (낭비 후보).
 * - 세지 않는 것: 캔버스 기본 프레임버퍼(1920×1080), 카메라 postFX·파이프라인 렌더 타깃, 브라우저 합성 버퍼.
 *   크롬 작업 관리자의 'GPU 메모리' 는 이것들과 디코딩 캐시까지 더한 값이라 이 추정보다 크다.
 */
import { VRAM } from '../core/Constants';

export interface VramSourceIn {
  width: number;
  height: number;
  /** GL 텍스처 식별 (같으면 한 번만 센다). 없으면 소스마다 따로 */
  gl?: unknown;
  /** 원본 이미지·캔버스 식별 (dupImages 용) */
  image?: unknown;
}

export interface VramTextureIn {
  key: string;
  sources: VramSourceIn[];
}

export interface VramReport {
  textures: number;
  /** 고유 GPU 텍스처 수 */
  uploads: number;
  bytes: number;
  mb: number;
  budgetMb: number;
  overBudget: boolean;
  /** 한 변이 VRAM.MAX_SIDE 를 넘는 텍스처 */
  over4096: { key: string; width: number; height: number }[];
  top: { key: string; width: number; height: number; mb: number }[];
  /** 분류별 MB (sheet:<이름 첫 토막> · variant(층 변형 @·색 교체 #) · tiles · border · dynamic · other) */
  byGroup: Record<string, number>;
  dupImages: { keys: string[]; mb: number }[];
  /** `all: true` 일 때만: 전체 목록 (큰 순) */
  all?: { key: string; group: string; width: number; height: number; mb: number }[];
}

const toMb = (b: number) => Math.round((b / (1024 * 1024)) * 100) / 100;

/** 텍스처 키 → 분류 */
export function vramGroup(key: string): string {
  if (key.startsWith('sheet_')) {
    if (/[@#]/.test(key)) return 'variant';
    const name = key.slice('sheet_'.length);
    return `sheet:${name.split('_')[0]}`;
  }
  if (key.startsWith('border_')) return 'border';
  if (key.startsWith('tile') || key.startsWith('json_tile')) return 'tiles';
  if (key.startsWith('__')) return 'builtin';
  // RenderTexture·DynamicTexture 는 UUID 키
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-/i.test(key)) return 'dynamic';
  return 'other';
}

export function measureVram(
  list: readonly VramTextureIn[],
  budgetBytes: number = VRAM.BUDGET_BYTES,
  opts: { all?: boolean } = {},
): VramReport {
  const seenGl = new Set<unknown>();
  const byImage = new Map<unknown, { keys: string[]; gls: Set<unknown>; bytes: number }>();
  const rows: { key: string; width: number; height: number; bytes: number }[] = [];
  const byGroup: Record<string, number> = {};
  const over: VramReport['over4096'] = [];
  let uploads = 0;
  for (const t of list) {
    let bytes = 0;
    let w = 0;
    let h = 0;
    for (const s of t.sources) {
      if (s.width > VRAM.MAX_SIDE || s.height > VRAM.MAX_SIDE)
        over.push({ key: t.key, width: s.width, height: s.height });
      w = Math.max(w, s.width);
      h = Math.max(h, s.height);
      const b = s.width * s.height * VRAM.BYTES_PER_TEXEL;
      if (s.image !== undefined && s.image !== null) {
        const e = byImage.get(s.image) ?? { keys: [], gls: new Set<unknown>(), bytes: b };
        e.keys.push(t.key);
        e.gls.add(s.gl ?? s);
        byImage.set(s.image, e);
      }
      if (s.gl !== undefined && s.gl !== null) {
        if (seenGl.has(s.gl)) continue;
        seenGl.add(s.gl);
      }
      uploads += 1;
      bytes += b;
    }
    if (bytes === 0) continue;
    rows.push({ key: t.key, width: w, height: h, bytes });
    const g = vramGroup(t.key);
    byGroup[g] = (byGroup[g] ?? 0) + bytes;
  }
  rows.sort((a, b) => b.bytes - a.bytes);
  const total = rows.reduce((a, r) => a + r.bytes, 0);
  const dupImages = [...byImage.values()]
    .filter((e) => e.gls.size > 1)
    .map((e) => ({ keys: e.keys, mb: toMb(e.bytes * (e.gls.size - 1)) }))
    .sort((a, b) => b.mb - a.mb);
  return {
    textures: list.length,
    uploads,
    bytes: total,
    mb: toMb(total),
    budgetMb: toMb(budgetBytes),
    overBudget: total > budgetBytes,
    over4096: over,
    top: rows.slice(0, VRAM.TOP).map((r) => ({ key: r.key, width: r.width, height: r.height, mb: toMb(r.bytes) })),
    byGroup: Object.fromEntries(
      Object.entries(byGroup)
        .sort((a, b) => b[1] - a[1])
        .map(([k, v]) => [k, toMb(v)]),
    ),
    dupImages,
    ...(opts.all
      ? {
          all: rows.map((r) => ({
            key: r.key,
            group: vramGroup(r.key),
            width: r.width,
            height: r.height,
            mb: toMb(r.bytes),
          })),
        }
      : {}),
  };
}

/** Phaser 텍스처 관리자에서 목록을 만든다 (구조만 쓰므로 Phaser import 없음) */
export interface TextureManagerLike {
  getTextureKeys(): string[];
  get(key: string): { source: { width: number; height: number; glTexture?: unknown; image?: unknown }[] };
}

export function vramOfTextures(tm: TextureManagerLike, opts: { all?: boolean; budgetBytes?: number } = {}): VramReport {
  // getTextureKeys 는 __DEFAULT·__MISSING·__WHITE 를 뺀다 — 작아서 무시
  const list: VramTextureIn[] = tm.getTextureKeys().map((key) => ({
    key,
    sources: tm.get(key).source.map((s) => ({ width: s.width, height: s.height, gl: s.glTexture, image: s.image })),
  }));
  return measureVram(list, opts.budgetBytes, opts);
}
