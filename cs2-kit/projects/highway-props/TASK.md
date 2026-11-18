# TASK.md - 한국 고속도로 소품 세트 (highway-props)

building: 한국 고속도로 소품 세트 (방음벽 2종, 녹색 안내표지 2종, W빔 가드레일, 콘크리트 중앙분리대) — 신탄진 일대 맵에 반복 배치
name: NoiseWallClear / NoiseWallMetal / SignGantry / SignSideDistance / GuardrailWBeam / MedianBarrierConcrete (밑줄 금지 규칙 준수)
photos: 없음 (photo_mode NOT_APPLICABLE — 국내 기준·일반 실사진 지식으로 치수 결정, shape_notes.md 에 출처)
glb: 없음
complex_name: 없음
region: 대전 대덕구 신탄진 일대 (경부고속도로 신탄진IC 주변)
built_year: 해당 없음
floors: 해당 없음 (소품)
refuge_floor: 없음
size_m: 소품별로 shape_notes.md 표 참고
louver: 해당 없음
railing: 해당 없음
balcony: 해당 없음
curtainwall: 없음
window_type: 없음 (창 없음 — kit 의 "win OBJ missing" 경고는 소품이라 해당 없음)
known_facts: |
  - 우선순위 1 방음벽: 투명(PC) 패널형 + 불투명 금속 흡음형, H-150 지주, 콘크리트 기초, 지주 간격 2.0 m 모듈.
  - 우선순위 2 녹색 안내표지: 문형(갠트리) 1종 + 측주식 1종, 녹색 바탕·흰 글자·국문/영문 병기, 지명 신탄진·대전·청주(+서울).
  - 우선순위 3 W빔 가드레일(4 m 모듈) + 1.27 m 콘크리트 중앙분리대(4 m 모듈).
wishes: 반복 배치용 저폴리 + LOD1/LOD2. 생성기 1개 = 소품 1개, 공용 코드는 hwprops_common.py.
blender_path: C:\Program Files\Blender Foundation\Blender 5.2\blender.exe

## 생성기

| 소품 | 생성기 | 출력 |
|---|---|---|
| 투명 방음벽 | `noise_wall_clear_cs2.py` | `output/NoiseWallClear_L1_1x1` (+ `_Gls`) |
| 금속 흡음 방음벽 | `noise_wall_metal_cs2.py` | `output/NoiseWallMetal_L1_1x1` |
| 문형 안내표지 | `sign_gantry_cs2.py` | `output/SignGantry_L1_3x1` |
| 측주식 이정표 | `sign_side_cs2.py` | `output/SignSideDistance_L1_1x1` |
| W빔 가드레일 | `guardrail_wbeam_cs2.py` | `output/GuardrailWBeam_L1_1x1` |
| 콘크리트 중앙분리대 | `median_barrier_cs2.py` | `output/MedianBarrierConcrete_L1_1x1` |

`highway_props_cs2.py` 는 위 6개를 차례로 final 빌드하는 편의 스크립트다.
게이트: `python tools/agent.py cycle --project highway-props --generator <생성기> --mode final --label final --json`
