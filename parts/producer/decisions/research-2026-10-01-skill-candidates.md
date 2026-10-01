# 조사 · 2026-10-01 · Claude Code 스킬 후보 (아트 / Phaser)

결정이 아닌 조사 기록. 결정은 `2026-10-01-round-03-skills.md`.

## 아트 (픽셀아트)
| 후보 | 방식 | 외부 의존 | 라이선스 | 평가 |
|---|---|---|---|---|
| [Gamezxz/pixel-art-studio](https://github.com/Gamezxz/pixel-art-studio) | Claude가 Pillow 코드로 픽셀을 직접 그리고 렌더를 보고 자기 비평·수정 반복. 스프라이트·타일셋·애니메이션·Phaser용 스프라이트시트 JSON | Python 3 + Pillow만 | MIT | **채택.** 컨테이너에서 Pillow 설치 가능 확인 |
| [thejacedev pixel-art-gen](https://github.com/thejacedev/claude-code-skills/tree/main/plugins/pixel-art-gen) | Pillow, 8~32px 단일 스프라이트 | Pillow | MIT | 애니메이션·타일셋 없음 |
| [ianlintner/ai-pixel-art-image-generation](https://github.com/ianlintner/ai-pixel-art-image-generation) | gpt-image / Gemini 이미지 모델로 생성 | OpenAI 또는 Gemini API 키 | - | 보류. 도영 님이 Gemini API 사용을 추후 검토할 뜻 표명 |
| SpriteCook (Anthropic 디렉터리 플러그인, [SpriteCook/skills](https://github.com/SpriteCook/skills)) | 원격 MCP로 스프라이트·UI 킷·타일셋 생성 | 외부 서비스 계정 가능성 | - | 미채택 |
| Aseprite 계열 ([with-pebbly/aseprite-ai-artist](https://github.com/with-pebbly/aseprite-ai-artist), [willibrandon/pixel-plugin](https://github.com/willibrandon/pixel-plugin)) | Aseprite를 MCP로 제어 | Aseprite 설치 | - | 컨테이너에서 불가 |

## Phaser
| 후보 | 내용 | 평가 |
|---|---|---|
| [OpusGameLabs/game-creator](https://github.com/OpusGameLabs/game-creator) `skills/phaser` | TS+Vite, 씬 구조, EventBus/GameState/Constants 규약, 물리·성능·안티패턴. 플러그인 전체에는 수익화(Play.fun)·Retro Diffusion API 등 외부 의존 포함 | **phaser 스킬만 발췌·개작하여 채택** (`.claude/skills/phaser/`) |
| [HermeticOrmus/claude-code-game-development](https://github.com/HermeticOrmus/claude-code-game-development) | 87개 플러그인 묶음, 로그라이크·전투 패턴 포함 | 과대. 미채택 |
| Anthropic 디렉터리 "phaser" 플러그인 | 이름만 같은 OpenSpec 기반 워크플로 도구, 게임 엔진과 무관 | 해당 없음 |

## 환경 확인
- Node 22.22 / npm 10.9 / Python 3.11 / ffmpeg 있음. Pillow·numpy 없음 (pip 설치 가능).
- 계정에 활성화된 플러그인·스킬 없음.
