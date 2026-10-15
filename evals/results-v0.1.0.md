# v0.1.0 평가 결과

평가 시작: 2026-10-15T10:41:20Z

평가 대상 SHA256: 8489CF13D1EE9FA936AA6C76B9D9B66CEEB87D26A0D2ACC1AA990361AE26B63E

GitHub CLI: 2.97.0

## 실행 환경

| 역할 | 에이전트 | 모델 | 추론 설정 | 샘플링 | 실행 환경 | 버전 | 실행 횟수 | 재시도 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| generator | codex | gpt-5.6-sol | high | runtime_default | codex-desktop | 26.1007.9446.0 | 50 | 0 |
| reviewer-a | codex | gpt-5.6-sol | high | runtime_default | codex-desktop | 26.1007.9446.0 | 50 | 0 |
| reviewer-b | codex | gpt-5.6-sol | high | runtime_default | codex-desktop | 26.1007.9446.0 | 50 | 0 |
| adjudicator | codex | gpt-5.6-sol | high | runtime_default | codex-desktop | 26.1007.9446.0 | 1 | 0 |

## 결과

| 평가 묶음 | 전체 | 통과 | 실패 |
| --- | --- | --- | --- |
| core | 24 | 23 | 1 |
| approved-copy | 2 | 2 | 0 |
| punctuation | 7 | 7 | 0 |
| context | 10 | 10 | 0 |
| pragmatics | 7 | 7 | 0 |
| 전체 | 50 | 49 | 1 |

평가자 간 판정 불일치: 1개 사례

추가 평가자 판정: 1개 사례

핵심 실패: 0개 사례

## 한계

모델 출력과 판정은 별도로 수집한 뒤 집계했습니다. 이 도구가 모델 평가를 자동 실행한 결과는 아닙니다.
평가는 기록된 모델과 설정에서 사례마다 한 번 생성한 출력에 한정되며 다른 모델의 품질을 뜻하지 않습니다.
집계 도구는 저장된 실행 정보와 판정의 일관성을 검사하며 실제 실행 여부를 외부 시스템과 대조하지 않습니다.
사례 통과 여부는 다수결 판정입니다. 완전 일치 기준과 배포 조건은 최종 검증 도구에서 별도로 검사합니다.

## 재현

    python -X utf8 scripts/run_evals.py prepare --version v0.1.0 --work-dir .eval-work

이전 대화가 없는 새 실행에서 출력과 판정을 수집하고 실행 정보를 기록한 뒤 다음 명령을 실행합니다.

    python -X utf8 scripts/run_evals.py aggregate --version v0.1.0 --work-dir .eval-work
    python -X utf8 scripts/run_evals.py check --version v0.1.0 --work-dir .eval-work
    python -X utf8 scripts/run_evals.py verify-tracked --version v0.1.0
