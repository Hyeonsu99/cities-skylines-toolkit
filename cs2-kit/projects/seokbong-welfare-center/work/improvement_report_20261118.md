# 석봉동 행정복지센터 · 금강엑슬루타워 101~112동 개선 보고서 (2026-11-18)

## 1. 프로젝트별 Final 게이트 상태 및 삼각형 수 (전/후)

모든 13개 프로젝트에서 `agent.py cycle --mode final` 및 산출물 시각 검토 후 `agent.py review --status PASS` 완료 (`gate.json` = `PASS`, `_Gls` 잔여 파일 0건).

| 프로젝트 | 에셋명 | Final 게이트 (`gate.json`) | `main` 삼각형 (전 → 후) | `LOD1` 삼각형 (전 → 후, 비율) | `LOD2` 삼각형 (전 → 후) | `_Win` / `_Gls` | 제거한 화분·식재 수 (`planter` + 식물) | `subobjects.json` 경로 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `seokbong-welfare-center` | `SeokbongWelfareCenter_L1_7x9` | **PASS** (전 항목 PASS) | `33,201 → 46,503` (+13,302) | `10,793 → 10,279` (`22.1%`) | `258 → 258` | `1,364 / 0` | `18` (`planter 9 + tree 4 + shrub 5`) | `cs2-kit/projects/seokbong-welfare-center/work/subobjects.json` |
| `exllu-101` (B형) | `HighriseTower101_L1_5x4` | **PASS** (`photo/tiles`: N/A) | `64,602 → 64,284` (-318) | `9,222 → 9,204` (`14.3%`) | `458 → 458` | `1,720 / 0` | `7` (`planter 2 + shrub 5`) | `cs2-kit/projects/exllu-101/work/subobjects.json` |
| `exllu-102` (A형) | `HighriseTower102_L1_5x4` | **PASS** (전 항목 PASS) | `77,426 → 77,328` (-98) | `11,982 → 11,978` (`15.5%`) | `266 → 266` | `2,970 / 0` | `8` (`planter 2 + shrub 6`) | `cs2-kit/projects/exllu-102/work/subobjects.json` |
| `exllu-103` (A형 기준) | `HighriseTower103_L1_5x4` | **PASS** (전 항목 PASS) | `77,426 → 77,328` (-98) | `11,982 → 11,978` (`15.5%`) | `266 → 266` | `2,970 / 0` | `8` (`planter 2 + shrub 6`) | `cs2-kit/projects/exllu-103/work/subobjects.json` |
| `exllu-104` (B형 기준) | `HighriseTower104_L1_5x4` | **PASS** (전 항목 PASS) | `64,602 → 64,284` (-318) | `9,222 → 9,204` (`14.3%`) | `458 → 458` | `1,720 / 0` | `7` (`planter 2 + shrub 5`) | `cs2-kit/projects/exllu-104/work/subobjects.json` |
| `exllu-105` (C형 기준) | `HighriseTower105_L1_5x6` | **PASS** (전 항목 PASS) | `88,254 → 88,172` (-82) | `17,850 → 17,768` (`20.2%`) | `392 → 392` | `2,908 / 0` | `6` (`planter 2 + shrub 4`) | `cs2-kit/projects/exllu-105/work/subobjects.json` |
| `exllu-106` (C형) | `HighriseTower106_L1_5x6` | **PASS** (전 항목 PASS) | `88,254 → 88,172` (-82) | `17,850 → 17,768` (`20.2%`) | `392 → 392` | `2,908 / 0` | `6` (`planter 2 + shrub 4`) | `cs2-kit/projects/exllu-106/work/subobjects.json` |
| `exllu-107` (C형) | `HighriseTower107_L1_5x6` | **PASS** (전 항목 PASS) | `88,254 → 88,172` (-82) | `17,850 → 17,768` (`20.2%`) | `392 → 392` | `2,908 / 0` | `6` (`planter 2 + shrub 4`) | `cs2-kit/projects/exllu-107/work/subobjects.json` |
| `exllu-108` (C형) | `HighriseTower108_L1_5x6` | **PASS** (전 항목 PASS) | `88,254 → 88,172` (-82) | `17,850 → 17,768` (`20.2%`) | `392 → 392` | `2,908 / 0` | `6` (`planter 2 + shrub 4`) | `cs2-kit/projects/exllu-108/work/subobjects.json` |
| `exllu-109` (B형) | `HighriseTower109_L1_5x4` | **PASS** (`photo/tiles`: N/A) | `64,602 → 64,284` (-318) | `9,222 → 9,204` (`14.3%`) | `458 → 458` | `1,720 / 0` | `7` (`planter 2 + shrub 5`) | `cs2-kit/projects/exllu-109/work/subobjects.json` |
| `exllu-110` (A형) | `HighriseTower110_L1_5x4` | **PASS** (전 항목 PASS) | `77,426 → 77,328` (-98) | `11,982 → 11,978` (`15.5%`) | `266 → 266` | `2,970 / 0` | `8` (`planter 2 + shrub 6`) | `cs2-kit/projects/exllu-110/work/subobjects.json` |
| `exllu-111` (A형) | `HighriseTower111_L1_5x4` | **PASS** (전 항목 PASS) | `77,426 → 77,328` (-98) | `11,982 → 11,978` (`15.5%`) | `266 → 266` | `2,970 / 0` | `8` (`planter 2 + shrub 6`) | `cs2-kit/projects/exllu-111/work/subobjects.json` |
| `exllu-112` (B형) | `HighriseTower112_L1_5x4` | **PASS** (`photo/tiles`: N/A) | `64,602 → 64,284` (-318) | `9,222 → 9,204` (`14.3%`) | `458 → 458` | `1,720 / 0` | `7` (`planter 2 + shrub 5`) | `cs2-kit/projects/exllu-112/work/subobjects.json` |

