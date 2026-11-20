# HandOff — 신탄진·대덕 권역 CS2 재현

이 저장소에서 일하는 **모든 AI 에이전트(Claude · Codex · Antigravity)와 사람**이 작업 전에 읽는 인수인계서입니다.

- 내용을 바꾸면 [`HandOff_HISTORY.md`](HandOff_HISTORY.md) 맨 아래에 한 줄(날짜 · 작성자 · 구분 · 섹션 · 요약)을 추가합니다. 기존 이력 줄은 고치지 않습니다.
- 작성자는 구분 가능하게 적습니다. 예: `Claude Opus 5.5 (Claude Code)`, `Codex gpt-6.2-astra`, `Antigravity Gemini 4 Neon`, `Hyeonsu99`.
- 확인하지 않은 내용은 `미확인`으로 표시합니다. 게임 안에서 확인하지 않은 결과는 `인게임 미확인`입니다.
- 엑슬루타워 세부 인수인계는 `cs2-kit/projects/EXLLU_인수인계.md`, 한국형 주거 재발 방지 규칙은 `reports/korean_housing_lessons.md`에 있습니다.

---

## 1. 한눈에 보기 (2026-11-19 기준)

**목표**: 대전 신탄진~대덕테크노밸리~전민·문지 권역(약 9×10 km)을 Cities: Skylines II에서 위성 사진 수준으로 재현한다(맵 14.336 km, 1:1).
**원칙**: 에셋을 더 만들기 전에 엑슬루 주변 1 km²를 게임 안에서 끝까지 완성해 스케일·성능·부족한 에셋을 확인한다.

| 구분 | 항목 | 상태 | 위치 |
|---|---|---|---|
| 맵 | 범위 확정·높이맵 재생성 | 대기 (사용자 결정) | `maps/sintanjin/`, `maps/tools/` |
| 맵 | 위성 오버레이·차선 가이드·맵 구축 모드 | 완료 (인게임 미확인) | `maps/sintanjin_jeonmin/` |
| 에셋 | 엑슬루타워 12개 동 | 완료 | `cs2-kit/projects/exllu-101`~`112` |
| 에셋 | 파란 지붕 공장 4종 | 완료 | `cs2-kit/projects/blue-factory/` |
| 에셋 | 신탄진IC 톨게이트 | 완료 | `cs2-kit/projects/sintanjin-tollgate/` |
| 에셋 | 석봉동 행정복지센터 | 완료 (남은 확인 있음) | `cs2-kit/projects/seokbong-welfare-center/` |
| 에셋 | 고속도로 소품 7종 | 완료 (인게임 미확인) | `cs2-kit/projects/highway-props/` |
| 에셋 | 신탄진형 단독주택 (저밀도) | 1단계 완료. 2단계는 01 승인 후 중단 | `cs2-kit/projects/korean-detached/` |
| 에셋 | 신탄진형 다세대 빌라 (중밀도) | 1단계 완료. 2단계 미배정 | `cs2-kit/projects/korean-villa/` |
| 에셋 | 1970~90년대풍 한국형 주택 4종 | **폐기** (2026-11-19) | git 기록 `748f6a5` |
| 도구 | 로컬 키트 확장 `kitext`, 알베도 검사 | 완료 | `cs2-kit/local/kitext.py`, `tools/albedo_check.py` |
| 도구 | 에셋 뷰어 | 사용 중 | `asset-viewer/` (`run.bat`) |

---

## 2. 에셋별 상태

### 엑슬루타워 12개 동 — 완료
- 2026-11-19: 창호 3D 창틀·야간 발광 조정, 유리 광택 0.38→0.875, P1 저층부 예산 재배분·P2 창 실내 깊이, 출입구 석재 받침 베벨.
- 107·108동은 생성기만 바뀌고 결과물이 옛 버전(92,660 tris)으로 남아 있던 것을 재빌드(71,438, 105·106과 동일). **게임에 이미 넣었다면 다시 가져와야 한다.**
- 삼각형: 101·104·109·112 55k / 102·103·110·111 76.7k / 105~108 71.5k.

### 파란 지붕 공장 4종 — 완료
- Small 3x4 · Mid 4x6 · Large 6x6 · RailDepot 4x8(시그니처). 가상 상호 간판(들빛산기·세별정밀·맑은터테크·새솔철도검수).
- 2026-11-19: 3D 창틀·작업장 점등, 채도 하향·광택 변주, P1 폴리곤 증액(골강판·물받이·하역장 캐노피), 창대·인방·하역 에이프런 베벨. main 10.6k/13.2k/17.2k/16.6k.
- 사진 정량 비교는 근접 실사진이 없어 미실시.

