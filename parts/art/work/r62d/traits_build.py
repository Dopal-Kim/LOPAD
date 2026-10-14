"""62 루프 4 (P18 §1) '떠올릴 개성' 8장 — 발동 fx(traits_fx) + 카드 그림(traits_cards) + 유품 짝짝이 신 다시 그림."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import traits_fx  # noqa: E402
import traits_cards  # noqa: E402


def build():
    traits_fx.rc.b2.WRITTEN.clear()
    fx = traits_fx.build()
    atlas = traits_fx.rc.b2.to_atlas()
    cards = traits_cards.build()
    return {"fx": fx, "atlas": [a[:2] for a in atlas], "cards": cards}
