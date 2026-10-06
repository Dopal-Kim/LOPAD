#!/usr/bin/env python3
"""Gemini 카드 콘셉트 생성 — 키는 클라우드 프록시가 붙인다(이 스크립트는 키를 읽거나 남기지 않음).

python3 gen.py [id ...] [--tag a] [--weapon katana] [--missing] [--jobs 4] [--extra "추가 지시"]
결과: raw/<id>_<tag>.jpg (512×512 로 줄여 보관 — 빌드 입력) · 기록 prompts.json (프롬프트·모델·시각·http·성공 여부, 이미지 데이터·키 없음)
"""
import argparse, base64, io, json, os, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cards as C  # noqa

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODEL = "gemini-3.1-flash-image"
LOG = os.path.join(HERE, "prompts.json")


def load_log():
    if os.path.exists(LOG):
        return json.load(open(LOG, encoding="utf-8"))
    return {"note": "61 단계 5 개성 카드 그림 Gemini 콘셉트 기록 — 키 없음(프록시가 붙임). prompt = STYLE + CAST + WEAPON[무기] + THE MOMENT(scene). 원본은 raw/<id>_<tag>.jpg(512 로 줄여 보관).",
            "model": MODEL, "style": C.STYLE, "cast": C.CAST, "weapon": C.WEAPON, "cards": {}}


def call(body):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body, f)
        path = f.name
    try:
        out = subprocess.run(["curl", "-sS", "--max-time", "240", "-H", "Content-Type: application/json",
                              "-w", "\n%{http_code}", "-d", "@" + path, URL.format(model=MODEL)],
                             capture_output=True, text=True)
    finally:
        os.unlink(path)
    txt, _, code = out.stdout.rpartition("\n")
    return int(code or 0), txt


def gen_one(card, tag, extra):
    cid, weapon = card[0], card[1]
    prompt = C.prompt_for(card)
    if extra:
        prompt += "\n\n" + extra
    ref = os.path.join(HERE, "ref", f"ref_{weapon}.png")
    parts = [{"text": prompt + "\n\nThe attached image is the character/weapon reference sheet (game sprites): match these designs, but draw a new scene."},
             {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(open(ref, "rb").read()).decode()}}]
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "1:1"}}}
    rec = {"tag": tag, "model": MODEL, "ref": os.path.relpath(ref, HERE), "extra": extra or None}
    for attempt in range(4):
        t0 = time.time()
        code, txt = call(body)
        rec.update({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "http": code, "seconds": round(time.time() - t0, 1)})
        img = None
        if code == 200:
            try:
                js = json.loads(txt)
                cand = js.get("candidates", [{}])[0]
                rec["finishReason"] = cand.get("finishReason")
                rec["modelVersion"] = js.get("modelVersion")
                for p in cand.get("content", {}).get("parts", []):
                    if "inlineData" in p:
                        img = base64.b64decode(p["inlineData"]["data"])
            except Exception as e:  # noqa
                rec["parseError"] = str(e)
        else:
            rec["error"] = txt[:300]
        if img:
            im = Image.open(io.BytesIO(img)).convert("RGB")
            rec["rawSize"] = list(im.size)
            im = im.resize((512, 512), Image.LANCZOS)
            os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
            im.save(os.path.join(HERE, "raw", f"{cid}_{tag}.jpg"), quality=93)
            rec["ok"] = True
            return cid, rec
        if code in (429, 500, 503, 0):
            time.sleep(15 * (attempt + 1))
            continue
        break
    rec["ok"] = False
    return cid, rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--tag", default="a")
    ap.add_argument("--weapon")
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--extra", default="")
    a = ap.parse_args()
    cards = [c for c in C.CARDS if (not a.ids or c[0] in a.ids) and (not a.weapon or c[1] == a.weapon)]
    if a.missing:
        cards = [c for c in cards if not os.path.exists(os.path.join(HERE, "raw", f"{c[0]}_{a.tag}.jpg"))]
    log = load_log()
    with ThreadPoolExecutor(a.jobs) as ex:
        for cid, rec in ex.map(lambda c: gen_one(c, a.tag, a.extra), cards):
            card = C.by_id()[cid]
            ent = log["cards"].setdefault(cid, {"weapon": card[1], "name": card[2], "conceptKo": card[3], "scene": card[4],
                                                "pair": card[5], "generations": []})
            ent["scene"] = card[4]
            ent["generations"].append(rec)
            json.dump(log, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(cid, rec["tag"], rec["http"], rec["ok"], rec.get("finishReason"), rec.get("seconds"), flush=True)


if __name__ == "__main__":
    main()
