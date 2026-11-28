# SintanjinVillaA01 형상 메모

## 근거 사진
`work/roadview_extra/` (git 제외, 출처 `SOURCES.md`). 대전 대덕구 덕암동 빌라 골목, 네이버 거리뷰 2024-06·2025-12·2026-10.
기존 브리프의 `v01~v24`, `user_ref_*` 원본은 이 PC에 없어(Desktop·Orca 작업폴더·에이전트 세션 전체 검색) 같은 생활권 실사를 새로 확보했다.

재확인용 출처: 네이버 거리뷰 기준 건물 약 36.43703N, 127.42029E. 파노라마 `2nQDiuCYy7H6eOaZRAatSA`(2026-10-07, 36.43694/127.42018, a01~a04), `DFiBvpqWt3dfdiYY9u5TCQ`(2026-10-07, 36.43651/127.42005, a05), `Nlp6eE_504ThcSI-Co8-kw`(2024-06-25, 36.43694/127.42056, a06). 사진은 로컬 참조 전용이며 배포하지 않는다.

| 파일 | 내용 |
|---|---|
| a01_road_oblique | 도로 쪽 사선: 흰 기둥 필로티, 층별 흰 띠, 다색 적갈 벽돌, 갈색 경사 처마, 적색 가스 배관 |
| a02_side_bands | 측면: 띠 3줄, 창 배치, 배관 수평·수직 |
| a03_rear_court | 후면 마당: 큰 미닫이창, 띠 |
| a04_entrance_plate | 계단 입구·남색 번호판 |
| a05_row_from_south | 같은 골목 빌라 열: 4층 적갈 벽돌 + 흰 띠 반복 |
| a06_courtyard_2024 | 2024년 같은 마당 (흰 띠·창틀·우수관) |

## 치수
- 1층 필로티 유효 2.45 m, 2층 바닥 3.00 m, 기준층 2.80 m, 슬래브선 11.40 m (브리프 2장, a02 벽돌 줄 수)
- 폭 10.6 / 깊이 12.4 m, 코어 x 2.5~5.3, 후면 실 y 8.0~12.4 — `# estimated`
- 흰 띠: 필로티 슬래브 2.45~3.10, 층간 z_f-0.08~z_f+0.14, 돌출 0.06 (모서리 감싸는 한 덩어리 박스, 규칙 8)
- 흰 모서리 띠 0.30 m (브리프 A), 띠 안쪽 0.03 돌출이라 겹침 0
- 창: 외틀 95 mm PVC, 유리 0.145 m 후퇴(detached_core.add_recessed_wall)

## 색
- 벽돌 BaseColor (128,92,86): a01 그늘 벽돌 면 (132,104,99) + 브리프 '진적갈'. 벽돌 28%는 0.70배 암자색, 14%는 밝은 적색(a01 다색 벽돌)
- 줄눈 (188,186,185) 밝은 회색 시멘트(규칙 18), 흰 띠 (212,211,208) V≤215
- 가스 배관 (150,88,75) 채도 0.50, 충돌방지 띠 바랜 노랑·흑 평균 채도 약 0.44

## 하지 않은 것
- 오염 띠·지면 바닥 메시·주차선 메시 없음 (카스토퍼 3D 블록과 기둥 충돌방지 띠만)
- 공동현관 캐노피: 현관이 필로티 안쪽이라 슬래브가 대신함

## 2026-11-22 총괄 교차 검토
- `coordinator-final` 재실행 후 근접 창틀·방범난간·흰 모서리·필로티·현관·가스관·옥상 렌더를 사진과 대조하고 `agent.py review` PASS 기록.
- final 체크 build/geometry/preview/LOD/FBX/visual_review PASS, 오류·경고 0, COPLANAR 0, 알베도 경고 0. 대표형이라 photo/tiles 자동 픽셀 매칭 NOT_APPLICABLE.
- main 14,782, LOD1 5,462(37%), LOD2 222 + 창 156 = 378. 브리프 목표 30k보다 낮으나 불필요한 폴리곤 증액은 하지 않았다.
- 눈높이 부재 검토는 키트의 낮은 pitch 확대 직교 렌더 기준이며 실제 게임 원근 카메라·스케일 검증은 남아 있다.
- 빌드 및 `cs2-import/SintanjinVillaA01_L1_2x3` 21개 FBX·PNG, asset-viewer 미리보기 동기화 완료.
- 인게임 중밀도 주거 Growable 등록·정면(-Y)·입주·야간·LOD 전환은 미확인. 레벨 1~5 세트와 전용 구역은 아직 제작하지 않았다.

