# 신탄진·전민 맵 풍향 설정 계획

대상: `maps/sintanjin_jeonmin/` 1.45× 맵. 코드 수정 없이 조사만 했다(2026-11-21). 결론은 **북북서→남남동**(바람이 337.5°에서 불어옴)이다. CS2 값은 `constantWind = (0.149, -0.359)`다. 바닐라 에디터에는 풍향 UI가 없어서 **모드 핫키로 `WindSimulationSystem.SetWind`를 호출해야 한다**. 인게임 검증은 아직 하지 않았다.

## 1. 공업 구역과 시작 타일의 위치 관계

좌표는 `generate_sintanjin_jeonmin_heightmap.py` 904~907행의 석유(공업 특화) 광상 중심과 2561행의 랜드마크에서 가져왔다. 시작 타일은 `START_AQUIFER`(36.44284N, 127.43195E, 신탄진IC 동쪽)이다. 거리는 생성기와 같은 m/deg 공식으로 계산했다.

| 공업 지역 | 좌표 | 시작 타일까지 | 산단에서 본 시작 타일 방위 |
|---|---|---|---|
| 평촌·신일 중소기업단지 | 36.4355, 127.4305 | **0.83 km** | 9° (거의 정북) |
| 대전철도차량정비단 | 36.4261, 127.4307 | 1.86 km | 3° (정북) |
| 목상·문평 대덕3·4산단 | 36.4408, 127.4025 | 2.65 km | 85° (정동) |
| 탑립·관평 동측 산단 | 36.4165, 127.4100 | 3.53 km | 34° (북동) |
| 벤처협동화·원촌 북측 | 36.3865, 127.3995 | 6.9 km | 25° (북북동) |

정리하면 공업 구역은 시작 타일의 **서쪽(대덕3·4)부터 남쪽·남남서(평촌·신일, 정비단, 탑립·관평)에 걸쳐** 있다. 평촌·신일이 1 km 안에 있어서 이곳이 가장 큰 위험이다.

## 2. 실제 대전 지역의 주풍향

- 대전시 기후 소개: "바람은 일반적으로 북서계절풍이 남서계절풍보다 강하고, 특히 겨울철에는 북서풍이 불며". 페이지 요약을 거쳐 확인한 문장이라 원문과 한 글자씩 대조하지는 못했다. <https://www.daejeon.go.kr/drh/DrhContentsHtmlView.do?menuSeq=2034>
- 기상청 평년값(대전 133 지점)의 최다풍향은 기상자료개방포털에서 로그인해야 받을 수 있어 직접 확보하지 못했다. <https://data.kma.go.kr/climate/average30Years/selectAverage30YearsList.do>
- 대체 자료로 Iowa Environmental Mesonet(IEM)의 METAR 관측 2016-01~2025-12를 받아 계절별로 직접 집계했다. 풍속 2 kt 미만은 무풍으로 제외했고 비율은 전체 관측 대비다. <https://mesonet.agron.iastate.edu/request/download.phtml?network=KR__ASOS>

| 관측소 | 겨울(12~2) | 봄(3~5) | 여름(6~8) | 가을(9~11) | 연간 |
|---|---|---|---|---|---|
| RKTF 대전(36.37N 127.37E, 맵 남서 경계 부근, 관측 2,324건으로 적음) | WNW 11%, W 11%, NW 6% | W 12%, WSW 10%, SSW 10% | SW 12%, WSW 9% | W 9% (무풍 54%) | W 9%, SW 8% |
| RKTU 청주(36.72N 127.50E, 북쪽 약 30 km, 87,425건) | W 13%, WNW 11% | WSW 14%, W 12% | WSW 11%, E 8% | E 11%, ENE 8% | WSW 10%, W 10% |
| RKTE 성무(36.57N 127.50E, 계곡 지형이라 남북 채널링) | NW 17%, S 16% | S 19% | S 25% | S 18% | S 20% |

요약하면 대전은 **연중 서~남서풍**(바람이 W/SW에서 불어옴)이 우세하고 **겨울에는 서북서~북서풍**이 분다. 가을에는 동풍 계열도 나타난다(청주 기준). 실제 풍향대로 설정하면 바람이 서·남서쪽 산단에서 **시작 타일 쪽(동·북동)으로** 분다는 점이 핵심 문제다.

## 3. 추천 풍향

CS2 바람은 계절 변화가 없는 **단일 상수 벡터**다(4절). 그래서 한 방향만 정해야 한다. 각 후보에 대해 산단 5곳의 오염이 시작 타일로 가는지 계산했다. "풍하 a km / 측 b km"는 시작 타일이 산단에서 바람 방향으로 a km 아래, 오염 띠 중심선에서 b km 옆에 있다는 뜻이다. 측거리가 작을수록 나쁘다.

