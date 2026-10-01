# 2026-10-01 · 3라운드 · 스킬 확정

조사 내용은 `research-2026-10-01-skill-candidates.md` 참조.

### Q1. 아트 파트용 픽셀아트 스킬
- 선택지: Gamezxz/pixel-art-studio (추천) / ianlintner (OpenAI/Gemini 이미지 API) / pixel-art-studio + SpriteCook 보조 / 보류
- 결정 (도영 님 답변 인용): "PIXEL ART STUDIO 로 지금은 진행하고, 추후에 GEMINI 이미지 API 사용해서 이미지 제작할 생각도 존재함. 이미지 구현이 부족한 경우에 나중에 다시 설정함을 선언하고 할 것이니 일단은 PIXEL ART STUDIO 로 진행할게."
- 비고: **Gemini 이미지 API 도입은 보류 상태.** 도영 님이 "이미지 구현이 부족하다"고 선언하면 재인터뷰로 결정한다. 그 전에는 Claude가 제안하지 않는다.

### Q2. 게임 시스템/UI 파트용 Phaser 스킬
- 선택지: game-creator의 phaser 스킬만 발췌 (추천) / game-creator 플러그인 전체 설치 / 외부 스킬 없이 직접 작성
- 결정: **phaser 스킬만 발췌**, LOPAD에 맞게 개작. 제거한 것: Play.fun 수익화 안전 영역, 모바일 60/40 입력 규칙, 스펙터클 이벤트 강제, 뮤트 버튼 규칙, 플러그인 템플릿 의존.

### Q3. 스킬 파일 위치
- 선택지: 저장소 `.claude/skills/`에 커밋 (추천) / 사용자 레벨 `~/.claude/skills/`
- 결정: **저장소 `.claude/skills/`에 커밋**. 출처·라이선스 기록.

### Q4. 스킬 접근 범위 격리
- 선택지: 파트별 제한 (추천) / 모든 파트 공유
- 결정: **파트별 제한**. pixel-art-studio → 아트만, phaser → 시스템·UI만.
