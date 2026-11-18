# 한국 고속도로 소품 세트 — 형상·치수 노트

좌표: 1 unit = 1 m, 지면 z=0, 도로(차량) 쪽 = -Y, 이어 붙이는 방향 = X. 내보낼 때 바닥 중앙으로 피벗 이동.
`# estimated` = 기준 원문(별표·표준도)에서 수치를 직접 확인하지 못해 일반 실사진·제품 관례로 정한 값.

## 출처

| # | 출처 | 확인한 내용 |
|---|---|---|
| S1 | 한국 흡음형 방음벽 연구 (koreascience, 예: https://koreascience.kr/article/JAKO202108062271169.pdf 외 같은 검색 결과) | H-beam 을 일정 간격으로 세우고 폭 0.5 m × 길이 2 m(또는 4 m) 방음판을 끼우는 구조가 대부분, 흡음판 두께 100 mm, 전면 슬릿형, 흡음재 유리섬유 50 mm |
| S2 | 방음벽 특허 KR101220882B1 (https://patents.google.com/patent/KR101220882B1/ko) 등 | 콘크리트 기초 위 H-빔 지주, 지주 사이 방음판 상하 적층 |
| S3 | 도로표지규칙 (국토교통부령, https://ko.wikisource.org/wiki/도로표지규칙 , https://molit.go.kr/USR/law/m_46/dtl.jsp?r_id=8379) | 안내표지 글자·기호 백색, 영문 병기(생략 가능), 규격은 별표 2·3 (별표 수치 미확인) |
| S4 | 안내표지의 국·영문 문안 배치 연구 (https://koreascience.kr/article/JAKO201101660924881.page) | 기존 규칙: 한 지명의 국문 위·영문 아래 상하 배치 |
| S5 | 운전자 시력기준에 의한 도로표지 글자크기 연구 (https://koreascience.kr/article/JAKO201209857778623.page) | 고속도로 표지 글자 세로 22~60 cm |
| S6 | 콘크리트 중앙분리대 형식별 연구 (https://koreascience.or.kr/article/JAKO200311922077852.page, https://koreascience.kr/article/JAKO201725150297894.pdf) | 1980 남해고속도로 F형 810 mm + 방현망 → 이후 1270 mm 고규격(SB5급) 콘크리트 중앙분리대 |
| S7 | 국토교통부 도로안전시설 설치 및 관리지침 개정 공지 (https://www.molit.go.kr/USR/I0204/m_45/dtl.jsp?idx=18406) | 방호울타리 기준 문서 위치(2024.12 개정). 지주 간격·레일 높이 수치는 첨부 원문에서 미확인 |
| S8 | W빔 가드레일 제품 카탈로그 (https://www.shinkokenzai.co.jp/cms_wp/wp-content/uploads/2024/11/GF_catalogue_202411.pdf) | φ139.8 × 4.5 강관 지주, 지주 간격 2 m 급 (일본 제품 — 국내 원형 지주 W빔과 같은 계열이라 참고만) |

## 1. 방음벽 (우선순위 1)

| 항목 | 값 | 근거 |
|---|---|---|
| 모듈 길이 = 지주 간격 | 2.00 m | S1 (판 길이 2 m) |
| 지주 | H-150×150×7×10, 모듈 왼쪽 끝 1본(x=-1.0), 플랜지 ±y, 웨브에 판 끝이 홈으로 끼움 | S2, 단면 # estimated |
| 베이스플레이트 | 0.28 × 0.28 × 0.022 m | # estimated |
| 콘크리트 기초벽 노출 | 폭 0.30 m, 높이 0.60 m, 4 m 신축이음 홈(텍스처) | # estimated |
| 금속 흡음판 | 단 높이 0.50 m, 두께 0.095 m, 전면 슬릿 타공, 회녹색 | S1 (폭 0.5 m·두께 100 mm·슬릿형) |
| 금속형 단 수 | 7단 → 총고 4.10 m | # estimated |
| 투명형 구성 | 흡음판 1단 + 투명 PC 판 3단 × 1.00 m, 알루미늄 가로살 0.05 m, 판 두께 12 mm (`_Gls`) | # estimated |
| 상부 | 지주 캡 0.18 × 0.18, 금속형 상부 캡 채널 | # estimated |

- 투명판은 키트 `gls` 메시(`_Gls.fbx`)로 분리. LOD2 에는 유리 메시가 없어 불투명 청회색 `acrylic_lod` 판으로 대신함.
- 조류충돌 방지 점 패턴(환경부 가이드라인 5×10 규칙)은 생략 — 넣으려면 `glass` 칸에 painter 추가.
- 금속형 흡음판 뒷면도 앞면과 같은 슬릿 무늬(상자 1개 = 재질 1개). 실제 뒷면은 민판이 많음.

## 2. 녹색 안내표지 (우선순위 2)

공통: 녹색 바탕 (0,112,74) + 백색 글자·테두리, 국문 위·영문 아래(영문 글자 높이 ≈ 국문의 1/2, # estimated), 글꼴은 맑은 고딕 Bold / Arial Bold (공식 한길체 대체, # estimated).
간판 텍스처는 `sintanjin-tollgate` 생성기의 `_load_font / _fit_font / 텍스트 중앙정렬 / .npz 캐시` 방식을 `hwprops_common.py` 에 복사해 사용(실제 종횡비 캔버스에 그린 뒤 정사각 칸에 축소 → 면 UV 에서 원래 비율로 복원).

### 2-1. 문형식 갠트리 `SignGantry`

| 항목 | 값 | 근거 |
|---|---|---|
| 기둥 중심 간격 | 22.0 m (편도 4차로 3.6 m × 4 + 갓길·측대) | # estimated |
| 기둥 | 각형 0.50 × 0.50 m, 기초 페데스탈 1.1 × 1.1 × 0.6 m | # estimated |
| 보 | 4현재 와렌 트러스, 현재 0.14 m 각, 깊이(y) 0.9 m, 높이 6.30~7.90 m, 10칸 | # estimated |
| 판 하단 높이 | 5.50 m (문형식 하단 5.0 m 이상 관례 확보) | # estimated |
| 왼쪽 판(직진) | 6.5 × 3.0 m: 고속국도 1 노선표지 + 청주 Cheongju / 서울 Seoul + ↓ | 지명은 과제 지정, 노선 1 = 경부 |
| 오른쪽 판(진출) | 5.5 × 3.0 m: 신탄진 Sintanjin / 대전 Daejeon + ↗ + 출구 EXIT | 과제 지정 |
| 국문 글자 높이 | 약 0.66 m(판 높이의 22 %) | S5 범위(22~60 cm)보다 약간 큼 # estimated |

### 2-2. 측주식 이정표 `SignSideDistance`

| 항목 | 값 | 근거 |
|---|---|---|
| 판 | 3.6 × 2.4 m, 하단 2.0 m | # estimated |
| 지주 | φ216.3 강관 2본(x=±1.1), 콘크리트 기초 0.7 × 0.7 × 0.25 m | # estimated |
| 문안 | 신탄진 Sintanjin 2 km / 청주 Cheongju 23 km / 서울 Seoul 128 km | 거리값은 예시 문안 # estimated |

## 3. 가드레일·중앙분리대 (우선순위 3)

### 3-1. W빔 가드레일 `GuardrailWBeam`

| 항목 | 값 | 근거 |
|---|---|---|
| 모듈 | 4.0 m 레일 1장, 지주 x=-2.0, 0.0 (간격 2.0 m) | S8, # estimated |
| W 단면 | 폭 310 mm, 깊이 83 mm, 두께 4 mm (산 2·골 1) | 일반 W빔 규격 # estimated |
| 레일 중심 높이 | 0.60 m | # estimated |
| 지주 | φ139.8 원형 강관, 높이 0.80 m + 캡 | S8 |
| 간격재 | 0.12 × 0.10 × 0.18 m | # estimated |
| 시선유도표지 | 0.10 × 0.10 m 백색 반사체(모듈당 1개) | # estimated |

바닐라 비교: 바닐라 CS2 고속도로 가드레일과의 차이는 게임 안에서 직접 대조하지 못했음(NOT_CHECKED). 한국형의 눈에 띄는 차이는 원형 강관 지주·간격재·지주마다 반사체.

### 3-2. 콘크리트 중앙분리대 `MedianBarrierConcrete`

| 항목 | 값 | 근거 |
|---|---|---|
| 높이 | 1.27 m (SB5급 고규격) | S6 |
| 단면 | F형 2단 경사: 하단 수직 0.075 m → 55° 경사 → 꺾임 0.33 m → 84° 경사 → 상단 | S6(F형 도입) + 형상 # estimated |
| 하단 폭 / 상단 폭 | 0.81 m / 0.25 m, 상단 모따기 0.02 m | # estimated |
| 모듈 | 4.0 m, 신축이음 홈은 텍스처 | # estimated |
| 반사체 | 양면 황색 0.16 × 0.10 m, 모듈당 1쌍 | # estimated |

바닐라 비교: 바닐라 고속도로 중앙 방호벽(저지형)과 비슷한 계열이라 우선순위를 낮춰 단순 압출 1개로 만듦. 차이는 높이(1.27 m vs 저지형 약 0.8~0.9 m)와 반사체. 방현망·방현판은 생략.

## 4. LOD·삼각형 (final 기준)

| 소품 | 크기 (x×y×z m) | main | LOD1 | LOD2 | 비고 |
|---|---|---|---|---|---|
| NoiseWallClear | 2.14 × 0.30 × 4.17 | 116 (+Gls 36) | 54 (+Gls 12) | 40 | |
| NoiseWallMetal | 2.14 × 0.30 × 4.17 | 140 | 54 | 54 | |
| SignGantry | 23.1 × 1.28 × 8.64 | 724 | 352 | 124 | 아틀라스 2048, 하단 절반 비어 있음 |
| SignSideDistance | 3.6 × 0.70 × 4.45 | 144 | 52 | 52 | 아틀라스 2048 |
| GuardrailWBeam | 4.07 × 0.33 × 0.87 | 196 | 72 | 48 | |
| MedianBarrierConcrete | 4.0 × 0.81 × 1.27 | 42 | 18 | 10 | |

## 5. 키트 검사와 소품의 차이

- `win OBJ missing` 경고: 소품에 창이 없음 → 해당 없음(N/A).
- photo / tiles: `photo_refs.json` 없음 → NOT_APPLICABLE (사진 대조 없음, 형상은 기준·관례값).
- lot: 키트가 건물 로트를 붙여 이름이 `_L1_1x1` 형태가 됨. 소품 배치에는 의미 없음(갠트리만 3x1).
- lod_check 는 단일 모듈을 사방에서 보므로 이어 붙일 때 가려지는 모듈 끝면도 닫아야 통과 → 모든 상자를 닫음(밑면만 생략).
- `prism` 헬퍼 면 방향은 `work/check_normals.py` 로 자체 검사(바깥 법선).
- 에셋 뷰어(`asset-viewer`) 메뉴 미등록: `loadPreviewStem` 이 `<stem>_Win.fbx` 를 필수로 받는데 소품은 창 메시가 없어 로드가 실패함. 뷰어 코드 수정은 이번 범위 밖 → "에셋 폴더" 선택으로 확인 가능.

## 6. 실사진 대조 (신탄진IC~회덕JC~금강교 일대, 2025·2019 거리뷰 23매 기준)

실사진(`photos/`)과 기존 1차 미리보기(`work/before_*.png`)를 나란히 대조해 확인한 재질·색감·형상 격차:

1. **공통(전체 소품 텍스처 흐림·평면감 원인)**:
   - `hwprops_common.py` 의 `prism`·`extrude` 가 `A.uv(tag)`(칸 중앙 단색 픽셀)만 참조해 `_paint_concrete`·`_paint_galv` 등의 디테일이 **지주·압출 단면에 전혀 매핑되지 않았음**(특히 중앙분리대·가드레일·갠트리가 완전 단색으로 보임).
   - 아연도금·강재·기초부 칸이 `px=64` 소형으로 타일링·거칠기(MaskMap)·요철(Normal) 대비가 부족함.

2. **NoiseWallClear (`noisewall_clear_01~04`)**:
   - 실물 하단 흡음패널은 청록 단색이 아니라 **따뜻한 스톤베이지·회갈색 정사각 루버 카세트 격자**(폭당 6열 × 단당 5행, 하단 2단 노면 비산 오염 더 짙음, `(168,154,147)`→하단 `(143,129,117)` 실사진 중앙값)이며, 기초 콘크리트는 **세로 골이 파인 주름 옹벽(fluted plinth)** + 줄눈 빗물 얼룩이 뚜렷함.
   - H형강 지주 하단에 **삼각 보강 리브·앵커볼트 베이스플레이트** 가 붙고, 상단 투명부에는 일정 간격 **수평 고무 가스켓 가로바(transom)** 와 지주 클램프, **맹금류(조류 충돌 방지) 실루엣** 이 부착됨.

3. **NoiseWallMetal (`noisewall_metal_01~03`)**:
   - 실물 경부고속도로(엑슬루·덕암동 인접) 금속 방음벽은 밝은 민트색(`122,150,146`)이 아니라 **진한 챠콜·브론즈그레이 계열(`~75,70,68`)** 이며, 하단 1~2단만 밝은 스톤그레이(`~125,115,108`) 변화·풍화가 있음.
   - 기존 슬릿 가로선 대신 **세로 분절된 사각 흡음 카세트 격자(베이당 4~5열 × 다단 적층) + 상하 이음 프레임 + 수직 물때** 와 하단 **세로 주름 콘크리트 기초** 가 핵심 특징.

4. **SignGantry (`sign_gantry_01~04`)**:
   - 실물 트러스는 단순 수직 프랫(Pratt)이 아니라 **굵은 원형 강관 상·하현재 + 와렌(Warren, `/` `\`) 사선 부재 + 중앙 스플라이스 볼트 플랜지**, 양끝 **복열(2열) 원형 강관 지주 + 수평 타이 플레이트(리브) + 앵커 베이스플레이트**, 우측 **안전 케이지 사다리 + 트러스 상부 점검 난간**, 표지판 뒷면 **가로·세로 보강 C채널 프레임과 볼트 클램프** 로 구성됨.
   - 트러스·지주는 무광 단색 회색이 아니라 아연도금강 은회색 반사질감(`metal=0.72, gloss=0.58`) + 용접/볼트 이음 명암이 있음.

5. **SignSideDistance (`sign_side_01~05`)**:
   - 실물 표지판 정면은 백색 이중 라운드 테두리 안쪽에 짙은 **고속도로 반사지 녹색(`~(8,108,76)` 보정 반사율)**, 청색 타원/방패 노선번호, 상단 출구 번호 보조판, 굵고 여백이 균형 잡힌 국/영문 및 진출 화살표가 인쇄되며, 테두리 리벳·프레임 두께감·약한 프리즘 입자 반사(gloss/normal)가 있음.
   - 뒷면(`03`, `04`)은 단색 알루미늄 상자가 아니라 **복수의 수평·수직 C형 보강 채널 + 파이프 지주를 감싸는 2볼트 U클램프/구멍 뚫린 브래킷 + 지주 상단 캡·하단 기초** 가 선명히 드러남.

6. **GuardrailWBeam (`guardrail_01~03`)**:
   - 실물은 지주가 노출된 1자 각관이 아니라 **원형 강관 지주 + 상단 파이프 캡 + 레일 배면 U/사각 블록아웃 간격재**, 겹침 이음부 **타원형 8볼트 패턴 + 중앙 슬롯 볼트**, 아연도금 스팽글 질감, 단부/구간 **황·흑 사선 반사지 또는 반사 시선유도표** 가 명확함.
   - 레일 전면 W자 굴곡의 음영 대비와 지주/간격재 결합부 3D 형상이 보강되어야 근접 시 철제 입체감이 살아남.

7. **MedianBarrierConcrete (`median_01~04`)**:
   - 실물 경부고속도로 F형 콘크리트 중앙분리대는 노면과 닿는 하단 25 cm 에 진한 타이어·빗물 오염 띠, 측면 거푸집 결·잔골재 질감·타이홀 자국, 4 m 마다 뚜렷한 **V자 신축이음 홈** 이 있으며, 일부 구간 상단 시선유도띠·표지병/반사체가 부착됨.
   - 기존 압출 메쉬가 `A.uv("concrete")` 단색 1픽셀만 샘플링하던 오류를 수정하고 4 m 전체 UV 타일링 + 고해상도(512×256) 콘크리트/오염/줄눈 노멀·거칠기 맵 적용 필요.

## 7. 실사 기반 보강 결과 및 최종 삼각형 수 (Before → After)

| 소품 | Before (main / LOD1 / LOD2) | After (main / LOD1 / LOD2) | 비교 이미지 (`work/`) |
|---|---|---|---|
| NoiseWallClear | 116 (+Gls 36) / 54 (+Gls 12) / 40 | 288 (+Gls 36) / 62 (+Gls 12) / 40 | `compare_photo_NoiseWallClear.png` |
| NoiseWallMetal | 140 / 54 / 54 | 206 / 38 / 38 | `compare_photo_NoiseWallMetal.png` |
| SignGantry | 724 / 352 / 124 | 1,688 / 464 / 76 | `compare_photo_SignGantry.png` |
| SignSideDistance | 144 / 52 / 52 | 402 / 106 / 52 | `compare_photo_SignSideDistance.png` |
| GuardrailWBeam | 196 / 72 / 48 | 296 / 84 / 48 | `compare_photo_GuardrailWBeam.png` |
| MedianBarrierConcrete | 42 / 18 / 10 | 114 / 22 / 10 | `compare_photo_MedianBarrierConcrete.png` |

- `hwprops_common.py`: `prism`·`extrude` 미터 UV 타일링 구현, `concrete`(448px)·`concrete_fluted`(384px)·`absorb_panel`(512px)·`absorb_warm`(384px)·`galv`(256px)·`galv_wbeam`(512px)·`sign_back`(256px) 실사진 색상/노멀/광택 반영, 도로표지 반사지 프리즘 질감·노멀·테두리 리벳 추가.
- 6개 소품 모두 `main <= 3×` (및 `<= 2500 / <= 600`), `LOD1 < 0.5× main`, `LOD2 <= 기존 삼각형 수`, 모듈 X 방향 연속 타일링 유지, `check.py` / `lod_check` / `fbx` 전 항목 통과.

## 8. 2차 실사진 보정 (v2: 투명방음벽 · 가드레일 1단/2단 · 중앙분리대)

1. **NoiseWallClear (`noise_wall_clear_cs2.py`)**:
   - **격자 분할 측정**: `noisewall_clear_01_front.png` 픽셀 실측 결과 지주 사이 1칸 폭 약 137~144 px, 유리 단 높이 약 68~73 px (약 **2:1** 가로 긴 직사각형 칸, 4단 적층). 2.0 m 모듈 중앙에 세로 멀리언(폭 0.044 m, 두께 0.050 m)과 4단 가로 프레임(z = 1.80, 2.375, 2.95, 3.525, 4.10 m)을 배치해 **1.0 × 0.575 m (1.74:1) 2열×4단 8칸 격자** 로 재분할.
   - **조류 충돌 방지 스티커**: 3D Y자 막대 대신 PIL 512 px 고해상도 **맹금류(매) 비행 실루엣 알파 텍스처**(`bird_sticker` BaseColor Alpha 컷아웃, 0.44 m / 0.40 m, 날개 칼깃·부채꼴 꼬리)로 교체하고 닫힌 2 mm 박스로 `lod_check` 구멍 0.000% 유지.
   - **유리 재질(Gls)**: 기존 6면 닫힌 유리 박스(렌더 시 이중 블렌딩으로 과도한 불투명 하늘색)를 **단일 얇은 판(gls 16 tris)** 으로 바꾸고 `"glass"` 색상을 중립 회색 반사 톤 `(194, 198, 202)` + `alpha=76` 으로 조정.

2. **GuardrailWBeam (1단 유지) vs GuardrailWBeamDouble (2단 변형 추가)**:
   - **주 형식 판단 근거**: 경부고속도로 본선 노측·IC 램프·금강교 진입부·톨게이트 진입차로 실사진(`guardrail_01_rear_blockout.png`, `guardrail_02_terminal_front.png`, `noisewall_clear_01_front.png`, `sign_side_04_rear_ramp.png`, `sintanjin-tollgate/photos/west_close_look_ne.png`)의 **연속 구간 주 형식은 모두 1단 W빔** 이므로 기본 `GuardrailWBeam` 은 1단으로 유지.
   - **2단형 변형 추가(`GuardrailWBeamDouble`)**: 문형표지(`SignGantry`) 강관 지주·교각 앞 강성 구조물 보호 단부(~16 m 구간, `guardrail_03_run_sunlit.png`, `sign_gantry_02_truss_side.png`)에서 확인된 2단 적층 W빔(레일 중심 z=0.43·0.83 m, 지주 높이 1.06 m, 2단 U블록아웃·8볼트 이음·시선유도표지)을 별도 에셋 `guardrail_wbeam_double_cs2.py` 로 추가하고 `asset-viewer/index.html` 메뉴에 등록.

3. **MedianBarrierConcrete (`median_barrier_cs2.py`)**:
   - **줄눈 간격**: `median_02_corridor_clean.png`·`median_04_sunlit_profile.png` 에서 4.5 m 이상 연속 구간 내 중간 거푸집 줄눈·타이홀 없이 4~6 m 단위 끝단 수직 신축이음만 확인 → 기존 1 m/2 m 중간 줄눈과 폼타이 점을 제거하고 **4 m 모듈 끝단(`x = ±2.0 m`) 신축이음 홈** 만 남김.
   - **색감·오염**: 어둡고 얼룩졌던 1차 콘크리트 대신 실물 밝은 회색 슬립폼 콘크리트 `(202, 198, 191)` (`normal_strength=0.85`)로 밝히고, 오염은 노면 접지 최하단 `0~0.16 m` 에만 약하게(`~9.5%`) 제한.

| 에셋 | 1차 (main / LOD1 / LOD2) | 2차 (main / LOD1 / LOD2) | 2차 비교 시트 (`work/`) |
|---|---|---|---|
| NoiseWallClear | 288 (+Gls 36) / 62 (+Gls 12) / 40 | 292 (+Gls 16) / 62 (+Gls 2) / 40 | `compare_photo_v2_NoiseWallClear.png` |
| GuardrailWBeam | 296 / 84 / 48 | 296 / 84 / 48 (유지) | `compare_photo_v2_GuardrailWBeam.png` |
| GuardrailWBeamDouble (신규) | — | 440 / 136 / 44 | `compare_photo_v2_GuardrailWBeamDouble.png` |
| MedianBarrierConcrete | 114 / 22 / 10 | 114 / 22 / 10 | `compare_photo_v2_MedianBarrierConcrete.png` |
