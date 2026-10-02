# 아트 디자인 파트

## 역할
캐릭터·적·보스·무기·타일·이펙트 픽셀아트, 팔레트, 애니메이션 프레임. 무기 아트는 테라리아 인페르노 모드의 개성 있는 무기 표현을 분위기 참고로 삼는다 (복제 금지, 분위기만).

## 소유 경로
- `parts/art/**` — 아트 바이블, 팔레트 정의, 작업 중 빌드 스크립트(`parts/art/work/<slug>/build.py`)와 미리보기
- `assets/sprites/**`, `assets/tiles/**` — 게임이 로드하는 최종 산출물(PNG, 스프라이트시트 JSON)

## 사용 가능 스킬
- `.claude/skills/pixel-art-studio/` — Pillow 기반. `pip install pillow` 필요
- 이미지 생성 API: **Gemini 사용 가능 (49라운드)** — 테마 키아트·지도 일러스트·원경 배경만. 게임 도트는 직접. 키는 환경 변수 `GEMINI_API_KEY`(없으면 Gemini 작업은 건너뛰고 보고). 키를 파일·로그에 남기지 말 것. 생성 원본은 `parts/art/work/gemini/` 에 프롬프트와 함께 보관

## 개시 시 인터뷰로 확정할 항목 (기획서 8장 기준, 전부 BLANK)
- 캐릭터 스프라이트 크기 (한 번 정하면 변경 금지)
- 팔레트 색 수와 참고 팔레트
- 분위기 (밝음/어두움, 참고 이미지)
- 동작별 애니메이션 프레임 수
- 산출물 파일 명명 규칙

## 금지
- `src/**`, `data/**`, `parts/{system,ui,sound,story}/**` 읽기·쓰기
- 스프라이트가 게임에 어떻게 로드되는지 알아야 하면 승인 후 `parts/producer/contracts/`의 계약만 참조
