import type {
  UiBuildState,
  UiConsumableSlot,
  UiCurse,
  UiNodeGrade,
  UiNodeGraded,
  UiNodeTrial,
  UiPerfectSuccess,
  UiSnapshot,
  UiTagId,
  UiTagSetChanged,
  UiTagState,
} from '../contract/ui';
import { fill } from './fmt';
import { R60_TEXT, TAG_NAME, type R60TextKey } from './textBuild';

/**
 * 57·60라운드 계약 §14.1~14.4·§14.8·§14.10·§14.11 순수 계산 (Phaser 없음 — 단위 테스트 대상).
 * 문구 틀은 `R60_TEXT`(텍스트 팩 조회 없이 기본값 — 씬 쪽이 `r60Text` 로 바꿔 끼울 수 있게 `tx` 를 받는다).
 */
export type Tx = (key: R60TextKey) => string;
const defaultTx: Tx = (k) => R60_TEXT[k];

/** 스냅샷에 build 가 없을 때(옛 스냅샷·디버그 덮어쓰기) */
export const EMPTY_BUILD: UiBuildState = { tags: [], dualTraits: [], curse: null };

export function buildOf(s: { build?: UiBuildState | null }): UiBuildState {
  const b = s.build;
  if (!b) return EMPTY_BUILD;
  return { tags: b.tags ?? [], dualTraits: b.dualTraits ?? [], curse: b.curse ?? null };
}

/** 태그 이름: 스냅샷 build.tags 의 이름 → 계약 자리표시 이름 → id */
export function tagName(id: UiTagId | string, build?: UiBuildState | null): string {
  const t = build?.tags.find((x) => x.id === id);
  if (t?.name) return t.name;
  return (TAG_NAME as Record<string, string>)[id] ?? String(id);
}

/** 세트 임계 2·4·6 중 점수로 닿은 칸 (stage 와 같아야 하지만 score 로 다음 칸 차오름을 보인다) */
export function scorePips(score: number): [number, number, number] {
  // 칸마다 0..1 채움 (0~2 / 2~4 / 4~6)
  return [0, 1, 2].map((i) => Math.max(0, Math.min(1, (score - i * 2) / 2))) as [number, number, number];
}

/** HUD 태그 칩에 그릴 태그 (시스템 정렬 그대로, score > 0, 최대 max 개) */
export function hudTags(build: UiBuildState, max: number): UiTagState[] {
  return build.tags.filter((t) => t.score > 0).slice(0, Math.max(0, max));
}

/** 태그 칩 오른쪽 글: '3 · 2단' / '1' */
export function tagChipValue(t: Pick<UiTagState, 'score' | 'stage'>, tx: Tx = defaultTx): string {
  return t.stage > 0 ? `${t.score} · ${fill(tx('setStage'), { stage: t.stage })}` : String(t.score);
}

/** 저주 남은 기간: '3노드 남음' / '12처치 남음' / '' */
export function curseLeft(c: Pick<UiCurse, 'nodesLeft' | 'killsLeft'> | null, tx: Tx = defaultTx): string {
  if (!c) return '';
  if (typeof c.killsLeft === 'number') return fill(tx('curseKills'), { n: Math.max(0, c.killsLeft) });
  if (typeof c.nodesLeft === 'number') return fill(tx('curseNodes'), { n: Math.max(0, c.nodesLeft) });
  return '';
}

/**
 * TAG_SET_CHANGED 토스트 (오르면 획득 톤, 내리면 손실 톤). 이전 단계를 모르거나 같으면(스냅샷이 이벤트보다 먼저 바뀐 경우)
 * 오른 것으로 본다
 */
