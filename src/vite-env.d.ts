/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 데모 배포본 전용: 'all' 이면 층마다 그 층 구조물을 전부 배치 (47라운드) */
  readonly VITE_DEMO_STRUCTURES?: string;
  /** 데모 배포본 전용: 주소 옵션이 하나도 없을 때 쓸 기본 옵션(예: 'slice=outer') — 아티팩트는 주소 옵션을 넘길 수 없음 (52라운드 맵 검수) */
  readonly VITE_DEMO_QUERY?: string;
}
