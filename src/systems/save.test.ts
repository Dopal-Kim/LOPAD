import { describe, expect, it } from 'vitest';
import { SAVE_VERSION, SaveSlot, type SaveData, type StorageLike } from './save';

function memStorage(): StorageLike {
  const m = new Map<string, string>();
  return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => void m.set(k, v), removeItem: (k) => void m.delete(k) };
}

const sample: SaveData = {
  version: SAVE_VERSION,
  seed: 'abc',
  stageIndex: 2,
  hp: 70,
  maxHp: 100,
  kills: 20,
  sense: 3,
  savesLeft: 1,
  weapon: { id: 'katana', personality: 40, stage: 1 },
  gold: 120,
  potions: 2,
  pointsPending: 0,
  bonus: { attack: 1, maxHp: 10, defense: 0, crit: 3 },
  passives: { sprint: 1 },
  savedAt: 0,
};

describe('SaveSlot', () => {
  it('쓰고 읽고 지운다', () => {
    const s = new SaveSlot(memStorage());
    expect(s.read()).toBeNull();
    s.write(sample);
    expect(s.read()).toEqual(sample);
    s.clear();
    expect(s.read()).toBeNull();
  });
  it('버전이 다르거나 깨진 데이터는 무시한다', () => {
    const st = memStorage();
    const s = new SaveSlot(st);
    st.setItem('lopad.save', JSON.stringify({ ...sample, version: 99 }));
    expect(s.read()).toBeNull();
    st.setItem('lopad.save', '{not json');
    expect(s.read()).toBeNull();
  });
  it('저장소가 없으면 조용히 무시한다', () => {
    const s = new SaveSlot(null);
    s.write(sample);
    expect(s.read()).toBeNull();
  });
});
