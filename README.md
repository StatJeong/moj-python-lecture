# 파이썬 활용 교정정보 분석 실습

법무연수원 교정AI데이터 활용 실무 과정 강의자료입니다.

강의자료 보기: https://statjeong.github.io/moj-python-lecture/

## 내용

| 장 | 내용 | 실습 노트북 |
|---|---|---|
| 1. 파이썬 기초 | 자료형, 연산자, 리스트, 딕셔너리, 반복문, 함수 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/01_python_basics.ipynb) |
| 2. 데이터 다루기 | pandas로 읽기, 선택, 필터, 집계, 결측치, 날짜, 병합, 저장 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/02_pandas.ipynb) |
| 3. 시각화 | 그래프의 구조(층 쌓기), 막대그래프, 산점도, seaborn 히트맵 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/03_visualization.ipynb) |
| 4. 기초통계와 회귀 | 기술통계, 교차표, 평균 비교, 선형·로지스틱 회귀(모형식, 최소제곱법, 오즈비) | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/04_statistics.ipynb) |
| 5. AI와 함께 분석하기 | AI에게 요청하기, 함수로 받기, 받은 코드 검증하기 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/05_ai.ipynb) |
| 6. 교정통계연보 실습 | 수용률 35년 추이, 교정공무원 1인당 수용인원, 죄명별 구성 변화, 고령 수형자, seaborn 히트맵, 연보 도표 따라 그리기 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/06_yearbook.ipynb) |

## 폴더 구성

```
moj-python-lecture/
├── _quarto.yml          Quarto 웹사이트 설정
├── index.qmd            강의 소개
├── 01_python_basics.qmd ~ 06_yearbook.qmd   각 장 원고
├── data/                실습용 가상 데이터 (inmates.csv, facilities.csv)
│   └── yearbook/        2026 교정통계연보 표 (실제 공개 통계)
├── images/              강의용 움짤 (반복문, 함수, 병합)
├── notebooks/           Colab 실습 노트북 (qmd에서 자동 생성)
├── tools/               움짤 생성기, 노트북 생성기
└── docs/                렌더링 결과 (GitHub Pages)
```

## 자료 수정 후 다시 만들기

```bash
python tools/make_notebooks.py   # qmd → notebooks/*.ipynb
quarto render                    # qmd → docs/ (웹사이트)
```

3장의 그래프 구조 그림과 층 쌓기 움짤은 `python tools/make_structure_figs.py`로 다시 만듭니다.
4장의 t분포, 잔차, 로지스틱 비교, 시그모이드 그림은 `python tools/make_stats_figs.py`로 다시 만듭니다.
5장의 흐름 그림은 `python tools/make_ai_figs.py`로 다시 만듭니다.

반복문 움짤을 새로 만들 때는 예제 코드를 파일로 저장한 뒤 실행합니다.

```bash
python tools/code_stepper.py tools/examples/loop_sum.py images/loop_sum.gif --title "for 반복문: 형기 합계 구하기"
```

## 데이터에 대하여

`data/` 폴더의 inmates.csv, facilities.csv는 강의를 위해 만든 가상 데이터이며 실제 수용자, 시설과 관계가 없습니다.

`data/yearbook/` 폴더의 자료는 『2026 교정통계연보』(법무부 교정본부, 2026) 38쪽, 108쪽, 110쪽, 120~121쪽에서 전재하였습니다. 표를 옮긴 스크립트는 `tools/yearbook_tables.py`입니다.
