# Artifact Style Profiles

Use the profile that fits the requested output. A conversation about a document does not set that document's voice. Keep the source's facts and the requested scope while adapting to the reader's knowledge and purpose.

For Korean prose intended for other readers or remote publication, use natural `합니다/했습니다`-style honorifics from the local draft unless the user or destination explicitly requires another register. Include explanatory and checklist sentences in that check; short titles, labels, status values, code, and source quotations retain their appropriate form. Follow explicit user or repository wording restrictions within their scope rather than applying one author's personal preferences to everyone.

## 1. Conversation

1. Reader: the person in the current exchange, with the context already shared there.
2. Purpose: answer a question, clarify a distinction, correct an answer, or make an authorized commitment.
3. Information: the direct answer and the reason needed to understand it. Include a next action only when the request calls for one.
4. Tone: the user's requested conversational style and the established relationship. Concision does not require formal prose or omitted particles that change the meaning.
5. Common errors: answering an adjacent question, unnecessary preamble, abrupt personal evaluation, and switching speech level without a reason.
6. Output: a ready-to-send reply. For an actual casual commitment, a short sentence such as `다시 확인할게.` can be sufficient.

## 2. Technical explanation

1. Reader: a practitioner or learner whose knowledge is established by the request.
2. Purpose: explain the requested concept, behavior, comparison, or cause.
3. Information: the relevant conditions, mechanism, and impact. Define an unfamiliar term before relying on it; use an already familiar term directly. Add examples only when they help explain the requested subject and do not expand a rewriting task.
4. Tone: precise, direct, and appropriate to the reader's technical background. Preserve established terms instead of introducing unfamiliar translations.
5. Common errors: turning background concepts into a separate lesson, restating a known word as though it were new, and presenting an inferred cause as confirmed behavior.
6. Output: an explanation at the requested depth. Use code-level names where the technical reader needs them, with enough meaning to understand their role.

## 3. GitHub PR, issue, review, or comment

1. Reader: contributors, maintainers, and reviewers familiar with the repository.
2. Purpose: explain a change, report a problem, request a concrete correction, or record a review conclusion.
3. Information: for a PR, the scope, reason, changed behavior, and actual verification; for an issue, the observed state, relevant conditions, and expected behavior; for a review, the problem, impact, reason, and requested correction. Use only the information relevant to that artifact.
4. Tone: direct and respectful, with consistent honorifics in Korean prose. Explain criticism and make the requested change specific. A terse conversation does not authorize terse memo endings in a publication draft.
5. Common errors: vague requests such as `이 부분을 확인해 주세요.` without identifying what to check, a bare file list without behavioral meaning, and claims that unperformed tests passed.
6. Output: copy-ready Markdown following the repository's format. Headings such as `변경 내용` and `검증 결과` can organize a PR when that structure helps.

## 4. UI label and guidance

1. Reader: a person deciding what to select, enter, or do next.
2. Purpose: identify an available action or explain the current state, consequence, or recovery.
3. Information: the visible state and the action the person can actually take. Include a cause only when it is confirmed and helps that decision. State the target and consequence when the action is irreversible.
4. Tone: short and concrete. Labels may be noun or verb phrases; explanatory text needs enough sentence structure to avoid ambiguity.
5. Common errors: adding a failure that the source never established, vague emotional reassurance, and describing a recovery action that is not available.
6. Output: a label or brief message that matches the stated behavior. `저장` names saving; `다시 시도` fits only when retrying is actually available. Do not describe a dismiss action as recovery.

## 5. External email

1. Reader: the recipient named by the actual thread or request.
2. Purpose: inform, request a response, confirm an arrangement, or follow up.
3. Information: the relevant thread state, confirmed facts, requested answer or action, and an established deadline if there is one. Identify the sender or recipient only when the reader needs that distinction.
4. Tone: polite without unnecessary ceremony, matching the relationship and subject.
5. Common errors: calling an unanswered follow-up a reply, inventing a deadline or commitment, and saying a file is attached when it is not.
6. Output: a ready-to-send email with a clear request. Use `수정한 파일을 첨부합니다.` only when the attachment is actually part of the message.

## 6. Portfolio or resume

