# Korean punctuation rules

Apply this reference to every Korean natural-language span you write or edit, including headings, labels, table cells, and prose. These are required writing rules, not an optional style profile. The punctuation functions follow the National Institute of Korean Language's [한글 맞춤법 부록: 문장 부호](https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001&regltn_no=714), sections 5, 15, 16, and 17.

An allowed punctuation mark is not obligatory. When the user or repository further restricts a mark in the requested output, use a permitted Korean alternative or rewrite the sentence. For example, a no-U+00B7 instruction limits editable prose even where a middle dot would otherwise be allowed. Do not describe that preference as a universal grammar prohibition or change protected text to satisfy it. A later instruction overrides an older restriction only for the same target and scope.

## Protect exact text first

Preserve user-confirmed wording exactly, including spaces and punctuation, unless the user explicitly authorizes changing that wording. That requirement takes priority over general punctuation cleanup. Also preserve characters that belong to code, identifiers, filenames, paths, URLs, commands, options, Git branches, package names, versions, regular expressions, API values, official names, or quotations retained as source text.

Examples of protected literals: `feature/fix-copy`, `--dry-run`, `Content-Type`, `v0.1.0`, `2026-08-31`, and `https://cli.github.com/manual/gh_skill_install`.

Quotation marks or a code fence used only to delimit text submitted for rewriting do not make the entire input immutable. Distinguish the editable passage from literal content inside it. Never rewrite a protected literal merely to satisfy a punctuation scan; revise only the surrounding Korean.

## Identify the character

Inspect the Unicode code point rather than the mark's apparent length.

| Character | Code point | Unicode name | Korean function |
| --- | --- | --- | --- |
| `·` | `U+00B7` | MIDDLE DOT | 가운뎃점 |
| `-` | `U+002D` | HYPHEN-MINUS | 붙임표 |
| `~` | `U+007E` | TILDE | 물결표 |
| `―` | `U+2015` | HORIZONTAL BAR | 줄표 |
| `–` | `U+2013` | EN DASH | Not the Korean 줄표 |
| `—` | `U+2014` | EM DASH | Not the Korean 줄표 |

## Match the function

### Middle dot

Use the middle dot for items grouped by a consistent criterion, paired expressions, or expressions with a shared component omitted. Attach it to both sides. A comma or Korean particle is often sufficient for a plain list; do not add a middle dot just to shorten an arbitrary phrase.

1. Paired expressions: `참·거짓`.
2. Shared component: `초·중급 과정`, meaning both `초급 과정` and `중급 과정`.
3. Plain list: `이름과 이메일을 입력하세요.`

### Hyphen

Use the hyphen between ordered stages or closely related expressions. It can also replace the tilde for a period, distance, or range. Attach it to both sides: `준비-실행-검토`, `원-달러 환율`, `5-10쪽`.

Do not use it to append an explanation or imitate an English compound in Korean prose. A linguistic form such as `-습니다` is specialist notation, not ordinary prose punctuation; preserve it when that form is the subject of the text.

### Tilde

Use the tilde for a period, distance, or range, attached to both sides: `8월 1일~8월 3일`, `서울~부산`, `5~10쪽`. A hyphen is allowed in the same position.

Do not append it as a general sentence-ending decoration or tone marker. For editable prose, `감사합니다~` becomes `감사합니다.`

The older use for omitted material before or after a word, such as `~사회`, is outside the current punctuation rules. The official commentary does not prohibit that specialist notation. Preserve it only when a linguistic example or exact source requires it; do not generalize it to ordinary Korean.

### Horizontal bar

Use the horizontal bar around a subtitle following a title. The trailing bar may be omitted. Spaces around the bar are standard; closed spacing is also allowed. Example: `도시의 기록 ― 골목의 변화`.

Do not use it for an inserted explanation in a sentence.

### En dash and em dash

Do not use either character as Korean prose punctuation or substitute it for the horizontal bar. Identify whether the passage expresses a contrast, explanation, or range, then rewrite that relationship with Korean syntax or a suitable Korean mark.

1. Explanation: `저장이 끝났습니다—이제 창을 닫아도 됩니다.` becomes `저장이 끝났습니다. 이제 창을 닫아도 됩니다.`
2. Range: `5–10쪽` becomes `5~10쪽`.

Do not apply those replacements inside protected literals.

## Separate Markdown from Korean punctuation

A line-initial `-` used as a list marker and a Markdown horizontal rule are formatting syntax. They are not grammatical uses of the Korean hyphen. Use numbered lists by default in generated Korean Markdown, and avoid adding hyphen-based horizontal rules. Preserve hyphen lists or rules when the user explicitly requests that Markdown format or asks to retain the existing format. Do not label valid Markdown syntax a Korean grammar error.

## Review by meaning

1. Separate protected text, formatting syntax, and editable Korean.
2. Check the six code points above against their actual functions.
3. Confirm that each range keeps its original endpoints and units.
4. Rewrite invalid punctuation together with the sentence structure; do not run a blind character replacement.
5. Compare protected text with the source to confirm exact preservation.
6. Check the user's additional restrictions in editable prose without treating protected literals or Markdown syntax as ordinary punctuation.
