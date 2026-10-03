#!/usr/bin/env python3
"""Gemini 이미지 생성 호출기 — 53라운드 무기 개념 시안용 사본 (gen.py 와 동일, 결과·기록은 concept_weapons/ 안에만).

키는 클라우드 프록시가 붙인다 — 이 스크립트는 키를 읽지도, 쓰지도, 로그에 남기지도 않는다.
사용:
  python3 gen_weapons.py <weapon_A> --prompt-file prompt_<weapon_A>.txt [--model gemini-3.1-flash-image]
                 [--ref path.png ...] [--aspect 16:9] [--tag a]
결과: raw_<id>_<tag>.jpg, raw_<id>_<tag>.json (모델·프롬프트·참고 이미지 경로·응답 메타, 이미지 데이터 제외)
모든 호출(성공·실패)은 concept_weapons/gen_log.jsonl 에 한 줄씩 기록 — 생성 횟수 집계용.
"""
import argparse, base64, json, os, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))  # = concept_weapons/
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def call(model, body):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body, f)
        path = f.name
    try:
        out = subprocess.run(
            ["curl", "-sS", "--max-time", "300", "-H", "Content-Type: application/json",
             "-w", "\n%{http_code}", "-d", "@" + path, URL.format(model=model)],
            capture_output=True, text=True)
    finally:
        os.unlink(path)
    txt = out.stdout
    body_txt, _, code = txt.rpartition("\n")
    return int(code or 0), body_txt, out.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--model", default="gemini-3.1-flash-image")
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--tag", default="a")
    ap.add_argument("--retries", type=int, default=4)
    a = ap.parse_args()

    d = HERE  # id 는 기록용 이름(무기_안)
    os.makedirs(d, exist_ok=True)
    prompt = open(a.prompt_file, encoding="utf-8").read().strip()
    parts = [{"text": prompt}]
    for r in a.ref:
        with open(r, "rb") as f:
            mime = "image/jpeg" if r.lower().endswith((".jpg", ".jpeg")) else "image/png"
            parts.append({"inlineData": {"mimeType": mime, "data": base64.b64encode(f.read()).decode()}})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": a.aspect}}}

    for attempt in range(a.retries):
        t0 = time.time()
        code, txt, err = call(a.model, body)
        rec = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "id": a.id, "tag": a.tag, "model": a.model,
               "aspect": a.aspect, "refs": [os.path.relpath(r, HERE) for r in a.ref], "http": code,
               "seconds": round(time.time() - t0, 1)}
        img = None
        meta = {}
        if code == 200:
            try:
                js = json.loads(txt)
                cand = js.get("candidates", [{}])[0]
                for p in cand.get("content", {}).get("parts", []):
                    if "inlineData" in p:
                        img = base64.b64decode(p["inlineData"]["data"])
                        meta["mime"] = p["inlineData"].get("mimeType")
                    elif "text" in p:
                        meta.setdefault("text", []).append(p["text"])
                meta["finishReason"] = cand.get("finishReason")
                meta["usage"] = js.get("usageMetadata")
                meta["modelVersion"] = js.get("modelVersion")
            except Exception as e:  # noqa
                meta["parseError"] = str(e)
        else:
            meta["error"] = txt[:600]
        rec["ok"] = img is not None
        rec.update({k: v for k, v in meta.items() if k in ("finishReason", "error", "parseError")})
        with open(os.path.join(HERE, "gen_log.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if img is not None:
            ext = ".png" if (meta.get("mime") or "").endswith("png") else ".jpg"
            out = os.path.join(d, f"raw_{a.id}_{a.tag}{ext}")
            with open(out, "wb") as f:
                f.write(img)
            with open(os.path.join(d, f"raw_{a.id}_{a.tag}.json"), "w", encoding="utf-8") as f:
                json.dump({"model": a.model, "aspect": a.aspect, "prompt": prompt,
                           "refs": rec["refs"], "response": meta, "time": rec["time"]}, f,
                          ensure_ascii=False, indent=1)
            print("OK", out, meta.get("modelVersion"), meta.get("finishReason"))
            return 0
        print("FAIL", code, (meta.get("error") or meta.get("finishReason") or "")[:400], file=sys.stderr)
        if code in (429, 500, 503):
            time.sleep(20 * (attempt + 1))
            continue
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
