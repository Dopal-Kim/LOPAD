import { describe, expect, it } from 'vitest';
import build from '../../data/build.json';
import pack from '../../parts/story/text-pack-63-loop2.json';

/** 62 I (P1-N2): 세트 단계 카드 문장 — 용어집 카드 문장 규칙(숫자·×·% 금지) + 금지어 */
describe('62 I 세트 단계 line (story-glossary §1.3 카드 문장)', () => {
  const G = (pack as unknown as { glossary: { bannedWords: string[] } }).glossary;
  const sets = (build as unknown as { sets: Record<string, { name: string; line: string }[]> }).sets;
  const lines = Object.entries(sets).flatMap(([tag, arr]) =>
    arr.map((s) => ({ at: `${tag} ${s.name}`, line: s.line })),
  );

  it('모든 단계에 문장이 있다', () => {
    expect(lines.filter((l) => !l.line)).toEqual([]);
  });

  it('숫자·×·% 가 없다', () => {
    expect(lines.filter((l) => /[0-9×%]/.test(l.line))).toEqual([]);
  });

  it('금지어가 없다', () => {
    const bad = lines.flatMap((l) => G.bannedWords.filter((w) => l.line.includes(w)).map((w) => `${w} ← ${l.at}`));
    expect(bad).toEqual([]);
  });
});
