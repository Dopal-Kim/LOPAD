/**
 * 53라운드 후속: Phaser 3.90 KeyboardPlugin 키 이벤트 재전달 막기 (Phaser 없음).
 *
 * KeyboardManager 는 DOM 키 이벤트가 올 때마다 큐에 넣고 곧바로 모든 씬의 KeyboardPlugin.update 로 **큐 전체**를 다시 돌린다.
 * 큐는 스텝이 끝날 때(POST_STEP)만 비우고, 플러그인의 중복 거르기는 바로 앞 이벤트 하나와만 비교한다. 그래서 프레임이 밀려
 * 한 스텝에 키 이벤트가 3개 이상 쌓이면 앞 이벤트가 같은 객체로 한 번 더 `keydown`·`keydown-X` 로 나온다.
 * `JustDown` 폴링은 한 프레임에 한 번만 읽으므로 영향이 없고, 이벤트 구독(`keyboard.on('keydown…')`)만 두 번 실행될 수 있다.
 */

/**
 * 같은 이벤트 객체는 처음 한 번만 넘기는 처리기. 처리기마다 따로 기억한다(다른 처리기가 같은 이벤트를 받는 것은 막지 않음).
 * `off` 에는 이 함수가 돌려준 처리기를 그대로 넘긴다. 객체가 아닌 인자(테스트·직접 호출)는 거르지 않는다.
 */
export function oncePerKeyEvent<E>(fn: (e: E) => void): (e: E) => void {
  const seen = new WeakSet<object>();
  return (e: E) => {
    if (typeof e === 'object' && e !== null) {
      if (seen.has(e)) return;
      seen.add(e);
    }
    fn(e);
  };
}
