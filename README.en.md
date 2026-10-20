# natural-korean-writing

An Agent Skill that preserves the original meaning while refining translation-like and awkward Korean for the text's purpose and audience.

[한국어](README.md) | [English](README.en.md)

## Before and after

A Korean feature description:

Before

```text
본 기능을 통해 사용자는 작성한 내용을 보다 편리하게 확인하는 것이 가능합니다.
```

After

```text
이 기능을 사용하면 작성한 내용을 더 편리하게 확인할 수 있습니다.
```

The meaning stays the same while unnecessary nominalization and translation-like phrasing are reduced.

## Writing principles

Use the skill to draft, revise, or review Korean.

1. Preserve facts, measurements, responsibilities, intent, and commitments. Keep confirmed wording, code, paths, URLs, and technical identifiers unchanged.
2. Match who is speaking to whom, when, where, and for what purpose. Do not automatically turn casual conversation into formal prose.
3. Review particles, predicates, omitted referents, information order, and politeness. Reduce unnecessary nominalization and repetition, and use punctuation according to Korean conventions.

See [12 before-and-after examples](examples/before-after.md) for the reasoning and facts preserved in each revision.

The [context and audience companion](skills/natural-korean-writing/references/context-audience-boundary.md) is included in the same installation and is mandatory for Korean writing and review. No separate installation or opt-in is needed. It guides decisions about the speaker, relationship, timing, setting, and disclosure scope.

## Installation

Install the skill in Claude, Claude Code, or Codex. Each method includes the same `SKILL.md` and `references/` folder, including the context and audience companion.

### Claude Code and Codex

