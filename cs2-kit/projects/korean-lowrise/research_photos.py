"""M0 거리뷰 근거 수집. 기존 키트 캡처기를 사용하며 원본은 커밋하지 않는다."""
import concurrent.futures
import json
from pathlib import Path
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import naver_pano_view as pano

POINTS = {
    "A1": (127.425, 36.450), "A2": (127.426, 36.452), "A5": (127.424, 36.448),
    "B2": (127.387, 36.434), "B4": (127.392, 36.423),
    "C1": (127.426, 36.441), "C4": (127.426, 36.440),
}

PUBLIC_D = [
    ("https://www.joongdo.co.kr/web/view.php?key=20250303010000241", "https://dn.joongdo.co.kr/mnt/images/file/2025y/03m/04d/2025030301000044700002413.jpg", "청양, 붉은 벽돌과 청색 지붕; 주택 전용 사례는 아님"),
    ("https://thebogi.com/595", "https://img1.daumcdn.net/thumb/R1280x0/?fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2Fbztufg%2Fbtsycsi7rCk%2Fp9C47rixRcbZkrpNzdPKXK%2Fimg.jpg&scode=mtistory2", "경북 농가, 청색 지붕·전면 차양"),
    ("https://www.fnnews.com/news/202002051459450744", "https://image.fnnews.com/resource/media/image/2020/02/05/202002051500559216_e.jpg", "임실 빈집 개보수, 청색 지붕·낮은 처마"),
    ("https://sigoljibmeme.com/board/16806", "https://sigoljibmeme.com/files/attach/images/2025/12/09/ee92176a40a164f4a09bd32912916981.jpg", "산청, 청색 지붕·노출 목구조 처마"),
    ("https://www.janews.co.kr/news/articleView.html?idxno=5378", "https://cdn.janews.co.kr/news/photo/200807/5378_2036_2830.jpg", "진안, 청색 지붕·주황 처마선"),
    ("https://sigoljibmeme.com/board/17939", "https://sigoljibmeme.com/files/attach/images/2026/01/18/557dadf5222f58fe3499fd5777bc2f2d.jpg", "안성, 청색 지붕·주황 테두리·부속 창고"),
]

SELECTED = {
    "A": ["A1_000", "A1_180", "A2_000", "A2_270", "A5_180", "A5_270"],
    "B": ["B4_000", "B4_090", "B4_270", "B4_030", "B4_330", "B2_270"],
    "C": ["C1_000", "C1_090", "C1_330", "C1_040", "C4_000", "C4_270"],
}


def provenance(records):
    index = {r["key"]: r for r in records if "pid" in r}
    for key, yaws in {"B4": (30, 330), "C1": (330, 40)}.items():
        meta, faces = pano.faces(str(HERE / "photos"), index[key]["pid"])
        for yaw in yaws:
            path = HERE / "photos" / f"{key}_{yaw:03}.png"
            if not path.exists():
                pano.render(meta, faces, yaw, 10, 78, W=1200, H=850).save(path)
    lines = ["# 한국형 저밀도 주거 사진 출처", "",
             "조회·검토일: 2026-11-18. 사진은 로컬 검토용이며 저작권 이미지·큐브맵은 커밋하지 않는다.",
             "A/B/C는 대전 현지 거리뷰, D는 지역 밖 공개 사진을 통한 유형 보조 근거다. 위성만으로 재료·층수·높이를 확정하지 않았다.",
             "선정 6장씩, 총 24장. 같은 건물의 서로 다른 시점도 포함하며 24개 독립 건물 표본을 뜻하지 않는다.", "",
             "## A/B/C — 네이버 거리뷰", "",
             "기존 `tools/naver_pano_view.py`로 직접 저장. yaw는 북=0°·동=90°, pitch=10°, 수평 fov=78°, 1200×850.",
             "실제 상호는 관찰 자료에만 있으며 생성 텍스처에는 사용하지 않는다.", "",
             "| 유형 | 파일 | 촬영일시 | 위도, 경도 | 위치 | 파노라마 ID / 출처 | yaw/pitch/fov |",
             "|---|---|---|---|---|---|---|"]
    for kind, names in SELECTED.items():
        for name in names:
            key, yaw = name.split("_")
            r = index[key]
            m = r["metadata"]
            info = m["info"]
            lines.append(f'| {kind} | `{name}.png` | {info["photodate"]} | {m["latitude"]}, {m["longitude"]} | {info["description"]} {info["title"]} | [{r["pid"]}](https://map.naver.com/p?c=18.00,0,0,0,dh&p={r["pid"]}) | {int(yaw)}/10/78 |')
    lines += ["", "## D — 지역 밖 유형 보조 사진", "",
              "평촌·목상 후보 거리뷰는 철도·공장·수목에 가려 단층 주택을 확보하지 못했다. 아래 6장은 국내 다른 지역의 형태 근거이며 대전 현장 관찰로 취급하지 않는다.",
              "촬영일시·정확한 좌표는 미확인. 지붕 사진만으로 컬러강판/금속기와/슬레이트의 세부 재질을 확정하지 않는다. M3 전 지역 근접 사진으로 보완한다.", "",
              "| 파일 | 공개 페이지 | 관찰 대상 |", "|---|---|---|"]
    for i, (page, url, note) in enumerate(PUBLIC_D, 1):
        path = HERE / "photos" / f"D_public_{i:02}.jpg"
        if not path.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                path.write_bytes(response.read())
        lines.append(f"| `{path.name}` | [공개 원문]({page}) | {note} |")
    lines += ["", "## 검토 관찰", "",
              "- A: 낮은 담장·대문, 붉은 벽돌, 평지붕/녹색 상부와 기와 처마가 혼재한다. 거리뷰에서 보이지 않는 옥상 설비·정확한 외부계단 치수는 추정이다.",
              "- B: 관평동 B4는 3층+박공 다락, 1층 가게·차양, 상층 주택 창이 반복된다. B2는 송강동 상가주택 맥락으로 별도 기록한다.",
              "- C: 덕암동 C1은 필로티 위 주거층, 기둥·차량 주차·작은 금속 창난간이 보인다. C4는 옛 벽돌 다세대 입면 보조 자료로 4층 필로티를 증명하지 않는다.",
              "- D: 단층 낮은 처마, 청색 지붕, 주황 끝선, 전면 차양과 부속 창고가 유형 단서다. 지역 분포와 실제 재료는 후속 확인한다."]
    (HERE / "photos" / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def capture(item):
    key, (lon, lat) = item
    url = f"https://map.naver.com/p/api/panorama/nearby/{lon}/{lat}/3"
    request = urllib.request.Request(url, headers=pano.HDR)
    with urllib.request.urlopen(request, timeout=30) as response:
        features = json.loads(response.read())["features"]
        if not features:
            return dict(key=key, request=url, status="NO_PANORAMA")
        feature = features[0]
    pid = feature["properties"]["id"]
    meta, faces = pano.faces(str(HERE / "photos"), pid)
    for yaw in (0, 90, 180, 270):
        path = HERE / "photos" / f"{key}_{yaw:03}.png"
        if not path.exists():
            pano.render(meta, faces, yaw, 10, 78, W=1200, H=850).save(path)
    print(key, pid, flush=True)
    return dict(key=key, pid=pid, metadata=meta, request=url)


if __name__ == "__main__":
    (HERE / "photos").mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(capture, POINTS.items()))
    (HERE / "photos" / "capture_index.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    provenance(records)