### 신탄진IC 톨게이트 — 완료
- `SintanjinTollgate_L1_6x4`, 7차선 비대칭 아치·3갠트리.
- 2026-11-20: 차로 데이터 `toll_lanes.json`(진입 2·진출 5, 부스 4)과 본선 차로 조사 `lane_research.md`(왕복 8차로, 출처 포함) 추가. 작동 구현 방안은 `docs/tollgate_operation_plan.md`(설계만, 코드 미작성). 진출 하이패스 수는 사진 2 vs 나무위키 '3차로'로 미확인. X/V 차로 신호는 서측 아치 전면 테두리 상단에 밀착(가림 해소).
- 2026-11-19: `trim_white` 6 m 타일로 삼각형 절감 후 캐노피 하부 강재·부스 디테일 재투자, 드레인 부재 겹침면 수정, 기둥 받침·부스 지붕 캡 베벨. main 20.3k.

### 석봉동 행정복지센터 — 완료, 남은 확인 있음
- `SeokbongWelfareCenter_L1_7x9`(시그니처). 경사로–동측 데크 연결(2안), 로컬푸드 통창·간판, 현관 LED, 서측 2층 테라스 등은 2026-11-18 완료(근거 `work/ramp_link_report.md`, 비교 이미지 `work/*_compare.png`).
- 2026-11-19: 백색 패널 명도 하향·줄눈 노멀, 태양광 거치대 하부 비가시 부재 제거(48.7k→39.9k) 후 옥상 설비·코핑·물끊기 재투자, 창대·인방 베벨(→44.3k). 위성 외곽 일치 64% 유지.
- **남은 확인**: 북측동 3층 띠 색(`brown_panel` vs 준공 사진의 짙은 회색) 사용자 판단, 남동 표지석 구성, 계단·국기게양대·전실 치수(추정값).

### 고속도로 소품 7종 — 완료 (인게임 미확인)
- 방음벽(투명·흡음), 문형·측주식 녹색 표지, W빔 가드레일(1단·2단), 콘크리트 중앙분리대. 실사진 23매 근거, 치수·출처는 `shape_notes.md`.

### 신탄진형 단독주택

- 1단계 완료. 신탄진 일대 단독주택 24동의 거리뷰 120장을 조사하고 [단독주택 설계 기준](cs2-kit/projects/korean-detached/STYLE_BRIEF.md)에 유형별 치수와 색을 정리했다.
- 2단계는 고동색 벽돌과 옥상 테라스를 갖춘 01호(2×3칸)까지 승인했다. 최종 검사에서 겹침 면은 0개였으며 인게임 확인은 남아 있다.
- 02호(마당 단독주택), 03호(외부 계단과 흰 난간벽), 04호(1층 상가 겸용)는 보류했다.

### 신탄진형 다세대 빌라

- 1단계 완료. 빌라 24동의 거리뷰 120장을 조사하고 [빌라 설계 기준](cs2-kit/projects/korean-villa/STYLE_BRIEF.md)에 중밀도 주거 후보 4종을 정리했다.
- 후보는 적갈색 벽돌과 흰 모서리의 4층 필로티형, 차콜색 벽돌과 석재의 4층 필로티형, 흰 미장과 돌출창의 4~5층 필로티형, 1층 상가 겸용형이다.
- 2단계 모델링은 미배정이다. 재개 시 사진 모음으로 유형을 검토하고, 거리뷰에 보이지 않는 옥상 평면은 위성사진으로 확인한다.

### 폐기: 1970~90년대풍 한국형 주택 4종 (`korean-lowrise`)
- "너무 올드하고 모델링이 어색하다"는 판단으로 2026-11-19 삭제. 코드: `git show 748f6a5:cs2-kit/projects/korean-lowrise/house_core.py`.
- 여기서 나온 지적 25건은 `reports/korean_housing_lessons.md`로 정리해 새 단독·빌라에 적용한다.

---

## 3. 열린 결정과 인게임 확인 목록

