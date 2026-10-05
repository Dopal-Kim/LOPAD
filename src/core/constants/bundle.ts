/** 60라운드 2차 묶음 연출·배치 값 (게임 수치는 data/bundle2.json) */
export const BUNDLE_FX = {
  /**
   * 61라운드 플레이 점검 #11: 노드 성과 등급 카드(NODE_GRADED)를 읽을 시간 — 이 시간 뒤에 보상 메뉴를 연다 (등급이 매겨진 노드만, 임시값).
   * UI 의 카드 표시 시간과 맞춘다
   */
  GRADE_CARD_HOLD_MS: 1600,
  /** 소품 플레이스홀더 색 (시트가 없을 때 StructureView 기본 도형) */
  PROP_COLOR: '#8a6a3a',
  /** E 소품 안내 반경 (칸) · 못 쓰는 사유 문구 (자리표시) */
  INTERACT_TILES: 1.5,
  NOT_READY_TEXT: '지금은 아니다',
  COMBAT_TEXT: '전투 중',
  /** 60라운드 Q32 E 조사 소품 (UI 계약 §14.10 clue·eventProp·mapSeller) 행동 문구 (자리표시) */
  EVENT_ACTION: '살펴본다',
  SELLER_ACTION: '말을 건다',
  /** 소품 자리: 전투장 가운데에서 (칸) — 이벤트 소품은 가운데 위, 성소 깃발은 가운데 왼쪽, 단서는 가운데 아래 */
  EVENT_OFFSET: { x: 0, y: -2 },
  SHRINE_OFFSET: { x: -3, y: -1 },
  CLUE_OFFSET: { x: 2, y: 2 },
  SELLER_OFFSET: { x: 3, y: -2 },
  /** E6 술독 깨기: 술통 판정 반경 (칸) · 술통 플레이스홀더 시트 */
  CASK_HIT_TILES: 1.1,
  CASK_SHEET: 'cask',
  /** 엘리트: 외곽선 깊이 (적 바로 아래) · 문장 위 여백 도트(10) · 문장 머리 위 기본 높이(도트, headTopByEnemy 가 없을 때) */
  ELITE_OUTLINE_DEPTH: 2.5e-6,
  ELITE_EMBLEM_GAP_DOTS: 10,
  ELITE_HEAD_TOP_DOTS: 120,
  /** 떨어진 소모품 줍기 반경(칸) */
  ITEM_PICK_TILES: 0.7,
  /** 결정타·등급 월드 문구 */
  FINISHER_TEXT: 'FINISHER',
  /** 보스 파훼: 경직 길이를 보스 정의에서 못 읽을 때(술통 되차기)의 결정타 창 ms */
  BREAK_FALLBACK_STUN_MS: 1500,
  /** 위험 노드 저주 길·이벤트 메뉴를 노드 진입 잠금 뒤 여는 여유 ms */
  MENU_AFTER_ENTER_MS: 120,
  /** 단서 소품 문구 (자리표시) */
  CLUE_TEXT: '무언가 지나간 자국이 있다. 살펴본다.',
  CLUE_LABEL: '살펴본다',
  /** 성소 깃발 E 안내 문구 · 세운 뒤 알림 (자리표시) */
  SHRINE_ACTION: '깃발을 세운다',
  SHRINE_GOAL: '엘리트 1 추가 · 마지막 웨이브 +1',
  SHRINE_RAISED_TEXT: '전장 깃발을 세웠다',
  /** E6 술독 깨기 · E8 기도 (자리표시) */
  CASK_GOAL: '술통 {n}개',
  CASK_FAIL_TEXT: '술통이 남았다',
  PRAY_LABEL: '손을 모은다',
} as const;
