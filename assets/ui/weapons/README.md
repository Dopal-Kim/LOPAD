# HUD 무기 아이콘 (UI 파트 사본)

| 파일 | 출처 (아트 파트) | 무기 |
|---|---|---|
| `katana_icon.png` | `assets/sprites/weapons/katana_icon.png` | 사무라이 칼 |
| `greatsword_icon.png` | `assets/sprites/weapons/greatsword_icon.png` | 대검 |
| `dagger_icon.png` | `assets/sprites/weapons/dagger_icon.png` | 단검 |
| `bow_icon.png` | `assets/sprites/weapons/bow_icon.png` | 활 |

- 16×16 RGBA. 아트 파트 산출물을 **그대로 복사**한 사본이다 (계약 §7: UI 는 `assets/ui/**` 만 소유).
- 아트 파트가 아이콘을 갱신하면 이 폴더로 다시 복사한다 (교차 참조 승인 범위 안에서).
- 로드: `src/ui/HudScene.ts` `preload()` 가 `assets-game/ui/weapons/<id>_icon.png` 로 직접 `load.image`. 파일이 없으면 아이콘 없이 이름만 표시.
- 무기 이름 → 아이콘 id 매핑은 `src/ui/HudScene.ts` 의 `WEAPON_ICON_IDS` (스냅샷에 `weapon.id` 가 없어 이름으로 매핑, 29라운드 자율 결정).
