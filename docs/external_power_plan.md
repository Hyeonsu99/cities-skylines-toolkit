# 맵 외부 전력 연결 방법론 (CS2)

신탄진·전민 맵(`maps/sintanjin_jeonmin/`)에 외부 전력 연결(Outside Connection)을 넣어, 발전소 없이 전력을 수입하거나 남는 전력을 수출할 수 있게 하는 방법을 정리한다. 이 문서는 계획이며 코드는 아직 바뀌지 않았다.

표시 규칙(HandOff 기준): 게임 안에서 확인하지 않은 내용은 `인게임 미확인`, 근거를 찾지 못한 내용은 `미확인`.

---

## 1. 게임 메커니즘

### 1.1 수입·수출 방식
- 전력은 **송전선(Power Line, 고압선)** 을 통해 외부 연결과 거래한다. 도시에 전력이 모자라면 외부 연결로 이어진 송전선을 통해 **자동으로 수입**하고, 남으면 **자동으로 수출**한다. 플레이어가 따로 켜는 설정은 없다. [P1]
- 수입은 "꽤 비싸며" 사용량이 순간적으로 몰릴 때 쓰는 용도이고, 수출은 발전 비용을 일부 메우는 정도다. [P1] 패치에서 전력 수입 가격이 오른 적이 있다(수치 미확인). [G1]
- 전력 정보 화면의 **Electricity Trade** 계기로 수입·수출 여부를 본다. [P1]

### 1.2 연결 조건
1. 맵에 **전력 외부 연결 지점**이 있어야 한다. 맵 선택 화면의 맵 정보 → Outside Connections 항목에 전기가 표시되는지 확인한다. 대부분의 기본 맵에는 있다. [V1][S1]
2. 외부 연결 지점부터 도시까지 **고압 송전선**이 이어져야 한다.
3. 송전선(고압)과 도로·저압 전선망 사이에는 **변전소(Transformer Station)** 가 필요하다. 변전소는 총 변환 용량에 한계가 있고, 저압→고압으로 바꿔 수출도 한다. [P1]
4. 저압 전선(도로에 포함된 전선)은 용량이 작고, 송전선은 용량이 크다. [P1]

### 1.3 요금·수출입 가격
- 게임 코드에서 거래 가격은 `Game.Prefabs.OutsideTradeParameterData`(원본 `OutsideTradeParameterPrefab`)의 `m_ElectricityImportPrice`·`m_ElectricityExportPrice` 필드에 있다. 실제 수치는 미확인(게임 데이터 또는 인게임 예산 화면으로 확인). [L1]
- 시민에게 받는 전기 요금(`m_ElectricityFee`, 행복도 효과 `ElectricityFeeHappinessFactor`)은 외부 거래 가격과 별개다. [L1]

### 1.4 맵 에디터에서 연결 지점 만들기
- 에디터 검색창에 `outside`를 치면 맵 경계에 놓는 **작은 원 모양의 외부 연결 마커**가 나온다. 전력용(outside electricity connection)을 골라 경계 위에 놓는다. [S1]
- 송전선은 마커와 별개다. 검색창에 **`High Voltage`** 를 쳐야 그릴 수 있는 고압 송전선이 나온다(모델만 놓으면 전선이 없는 철탑만 생긴다). [S1]
- 마커에서 송전선을 맵 안쪽(시작 타일)까지 그린다. 게임 중에도 송전선을 맵 경계까지 끌고 가면 외부 연결이 생긴다는 공략이 있다(버전별 동작 인게임 미확인). [G2]
- 지하 고압 송전선으로 이웃과 거래하는 커스텀 맵 사례도 있다. [N1]

### 1.5 ECS 내부 구조(모드용, `Game.dll`에서 이름 확인)
로컬 `Cities2_Data/Managed/Game.dll`의 형식 이름으로 확인했다. 필드 의미는 이름에서 추정한 것이므로 미확인이다. [L1]

| 형식 | 역할(추정) |
|---|---|
| `Game.Objects.OutsideConnection`, `Game.Objects.ElectricityOutsideConnection` | 에디터 마커 오브젝트에 붙는 외부 연결·전력 외부 연결 태그 |
| `Game.Prefabs.OutsideConnectionData`, `MarkerObjectPrefab` | 마커 프리팹 데이터 |
| `Game.Net.OutsideConnection` | 맵 경계 넷 노드 |
| `Game.Prefabs.PowerLineData`, `PowerLinePrefab` | 송전선 넷 프리팹 |
| `Game.Simulation.ElectricityOutsideConnectionGraphSystem` | 외부 연결을 전력 흐름 그래프에 붙임 |
| `Game.Simulation.ElectricityFlowSystem` (`ElectricityFlowNode`/`ElectricityFlowEdge`, `TradeNode`) | 전력 흐름 계산. 거래 노드 포함 |
| `Game.Simulation.ElectricityTradeSystem` | 수입·수출량과 금액 계산 |

