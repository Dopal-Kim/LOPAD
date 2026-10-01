# LOPAD

PC 웹용 2D 탑다운 로그라이크 액션 게임. Phaser 3 + TypeScript.

- 운영 규칙: [`CLAUDE.md`](CLAUDE.md)
- 기획서: [`parts/producer/GDD.md`](parts/producer/GDD.md)
- 결정 로그: [`parts/producer/decisions/`](parts/producer/decisions/)

## 파트
`parts/producer` · `parts/system` · `parts/ui` · `parts/art` · `parts/sound` · `parts/story`
각 파트는 독립적으로 작업하며, 파트 간 참조는 승인 기록 후에만 이루어진다.

## 실행
```
npm install
npm run dev        # http://localhost:8080  (WASD 이동, 좌클릭 공격, R 재시작, ?seed=값 으로 같은 층 재현)
npm run typecheck
npm run test       # vitest
npm run lint       # eslint
npm run build
```
Claude Code 웹 세션에서는 `.claude/hooks/session-start.sh`가 npm 의존성과 Pillow(아트 스킬용)를 자동 설치한다.

## 요구 사항
- Node.js 22+, npm
- Python 3 + Pillow (아트 파트 스킬용): `pip install pillow`