**사용자 결정 대기**
- 맵 범위를 북쪽으로 1.5~2 km 옮길지(현재 높이맵 북단 금강교 36.4585°N, 남단 둔산 36.3295°N). 높이맵은 다른 PC에서 작업했다고 함 — 저장소 반영 여부 미확인.
- 석봉센터 북측동 3층 띠 색.
- 공장 사무동의 차가운 흰색 창 조명 유지 여부.

**게임 안에서 확인할 것**
- 이번에 바뀐 전 에셋 재가져오기: 게임을 끄고 `ImportedData` 캐시에서 해당 에셋 항목을 지운 뒤 `cs2-import/<에셋>`에서 가져온다(아래 규칙).
- 알파 컷아웃(빗물 자국 등 투명 칠 면)이 게임 셰이더에서 뚫리는지.
- 야간 조명: 석봉 LED·유리 그래픽, 공장 고측창·사무동, 톨게이트 부스·신호, 엑슬루 창.
- 톨게이트 도로·차량 통과와 배치 방법(`Building` 프리셋 + Anarchy, 미확인).
- uzacha 에셋과 같은 시간대·카메라로 나란히 비교(`reports/detail_gap_analysis.md`의 남은 P1·P2 판단 근거).
- 한국 주거 구역 등록 방식: `reports/korean_lowrise_zone_guide.md`(저밀도 주거로 재구성, 독립 ZonePrefab, 레벨 1~5 × lot 세트).

---

## 4. 작업 규칙

### Git
- 커밋은 `main`에 직접 하고 `origin main`으로 푸시한다. 기능 브랜치를 만들지 않는다. 커밋 메시지는 한국어.
- 커밋하지 않는 것: `cs2-import/`(생성물), `projects/*/work/_sign_cache/`, `projects/*/work/roadview_extra/`(저작권 사진), `.chrome-vr`, 워커 임시 기록(`work/kitext_*` 등).
- `cs2-kit`은 git subtree(squash)다. 원본 갱신: `git subtree pull --prefix cs2-kit https://github.com/nazunamoe/cs2-kit.git claude --squash`.

### 키트와 확장
- 원본 키트(`cs2kit.py`, `tools/`)는 고치지 않는다(업스트림 충돌 방지). 기능 추가는 `cs2-kit/local/kitext.py`(opt-in) — 베벨 `bevel_box`/`ax_bevel`, 개구부 옆면 `paint_reveal`, 칸 전체 UV `uv_cell`, 질감 `solid_weather`/`stone_trim`. 오염 띠 함수(`grime_band` 등)는 사용자가 싫어해 쓰지 않는다.
- 단색 칸·`K.paint()`는 텍스처 칸 가운데 절반만 늘여 쓴다. 글자·그림 칸은 `uv_full`/`uv_cell`로.
- 한국형 주거는 `reports/korean_housing_lessons.md` 25항(겹침 면 0, 계단 틈 0, 모서리 끊김 0, 쨍한 색 금지, 한글 간판 글꼴 등)을 지킨다.

### 빌드·검증
- 완료 조건: `agent.py cycle --mode final` PASS(geometry·LOD·FBX) + 근접(눈높이) 렌더 확인 + `agent.py review`.
- 워커 결과는 총괄이 diff 크기·줄끝·범위 밖 변경을 보고 final을 직접 다시 돌린 뒤 커밋한다.
- 생성기를 고쳤으면 반드시 다시 빌드한다(생성기만 커밋되고 결과물이 옛 버전으로 남은 사례: 한국형 P1, 엑슬루 107·108).