Requires [GitHub CLI 2.90.0 or later](https://github.com/cli/cli/releases/tag/v2.90.0). Command syntax is based on GitHub CLI 2.97.0. `gh skill` is in public preview, so its commands and behavior may change.

Check your version and command availability:

```powershell
gh --version
gh skill --help
```

Read the instructions with [preview](https://cli.github.com/manual/gh_skill_preview) before installing:

```powershell
gh skill preview Jiyeong-kor/natural-korean-writing natural-korean-writing
```

#### Claude Code

Install at user scope to use the skill across your projects:

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing --agent claude-code --scope user
```

For the current project only, run inside its Git repository:

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing --agent claude-code --scope project
```

#### Codex

Install at user scope to use the skill across your projects:

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing --agent codex --scope user
```

For the current project only, run inside its Git repository:

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing --agent codex --scope project
```

#### Advanced: pin a version

Specify a release tag to keep using the same version. This example uses Claude Code; replace the agent flag with `--agent codex` for Codex. The tag must exist in the repository:

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing@v0.1.0 --agent claude-code --scope user
```

Without a version, the CLI selects the latest release or, if none exists, the default branch HEAD. See the [installation manual](https://cli.github.com/manual/gh_skill_install) for scope and version behavior.

### Claude web and desktop app

Enable code execution in Claude. For organization accounts, an administrator must allow skill uploads and use. See [Claude's skill guide](https://support.claude.com/en/articles/12512180-use-skills-in-claude) for the settings.

1. Download this repository through `Code > Download ZIP` and extract it.
2. Copy the repository's root `LICENSE` into `skills/natural-korean-writing`, then ZIP that entire folder. The ZIP must contain a top-level `natural-korean-writing/` folder with `SKILL.md`, `references/`, and `LICENSE` inside. Do not upload the whole repository ZIP or package only `SKILL.md`.
3. In Claude, open `Customize > Skills`, then select `+ > + Create skill > Upload a skill`.
4. Upload the prepared ZIP and enable `natural-korean-writing` in the list.

See [Claude's custom skill guide](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) for the folder structure.

## Usage

After installing, invoke the skill for your tool and include the request below.

1. Claude Code: prefix the request with `/natural-korean-writing`. See [Claude Code's skill guide](https://code.claude.com/docs/en/skills) for invocation details.
2. Codex: prefix the request with `$natural-korean-writing`.
3. Claude web and desktop app: enable the skill, then prefix the request with `natural-korean-writing 스킬을 사용해 주세요.` (Use the natural-korean-writing skill.)

The request uses the fictional save-error message from the [before-and-after examples](examples/before-after.md#8-ui-안내-저장-실패와-재시도).

```text
아래 안내문을 원래 의미는 유지하면서 자연스러운 한국어로 고쳐 주세요. 수정한 안내문만 보여 주세요.

문맥: 인터넷 연결이 끊겨 저장에 실패했습니다. 연결을 확인한 뒤 다시 시도할 수 있습니다. 저장하지 못한 내용이 남아 있는지는 확인되지 않았습니다.
독자와 사용처: 앱에서 문서를 저장하던 사용자에게 보여 줄 오류 안내입니다.
말투: 짧고 정중한 존댓말을 사용합니다.
보존할 내용: 저장 실패 원인과 재시도 방법을 유지합니다. 작성한 내용이 보존됐거나 다시 시도하면 반드시 저장된다고 쓰지 않습니다.

원문:
인터넷 연결이 끊어진 관계로 저장 작업을 수행할 수 없습니다. 연결 상태에 대한 확인 후 저장 작업을 다시 진행해 주시기 바랍니다.
```

Then replace the source and context with your own text. Remove personal and confidential information before sharing a real example in a public issue.

Identify whose voice the text uses, its recipient, where it will appear, and the tone to preserve. Add delivery timing or prior conversation when it affects the wording; there is no need to repeat context already established. Identify confirmed wording and measurements that must not change. For a new draft, provide the facts to include and the purpose of the text.

If an installed skill does not appear in Codex, restart Codex. See [OpenAI's skill guide](https://learn.chatgpt.com/docs/build-skills) for discovery behavior.

## Use cases

Conversation, technical explanations, GitHub PRs, issues and reviews, UI labels and guidance, email, portfolios, resumes, and learning material. The skill adapts the wording to the reader while keeping the supplied facts and scope.

## Evaluation and validation

On October 15, 2026, 49 of 50 regression cases for `v0.1.0` passed in Codex Desktop using `gpt-5.6-sol` with `high` reasoning effort. One case failed, with no critical failures. One reviewer disagreement required adjudication. The [evaluation results](evals/results-v0.1.0.md) include the runtime, evaluated source hash, and results. These are not full-suite results for subsequent instruction changes on `main`.

These evaluation results are from Codex. In Claude on the web, `v0.1.0` ZIP upload and skill activation were tested, and reading and application of the skill and required companion were confirmed in a limited set of cases. Some responses did not follow the instructions. These checks do not establish consistent output quality or instruction compliance across situations; review generated text before use.

The revised instructions on `main` were checked in Claude on the web with cases covering speaker, delivery time, location, disclosure scope, communicative intent, and learning explanations. File-read records for the skill and required companion were observed, and the actual outputs were reviewed. This validation is limited to those cases; it is not a rerun of the full Codex evaluation.

For Claude Code, installation of `v0.1.0` at project scope with GitHub CLI 2.97.0 and inclusion of the required reference files have been verified. Actual execution in Claude Code and ZIP upload in the desktop app have not been verified.

The evaluation set contains 24 core cases, 2 confirmed-copy cases, 7 punctuation cases, 10 context and instruction-following cases, and 7 situation-dependent writing cases. Its rubric covers meaning, unsupported additions, audience fit, natural Korean, consistent politeness, literal preservation, and output format.

For the failed `register-casual-001` case, two judges treated ‘바로’ (immediately) as an unsupported promise, although the [supplied context](evals/core.json) explicitly includes ‘바로 고치고’. That rationale conflicts with the provided context. The [original output and judgments](evals/runs/v0.1.0.jsonl) remain unchanged, including the failed result. This illustrates a limitation of same-model judges: they can share a mistaken reading of the context.

The [evaluation guide](evals/README.md) defines independent reviewer judgments and reproduction commands. Python tools validate file formats, execution records, and aggregation; they do not automatically judge Korean quality. Some regression cases overlap with the writing examples.

## Limitations

1. This is writing guidance, not a fact-checking service or a tool for translating entire documents from other languages.
2. Appropriate wording depends on context. Review important documents for meaning and tone after revision.
3. The repository follows the [Agent Skills specification](https://agentskills.io/specification). Format compatibility does not guarantee equal quality across agents or models.
4. A limited regression set cannot establish quality across unseen Korean documents.

## Contributing

For an awkward result, provide the original text, actual output, audience, and purpose. Remove private information before sharing. See [CONTRIBUTING.md](CONTRIBUTING.md) for adding cases or changing rules.

## License

[MIT License](LICENSE)

If the skill helps with your Korean writing, please star the repository.
