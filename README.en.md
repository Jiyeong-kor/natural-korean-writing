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

### User scope

Install for Codex across your projects:

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing --agent codex --scope user
```

### Project scope

Run inside the Git repository where you want to use the skill:

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing --agent codex --scope project
```

### Advanced: pin a version

Specify a release tag to keep using the same version. The tag must exist in the repository:

```powershell
gh skill install Jiyeong-kor/natural-korean-writing natural-korean-writing@v0.1.0 --agent codex --scope user
```

Without a version, the CLI selects the latest release or, if none exists, the default branch HEAD. See the [installation manual](https://cli.github.com/manual/gh_skill_install) for scope and version behavior.

## Usage

In Codex, submit this request followed by the Korean text:

```text
$natural-korean-writing을 사용해 다음 문장을 원래 의미는 유지하면서 독자와 목적에 맞는 자연스러운 한국어로 고쳐 주세요.
```

Identify whose voice the text uses, its recipient, where it will appear, and the tone to preserve. Add delivery timing or prior conversation when it affects the wording; there is no need to repeat context already established. Identify confirmed wording and measurements that must not change. For a new draft, provide the facts to include and the purpose of the text.

If an installed skill does not appear, restart Codex. See [OpenAI's skill guide](https://learn.chatgpt.com/docs/build-skills) for discovery behavior.

## Use cases

Conversation, technical explanations, GitHub PRs, issues and reviews, UI labels and guidance, email, portfolios, resumes, and learning material. The skill adapts the wording to the reader while keeping the supplied facts and scope.

## Evaluation and validation

On October 15, 2026, 49 of 50 regression cases passed in Codex Desktop using `gpt-5.6-sol` with `high` reasoning effort. One case failed, with no critical failures. One reviewer disagreement required adjudication. The [evaluation results](evals/results-v0.1.0.md) include the runtime, evaluated source hash, and results.

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
