# natural-korean-writing

원래 의미를 그대로 유지하면서 번역투와 어색한 표현을 글의 목적과 독자에 맞게 다듬을 수 있는 자연스러운 한국어 스킬입니다.

[한국어](README.md) | [English](README.en.md)

[Claude Code 설치](#claude-code) | [Codex 설치](#codex) | [Claude 웹과 앱 설치](#claude-웹과-데스크톱-앱) | [바로 써 볼 요청문](#사용법)

## 교정 예시

고치기 전

```text
본 기능을 통해 사용자는 작성한 내용을 보다 편리하게 확인하는 것이 가능합니다.
```

고친 뒤

```text
이 기능을 사용하면 작성한 내용을 더 편리하게 확인할 수 있습니다.
```

뜻은 유지하면서 불필요한 명사화와 번역투를 줄였습니다.

### 상황에 따른 표현

같은 요청도 상대가 보고 듣는 상황에 맞게 작성합니다. 아래는 서류 봉투를 보관함에 넣어 달라는 가상의 요청입니다.

| 상대의 상황 | 요청 문장 |
| --- | --- |
| 직원 옆에서 직원이 가리키는 보관함을 보고 있습니다. | 서류 봉투를 여기에 넣어 주세요. |
| 다른 건물에서 전화를 받으며 보관함의 위치를 모릅니다. | 서류 봉투를 서울 본사 1층 로비 안내 데스크 옆의 파란 보관함에 넣어 주세요. |

대면 상황에서는 함께 보는 대상을 짧게 가리키고, 전화에서는 보관함을 찾는 데 필요한 위치를 설명합니다. 요청하는 행동은 바꾸지 않습니다.

## 작성 기준

한국어 초안 작성, 문장 교정, 검토에 사용할 수 있습니다.

1. 사실, 수치, 담당 범위, 의도와 약속을 보존합니다. 사용자가 확정한 문구와 코드, 경로, URL, 기술 식별자는 임의로 바꾸지 않습니다.
2. 누가 누구에게 언제 어디서 말하는지, 어떤 목적으로 전달하는지에 맞춰 말투와 설명의 양을 조절합니다. 편한 대화를 일괄적으로 존댓말로 바꾸지 않습니다.
3. 조사와 서술어의 호응, 생략한 대상, 정보 순서, 높임 수준을 점검합니다. 불필요한 명사화와 반복을 줄이고, 문장부호는 한국어의 쓰임에 맞게 사용합니다.

구체적인 수정 이유와 보존한 내용은 [교정 예시 12개](examples/before-after.md)에서 확인할 수 있습니다.

[문맥과 독자에 관한 보조 지침](skills/natural-korean-writing/references/context-audience-boundary.md)이 함께 설치됩니다. 한국어를 작성하거나 검토할 때 필수로 적용하며, 별도로 설치하거나 선택할 필요가 없습니다. 화자와 상대의 관계, 전달 시점과 장소, 공개 범위에 맞는 표현을 판단하도록 안내합니다.

## 설치

Claude, Claude Code, Codex에 설치할 수 있습니다. 모든 설치 방법에 같은 `SKILL.md`와 `references/` 폴더가 포함되며, 문맥과 독자에 관한 보조 지침도 함께 사용합니다.

아래 명령의 `@main`은 현재 기본 브랜치의 지침을 설치합니다. Claude 웹에서 확인한 수정본을 포함하며, 공개 릴리스 `v0.1.0`과는 다릅니다. 두 버전의 [검증 범위](#평가와-검증)를 확인해 주세요.

### Claude Code와 Codex

[GitHub CLI 2.90.0 이상](https://github.com/cli/cli/releases/tag/v2.90.0)이 필요합니다. 명령 안내는 GitHub CLI 2.97.0을 기준으로 합니다. `gh skill`은 공개 시험 단계인 public preview 기능이므로 명령과 동작이 바뀔 수 있습니다.

설치한 버전과 `gh skill` 지원 여부를 확인합니다.

```powershell
gh --version
gh skill --help
```

설치 전에 [미리보기 명령](https://cli.github.com/manual/gh_skill_preview)으로 지침을 읽을 수 있습니다.

```powershell
gh skill preview Jiyeong-kor/natural-korean-writing natural-korean-writing@main
```

#### Claude Code

[GitHub CLI를 준비](#claude-code와-codex)한 뒤 실행합니다. 모든 프로젝트에서 사용하려면 사용자 범위에 설치합니다.

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing@main --agent claude-code --scope user
```

현재 프로젝트에서만 사용하려면 사용할 Git 저장소 안에서 실행합니다.

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing@main --agent claude-code --scope project
```

#### Codex

[GitHub CLI를 준비](#claude-code와-codex)한 뒤 실행합니다. 모든 프로젝트에서 사용하려면 사용자 범위에 설치합니다.

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing@main --agent codex --scope user
```

현재 프로젝트에서만 사용하려면 사용할 Git 저장소 안에서 실행합니다.

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing@main --agent codex --scope project
```

#### 고급 사용법: 버전 고정

같은 버전을 계속 사용하려면 릴리스 태그나 커밋 SHA를 지정합니다. `@main`은 실행 시점의 기본 브랜치를 가리키므로 이후 설치에서는 내용이 달라질 수 있습니다. 다음은 공개 릴리스 `v0.1.0`을 설치하는 Claude Code의 예시이며, Codex에서는 `--agent codex`로 바꿉니다. `v0.1.0`에는 이후 `main`에 반영한 지침 수정이 포함되지 않습니다.

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing@v0.1.0 --agent claude-code --scope user
```

버전을 생략하면 최신 릴리스를, 릴리스가 없으면 기본 브랜치의 최신 내용을 설치합니다. 설치 범위와 버전 선택은 [공식 설치 안내](https://cli.github.com/manual/gh_skill_install)에 설명되어 있습니다.

### Claude 웹과 데스크톱 앱

Claude의 코드 실행 기능이 켜져 있어야 합니다. 조직 계정에서는 관리자가 스킬 업로드와 사용을 허용해야 합니다. 설정 위치는 [Claude의 스킬 사용 안내](https://support.claude.com/en/articles/12512180-use-skills-in-claude)를 참고하세요.

1. 이 저장소의 `Code > Download ZIP`에서 파일을 내려받고 압축을 풉니다.
2. 저장소 최상위의 `LICENSE` 파일을 `skills/natural-korean-writing` 폴더 안에 복사한 뒤, 이 폴더 전체를 ZIP으로 압축합니다. ZIP의 최상위에는 `natural-korean-writing/` 폴더가 있고, 그 안에 `SKILL.md`, `references/`, `LICENSE`가 있어야 합니다. 저장소 전체를 그대로 업로드하거나 `SKILL.md`만 압축하지 않습니다.
3. Claude에서 `Customize > Skills`를 열고 `+ > + Create skill > Upload a skill`을 선택합니다.
4. 준비한 ZIP을 업로드하고 목록에서 `natural-korean-writing`을 활성화합니다.

폴더 구성은 [Claude의 사용자 스킬 작성 안내](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)에 설명되어 있습니다.

## 사용법

설치 후 사용하는 도구에 맞춰 스킬을 지정하고, 아래 요청문을 함께 입력해 보세요.

1. Claude Code: `/natural-korean-writing` 뒤에 요청문을 붙입니다. 호출 방식은 [Claude Code의 스킬 안내](https://code.claude.com/docs/en/skills)를 참고하세요.
2. Codex: `$natural-korean-writing` 뒤에 요청문을 붙입니다.
3. Claude 웹과 데스크톱 앱: 스킬을 활성화한 뒤, 요청문 앞에 `natural-korean-writing 스킬을 사용해 주세요.`를 붙입니다.

[교정 예시](examples/before-after.md#8-ui-안내-저장-실패와-재시도)에 있는 가상의 저장 실패 안내문을 사용합니다.

```text
아래 안내문을 원래 의미는 유지하면서 자연스러운 한국어로 고쳐 주세요. 수정한 안내문만 보여 주세요.

문맥: 인터넷 연결이 끊겨 저장에 실패했습니다. 연결을 확인한 뒤 다시 시도할 수 있습니다. 저장하지 못한 내용이 남아 있는지는 확인되지 않았습니다.
독자와 사용처: 앱에서 문서를 저장하던 사용자에게 보여 줄 오류 안내입니다.
말투: 짧고 정중한 존댓말을 사용합니다.
보존할 내용: 저장 실패 원인과 재시도 방법을 유지합니다. 작성한 내용이 보존됐거나 다시 시도하면 반드시 저장된다고 쓰지 않습니다.

원문:
인터넷 연결이 끊어진 관계로 저장 작업을 수행할 수 없습니다. 연결 상태에 대한 확인 후 저장 작업을 다시 진행해 주시기 바랍니다.
```

이후에는 원문과 문맥을 자신의 글에 맞게 바꿔 사용할 수 있습니다. 실제 문장을 공개 이슈에 공유할 때는 개인정보와 비공개 자료를 제외해 주세요.

누구의 말로 누구에게 전달할지, 어디에 사용할 문장인지, 어떤 말투를 유지할지 알려 주세요. 전달 시점이나 앞선 대화가 표현에 영향을 준다면 함께 알려 주세요. 대화에서 이미 확인한 내용은 반복하지 않아도 됩니다. 확정한 문구나 바꾸면 안 되는 수치가 있다면 명시합니다. 초안을 새로 작성할 때는 글에 담을 사실과 목적을 알려 주세요.

Codex에서 설치한 스킬이 나타나지 않으면 Codex를 다시 실행합니다. 자세한 인식 방식은 [OpenAI의 스킬 안내](https://learn.chatgpt.com/docs/build-skills)에 설명되어 있습니다.

## 대표 사용처

1. 대화와 기술 설명: 관계에 맞는 말투를 유지하고, 주체와 동작을 분명하게 설명합니다.
2. GitHub PR, 이슈, 리뷰: 변경 내용과 이유를 정리하고 구체적인 수정 요청을 작성합니다.
3. UI 버튼과 안내: 사용자가 할 수 있는 행동과 현재 상태를 짧게 전달합니다.
4. 이메일: 실제 연락 상황에 맞춰 필요한 답변이나 행동을 요청합니다.
5. 포트폴리오와 이력서: 팀 성과와 담당 범위를 구분하고 확인된 결과를 설명합니다.
6. 학습 자료: 먼저 알아야 할 개념부터 설명하고, 문단 사이의 관계를 자연스럽게 연결합니다.

## 평가와 검증

2026년 10월 15일, Codex Desktop에서 `gpt-5.6-sol` 모델과 `high` 설정으로 `v0.1.0`의 회귀 사례 50개를 평가했습니다. 49개를 통과했고 1개는 실패로 집계했습니다. 핵심 실패는 없었으며, 두 평가자의 판정이 달랐던 1개 사례에는 추가 평가를 진행했습니다. [평가 결과](evals/results-v0.1.0.md)에서 실행 환경, 평가 대상 해시와 결과를 확인할 수 있습니다. 이 결과는 이후 지침이 바뀐 `main`의 전체 평가 결과가 아닙니다.

위 평가는 Codex에서 수행했습니다. Claude 웹에서는 `v0.1.0` ZIP 업로드와 스킬 활성화 후 일부 사례에서 스킬 본문과 필수 보조 지침을 읽고 적용하는 것을 확인했습니다. 지침을 따르지 않은 답변도 있었습니다. 모든 상황에서의 출력 품질이나 지침 준수를 보장하지 않으므로, 생성된 문장은 사용 전에 검토해 주세요.

현재 `main`의 수정된 지침은 Claude 웹에서 화자, 발송 시점, 장소, 공개 범위, 요청 의도와 학습 설명 사례로 확인했습니다. 스킬 본문과 필수 보조 지침을 읽은 기록을 확인하고 실제 출력을 검토했습니다. 이 검증은 해당 사례에 한정되며, Codex의 전체 평가를 다시 수행한 결과는 아닙니다.

Claude Code는 GitHub CLI 2.97.0으로 `v0.1.0`을 프로젝트 범위에 설치하고 필수 참조 파일이 포함되는 것까지 확인했습니다. `@main` 명령도 Claude Code와 Codex의 별도 프로젝트에서 실행해 스킬 본문과 필수 참조 파일이 보존되는 것을 확인했습니다. 설치 파일 검사는 모델의 출력 품질 평가가 아닙니다. Claude Code의 실제 실행과 데스크톱 앱의 ZIP 업로드는 검증하지 않았습니다.

평가 자료는 범용 사례 24개, 확정 문구 보존 사례 2개, 문장부호 사례 7개, 문맥과 요청 반영 사례 10개, 상황에 따른 표현 사례 7개로 구성됩니다. 각 사례에는 의미 보존, 근거 없는 내용의 추가 여부, 문맥 적합성, 한국어 문장 구조, 높임 수준, 코드와 식별자 보존, 결과 형식을 판정하는 기준이 있습니다.

실패로 집계한 `register-casual-001`에서는 평가자 2명이 출력의 ‘바로’를 근거 없는 즉시성 약속으로 판단했습니다. 그러나 [사례의 문맥](evals/core.json)에는 ‘바로 고치고’가 명시돼 있습니다. 판정 근거와 제공된 문맥이 일치하지 않는 사례이며, 최초 판정은 수정하지 않고 [원래 출력과 판정](evals/runs/v0.1.0.jsonl)을 보존했습니다. 같은 모델을 사용하는 평가자들이 문맥을 잘못 해석할 수 있다는 한계도 함께 고려해야 합니다.

[평가 방법](evals/README.md)에는 독립 평가자의 판정 절차와 재현 명령이 있습니다. Python 도구는 파일 형식과 실행 기록, 결과 집계를 검사하며 한국어 품질을 자동으로 판정하지 않습니다. 평가 자료 일부는 교정 예시와 겹치는 회귀 사례입니다.

## 사용 전 참고 사항

1. 문장 표현을 다듬는 지침입니다. 원문의 사실관계를 대신 확인하거나 다른 언어의 문서 전체를 번역하는 도구는 아닙니다.
2. 독자와 상황에 따라 적절한 표현이 달라집니다. 중요한 문서는 수정한 내용과 말투가 원래 의도에 맞는지 검토해야 합니다.
3. 저장소는 [Agent Skills 규격](https://agentskills.io/specification)에 맞춰 구성되어 있습니다. 형식이 같다는 이유만으로 모든 에이전트와 모델에서 같은 품질이 나온다고 보장하지 않습니다.
4. 제한된 회귀 사례만으로 처음 보는 한국어 문서 전반의 품질을 판단할 수는 없습니다.

## 기여 방법

어색한 결과를 발견했다면 원문, 실제 출력, 독자와 사용 목적을 함께 알려 주세요. 개인정보와 비공개 자료는 제외합니다. 사례 추가와 규칙 수정 방법은 [기여 안내](CONTRIBUTING.md)를 참고하세요.

## License

[MIT License](LICENSE)

한국어 글을 다듬는 데 도움이 됐다면 Star를 남겨 주세요.
