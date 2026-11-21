# -*- coding: utf-8 -*-
"""cs2-kit 결과물을 CS2 가져오기 전용 폴더(cs2-import/)로 모은다.

각 cs2-kit/projects/*/output/<에셋>/ 의 FBX·PNG 만 cs2-import/<에셋>/ 으로 복사한다.
대상 폴더는 매번 지우고 새로 만들어 옛 파일(_Gls 등)이 남지 않게 한다.
게임 Asset Importer 에서는 cs2-import/<에셋> 폴더만 고른다.

사용: python tools/sync_cs2_import.py            (전체)
      python tools/sync_cs2_import.py Seokbong   (이름에 포함된 문자열로 거르기)
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "cs2-kit" / "projects"
DST = ROOT / "cs2-import"
KEEP = {".fbx", ".png"}
# _Gls 는 창 앞에 두면 야간 떨림(cs2-kit/memory/LESSONS.md) -> 창 앞이 아닌 의도된 투명판 에셋만 허용
GLS_OK = {"NoiseWallClear_L1_1x1", "SintanjinTollgate_L1_6x4"}


def sync(name_filter=""):
    DST.mkdir(exist_ok=True)
    done = []
    for out in sorted(SRC.glob("*/output/*/")):
        if not out.is_dir() or not any(out.glob("*.fbx")) or name_filter not in out.name:
            continue
        dst = DST / out.name
        shutil.rmtree(dst, ignore_errors=True)
        dst.mkdir()
        for f in out.iterdir():
            if f.is_file() and f.suffix.lower() in KEEP:
                shutil.copy2(f, dst / f.name)
        done.append(dst)
    return done


if __name__ == "__main__":
    for d in sync(sys.argv[1] if len(sys.argv) > 1 else ""):
        files = list(d.iterdir())
        assert files and all(f.suffix.lower() in KEEP for f in files), d
        if d.name not in GLS_OK:
            assert not any("_Gls" in f.name for f in files), f"_Gls left in {d}"
        print(f"{d.relative_to(ROOT)}  ({len(files)} files)")
    # 로컬 확장 검사: 알베도 상한 경고 (실패시키지 않음)
    import albedo_check
    albedo_check.run(sys.argv[1] if len(sys.argv) > 1 else "")
