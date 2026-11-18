# 한국형 저밀도 주거 에셋팩 — M1.5 품질 패스

building: 한국 구도심 70s/80s/90s 2층 주택 대표와 시드 비교
name: KoreanHouseA01
photos: photos/SOURCES.md 선정 24장, 원본 사진은 로컬 전용
glb:
complex_name:
region: 대전 석봉·신탄진·덕암·관평·송강·전민 권역
built_year: 특정 주소·연도 재현 아님
floors: 2
refuge_floor:
size_m: 담장 포함 폭 12.4~13.6 m, 깊이 12.7~13.9 m, 높이 7.58~8.08 m, lot 2x2 (추정)
louver: 옥상 실외기 전면 디테일은 추정
railing: 외부 철계단·발코니 금속 난간, 1층 방범창
balcony: 난간형 / 알루미늄 샷시 확장형 / 없음
curtainwall: 없음
window_type: 미서기 2분할, 유리 0.20m 후퇴
known_facts: A/B/C 현지 거리뷰, D는 지역 밖 공개 사진 보조 근거. 특정 주소 재현 아님.
wishes: 본체 마감 4종 이상·흰 담·석재 문주·생활 소품·기와 눈썹처마·ㄱ자·발코니·셔터 가게, 시대별 대표 final PASS와 12시드 비교. 녹색은 옥상 수평면뿐. 화분·화단 틀·흙·식생 메시 금지. M2는 사용자 인게임 승인 뒤.
blender_path: C:\Program Files\Blender Foundation\Blender 5.2\blender.exe

## 구조와 범위

- `python tools/project.py new korean-lowrise --template generic`으로 생성.
- `house_core.py` + 13줄 `korean_lowrise_cs2.py` 프리셋 래퍼.
- 키트 `volume_prism`, `WindowSet`, `feature_roof_equipment`, `export_asset` 사용.
- `house_70s_cs2.py`, `house_80s_cs2.py`, `house_90s_cs2.py` 대표 프리셋 및 기존 A01 갱신.
- 닫힌 셔터는 키트 axbox/paint로 제작한다. shopfront helper의 유리 점포, 모임·박공·필로티 B형은 별도 범위다.
- `seeded(era, seed)`와 `variety.py`: 시대당 12시드의 OBJ 기하 검사·비교 렌더, 대표 3종만 별도 final. `work/M15_REPORT.md` 참고.
- `cs2kit.py`, `tools/`, 다른 프로젝트는 수정하지 않는다.
