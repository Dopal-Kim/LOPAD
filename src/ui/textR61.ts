/**
 * 61라운드 UI 문구 (P10 — 설정 화면 §15 · 전투 HUD 다이어트 · 키캡 안내). 전부 임시값(도영 님·스토리 검수 대상).
 * 데이터만 둔다(순수 계산 모듈이 import). 텍스트 팩 조회는 `text.ts` 의 `r61Text`(팩 `hud.<키>` 우선).
 */
export const R61_TEXT = {
  // ---- 설정 화면 (계약 §15)
  settingsTitle: '설정',
  settingsItem: '설정',
  groupScreen: '화면',
  groupSound: '소리',
  shake: '화면 흔들림',
  flash: '섬광',
  tilt: '화면 기울기',
  damageNumbers: '피해 숫자',
  master: '전체 음량',
  bgm: '배경음',
  sfx: '효과음',
  on: '켬',
  off: '끔',
  reset: '처음 값으로 되돌린다',
  close: '덮는다',
  settingsHint: '↑↓ 고르기 · ←→ 바꾸기 · Enter 켜고 끄기 · 마우스로 끌기 · Esc 덮기',
  // ---- 전투 HUD (다이어트)
  /** 빌드 띠 끝 Tab 안내 (노드 지도 층·시험장) */
  stripTab: '빌드',
  /** 저주 칩 짧은 꼴 — {n} = 남은 노드/처치 수, {unit} = 노드·처치 */
  curseShort: '저주 {n}{unit}',
  curseUnitNode: '노드',
  curseUnitKill: '처치',
  // ---- Tab 빌드 보기 (누르고 있는 동안)
  peekWeapon: '{name}',
  peekKeys: '조작',
  peekFoot: 'Tab 을 떼면 닫힌다 · Esc 일기장에 더 적혀 있다',
  /** 조작 안내 줄 (노드 지도 층·시험장) */
  controlPeek: 'Tab 빌드',
  // ---- 키캡 안내 기본 동작 이름 (시스템 4동사 필드가 오기 전 — 지금 조작)
  verbAttack: '공격',
  verbDash: '대쉬',
  verbPotion: '독주',
  verbConsumable: '소모품',
  verbCarry: '넣기·뽑기',
} as const;
export type R61TextKey = keyof typeof R61_TEXT;