## B01 — 차콜 벽돌 4층 필로티 (2026-11-22, 구현 워커)

`SintanjinVillaB01_L1_2x3`, Desktop 작업본에서만 제작. A01 코어의 아틀라스·번호판·충돌방지판과 detached_core의 실제 후퇴창·PVC틀·난간·설비 헬퍼를 재사용했다. B01 별도 생성기는 A01 빌더를 호출하지 않는다. 공용 변경은 `build_atlas(..., charcoal=False)` opt-in과 B 전용 석재 칸뿐이며 A 기본값은 그대로다.

### 실사 근거
원본 v13은 Desktop 검색에서 발견되지 않아 `naver_pano_view.py`로 덕암로221번길 실사를 새로 확보했다. 핵심 파노라마 `n9T1rrgt58a0XZIpappJGA`, 위치 36.440440N / 127.421832E, 촬영 2026-10-14 10:10:54. `b08_front/left/right/piloti/window/full/roof.png`의 자세한 시점은 로컬 `work/roadview_extra/SOURCES.md`에 있다. 보조 파노라마 `D8howePaMetySDuxrwOXmg`(36.440442/127.422045, 2026-10-14 10:10:57, b07_w)에서 전체 4층 실루엣을 확인했다. 원본 사진은 git 제외이며 이동·복사·변경·커밋하지 않았다.

사진에서 흰 층간 띠가 없는 명암 혼합 차콜 벽돌, 회색 줄눈, 흰 PVC 2~3짝 창, 검정 낮은 살난간, 전면 실외기와 연결관, 왼쪽 계단실의 다크 수직 유리와 반층 멀리언, 양쪽 필로티와 황흑 기둥 보호띠, 공동현관을 관찰했다. 사진은 강한 직사광으로 밝게 보이므로 차콜(96,98,100)과 흑화강석(54,56,59)은 브리프 권장값으로 청천반사를 중화한 값이며 픽셀 실측치라고 주장하지 않는다.

### 대표형 차이와 추정
- 특정 번지 실측 복제가 아니다. 폭 11.6m·깊이12m·층고2.8m·파라펫1m는 사진 비례 추정. 2x3 lot은 정면1+2면 필로티와 후면 여유를 위해 선택했다. 사진의 왼쪽 날개·정면 폭을 축소하고 계단실은 x=-3.1~-0.7m의 왼쪽으로 유지했다.
- 주차는 좌측1면·우측2면, 코어 정면 유리문은 도로에서 직접 접근하고 우편함은 코어 우측 보행공간에 놓았다. 주차 바닥·주차선 메시 없이 카스토퍼만 배치했으며 실제 차량/시민 경로는 인게임 검증 필요.
- A01의 갈색 경사 처마·층마다 흰 띠·흰 모서리는 사용하지 않는다. 사진상 짙은 슬래브 마감은 판넬 구획이 보이지만 브리프 B의 흑화강석 띠로 재해석했다. 코핑·기단은 모서리를 감싸는 닫힌 솔리드이며 현관 아래 기단은 비웠다.
- 사진 공동현관의 실제 상호와 지붕모양 간판은 넣지 않고 무문자 평캐노피로 단순화했다. 남색 가상번호판과 우편함은 브리프 B를 따른 보충이다.
- 실제 후퇴유리 0.145m, PVC 외틀95mm, 검정 방범난간0.62m. 상층 발코니 돌출 매스는 사진에 없어 만들지 않았고 필로티 슬래브·캐노피의 옆면과 하부는 닫았다.
- 후면/측면 창 배열·실외기·우수관은 가려진 부분을 브리프로 보충한 추정. 옥상 내부·방수색은 위성 미확인이며 회녹 방수 바닥과 1m 파라펫만 추정했다. 관측되지 않은 물탱크·옥탑을 임의로 더하지 않았다.
- 지면 아래 형상·지면포장 메시·오염띠 없음. 모든 지면 접촉 박스는 밑면 생략. 최소 3D 부재와 실제 창 리빌에 삼각형을 사용했다.

