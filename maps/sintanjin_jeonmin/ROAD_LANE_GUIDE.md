# 도로·차선 오버레이

게임 Image Overlay에서 `Sintanjin_Jeonmin_145x_Road_Lanes_Overlay.png`를 선택합니다.
기존 위성 오버레이와 같은 범위·8192×8192 좌표 격자입니다. 위치·축척 설정은 기존 값을 사용합니다.

- 청록색: 차선 수가 등록된 도로의 폭 가이드
- 흰 점선: 등록된 차선 수를 균등하게 나눈 참고선
- 분홍색: 차선 수 미확인 구간의 도로 중심 경로
- 주황 점선: 지하 구간
- `4 L one-way`: 해당 일방통행 도로 4차로
- `4 L total`: 양방향 합계 4차로

2026-11-17 OpenStreetMap에서 받은 5,254개 도로 중 영역과 겹치는 지상 경로 4,840개를 표시했습니다.
513개는 차선 수 태그가 있고, 4,327개는 차선 수 미확인입니다. 지하 구간은 별도로 표시합니다.

**도로 폭은 차로당 3.25m를 가정한 도식입니다.** 실제 갓길·차로 폭·차선 도색 위치·교차로 유도선·회전 포켓을 측량하거나 사진에서 추출한 결과가 아닙니다.
OSM 차선 정보도 현황과 다를 수 있습니다. 교량 교차부에서는 모든 경로를 보여주므로 선이 겹칠 수 있습니다.
실제 도로 모양과 비교한 확대 미리보기: `../../output/road_lane_guide_detail.png`.

생성: `python maps/tools/render_road_lane_guide.py` (원본 OSM 캐시 `_imagery_cache/roads_osm.json` 필요)
검사: `python maps/tools/test_road_lane_guide.py`
파일 크기·좌표 계산·차선 파싱·선 오프셋 검사 및 출력 이미지 육안 확인 완료. 인게임 로딩은 미확인입니다.

도로 자료: © OpenStreetMap contributors, ODbL — https://www.openstreetmap.org/copyright
차선 태그 설명: https://wiki.openstreetmap.org/wiki/Key:lanes
영상: Esri / Vantor / Earthstar Geographics / GIS User Community.
