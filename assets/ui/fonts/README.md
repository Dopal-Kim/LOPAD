# Galmuri (갈무리) 비트맵 폰트 — 34라운드 채택
- 출처: npm `galmuri@2.40.3` (https://galmuri.quiple.dev), 라이선스 SIL OFL 1.1 (`LICENSE-OFL.txt`)
- 파일: Galmuri11 (본문, 12px 줄높이), Galmuri14 (제목, 15px), Galmuri9 (설명, 10px), Galmuri11-Bold (한글 전용, 한자 없음)
- 한자 포함 텍스트(무기 진화명·층 이름 등)는 반드시 **Galmuri11** 로 그린다. Galmuri14/9 는 擊·步·虛 가 없고, Bold 는 한자가 전혀 없다.
- 로드: `public/style.css` 또는 UI 씬에서 `@font-face`, Phaser Text `fontFamily: 'Galmuri11'`. 글꼴 로드 완료 후 씬 시작(document.fonts.load).
