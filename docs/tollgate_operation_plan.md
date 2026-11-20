# 톨게이트 작동 구현 방안 (설계 문서, 코드 미작성)

대상: 신탄진IC 영업소. 차로 데이터는 `cs2-kit/projects/sintanjin-tollgate/toll_lanes.json`(진입 2 + 진출 5, 부스 4, 하이패스 30 km/h), 조사 근거는 같은 폴더 `lane_research.md`.

이 저장소에서 "게임 안"은 두 곳이다.

- **A. 플래너 시뮬레이터** `planner/simulator.js` (`CitySimulator`) — 차량 이동·정체·신호가 이미 있다. 여기서 먼저 만든다.
- **B. CS2 본게임** — CS2에는 요금 징수 기능이 없다. `maps/tools/cs2_mod/SintanjinMapBuilder`(C# `GameSystemBase`)와 같은 방식의 모드가 필요하다.

## 현재 코드에서 붙일 곳 (A)

| 기능 | 있는 것 | 붙일 곳 |
|---|---|---|
| 도로 종류 | `road.facility` (`brt`, `ramp`, `interchange` …), `ROAD_CONFIGS` | `facility: 'toll'` + `road.toll = { lanes:[…toll_lanes.json…], fee }` |
| 정지/감속 | BRT 정류장: `updateSimulation()`의 `car.dwell` + `car.stoppedRoad` (simulator.js 911행 부근) | 같은 블록에 `road.facility === 'toll'` 분기 |
| 진입 대기 | `signalIsGreen(road)` + 노드 `signal` (942행) | 부스 점유 중이면 `false`를 돌려 뒤차를 세움 |
| 정체 | `road.trafficLoad`, `cfg.capacity`, `updateTrafficMeter()` 경고 | 톨 도로 용량 = 열린 차로 처리량 합 |
| 차량 | `spawnCar()`가 만드는 `{roadIndex, progress, path, color}` | `car.hipass` (불리언) 추가 |
| 통계/경제 | `updateStats()` (인구·일자리·도로 km만, 경제 없음) | `this.tollRevenue` 누적, 통계 패널 한 줄 |
| 데이터 | `korean_newtown_preset.js` `road(...)`, `exportCS2()` | 프리셋에 톨 도로 1개, 내보내기에 `toll` 필드 |
| 검증 | `planner/tests/test_traffic.js`, `test_simulator.js` | 톨 통과 시간·수입 assert |

## 단계

### 1단계 — 최소 구현 (A, 반나절)
1. `simulator.js`: `facility === 'toll'` 도로의 중앙(`length/2`)을 지날 때 차량을 멈춘다. BRT `dwell` 코드를 그대로 따라 한다.
   - 일반: `dwell = 8~12 s` (현금/카드 수납, 추정), 통과 시 `this.tollRevenue += road.toll.fee`.
   - 하이패스(`car.hipass`, 스폰 시 약 85% 확률 — 하이패스 이용률 추정): 정지 없음, 30 km/h로만 감속(`speedLimit` 대신 30 적용), 요금 가산.
2. `spawnCar()`: `car.hipass` 부여.
3. `updateStats()`: 톨 수입 표시. 테스트 1개(`test_traffic.js`에 톨 통과 시 수입 증가·일반 차량 정지 확인).

### 2단계 — 차로 선택·부스 대기열 (A)
1. 차량 객체에 `tollLane` 추가. 톨 도로 진입 시 `toll_lanes.json`의 해당 방향(`dir`) 차로 중 `accepts`가 맞는 것 가운데 대기열이 가장 짧은 차로를 고른다(하이패스 차량은 하이패스·겸용, 일반은 TCS·겸용).
2. 차로별 `queue` 배열과 `busyUntil`. 부스는 한 번에 한 대(서버 1, M/D/1 대기열). 앞차가 서 있으면 뒤차는 `progress = 정지선 - 차량간격*순번`에서 대기 → 대기열이 길어지면 `trafficLoad` 상승 → 기존 색상·경고가 자동으로 정체를 보여 준다.
3. `signal: 'red_x'` 차로(3차로)는 선택 대상에서 뺀다. 인스펙터(`updateInspector()`)에 차로별 개폐 토글.

### 3단계 — 합류·정체 확장 (A)
1. 요금소 뒤 합류부: 7차로 → 본선 진입 램프 1~2차로. 합류 구간 도로를 `capacity`가 작은 별도 `road`로 두고, 진출 차량이 같은 시점에 몰리면 교대 통과(지퍼)만 허용.
2. 시간대 수요(출근 피크 배율) — 신탄진IC 출근 정체(진입 신호 4~5회 대기 보도)를 재현해 차로 개방 수·하이패스 비율 변화 효과를 비교.
3. 차종(화물·버스)별 요금·처리시간 차등, 1차로/5차로 화물 겸용 반영.

### 4단계 — CS2 본게임 (B, 모드)
1. 에셋 배치: `SintanjinTollgate_L1_6x4`는 도로를 덮는 캐노피일 뿐이다. HandOff 3절대로 `Building` 프리셋 + Anarchy로 도로 위에 겹쳐 놓는다(미확인). 7차로 도로 프리팹을 캐노피 아래로 깔고 차로 x 범위를 `toll_lanes.json`과 맞춘다. 가져오기는 `cs2-import/SintanjinTollgate_L1_6x4` 폴더 하나만 고른다.
2. 감속/정지: 새 `GameSystemBase`(예: `TollPlazaSystem`)가 톨 영역 `Game.Net.Edge`의 차로를 표시해 두고, 그 위 차량(`Game.Vehicles.CarCurrentLane`)의 목표 속도를 낮춘다. 일반 차로는 신호 노드(CS2 기본 신호등)를 부스 처리시간 주기로 돌려 정지를 흉내 낸다 — 경로 계산은 건드리지 않는다.
3. 요금 징수: 통과 차량 수 × 요금을 도시 수입에 더한다(`Game.Simulation.CitySystem`/`PlayerMoney`, 정확한 API는 모드 개발 시 확인 — 미확인).
4. 하이패스·차로 선택: 하이패스 차로는 속도 제한만, 일반 차로는 신호 정지. 차량별 하이패스 구분은 CS2에 없으므로 차로 단위로만 나눈다(차량 비율은 CS2 기본 차로 선택에 맡김).
5. 정체는 CS2 기본 교통 시뮬레이션이 그대로 만든다. 모드는 처리시간만 조절.

## 하지 않은 것

- 1~4단계 코드는 작성하지 않았다(설계만).
- 처리시간 8~12 s, 하이패스 이용률 85%, 요금 값은 모두 **추정**이다. 실제 요금은 출발·도착 영업소 거리제라 시뮬레이터에서는 고정 요금으로 단순화한다.
