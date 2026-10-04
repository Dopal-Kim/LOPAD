/**
 * 이벤트 → 효과음 표의 한 줄 형식 (56라운드 2단계 6-1 정리 — audioMap 에서 분리, 내용 그대로). 순수 데이터.
 */
export interface AudioTrigger<P = unknown> {
  event: string;
  /** 설명 (매핑 요약용) */
  note: string;
  /** 재생할 효과음 id (고정 또는 페이로드로 결정). 목록이면 로드된 첫 후보 (55라운드 — 키 이름 대체) */
  sfx?: string | ((p: P) => string | readonly string[] | null);
  /** 조건. 없으면 항상 */
  when?: (p: P) => boolean;
  /** 재생 지연 ms (애니 프레임에 맞출 때) */
  delayMs?: (p: P) => number;
  /** 루프 효과음 시작 (가드 유지) */
  loop?: string;
  /** 정지할 효과음·루프 id */
  stop?: string[];
  /** 54라운드: 페이로드로 정하는 루프·정지 (보스 루프) */
  loopOf?: (p: P) => string;
  stopOf?: (p: P) => string[];
  /** 54라운드: 정지 페이드 ms (루프 끝 80~150ms 권장 — 음향 파트). 55라운드: 페이로드로 (피격 취소 60ms) */
  stopFadeMs?: number | ((p: P) => number);
  /** 55라운드: 루프 시작 페이드 인 ms (차지 루프 150ms — 음향 권장) */
  loopFadeInMs?: number;
  /** 54라운드: 재생 속도 (3연 취권 1·2·3타 1.0/1.06/1.12 — 음향 파트 권장) */
  rate?: (p: P) => number;
  /** 56라운드: 돌고 있는 루프의 재생 속도를 바꾼다 (차지 유지음 단계 1.0/1.03/1.06) */
  loopRate?: (p: P) => { id: string; rate: number } | null;
}

export function t<P>(def: AudioTrigger<P>): AudioTrigger {
  return def as AudioTrigger;
}