export function setChangeToast(
  p: Partial<UiTagSetChanged> | null | undefined,
  prevStage: number | undefined,
  tx: Tx = defaultTx,
): { tone: 'gain' | 'loss'; text: string } | null {
  if (!p || typeof p.stage !== 'number') return null;
  const name = p.name || tagName(p.tag ?? '');
  const up = prevStage === undefined || p.stage >= prevStage;
  if (up && p.stage > 0) {
    const text = p.effectName
      ? fill(tx('setUp'), { name, stage: p.stage, effect: p.effectName })
      : fill(tx('setUpPlain'), { name, stage: p.stage });
    return { tone: 'gain', text };
  }
  if (p.stage <= 0) return { tone: 'loss', text: fill(tx('setOff'), { name }) };
  return { tone: 'loss', text: fill(tx('setDown'), { name, stage: p.stage }) };
}

/** 완벽 성공 HUD 문구 */
export function perfectText(p: Partial<UiPerfectSuccess> | null | undefined, tx: Tx = defaultTx): string {
  switch (p?.kind) {
    case 'parry':
      return tx('perfectParry');
    case 'perfectGuard':
      return tx('perfectGuard');
    case 'perfectRelease':
      return tx('perfectRelease');
    case 'perfectEvade':
      return tx('perfectEvade');
    default:
      return '';
  }
}

/** 도장 글자 (完·良) · 이름 (완·양) */
export function gradeStamp(g: UiNodeGrade | null | undefined, tx: Tx = defaultTx): string {
  return g === 'perfect' ? tx('stampPerfect') : g === 'good' ? tx('stampGood') : '';
}
export function gradeName(g: UiNodeGrade | null | undefined, tx: Tx = defaultTx): string {
  return g === 'perfect' ? tx('gradePerfect') : g === 'good' ? tx('gradeGood') : tx('gradeNone');
}

/** 성과 진행 칩: 남은 초(소수 없이 올림) · 비율 · 피격 여부 */
export function trialView(
  t: UiNodeTrial | null | undefined,
  tx: Tx = defaultTx,
): { text: string; ratio: number; over: boolean; hit: boolean; hitText: string } | null {
  if (!t || !(t.timeLimitMs > 0)) return null;
  const left = Math.max(0, t.timeLimitMs - Math.max(0, t.elapsedMs));
  const over = left <= 0;
  return {
    text: over ? tx('trialOver') : fill(tx('trialLeft'), { sec: Math.ceil(left / 1000) }),
    ratio: Math.max(0, Math.min(1, left / t.timeLimitMs)),
    over,
    hit: Boolean(t.hitTaken),
    hitText: t.hitTaken ? tx('trialHit') : tx('trialNoHit'),
  };
}

/** NODE_GRADED 도장 카드 내용 */
export function gradedView(
  g: Partial<UiNodeGraded> | null | undefined,
  goldName: string,
  tx: Tx = defaultTx,
): { stamp: string; name: string; text: string; conds: string; deltas: string } | null {
  if (!g) return null;
  const ok = (b: unknown): string => (b ? tx('gradeOk') : tx('gradeNg'));
  const deltas: string[] = [];
  if (g.deltas?.gold) deltas.push(fill(tx('deltaGold'), { n: g.deltas.gold, gold: goldName || 'G' }));
  if (g.deltas?.personality) deltas.push(fill(tx('deltaPersonality'), { n: g.deltas.personality }));
  return {
    stamp: gradeStamp(g.grade ?? null, tx),
    name: gradeName(g.grade ?? null, tx),
    text: g.text ?? '',
    conds: `${tx('gradeNoHit')} ${ok(g.noHit)}  ·  ${tx('gradeInTime')} ${ok(g.inTime)}`,
    deltas: deltas.join('  '),
  };
}

/** 소모품 칸 표시: 개수 글 'n/m' · 빈 칸 여부 · 키 */
export function consumableView(
  c: UiConsumableSlot | null | undefined,
  tx: Tx = defaultTx,
): { key: string; empty: boolean; count: string; name: string; kind: 'throw' | 'drink' | null } | null {
  if (!c) return null;
  const key = c.key || 'C';
  if (!c.item) return { key, empty: true, count: '', name: tx('consumableEmpty'), kind: null };
  return {
    key,
    empty: false,
    count: `${Math.max(0, c.item.count)}/${Math.max(1, c.item.max)}`,
    name: c.item.name,
    kind: c.item.kind,
  };
}

