---
name: natural-korean-writing
description: Write, rewrite, and review Korean that preserves meaning and fits its speaker, reader, situation, and purpose. Use for Korean conversations and reader-facing copy, including translated, stiff, repetitive, ambiguous, or contextually inappropriate wording. Before answering, read the full SKILL.md and its required references/context-audience-boundary.md; the description alone is not the writing guidance.
license: MIT
---

# Natural Korean Writing

Write Korean that belongs in its reading context. Improve expression without changing what the source says, who did it, or how certain it is. This skill supports Korean drafting, revision, and review; it is not a full-document translation or fact-checking service.

## Establish the reading context

Before drafting, rewriting, or reviewing any Korean, read this entire SKILL.md, then the entire bundled [context and audience companion](references/context-audience-boundary.md). It is mandatory, not an optional profile or a separately installed skill. A skill name, description, discovered link, or truncated excerpt does not complete this reading. Continue to the end of either file if a tool truncates it. Reuse a complete, unchanged reading already available in the current conversation; read again in a fresh conversation, after losing that context, or after the files change. If a required file is unavailable, state that limitation instead of claiming to have applied it.

Apply the two instructions before choosing words: establish whose words these are, to whom, when, where, through which channel, and for what purpose; check shared knowledge and disclosure boundaries. On a follow-up, apply the established context and reassess whatever changed. Reading the files is not sufficient: check the finished response against the supplied situation.

For instructions about the same target and scope, apply the user's latest explicit correction rather than an older plan, example, or skill default. Keep instructions for conversation, publication copy, and protected text distinct. A general style change does not authorize changing previously confirmed wording; that requires explicit permission for the affected wording.

Keep conversation style separate from artifact style. Preserve the user's chosen chat register; do not impose formal public-document prose on a casual reply or copy chat shorthand into an external email.

Distinguish labels from prose. Titles, buttons, tabs, and table labels can be short phrases. Put explanations in value cells or surrounding prose rather than turning table labels into questions. Prose needs enough structure to make the action and target clear, not a mechanically repeated subject.

## Protect meaning and exact text

1. Preserve facts, scope, ownership, measurements, intent, tone, terminology, uncertainty, and commitments. Do not add a cause, failure, result, or benefit merely to make the sentence more specific.
2. Preserve user-confirmed wording exactly, including spaces and punctuation, unless the user explicitly authorizes changing it. This takes precedence over punctuation correction and stylistic polishing.
3. Identify protected literals before rewriting: code, identifiers, filenames, paths, URLs, commands, options, branches, versions, regular expressions, API values, and official names or quotations whose spelling must be reproduced. Preserve their characters exactly. A familiar Korean name in ordinary prose may identify the same entity without changing it; do not substitute names inside protected text. A quoted sentence explicitly submitted for rewriting is editable; a quotation to reproduce is not.
4. Keep facts, inferences, and proposals distinct. A request to polish wording does not authorize changing technical claims or expanding a calculation's scope. If supplied facts conflict or a missing referent changes the meaning, identify the uncertainty rather than inventing an answer.
5. Apply an explicit expression ban to the user's entire stated output scope. For an exact-string ban, check the assembled text for that substring, including occurrences inside longer words; a plausible context is not an exception. If the ban includes a verb's inflected forms or a sentence-ending pattern, check those forms and patterns rather than only the dictionary spelling or one sample sentence. Do not evade a banned pattern by changing its spacing or swapping it for an equally empty formula. Preserve the facts and unbanned words or forms rather than broadening the ban to unrelated words. Follow an explicit later authorization to change affected locked copy while preserving other protected text. An explanatory quotation in a rule or test fixture is a separate deliverable from the manuscript unless the user includes it in the ban's scope.
6. When the user specifies quotation marks for a particular name, check every mention within the specified scope, including later mentions and names followed by particles. Keep the particle outside the name's marks and preserve the name's spelling and requested quote characters. Normalize each complete existing quoted span instead of blindly wrapping the name: replace misplaced marks with one opening and one closing mark around the name, remove the displaced marks, and leave the particle outside. Inspect the characters immediately before and after each occurrence for doubled, unmatched, or leftover quotes. Respect a first-mention-only instruction when that is the actual scope; do not quote unrelated names by inference. A local word substitution is not a universal language correction or a new global ban. Apply only the authorized changes and compare the remaining protected text exactly.

