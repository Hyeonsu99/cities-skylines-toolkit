# CS2 신탄진 IC 기본 에셋 이름 검증

## 어떤 기본 에셋을 실제로 찾을 수 있는가

### Takeaway
설치 게임의 영문·한국어 현지화에서 아래 표시명과 내부 ID를 직접 대조했다. 기본 패키지에서 관련 모델 존재도 확인했다. 현지화·모델의 존재와 실제 배치 성공은 구별해야 한다.

### Cited Findings
로컬 원천: `C:/Program Files (x86)/Steam/steamapps/common/Cities Skylines II/Cities2_Data/Content/Game/Locale.cok` 안 `en-US.loc`, `ko-KR.loc`의 `Assets.NAME[ID]` 키. Locale.cok는 ZIP이며 .loc는 버전 ushort, 3개 BinaryReader 문자열, uint 항목 수, 키·값 BinaryReader 문자열 쌍 구조다. 다음 표의 이름은 모두 이 파일에서 직접 추출했다. 이름 끝 공백은 제거했다.

| 내부 ID / 검색어 | 영문 표시명 | 한국어 표시명 | 권장 용도 |
|---|---|---|---|
| PineTree01 | Pine | 소나무 | 큰 루프 외곽의 주 수목 |
| OakTree01 | Oak | 참나무 | 소나무 사이 넓은 수관 포인트 |
| EU_AlderTree01 | Alder | 오리나무 | 램프 바깥 완충 녹지 |
| EU_PoplarTree01 | Poplar | 포플러 | 외곽에 드문드문 |
| NA_LindenTree01 | Linden | 피나무 | 시내 연결부 가로수 후보 |
| GreenBushWild01 | Wild Green Bush 01 | 야생 나무 덤불 01 | 나무 군락 가장자리 |
| GreenBushWild02 | Wild Green Bush 02 | 야생 나무 덤불 02 | 야생 덤불 01과 교차 사용 |
| GreenBushCity01 | Cultivated Green Bush 01 | 재배 나무 덤불 01 | 오른쪽 삼각 녹지의 낮은 식재 |
| GreenBushCity02 | Cultivated Green Bush 02 | 재배 나무 덤불 02 | 관리된 녹지 테두리 |
| GreenBushCity03 | Cultivated Green Bush 03 | 재배 나무 덤불 03 | 덤불 변주 |
| FlowerBushCity01 | Cultivated Flower Bush 01 | 재배 꽃 덤불 01 | 진입부 소량 강조 |
| FlowerBushCity02 | Cultivated Flower Bush 02 | 재배 꽃 덤불 02 | 꽃 덤불 01 대안 |
| FlowerBushCity03 | Cultivated Flower Bush 03 | 재배 꽃 덤불 03 | 꽃 덤불 01 대안 |
| Grass Surface 01 | Grass Surface 01 | 초원지역 01 | 잔디 면 후보 |
| Grass Surface 02 | Grass Surface 02 | 초원지역 02 | 잔디 면 변주 후보 |
| Concrete Surface 01 | Concrete Surface 01 | 콘크리트 지역 01 | 작은 관리용 포장면 후보 |
| Concrete Surface 02 | Concrete Surface 02 | 콘크리트 지역 02 | 포장면 변주 후보 |
| Rock01 / Rock02 | Rock | 암석 | 식재 안쪽 소량, 내부 번호로 구분 |
| ConcreteBarrier01 | Concrete Barrier 1 | 콘크리트 벽 1 | 도로 소품 후보 |
| SafetyBarrier01 | Safety Barrier 01 | 안전 장벽 01 | 도로 소품 후보; 형상 미검증 |
| StreetlightSingle01 | Streetlight Single 01 | 단일 가로등 01 | 톨게이트 주변 후보 |
| StreetlightDouble01 | Streetlight Double 01 | 양방향 가로등 01 | 넓은 진입부 후보 |
| Sound Barrier | Sound Barrier | 방음벽 | 도로 서비스 기능; 민가 방향 검토 |

