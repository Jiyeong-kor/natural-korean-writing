# Korean Language Principles

Use this reference for sentence structure and lexical choices. A review signal calls for judgment, not automatic replacement. Apply each change only when the source's meaning and the requested scope remain intact.

## 1. Predicate frames and particles

Start with the predicate. Identify the actor or subject, the object, and any required complement, destination, condition, or means. Choose particles from those roles rather than from the nearest word.

1. Restore particles omitted in notes when the result is prose. For example, `자료를 접근할 수 있습니다` becomes `자료에 접근할 수 있습니다` when the intended action is accessing the material.
2. If the predicate changes, check its required components again. A noun that was an object may need a different particle or may no longer belong in the sentence.
3. Keep coordinated items parallel when they serve the same role. Do not force different roles into the same form merely to make a list look uniform.

## 2. Omission and reference

Omit a subject or object when the title, preceding sentence, or immediate context identifies it unambiguously. Repeating an established actor in every sentence can make Korean sound translated.

1. Restore the subject when the actor changes or responsibility could be confused. When the source says an editor revised sentences and a reviewer checked figures, `편집자는 문장을 다듬었고 검토자는 수치를 확인했습니다.` keeps those roles distinct. A clause describing a group's work can make that group the apparent actor of the next clause too. When the next action belongs to an individual, make the change clear through the wording or sentence structure. Do not require a repeated pronoun when the actor is already unambiguous.
2. Restore an object or concrete noun when more than one referent is plausible. Do not guess what `이것`, `해당 내용`, or `이 부분` refers to; use the supplied context or ask for the missing distinction.
3. Keep conditions, necessary adverbials, particles, and complements even when the subject can be omitted.
4. Do not insert an unspecified person, `시스템`, or `프로그램` solely to complete a sentence.
5. Keep the same proper noun for the same entity when naming it again clarifies the reference. Do not rotate names through synonyms or descriptive aliases merely to avoid repetition. Omit a repeated name only when the actor remains unambiguous.

## 3. Voice and actor changes across clauses

Trace each noun's role through linked clauses. When a passive clause makes the affected object its subject, a following active predicate may require a different actor. If the context does not clearly supply that actor, state a source-supported actor or recast the clauses consistently.

1. Use active wording when identifying the actor makes the responsibility or action clearer.
2. Keep passive wording when the actor is unknown, irrelevant, or less important than the affected object. `오류가 수정됐습니다.` can be appropriate when only the completed correction is known.
3. Do not invent an actor to avoid a passive construction. Conversely, do not remove a known actor when responsibility matters.
4. A change of voice is not itself an error. Check whether each predicate's subject and object remain clear, including subjects that Korean naturally omits.

## 4. Information order and logical connections

Begin with established context and introduce new information where the reader can connect it. Place a condition close to the action it limits. Preserve the source's time order, comparison, and causal direction rather than forcing every text into one fixed sequence.

1. Use a connective only for a supported relationship. `따라서` asserts a consequence, while `반대로` introduces a contrast; neither is a decorative transition.
2. Keep the main action visible. Split long modifiers or overlapping conditions when the reader otherwise has to reconstruct the relationship.
3. Keep multiple related judgments together when the sentence is clear. Sentence length or the number of clauses alone does not require a split.
4. Do not turn a sequence into a cause, a contrast into a supplement, or a possibility into a result while smoothing the connection.

## 5. Nominalization and abstract subjects

Review noun stacks, long modifiers, repeated demonstratives, and abstract nouns when they hide who does what. Rewrite the relationship with a verb when that makes the same meaning easier to follow.

1. `변경 사항에 대한 검토를 진행했습니다.` can become `변경 사항을 검토했습니다.` without changing the action.
2. Keep a nominal expression when the concept, category, or possession is the point. A genuine definition such as `교정은 글의 잘못된 부분을 바로잡는 일입니다.` does not need a different structure merely because it ends in `입니다`.
3. Treat a possessive expression such as `검토자의 판단` as a question about meaning, not a forbidden form. State the decision and its criteria when those are what the reader needs; retain the possessive when whose judgment it was matters.
4. A sentence beginning with `이 문서는` or another demonstrative can distinguish its subject. Remove it only when it repeats an already clear subject without adding a useful connection.

## 6. Relationship, speech level, and speech act

Follow the requested tone and the established relationship. Preserve a clear source register unless the user asks to change it. When the user speaks politely and requests no different style, keep the reply polite.