1. Reader: a hiring manager or interviewer assessing relevant experience.
2. Purpose: explain the applicant's responsibilities, decisions, actions, and supported results.
3. Information: the problem, relevant constraint, actual contribution, reasoning, outcome, and evidence needed to understand the work. Distinguish individual work from team results.
4. Tone: concise professional prose with natural omissions where each action's actor remains clear. A portfolio's known author does not by itself mark a shift from a team's work to that person's contribution; retain the needed contrast through wording or structure before removing a first-person expression.
5. Common errors: claiming team work as individual work, inventing measurements, repeating `저는` in every sentence, and listing technologies without explaining their use.
6. Output: reader-facing prose or concise resume entries. `담당 역할` can identify responsibilities; do not impose a fixed count-label order or an arbitrary number of accomplishments.

### Application essays and narrative experience answers

Read the entire [application answer workflow](application-answer-workflow.md) for these answers. Use it to choose evidence against the full question and guidance, reconcile all answers for the same company, and preserve the reviewed version through delivery. The guidance here explains the prose; the workflow explains the decisions and evidence needed to keep that prose accurate through revisions.

An application essay is reader-facing written explanation, not chat, a commit log, or a verification memo. Interpret the actual question before selecting evidence: a reason for choosing work is not merely evidence of qualification, and a request about overcoming constraints needs the constraint and completion process, not only a list of technical operations. Treat inferred question intent as interpretation unless the employer publishes its criteria.

Use professional written Korean appropriate to the destination. Keep source-supported causal, contrastive, and temporal links, including connective endings when useful; do not equate formality with nominalized jargon or brevity with isolated short sentences. Organize each paragraph around the point the experience establishes. A technical name, test value, or implementation detail belongs only when its role in the applicant's decision or contribution is clear to the intended reader.

Keep evidence checks separate from submitted prose. A test source's expected value is not a passed run or a user outcome. Do not fill a missing result with detailed expected values, invented metrics, or a long account of what the writer inspected. If evidence is insufficient, narrow the claim, select another supported example when authorized, or state the necessary clarification to the writer separately.

Explain a career choice through the applicant's source-supported experiences and reasons, not generic declarations that a field fits a criterion. Broad phrases about creating something valuable or proving ability do not explain what the applicant did or why it mattered. Select a concrete supplied interest or experience; do not invent an emotional reaction, disparage a former field, or treat a student's lack of professional outcomes as an established reason for changing direction.

Evidence of learning can come from another field when it supports the question. Describe what was learned, how it was applied, and the verified result. A prize does not by itself establish a short learning period, superior speed, or an identical ability in every field. Use those stronger claims only when the source supports them. Honor explicit word preferences within their stated scope, while retaining the underlying verification; a reader-facing answer can show the action and reason without naming the writer's evidence framework.

Do not manufacture a growth lesson to finish an experience answer. A self-evident maxim such as saying that accurate information matters may make an otherwise competent applicant sound as though they only just discovered a basic obligation. Check what was genuinely new to this person in this situation and what the supplied experience actually changed. When established, show the specific choice, changed practice, or subsequent action rather than appending a generic claim that its importance was learned. If no change or learning is supported, do not invent one; use another supported experience or identify the missing material separately when the question requires it. This does not prohibit `배웠습니다`: retain genuine technical learning, a concrete unfamiliar insight, or a source-confirmed realization when it answers the question and fits the reader's expectations.

For a dated experience entry, distinguish the actual activity state from how a form forced the writer to enter it. Keep an ongoing-activity statement when the reader needs it. Do not automatically put remarks about entry limitations, reference dates, or missing menu choices in a responsibilities field. Preserve any qualification needed to avoid a misleading end date in an appropriate note or field; omission of drafting commentary does not authorize a false date or completed-status claim.



Balance detail against the question and the judgment the reader must make. In an answer covering both strengths and limitations, an extended list of remedies can make the limitation appear to dominate the applicant's profile. Give the supported improvement action enough space to be understood without crowding out the relevant strength. Do not enforce a fixed word ratio, conceal a material limitation, or turn a proposed remedy into an established habit.

Keep a growth narrative about the source-supported character and choices that led to the present direction, rather than letting an implementation report take over. An achievement answer may need the difficult situation, why it mattered, the alternatives actually considered, the choice and its reason, the action, and the observed result. Include only the elements the question requires and the source establishes; this is not a mandatory paragraph template or permission to invent deliberation. Close the answer by completing its central point, not by appending a generic pledge or an obvious lesson. For a decision to enter a profession, a direct expression such as `개발자가 되기로 했습니다.` can convey the intended action more naturally than `개발자의 일을 선택했습니다.`; apply it only when that is the source-supported meaning, not as a mandatory ending or a replacement for locked wording.

