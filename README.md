<!--# IndustrialSafetyAiCctv -->
<!--Inteldx team project 01 - Team TOST(Team Of Safe T) -->
<!-- 이하 부분을 위에 내용으로 양식 맞춰 채우기 -->
# Project Industrial Safety A.I CCTV(ISAC)
## Team Name : TOST(Team of Safe T)

* 산업 현장에서 발생할 수 있는 다양한 위험 상황을 실시간으로 탐지하고, 구조 활동을 지원하는 감시 시스템을 구축하는 프로그램 개발 프로젝트  
  
**주요 기능**  
  
**1. 위험 상황 탐지 및 구호 지원 기능**  

* AI 모델을 사용하여 작업자 기절 등의 위험 상황 감지  

* Pose Estimation 기술을 사용하여 인근 구조자의 구조 신호를 실시간 감지  

* 쓰러진 작업자의 헬멧 색상을 기반으로 미리 등록된 건강 정보를 불러오며, 이를 통해 초기 대응 및 구급 활동에 필요한 정보 제공  

**2. 위험 발생 요소 모니터링**  
  
* 특정 위험 작업 상황에서 소화기 등 필수 오브젝트의 존재여부를 판단하는 기능 제공  

* 영상 분석을 통해 화재 및 연기를 실시간으로 탐지하고, 재난 상황을 신속하게 파악  

**3. 위험 요소 통합 관리 지원**  

* 통제실 및 관리자에게 탐지된 정보 실시간 전달 및 대응 촉구  

## High Level Design

* (프로젝트 아키텍쳐 기술, 전반적인 diagram 으로 설명을 권장)

## Clone code

* (각 팀에서 프로젝트를 위해 생성한 repository에 대한 code clone 방법에 대해서 기술)

```shell
git clone https://github.com/xxx/yyy/zzz
```

## Prerequite

* (프로잭트를 실행하기 위해 필요한 dependencies 및 configuration들이 있다면, 설치 및 설정 방법에 대해 기술)

```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Steps to build

* (프로젝트를 실행을 위해 빌드 절차 기술)

```shell
cd ~/xxxx
source .venv/bin/activate

make
make install
```

## Steps to run

* (프로젝트 실행방법에 대해서 기술, 특별한 사용방법이 있다면 같이 기술)

```shell
cd ~/xxxx
source .venv/bin/activate

cd /path/to/repo/xxx/
python demo.py -i xxx -m yyy -d zzz
```

## Output

* (프로젝트 실행 화면 캡쳐)

![./result.jpg](./result.jpg)

## Appendix

* (참고 자료 및 알아두어야할 사항들 기술)
