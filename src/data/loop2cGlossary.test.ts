import { describe, expect, it } from 'vitest';
import relics from '../../data/relics.json';
import memory from '../../data/memory.json';
import runEnd from '../../data/runEnd.json';
import meta from '../../data/meta.json';
import pack from '../../parts/story/text-pack-63-loop2.json';

/** 화면 문자열만 (키가 '_' 로 시작하는 주석·id·경로 제외) */
function strings(v: unknown, key = '', out: string[] = []): string[] {
  if (
    key.startsWith('_') ||
    key === 'id' ||
    key === 'weapon' ||
    key === 'trait' ||
    key === 'traits' ||
    key === 'good' ||
    key === 'memory' ||
    key === 'key'
  )
    return out;
  if (typeof v === 'string') out.push(v);
  else if (Array.isArray(v)) v.forEach((x) => strings(x, '', out));
  else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) strings(x, k, out);
  return out;
}

describe('62 루프 2 C 화면 문구 — 스토리 용어집 금지어 (계약 story-glossary §1.3)', () => {
  const G = (
    pack as unknown as { glossary: { bannedWords: string[]; bannedPatterns: { id: string; regex: string }[] } }
  ).glossary;
  const run = new RegExp(G.bannedPatterns.find((p) => p.id === 'run')!.regex);
  const all = [...strings(relics), ...strings(memory), ...strings(runEnd), ...strings(meta.upgrades)];
  it('금지어가 없다', () => {
    const bad = all.flatMap((s) => G.bannedWords.filter((w) => s.includes(w)).map((w) => `${w} ← ${s}`));
    expect(bad).toEqual([]);
    expect(all.filter((s) => run.test(s))).toEqual([]);
  });
});