| 바람(불어오는 쪽→가는 쪽) | CS2 `constantWind` (x=동, z=북) | 시작 타일이 풍하에 들어가는 산단 |
|---|---|---|
| 남서→북동 (**현재 기본값**) | (0.275, 0.275) | 5곳 모두. 평촌·신일 풍하 0.7 km/측 0.5 km, 탑립 측 0.7 km로 **최악** |
| 서→동 (실제 연간 주풍) | (0.389, 0) | 대덕3·4 측 0.2 km, 평촌 측 0.8 km로 **나쁨** |
| 북서→남동 (실제 겨울) | (0.275, -0.275) | 대덕3·4만 해당(풍하 1.7 km/측 2.0 km) |
| **북북서→남남동 (추천)** | **(0.149, -0.359)** | 대덕3·4만 해당(풍하 0.8 km/측 2.5 km). 나머지는 모두 풍상 |
| 북→남, 북동→남서, 동→서 | (0, -0.389) 등 | 없음 (가장 안전하지만 실제 대전과 거리가 멂) |

**추천: 북북서→남남동.**

1. 시작 타일에서 1~2 km 거리인 평촌·신일과 정비단이 시작 타일의 정남쪽에 있다. 바람이 남쪽으로 불면 이 두 곳의 오염이 시작 타일에서 멀어진다. 탑립·관평과 벤처협동화도 같은 이유로 안전하다.
2. 대덕3·4산단(서쪽)의 오염 띠는 시작 타일에서 남쪽으로 약 2.5 km 떨어져 지나간다.
3. 대전의 실제 겨울 북서계절풍에서 22.5°만 돌린 방향이다. 실제 기후를 참고했다는 설명이 성립하는 범위에서 시작 타일이 가장 안전한 방향이다.
4. 오염 띠는 남남동쪽의 회덕·계족산 서사면(광석 광상, 산지)으로 빠진다. 기존 시가지가 가장 적은 쪽이다.

리얼리즘보다 안전을 우선하면 **북→남 `(0, -0.389)`**이 대안이다. 이 경우 5곳 모두 풍상이다. 크기는 바닐라 기본값과 같은 0.389로 맞췄다. 에디터 내부 setter는 길이 1.0 벡터를 쓰는데, 그러면 경계 압력차가 커져 바람이 약 2.6배 강해지고 오염도 더 멀리 퍼진다.

주의할 점이 있다.

- 대기오염은 바람에 실려 가는 이동(advection) 외에 4방향 확산(`kSpread = 3`)도 한다. 그래서 평촌·신일처럼 0.8 km 거리라면 풍향과 상관없이 어느 정도 오염이 온다. 시작 구역 바로 남쪽에는 오염이 큰 공업보다 사무·상업이나 저오염 특화 공업을 두는 것을 권한다.
- 지면오염·수질오염·소음은 바람과 관계없다.

## 4. CS2에서 풍향을 정하는 방법 (Game.dll 확인 결과)

로컬 `Cities2_Data/Managed/Game.dll`을 ILSpy 8.2(`ilspycmd`)로 디컴파일해 확인했다.

- `Game.Simulation.WindSimulationSystem`
  - `public float2 constantWind { get; set; }`의 기본값은 `OnCreate`에서 `(0.275f, 0.275f)`이고 압력은 40이다.
  - `public void SetWind(float2 direction, float pressure)`는 상수를 바꾸고 `SetDefaults`로 64×64×16 바람 셀 전체를 다시 초기화한다.
  - `UpdatePressureJob`은 맵 경계 중 바람이 향하는 쪽 가장자리의 압력을 낮춘다. 그러면 지형을 감안한 풍속장이 생긴다.
  - `Serialize`가 `constantWind`를 기록하고 `Deserialize`가 `Version.windDirection` 이후 세이브와 맵에서 이를 읽는다. 즉 **풍향은 맵/세이브 파일에 저장된다**.
