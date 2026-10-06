#!/usr/bin/env python3
"""61 단계 6 — Gemini 콘셉트 호출기(입구 그림·수련장 지도). 키는 클라우드 프록시가 붙인다 — 이 스크립트는 키를 읽지도 쓰지도 않는다.

python3 gen.py [id ...] [--tag a] [--jobs 4] [--extra "추가 지시"] [--missing]
  id = doors.DOORS 의 키(예: outer_shop) 또는 map_training
원본: parts/art/work/gemini/paint61s6/<id>/raw_<tag>.jpg (+ raw_<tag>.json: 모델·프롬프트 전문·참고 이미지·응답 메타, 이미지 데이터·키 없음)
기록: parts/art/work/gemini/paint61s6/gen_log.jsonl (모든 호출 한 줄씩)
"""
import argparse, base64, io, json, os, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
RAW = os.path.normpath(os.path.join(HERE, "../gemini/paint61s6"))
sys.path.insert(0, HERE)
import doors as D  # noqa: E402

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODEL = "gemini-3.1-flash-image"


def prompt_for(gid):
    if gid == "map_training":
        return "\n\n".join([D.REF_NOTE.replace("an earlier piece of the same series", "the existing floor map of the same series"),
                            D.MAP_STYLE, D.MAP_TRAINING]), [os.path.join(ROOT, "assets/sprites/ui/map_bg_f1.png")]
    region, kind, ref, scene, light, ko = D.DOORS[gid]
    style = D.STYLE_TRAINING if region == "training" else D.STYLE
    refs = [os.path.join(ROOT, D.KEYART.format(ref))] if ref else [os.path.join(ROOT, D.KEYART.format("outer"))]
    note = D.REF_NOTE if ref else D.REF_NOTE + " Make it lighter, hazier and calmer than the reference."
    return "\n\n".join([note, style, D.COMPOSITION, scene]), refs


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


def gen_one(gid, tag, extra):
    prompt, refs = prompt_for(gid)
    if extra:
        prompt += "\n\n" + extra
    parts = [{"text": prompt}]
    for r in refs:
        parts.append({"inlineData": {"mimeType": "image/png", "data": base64.b64encode(open(r, "rb").read()).decode()}})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}}
    rec = {"id": gid, "tag": tag, "model": MODEL, "refs": [os.path.relpath(r, ROOT) for r in refs], "extra": extra or None}
    d = os.path.join(RAW, gid)
    os.makedirs(d, exist_ok=True)
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
        rec["ok"] = img is not None
        with open(os.path.join(RAW, "gen_log.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({k: v for k, v in rec.items()}, ensure_ascii=False) + "\n")
        if img:
            im = Image.open(io.BytesIO(img)).convert("RGB")
            rec["rawSize"] = list(im.size)
            im.save(os.path.join(d, f"raw_{tag}.jpg"), quality=94)
            json.dump(dict(rec, prompt=prompt), open(os.path.join(d, f"raw_{tag}.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            return gid, rec
        if code in (429, 500, 503, 0) or (code == 200 and not img):
            time.sleep(12 * (attempt + 1))
            continue
        break
    return gid, rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--tag", default="a")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--extra", default="")
    ap.add_argument("--missing", action="store_true")
    a = ap.parse_args()
    ids = a.ids or list(D.DOORS) + ["map_training"]
    if a.missing:
        ids = [i for i in ids if not os.path.exists(os.path.join(RAW, i, f"raw_{a.tag}.jpg"))]
    with ThreadPoolExecutor(a.jobs) as ex:
        for gid, rec in ex.map(lambda i: gen_one(i, a.tag, a.extra), ids):
            print(gid, rec["tag"], rec["http"], rec["ok"], rec.get("finishReason"), rec.get("seconds"), rec.get("error", "")[:120],
                  flush=True)


if __name__ == "__main__":
    main()
