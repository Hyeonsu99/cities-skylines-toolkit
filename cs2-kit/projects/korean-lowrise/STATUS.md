# 한국형 저밀도 주거 — M1.5 완료

2026-11-18 사용자 승인 품질 패스 완료. M2는 인게임 확인·사용자 승인 대기.

| 에셋 | final | main / LOD1 / LOD2 tris (Win 별도) |
|---|---|---|
| KoreanHouseA70s01_L1_2x2 | PASS | 5032 / 1740 / 410 (+56씩) |
| KoreanHouseA80s01_L1_2x2 | PASS | 4036 / 1510 / 364 (+44씩) |
| KoreanHouseA90s01_L1_2x2 | PASS | 4652 / 1392 / 318 (+48씩) |
| KoreanHouseA01_L1_2x2 기존 경로 갱신 | PASS | 4484 / 1512 / 326 (+56씩) |

각 `output/<에셋>/_check/gate.json`의 build/geometry/preview/lod/fbx/visual_review PASS, errors/warnings 없음.
photo/tiles는 유형 합성으로 NOT_APPLICABLE이며 사진 정량 비교 PASS를 뜻하지 않는다.

36시드 셀프 검사·키트 기하 검사 PASS. 시트: `work/variety_70s.png`, `variety_80s.png`, `variety_90s.png`.
동일 시대의 2층 골격·옥탑에서 반복감은 남음. 판정과 세부 구현·추정·검증은 `work/M15_REPORT.md`.
텍스처 2048/2048/512, `_Gls` 없음, 식생·화분·화단 틀·흙면 메시 없음.

가져오기는 반드시 `output/<에셋이름>` 폴더만 선택. 구역 성장·Mixed 지원·야간·다량 배치 FPS·LOD 전환·서브오브젝트 축은 미확인.
푸시하지 않음.