Use supplied context and explicit corrections to resolve a vague or inaccurate draft; preserving meaning does not mean preserving the draft's ambiguity. Before rewriting a status report or responsibility description, identify the relevant actor, concrete action, target, and completed, ongoing, or planned state. Carry those distinctions into the requested result. Do not add unrelated background facts or require a separate status explanation when the reader does not need one.

Before deleting or softening a sentence, identify what it contributes to the reader: a reason, a supported claim of ability, a choice, a qualification, or a necessary connection. Concision and modesty must not remove the author's central intended claim. Distinguish having studied something, expecting to perform it well, and deciding to attempt it; none proves the others. Interpret an educational or cultural reference from the supplied original and context rather than converting it into a different competence or motive. When a material interpretation remains unknown, preserve the distinction or ask instead of silently choosing a flattering or cautious story.

## Match the relationship

Check endings, pronouns, possessive expressions, forms of address, and requests together. Preserve a clear source relationship. In a polite conversation, use consistently polite wording; in a casual conversation, do not introduce honorifics without a reason.

For a polite evaluation, `제안해 주신 문장이 더 자연스럽습니다.` is appropriate when that is the intended judgment. Do not use `네 문장이 낫습니다.` as its polite model.

## Check Korean structure and word choice

Read [Korean language principles](references/korean-language-principles.md) when checking particles, predicate frames, omissions, referents, information order, or lexical meaning, including ambiguous English verbs such as `fix` and `close`.

Treat noun stacks, long modifiers, unnecessary passive wording, repeated demonstratives, and abstract nouns that hide actions as review signals, not banned forms. Revise only when the context supports a clearer, meaning-preserving sentence. Keep established professional terminology when an invented translation would be less exact or less familiar.

In a report, résumé, or other account of completed work, do not default to repeated `검증했습니다`, `검증 결과`, or `검증 자료` when readers need to know what was checked. Describe the actual target and method, and the observed result when it is known. Prefer a concrete action such as checking a condition, comparing results, or running a test when the source supports that action. Retain `검증` when it accurately names a formal process or established technical term. Do not invent a test, passing result, or broader quality claim to make a vague sentence more specific.

Read [official Korean sources](references/official-korean-sources.md) when a lexical or normative question needs evidence. Do not look up every ordinary sentence or claim usage trends from a corpus you have not inspected.

## Check meaning before surface fluency

Check whether each predicate can express the supplied action with its actual subject, object, and complements. Correct particles and complete sentence endings do not make an incompatible verb-object combination natural. Resolve the intended action from context instead of replacing a flagged word with a fixed synonym. Preserve valid literal and figurative uses; examples are not blacklists.

For Korean originals, draft and review in Korean without requiring an invented English intermediate. For translations, use an actual source when available to check meaning, then reread the Korean alone as the intended reader. A plausible English back-translation does not prove that the Korean is natural, and a later comparison text is not the original source.

When the user flags an awkward sentence, diagnose the failed meaning or reader relationship before polishing it. Check the affected paragraph, not only the quoted phrase. An abstract assessment is not a substitute for a concrete reason, a chronological sequence is not a cause, and a writer's form-filling explanation is not automatically part of the reader-facing answer. Use the relevant application guidance and fictional examples below; do not retain the same unsupported story with smoother wording.

## Choose the artifact profile

Read the relevant section of [artifact style profiles](references/artifact-style-profiles.md) for conversations, technical explanations, GitHub text, UI copy, email, portfolios or resumes, learning material, and proposals or service introductions.

When creating or checking Korean document or PDF layout, also apply the shared layout section in that reference, regardless of the document's content profile.

For application essays or a set of application answers, also read the entire [application answer workflow](references/application-answer-workflow.md) before selecting experiences or revising answers. It carries the full question and guidance through evidence selection, review, and the exact final text. Its form and file operations apply only when those actions are authorized and the required tools are available.

Apply spoken-lesson guidance only when writing that kind of material. Do not turn one script's preferred endings, number notation, or sequence into a universal rule for Korean.

## Apply punctuation

Before finalizing any visible Korean, read and apply [Korean punctuation rules](references/korean-punctuation-rules.md). This reference is mandatory, not an optional style profile. Keep the protected literals and confirmed copy identified above unchanged.

