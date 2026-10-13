/**
 * 61 단계 6 (계약 art §28) 입구 그림 이름 고르기 — 순수 규칙.
 * 찾는 순서: (62 I · art §32-1 위험 노드면 `door_<region>_<risk>` 먼저) → 정확한 `door_<region>_<kind>` →
 * 별칭(doors.json aliases, 키 `<region>_<kind>`) → `door_<region>_battle` → 없음.
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
  /** 62 I (art §32-1): 노드 위험 (elite·curse — bundle2 NodeExtra.risk) */
  risk?: string | null,
): string | null {
  if (!region) return null;
  const table = aliases ?? DEFAULT_DOOR_ALIASES;
  const base = `${region}_${kind}`;
  const tries = [risk ? `${region}_${risk}` : null, base, table[base], `${region}_battle`].filter((s): s is string =>
    Boolean(s),
  );
  for (const t of tries) if (exists(`door_${t}`)) return `door_${t}`;
  return null;
}

/** 수련장 방 입구 (art §28): 만취 그림자 = door_training_boss, 그 밖 = door_training_training */
export function trainingDoorName(bossRoom: boolean): string {
  return bossRoom ? 'door_training_boss' : 'door_training_training';
}

/** 62 I (art §32-2): 미리보기 카드판 이름 (`<이름>_small`, 512×288) — 있으면 그것, 없으면 원본 */
export function smallDoorName(name: string | null, exists: (name: string) => boolean): string | null {
  if (!name) return null;
  const small = `${name}_small`;
  return exists(small) ? small : name;
}
