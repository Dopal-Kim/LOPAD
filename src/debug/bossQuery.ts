/**
 * 54라운드 보스 확인용 주소 옵션 (데모·검증). `?boss` = 이 층 보스 노드로 바로 (Preloader·WorldSetup),
 * `?bossPhase=<1..>` = 보스가 그 페이즈로 시작, `?bossPattern=<이름>[,<이름>…]` = 패턴을 그 순서로 되풀이 (쿨타임 무시).
 * 브라우저 밖(테스트)에서는 빈 값
 */
import { isBossPatternName, type BossPatternName } from '../data/bossPatterns';

export interface BossQuery {
  jump: boolean;
  /** 1부터 */
  phase: number | null;
  patterns: BossPatternName[] | null;
}

export function parseBossQuery(search: string): BossQuery {
  const q = new URLSearchParams(search);
  const ph = Number(q.get('bossPhase'));
  const list = (q.get('bossPattern') ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(isBossPatternName);
  return {
    jump: q.has('boss') || q.has('bossPhase') || q.has('bossPattern'),
    phase: Number.isInteger(ph) && ph >= 1 ? ph : null,
    patterns: list.length > 0 ? list : null,
  };
}

export function bossQuery(): BossQuery {
  return parseBossQuery(typeof location === 'undefined' ? '' : location.search);
}
