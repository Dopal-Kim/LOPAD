# 2026-10-01 · 11라운드 보충 · 무기 개성 1차 구현 임시값 (도영 님 확인 필요)

11라운드 Q4 결정("기본 무기 1종 + 개성 변화 1단계")을 구현하며 Claude가 둔 값. 전부 `data/` 에 있어 바로 조정 가능.

| 항목 | 임시값 | 위치 |
|---|---|---|
| 기본 무기 | 사무라이 칼 (katana): 히트박스 24×16, 리치 14, 지속 0.1초, 쿨 0.35초, 데미지 배율 1.0 | `data/weapons.json` |
| 개성 임계값 | 100 (기획 4장) | `data/weapons.json` |
| 처치당 개성 획득 | 더미 8 · 궁수 10 · 돌진병 12 · 보스 50 | `data/enemies.json`, `data/bosses.json` `personalityValue` |
| 1단계 진화 "거합" | 데미지 ×1.2, 히트박스 ×1.4, 베기 궤적 이펙트(플레이스홀더) | `data/weapons.json` |
| 임계값 초과분 | 버림 (기획 "초기화" 를 0으로 해석) | `src/systems/weapons.ts` |
| 사망 시 | 무기·개성 초기화 (기획 3장) | `src/core/GameState.ts` |
| 개성 변화 알림 | 화면 중앙 임시 텍스트 1.5초 (정식 연출·UI는 UI 파트) | `src/scenes/Game.ts` |

플레이어 `attackHitbox` 는 무기로 이동했고 `data/player.json` 에서 제거됨.
