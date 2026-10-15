/**
 * 62 루프 2 UI 문구 (P1-16 설정·접근성 · P2-5 일시정지 · P2-6 로딩). 전부 임시값 — 스토리 63 팩·용어집이 오면 바꾼다.
 * 데이터만 둔다(순수 계산 모듈이 import). 텍스트 팩 조회는 `text.ts` 의 `r62Text`(팩 `hud.<키>` 우선).
 */
export const R62_TEXT = {
  // ---- 설정 탭
  tabScreen: '화면',
  tabSound: '소리',
  tabControls: '조작',
  tabAccess: '접근성',
  fullscreen: '전체화면 (F11)',
  fullscreenNo: '이 창에서는 쓸 수 없다',
  muted: '소리 끄기',
  hitstop: '타격 멈춤',
  textSize: '글자 크기',
  textNormal: '보통',
  textLarge: '크게',
  textPreview: '자막·대사·쪽지 글이 이 크기로 적힌다.',
  // ---- 키 재설정
  keyUp: '위로',
  keyDown: '아래로',
  keyLeft: '왼쪽으로',
  keyRight: '오른쪽으로',
  keyDash: '대쉬',
  keyInteract: '상호작용',
  keyPotion: '독주 마시기',
  resetKeys: '기본 키로 되돌린다',
  keyWaitTitle: '「{action}」',
  keyWaitBody: '쓸 키를 누른다',
  keyWaitFoot: 'Esc 그만둔다',
  keyReserved: '{key} 는 다른 일에 쓴다',
  keyUnknown: '그 키는 쓸 수 없다',
  keySwapped: '「{other}」 와 키를 맞바꿨다',
  settingsHintTabs: '←→ 탭 · ↑↓ 고르기 · ←→ 바꾸기 · Enter · 클릭 정하기 · Esc 덮기',
  // ---- 일시정지 일기장 (P2-5)
  pauseResume: '이어서 하기',
  pauseClose: '일기장 덮기',
  pauseCloseNote: '여기까지 적어 두고 타이틀로 — 이어 쓸 수 있다',
  pauseAbandon: '이번 생을 포기한다',
  abandonConfirm: '이번 생을 여기서 끝낸다 — 예',
  abandonCancel: '아니, 더 쓴다',
  abandonNote: '쓰러진 것으로 친다. 모은 영혼은 남는다',
  /** 키를 바꿨을 때 일기장 조작 줄 (4동사는 키캡 안내가 따로 보인다) */
  controlsBound:
    '{move} 이동 · {dash} 대쉬 · {interact} 상호작용 · {potion} {potionName} · Shift 달리기 · M 지도 · Tab 빌드 · Esc 일시정지',
  // ---- 로딩 (P2-6)
  loadingTitle: '다음 장을 펼치는 중',
  /**
   * 단서 팁 — 스토리 63 팩 `loadingTips` 중 requires 없는 줄 (requires 있는 줄은 단서를 적은 뒤에만 — 시스템이 걸러 `hud.loadingTips` 로
   * 줄 때 쓴다). 팩 `hud.loadingTips`(줄바꿈으로 여러 줄)가 오면 그것
   */
  loadingTips: [
    "'만취는 마시는 동안 잔을 내려놓지 않는다.' 지난 생의 메모다.",
    "'사수는 거리를 잰다. 기둥 뒤에서는 재지 못한다.'",
    "'결사병은 달려들기 전에 발을 구른다. 그때 옆으로.'",
    "'독주 행상의 술병은 떨어진 자리를 태운다. 불 위에 서 있지 마라.'",
    "'술 웅덩이에 불이 닿으면 번진다. 어느 쪽 발밑이든.'",
    "'공격이 닿기 직전에 대쉬하면 손이 먼저 반응한다.'",
    "'각성 게이지가 눈금에 닿으면 개성 하나를 고른다. 고른 것은 그 생 동안 남는다.'",
    "'군주의 유품은 하나만 가져간다. 나머지는 다음 생의 몫이다.'",
    "'독주는 아픔을 지운다. 잠시.' 잠시가 지나기 전에 끝내라.",
    "'쓰러지면 영혼이 남는다. 영혼을 부으면 무언가 떠오른다.'",
    '전표는 어디서나 통한다. 전쟁보다 먼저 통일된 것이다.',
    '종군 상인은 어느 쪽이 이기든 판다.',
    '잔(盞)에서는 술값을 외상으로 단다. 돌아오면 갚는다고들 한다.',
    '번진 이름 위에 덧쓴다. 획은 같은 손이다.',
    "쉼터 기둥에 칼로 새긴 글씨. '외상 갚고 금방 온다.'",
  ].join('\n'),
  // ---- P19 1-U 연속 처치 (오른쪽 가장자리 작은 표 — 숫자 앞 낱말, 스토리 결이 오면 바꾼다)
  comboTag: '연속',
} as const;
export type R62TextKey = keyof typeof R62_TEXT;