### 검토 상태
구현 워커는 자기 visual review를 수행하지 않았다. 총괄이 `coordinator-b01` final을 직접 다시 실행한 뒤 사진/전체/근접/야간을 대조하고 review PASS를 기록했다. build/geometry/preview/LOD/FBX/visual_review PASS, 오류·경고0, photo/tiles 자동 픽셀 대조는 대표형이라 NOT_APPLICABLE이다. 사진 원본과 렌더는 서로 분리되어 있으며 렌더는 `previews/`의 B01 명명 파일만 사용한다. 인게임 Growable 등록·입주·정면(-Y)·야간·LOD 전환은 미확인.

### B01 구현 검증 및 총괄 인계
- doctor OK, resume 실행 후 `agent.py cycle --project korean-villa --generator sintanjin_villa_b01_cs2.py --mode final --label b01-roof-closure --json` 실행. build/geometry/preview/LOD/FBX PASS, 오류0·경고0. 전체 final 상태는 **INCOMPLETE**(visual_review NOT_CHECKED만 남음)이며 final PASS로 주장하지 않는다.
- 삼각형 main **18,794**, LOD1 **4,478 (23.83%)**, LOD2 본체 **216** + 창72면x2 **144** = **360**. COPLANAR main/LOD1/LOD2/Win 모두0, WIN_BLOCKED main/LOD1/LOD2 모두0, dropped_windows0, zmin0. 불필요한 예산 증액 없음.
- LOD 검사는 PASS. 소수 `HOLE_SMALL` 표본(최대0.004%,1px)은 통과기준 내이며 열린 구조를 의도한 것이 아니다. 창 상단이 옥상 내부에서 역면으로 보이던 최초 LOD FAIL은 창을 지붕덱 아래에서 끝내고 덱 접합을 닫아 해결했다.
- `python tools/albedo_check.py SintanjinVillaB01_L1_2x3` 경고0. `python tools/sync_cs2_import.py SintanjinVillaB01_L1_2x3` 완료(21 FBX·PNG), `asset-viewer/sync_preview.bat korean-villa` 완료. 게임에서는 `C:/Users/johye/Desktop/CitiesSimulator/cs2-import/SintanjinVillaB01_L1_2x3` 폴더 하나만 선택한다.
- A01 회귀: 기존 output을 덮어쓰지 않고 `work/b01_a01_regression`에서 별도 OBJ 생성 후 기존 `_check` OBJ6개·PNG15개 **21파일 SHA256/byte 동일** 확인. 기존 텍스처15개도 작업 시작 전 hash와 동일. 증거 `work/b01_a01_regression.json`; 임시 재생성본 정리 명령이 실행 정책에 차단되어 폴더를 보존했으며 커밋 대상에서 제외한다. A01 생성기·스펙·기본값·실제 output·기존 previews는 변경하지 않았다.
- 변경 소스는 `sintanjin_villa_b01_cs2.py`, `building_spec_SintanjinVillaB01.yaml`, `villa_core.py` 7줄 최소 opt-in 수정, 이 메모와 STATUS 및 프로젝트 작업상태/검증 결과뿐이다. 원본 kit/tools·kitext·detached_core·단독01/02·근린상가에는 변경 없음. Git mutation/commit/push 없음.
- 렌더(모두 `cs2-kit/projects/korean-villa/previews/`): `SintanjinVillaB01_L1_2x3.png` 자동 기본4방향, `B01_full_four.png` 정면/오른쪽/후면/왼쪽, `B01_piloti_entrance.png`, `B01_window_railing.png`, `B01_corner_plinth.png`, `B01_stairwell.png`, `B01_roof_edge.png`, `B01_night.png`, `B01_night_piloti.png`. 근접은 전체 메시를 낮은 pitch로 확대하는 키트 직교 렌더이며 물리적인 1.6m 원근카메라를 실측 검증한 것은 아니다.

총괄은 kit 루트 `C:/Users/johye/Desktop/CitiesSimulator/cs2-kit`에서 final을 다시 돌린 뒤 사진과 위 렌더 전부 대조했다. 아래는 재검토 시 사용하는 명령이며 이번 검토는 위 검토 상태 절에 기록한 대로 완료했다. 자동 반환된 정확한 review 명령:

```text
python tools/agent.py review --project korean-villa --status PASS --note "reviewed current artifacts" --artifact "previews/SintanjinVillaB01_L1_2x3.png"
```

추가 근접·야간까지 기록할 권장 명령(총괄이 실제 검토한 후에만 실행):