기본 패키지 모델: `Content/Game/Blob.cok` ZIP 목록에 `PineTreeElderly01_*`, `OakTreeElderly01_*`, `GreenBushWildChild02_*`, `GreenBushCity01_*`, `SafetyBarrier01_Geom_*`, `ConcreteBarrier01_Geom_*`, `StreetlightSingle01_Geom_*` 등이 있다. `Blob_Environment.cok`에도 Pine/Oak 모델 업데이트가 있다. DLC·구독 에셋 폴더에서 추출한 이름이 아니다.

설치 버전 기록: `C:/Users/johye/AppData/LocalLow/Colossal Order/Cities Skylines II/version` = `1.6.4f1 (1097.158a) [6360.18886]`. 실행 중 버전 UI는 미확인.

### Inferences
- 핵심은 소나무 + 참나무 + 야생 나무 덤불 01/02 + 재배 나무 덤불 01/02 정도면 충분하다.
- 큰 왼쪽 루프에 2~3개의 불규칙한 군락, 중앙 잔디는 비우기. 작은 왼쪽 루프는 더 성기게. 오른쪽 합류부는 낮은 덤불만 두기.
- CS2 기본 Pine 모델을 한국 도로변 상록수 분위기의 대용으로 쓰는 제안이다. 실제 신탄진 IC 식생 종이나 조경 배치를 재현했다고 주장하면 안 된다.

### Gaps
- Prefab의 DLC Required 컴포넌트 및 런타임 메뉴 노출 플래그는 직접 읽지 않았다. 오래된 기본 수목·덤불과 소품의 base 분류는 높은 신뢰도이나 각 소품의 현재 메뉴 노출까지 단정하지 말 것.
- 실제 배치와 성체 미리보기는 하지 않았다. Rock01/02 크기, SafetyBarrier01 형상, Grass Surface 01/02 색 차이는 미검증.

## 기본 에셋을 배치할 때 무엇이 필요한가

### Takeaway
나무·덤불을 먼저 일반 조경 메뉴에서 사용하면 된다. 기본 파일 속 소품·표면 전체가 같은 메뉴에 노출된다고 가정하지 말고, 찾기 어려운 경우 Find It을 검색 수단으로 안내한다. Find It은 검색·배치 보조 코드 모드다.

### Cited Findings
- 개발사 조경 설명은 Landscaping의 Vegetation 메뉴에서 나무를 심으며 시간이 흐르면 성장한다고 설명한다. [개발사 City Services 설명을 포함한 Steam 발표](https://store.steampowered.com/news/posts/?enddate=1689602510&feed=steam_community_announcements)
- 개발사 Decorations Patch 안내는 기본 게임에 Decorations Menu를 추가했다고 설명한다. 따라서 기본 소품 전체를 개발자 모드 전용이라고 설명하면 부정확하다. [공식 Dev Diary](https://www.paradoxinteractive.com/games/cities-skylines-ii/news/decorations-patch)
- Find It 공식 페이지는 게임 내 에셋 검색·분류, Ctrl+F 검색 패널, Ctrl+P Picker, Tree Controller·Line Tool 옵션 호환을 안내한다. 현재 페이지 표기 1.5.8 / 대상 게임 1.6.*, 요구사항 Unified Icon Library, Asset Icon Library. [Find It 공식 모드 페이지](https://mods.paradoxplaza.com/mods/77240/Windows)
- Beach Properties는 기본 게임에 편입됐다. 과거 DLC라는 이유만으로 유료라고 간주하면 안 된다. 이 제안에는 야자수가 필요 없다. [공식 공지](https://www.paradoxinteractive.com/games/cities-skylines-ii/news/beach-properties-now-in-the-base-game)

### Inferences
- 기본 조경의 소나무·참나무·덤불로 먼저 완성하고, 표면·소품은 옵션으로 두는 구성이 적합하다.
- 일반 조경에서 원하는 기본 오브젝트가 안 보이면 Find It에서 한국어 이름 또는 내부 ID로 검색할 수 있다. 실제 설치·활성화 여부는 미확인이다.

### Gaps
- 현 버전 surface 직접 배치 메뉴 여부는 실제 UI로 확인하지 않았다. Grass Surface가 반드시 모드 필요 또는 일반 메뉴에 반드시 존재한다고 단정하지 말 것.
- Wiki Landscaping은 401, 공식 포럼 본문은 JS challenge로 완전 열람하지 못했다.
