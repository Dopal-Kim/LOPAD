/**
 * 스테이지 전환 세이브 (기획 3장): 스테이지를 넘어가는 순간에만, 런당 최대 maxSaves 회.
 * 저장 시점은 "새 층 시작 직전" 상태라서, 이어하면 그 층의 시작 방에서 시작한다.
 * 사망·클리어 시 삭제. 브라우저 localStorage 사용 (StorageLike 로 추상화해 테스트 가능).
 */
import type { ScarData } from './setup/scar';
import type { BuildSave } from './build/BuildState';
import type { WeaponProgress } from './weapon/weapons';
import type { BundleSave } from './bundle2/BundleState';
import type { RunMemorySave } from './memory/runMemory';

export const SAVE_VERSION = 6;
export const SAVE_KEY = 'lopad.save';

export interface SaveData {
  version: typeof SAVE_VERSION;
  seed: string;
  stageIndex: number;
  hp: number;
  maxHp: number;
  kills: number;
  sense: number;
  savesLeft: number;
  /** 61 G (v6): 무기 성장 — 각성 게이지·경로·개성·단련·처리한 눈금 */
  weapon: { id: string } & WeaponProgress;
  gold: number;
  potions: number;
  pointsPending: number;
  bonus: { attack: number; maxHp: number; defense: number; crit: number };
  passives: Record<string, number>;
  playerName: string;
  /** 53라운드 Q4: 등 상흔 (선택 항목 — 이전 세이브는 없음, 버전 그대로) */
  scar?: ScarData;
  /** 57라운드 빌드 축: 이중 개성·저주·각성·영구 보너스 (선택 항목 — 이전 세이브는 없음, 버전 그대로) */
  build?: BuildSave;
  /** 60라운드 2차 묶음: 나온 이벤트·소모품 칸·이벤트 예약 (선택 항목 — 이전 세이브는 없음, 버전 그대로) */
  bundle?: BundleSave;
  /** 62 루프 2 C: 이번 생에 지닌 기억 (선택 항목 — 이전 세이브는 없음, 버전 그대로) */
  memory?: RunMemorySave;
  /**
   * 62 루프 2 시스템 D (P2-5) 나갈 때 자동 저장 (횟수 제한 없음 — 선택 항목, 버전 그대로). 있으면 층 처음이 아니라 이 노드로 이어한다.
   * 싸우는 중에 나갔으면 그 노드에 들어설 때의 상태(노드를 처음부터), 마친 노드면 나갈 때 상태(출구가 열린 채로)
   */
  suspend?: SuspendData;
  savedAt: number;
}

/** 62 D (P2-5) 노드 이어하기 — 노드 지도 진행 · 층 덧붙임(위험·이벤트·숨은 길·지도 정보) · 상점 진열 · 층 구조물 상태 */
export interface SuspendData {
  floor: number;
  currentId: string | null;
  path: string[];
  cleared: string[];
  /** 마친 노드에서 나갔다 (이어하면 출구가 열린 채로) */
  nodeCleared: boolean;
  /** BundleState.floor (FloorExtras — JSON 그대로) */
  extras: unknown;
  /** BundleState.shops (상점 진열 — JSON 그대로) */
  shops: unknown;
  /** gameState.structureCarry (StructureFloorCarry — JSON 그대로, 없으면 null) */
  structures: unknown;
  birthPending: boolean;
  /** 이어할 노드 종류 (보스 노드면 Game preload 가 보스 묶음을 받는다) */
  nodeKind?: string;
}

/** 이어하기 자동 저장 형식 검사 (깨졌으면 null — 층 처음으로 이어한다) */
export function readSuspend(raw: unknown): SuspendData | null {
  if (!raw || typeof raw !== 'object') return null;
  const s = raw as Partial<SuspendData>;
  const strs = (v: unknown): v is string[] => Array.isArray(v) && v.every((x) => typeof x === 'string');
  if (typeof s.floor !== 'number' || !strs(s.path) || !strs(s.cleared)) return null;
  if (s.currentId !== null && typeof s.currentId !== 'string') return null;
  return {
    floor: s.floor,
    currentId: s.currentId ?? null,
    path: [...s.path],
    cleared: [...s.cleared],
    nodeCleared: Boolean(s.nodeCleared),
    extras: s.extras ?? null,
    shops: Array.isArray(s.shops) ? s.shops : [],
    structures: s.structures ?? null,
    birthPending: Boolean(s.birthPending),
    ...(typeof s.nodeKind === 'string' ? { nodeKind: s.nodeKind } : {}),
  };
}

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export class SaveSlot {
  constructor(
    private storage: StorageLike | null,
    private key: string = SAVE_KEY,
  ) {}

  read(): SaveData | null {
    if (!this.storage) return null;
    try {
      const raw = this.storage.getItem(this.key);
      if (!raw) return null;
      const d = JSON.parse(raw) as Partial<SaveData>;
      if (d.version !== SAVE_VERSION || typeof d.seed !== 'string' || typeof d.stageIndex !== 'number' || !d.weapon)
        return null;
      return d as SaveData;
    } catch {
      return null;
    }
  }

  write(d: SaveData): void {
    this.storage?.setItem(this.key, JSON.stringify(d));
  }

  clear(): void {
    this.storage?.removeItem(this.key);
  }
}

/** 브라우저 localStorage 를 안전하게 얻는다 (없거나 막혀 있으면 null) */
export function browserStorage(): StorageLike | null {
  try {
    if (typeof localStorage === 'undefined') return null;
    const k = '__lopad_probe__';
    localStorage.setItem(k, '1');
    localStorage.removeItem(k);
    return localStorage;
  } catch {
    return null;
  }
}
