/**
 * 키 입력 한 번 = 동작 한 번 (53라운드 시험장 갈래 Esc 버그).
 *
 * Phaser 3.90 KeyboardPlugin 은 DOM 키 이벤트가 올 때마다 그 스텝 동안 쌓인 큐(`KeyboardManager.queue`, POST_STEP 에서 비움)를
 * 처음부터 다시 훑는다. 중복 방지는 '바로 앞 이벤트와 같으면 건너뛴다' 뿐이라, 프레임이 밀려 한 스텝 사이에 키 이벤트가
 * 셋 이상 쌓이면(예: 이동 키 자동 반복 + Esc 누름·뗌) **같은 KeyboardEvent 객체가 다시 넘어온다** (`e.repeat` 는 false).
 * 그 사이에 메뉴가 바뀌었으면 두 번째 처리가 새 메뉴에 들어간다 — labBranch 에서 Esc 가 '9'(갈래 → 무기 고르기)로
 * 처리된 뒤, 같은 Esc 가 다시 넘어와 새로 열린 lab 메뉴의 cancelKey '0' 으로 메뉴 전체가 닫혔다.
 * (RouteMap 확인 창의 `inputAfter` 와 같은 원인, 49라운드 헤드리스 확인)
 *
 * UI 의 키 처리기는 **실제로 동작할 때** `takeKey(e)` 를 부르고, false 면 아무것도 하지 않는다.
 * 기록은 이벤트 객체 단위(WeakSet)라 UI 씬 전체가 공유한다 — 한 씬이 처리한 Esc 를 다른 씬이 다시 처리하지 않는다
 * (예: 일시정지가 Esc 로 닫힌 뒤 같은 Esc 가 HUD 에 다시 와서 일시정지를 또 여는 일).
 * 동작하지 않고 지나치는 처리기(메뉴가 떠 있어 HUD 가 Esc 를 넘기는 경우 등)는 부르지 않는다.
 */
const taken = new WeakSet<object>();

/** 이 키 이벤트로 처음 동작하면 true (기록), 이미 어느 UI 처리기가 동작했으면 false. 이벤트가 없으면 항상 true */
export function takeKey(e?: object | null): boolean {
  if (!e || typeof e !== 'object') return true;
  if (taken.has(e)) return false;
  taken.add(e);
  return true;
}

/** 이미 어느 UI 처리기가 동작한 이벤트인가 (기록하지 않는다) */
export function keyTaken(e?: object | null): boolean {
  return Boolean(e && typeof e === 'object' && taken.has(e));
}