`ElectricityFlowSystem`이 128프레임 주기로 돌고 `ElectricityFlowEdge.m_Capacity`가 간선 용량이라는 점은 공개 모드 소스에서 확인된다. [M1]

---

## 2. 현재 프로젝트 상태

| 파일 | 전력 관련 현황 |
|---|---|
| `maps/tools/generate_sintanjin_jeonmin_heightmap.py` | `fetch_osm_features()`의 Overpass 쿼리에 물·도로·철도·토지이용만 있고 `power=line`이 없다. `generate_backbone_roads()`는 도로를 경계 안쪽 ±7150 m에서 잘라(`clip_lim`) 외부 연결과 이어지지 않는다. |
| `maps/sintanjin_jeonmin/*.bin` | 자원(`sintanjin_resources_256.bin`)·나무·도로(`SJR1`)만 있다. 전력 데이터 없음. |
| `maps/tools/cs2_mod/SintanjinMapBuilder/SintanjinMapBuilderSystem.cs` | 도로·철도를 `CreationDefinition`+`NetCourse`로 생성한다(`ProcessRoadBatch`). 송전선 프리팹 조회나 외부 연결 생성은 없다. |
| `maps/sintanjin_jeonmin/MAP_GUIDE.md` | 높이맵·수위·모드 단축키 안내만 있다. |
| `planner/` | 도로·교통 시뮬레이터. 전력 모델 없음. `exportCS2()` JSON에도 전력 항목 없음. |
| `cs2-kit/` | 건물 에셋 키트. 외부 전력과 무관. |

**결론**: 외부 전력은 맵 쪽 일이다. 플래너와 cs2-kit는 손대지 않는다.

---

## 3. 단계별 작업 (파일 단위)

### 1단계 — 수작업으로 먼저 넣기 (코드 없음, 권장 시작점)
외부 연결 지점은 맵 전체에 2~4개면 충분하므로 처음에는 에디터에서 손으로 놓는다.

1. 맵 에디터에서 높이맵·위성 오버레이를 불러온다(`maps/sintanjin_jeonmin/MAP_GUIDE.md` 3절).
2. 위성 오버레이와 OpenStreetMap의 `power=line` 레이어로 실제 송전선이 맵 경계를 지나는 곳을 찾는다. 위치·전압은 미확인이므로 직접 확인한다.
3. 그 경계 지점에 `outside` 검색 → 전력 외부 연결 마커를 놓는다.
4. `High Voltage` 검색 → 고압 송전선을 마커에서 안쪽으로 실제 노선을 따라 그린다.
5. 맵을 저장하고 새 게임으로 연 뒤 맵 정보의 Outside Connections에 전기가 보이는지, 변전소를 이었을 때 Electricity Trade가 움직이는지 본다(인게임 미확인).
6. `maps/sintanjin_jeonmin/MAP_GUIDE.md`에 "외부 전력 연결" 절을 추가해 놓은 지점 좌표와 확인 결과를 적는다.

### 2단계 — 송전선 데이터 만들기 (노선이 많아 손으로 그리기 어려울 때만)
`maps/tools/generate_sintanjin_jeonmin_heightmap.py`
1. `fetch_osm_features()` 쿼리에 `way["power"="line"]({bbox});`를 추가한다. 기존 캐시(`osm_cache_path`, `osm_collage_area.json`)에는 전력선이 없으므로 캐시를 지우거나 전력선만 따로 받는 함수를 둔다.
2. `generate_backbone_roads()`의 `to_cs2()`·`_clip_polyline_box()`·`_sample_elev_bilinear()`를 재사용해 `generate_power_lines()`를 만든다.
   - 도로와 달리 **경계에서 자르지 않고 경계까지 늘인다**(±7168 m). 경계와 만나는 점을 외부 연결 후보로 따로 기록한다.
   - `voltage` 태그로 고압(예: 154 kV 이상)만 남긴다.
3. 출력: `sintanjin_power.bin`(헤더 `SJP1`, 레코드는 SJR1과 같은 `<BBH14f>` 구조, `kind` 0=송전선, `flags` 비트로 "시작/끝이 경계")과 `preview_power_lines.png`.
4. `main()`에서 호출하고, 같은 파일의 `map_metadata.json`·MAP_GUIDE 생성부 `files` 표에 두 파일을 추가한다.

