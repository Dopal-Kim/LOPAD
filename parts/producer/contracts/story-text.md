# 계약: 스토리 텍스트 (26라운드 승인)

스토리 파트가 확정한 이름과 문장(`parts/story/text-pack.md` 24·25라운드)을 시스템·UI 가 쓰기 위한 계약. 시스템은 이 문서대로 `data/story.json` 을 만들고, UI 는 시스템이 넘기는 키·문장만 표시한다. **문장 수정은 스토리 파트 재인터뷰 후 이 문서부터.**

## 1. 층 표
| 스테이지 id | 층 | 제국 | 보스 이름 | 비고 |
|---|---|---|---|---|
| stage1 | 1층 | 술독 제국 '잔(盞)' | 양조장주 '만취(滿醉)' | |
| stage2 | 2층 | 도박장 제국 '패(牌)' | 판돈 백작 | |
| stage3 | 3층 | 야전병원 제국 '붕(繃)' | 군의관 총재 | |
| stage4 | 4층 | 용병 제국 '계(契)' | 용병왕 | |
| stage5 | 5층 | 첩보 제국 '귀(耳)' | 감찰 총장 | |
| stage6 | 6층 | 연회 제국 '연(宴)' | 연회 후작 | |
| stage7 | 7층 | 붉은 근위 제국 '적(赤)' | 근위 총사령 | 황제 직할. 붉은 두려움 |
| stage8 | 8층 | 황제의 수도 '평상' | 황제 '평(平)' | 최종. 늘씬하고 정중한 인간 |

## 2. 텍스트 키 (`data/story.json`)
```
floors[stageId]: { title, empire, bossName, enter, bossIntro, restNote }
names: { potion, potionDesc, gold, goldDesc, souls, soulsDesc, sense, shop, shopDesc }
diary: { first, beforeFate, fate }           // fate: "{weapon}." 무기 이름만
evolution: { generic, byName: { "<진화명>": 문장 } }
death: "다시 태어난다. 기록만 남는다. {name}, {floor}층, {kills}명."
endings: { destroy, understand, choice: ["없앤다", "이해한다"] }   // 분기 구현은 별도 인터뷰
notices: { trialStart, trialClear, bossUnlocked, saved }   // saved: "{savesLeft}" 치환
```
문장은 text-pack 의 확정 문장을 그대로 복사한다 (여기 재수록하지 않음 — 시스템은 text-pack 을 읽지 않으므로 프로듀서가 story.json 초안을 만들어 넘긴다: `parts/producer/contracts/story-text.json`).

## 3. UI 계약 추가분 (ui-system-interface.md 에 반영)
- 이벤트 `STORY`: `{ kind: 'floor' | 'boss' | 'rest' | 'notice' | 'evolution' | 'death', text: string }` — HUD 가 하단 자막으로 표시.
- 스냅샷 `playerName: string`, `floorTitle: string`(예: "1층 · 술독 제국 '잔(盞)'"), `names: { potion, gold, shop }`.
- 결과 `UiResult.playerName`, `deathLine`.

## 4. 이름 입력
- 개성 선택 앞 단계에서 플레이어가 이름을 적는다 (일기장 첫 장). 시스템 `Setup` 씬이 입력을 받고 `gameState.playerName` 에 저장, 세이브에 포함.