- `Game.Simulation.AirPollutionSystem.AirPollutionMoveJob`은 `cellCenter - m_WindAdvectionSpeed * wind`(상류) 위치의 오염을 끌어오는 방식이다. 따라서 **벡터는 바람이 가는 방향**이다. 좌표는 x=동, z=북이다. z=북은 프로젝트 문서의 "X +3,570m / Z +3,681m(동·북)" 관례를 따른 것이다.
- `Game.UI.Editor.ClimatePanelSystem`에는 `private double windDirection`(각도↔벡터 변환, `SetWind(dir, 40f)` 호출, 바람 인포뷰 자동 표시) 속성이 남아 있다. 하지만 **어떤 위젯도 이 속성을 참조하지 않는다**. 현재 빌드 맵 에디터의 기후 패널에는 풍향 항목이 없다는 뜻이다.
- `ClimatePrefab`(기후 프리셋)에는 기온·강수·구름·오로라·안개 곡선과 위도·경도만 있고 바람 항목은 없다. 기후 프리셋으로는 풍향을 바꿀 수 없다.
- `Game.Rendering.WindVolumeComponent.windDirection`(기본 65°)은 나무 흔들림 같은 **렌더링 전용 값**이고 시뮬레이션과는 무관하다. Thunderstore의 TreeWindController 모드는 이 값만 바꾸므로 오염 방향에는 영향이 없다. <https://thunderstore.io/c/cities-skylines-ii/p/donutmonger/TreeWindController>
- 게임 안에서는 대기오염 인포뷰로 현재 바람 방향을 볼 수 있다(바람 화살표 표시). Steam 토론에도 "맵의 바람은 항상 같다"는 보고가 있어 상수 바람이라는 사실과 맞는다. <https://steamcommunity.com/app/949230/discussions/0/6982351752477766950>
- 시뮬레이션 풍향을 바꾸는 배포 모드는 찾지 못했다(Paradox Mods·Thunderstore 검색 기준).

**한계**: 계절별 풍향 변화는 불가능하고 방향 하나만 정할 수 있다. 설정 파일이나 프리셋 경로도 없으며 코드 모드가 필요하다.

## 5. 이 프로젝트에서 설정하는 방법

`maps/tools/cs2_mod/SintanjinMapBuilder`가 이미 `GameSystemBase`로 시스템들을 가져오고 있다(`m_TerrainSystem` 등, 97행). 핫키 블록도 195행 부근에 있다. 같은 방식으로 핫키 하나만 추가하면 된다. 이 작업에서는 구현하지 않았다.

```csharp
// OnCreate
m_WindSimulationSystem = World.GetOrCreateSystemManaged<WindSimulationSystem>();
// OnUpdate 핫키 블록, 예: Ctrl+Shift+W (현재 미사용 키)
if (ctrl && shift && kb.wKey.wasPressedThisFrame)
{
    m_WindSimulationSystem.SetWind(new float2(0.149f, -0.359f), 40f); // NNW→SSE, 기본 크기 0.389
    WriteStatus($"Wind set -> {m_WindSimulationSystem.constantWind}");
}
```

적용 절차:

1. 위 핫키를 추가하고 모드를 빌드·설치한다(기존 csproj 그대로 사용).
2. CS2 **맵 에디터**에서 신탄진·전민 맵을 연다.
3. `Ctrl+Shift+W`를 누르고 대기오염(또는 바람) 인포뷰에서 화살표가 남남동을 가리키는지 확인한다. 반대로 나오면 z축 부호가 가정과 다른 것이므로 `(0.149, 0.359)`로 바꾼다.
4. 맵을 저장한다. `constantWind`가 맵 데이터에 직렬화된다.
5. 그 맵으로 **새 도시**를 시작하고 인포뷰에서 풍향이 유지되는지 확인한다. 기존 세이브에도 핫키를 누르면 바로 적용된다(세이브에 저장됨).

## 6. 대안 (풍향 설정을 쓰지 않거나 보완할 때)

- 오염이 많은 공업과 발전소는 시작 타일의 **남남동~남쪽 풍하**(정비단·회덕 방향)나 서쪽 대덕3·4산단에 몰아 두고, 주거는 북쪽(석봉·신탄진)과 동쪽으로 확장한다. 바닐라 기본 바람(남서→북동)을 그대로 쓴다면 반대로 공업을 **북동쪽**에 두어야 하는데, 이는 실제 산단 배치와 맞지 않는다.
- 평촌·신일 석유 광상(시작 타일에서 0.8 km)이 공업을 시작 구역 바로 옆으로 끌어들인다. 필요하면 생성기 905행의 반경이나 강도를 줄이는 방안을 검토한다(이번에는 변경하지 않음).
- 주거와 공업 사이에 녹지·사무 완충대를 두면 확산 성분을 줄일 수 있다.

## 출처

- 대전광역시 기후: <https://www.daejeon.go.kr/drh/DrhContentsHtmlView.do?menuSeq=2034>
- 기상자료개방포털 평년값: <https://data.kma.go.kr/climate/average30Years/selectAverage30YearsList.do>
- IEM ASOS/METAR 다운로드(RKTF·RKTU·RKTE, 2016~2025): <https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py>
- Steam 토론(상수 바람): <https://steamcommunity.com/app/949230/discussions/0/6982351752477766950>
- TreeWindController(렌더링 전용 바람): <https://thunderstore.io/c/cities-skylines-ii/p/donutmonger/TreeWindController>
- 로컬 Game.dll 디컴파일: `WindSimulationSystem`, `WindSystem`, `AirPollutionSystem`, `ClimatePanelSystem`, `WindVolumeComponent`, `Version.windDirection`
