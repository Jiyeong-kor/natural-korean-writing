## 4. UI label and guidance

1. Reader: a person deciding what to select, enter, or do next.
2. Purpose: identify an available action or explain the current state, consequence, or recovery.
3. Information: the visible state and the action the person can actually take. Include a cause only when it is confirmed and helps that decision. State the target and consequence when the action is irreversible.
4. Tone: short and concrete. Labels may be noun or verb phrases; explanatory text needs enough sentence structure to avoid ambiguity.
5. Common errors: adding a failure that the source never established, vague emotional reassurance, and describing a recovery action that is not available.
6. Output: a label or brief message that matches the stated behavior. `저장` names saving; `다시 시도` fits only when retrying is actually available. Do not describe a dismiss action as recovery.

### Check code-backed copy in context

When writing or reviewing a string tied to implementation, use sufficient supplied context without asking for more code. Otherwise inspect the relevant call sites when access is authorized. Check where the string appears, which branch displays it, what the user just did, and which controls are visible and enabled in the current state, and what they do. A handler in the code is not by itself an available action. Compare adjacent copy for established terms and voice. A shared key may appear in different states: check the affected uses and keep shared wording true in each. If the affected uses cannot share accurate copy, report the mismatch instead of silently changing UI behavior or resource wiring.

Preserve exact interpolation tokens. Check the values actually passed to them, including formatting and units already present. Check a representative substitution for each different value format so units and Korean particles read correctly. If an important condition or value cannot be established, keep the affected change conditional and identify what would resolve it, without promising unsupported behavior. Distinguish what the code shows from what was observed in a running UI.