### 결과물 배포와 게임 가져오기
- 빌드 후 `python tools/sync_cs2_import.py <이름 일부>`로 `cs2-import/<에셋>/`을 갱신한다(FBX·PNG만, 매번 새로 만듦, 끝에 알베도 검사). 뷰어는 `asset-viewer\sync_preview.bat <프로젝트>`.
- 게임 Asset Importer에서는 `cs2-import/<에셋>` 폴더 **하나만** 고른다. 프로젝트 폴더를 고르면 가짜 프리팹·같은 ID 중복 저장 오류가 난다(2026-11-18 석봉센터 2회).
- 같은 게임 세션에서 같은 에셋을 두 번 가져오지 않는다. 메시를 고친 뒤에는 게임을 끄고 `%USERPROFILE%\AppData\LocalLow\Colossal Order\Cities Skylines II\ImportedData\<캐시ID>\`의 해당 항목을 지운 뒤 가져온다.
- 프리셋: 6x6 이하 주거·상업은 `Spawnable (Growable)`(이름 `_L<레벨>_<너비>x<깊이>`), 6x6 초과(석봉 7x9, RailDepot 4x8)는 `Signature`. 구역 건물은 lot마다 레벨 1~5 세트가 있어야 레벨업 때 바닐라로 안 바뀐다.

### 오케스트레이션 (Orca)
- 총괄이 Orca CLI(`orchestration worker-start`)로 워커를 띄우고 `worker_done`을 받아 교차 검토한다. 구현한 워커가 자기 결과를 검토하지 않는다.
- 2026-11-19 사용: Antigravity `gemini-4-neon` high(단독·빌라), Codex `gpt-6.2-astra` low(kitext 적용 4워커).

---

## 5. 계획

**0단계 범위 확정** — 위 3절 결정 대기.

**1단계 뼈대**: 높이맵·자원맵 임포트, 금강·갑천 수원(`maps/sintanjin/MAP_GUIDE.md`) → 위성 오버레이 트레이싱 → 광역 교통축(경부고속도로, 신탄진IC, 회덕JC, 호남고속도로지선, 북대전IC, 경부선·고속선, 철도차량정비단, 국도 17호선) → 간선도로·산업단지 격자.

**2단계 파일럿 신탄진 1 km²**: 엑슬루·신탄진역·주변 상가·빌라로 스케일·프레임·구독 에셋 호환·부족 에셋 확인. 바닐라 역의 이질감이 크면 `신탄진역`을 앞당겨 제작.

**3단계 에셋**

| 구분 | 대상 | 상태 |
|---|---|---|
| 자체 제작 완료 | 엑슬루 12동, 공장 4종, 톨게이트, 석봉센터, 고속도로 소품 7종 | 완료 |
| 주거 에셋 | 신탄진형 단독주택과 다세대 빌라 | 모두 1단계 완료. 모델링 현황은 2절 참고 |
| 랜드마크 대기 | 신탄진역, 한국타이어·KT&G 공장, 엑스포아파트 대표 동, 관평동 단지, 대학 본관, 신탄진휴게소(하이패스) | 구역 순서에 맞춰 하나씩 |
| 범용 대기 | 대학·R&D 커튼월(`--template cw`), 지식산업센터, 근생 상가 | 대기 |
| 구독 | 판상형 아파트, 필로티 빌라, 상가, 이마트, 주차장 | 호환 미확인 |

**4단계 구역 순서**: 신탄진 → 대덕산업단지(목상·문평) → 대덕테크노밸리(관평·송강, 캠퍼스) → 전민·문지 → 평촌·철도차량정비단·회덕·읍내동·경부고속도로 축 → 계족산·골프장.

**5단계 디테일링**: 한글 간판·데칼, 가로수, 하천 둔치, 방음벽, 전봇대·전선(한국 골목 인상의 핵심 — 건물 밖 소품).

### 구독 후보 에셋 (호환 미확인)

| 이름 | 용도 | 제작자 |
|---|---|---|
| KR Apartment Set | 판상형 아파트 | 의릴라 |
| CS Korean Style Piloti Villa Set | 필로티 빌라 | uzacha |
| Cities Shopping Town - Korean Commercial Building 2 | 근생 상가 | deokpal |
| CS Korean E-Mart | 대형마트 | uzacha |
| CS KR Parking Pack | 주차 데칼 | 미확인 |
| Apartment Plan (모드) | 아파트 단지 구획 | zacumyou |

참고: [나무위키 CS2 애셋 목록](https://namu.wiki/w/시티즈:%20스카이라인%20II/모드/애셋) · [Apartment Plan](https://github.com/zacumyou/ApartmentPlan) · [디시 한국형 아파트 에셋 정리](https://m.dcinside.com/board/citiesskyline/105876) · [CS2 Wiki 에셋 임포트](https://cs2.paradoxwikis.com/Assets:_Importing)

### 참고 보고서
- `reports/detail_gap_analysis.md` — uzacha 대비 디테일 차이 원인(재질 반응·폴리곤 배분·부지·알베도)과 P0~P2 권고.
- `reports/korean_lowrise_zone_guide.md` — 한국 주거 구역 등록 방식.
- `reports/korean_housing_lessons.md` — 한국형 주거 재발 방지 규칙 25항.
- `maps/sintanjin_jeonmin/ROAD_LANE_GUIDE.md`, `SATELLITE_UPGRADE.md` — 차선 가이드·위성 오버레이(인게임 미확인).
