# LOPAD

PC 웹용 2D 탑다운 로그라이크 액션 게임. Phaser 3 + TypeScript.

- 운영 규칙: [`CLAUDE.md`](CLAUDE.md)
- 기획서: [`parts/producer/GDD.md`](parts/producer/GDD.md)
- 결정 로그: [`parts/producer/decisions/`](parts/producer/decisions/)

## 파트
`parts/producer` · `parts/system` · `parts/ui` · `parts/art` · `parts/sound` · `parts/story`
각 파트는 독립적으로 작업하며, 파트 간 참조는 승인 기록 후에만 이루어진다.

## 로컬 준비 (게임 시스템 파트 개시 후 확정)
- Node.js 22+, npm
- Python 3 + Pillow (아트 파트 스킬용): `pip install pillow`
