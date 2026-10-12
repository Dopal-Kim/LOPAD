/**
 * 62 루프 2 시스템 C (P16 §4 · 점검 P1-8) 의식 화면의 '기억' (Setup 이 쓴다 — 흐름만, 그리기는 UI 메뉴):
 * - 기억 장 (F2, 두 번째 생부터): 메뉴 id 'meta' — 소품 · 손이 기억한 모양 · 떠올릴 개성 · 장터에 놓일 것 · 몸의 기억(능력치 3줄).
 *   줄 key 'm:<기억 id>' (몸의 기억 'm:stat:<id>') · `line.memory` · 닫기 '0'. 떠올리면 MEMORY_CHANGED.
 * - 운명 공개 뒤 고르기: 모양(메뉴 'aspect' — 이 무기 모양을 떠올렸을 때만) → 소품(메뉴 'keepsake' — 소품을 하나라도 떠올렸을 때만).
 *   둘 다 필수 선택(cancelKey 없음). 고른 소품은 다음 생 기본값으로 메타에 남긴다.
 */
import { MEMORY, memoryDef } from '../../data/memory';
import { RELICS } from '../../data/relics';
import type { UiMemoryEntry, UiMenuLine } from '../../contract/ui';
import { META_CONFIG, metaStore } from '../../systems/meta';
import {
  defaultKeepsake,
  memoryBook,
  memoryEntry,
  memoryLineDetail,
  openAspect,
  openKeepsakes,
} from '../../systems/memory/memory';
import { iconLoaded } from '../../systems/growth/traitArt';
import { chooseKeepsake, recallMemory } from '../../contract/hostLoop2C';
import { fill } from '../../systems/story';
import type { TextMenu } from '../../systems/TextMenu';

export const MEMORY_KEY_PREFIX = 'm:';
const CLOSE = '0';

export class MemoryPicks {
  /** 운명 공개 뒤 지금 여는 고르기 */
  picking: 'aspect' | 'keepsake' | null = null;
  /** 고른 모양 기억 id (null = 처음 모양) · 지닐 소품 id (null = 빈손) */
  aspect: string | null = null;
  keepsake: string | null = null;

  constructor(
    private readonly menu: TextMenu,
    private readonly changed: () => void,
  ) {}

  // --- 기억 장 ---

  /** 기억 장 (계약 MENU 'meta'). onClose = 닫기 '0' */
  openBook(onClose: () => void): void {
    const meta = metaStore.read();
    const book = memoryBook(meta, META_CONFIG, iconLoaded);
    const lines: UiMenuLine[] = [];
    for (const c of book.chapters)
      for (const e of c.entries)
        lines.push({
          key: `${MEMORY_KEY_PREFIX}${e.id}`,
          label: e.name,
          enabled: e.affordable,
          detail: memoryLineDetail(e, (n) => fill(RELICS.ui.level, { n })),
          memory: e,
        });
    this.menu.open(
      'meta',
      `${book.title} · ${book.soulsText}`,
      lines,
      (key) => {
        if (key === CLOSE) {
          this.menu.close();
          onClose();
          return;
        }
        const id = key.startsWith(MEMORY_KEY_PREFIX) ? key.slice(MEMORY_KEY_PREFIX.length) : '';
        if (this.unlock(id)) this.openBook(onClose);
      },
      book.intro.join(' '),
      { cancelKey: CLOSE },
    );
  }

  /** 떠올린다 (영혼 부족·이미 떠올림이면 false) — 계약 명령 `memory.unlock` 과 같은 길 */
  unlock(id: string): boolean {
    return recallMemory(id);
  }

  // --- 운명 공개 뒤 고르기 ---

  /** 고를 것이 있으면 차례로 열고 끝나면 done. 없으면 기본값(소품 = 마지막 고른 것)으로 바로 done */
  begin(weapon: string, done: () => void): void {
    const meta = metaStore.read();
    this.aspect = null;
    this.keepsake = defaultKeepsake(meta);
    const aspect = openAspect(meta, weapon);
    const keepsakes = openKeepsakes(meta);
    const pickKeepsake = () => {
      if (keepsakes.length === 0) return this.finish(done);
      this.openPick(
        'keepsake',
        MEMORY.pick.keepsakeTitle,
        [
          ...keepsakes.map((m) => this.pickLine(`k:${m.id}`, m.id)),
          this.baseLine('none', MEMORY.pick.keepsakeNone, MEMORY.pick.keepsakeNoneLine),
        ],
        (key) => {
          this.keepsake = key.startsWith('k:') ? key.slice(2) : null;
          chooseKeepsake(this.keepsake);
          this.finish(done);
        },
      );
    };
    if (!aspect) return pickKeepsake();
    this.openPick(
      'aspect',
      MEMORY.pick.aspectTitle,
      [
        this.baseLine('base', MEMORY.pick.aspectBase, MEMORY.pick.aspectBaseLine),
        this.pickLine(`a:${aspect.id}`, aspect.id),
      ],
      (key) => {
        this.aspect = key.startsWith('a:') ? key.slice(2) : null;
        pickKeepsake();
      },
      MEMORY.pick.aspectHint,
    );
  }

  private finish(done: () => void): void {
    this.picking = null;
    this.menu.close();
    this.changed();
    done();
  }

  private openPick(
    id: 'aspect' | 'keepsake',
    title: string,
    lines: UiMenuLine[],
    onPick: (key: string) => void,
    footer = '',
  ): void {
    this.picking = id;
    this.menu.open(
      id,
      title,
      lines,
      (key) => {
        if (!lines.some((l) => l.key === key)) return;
        onPick(key);
      },
      footer,
    );
    this.changed();
  }

  private pickLine(key: string, id: string): UiMenuLine {
    const e = this.entry(id)!;
    return { key, label: e.name, enabled: true, detail: `${e.line} — ${e.detail}`, memory: e };
  }

  private baseLine(key: string, label: string, detail: string): UiMenuLine {
    return { key, label, enabled: true, detail };
  }

  /** 기억 한 칸 (계약 UiMemoryEntry) */
  entry(id: string | null): UiMemoryEntry | null {
    const m = id ? memoryDef(id) : undefined;
    return m ? memoryEntry(m, metaStore.read(), iconLoaded) : null;
  }

  /** 의식 상태 (`UiRitual.memory`) */
  state(): { picking: 'aspect' | 'keepsake' | null; aspect: UiMemoryEntry | null; keepsake: UiMemoryEntry | null } {
    return { picking: this.picking, aspect: this.entry(this.aspect), keepsake: this.entry(this.keepsake) };
  }
}
