/** 62 루프 2 시스템 D (P2-6) 로딩 팁 데이터 (data/loading.json — 스토리 63 팩 loadingTips 복사). 숫자 금지 검사 */
import loadingJson from '../../data/loading.json';
import type { LoadingTip } from '../systems/loadingTips';

function validate(raw: unknown): LoadingTip[] {
  const r = raw as { tips?: unknown };
  if (!Array.isArray(r.tips)) throw new Error('[data] loading.tips 없음');
  return r.tips.map((t, i) => {
    const x = t as Partial<LoadingTip>;
    if ((x.kind !== 'tip' && x.kind !== 'lore') || typeof x.text !== 'string' || !x.text)
      throw new Error(`[data] loading.tips[${i}] 형식`);
    if (/[0-9]/.test(x.text)) throw new Error(`[data] loading.tips[${i}] 숫자 금지`);
    return { kind: x.kind, text: x.text, ...(typeof x.requires === 'string' ? { requires: x.requires } : {}) };
  });
}

export const LOADING_TIPS: readonly LoadingTip[] = validate(loadingJson);