`maps/tools/test_osm.py` 또는 새 `maps/tools/test_power_lines.py`
- 작은 가짜 OSM 입력으로 ① 경계를 넘는 선이 경계점에서 끝나는지 ② 경계점이 외부 연결 후보로 잡히는지 ③ 바이너리 레코드 수가 맞는지 확인하는 `assert` 하나.

### 3단계 — 모드로 자동 배치 (2단계를 했을 때만)
`maps/tools/cs2_mod/SintanjinMapBuilder/SintanjinMapBuilderSystem.cs`
1. `OnCreate()`에 송전선 프리팹 쿼리 추가: `PowerLineData`+`NetGeometryData`+`PlaceableNetData`+`PrefabData`. 이름에 `High Voltage`가 들어간 지상형 프리팹을 고른다(`DiscoverNetPrefabs()`의 이름 점수 방식 재사용).
2. `StartPowerSpawn()`·`ProcessPowerBatch()`를 추가한다. `sintanjin_power.bin`을 읽고 `ProcessRoadBatch()`와 같은 `CreationDefinition`+`NetCourse` 생성 경로를 쓴다. 노드 스냅(`m_NodeGrid`)도 그대로 재사용한다.
3. 외부 연결 마커는 **1단계처럼 에디터에서 손으로 놓고**, 모드는 경계 끝점을 가장 가까운 기존 마커 노드에 스냅만 한다. 마커 자체를 코드로 만드는 방법(`Game.Objects.ElectricityOutsideConnection`이 붙은 `MarkerObjectPrefab` 생성)은 미확인이라 필요해질 때 검증한다.
4. 단축키 `Ctrl+Shift+P`(송전선만), `F6` 전체 실행과 명령 파일(`Sintanjin_Command.txt`)의 `POWER` 키워드에 연결한다. 로그·상태 문자열도 갱신한다.

`maps/tools/cs2_mod/SintanjinMapBuilder/Mod.cs`
- `OnLoad()` 로그의 단축키 목록에 `Ctrl+Shift+P`를 추가한다.

`maps/sintanjin_jeonmin/MAP_GUIDE.md`
- 파일 표에 `sintanjin_power.bin`, 적용 방법 5번에 `Ctrl+Shift+P`를 추가한다. 이 파일은 생성기가 다시 쓰므로 생성기 쪽 문자열과 함께 고친다.

### 4단계 — 시뮬레이션 (하지 않음)
- 전력 수급·거래 계산은 게임의 `ElectricityFlowSystem`·`ElectricityTradeSystem`이 한다. 플래너(`planner/simulator.js`)에 전력 모델을 따로 만들 이유가 없다.
- 플래너에서 외부 연결 위치를 설계해야 할 때만 `exportCS2()`의 JSON에 `powerConnections: [{x, z}]`를 추가한다. 이를 읽는 연동 수단은 아직 없다(README "사용 시 참고").

### 5단계 — 확인과 기록
1. 게임에서 확인: 맵 정보 Outside Connections, 전력 정보 화면 Electricity Trade, 예산의 수입·수출 금액.
2. HandOff.md 3절 "게임 안에서 확인할 것"에 결과를 적고, `HandOff_HISTORY.md` 맨 아래에 이력 한 줄을 추가한다.

---

## 4. 출처

- [P1] Paradox Interactive, Cities: Skylines II 개발 일지 "Electricity & Water"(2023-07-24, 출시 전 설계 기준): https://www.paradoxinteractive.com/games/cities-skylines-ii/features/electricity-water
- [S1] Steam 토론 "Map Editor Help"(2024-03~04, 사용자 보고): https://steamcommunity.com/app/949230/discussions/0/4362372998095339193
- [V1] VideoGamer, 전력 수출 공략: https://www.videogamer.com/guides/cities-skylines-2-sell-electricity-export
- [G1] GTPlanet 포럼 패치 노트 인용("Increased electricity import price"): https://www.gtplanet.net/forum/threads/cities-skylines-ii.417363/page-6
- [G2] Pro Game Guides, 전력 수출 공략: https://progameguides.com/cities-skylines-2/how-to-export-power-in-cities-skylines-2/
- [N1] Nexus Mods 커스텀 맵(지하 고압 송전선 외부 연결 사례): https://www.nexusmods.com/citiesskylines2/mods/4
- [M1] bootes-h/Adjustable-Powerline-Capacity 모드 소스: https://github.com/bootes-h/Adjustable-Powerline-Capacity
- [L1] 로컬 설치본 `Cities2_Data/Managed/Game.dll`의 형식·필드 이름(2026-11-20 확인). 필드 의미와 값은 미확인.
- 위키(`cs2.paradoxwikis.com`의 Electricity·Outside connections·Map Editor)는 자동 조회가 막혀 읽지 못했다. 브라우저로 직접 확인을 권한다.
