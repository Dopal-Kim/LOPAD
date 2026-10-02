# 프로듀서 도구

## weapon-ledger.html — 무기 발현 대장 (실시간 조회·수정)
- 배포: https://claude.ai/artifact/TUFsuDhXEK9MHGLa26kDxg (도영 님 전용, db 저장)
- 내용: `data/weapons.json` + `data/personality.json` 을 페이지에 내장해 무기 4종의 기본 성능·우클릭 보조 동작·개성 성향·분기 트리(1차→2차)·강화 규칙·개성 선택 파라미터를 표시. 칸을 고치면 아티팩트 DB `overrides/<경로>` 에 `{path, value, base, at}` 로 저장되고 변경 목록에 쌓인다. '되돌리기'는 문서를 삭제.
- 반영 절차: 도영 님이 "무기 대장 적용"이라고 하면 프로듀서가 `overrides` 컬렉션을 읽어 `data/weapons.json`·`personality.json` 에 적용하고(시스템 파트, 검증 포함) 결정 로그에 기록한 뒤 DB 를 비운다.
- 재생성: 데이터가 바뀌면 `parts/producer/tools/weapon-ledger.html` 안의 `const BASE = {...}` 를 최신 JSON 으로 갱신해 같은 URL 로 재발행.