Connect an experience to a future plan through the relevant similarity and difference. Prior work can explain what the applicant will examine or learn next without proving mastery of an unfamiliar employer system. Use the actual role description and confirmed company information; distinguish an architectural inference from a known implementation. Do not guess a stack, team structure, colleague's role, or future decision authority. Describe the work with an appropriate colleague or established review process when the exact counterpart is unknown, and retain a concrete personal contribution without boasting or erasing it through excessive modesty.

Distinguish first learning, further study, and prior application. An enrollment date alone does not establish when learning began. In a future plan, do not describe an already used skill as something the applicant will learn for the first time. Explain the particular unfamiliar task or deeper study instead. Preserve a source-supported plan to consult someone with relevant experience; do not invent that person's rank or quietly delete the consultation while polishing the passage.

When explaining verification work, connect the actual risk to the checks selected and the different roles of tests, review, and automation. A list of passing CI jobs does not explain why those checks were needed. Do not claim a review covered the exact final commit, or that every relevant case passed, without records establishing that scope.

When drafting under a length limit, first preserve the answer's necessary reasons, relationships, and supported details. If the user permits an over-limit working draft, identify it as a draft and retain important content for review rather than silently deleting it to fit. A submission-ready version must satisfy the actual field limit and counting rule. Do not pad a short answer with technology names or generic aspirations to fill the space. Honor an explicitly requested balance between parts without making that ratio a universal rule.

Reread the complete answer for question coverage, factual boundaries, natural predicate-object combinations, and continuity between paragraphs. Search-based checks can find suspicious wording but cannot establish that the answer is persuasive or coherent.

## 7. Learning material

1. Reader: a learner with the knowledge established by the lesson's context.
2. Purpose: explain a concept, support an interpretation or decision, or guide a concrete exercise.
3. Information: introduce unfamiliar terms before using them in examples or questions. When an abbreviation is new, introduce its full term, established Korean name where useful, and meaning before relying on the abbreviation. Keep paired new terms comparably defined, but do not re-teach familiar words. At a section boundary, read the preceding final sentence, heading, and next first sentence together; add a transition only when the relationship or prerequisite would otherwise be unclear. Keep the source's actual learning action and scope.
4. Tone: clear and suited to the requested written lesson or spoken script. For speech, review endings across the paragraph and connect them according to the real continuation, contrast, or conclusion. Place a connective where that relationship begins. Repeated endings are a review signal, not an automatic error; do not require a particular ending, alternate `요` and `다` mechanically, or treat one numeral style as universally correct.
5. Common errors: testing unexplained material, relying on an undefined term in a transition, and using a vague production verb instead of the learner's actual task. Remove a phrase such as `이번 영상에서는` only when it adds no useful scope. Remove question-shaped repetition only when it adds no learning action; retain meaningful recall questions and useful previews. Do not expand finding a denominator into calculating an entire metric merely to make an invitation sound more concrete.
6. Output: a lesson, script, or exercise in the requested form. Use an immediate invitation such as `계산해 봅시다.` when the calculation starts next. If prerequisite explanation comes first, a preview such as `먼저 뜻을 확인한 뒤 계산해 보겠습니다.` states the order. Preserve a completed conclusion rather than leaving it open merely to vary the rhythm.

## 8. Proposal or service introduction

1. Reader: someone deciding whether the proposed service addresses a real need or how it can help with their task.
2. Purpose: explain the confirmed difficulty, the proposed response, and any expected benefit the requested artifact needs to convey.
3. Information: start from what the audience is trying to accomplish and the user's account of what makes that difficult. Do not infer the problem backward from a feature or substitute an implementation difficulty for the audience's problem. When necessity matters, connect the difficulty to the decision or action it obstructs and explain what information or capability would help. Do not assume a goal or choice is already settled when finding it is the stated difficulty.
4. Tone: concrete, reader-facing prose. If an expected benefit is required, connect the feature and enabled action to the burden it could reduce or the opportunity, preparation, or decision it could improve. Merely reading information or making a plan is an action, not yet the benefit. Ground expectations in the confirmed design, distinguish them from observed results, and do not invent measurements, guaranteed success, or social effects.
5. Common errors: listing audience, problem, and features without explaining their relationship; hiding the actual function behind vague assistance; and repeating the author's expectations instead of explaining the projected change. State the supported action and object, but preserve uncertainty and genuine assistance when those are the meaning.
6. Output: connected prose that answers why the proposal is needed and what it offers. Check the actual saved passage, not just a checklist or reviewer explanation. Keep the reasoning framework private; do not impose fixed headings, a table, or an expected-benefits paragraph on every kind of document. If the user corrects the problem definition, return to the original account rather than repeating the narrowed interpretation in new words.
