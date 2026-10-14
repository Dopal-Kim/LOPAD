/**
 * 62 루프 1 P0-2 첫 생 의식 UI 틀 문구 (계약 §20). 문장(일기장 줄·안내·'왜'·운명)은 시스템이 스냅샷으로 보낸다 — 여기는 칸 이름뿐.
 * 임시값 — 스토리 검수 대상. 수치·내부 용어는 쓰지 않는다.
 */
export const RITUAL_TEXT = {
  nameLabel: '이름',
  /** 이름 칸이 비었을 때 흐린 자리표시 */
  namePlaceholder: '여기에 적는다',
  legendHead: '획이 부르는 무기',
  sealsHead: '세 획',
  tasksHead: '회피 시험',
  rememberedTag: '손이 기억한 무기',
  /** 영혼 강화 귀퉁이 — {souls} = 가진 영혼 */
  metaSouls: '영혼 {souls}',
} as const;

export type RitualTextKey = keyof typeof RITUAL_TEXT;

export function ritualText(k: RitualTextKey): string {
  return RITUAL_TEXT[k];
}