## Deliver the requested result

First distinguish text to use from commentary about that text. A request to write what someone will actually say, send, or post asks for usable copy, even without the words "final" or "only." Instructions about what to explain to the recipient govern that copy; they do not ask the assistant to explain its drafting choices to the writer.

For usable copy, return one settled version for each requested situation, with only necessary identifying labels. Correct an error before delivery; replace the wrong draft rather than retaining it alongside a correction. Omit generic introductions, self-evaluation, unsolicited alternatives, follow-up offers, and explanations of how the wording was chosen. When the requested deliverable is a review or an explanation, give that reasoning or teaching content without claiming facts not in the source.

When asked for final copy after successive edits, provide the complete affected field with all accepted changes. Preserve confirmed wording and read the assembled paragraph for duplication and broken connections; do not leave the user to combine fragments.

Preserve the requested platform format. For structural examples, read [rewrite examples](references/rewrite-examples.md); use their reasoning, not their sentences as universal templates.

## Final pass

Read the entire response, including headings, introductions, notes, and closing remarks, then check:

1. Compare the actual output with the supplied context and requested corrections, not only the editable draft. Meaning, facts, ownership, certainty, commitments, confirmed copy, and protected literals remain intact.
2. Particles, predicates, required complements, and changes of actor are clear. Trace each linked clause to its actor, and check that a known action has not become vague wording such as `작업` or `처리` merely to shorten the text.
3. The speaker, relationship, timing, setting, and intended act fit the supplied situation. Terminology and explanation fit the reader and artifact; apply the mandatory context companion to the actual wording.
4. Each sentence belongs to the requested deliverable. A correct draft followed by unrequested working notes is not final copy; remove drafting history, date-calculation steps, and explanations of disclosure decisions unless the requested artifact needs them.
5. The mandatory punctuation reference and requested output format are satisfied.
6. Reread the Korean as a standalone text in its intended register. Check predicate-object compatibility, collocations, clause relationships, and paragraph progression, not only spelling or banned-word searches. If a reader must mentally add a reason or transition, restore the source-supported relationship rather than merely inserting a decorative connective.
7. The actual sentences answer the artifact's central question. Grammatical sentences and the presence of topic words do not establish a missing relationship, need, or benefit; do not supply that meaning only in the review explanation.

For a full audit, read every heading, paragraph, table cell, caption, and visible image label in context. Keep a private coverage record; keyword searches identify candidates, not completion. A local wording correction still requires checking the affected paragraph and related passages for meaning and duplication. When saving or posting is part of the authorized task, read the saved text again, including carried-over paragraphs. Report any inaccessible region instead of claiming an exhaustive review.


### Independent review when requested or established

Reading the writing rules is preparation, not evidence that the finished copy follows them. Treat an established user instruction to obtain independent review as part of subsequent applicable revisions; do not wait for the user to repeat it. When that review is authorized and an appropriate separate reviewer is available, require the reviewer to read this SKILL.md, the context companion, punctuation reference, and relevant artifact guidance before reviewing. Provide the exact question, source facts, latest user corrections, protected wording, complete draft, and applicable length limit with its counting convention within the permitted disclosure scope. Where available, use a reviewer without the writer's full reasoning history so it evaluates the actual materials rather than inheriting the writer's conclusions. Ask the reviewer to judge the draft against those materials, including what each sentence contributes and whether the intended claim survived editing, rather than merely endorse the writer's explanation. Reconcile findings with the source; a reviewer may not override confirmed wording without authorization. Recheck the revised whole text after accepted fixes. If a separate reviewer is unavailable or has not returned findings, report that state and do not label self-review as independent review. This instruction does not itself authorize sharing private material with an external service or creating new tasks.

Before delivering a revision, compare the previous draft with the new draft against the latest correction. Check both what changed and what disappeared: a wording fix must not silently remove the central claim, a necessary transition, accepted facts, or an authorized commitment. Resolve relevant independent findings, then recheck the assembled answer; if a material finding remains unresolved, do not present it as a finished review. When the user asks to inspect application answers in chat, show each exact question with its complete answer and checked character count or clearly stated counting limitation, rather than sending them back to the form. If the user explicitly requests only the answer text, omit the question and count from the delivered copy while still checking them internally. Do not claim a revised answer was saved or submitted merely because it was drafted.
