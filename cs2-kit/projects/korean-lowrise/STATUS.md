# 한국형 저밀도 주거 진행 상태

## 현재 단계

M0 조사 완료, M1 A형 1종 final PASS + 낮·야간 프리뷰 이미지 리뷰 PASS (2026-11-18).
M2는 사용자 인게임 승인 전 정지.

## 생성기

`korean_lowrise_cs2.py` → `house_core.PRESETS["a01"]` → `KoreanHouseA01_L1_2x2`.

## 검증

권위: `output/KoreanHouseA01_L1_2x2/_check/gate.json`.
build / geometry / preview / lod / fbx / visual_review = PASS.
photo / tiles = NOT_APPLICABLE (특정 주소 복제가 아닌 유형 합성, 자동 사진 비교 PASS 아님).
main/LOD1/LOD2 = 3096/1286/422 tris, 창 포함 3152/1342/478.
텍스처 = 2048/2048/512, 5종×3단계 = 15 PNG. `_Gls` 없음.

## 다음 행동

`output/KoreanHouseA01_L1_2x2` 폴더만 CS2 에셋 가져오기에서 선택.
저밀도 2×2 성장·입주, 야간·색 변주·창 떨림, 수백 채 프레임·메모리·LOD 전환을 사용자가 확인.
M2 승인 후 A형 4~6종+B형 4~6종. Mixed 등록·uzacha 호환 미확인.
자세한 추정치·근거·한계는 `shape_notes.md`, 결과는 `work/M1_REPORT.md`.
