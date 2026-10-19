/**
 * P21 어두운 톤 · 잔혹 전투 · 상흔 이벤트 (계약 `parts/producer/contracts/dark-brutal.md` §2). EventBus `Events` 에 펼쳐 넣는다.
 * 시스템 `scenes/game/brutal/*` 가 낸다. UI 는 EXECUTABLE·PLAYER_EXECUTE·PLAYER_WOUNDED·LOW_HP 를 `ui:` 접두로 받는다 (contract/ui.ts 'P21' 절).
 */
export const P21_EVENTS = {
  /** 적 상처 단계가 오름 (`EnemyWoundedPayload` — HP ≤ 66% → 1, ≤ 33% → 2) */
  ENEMY_WOUNDED: 'enemy:wounded',
  /** 적중마다 피 분출 (`EnemyGorePayload`) */
  ENEMY_GORE: 'enemy:gore',
  /** ENEMY_DIED 바로 뒤 — 사망 변형 (`EnemyDeathVariantPayload`) */
  ENEMY_DEATH_VARIANT: 'enemy:death-variant',
  /** 처형 가능 표식 (`EnemyExecutablePayload`) */
  ENEMY_EXECUTABLE: 'enemy:executable',
  /** 처형 시작 (`PlayerExecutePayload`) */
  PLAYER_EXECUTE: 'player:execute',
  /** 주인공 상처 단계·박힌 화살 (`PlayerWoundedPayload`) */
  PLAYER_WOUNDED: 'player:wounded',
  /** HP ≤ 25% 진입·이탈 (`LowHpPayload`) */
  LOW_HP: 'player:low-hp',
} as const;

export type GoreWeapon = 'katana' | 'greatsword' | 'dagger' | 'bow';
export type GoreCut = 'slash' | 'stab' | 'crush' | 'pierce';
export type DeathVariant = 'collapse' | 'behead' | 'bisect' | 'pinned' | 'burn' | 'drown';

export interface EnemyWoundedPayload {
  id: string;
  x: number;
  y: number;
  stage: 1 | 2;
  /** 적 종류 id (id 와 같다 — 계약 칸) */
  kind: string;
}

export interface EnemyGorePayload {
  id: string;
  x: number;
  y: number;
  dirX: number;
  dirY: number;
  weapon: GoreWeapon | null;
  cut: GoreCut;
  amount: 1 | 2 | 3;
}

export interface EnemyDeathVariantPayload {
  id: string;
  x: number;
  y: number;
  kind: string;
  variant: DeathVariant;
  dirX: number;
  dirY: number;
  /** (음향 sound §15 요청) 갑옷 적 — 방패병·통 갑옷 엘리트 → body_fall_armor */
  armored?: boolean;
  /** 엘리트 (전용 사망음 elite_die 가 있어 body_fall 생략) */
  elite?: boolean;
}

export interface EnemyExecutablePayload {
  id: string;
  /** 개체 번호 (offscreen 과 같은 번호) */
  uid: number;
  x: number;
  y: number;
  on: boolean;
}

export interface PlayerExecutePayload {
  target: string;
  x: number;
  y: number;
  weapon: GoreWeapon;
  ms: number;
  /** 시작 → 결정타까지 ms (음향 execute_hit 을 이만큼 늦춰 결정타 프레임에) */
  impactMs: number;
}

export interface PlayerWoundedPayload {
  stage: 0 | 1 | 2 | 3;
  arrows: number;
  /** 시스템 내부(음향): 단계가 올랐다 · 화살이 하나 늘었다 (UI 계약 밖 — 중계에 그대로 실려도 무해) */
  rose?: boolean;
  arrowAdded?: boolean;
}

export interface LowHpPayload {
  on: boolean;
  ratio: number;
}
