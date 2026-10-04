#!/usr/bin/env python3
"""56라운드 원문 8번 + Q13~Q24 — 무기별 공격 수단 키아트 데이터 (프롬프트·라벨·수단 목록의 단일 원본).

키아트는 참고 그림이다(게임 도트 아님, 루트 CLAUDE.md 4). 각 수단의 입력·조건은 키아트 검수 후 인터뷰(56라운드 Q21~Q24 비고).
'ref' = 메커니즘 참조(2010년 이후 게임·도영 님 원문·조사 문서). 프롬프트에는 작품 이름을 넣지 않는다(4-1, 49라운드 관례).
교훈(52·53라운드): 대문자 강조어·번호 나열은 그림 속 라벨 글자를 부른다 → 산문 + 위치어(top-left 등)만 쓴다.
"""

# 시트 배치: grid=(cols, rows). 패널 순서 = 왼→오, 위→아래.
WEAPONS = {
    # ------------------------------------------------------------------ 칼 (53라운드 Q26: B 재 칼날)
    "katana": {
        "ko": "칼",
        "ref_img": "../concept_weapons/raw_katana_B2.jpg",
        "weapon_en": (
            "His weapon is a katana: a long, slender, gently curved single-edged blade made of hardened dark ash and battlefield earth, "
            "matte charcoal-black, its whole cutting edge one thin bright amber fissure glowing from inside; a small round guard made "
            "from a fused shard of breastplate; a long grip wrapped in dirty bandage; a slim cracked ash scabbard with a glowing seam "
            "worn at his left hip. It is clearly a katana in every panel - no cross-guard, no straight double-edged blade. "
        ),
        "sheets": [
            {"grid": (2, 2), "panels": [
                dict(ko="기본 연격", desc="3연격 약 1.5초, 타마다 짧은 멈춤. 대각 두 획이 X로 교차하고 셋째 타로 이어짐. 붓획 궤적(시작 가늘고·가운데 굵고·끝 갈라짐).",
                     src="56라운드 Q1·Q11", ref="데드셀(궤적·타격 밀도), 몬스터 헌터 태도(연계)",
                     en="his basic three-hit combo against a cluster of drunken conscripts: two fast diagonal cuts have just crossed as a large X of thin amber brush strokes hanging in the air, and the third cut is in progress; enemies recoil with ash bursting from the cuts."),
                dict(ko="일섬 (발도 돌진)", desc="3타 발도 = 앞으로 4칸 돌진, 적을 관통해 뒤로 빠져나감. 지나간 자리에 가는 일섬 선이 남고 잠시 뒤 터짐. 돌진 중 무적.",
                     src="56라운드 원문 1번·Q2", ref="귀멸의 칼날 '벽력일섬'(도영 님 원문)",
                     en="the lightning-flash draw cut: he has just dashed straight forward through a line of three enemies, about four body-lengths in a single blink, and is now crouched low at the far end with the blade fully extended behind him; behind him one perfectly straight, razor-thin glowing amber line runs across the ground and through the enemies, who are frozen mid-step a split second before they burst apart; a trail of ash and ember sparks marks his path."),
                dict(ko="그림자 분신", desc="일섬 0.2초 뒤 어두운 재 실루엣이 출발점→도착점을 같은 선으로 달려 다시 벰(피해 50%). 검기 3단일 때도 분신이 따라 벰.",
                     src="56라운드 원문 1번·Q3·Q13", ref="자체 설계(도영 님 원문 '플레이어의 그림자 같은 존재')",
                     en="the shadow echo: right after his dash, a pitch-dark ash silhouette of himself - a featureless shadow copy, faintly smoking, with one dim ember for an eye - races along the very same straight line from the starting point and cuts it again; the old amber cut line flares up again where the shadow's blade passes; the real hero stands at the end of the line, looking back over his shoulder."),
                dict(ko="검기 3단", desc="칼 고유 자원. 타격으로 조금씩, 패링 성공 시 1단 즉시 충전. 칼날 빛 재→호박→백열. 소모하면 일섬 강화, 3단이면 그림자 분신.",
                     src="56라운드 Q13~Q20", ref="몬스터 헌터 태도 기인 게이지(3단 색), 세키로(간파로 자원)",
                     en="sword spirit rising in three stages: three close views of the hero's katana raised side by side, each edge glowing stronger than the last - first a faint ash-gray smoulder along the edge, then a strong amber fire along the edge, then a white-hot pale gold blaze with heat haze and sparks; behind the third blade a faint shadow copy of the hero rises."),
            ]},
            {"grid": (2, 2), "panels": [
                dict(ko="간파 반격 자세", desc="낮은 납도 자세로 적의 찌르기를 받는 순간 반 발 비켜 흘리고 바로 반격 베기. 성공 시 'PARRY' 문구와 검기 1단.",
                     src="56라운드 Q21", ref="세키로(간파), 몬스터 헌터 태도(간파 베기)",
                     en="the foresight counter: a pikeman's thrust comes at him; at the instant of contact he has already slipped past the spear point with a short sidestep, the pike head glancing off in a burst of amber sparks and a pale flash ring that marks perfect timing, and his counter cut is already slicing up across the pikeman."),
                dict(ko="대치 일격", desc="한 적과 마주 서 멈춘 뒤 단 한 번 엇갈려 벰. 칼을 거두는 순간 뒤의 적이 일섬 선을 따라 갈라짐.",
                     src="56라운드 Q21", ref="고스트 오브 쓰시마(대치)",
                     en="the standoff: in an open patch of mud he and a single tall enemy duelist have just exchanged one cut and passed each other; the hero calmly slides the blade back into the scabbard, his back turned, while behind him the enemy stands frozen with one thin glowing amber line across his body, about to burst into ash; drifting ash hangs still in the air."),
                dict(ko="회전 베기", desc="둘러싸였을 때 낮게 한 바퀴 돌며 벰. 원 전체가 아닌 열린 한 획(끝이 재로 갈라짐).",
                     src="56라운드 Q21", ref="몬스터 헌터 태도(기인 대회전 베기)",
                     en="the spinning slash: surrounded by enemies on all sides, he spins low with the blade extended, leaving one ragged circular brush stroke of amber light around him - a single stroke, open at one end and splitting into ash, not a closed ring - and enemies are knocked back in every direction."),
                dict(ko="가드 불가 내려베기", desc="칼이 하얗게 달아오르는 긴 예고 뒤 두 손 내려베기. 방패·가드를 무시하고 세로로 가름.",
                     src="56라운드 Q21", ref="엘든 링(전기 '가드 불가의 칼날'), 세키로(위험 공격 예고 문법)",
                     en="the unblockable overhead cut: after a wind-up in which his blade glows white and ash swirls around him, he brings the katana down two-handed in one heavy vertical cut on a bucket-helmed brute hiding behind a tall rectangular pavise shield; the cut goes straight through, splitting shield and helm with one vertical white-hot line."),
            ]},
        ],
    },
    # ------------------------------------------------------------------ 대검 (53라운드 Q26: A 녹슨 츠바이헨더)
    "greatsword": {
        "ko": "대검",
        "ref_img": "../concept_weapons/raw_greatsword_A2.jpg",
        "weapon_en": (
            "His weapon is a huge rusted two-handed greatsword almost as long as his body: a long straight cross-guard with hooked tips, "
            "small parrying hooks above a leather-wrapped ricasso, a broad notched and chipped blade pitted with rust, a broken arrow shaft "
            "stuck in the blade, and amber soul-fire smouldering inside the deepest notch like embers. It is brutally heavy - every pose "
            "shows the weight: wide stance, the body dragged by the blade, mud and dust thrown up. "
        ),
        "sheets": [
            {"grid": (2, 2), "panels": [
                dict(ko="내려찍기 ↔ 휘두르기", desc="기본 연격. 정면 내려찍기와 가로 휘두르기가 번갈아 이어짐. 긴 선딜(들어 올리는 자세), 휘두른 뒤 몸이 끌려감, 8방향.",
                     src="56라운드 Q5·Q6", ref="몬스터 헌터 대검, 데드셀(무거운 무기 템포)",
                     en="his alternating heavy combo: a huge downward chop has just bitten deep into the ground in front of him, cracking the earth and throwing up mud, while the fading trace of the previous move - a wide horizontal sweep - still hangs at waist height as one broad brush stroke of dust and ash; his body is dragged forward by the weight, feet sliding in the mud."),
                dict(ko="모아 내려찍기", desc="오래 들어 올려 모았다가 내리찍음. 기본은 충격파 없이 칼 아래만 크게 패임(위력·경직).",
                     src="56라운드 Q10", ref="몬스터 헌터 대검(모아 베기 3단)",
                     en="the charged slam with no shockwave: having held the sword high above his head, blade smouldering brighter and brighter, he slams it straight down onto an enemy; the impact craters the ground directly under the blade, chunks of earth and mud fly up and the enemy is crushed - the impact stays local, no wave travels outward."),
                dict(ko="땅 꽂기 충격파", desc="개성 발현 후의 차지. 휘두르지 않고 칼을 땅에 꽂아 마우스 방향으로 좁은 충격파만 보냄.",
                     src="56라운드 원문 2번·Q10", ref="엘든 링(땅을 내리치는 충격파 전기류)",
                     en="the planted shockwave: he does not swing at all - he drives the greatsword point-first deep into the ground with both hands, and from the blade a straight, narrow shockwave of splitting earth and amber fire rips forward diagonally across the ground toward distant enemies, tossing them into the air; the sword stays planted upright."),
                dict(ko="울분", desc="대검 고유 자원. 가드로 막은 피해가 칼에 재 자국→잔불로 쌓임(퍼펙트 가드 2배, 그로기 중 가드가 가장 많이). 차지 내려찍기가 전부 소모.",
                     src="56라운드 Q13~Q20", ref="Nine Sols(막은 기운을 공격으로), 퍼스트 버서커: 카잔(가드·탈진)",
                     en="grudge: he blocks with the flat of the greatsword held across his body like a wall while several enemies hammer and stab at it and musket shots spark off the steel; every blocked blow leaves a dark ash scar on the blade that is slowly turning into glowing embers, the notches filling with amber heat; his single eye blazes with mounting hatred."),
            ]},
            {"grid": (2, 2), "panels": [
                dict(ko="어깨 태클", desc="칼을 뒤로 끌며 어깨로 들이받음. 방패병 자세 무너뜨림, 연계 중간에 끼워 넣는 짧은 기술.",
                     src="56라운드 Q22", ref="몬스터 헌터 대검(태클)",
                     en="the shoulder tackle: dragging the greatsword low behind him, he rams his armored shoulder into a pavise-shield brute; the shield caves in and the enemy staggers backward off balance, dust bursting from the impact."),
                dict(ko="버티기 올려베기", desc="낮게 버티는 동안 맞아도 밀리지 않음(재가 떨어짐), 이어 크게 올려베어 적을 띄움.",
                     src="56라운드 Q22", ref="엘든 링(전기 '버티기(올려베기)')",
                     en="the enduring rising slash: he crouches with the sword low while enemy blows and an arrow strike him without moving him at all - ash chips fly off his shell - and then he rips the greatsword upward in a huge rising cut that launches an enemy into the air, a vertical brush stroke of dust and amber following the blade."),
                dict(ko="공중제비 도약 찍기", desc="앞으로 뛰어 공중제비를 돌며 칼과 함께 회전, 착지 지점을 크게 내려찍음.",
                     src="56라운드 Q22", ref="엘든 링(전기 '사자의 발톱')",
                     en="the somersault leap slam: he is upside down in mid-air at the top of a forward flip high above a group of enemies, the greatsword whirling with him in a vertical arc of ash, about to crash down on them; a ring of dust is already rising from the landing spot below."),
                dict(ko="막다가 떼면 돌진", desc="가드 중 막은 뒤 가드를 떼는 순간 낮게 돌진하며 칼을 끌어 적 줄을 들이받음.",
                     src="56라운드 Q22", ref="몬스터 헌터 대검(가드 후 태클 연계)",
                     en="the guard-release charge: with sparks and ash still on the raised blade from a block, he bursts forward out of his guard in a low charge, the blade dragged at his side carving a long furrow of torn earth behind him, ploughing through a line of enemies."),
            ]},
        ],
    },
    # ------------------------------------------------------------------ 단검 (53라운드 Q26: B 재 껍데기 송곳니, 역수)
    "dagger": {
        "ko": "단검",
        "ref_img": "../concept_weapons/raw_dagger_B.jpg",
        "weapon_en": (
            "His weapon is a dagger: a fang-shaped shard broken off his own ash shell - a short, thick, curved spike of cracked charcoal "
            "with amber soul-fire veins in its cracks and a white-hot glowing tip, its base wrapped in dirty bandage with a rusty nail "
            "driven through. He holds it in a reverse grip, the blade pointing down out of the bottom of his fist. He is fast and "
            "predatory, low to the ground, darting. "
        ),
        "sheets": [
            {"grid": (2, 2), "panels": [
                dict(ko="고속 찌르기", desc="빠른 기본 찌르기 연타. 수평 사거리 ×1.5·무기 1.3배·피해 ×1.4(56 Q4). 숫돌 불꽃 같은 짧은 직선 줄.",
                     src="56라운드 원문 9번·Q4", ref="데드셀(단검류 빠른 연타)",
                     en="rapid thrusts: he lunges in from a distance at a musketeer and stabs again and again with the reverse-grip fang dagger, several short, sharp, straight amber spark streaks like whetstone sparks radiating from the point of impact in quick succession, his arm blurred with speed."),
                dict(ko="그림자 걸음", desc="몸이 재로 흩어져 대상 적의 등 뒤에서 다시 뭉침. 낙인 기폭의 방아쇠.",
                     src="56라운드 Q13~Q20", ref="데드셀(스킬 '페이저' 등 뒤 순간이동)",
                     en="the shadow step: his body bursts into a cloud of ash and ember sparks in front of an enemy and reforms directly behind that enemy in the same instant, a faint trail of ash linking the two spots on the ground; he reappears crouched behind the enemy's back, dagger raised."),
                dict(ko="낙인 표식 · 기폭", desc="같은 적을 칠 때마다 낙인(등 뒤 2, 최대 5). 그림자 걸음으로 그 적 뒤로 가면 전부 폭발.",
                     src="56라운드 Q13~Q20", ref="하데스(쌓였다 터지는 저주 '파멸' 계열)",
                     en="brand and detonate: an enemy soldier is covered with five small glowing amber brand marks, claw-like cracks burned into his armor, and in the same instant, as the hero appears behind him, all the marks erupt together in a burst of amber fire and ash shards from inside the enemy."),
                dict(ko="등 뒤 치명 찌르기", desc="적의 등 뒤에서 찌르면 치명타. 투구와 갑옷 틈을 내려찌르는 백열 섬광.",
                     src="56라운드 Q23", ref="데드셀(암살자의 단검 — 등 뒤 치명타), 하데스 2(자매 단검)",
                     en="the backstab: from directly behind a big pavise brute, he drives the fang dagger down into the gap between helm and armor at the back of the neck; a sharp white-hot flash and a starburst of amber sparks at the point, the enemy arching in shock."),
            ]},
            {"grid": (2, 2), "panels": [
                dict(ko="부채꼴 투척", desc="팔을 휘둘러 재 송곳니 단검 여러 자루를 부채꼴로 던짐. 근거리 견제·낙인 쌓기.",
                     src="56라운드 Q23", ref="데드셀(투척 칼), 하데스 2(자매 단검 투척)",
                     en="the fan throw: with one sweep of his arm he throws five ash-fang daggers in a wide fan; each flying blade trails a thin amber streak, and several enemies in front are pinned by them."),
                dict(ko="고속 난타", desc="한 적에게 짧은 베기를 아주 빠르게 퍼부음. 팔 잔상, 짧은 교차 칼자국 다발.",
                     src="56라운드 Q23", ref="하데스 2(자매 단검 연타), 데드셀(단검 연타)",
                     en="the flurry: a blur of countless rapid cuts against one enemy, his arm multiplied into afterimages, a dense knot of short crossing amber nicks covering the enemy, ash flakes spraying everywhere."),
                dict(ko="그림자 분신 교차 베기", desc="주인공과 재 그림자 분신이 반대쪽에서 동시에 지나가며 X로 교차해 벰.",
                     src="56라운드 Q23", ref="자체 설계(칼의 그림자 분신과 짝)",
                     en="the shadow cross-cut: he and a pitch-dark ash shadow copy of himself dash past one enemy from opposite sides at the same moment, their two cuts crossing as a sharp X of amber lines through the enemy."),
                dict(ko="과열", desc="단검 고유. 과열이 차면 낙인이 더 빨리 쌓이고, 100%면 주변 낙인 일괄 자동 폭발 후 식는 동안 잠깐 느려짐.",
                     src="56라운드 Q13~Q20", ref="56라운드 결정(과열 꽉 차면 자동 폭발·식힘) — 연구 원칙 '연타로 채움'",
                     en="overheat: his dagger and forearm glow white-hot, heat haze and smoke pour from the cracks of his body and the ground around him is scorched; all the branded enemies around him explode at once in a ring of amber bursts, while he hunches over, venting ash like steam, briefly sluggish as he cools."),
            ]},
        ],
    },
    # ------------------------------------------------------------------ 활 (53라운드 Q26: B 혼불 시위 + 몸에서 화살 뽑기)
    "bow": {
        "ko": "활",
        "ref_img": "../concept_weapons/raw_bow_B.jpg",
        "weapon_en": (
            "His weapon is a longbow whose limbs are hardened ash and earth around an old pike shaft, with thin amber cracks along the "
            "limbs and shards of armor plate capping both tips; its bowstring is a single thread of amber soul-fire, the only glowing "
            "line on the weapon. His arrows are the broken arrow shafts pulled out of his own body: dark shafts whose heads catch amber "
            "fire when nocked. "
        ),
        "sheets": [
            {"grid": (2, 2), "panels": [
                dict(ko="당겨 떼기 정밀 사격", desc="누르면 당기고 떼면 발사(자동 발사 없음, 당기는 중 이동 50%). 가득 당긴 직후 0.15초 안에 떼면 완벽 놓기 섬광 + 강화 화살.",
                     src="56라운드 원문 9번·Q9·Q20", ref="하데스(코로나흐트 파워샷 완벽 창)",
                     en="the drawn precise shot with a perfect release: he holds the soul-fire string at full draw and releases at the perfect instant - a bright pale-gold flash bursts at the bow, the arrow leaves as a dense amber streak with a ring-shaped shock wave behind it, the soul-fire string still quivering."),
                dict(ko="관통 화살", desc="한 발이 일렬의 적을 꿰뚫고 계속 날아감.",
                     src="56라운드 Q24", ref="몬스터 헌터 활(관통 타입)",
                     en="the piercing arrow: one heavy arrow has passed straight through three enemies standing in a row, a straight line of amber fire with puffs of ash where it pierced each one, the arrow still flying on beyond them."),
                dict(ko="화살비", desc="하늘로 쏘아 올린 화살이 앞쪽 원형 구역에 비처럼 쏟아짐.",
                     src="56라운드 Q24", ref="엘든 링(전기 '화살비')",
                     en="the arrow rain: he looses an arrow straight up into the dark sky; over a circular zone of enemies ahead, dozens of burning arrows fall like rain, the zone on the ground marked by falling embers, enemies pinned and scattering."),
                dict(ko="속사 연사", desc="짧게 당겨 여러 발을 빠르게 이어 쏨. 한 발 위력은 약함.",
                     src="56라운드 Q24", ref="데드셀(퀵 보우), 엘든 링(전기 '속사')",
                     en="rapid fire: at short range he fires arrow after arrow in a quick barrage, three or four arrows in flight at once in a tight stream, his drawing hand a blur, sparks of soul-fire flicking off the string."),
            ]},
            {"grid": (2, 1), "panels": [
                dict(ko="숨 (감속 정밀 조준)", desc="활 탄창 자리 = 숨. 완벽 놓기 시 화살 미소모·숨 회복, 숨이 차면 짧은 감속 정밀 조준.",
                     src="56라운드 Q13~Q20", ref="고스트 오브 쓰시마(활 조준 집중 감속), 호라이즌 제로 던(집중)",
                     en="breath, slowed-time precision aim: the world around him is drained of light and frozen - drifting ash stopped mid-air, an enemy musketeer frozen in the act of firing, a musket ball hanging in the air - and only the hero, his burning eye, the glowing string and the arrowhead stay vivid; a thin amber aim line stretches to the enemy's head; a slow breath of ash leaves his mouthless face."),
                dict(ko="재장전 (몸에서 뽑기)", desc="'숨 + 재장전 유지'(56라운드 Q13~Q20)의 재장전 동작. 자기 몸에 꽂힌 화살을 뽑아 시위에 메김(53라운드 Q26). 요청 5종 외 참고 패널.",
                     src="53라운드 Q26 · 56라운드 Q13~Q20", ref="자체 설계(주인공 몸에 꽂힌 화살)",
                     en="reload from his own body: he pulls a broken arrow shaft out of his own shoulder - ash crumbling from the wound, a flicker of soul-fire escaping - to nock it on the soul-fire string; the arrowhead ignites amber as it touches the string."),
            ]},
        ],
    },
}