---

## 2. 작업 1: 석봉센터 옥상 태양광 패널 입체화 (`_build_solar_array`)

- **적용 내용**:
  - 기존 평판 상자(`mb.box(..., 20.00, 20.16, "solar_pv")`)를 줄(row) 단위 입체 경사 거치대 구조(`_build_solar_array`)로 교체.
  - 북측 지붕(`Z=20.00 m`): 좌측 6줄(`-21.0..7.0, 51.6..68.8`), 우상단 4줄(`7.2..23.6, 56.6..68.8`), 우하단 2줄(`14.0..23.6, 51.6..56.4`).
  - 남동 지붕(`Z=15.10 m`): 본체 5줄(`3.8..20.4, 14.0..27.6`), 북측 소형 2줄(`3.8..13.5, 29.0..34.0`).
  - 건물 정면(`-Y`)의 실제 도로 방위각(`notes["azimuth_deg"] = -11.2°`)을 반영하여 실제 남향 법선 벡터로 경사각 `16.0° # estimated` 기울기 부여, 지붕 바닥에서 `0.14 m # estimated` 띄워 하부 그림자 틈을 확보하고 줄 간격 `0.20 m # estimated`, 2m 단위 테이블, 알루미늄 외곽 테두리(`railing_steel`), 하부 베이스 레일·전후 수직 지주·경사 서까래 보(`frame_metal`/`railing_steel`) 구현.
  - `LOD1`은 줄 단위 기울어진 판 상자로 단순화(`10,279` tris = `22.1% < 50%`), `LOD2`는 기존 수준(`258` tris `<= 500`) 유지.
  - `_paint_solar_pv`: 짙은 청색 단결정 셀 `(44, 64, 76)` + 가는 은색 셀 격자 `(116, 134, 148)` + 버스바 `(64, 86, 100)` + 알루미늄 프레임 `(188, 194, 202)`.
- **위성 정합 결과**:
  - `previews/photo_check/satellite.png` 외곽·엣지 일치도: **`63% → 65%`** (향상)
  - `tile_compare.py` 위성 타일 일치도: `recall 39% → 40%`, `precision 49% → 50%`, `DETAIL_COLOR tiles_off 0/7` 유지.
- **비교 그림 경로**:
  - 전/후 통합 비교: `cs2-kit/projects/seokbong-welfare-center/work/compare_solar.png`, `cs2-kit/projects/seokbong-welfare-center/work/compare_solar_zoom.png`
  - 개별 렌더: `work/before_solar.png`, `work/after_solar.png`, `work/before_solar_zoom.png`, `work/after_solar_zoom.png`

---

## 3. 작업 2: 화분·화단 틀·식물 메시 제거 및 `work/subobjects.json` 분리

