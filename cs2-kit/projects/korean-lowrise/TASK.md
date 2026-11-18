# 한국형 저밀도 주거 에셋팩 — M0+M1

building: 한국 구도심 2층 붉은 벽돌 양옥 유형 시제품
name: KoreanHouseA01
photos: photos/SOURCES.md 선정 24장, 원본 사진은 로컬 전용
glb:
complex_name:
region: 대전 석봉·신탄진·덕암·관평·송강·전민 권역
built_year: 특정 주소·연도 재현 아님
floors: 2
refuge_floor:
size_m: 담장 포함 13.6 x 13.5 x 8.28 m, lot 2x2 (추정)
louver: 옥상 실외기 전면 디테일은 추정
railing: 외부 철계단 금속 난간
balcony: 없음
curtainwall: 없음
window_type: 미서기 2분할, 유리 0.20m 후퇴
known_facts: A/B/C 현지 거리뷰, D는 지역 밖 공개 사진 보조 근거. 특정 주소 재현 아님.
wishes: 녹색 방수 옥상·물탱크·실외기·담장·대문·외부계단. 화분·화단 틀·흙·식생 메시 금지. M1 final과 이미지 리뷰 후 정지, M2는 사용자 인게임 승인 뒤.
blender_path: C:\Program Files\Blender Foundation\Blender 5.2\blender.exe

## 구조와 범위

- `python tools/project.py new korean-lowrise --template generic`으로 생성.
- `house_core.py` + 13줄 `korean_lowrise_cs2.py` 프리셋 래퍼.
- 키트 `volume_prism`, `WindowSet`, `feature_roof_equipment`, `export_asset` 사용.
- M1은 A형 주택 1종만. 가게는 M2에서 `feature_shopfront`를 사용하고 모임·박공·필로티는 B형 단계에서 구현한다.
- 대지·층수·벽색·옥상색·외부계단·물탱크·담장은 현재 코어 매개변수다. 아직 구현하지 않은 변형을 지원한다고 표기하지 않는다.
- `cs2kit.py`, `tools/`, 다른 프로젝트는 수정하지 않는다.
