import { describe, expect, it } from 'vitest';
import { NARRATIVE, NARRATIVE_STORY, VOICE_SCENES, voiceLine } from '../../data/narrative';
import { WEAPONS } from '../../data';
import { BUNDLE2, eventDef } from '../../data/bundle2';
import { MetaStore, emptyMeta } from '../meta';
import { optionLabel } from '../bundle2/eventText';
import {
  bossKilledBefore,
  clueLines,
  diaryReadLine,
  emptyDiary,
  hasPastLife,
  inFirstLife,
  isFirstLife,
  koreanCount,
  readDiary,
  recordBirth,
  recordBossKill,
  recordClue,
  recordLifeEnd,
  updateDiary,
} from './diary';
import { NarrativeState } from './NarrativeState';

class MemStorage {
  private m = new Map<string, string>();
  getItem(k: string) {
    return this.m.get(k) ?? null;
  }
  setItem(k: string, v: string) {
    this.m.set(k, v);
  }
  removeItem(k: string) {
    this.m.delete(k);
  }
}

const life = (cleared = false) => ({ name: 'a', weapon: 'katana', floor: 1, kills: 9, cleared, bosses: [] });

describe('61라운드 P7·P8 일기장 이력 (메타 diary)', () => {
  it('첫 생 → 운명(생 +1) → 사망(지난 생 기록·사망 수) → 두 번째 생', () => {
    let d = emptyDiary();
    expect(isFirstLife(d)).toBe(true);
    d = recordBirth(d, '도영');
    expect(inFirstLife(d)).toBe(true);
    expect(isFirstLife(d)).toBe(false);
    expect(hasPastLife(d)).toBe(false);
    d = recordLifeEnd(d, life(), 2);
    expect(d.deaths).toBe(1);
    expect(hasPastLife(d)).toBe(true);
    d = recordBirth(d, '도영');
    expect(inFirstLife(d)).toBe(false);
    d = recordLifeEnd(recordLifeEnd(d, life(true), 2), life(), 2);
    expect(d.pastLives).toHaveLength(2);
    expect(d.deaths).toBe(2);
    expect(d.lastName).toBe('도영');
  });

  it('옛 메타(diary 없음)는 런 수로 채운다 · 깨진 값은 다듬는다', () => {
    expect(readDiary({ runs: 3, clears: 1 }).lives).toBe(3);
    expect(readDiary({ runs: 3, clears: 1 }).deaths).toBe(2);
    const bad = readDiary({ runs: 0, clears: 0, diary: { lives: -2, clues: [3 as never, 'x'], bossKills: { s: -1 } } });
    expect(bad.lives).toBe(0);
    expect(bad.clues).toEqual(['x']);
    expect(bad.bossKills).toEqual({});
  });

  it('메타 세이브에 읽고 쓴다', () => {
    const store = new MetaStore(new MemStorage());
    store.write(emptyMeta());
    updateDiary((d) => recordClue(recordBossKill(d, 'stage1'), 'birthMask'), store);
    updateDiary((d) => recordClue(d, 'birthMask'), store);
    const d = readDiary(store.read());
    expect(d.clues).toEqual(['birthMask']);
    expect(d.bossKills.stage1).toBe(1);
  });

  it('단서 repeatLast · 만취 처치 이력 · E4 지난 생의 기록', () => {
    const c = NARRATIVE_STORY.clues.birthMask;
    expect(clueLines(c, false)).toEqual(c.lines);
    expect(clueLines(c, true).at(-1)).toBe(c.repeatLast);
    expect(clueLines(c, true)).toHaveLength(c.lines.length);
    const d = recordBossKill(emptyDiary(), 'stage1');
    expect(bossKilledBefore(d, 'stage1', true)).toBe(false);
    expect(bossKilledBefore(d, 'stage1', false)).toBe(true);
    const t = eventDef('diary')!.diaryRead!;
    expect(diaryReadLine(t, { bossKilledBefore: true, hasPastLife: true }, 0)).toBe(t.bossKilledBefore);
    expect(t.tips).toContain(diaryReadLine(t, { bossKilledBefore: false, hasPastLife: true }, 0.99));
    expect(diaryReadLine(t, { bossKilledBefore: false, hasPastLife: false }, 0)).toBe(t.empty);
  });

  it('번진 겹 수는 한글 관형사 (1~9)', () => {
    expect(koreanCount(2)).toBe('두');
    expect(koreanCount(5)).toBe('다섯');
    expect(koreanCount(12)).toBe('12');
  });
});

describe('61라운드 P8 서사 데이터 · 런 상태', () => {
  it('무기 4 × 장면 5 한마디 · 단서 3 소품 배치 · 만취 대사', () => {
    for (const w of Object.keys(WEAPONS))
      for (const s of VOICE_SCENES) expect(voiceLine(w, s), `${w}.${s}`).toBeTruthy();
    expect(NARRATIVE.props.map((p) => p.sheet)).toEqual([
      'clue_masked_corpse',
      'clue_gate_register',
      'clue_tab_ledgers',
    ]);
    expect(NARRATIVE.props.map((p) => p.node)).toEqual(['birth', 'post', 'boss']);
    expect(NARRATIVE_STORY.boss1.speaker).toBe('만취');
  });

  it('장면 한마디는 런당 1회 · 한 번만 하는 말', () => {
    const n = new NarrativeState();
    expect(n.takeVoice('firstKill')).toBe(true);
    expect(n.takeVoice('firstKill')).toBe(false);
    expect(n.once('boss1.break.cup')).toBe(true);
    expect(n.once('boss1.break.cup')).toBe(false);
  });

  it('이벤트 선택지 문구: {…} 를 효과 값으로 채운다', () => {
    const labels = (id: string) => eventDef(id)!.options!.map((o) => optionLabel(o));
    expect(labels('diary')).toEqual(['떠올린다 — 각성 게이지 +30', '다듬는다 — 감각 +1', '지난 생의 기록을 읽는다']);
    expect(labels('tasting')[0]).toBe('한 잔 — 최대 체력 −10 · 패시브 2택');
    expect(labels('offering')[0]).toBe('고개를 숙인다 — 최대 체력 +8');
    expect(labels('droppedLedger')).toEqual([
      '돌려준다 — 다음 상점 −10%',
      "한 줄 긋는다 — 저주 '외상'",
      '태운다 — 전표 +15',
    ]);
    for (const e of BUNDLE2.events.items)
      for (const o of e.options ?? []) expect(optionLabel(o)).not.toMatch(/\{\w+\}/);
  });
});