- **적용 내용 (변경 지시 반영)**:
  - 식물뿐 아니라 화분·화단 틀(콘크리트·화강석 테두리, B형 좌측 화단 상부 안전난간 포함)과 흙면(`soil`/`green_planter`) 전체를 메시에서 제거하고 `work/subobjects.json`에 `kind: "planter"` 및 `kind: "tree"|"shrub"` 항목으로 분리(대지 중심 좌표 = 생성기 좌표 + `pivot_shift`, 가로×세로×높이 `size_m`, 회전 `rot_deg`, 스케일, 바닐라 에셋 종류 제안 포함).
  - 제거 후 노출되는 석봉센터 중정 북서 1층 연결 브리지 상부 슬래브(`X=-6.0..-0.5, Y=44.6..50.4, Z=4.70`) 상면을 `terrace_deck`으로 마감하고, 모든 화분·화단 제거 위치의 바닥면·벽면이 빈틈없이 닫혀 있음을 확인(`coplanar = 0`, 64뷰 `lod_check` `bad_views = 0/64`).
  - 각 프로젝트 `shape_notes.md` 및 `STATUS.md`에 `"식재는 subobjects.json 으로 분리"` 기록 완료.

---

## 4. 작업 3: 석봉센터 간판 글자 발광 1/3 축소

- **전/후 발광 값 비교** (배경판 발광은 모두 `0.0`, 글자 획만 발광):
  1. **지붕 간판 (`sign_center_roof`, "석봉복합문화센터")**:
     - 아틀라스 `emissive`: `(118, 126, 136) → (68, 73, 78)` / 페인터 `emis_val`: `165 → 95`
     - 최종 베이킹 `Emissive.png` 글자 획 RGB: **`(76, 82, 88) → (25, 27, 29)` (기존의 33.3%, 약 1/3)**
  2. **1층 현관 풀컬러 LED 전광판 (`sign_welfare_led`, "석봉동 행정복지센터")**:
     - 아틀라스 `emissive`: `(135, 235, 255) → (78, 136, 148)` / 페인터 `emis_val`: `244 → 140`
     - 최종 베이킹 `Emissive.png` 글자 획 RGB: **`(129, 225, 244) → (43, 75, 81)` (기존의 33.3%, 약 1/3)**
  3. **로컬푸드 파시아 간판 (`sign_localfood`, "대덕로컬푸드직매장")**:
     - 근거: 실물(`storefront_se_oblique.png`)은 지붕 간판과 동일한 백색 파시아 위 입체 채널 글자이나, 기존 유효 발광 RGB가 `(131,100,67)`/`(148,113,75)`로 지붕 간판 `(76,82,88)`보다 오히려 약 1.8배 과도하게 밝았음.
     - 아틀라스 `emissive`: `(215, 165, 110) → (124, 95, 64)` / 페인터 `emis_val`: `155/175 → 90/100`
     - 최종 베이킹 `Emissive.png` 글자 획 RGB: **`(131,100,67)/(148,113,75) → (44,34,23)/(49,37,25)` (기존의 33.1%, 약 1/3)**
- **비교 그림 경로**:
  - `--mode emissive` 전/후 비교: `cs2-kit/projects/seokbong-welfare-center/work/compare_emissive.png` (`work/before_emissive.png`, `work/after_emissive.png`)
  - `--night` 전/후 비교: `cs2-kit/projects/seokbong-welfare-center/work/compare_night.png` (`work/before_night.png`, `work/after_night.png`)

---

## 5. 추정값 목록 (`# estimated`)

- `SOLAR_TILT_DEG = 16.0` (15~25° 범위 내 옥상 경사형 태양광 거치대 각도, `# estimated`)
- `SOLAR_CLEAR_Z = 0.14` (지붕 슬래브 바닥에서 띄운 태양광 전면 하단 이격 높이, `# estimated`)
- `SOLAR_PANEL_T = 0.052` (알루미늄 프레임 태양광 모듈 두께, `# estimated`)
- `SOLAR_ROW_GAP = 0.20` (태양광 줄 사이 간격, `# estimated`)
- `subobjects.json` 내 바닐라 에셋 프리팹 실제 이름 (`"미확인"` 표기, 한국어 종류·크기 제안 병기)

---

## 6. 남은 문제 및 인게임 확인 사항

- 13개 프로젝트 모두 `final` 게이트 및 시각 리뷰 `PASS` (FAIL/INCOMPLETE 없음).
- A형 4개 동(`exllu-102, 103, 110, 111`)은 기존과 동일한 저해상도 텍셀 경고(`TEXEL: 29% of faces > 1 m2 are below 64 px/m`)만 있으며(`exllu-103` 기준 모델 형태·색·UV 불변 원칙 준수), 석봉센터는 `lot 7x9 > 6x6` 시그니처 등록 안내 경고만 있음.
- CS2 에셋 에디터/인게임 확인 필요: `work/subobjects.json` 좌표를 참고한 바닐라 조경/화단 서브오브젝트 실제 배치, 석봉센터 야간 간판 발광 밝기(1/3 축소분) 및 옥상 태양광 거치대 입체 그림자 확인.
