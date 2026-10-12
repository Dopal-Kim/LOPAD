/**
 * 시스템 파트: 62 루프 2 시스템 C 계약 명령 구현 (계약 ui.ts 'C 절' — `uiCommands.endChoice` · `uiCommands.memory.*`). UI 파트는 import 금지.
 * main.ts 가 installContractHost 다음에 부른다. 메타 세이브만 읽고 쓰므로 어느 화면에서나 된다(타이틀·의식·결과).
 */
import { UI_EVENTS, __system, uiCommands, type UiEndChoice, type UiMemoryBook } from './ui';
import { META_CONFIG, metaStore } from '../systems/meta';
import { memoryBook, setKeepsake, unlockMemory } from '../systems/memory/memory';
import { iconLoaded } from '../systems/growth/traitArt';
import { invalidateMetaSummary } from './metaSummary';
import { EventBus, Events, type MemoryUnlockedPayload } from '../core/EventBus';
import { memoryDef } from '../data/memory';
import { STAT_PREFIX } from '../systems/memory/memory';

/** 지금 기억 장 */
export function currentMemoryBook(): UiMemoryBook {
  return memoryBook(metaStore.read(), META_CONFIG, iconLoaded);
}

/** 떠올린다 (영혼 부족·이미 떠올림·모르는 id 면 false) → MEMORY_CHANGED */
export function recallMemory(id: string): boolean {
  const next = unlockMemory(metaStore.read(), id);
  if (!next) return false;
  metaStore.write(next);
  invalidateMetaSummary();
  const kind = id.startsWith(STAT_PREFIX) ? 'stat' : (memoryDef(id)?.kind ?? '');
  EventBus.emit(Events.MEMORY_UNLOCKED, { id, kind } satisfies MemoryUnlockedPayload);
  __system.emit(UI_EVENTS.MEMORY_CHANGED, memoryBook(next, META_CONFIG, iconLoaded));
  return true;
}

/** 다음 생에 지닐 소품 (null = 빈손) → MEMORY_CHANGED */
export function chooseKeepsake(id: string | null): boolean {
  const next = setKeepsake(metaStore.read(), id);
  if (!next) return false;
  metaStore.write(next);
  __system.emit(UI_EVENTS.MEMORY_CHANGED, memoryBook(next, META_CONFIG, iconLoaded));
  return true;
}

export function installLoop2C(): void {
  __system.patchImpl({
    loop2C: {
      memoryBook: currentMemoryBook,
      unlockMemory: recallMemory,
      setKeepsake: chooseKeepsake,
      endChoice: (c: UiEndChoice) => {
        if (c === 'reborn') uiCommands.startNewRun();
        else uiCommands.toTitle();
        return true;
      },
    },
  });
}
