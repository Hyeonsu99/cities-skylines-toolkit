"""시대당 12시드: 키트 exporter/checker/renderer를 사용한 비교 시트."""
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
from house_core import HERE, build_and_export, seeded

KIT = HERE.parents[1]


def main():
    eras = sys.argv[1:] or ["70s", "80s", "90s"]
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
    records = []
    for era in eras:
        sheet = Image.new("RGB", (2080, 1560), "#e6e9ec")
        for seed in range(12):
            spec = seeded(era, seed)
            folder, summary = build_and_export(spec, HERE/"work"/"variety_assets", subobjects=False)
            folder = Path(folder)
            check = folder / "check.json"
            result = subprocess.run([sys.executable, str(KIT/"tools"/"check.py"), str(folder),
                                     "--json", str(check)], capture_output=True, text=True, encoding="utf-8")
            errors = json.loads(check.read_text(encoding="utf-8"))[0]["errors"]
            preview = folder / "preview.png"
            subprocess.run([sys.executable, str(KIT/"tools"/"render.py"), str(folder), "-o", str(preview),
                            "--views", "iso", "--size", "520x440", "--nolabel"],
                           check=True, capture_output=True)
            x, y = (seed % 4)*520, (seed // 4)*520
            with Image.open(preview) as im:
                sheet.paste(im.convert("RGB"), (x, y+72))
            draw = ImageDraw.Draw(sheet)
            draw.text((x+12, y+8), f"{era} / seed {seed:02} / {spec.finish}", font=font, fill="#17242b")
            draw.text((x+12, y+31), f"{spec.width}x{spec.depth} / {spec.balcony} / {'L-plan' if spec.notch else 'rectangle'}", font=font, fill="#17242b")
            draw.text((x+12, y+53), f"{'shop' if spec.shop else 'home'} / {spec.roof_prop} / {summary['tris']['main']} tris", font=font, fill="#17242b")
            records.append(dict(era=era, seed=seed, asset=summary["asset"], summary=summary,
                                geometry="PASS" if result.returncode == 0 else "FAIL", errors=errors))
            print(era, seed, records[-1]["geometry"], [e["key"] for e in errors], flush=True)
        sheet.save(HERE/"work"/f"variety_{era}.png")
    path = HERE/"work"/"variety_manifest.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    path.write_text(json.dumps([r for r in old if r["era"] not in eras] + records,
                               ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
