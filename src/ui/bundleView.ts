import type { UiNodeGrade, UiNodeRewardKind, UiRoute, UiRouteNode } from '../contract/ui';
import { gradeName, type Tx } from './buildView';
import { fill } from './fmt';
import { R60_TEXT, REWARD_GLYPH, REWARD_NAME, RISK_GLYPH } from './textBuild';

/**
 * 60라운드 계약 §14.5 노드 지도 순수 계산 (보상 미리보기·위험 노드·'?' 이벤트·숨은 노드·성과 도장·지도 정보).
 * 노드 필드는 계약 코드에서 아직 선택(`?`)이라 없으면 null 로 읽는다(시스템이 늘 채우면 그대로).
 */
const defaultTx: Tx = (k) => R60_TEXT[k];

export interface NodeLook {
  /** 얼룩만(smudge) · 위치 표시(located) — 노드 아이콘 대신 얼룩. found·null 은 보통 노드 */
  hidden: 'smudge' | 'located' | null;
  reward: UiNodeRewardKind | null;
  risk: 'elite' | 'curse' | null;
  grade: UiNodeGrade | null;
}

export function nodeLook(n: Partial<UiRouteNode>): NodeLook {
  const hidden = n.hidden === 'smudge' || n.hidden === 'located' ? n.hidden : null;
  return {
    hidden,
    // 숨은 노드(얼룩)는 보상을 보이지 않는다
    reward: hidden ? null : (n.reward ?? null),
    risk: hidden ? null : (n.risk ?? null),
    grade: n.grade ?? null,
  };
}

/** 노드 아이콘 대신 얼룩으로 그리는가 */
export function isSmudged(n: Partial<UiRouteNode>): boolean {
  return nodeLook(n).hidden !== null;
}

export function rewardGlyph(k: UiNodeRewardKind): string {
  return REWARD_GLYPH[k] ?? '?';
}
export function riskGlyph(k: 'elite' | 'curse'): string {
  return RISK_GLYPH[k] ?? '!';
}

/** 오른쪽 칸 '살펴보는 곳' 아래 줄: 보상 · 위험(+ 위험 한 줄) · 접두어 · 이벤트 내용 · 도장 · 숨은 길 */
export function nodeInfoLines(n: Partial<UiRouteNode>, tx: Tx = defaultTx): string[] {
  const look = nodeLook(n);
  if (look.hidden === 'smudge') return [tx('hiddenSmudge')];
  const out: string[] = [];
  if (look.hidden === 'located') out.push(tx('hiddenLocated'));
  else if (n.hidden === 'found') out.push(tx('hiddenFound'));
  if (look.reward) out.push(fill(tx('rewardHead'), { name: REWARD_NAME[look.reward] ?? look.reward }));
  if (look.risk) {
    out.push(fill(tx('riskHead'), { name: tx(look.risk === 'elite' ? 'riskElite' : 'riskCurse') }));
    if (n.riskText) out.push(n.riskText);
  }
  if (n.prefixes?.length) out.push(fill(tx('prefixHead'), { list: n.prefixes.join('·') }));
  if (n.eventName) out.push(fill(tx('eventHead'), { name: n.eventName }));
  if (look.grade) out.push(fill(tx('gradeHead'), { name: gradeName(look.grade, tx) }));
  return out;
}

/** 산 지도 정보 한 줄 ('' = 산 것 없음) */
export function intelLine(intel: UiRoute['intel'] | null | undefined, tx: Tx = defaultTx): string {
  if (!intel) return '';
  const parts: string[] = [];
  if (intel.nextTier) parts.push(tx('intelNextTier'));
  if (intel.fullFloor) parts.push(tx('intelFullFloor'));
  if (intel.hiddenLocated) parts.push(tx('intelHidden'));
  return parts.length ? `${tx('intelHead')} · ${parts.join(' · ')}` : '';
}

/** 지도에 보이는 보상 글리프 범례 ('전 전표 주머니 · 패 패시브 …', 없으면 '') — 아이콘이 오기 전 임시 */
export function rewardLegend(nodes: readonly Partial<UiRouteNode>[]): string {
  const seen: UiNodeRewardKind[] = [];
  for (const n of nodes) {
    const r = nodeLook(n).reward;
    if (r && !seen.includes(r)) seen.push(r);
  }
  // 61라운드 플레이 점검 #10: 한 항목('전 전표 주머니') 안에서는 줄을 바꾸지 않게 안쪽 띄어쓰기를 붙은 공백(NBSP)으로
  const keep = (t: string): string => t.replace(/ /g, '\u00a0');
  return seen.map((r) => keep(`${rewardGlyph(r)} ${REWARD_NAME[r] ?? r}`)).join(' · ');
}

/** 노드 띠·지도 다시 그리기 판단용 서명 (§14.5 필드 포함) */
export function nodeSig(n: UiRouteNode): string {
  return [
    n.id,
    `${n.col},${n.row}`,
    n.state,
    n.links.join('+'),
    n.reward ?? '',
    n.risk ?? '',
    n.hidden ?? '',
    n.grade ?? '',
  ].join(':');
}
