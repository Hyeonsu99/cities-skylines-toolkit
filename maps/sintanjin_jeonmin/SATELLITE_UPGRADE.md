# 위성 오버레이 해상도 개선 (2026-11-17)

- 기존 Esri 줌 15 기반 4096×4096 이미지와 비교해, 줌 17 기반 8192×8192 오버레이를 생성했습니다.
- `map_metadata.json`의 기존 범위를 사용합니다. 지형·자원·게임 설정은 변경하지 않습니다.
- 게임 Overlays 폴더의 `Sintanjin_Jeonmin_145x_Satellite_Overlay.png`에 적용했으며, 기존 이미지는 `.bak` 파일로 보존했습니다. 인게임 정렬·표시 확인은 미완료입니다.
- 생성: `python maps/tools/generate_satellite_overlay.py`
- 검사: `python maps/tools/test_satellite_overlay.py`
- 비교 미리보기: `../../output/satellite_quality_comparison.png` (로컬 생성물).
- 생성 PNG와 원본 다운로드 캐시는 Git에서 제외합니다. 다른 PC에서는 생성 명령을 실행하거나 별도로 파일을 옮겨야 합니다. 기존 4096 이미지는 `--size 4096`으로 생성할 수 있습니다.
- 영상 출처: Esri World Imagery, Vantor, Earthstar Geographics, GIS User Community.
  https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer
