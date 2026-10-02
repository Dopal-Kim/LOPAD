# 프로듀서 도구

## weapon-ledger.html — 무기 발현 대장 (실시간 조회·수정)
- 배포: https://claude.ai/artifact/TUFsuDhXEK9MHGLa26kDxg (도영 님 전용, db 저장)
- 내용: `data/weapons.json` + `data/personality.json` 을 페이지에 내장해 무기 4종의 기본 성능·우클릭 보조 동작·개성 성향·분기 트리(1차→2차)·강화 규칙·개성 선택 파라미터를 표시. 칸을 고치면 아티팩트 DB `overrides/<경로>` 에 `{path, value, base, at}` 로 저장되고 변경 목록에 쌓인다. '되돌리기'는 문서를 삭제.
- 반영 절차: 도영 님이 "무기 대장 적용"이라고 하면 프로듀서가 `overrides` 컬렉션을 읽어 `data/weapons.json`·`personality.json` 에 적용하고(시스템 파트, 검증 포함) 결정 로그에 기록한 뒤 DB 를 비운다.
- 이펙트 조회: 무기 탭마다 '이펙트' 절에 손에 든 무기 오버레이·기본 공격·1차·2차 이펙트 시트를 이미지와 애니메이션(프레임 시간표 재생, 방향 선택)으로 표시. '이펙트 공통' 탭에 보조 동작·대쉬·피격·예고·적 투사체 시트.
- 재생성: `python3 parts/producer/tools/build-ledger.py` (템플릿 `ledger.template.html` + data/*.json + assets/sprites/fx·weapons 를 내장) 후 같은 URL 로 재발행.
