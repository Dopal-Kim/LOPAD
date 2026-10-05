/**
 * 스테이지 전환 세이브 (기획 3장): 스테이지를 넘어가는 순간에만, 런당 최대 maxSaves 회.
 * 저장 시점은 "새 층 시작 직전" 상태라서, 이어하면 그 층의 시작 방에서 시작한다.
 * 사망·클리어 시 삭제. 브라우저 localStorage 사용 (StorageLike 로 추상화해 테스트 가능).
 */
import type { ScarData } from './setup/scar';
import type { BuildSave } from './build/BuildState';
import type { BundleSave } from './bundle2/BundleState';

export const SAVE_VERSION = 5;
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
  /** 무기 개성: 트리 선택 경로·강화 횟수 (v5, 27라운드) */
  weapon: { id: string; personality: number; path: string[]; reinforce: number; choicePending: boolean };
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
  savedAt: number;
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
