# Rewrite Examples

Each context supplies the facts needed for its revision. Preserve those facts; do not infer extra behavior, measurements, or ownership. These examples illustrate decisions, not a requirement to rewrite every similar-looking sentence.

## 1. General explanation: nominalization

Context: A feature lets users view content they wrote more conveniently.

Before: `본 기능을 통해 사용자는 작성한 내용을 보다 편리하게 확인하는 것이 가능합니다.`

After: `이 기능을 사용하면 작성한 내용을 더 편리하게 확인할 수 있습니다.`

Why: Replace nominalized phrasing with a direct predicate.

Preserved: The feature, the user's written content, and the stated convenience. No new capability or measurement.

## 2. General explanation: an abstract use of close

Context: An editing instruction requires correcting inconsistent content throughout a plan, alongside other edits.

Before: `기획서 전체의 충돌도 함께 닫는다.`

After: `기획서 전체에서 서로 맞지 않는 내용도 함께 수정한다.`

Why: Name the actual editing action instead of mechanically translating an abstract use of `close` as `닫다`.

Preserved: The whole-plan scope, inconsistent content, and the instruction to correct it alongside other edits.

## 3. Technical explanation: a predicate's particle

Context: A program accesses a settings file and reads its values.

Before: `프로그램은 설정 파일을 접근해 설정값을 읽습니다.`

After: `프로그램은 설정 파일에 접근해 설정값을 읽습니다.`

Why: The target of `접근하다` takes `에` in this sentence.

Preserved: The program, file, and reading action. No claim about writing the file.

## 4. Technical explanation: an actor change

Context: A server sends a response. The client updates the screen when it receives that response.

Before: `서버의 응답이 클라이언트에 전송되어 화면을 갱신합니다.`

After: `서버가 응답을 보내면 클라이언트가 응답을 받아 화면을 갱신합니다.`

Why: Make the actor of each action explicit instead of making the response the implied actor of a screen update.

Preserved: Both actors, transmission and receipt, and the condition for the screen update.

## 5. GitHub PR: completed work

Context: A contributor corrected typos in a document. No other changes or tests are supplied.

Before: `문서의 오타 수정에 대한 작업을 진행했습니다.`

After: `문서의 오타를 수정했습니다.`

Why: State the completed action directly.

Preserved: The document correction. No invented test result or broader improvement.

## 6. GitHub review: a concrete request

Context: Submission is allowed without an attachment, which registers an empty document. The requested correction is to allow submission only with an attachment.

Before: `이 부분은 문제가 있는 것 같습니다. 확인 부탁드립니다.`

After: `첨부 파일이 없어도 제출할 수 있어 빈 문서가 등록됩니다. 첨부 파일이 있을 때만 제출할 수 있도록 수정해 주세요.`

Why: Use the supplied occurrence condition, effect, and requested change instead of a vague concern.

Preserved: The confirmed defect and requested condition. The revision does not claim the defect has already been fixed.

## 7. UI label: the action

Context: A button saves the document being edited.

Before: `사용자의 작업 흐름 개선을 위해 작성 중인 문서를 저장하는 버튼입니다.`

After: `저장`

Why: A button needs its action label, not the creator's product strategy.

Preserved: The save action. The surrounding editor supplies the document context.

## 8. UI guidance: a confirmed failure

Context: An internet disconnection prevented saving. The user can check the connection and retry. Whether unsaved content remains is not specified.

Before: `인터넷 연결이 끊어진 관계로 저장 작업을 수행할 수 없습니다. 연결 상태에 대한 확인 후 저장 작업을 다시 진행해 주시기 바랍니다.`

After: `인터넷 연결이 끊겨 저장하지 못했습니다. 연결을 확인한 뒤 다시 시도해 주세요.`

Why: State the confirmed cause, result, and available next action concisely.

Preserved: The failed save and retry. No assurance about unsaved content or eventual success.

## 9. External email: an unanswered follow-up

Context: The sender sent material last Monday and has received no reply. They want to know whether the recipient has reviewed it.

Before: `답장드립니다. 지난 월요일에 보내드린 자료의 확인 여부에 대한 회신 부탁드립니다.`

After: `지난 월요일에 보내드린 자료를 확인하셨는지 알려 주세요.`

Why: Remove the incorrect claim that this is a reply and name the requested answer.

Preserved: The earlier message, timing, and request. No new deadline or claim about the recipient's actions.

## 10. Portfolio: responsibility without repetition

Context: The portfolio already identifies its author. That author implemented file upload and the associated error guidance.

Before: `저는 파일 업로드 기능을 구현했습니다. 이 구현을 통해 오류 안내를 제공했습니다.`

After: `파일 업로드 기능과 오류 안내를 구현했습니다.`

Why: Combine the supplied responsibilities without repeating an already-established author or nominalizing the previous action.

Preserved: The author's two implementation responsibilities. No adoption, performance, or team contribution claim.

## 11. Learning material: a prerequisite first

Context: A beginner needs the relation between bits and bytes. Supplied facts: a bit represents 0 or 1; a byte consists of eight bits.

Before: `바이트는 8비트로 이루어집니다. 비트는 0 또는 1을 나타냅니다.`

After: `비트는 0 또는 1을 나타냅니다. 비트 8개가 모이면 1바이트가 됩니다.`

Why: Explain the component before using it to define the larger unit.

Preserved: Both definitions and the ratio. No new calculation or learner exercise.

## 12. Conversation: consistent politeness

Context: A polite reply says the user's proposed sentence is more natural than the earlier one. No further evaluation reason is supplied.

Before: `네 문장이 낫습니다.`

After: `제안해 주신 문장이 더 자연스럽습니다.`

Why: Make the reference to the listener and the sentence ending fit the same polite relationship.

Preserved: The comparative judgment and polite tone. No invented praise or explanation.
