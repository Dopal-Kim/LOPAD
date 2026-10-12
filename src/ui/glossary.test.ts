import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import ts from 'typescript';
import { describe, expect, it } from 'vitest';

/**
 * 62 루프 2 (P1-18, 계약 `parts/producer/contracts/story-glossary.md`): UI 화면 문자열 금지어·말투 검사.
 * 금지어·패턴은 스토리 63 팩 `glossary` 배열을 그대로 쓴다(계약 §1.3). 검사 대상 = `src/ui/*.ts`(테스트 제외)의 문자열 리터럴 중
 * 한글이 든 것 — 주석·import 경로·디버그 이름은 빠진다(TypeScript 구문 트리로 문자열만 뽑는다).
 */
const ROOT = join(__dirname, '..', '..');
const PACK = JSON.parse(readFileSync(join(ROOT, 'parts/story/text-pack-63-loop2.json'), 'utf8')) as {
  glossary: {
    bannedWords: string[];
    bannedPatterns: { id: string; regex: string }[];
    tone: { patterns: string[] };
  };
};

const UI_DIR = join(ROOT, 'src/ui');
const HANGUL = /[가-힣]/;
/** 영문 금지어는 낱말 경계로 (예: 'HP' — 'HP_TRAIL' 같은 식별자 문자열은 한글이 없어 애초에 빠진다) */
const ASCII = /^[A-Za-z%]+$/;

interface Found {
  file: string;
  line: number;
  text: string;
}

function uiStrings(): Found[] {
  const out: Found[] = [];
  for (const name of readdirSync(UI_DIR)) {
    if (!name.endsWith('.ts') || name.endsWith('.test.ts')) continue;
    const src = readFileSync(join(UI_DIR, name), 'utf8');
    const sf = ts.createSourceFile(name, src, ts.ScriptTarget.Latest, true);
    const visit = (n: ts.Node): void => {
      if (ts.isImportDeclaration(n) || ts.isExportDeclaration(n)) return;
      if (
        ts.isStringLiteral(n) ||
        ts.isNoSubstitutionTemplateLiteral(n) ||
        ts.isTemplateHead(n) ||
        ts.isTemplateMiddle(n) ||
        ts.isTemplateTail(n)
      ) {
        const text = n.text;
        if (HANGUL.test(text))
          out.push({ file: name, line: sf.getLineAndCharacterOfPosition(n.getStart()).line + 1, text });
      }
      ts.forEachChild(n, visit);
    };
    visit(sf);
  }
  return out;
}

const found = uiStrings();
const where = (f: Found): string => `${f.file}:${f.line} ${f.text}`;

describe('용어집 금지어 (src/ui 화면 문자열)', () => {
  it('문자열을 찾는다 (검사기 자체 확인)', () => {
    expect(found.length).toBeGreaterThan(300);
  });

  it('bannedWords 가 없다', () => {
    const bad: string[] = [];
    for (const w of PACK.glossary.bannedWords) {
      const re = ASCII.test(w) ? new RegExp(`(^|[^A-Za-z])${w.replace('%', '\\%')}([^A-Za-z]|$)`) : null;
      for (const f of found) if (re ? re.test(f.text) : f.text.includes(w)) bad.push(`${w} — ${where(f)}`);
    }
    expect(bad).toEqual([]);
  });

  it("bannedPatterns.run ('런' 단독 낱말) 이 없다", () => {
    const p = PACK.glossary.bannedPatterns.find((x) => x.id === 'run');
    expect(p).toBeTruthy();
    const re = new RegExp(p!.regex);
    expect(found.filter((f) => re.test(f.text)).map(where)).toEqual([]);
  });

  it('말투: 지문·안내는 해라체 (습니까·하세요 등 없음)', () => {
    const res = PACK.glossary.tone.patterns.map((r) => new RegExp(r));
    expect(found.filter((f) => res.some((re) => re.test(f.text))).map(where)).toEqual([]);
  });
});
