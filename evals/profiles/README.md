# Astra Extra High 후보 평가

이 프로필은 `gpt-6-astra`와 `xhigh` 설정을 사용하는 별도 후보 평가입니다. 기존 `v0.1.0`의 실행 설정, 원문 결과와 판정을 변경하지 않습니다. `scripts/run_evals.py`의 기본 설정이나 Desktop 검사도 변경하지 않습니다.

## 실행 경로와 증거

`native-collaboration`은 클라우드의 `collaboration.spawn_agent`로 새 하위 에이전트를 만드는 경로를 뜻합니다. Codex Desktop이나 CLI로 기록하지 않습니다. 요청은 `model="gpt-6-astra"`, `reasoning_effort="xhigh"`, `fork_turns="none"`으로 지정합니다. 샘플링은 `runtime_default`입니다.

모델 선택이 포함된 요청과 요청을 수락한 응답을 각각 보존합니다. 요청 수락은 실제 Desktop 버전이나 별도로 제공되지 않은 모델 정보를 확인했다는 뜻이 아닙니다. 제공자가 실행 모델이나 버전을 노출하지 않으면 확인 불가로 기록합니다. 모델 본인이 답변에서 밝힌 이름은 실행 환경 증거로 사용하지 않습니다. 버전이 없는 경로라면 제공자가 버전을 제공하지 않는다는 근거를 함께 보존하며 버전을 만들어 넣지 않습니다. 현재 경로의 수락 사례는 경로 확인용이지 정식 평가 결과가 아닙니다.

실제 실행에 앞서 `preflight`에 요청 원문, 응답 원문, 실행 메타데이터의 파일 경로와 SHA256을 전달합니다. 이 도구는 구조와 해시만 검사하므로 별도 검토자가 원문에서 모델, 추론 수준, 경로를 확인해야 합니다. 실제 모델 확인 근거가 없으면 정식 결과의 확정을 보류합니다. 요청한 설정과 확인한 설정을 구분합니다.

## 준비 명령

승인된 원본 커밋에 이 프로필과 준비 도구만 적용한 별도 체크아웃에서 실행합니다. 아래 폴더는 아직 존재하지 않아야 합니다.

```text
python -X utf8 scripts/prepare_profile_eval.py prepare --work-dir .eval-astra-xhigh-v1
python -X utf8 scripts/prepare_profile_eval.py preflight --evidence runtime-evidence.json
```

`prepare`는 고정된 50개 사례, 스킬과 기존 평가 도구가 원본 커밋과 같은지 검사합니다. 프로필, 실행 절차, 준비 도구와 입력 해시를 포함한 별도 평가 동일성 값을 만듭니다. `prepared_not_started`는 실행 완료가 아닙니다. 실제 실행 시각, 모델 출력과 판정은 만들지 않습니다. 기본 50개와 별도 보충 사례의 결과를 섞지 않습니다.

## 독립 실행과 판정

각 사례의 생성자, 평가자 A, 평가자 B, 필요한 추가 평가자는 모두 `fork_turns="none"`인 새 세션에서 실행합니다. 생성자에게는 스킬과 필수 참고 문서, 사례의 문맥·요청·입력만 제공합니다. 평가자에게는 스킬, 생성자의 대화 이력, 다른 평가자의 결과를 제공하지 않습니다. 생성자와 두 평가자는 사례마다 한 번 실행합니다. 판정이 다를 때만 추가 평가자를 한 번 실행합니다.

기존 `render_generator_prompt`, `render_reviewer_prompt`, `render_adjudicator_prompt`를 사용합니다. 평가자 프롬프트는 생성자의 실제 원문 출력으로 렌더링합니다. 평가 기준은 프롬프트 렌더러와 기존 50개 사례 그대로 유지합니다. 보호 문자열, 항목별 판정, 핵심 실패와 필수 회귀 조건도 유지합니다. 한 사례를 통과했다고 전체를 통과시킬 수 없습니다.

각 실행에는 사례 ID, 역할, 새 context UUID, 제공된 실제 agent ID, 요청 및 응답 시각, 실제 프롬프트 해시, 최초 유효 출력 원문과 해시, 요청 설정, 확인된 실행 설정, 증거 경로를 기록합니다. 서로 다른 역할이나 사례에서 context와 agent ID를 재사용하지 않습니다. 전달 실패와 실제 응답 실패를 구분하며, 품질이나 JSON 형식을 이유로 유효 출력을 재생성하지 않습니다. 출력 없는 전송 오류를 복구할 때에는 기존 규약의 한 번 복구 조건과 근거 기록을 따릅니다.

## 결과의 구분

기존 `run_evals.py aggregate`에 새 설정의 기록을 넣지 않습니다. 이 도구는 구 설정을 엄격히 검사하는 도구입니다. 새 프로필의 실행 기록 검증과 집계는 아래 별도 도구로 수행합니다. 이 문서와 준비 도구만으로 전체 모델 평가가 완료되거나 통과됐다고 보고하지 않습니다. 원본 50개 사례와 결과 파일을 수정하지 않으며, 보충 사례의 2개에서 3개로 바뀐 안내 수량은 운영 문서 정정으로만 처리합니다.

