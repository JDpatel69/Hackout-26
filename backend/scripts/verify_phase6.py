"""Phase 6 end-to-end verification for the 'AI Trust Score' dual-model integration.

Run against a live backend on http://127.0.0.1:8000 with the venv that has httpx+PIL.
Exercises: model status, farm listing, sensor verify, image upload, dual verify,
trust-score composite, investor view-vs-run (403), and the verifier estimate-credits
regression. Prints a PASS/FAIL line per check and a final summary.
"""
from __future__ import annotations

import io
import sys

import httpx
from PIL import Image
import numpy as np

BASE = "http://127.0.0.1:8000/api"
USERS = {
    "farm_operator": "amina@greenalgae.co",
    "verifier": "elena@ecoaudit.org",
    "researcher": "marcus@oceanlab.edu",
    "investor": "sofia@impactvault.io",
}
PW = "password123"

results: list[tuple[bool, str]] = []


def check(cond: bool, label: str, detail: str = "") -> bool:
    results.append((cond, label))
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    return cond


def signin(client: httpx.Client, email: str) -> str | None:
    r = client.post(f"{BASE}/auth/signin", json={"email": email, "password": PW})
    if r.status_code != 200:
        print(f"   signin {email} -> {r.status_code} {r.text[:200]}")
        return None
    return r.json()["token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def synth_image() -> bytes:
    """A 512x512 image with a green algae-like blob so segmentation has something."""
    arr = np.full((512, 512, 3), (30, 60, 90), dtype=np.uint8)  # bluish water
    yy, xx = np.mgrid[0:512, 0:512]
    blob = ((xx - 256) ** 2 + (yy - 256) ** 2) < 150 ** 2
    arr[blob] = (40, 160, 55)  # green canopy
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def main() -> int:
    with httpx.Client(timeout=60.0) as client:
        tokens = {role: signin(client, email) for role, email in USERS.items()}
        for role, tok in tokens.items():
            check(tok is not None, f"signin {role}")
        if not all(tokens.values()):
            return 1

        op = auth(tokens["farm_operator"])
        inv = auth(tokens["investor"])
        vf = auth(tokens["verifier"])

        # 1) Model status — both trained, both ready
        r = client.get(f"{BASE}/ai/status", headers=op)
        st = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200, "GET /ai/status 200", str(r.status_code))
        check(
            st.get("image", {}).get("ready") and not st.get("image", {}).get("is_stub"),
            "image model ready & not stub",
            str(st.get("image")),
        )
        check(
            st.get("sensor", {}).get("ready") and not st.get("sensor", {}).get("is_stub"),
            "sensor model ready & not stub",
            str(st.get("sensor")),
        )

        # 2) Farm listing (operator-scoped)
        r = client.get(f"{BASE}/ai/farms", headers=op)
        farms = r.json() if r.status_code == 200 else []
        check(r.status_code == 200 and len(farms) > 0, "GET /ai/farms returns farms", f"{len(farms)} farms")
        if not farms:
            return 1
        farm_id = farms[0]["id"]
        print(f"   using farm_id={farm_id} ({farms[0].get('name')})")

        # 3) Sensor verify — real XGBoost biomass in rawOutput
        r = client.post(f"{BASE}/ai/sensor/verify", headers=op, json={"farmId": farm_id, "windowHours": 168})
        sv = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200, "POST /ai/sensor/verify 200", f"{r.status_code} {r.text[:160] if r.status_code!=200 else ''}")
        raw = (sv.get("rawOutput") or {})
        bm = raw.get("predicted_biomass_g_l", raw.get("predicted_biomass_g_L"))
        check(bm is not None, "sensor rawOutput has predicted biomass g/L", f"biomass={bm}")
        check(sv.get("isStub") is False, "sensor result is not a stub", f"isStub={sv.get('isStub')} verdict={sv.get('verdict')}")

        # 4) Image upload — real ONNX segmentation
        img_bytes = synth_image()
        r = client.post(
            f"{BASE}/ai/image/analyze/upload",
            headers=op,
            data={"farmId": farm_id, "source": "phone"},
            files={"file": ("pond.jpg", img_bytes, "image/jpeg")},
        )
        ia = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200, "POST /ai/image/analyze/upload 200", f"{r.status_code} {r.text[:160] if r.status_code!=200 else ''}")
        iraw = (ia.get("rawOutput") or {})
        check(ia.get("isStub") is False, "image result is not a stub", f"isStub={ia.get('isStub')}")
        check(
            "greenness" in iraw and ia.get("algaeCoveragePct") is not None,
            "image rawOutput has greenness + coverage",
            f"coverage={ia.get('algaeCoveragePct')} greenness={iraw.get('greenness')}",
        )

        # 5) Dual verify — composite + recommendation
        r = client.post(f"{BASE}/ai/dual-verify", headers=op, json={"farmId": farm_id, "imageSource": "phone", "windowHours": 168})
        dv = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200, "POST /ai/dual-verify 200", f"{r.status_code} {r.text[:160] if r.status_code!=200 else ''}")
        check(
            isinstance(dv.get("dualAiScore"), (int, float)) and dv.get("recommendation") in {"approve_ready", "needs_review", "reject_recommended"},
            "dual-verify composite score + recommendation",
            f"score={dv.get('dualAiScore')} reco={dv.get('recommendation')}",
        )

        # 6) Trust-score (operator) — ready
        r = client.get(f"{BASE}/ai/trust-score/{farm_id}", headers=op)
        ts = r.json() if r.status_code == 200 else {}
        check(r.status_code == 200 and ts.get("status") == "ready", "GET /ai/trust-score (operator) ready",
              f"status={ts.get('status')} score={ts.get('dualAiScore')}")

        # 7) Trust-score (investor) — view allowed
        r = client.get(f"{BASE}/ai/trust-score/{farm_id}", headers=inv)
        check(r.status_code == 200, "GET /ai/trust-score (investor) allowed (view)", str(r.status_code))

        # 8) Investor CANNOT run (403 on dual-verify and sensor verify)
        r = client.post(f"{BASE}/ai/dual-verify", headers=inv, json={"farmId": farm_id})
        check(r.status_code == 403, "investor dual-verify -> 403", str(r.status_code))
        r = client.post(f"{BASE}/ai/sensor/verify", headers=inv, json={"farmId": farm_id})
        check(r.status_code == 403, "investor sensor/verify -> 403", str(r.status_code))
        r = client.post(f"{BASE}/ai/image/analyze/upload", headers=inv,
                        data={"farmId": farm_id, "source": "phone"},
                        files={"file": ("pond.jpg", img_bytes, "image/jpeg")})
        check(r.status_code == 403, "investor image upload -> 403", str(r.status_code))

        # 9) Regression: verifier estimate-credits still works (runs dual-verify server-side)
        r = client.get(f"{BASE}/verifier/requests", headers=vf)
        reqs = r.json() if r.status_code == 200 else []
        if reqs:
            rid = reqs[0]["id"]
            r = client.get(f"{BASE}/verifier/requests/{rid}/estimate-credits", headers=vf)
            ec = r.json() if r.status_code == 200 else {}
            check(r.status_code == 200 and "estimatedCredits" in ec,
                  "verifier estimate-credits regression", f"{r.status_code} keys={list(ec.keys())}")
        else:
            check(False, "verifier estimate-credits regression", "no verification requests seeded")

    passed = sum(1 for ok, _ in results if ok)
    total = len(results)
    print(f"\n=== Phase 6 summary: {passed}/{total} checks passed ===")
    failed = [label for ok, label in results if not ok]
    if failed:
        print("FAILED:")
        for f in failed:
            print(f"  - {f}")
    return 0 if passed == total else 2


if __name__ == "__main__":
    sys.exit(main())