/** 일기장 빌드 쪽 한 줄 (스타일: 머리글 page_faint · 본문 page_body · 흐림 page_faint) */
export interface DiaryLine {
  text: string;
  style: 'head' | 'body' | 'faint';
  /** 앞 줄과 띄울 px */
  gap: number;
}

type DiarySnap = Pick<UiSnapshot, 'passives' | 'consumable'> & { build?: UiBuildState | null };

/**
 * 57·60라운드 일기장(일시정지) 빌드 쪽: 태그·세트 / 이중 개성 / 저주 / 패시브(Lv·최대·태그) / 소모품.
 * 쪽이 넘치면 접는다: compact 1 = 꺼진 세트 효과·이중 개성 설명을 뺀다, 2 = 세트 효과·저주 이득/저주 줄도 뺀다.
 */
export function diaryLines(s: DiarySnap, compact: 0 | 1 | 2, tx: Tx = defaultTx): DiaryLine[] {
  const b = buildOf(s);
  const out: DiaryLine[] = [];
  const head = (k: R60TextKey) => out.push({ text: tx(k), style: 'head', gap: out.length ? 6 : 0 });
  const none = () => out.push({ text: tx('buildNone'), style: 'faint', gap: 0 });
  head('buildTags');
  if (!b.tags.length) none();
  for (const t of b.tags) {
    const next = t.next !== null ? fill(tx('setNext'), { n: t.next }) : tx('setMax');
    out.push({ text: `${t.name || tagName(t.id)}  ${tagChipValue(t, tx)}  (${next})`, style: 'body', gap: 0 });
    if (compact >= 2) continue;
    const on = t.effects.filter((e) => e.active).map((e) => `${e.threshold} ${e.name}`);
    const off = t.effects.filter((e) => !e.active).map((e) => `${e.threshold} ${e.name}`);
    if (on.length) out.push({ text: `  ${on.join(' · ')}`, style: 'body', gap: 0 });
    if (off.length && compact < 1) out.push({ text: `  ${off.join(' · ')}`, style: 'faint', gap: 0 });
  }
  if (b.dualTraits.length) {
    head('buildDual');
    for (const d of b.dualTraits) {
      const pair = fill(tx('dualPair'), { branch: d.branchName, tag: tagName(d.tag, b), tier: d.tier });
      out.push({ text: `${d.name}  ${pair}`, style: 'body', gap: 0 });
      if (compact < 1 && d.description) out.push({ text: `  ${d.description}`, style: 'faint', gap: 0 });
    }
  }
  if (b.curse) {
    head('buildCurse');
    const left = curseLeft(b.curse, tx);
    out.push({ text: `${b.curse.name}${left ? `  ${left}` : ''}`, style: 'body', gap: 0 });
    if (compact < 2) {
      if (b.curse.benefit) out.push({ text: `  + ${b.curse.benefit}`, style: 'faint', gap: 0 });
      if (b.curse.penalty) out.push({ text: `  − ${b.curse.penalty}`, style: 'faint', gap: 0 });
    }
  }
  head('buildPassives');
  const passives = s.passives ?? [];
  if (!passives.length) none();
  for (const p of passives) {
    const lv = fill(tx('passiveLevel'), { level: p.level, max: p.maxLevel || p.level });
    const tags = (p.tags ?? []).map((t) => tagName(t, b)).join('·');
    out.push({ text: `${p.name}  ${lv}${tags ? `  ${tags}` : ''}`, style: 'body', gap: 0 });
  }
  const c = consumableView(s.consumable, tx);
  if (c) {
    head('buildConsumable');
    out.push({
      text: c.empty ? `${c.name}  (${c.key})` : `${c.name}  ${c.count}  (${c.key})`,
      style: c.empty ? 'faint' : 'body',
      gap: 0,
    });
  }
  return out;
}