```text
python tools/agent.py review --project korean-villa --status PASS --note "coordinator reviewed B01 photos, four sides, details and night" --artifact previews/SintanjinVillaB01_L1_2x3.png --artifact previews/B01_full_four.png --artifact previews/B01_piloti_entrance.png --artifact previews/B01_window_railing.png --artifact previews/B01_corner_plinth.png --artifact previews/B01_stairwell.png --artifact previews/B01_roof_edge.png --artifact previews/B01_night.png --artifact previews/B01_night_piloti.png --json
```

## 2026-11-24 퀄리티 업 (A01 · B01)
- 공용 벽돌 월드 좌표 연속 UV(`detached_core.add_recessed_wall`)와 야간 창 발광 강화를 두 빌라에 반영하고, `villa_core.py`에 무이음 옥상 방수 텍스처(`_roof_waterproof_painter`), PIL 로비폰 인터폰(`add_intercom`), 철제 방화문·보조문 디테일(`add_steel_door_details`), 천장 LED(`add_ceiling_lamp`), 계단실·현관 야간 점등 보장(`ensure_lit_windows`)을 추가했다.
- **A01 (`SintanjinVillaA01_L1_2x3`)**: 정면 우측 2~4층 수직 계단실 유리 띠(층간 흰 띠 깔끔 분리, 3층별 야간 점등), 옥상 파라펫 턱·갓돌, 물탱크 고정 프레임·보강 띠·2단 돔/점검 뚜껑·유입/유출/밸브/오버플로우 배관, 옥탑 방화문 디테일, 필로티 후면 철제 보조문·공동현관(문턱·상부 현관등·인터폰·우편함 슬롯·천장 LED). main 16,832 / LOD1 5,484(32.6%) / LOD2 218+창150=368, COPLANAR/WIN_BLOCKED/알베도 경고 0, LODCHECK PASS(0/64). 총괄 체크포인트 승인 완료.
- **B01 (`SintanjinVillaB01_L1_2x3`)**: 좌측 계단실 옥탑(차콜 벽돌·흑화강석 갓돌·철제 방화문), 환기 팬 2기, 배관·벤트 스택, TV 안테나, 무이음 옥상 방수 바닥, 좌측 4층 수직 계단실 유리 띠 3층별 상시 점등, 필로티 천장 LED·공동현관 캐노피/상부 조명·문턱·인터폰, 후면 철제 보조문 디테일 및 보행 동선 정렬(카스토퍼 간섭 해소), 우측 실외기 난간·모서리 간섭 해소(`x=5.18, z+0.30`). main 20,768 / LOD1 4,508(21.7%) / LOD2 226+창148=374, COPLANAR/WIN_BLOCKED/알베도 경고 0, LODCHECK PASS(0/64). B01 작업 중 `villa_core.py` 무수정으로 A01 출력 무변화 유지.
- `agent.py review`는 총괄 검수 후 기록(미기록). 인게임 배치·야간·LOD는 미확인.

## 2026-11-28 인게임 피드백 수정(B01·문 품질) + C01·D01 신규

### 공용 문 헬퍼 (`villa_core.py`)
- `wall_with_doors`: 벽에 문 개구부만 뚫고(창은 조각별 분배) 문 부재는 아래 헬퍼가 따로 설치한다. `detached_core` 는 수정하지 않았다.
- `add_glass_entry_door`: 아노다이징 다크 알루미늄(`alu_dark`) 외곽 문틀 65 mm, 양개 문짝 울거미(선대 60·상대 70·하대 170), 유리 누름대, 스텐 킥플레이트, 받침 2개 세로 바 손잡이, 실린더, 도어체크, 높이 2.35 m 이상이면 상부 트랜섬. 외부 샴페인 헤어라인 문선(`door_trim`)·인방·리빌. 유리는 짝당 1장 WindowSet(분할·겹침 없음, 기존 검증 창호 방식).
- `add_steel_door`: 도장 다크 문틀 + 회색 철판 문짝 + 패널·킥플레이트·레버·도어클로저 + 경첩 3개 + 문선·인방. `surface=True` 는 옥탑 표면형. `add_rooftop_door` 는 문턱+표면형 문+빗물막이.
- A01: 공동현관(코어 좌측면)·후면 보조문·옥탑문을 새 헬퍼로 교체. 벽부 현관등은 문선 인방과 겹쳐 제거(천장 LED 가 대신). main 16,832→17,248.

