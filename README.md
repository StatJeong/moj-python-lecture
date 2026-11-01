# 파이썬 활용 교정정보 분석 실습

법무연수원 교정AI데이터 활용 실무 과정 강의자료입니다.

강의자료 보기: https://statjeong.github.io/moj-python-lecture/

## 내용

| 장 | 내용 | 실습 노트북 |
|---|---|---|
| 1. 파이썬 기초 | 자료형, 연산자, 리스트, 딕셔너리, 조건문, 반복문 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/01_python_basics.ipynb) |
| 2. 데이터 다루기 | pandas로 읽기, 선택, 필터, 집계, 결측치, 날짜, 병합 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/02_pandas.ipynb) |
| 3. 시각화 | 막대그래프, 히스토그램, 산점도 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/03_visualization.ipynb) |
| 4. 기초통계와 회귀 | 기술통계, 교차표, 평균 비교, 선형·로지스틱 회귀 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/04_statistics.ipynb) |
| 5. AI와 함께 분석하기 | AI에게 요청하기, 받은 코드 검증하기 | [Colab](https://colab.research.google.com/github/StatJeong/moj-python-lecture/blob/main/notebooks/05_ai.ipynb) |

## 폴더 구성

```
moj-python-lecture/
├── _quarto.yml          Quarto 웹사이트 설정
├── index.qmd            강의 소개
├── 01_python_basics.qmd ~ 05_ai.qmd   각 장 원고
├── data/                실습용 가상 데이터 (inmates.csv, facilities.csv)
├── images/              강의용 움짤 (반복문, 병합)
├── notebooks/           Colab 실습 노트북 (qmd에서 자동 생성)
├── tools/               움짤 생성기, 노트북 생성기
└── docs/                렌더링 결과 (GitHub Pages)
```

## 자료 수정 후 다시 만들기

```bash
python tools/make_notebooks.py   # qmd → notebooks/*.ipynb
quarto render                    # qmd → docs/ (웹사이트)
```

반복문 움짤을 새로 만들 때는 예제 코드를 파일로 저장한 뒤 실행합니다.

```bash
python tools/code_stepper.py tools/examples/loop_sum.py images/loop_sum.gif --title "for 반복문: 형기 합계 구하기"
```

## 데이터에 대하여

`data/` 폴더의 데이터는 강의를 위해 만든 가상 데이터이며 실제 수용자, 시설과 관계가 없습니다.