1. Align endings, pronouns, possessive expressions, forms of address, and requests. Adding a polite ending does not make the casual possessive `네` appropriate in a polite evaluation. Omit an unnecessary pronoun or choose wording that fits the relationship.
2. Do not make a casual exchange formal by default. `확인해 줘.` and `확인해 주세요.` fit different relationships; choose the form required by the context.
3. Preserve the speech act. A suggestion is not an order, and an intention is not a completed action. Do not introduce a promise merely to make a reply sound helpful.
4. For an ordinary listener-oriented commitment in a casual exchange, `확인할게.` usually fits better than the stronger resolve of `확인하겠어.` Keep the latter for deliberate resolve or inference. A formal commitment may use `확인하겠습니다.`

## 7. Word meaning and professional usage

Choose words by their exact sense, predicate pattern, and intended readers. Dictionary inclusion alone does not make a word suitable for every genre, and dictionary absence alone does not invalidate an established professional term.

Keep familiar terms such as `business logic` when a newly coined Korean replacement would be less precise or less familiar. Replace broad verbs such as `처리하다` with a narrower action only when the source establishes that action. When the supplied context establishes a specific operation, retain it rather than falling back to a broader word for brevity. An ambiguous editable draft does not override that context.

In ordinary Korean prose, prefer an established, familiar Korean name when it is equally precise, such as `안드로이드 앱`. A technical audience alone does not require English spelling. Preserve exact code, API names, filenames, URLs, quotations, and labels the reader must match, such as `AndroidManifest.xml`. Do not invent translations or add redundant English equivalents.

Concision does not justify insulting, military-style, violent, or speculative slang in assistant-authored explanations. Name the verified action with an exact neutral verb, such as `추가하다`, `수정하다`, `설치하다`, or `실행하다`; if the operation is unknown, state only what is known. Apply explicit user restrictions to the requested scope without presenting a personal word preference as universal grammar. Preserve source quotations and deliberately requested character voices rather than sanitizing protected text.

### Polysemous English verbs

Translate the actual action, not one English word in isolation.

1. **Fix and pin:** use `고치다` or `수정하다` for incorrect text, code, or errors; use `해결하다` for resolving a problem or vulnerability when that is the intended action. Use `고정하다` for holding a position, value, or reference fixed, including pinning a version or commit SHA. Do not treat every `fix` as `고정하다`.
2. **Close:** use `닫다` for a door, window, dialog, or an actual platform action called close. For a problem, inconsistency, discussion, or task, name the actual action: `문제를 해결하다`, `잘못된 내용을 수정하다`, `논의를 마무리하다`, or `작업을 완료하다`. Select among them from the source; do not imply resolution when the source establishes only that discussion ended.
3. **Classify and divide:** distinguish assigning a category to each target from partitioning a set or splitting an object. `대상이 어느 종류에 속하는지 결정하다` or `분류하다` fits category assignment; `나누다` or `분할하다` can fit an actual partition. Do not ban every occurrence of `종류로 나누다`, `중`, or `가운데` without checking the action and register.
4. **Dependency resolution:** when the source means choosing a dependency version, use `의존성 버전 결정` or `빌드 도구가 최종 선택한 의존성 버전`. Do not translate that action mechanically as `의존성을 해석하다`. Match the stage described by the source instead of treating selection, retrieval, and execution as the same action.

## 8. Calculation bases and comparison groups

State the actual calculation relationship: which value is the numerator or denominator, which group is compared, and what serves as the reference. Use a phrase such as `참여자 수를 분모로 두고 계산합니다.` only when that denominator is supported by the source.

Avoid spatial wording such as `출발하다` when it obscures a calculation basis and no movement or sequence begins. Retain it for actual movement or a process beginning. Rewording must not change the formula, population, comparison group, or calculation scope. Finding a denominator and calculating an entire metric are different tasks.

## 9. Facts, inferences, and proposals

Match certainty and tense to the evidence. `중복된 문장이 있습니다.` asserts a finding; `중복된 문장이 있을 수 있습니다.` states a possibility; `중복된 문장은 삭제하는 편이 좋겠습니다.` proposes a change. These are not interchangeable ways to vary the tone.

Keep the source's uncertainty when the cause is unconfirmed. State confirmed behavior directly, and do not turn a proposal, expected effect, or planned action into an observed result. When a suspected technical error cannot be resolved from the supplied facts within the requested scope, do not silently rewrite the claim as though it had been verified.
