# SintanjinTollgate — 경부고속도로 신탄진IC 영업소 (톨게이트)

- **project**: `sintanjin-tollgate`
- **asset_name**: `SintanjinTollgate_L1_6x4`
- **category**: Landmark / Highway Toll Plaza (`Service / Road-Straddling Canopy`)
- **location**: 대전광역시 대덕구 덕암로 207 (경부고속도로 신탄진IC, `36.43942°N, 127.42217°E`, 방위각 `276.6° / -6.6°`)
- **lot**: `6 x 4` (`48 m × 32 m` 존 범위 내 실폭 `40.6 m × 28.4 m`, `front_yard=1.5`)
- **blender_path**: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- **photo_mode**: `NOT_APPLICABLE` (개방형 차선 관통 캐노피·곡선 아치·부스 복합 구조물; 15장 실사 다각도 직접 대조)

## Reference Evidence (`photos/`)

- `sat_tollgate_z19.png`: Esri World Imagery z19 정사 위성 (`0.2402 m/px`, 비대칭 아치 투영·차선 수·부속건물 배제 경계 확인)
- `west_far_look_e.png`, `west_near_look_e.png`, `west_close_booths.png`, `west_hipass_close.png`: 서측(고속도로 본선 진입·진출부) 원·근·접사 실사
- `east_far_look_w.png`, `east_near_look_w.png`, `east_lane2_hipass.png`, `east_sw_look_nw.png`: 동측(덕암로 시내측) 장대 동측 아치(`E2/E3`)·단축 아치(`E1`)·오렌지/실버 갠트리 실사
- `mid_south_look_n.png`, `mid_south_look_nw.png`, `mid_north_look_s.png`: 남북 횡단 뷰·지하통로 초록 돔·중앙 콘크리트 교각·V자 브레이싱 실사
- `under_canopy_look_n.png`, `under_canopy_look_s.png`, `under_canopy_look_e.png`: 캐노피 하부 암갈색 리브 천장·LED 등기구·부스 상세

## Architectural & Geometry Specification

1. **7-Lane + 6-Island + 2-Curb Cross-Section (`X ∈ [-20.30, +20.30]` = `40.60 m`)**
   - `z = 0.0` 개방 주행 차선(도로 관통 허용), 중앙 아일랜드(`z = 0.00..0.56`, 하단 로얄블루 연석 + 상단 백색 콘크리트 + 테이퍼 불노즈 + 북측 외곽 W-빔 가드레일·1차선 노란색 U자 보호가드).
   - 북측 화물 차선(1) + 하이패스(2) + TCS 유인(3,4,5) + 하이패스(6,7) 구성.
2. **Main Central Canopy Deck (`x ∈ [-15.30, +16.30]`, `y ∈ [-5.70, +5.70]`, `z = 5.18..6.62 m`)**
   - 외향 경사 사다리꼴 스카이블루 파시아(`#2a86c2`) + 슬림 백색 코핑 테두리(`z = 6.62..6.72`) + 청록색 스탠딩심 지붕 + 암갈색 골강판 천장(`z = 5.18`) + 슬림 이열 LED 조명등 + 1차선 1신호 차로제어 신호박스(`Red X` on Lane 3, `Green ↓` on Lanes 4,5 및 각 갠트리).
   - 옥상 대형 양면 간판(본체 중앙 정렬): 좌측 `신탄진`(`-6.40..+0.10`) + 우측 `Sintanjin`(`+0.60..+7.10`, `z = 7.12..9.02`) 및 피뢰/3색 풍향계 마스트 3본(`z = 9.02..10.22`).
3. **Asymmetric Polycarbonate Arch Extensions (`Closed Double-Skin Shells`)**
   - 북측 1차선 `Wing 0`: `x ∈ [-19.80, -15.48]`, 서측 캔틸레버(`y ∈ [-10.30, -5.74]`) + 본체·동측 낮은 베이(`y ∈ [-5.68, +8.58]`).
   - 서측 캔틸레버 아치(`y ∈ [-10.30, -5.72]`): `W1 (Lanes 2+3)`, `W2 (Lanes 4+5)`, `W3 (Lanes 6+7)` (`y = -5.70` 지주 및 전방 사재 지지).
   - 동측 비대칭 아치(`+Y`): 2차선 개방, 단축 `E1 (Lane 3, y ∈ [+5.72, +8.60])`, 장대 `E2 (Lanes 4+5, y ∈ [+5.72, +14.20])`, 장대 `E3 (Lanes 6+7, y ∈ [+5.72, +14.20])`.
   - 모든 아치 외피·트러스 리브·배수거터는 폐합 솔리드(`0.06 m` 두께)로 구성해 64뷰 `lod_check` 백페이스 홀 0%(`bad_views 0/64`) 달성.
4. **Toll Booths (4ea), Pedestrian Subway Domes (3ea), Overhead Portals (3ea)**
   - 부스 4동(아일랜드 1~4): 오렌지 상·하단 띠 + 실버 알루미늄 중앙 패널 + `WindowSet` 개방면 유리 (`_Gls` 미사용).
   - 아일랜드 2,3,4 서측 지하통로 초록 아치형 돔 3동.
   - 서측 출구 라임그린 2차선 갠트리(`y = -13.6`, Lanes 6+7), 동측 입구 실버 1차선 갠트리(`y = +12.0`, Lane 2), 동측 입구 오렌지 화물 1차선 갠트리(`y = +12.8`, Lane 1).

## Scope Note

- 인접 벽돌 관리동(`OSM WAY 744238937`, `38.14 m × 12.06 m`) 및 동측 직원 주차장 카포트·북측 창고는 CS2 곡선 IC 램프 배치 호환성 및 `6x4` 롯트 정합을 위해 단일 영업소 캐노피 본체에서 분리(추후 별도 소품/부속동 제작 가능).
