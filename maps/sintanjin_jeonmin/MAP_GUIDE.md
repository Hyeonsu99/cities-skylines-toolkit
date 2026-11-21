# 신탄진·대덕산단·관평·전민동·대전 벤처 협동화 단지 CS2 하이트맵 가이드

Generated PNG files and download caches are not versioned. Run the commands below from the repository root:



## 1. 포함 범위 및 축척 (1.45× 확대 매핑)
요청하신 범위(**불무산·금강 북안 ~ 전민동·문지동·대전 벤처 협동화 단지·원촌교**, **송강·화암·관평·탑립 ~ 석봉동·신탄진역·신탄진고·평촌산단·대전철도차량정비단·회덕JC·회덕역**)만 **약 9.89 km × 9.89 km** 정사각 영역으로 잘라내어 시티즈: 스카이라인 2 기본 맵 크기(**14.336 km × 14.336 km**)에 **1.45배**로 꽉 차게 확대했습니다.
- 둔산동/정부청사 남쪽 및 대청호/계족산 동쪽 외곽은 제외했습니다.
- 실제 지형·능선(불무산 160.8m, 동측 산지)은 Copernicus GLO-30 C2 연속 DEM 기반으로 매끄럽게 유지하고, 금강·갑천 하상/제방과 공단·주거지 평지(목상·대덕산단, 석봉동, 신탄진·철도정비단, 관평·탑립, 전민·벤처단지)를 단차·웅덩이 없이 연속 평탄화했습니다.

| 항목 | 값 |
| --- | --- |
| 위도 범위 | 36.37552°N ~ 36.46448°N |
| 경도 범위 | 127.34938°E ~ 127.45962°E |
| 실측 / CS2 축척 | 9886.9 m → 14336.0 m (1.45×) |
| 플레이 맵 최저 / 최고 고도 | 16.8 m / 426.4 m |
| 권장 해수면 (Sea Level) | **24.0 m** (금강·갑천 수로 안정 수위) |

## 2. 파일별 용도 및 CS2 에디터 Import 설정

| 파일명 | 권장 Height Scale | 설명 |
| --- | --- | --- |
| **`heightmap_cs2_4096_1024m.png`** | **`1024 m`** | **[추천] 고정밀 하이트맵** (1.56cm 단위 정밀도, 월드맵과 클리핑 없이 호환) |
| **`heightmap_cs2_worldmap_1024m.png`** | **`1024 m`** | **[추천] 4× 외곽 월드맵** (계룡산·식장산·대청호 원경 포함, 플레이 경계 심리스 블렌딩) |
| `heightmap_cs2_4096_std4096m.png` | `4096 m` (기본값) | 에디터 Height Scale 변경 없이 기본 `4096 m` 그대로 Import용 |
| `heightmap_cs2_worldmap_4096m.png` | `4096 m` (기본값) | 기본 `4096 m` 설정과 짝을 이루는 외곽 월드맵 |
| `heightmap_cs2_4096_500m.png` | `500 m` | 플레이 영역 전용 초정밀 하이트맵 (0.76cm 단위, 월드맵 불필요 시) |
| `satellite_overlay_4096.png` | - | **Image Overlay 모드용 4096×4096 위성 오버레이** (하이트맵과 1:1 좌표 일치) |
| `resources_overlay_4096.png` | - | **Image Overlay 모드용 4096×4096 천연자원 배치 가이드** (비옥·석유·광물·지하수·산림) |
| `sintanjin_resources_256.bin` | - | `SintanjinMapBuilder` 모드용 `256×256` 천연자원 바이너리 (비옥·광물·석유·어업·지하수) |
| `sintanjin_trees.bin` | - | `SintanjinMapBuilder` 모드용 실측 위성·DEM 기반 산림/수변 식생 바이너리 (~8.4만 그루) |
| `sintanjin_roads.bin` | - | (모드에서 도로 배치 삭제됨, 참고용) Method A 간선도로·고속도로·철도 백본 바이너리 (IC 램프 제외) |

## 3. 적용 방법
1. `%UserProfile%\AppData\LocalLow\Colossal Order\Cities Skylines II\Heightmaps\` 폴더에 원하는 하이트맵 복사
2. (선택) `...\Overlays\` 폴더에 `satellite_overlay_4096.png` 복사
3. CS2 **Map Editor → Terrain → Import Heightmap**에서 하이트맵 선택 후 **Height Scale**을 표에 맞게 설정 (`1024 m` 권장, 월드맵 쓰면 **Import Worldmap**도 동일 스케일로 선택)
4. **Water → Sea Level**을 **`24.0 m`** 로 맞추면 금강·갑천 수로가 즉시 채워집니다.
5. `SintanjinMapBuilder` 모드가 설치되어 있으므로 에디터 또는 게임에서 **`F6`** (전체: 천연자원+실측 숲), **`Ctrl+Shift+R`** (천연자원만), **`Ctrl+Shift+T`** (숲/나무만), **`Ctrl+Shift+X`** (심은 나무 초기화), **`Ctrl+Shift+W`** (풍향 북북서→남남동) 단축키로 즉시 자동 반영됩니다. `Sintanjin_Command.txt` 명령은 `ALL`/`RESOURCE`/`TREE`/`CLEAR`/`WIND`입니다. 도로·철도 자동 배치 기능은 모드에서 삭제되었습니다(`sintanjin_roads.bin`은 참고용으로만 남음).
6. 백본 도로 깔기 후 회덕JC·신탄진IC·북대전IC 연결 램프만 바닐라 도로 커브 + `Move It`으로 매끄럽게 이어 주면 1:1 대전 북부 도로망이 완성됩니다.

## Recreating local images

Run `python maps/tools/generate_sintanjin_jeonmin_heightmap.py` for the base pack. See `SATELLITE_UPGRADE.md` and `ROAD_LANE_GUIDE.md` for the 8192 overlays. Existing local PNG files can also be copied separately.