## 독립된 기록 검사와 집계

새 `scripts/aggregate_profile_eval.py`는 새 프로필 전용입니다. 준비 시 집계 도구의 해시도 평가 동일성에 포함합니다. 이전 준비 폴더는 고치지 않고 새 폴더에서 다시 준비합니다. 실행 출력이나 판정은 생성하지 않습니다.

```text
python -X utf8 scripts/aggregate_profile_eval.py --work-dir .eval-astra-xhigh-v1 --output candidate-summary.json
python -X utf8 scripts/aggregate_profile_eval.py --work-dir .eval-astra-xhigh-v1 --audit independent-audit.json --output verified-summary.json
```

각 역할의 최초 원문은 `events.jsonl`에 한 행씩 기록합니다. 필드는 `case_id`, `role`, `attempt`(1), `context_id`(새 UUID), `agent_id`, `evaluation_identity`, `prompt`, `output`, `spawn_request`, `spawn_response`, `provider_attestation`입니다. 마지막 세 필드는 후보 폴더 안에 보관한 JSON 증거의 `path`와 `sha256`입니다. 증거의 원문을 별도로 보존하며, 제공자가 JSON으로 반환하지 않은 기록은 원문과 변환 과정을 독립 검토해야 합니다. 작성자가 만든 설명을 제공자 증거로 바꾸어 기록하지 않습니다.

요청 증거에는 `model`, `reasoning_effort`, `fork_turns`, `prompt`, 응답 증거에는 `agent_id`가 있어야 합니다. 제공자 실행 증거에는 `source=provider`, 실제 `runtime_surface`, `model`, `reasoning_effort`, `sampling`, `fork_turns`, `runtime_version`과 해당 실행의 `case_id`, `role`, `context_id`, `agent_id`, `evaluation_identity`, `prompt_sha256`, `output_sha256`, `first_completed_output=true`, `fresh_context=true`가 필요합니다. 제공자가 이 내용을 확인할 근거를 주지 않았다면 실제 기록을 만들어 채우지 않습니다. 해당 역할의 정식 검증은 차단된 것으로 처리합니다.

생성자 출력 전에 평가하거나 두 평가자의 판정 전에 추가 평가하는 기록, 중복 context나 agent ID, 같은 역할의 두 번째 출력, 변경된 프롬프트나 다른 모델의 증거는 거부합니다. 현 구현은 최초 완료 출력만 지원합니다. 출력 없는 실패의 복구 기록은 기존 허용 조건이 있더라도 이 검사기를 우회하지 않고 별도 지원·검수 후 처리합니다. 평가자 원문은 기존 JSON 판정 형식 그대로 읽고, 항목별 다수결과 핵심 실패 다수결은 기존 함수를 사용합니다. 완전 일치 조건과 기본 묶음별 최소 통과 수를 별도 품질 기준에 반영합니다.

상태는 다음과 같이 구분합니다.

- `prepared`: 역할 출력이 없습니다.
- `partial`: 일부 출력만 있거나 추가 평가를 기다립니다.
- `candidate-error`: 입력·증거·독립성 검사 오류입니다. 품질 실패와 구분합니다.
- `complete`: 50개 판정 집계가 끝났습니다. 제공자 원본 증거의 독립 확인은 별개입니다.
- `verified`: 완전한 집계와 연결된 독립 확인 기록이 있습니다. 품질 통과 여부는 `quality_gate_passed`로 따로 표시합니다. 검증된 실패도 이 상태가 될 수 있습니다.

독립 확인 기록은 `evaluation_identity`, `events_sha256`, `summary_sha256`(정렬한 JSON의 UTF-8 SHA256), 실행 agent와 다른 `reviewer_id`, `provider_receipts_verified=true`, `first_outputs_and_independence_verified=true`, `evidence_source`, `reviewed_at`을 포함합니다. 확인자는 원본 제공자 기록에서 실행 설정과 첫 출력, 역할별 새 대화를 직접 대조해야 합니다. 로컬 JSON과 해시 검사는 제공자 서명 검증이 아니며 기록의 진위를 스스로 입증하지 않습니다. 미제공 메타데이터를 추정하거나 테스트용 가상 증거로 실제 평가를 통과시키지 않습니다.

`verified`에는 위 필드 외에 독립 검토 원문 `independent_review_response`와 제공자가 확인한 검토자 실행 증거 `independent_review_attestation`의 경로 및 해시도 필요합니다. 검토 원문은 검토자 ID, 평가 동일성, 이벤트·집계 해시와 두 확인 판정을 포함합니다. 실행 증거는 `source=provider`, 동일한 `reviewer_id`, 검토 원문 `response_sha256`, `fresh_context=true`, 평가에 사용하지 않은 새 `context_id`를 포함해야 합니다. 확인 플래그만 작성한 로컬 audit 파일은 검증 완료 근거로 인정하지 않습니다. 독립 확인 원문과 실행 근거가 없으면 `complete`에서 멈추며 `verified`로 승격하지 않습니다.
