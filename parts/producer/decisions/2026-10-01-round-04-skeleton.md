# 2026-10-01 · 4라운드 · 저장소 뼈대

### Q1. 파트 폴더 이름과 배치
- 선택지: parts/ 아래 영문 6개 (추천) / 루트에 바로 6개 / 한글 폴더명
- 결정: **`parts/{producer,system,ui,art,sound,story}`**.

### Q2. 기획서(docx) 원본 처리
- 선택지: 마크다운 변환 + BLANK 유지 (추천) / 마크다운 + docx 둘 다 보관 / 저장소에 넣지 않음
- 결정: **마크다운 변환 + BLANK 유지** → `parts/producer/GDD.md`. docx는 커밋하지 않음.

### Q3. 게임 코드(src/) 소유 분할
- 선택지: 폴더 단위 분할 (추천) / 시스템 파트가 src/ 전부 소유 / 보류
- 결정: **폴더 단위 분할**. `src/ui/**`는 UI 파트, 그 외 `src/**`는 시스템 파트. 경계 인터페이스는 `parts/producer/contracts/` 계약 문서로만 공유.

### Q4. 뼈대 구성 후 첫 개시 파트
- 선택지: 게임 시스템 (프로토타입) (추천) / 스토리 / 아트 / 뼈대만 만들고 종료
- 결정: **게임 시스템 (프로토타입)**. 개시 시 해상도·JSON 데이터·폴더 구조·프로토타입 범위 인터뷰 진행.

---

## Claude가 뼈대 구성 중 세운 가정 (도영 님 확인 필요)
인터뷰로 묻지 않고 설정한 것들이다. 다르게 정하시면 즉시 수정한다.

1. **공개 자료 범위**: 루트 CLAUDE.md, `parts/producer/GDD.md`, `parts/producer/decisions/**`, `parts/producer/contracts/**`는 모든 파트가 읽을 수 있다고 설정했다. (기획서와 결정 기록은 도영 님의 문서이므로 특정 파트의 산출물이 아니라고 판단.)
2. **에셋 폴더 소유**: `assets/sprites`, `assets/tiles` → 아트, `assets/audio` → 음향, `assets/ui` → UI, `data/` → 시스템으로 배정했다. 실제 `assets/`·`data/` 존재 여부와 세부 구조는 시스템 파트 개시 인터뷰에서 확정.
3. **커밋 접두어**: `[system]`, `[ui]`, `[art]`, `[sound]`, `[story]`, `[producer]`.
4. **pixel-art-studio 복사 범위**: 스킬 본문·레퍼런스·스크립트·예제 .py만 복사하고, 원본 저장소의 샘플 이미지(약 2.4MB)는 제외했다.
