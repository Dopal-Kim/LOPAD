/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 데모 배포본 전용: 'all' 이면 층마다 그 층 구조물을 전부 배치 (47라운드) */
  readonly VITE_DEMO_STRUCTURES?: string;
}
