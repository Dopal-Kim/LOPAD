/**
 * 57라운드: 공격 페이로드가 어느 빌드 동작에서 나왔는지 (속사 연사 화살 등). EventBus 발행은 동기라 발행하는 동안만 표시를 켠다.
 * `move` 필드는 음향이 휘두름 소리를 빼는 데 쓰므로(audioMap) 화살에는 쓰지 않는다.
 */
let current: string | null = null;

export function withAttackTag<T>(tag: string, fn: () => T): T {
  const prev = current;
  current = tag;
  try {
    return fn();
  } finally {
    current = prev;
  }
}

/** 지금 발행 중인 공격의 빌드 표시 (없으면 null) */
export function currentAttackTag(): string | null {
  return current;
}