### B01 출입구 이동 (사용자 11/24 "출입구가 너무 길어 보인다, 뒤로 옮겨 주차장과 맞추자")
- 정면에서 후면 실까지 8 m 이어지던 흑화강석 현관 코어 박스와 정면 돌출 캐노피(0.65 m)를 없앴다. 상층 좌측 계단실 유리 띠·외관·재질은 그대로.
- 1층 코어 자리는 기둥 2열(x=-2.85, -0.95)이 받치는 폭 1.4 m 보행 통로가 되고, 공동현관(양개 유리문 1.44 m)은 통로 끝 주차 후면 벽 y=8.0(카스토퍼 6.9~7.08 바로 뒤)에 둔다. 정면 돌출 0.
- 인터폰·우편함은 현관 양옆 후면 벽, 남색 번호판은 도로 쪽 통로 기둥 정면, 천장 LED 3개를 통로에. 보조문은 후면실 우측 벽(측면 마당)으로 옮겼다.
- main 20,768→21,116, LOD1 4,688(22%), LOD2 218+창148=366.

### C01 `SintanjinVillaC01_L1_2x3` (브리프 프리셋 C, 새 로드뷰 없음 → 브리프 집계·수치 기반 대표형)
- 흰 미장(206,204,200) 5층(필로티+주거 4개 층), 12.4×12.4 m. 정면 폭 3.0 m·깊이 0.60 m 수직 돌출창 매스 2열(옆면·밑면 닫힘, 층별 화강석 창대 띠), 확장형 창 2.3×1.75 m + 스텐 난간, 다크 알루미늄 창틀, 계단형 파라펫, 우측면 후면 계단실 수직 유리(층별 점등), 옥탑·물탱크.
- 필로티 기둥 5열×2, 주차 3면 + 우측 보행 통로, 공동현관은 통로 끝 후면 벽(B01 기준과 동일), 보조문은 후면실 좌측 벽.
- main 26,562, LOD1 6,238(23%), LOD2 208+창200=408.

### D01 `SintanjinVillaD01_L1_3x3` (브리프 프리셋 D)
- 14.0×12.5 m, 1층 근린상가 층고 3.5 m + 2~4층 고동 벽돌(142,118,104), 연베이지 미장(196,184,168) 정면 모서리 기둥·파라펫·중앙 박공(4.4×1.2 m, 경사 갓돌). 정면 중앙 계단실 수직 유리.
- 상가 2칸: 알루미늄 3분할 쇼윈도 + 트랜섬(2.10 m) + 양개 유리문(트랜섬 포함), 화강석 기단 0.35 m·간판 띠·처마 띠. 가로 간판 2개(신탄칼국수·덕암컴퓨터, 브리프 4장 가상 예시, 전화 042-000-xxxx)와 세로 돌출 간판(칼국수), HMKMRHD/H2GTRE/H2HDRM. 발광 0.05~0.22 로 약하게(근린상가 01 과발광 피드백).
- 주거 현관은 중앙 1.8 m 폭·1.4 m 깊이 매립형(정면 돌출·캐노피 없음), 우편함·인터폰·천장등. 1층 측면 실외기 4대, 후면 보조문.
- main 17,186, LOD1 4,974(29%), LOD2 142+창200=342.

### 검증 (worktree 에서 빌드 후 주인 폴더에 반영)
- 4종 `agent.py cycle --mode final`: build/geometry/preview/LOD/FBX PASS, COPLANAR 0, WIN_BLOCKED 0, LODCHECK PASS(0/64), `albedo_check.py` 경고 0. `agent.py review` PASS 기록.
- 렌더(주인 폴더 `previews/`): `A01_doors_before/after`, `B01_entrance_before/after`, `B01_roof_door`, `C01_eye_entrance`, `C01_bay_window`, `D01_storefront`, `D01_signs_roof`, `*_full_four`, `*_eye_night`. 키트 렌더러는 직교 투영이라 "눈높이"는 pitch 3~4° 근접 확대로 근사했다(실제 1.6 m 원근 카메라 아님).
- 인게임 Growable 등록·입주·야간·LOD 전환·유리 깜빡임은 미확인. C·D 는 사진 대조 NOT_APPLICABLE(브리프 v 시리즈 원본이 이 PC 에 없음).
