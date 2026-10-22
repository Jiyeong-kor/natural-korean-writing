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

## 13. Written application: a supported relationship

Fictional context: An applicant designed a form. People could submit it with a required field empty. The applicant added guidance next to that field. No test result or effect measurement is supplied.

Before: `필수 항목이 비어 있어도 제출할 수 있었습니다. 항목 옆에 안내를 추가했습니다.`

After: `필수 항목이 비어 있어도 제출할 수 있어, 해당 항목 옆에 입력 안내를 추가했습니다.`

Why: Make the supplied reason for the action explicit. A connective ending can carry the relationship; no sentence-opening conjunction or universal preference for a single sentence is required.

Preserved: The empty-field condition and the applicant's action. The revision does not claim that the guidance blocked submission or reduced errors.

## 14. Written report: action and object

Fictional context: A team completed the scheduled review. Whether the review achieved its broader quality goal has not been measured.

Before: `예정된 검토 작업을 달성했습니다.`

After: `예정된 검토 작업을 마쳤습니다.`

Why: The object is a scheduled task, and the supplied action is its completion. Choose the predicate from that relationship, not from a list of approved or prohibited verbs.

Preserved: Completion of the review. The revision does not turn completion into an achieved quality goal.

## 15. Application motivation: replace an empty assessment

Fictional context: An applicant enjoyed explaining difficult science concepts in a volunteer class and chose teaching because they wanted to keep doing that work. No claim about earlier study dissatisfaction is supplied.

Before: `교육은 제가 세운 진로 기준과 맞았습니다.`

After: `봉사 수업에서 어려운 과학 개념을 풀어 설명하는 일이 즐거웠고, 이 일을 계속하고 싶어 교사를 진로로 정했습니다.`

Why: State the supplied experience and reason for the choice instead of an unexplained match with a criterion. Enjoyment is allowed here only because this fictional source supplies it; it is not a stock motivation to add to another person's story.

Preserved: The volunteer activity, stated enjoyment, and career choice. No invented learning speed or criticism of a former field.

## 16. Career history: do not manufacture a causal bridge

Fictional context: A person studied geography and later took an accounting course. They say that organizing expenditure records in that course interested them. No reason for leaving geography is supplied.

Before: `가치 있는 일을 하고 싶어 지리학을 공부했지만 성과를 보기 어려워 회계를 선택했습니다.`

After: `지리학을 공부한 뒤 회계 수업을 들으며 지출 내역을 정리하는 일에 관심을 갖게 됐습니다.`

Why: Remove the invented initial motive and dissatisfaction instead of smoothing their wording. A chronological connection does not establish why a person changed fields.

Preserved: The two learning experiences, their sequence, and the supplied interest. The revision does not claim that a career choice was made.

## 17. Experience entry: ongoing work instead of drafting commentary

Fictional context: A person produces and regularly publishes a community newsletter. An adjacent date label already says that the period is current as of the stated date. The editable responsibilities field contains an unnecessary explanation of that label.

Before: `뉴스레터를 제작하고 있습니다. 입력한 마지막 날짜는 작성 시점입니다.`

After: `뉴스레터를 제작하고 있으며 현재도 정기적으로 발행하고 있습니다.`

Why: Describe the source-confirmed regular publication; the adjacent date label already supplies the date's interpretation. Without that label or another adequate clarification, first resolve a misleading end-date claim rather than simply deleting the explanation.

Preserved: Ongoing newsletter work and the source-confirmed regular publication. No completed employment or activity end date is invented.

## 18. Goal and task: preserve what was achieved

Fictional context: A team aimed to review every item on a checklist and did review them all.

Before: `모든 항목을 검토한다는 목표를 마쳤습니다.`

After: `점검표의 모든 항목을 검토해 목표를 달성했습니다.`

Why: A goal is achieved; a review task is completed. The supplied all-item result supports achievement here, unlike the unmeasured broader goal in example 14.

Preserved: The specific goal and verified completion of its scope. This example does not require replacing every occurrence of `마치다` with `달성하다`.
