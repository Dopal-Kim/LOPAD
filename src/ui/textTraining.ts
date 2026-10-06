/**
 * 61 단계 6 (P14) 수련장 · 그림 속 입구 UI 틀 문구. 임시값 — 도영 님·스토리 검수 대상. 데이터만 둔다.
 * 텍스트 팩 조회는 `text.ts` 의 `trainingText`(팩 `hud.<키>` 우선). 서사 틀: 수련장 = '이름이 번지기 전, 손이 기억하는 곳'.
 */
export const TRAINING_TEXT = {
  // ---- 메뉴 항목
  titleItem: '수련장',
  pauseItem: '수련장',
  pauseLeave: '수련장을 나간다',
  /** 일기장 '수련장' 거부 사유 (`startTraining` 결과) */
  denyCombat: '싸움이 끝난 뒤에 갈 수 있다',
  denyBoss: '본영 앞에서는 수련장에 갈 수 없다',
  denyBusy: '지금은 수련장에 갈 수 없다',
  // ---- 과제 목록
  hudTitle: '수련장 · {room}',
  hudCount: '{done}/{total}',
  hudStamped: '도장',
  taskDone: '과제 · {label}',
  // ---- 도장
  stampMark: '수련',
  stampLine: '{room} · 도장',
  stampAll: '여덟 방 모두 도장',
  // ---- 수련장 지도 (두루마리)
  mapTitle: '수련장',
  mapSub: '이름이 번지기 전, 손이 기억하는 곳',
  mapHint: '←→ 고르기 · Enter·클릭 들어간다 · 1~8 바로',
  mapStamped: '도장',
  mapAgain: '다시 들어갈 수 있다',
  // ---- 첫 생 선택
  choiceHint: '←→ 고르기 · Enter·클릭',
  choiceTraining: '손이 기억하는 것부터 확인한다',
  choiceRun: '익숙한 손을 믿고 곧장 나간다',
} as const;
export type TrainingTextKey = keyof typeof TRAINING_TEXT;
