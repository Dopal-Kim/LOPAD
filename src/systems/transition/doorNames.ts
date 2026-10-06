/**
 * 61 단계 6 (계약 art §28) 입구 그림 이름 고르기 — 순수 규칙.
 * 찾는 순서: 정확한 `door_<region>_<kind>` → 별칭(doors.json aliases, 키 `<region>_<kind>`) → `door_<region>_battle` → 없음.
 * 별칭 표가 아직 없으면(로드 전) 아트 §28 의 기본 별칭을 쓴다.
 */
export const DEFAULT_DOOR_ALIASES: Readonly<Record<string, string>> = {
  waste_birth: 'waste_battle',
  waste_road: 'waste_battle',
  gate_post: 'gate_rest',
  boss_boss: 'hall_boss',
  hall_battle: 'hall_boss',
};

export function resolveDoorName(
  region: string,
  kind: string,
  aliases: Readonly<Record<string, string>> | null,
  exists: (name: string) => boolean,
): string | null {
  if (!region) return null;
  const table = aliases ?? DEFAULT_DOOR_ALIASES;
  const base = `${region}_${kind}`;
  const tries = [base, table[base], `${region}_battle`].filter((s): s is string => Boolean(s));
  for (const t of tries) if (exists(`door_${t}`)) return `door_${t}`;
  return null;
}

/** 수련장 방 입구 (art §28): 만취 그림자 = door_training_boss, 그 밖 = door_training_training */
export function trainingDoorName(bossRoom: boolean): string {
  return bossRoom ? 'door_training_boss' : 'door_training_training';
}
