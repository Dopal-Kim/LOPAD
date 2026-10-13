import { alertNorm } from './alertPlan';

/**
 * 62 루프 3 UI H (점검 P1-N2): 개성 발현·세트 단계 알림이 시스템 공지(STORY notice)로도 같은 말을 한 번 더 할 때
 * — '발도풍 — 검기를…'(위 큰 카드) + 개성 칩, '중량 2 — 강공 피해 +20%' + 세트 토스트 — 공지 쪽을 삼킨다 (순수).
 * 머리말 = 공지의 ' — ' 앞 (공백·문장부호를 뺀 비교). 공지가 먼저 왔으면 `remember` 뒤 HUD 가 `echoes` 로 골라 거둔다.
 */
export const ECHO_WINDOW_MS = 4000;

/** 공지의 머리말 (' — ' · ' - ' · ':' 앞, 없으면 전체) — 비교용 */
export function noticeHead(text: string): string {
  const m = text.split(/\s[—–-]\s|:/)[0] ?? text;
  return alertNorm(m);
}

export class NoticeEcho {
  private heads: { head: string; at: number }[] = [];

  constructor(readonly windowMs = ECHO_WINDOW_MS) {}

  /** 개성·세트 알림이 떴다 — 같은 머리말의 공지는 `windowMs` 동안 메아리 */
  remember(heads: readonly string[], now: number): void {
    this.prune(now);
    for (const h of heads) {
      const n = alertNorm(h);
      if (n) this.heads.push({ head: n, at: now });
    }
  }

  echoes(text: string, now: number): boolean {
    this.prune(now);
    const h = noticeHead(text);
    return h.length > 0 && this.heads.some((e) => e.head === h);
  }

  clear(): void {
    this.heads = [];
  }

  private prune(now: number): void {
    this.heads = this.heads.filter((e) => now - e.at <= this.windowMs);
  }
}

/** 개성 알림의 머리말 (이름) */
export function traitEchoHeads(name: string): string[] {
  const n = name.split(' — ')[0].trim();
  return n ? [n] : [];
}

/** 세트 단계 알림의 머리말 ('중량 2' · 효과 이름) */
export function setEchoHeads(p: { name?: string; stage?: number; effectName?: string } | null | undefined): string[] {
  if (!p) return [];
  const out: string[] = [];
  if (p.name && typeof p.stage === 'number') out.push(`${p.name} ${p.stage}`, `${p.name} 세트 ${p.stage}단`);
  if (p.effectName) out.push(p.effectName);
  return out;
}
