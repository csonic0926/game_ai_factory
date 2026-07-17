# Craft — spoken-fluency（唸稿潤句）

Repair the sentence grammar of quoted spoken lines — and ONLY the sentence
grammar — so that every line is something a native speaker's mouth can
actually produce. Everything else is frozen: beat structure, pragmatic
function, information content, character voice, canon terms.

Origin: vinci_world dialogue production test (2026-07-13). The USER ruling:

> Story factory 的產出唯一問題就是文句不流暢。就算生成英文的，也是非常
> 古怪的句子。但 beat、情感、身份等等確實是正確的。以語言學的角度講，
> 是文法不對——factory 產出的句子文法是有問題的。

The disease: a worker that has spent its whole context on design reasoning
(beat duties, pragmatic functions, red-line self-checks) carries the
**compressed syntax of design annotation** into the quotation marks —
subjects and prepositions elided to a degree only written notes allow,
relative clauses stacked before nouns, verb collocations that exist in no
one's daily speech. The constraints all land (beat / emotion / identity
correct); the language layer fails because language was never any worker's
sole task.

## Architecture requirement — independent fresh worker

This craft MUST run as its own fresh worker. The worker that created the
lines must never perform this pass on them "while it's at it": the whole
point is that a context contaminated by a day of design reasoning cannot
hear its own annotation register. Same principle as review gates being
independent workers. This pass is a production step (integer-step side),
not a gate: it changes text; gates only judge.

## Input

1. One artifact containing quoted spoken lines. Typical: a CHAPTER STEP 6
   runtime draft, a STEP 8 quoted-dialogue revision (the touched timeline /
   locale rows), or a `dialogue-runway` / `quoted-dialogue` craft output.
   Any artifact with lines inside `「…」` / `"..."` qualifies.
   **Bare-lines rule**: when the artifact wraps its lines in design prose
   (per-line annotations, beat rationale), the caller extracts a bare line
   list — speaker + line + a one-line scene anchor per group — and
   dispatches THAT. The worker must not read the surrounding design
   annotation: a context marinated in annotation register cannot hear
   annotation register. The full artifact stays with the caller for
   merging the repairs back.
2. The adapter `STYLE_GUIDE.md`. If it has a spoken-grammar section (e.g.
   vinci_world §4.1「對白口語文法」), those project rules BIND this pass —
   read that section before touching a line. If the project has no such
   section, the generic rules below apply.
3. From the caller: the output path for the fluency log (see Output).
4. `<ADAPTER>/GLOSSARY.csv`, when available, belongs to the **caller and
   canon-aware back-check**, not to the clean-room worker. The caller extracts
   the current scene language's canon `dialogue_protected=true` forms and
   exact `banned` forms mechanically with
   `scripts/glossary_check.py --glossary <ADAPTER>/GLOSSARY.csv --extract-cleanroom <LOCALE> <artifact>`
   (plus repeated `--speaker` filters when needed). Missing glossary means
   `NOT_AVAILABLE` and preserves the former hand-picked/STYLE_GUIDE behavior.

## Freeze list (never change)

- beat structure and beat order — no line added, dropped, or reordered
- each line's pragmatic function (ask / warn / refuse / push / …)
- information content — no new reveal, no lost information, no
  strengthened or weakened claim
- character voice markers — sentence-final particles, verbal tics,
  short-vs-long sentence personality contrast, register differences
  between speakers
- canon / red-line wording (decided terms stay exactly as decided)
- when a glossary exists, every applicable canon
  `dialogue_protected=true` form supplied by the caller
- narration outside quotation marks
- in landed runtime files: routing, ids, keys, structure — text values of
  the touched dialogue fields only

**Carve-out — metaphor noun-skeletons are NOT protected.** The
information freeze protects what a line says, not a broken image's
anatomy. Two defects sit on the grammar side of the line and MUST be
acted on: (a) a stranded classifier — a measure word whose noun is
neither said nor recoverable from anything present in the scene; (b) an
image that imposes structure a canon entity does not have (e.g. levels
onto something the world defines as level-less). Repair the skeleton when
the image's job survives the repair; when it cannot (the image itself is
the defect), red-flag the line for the creation side with one line of
diagnosis — never silently keep it because "the metaphor is content".

## Clean-room rewrite mode（淨室重寫）— DEFAULT for draft-stage dialogue (2026-07-17)

Validated by ablation (owner-run experiments 2026-07-14): the register
disease is cured by taking the rewrite OUT of the design context, not by
piling on rules. Zero-shot suffices — the model's native spoken ear does
the work once the context is clean; exemplars demote to taste
calibration; world-model errors stay invisible in the clean room BY
DESIGN and belong to the canon gate. Flow:

1. **Clean-room worker.** Its ENTIRE context is plain-speech material,
   written like a director's note — nothing in design register. It
   contains ONLY: a one-line scene anchor; a one-line persona sketch;
   the draft lines; each line's job as one plain phrase; hard
   constraints as spoken rules (the glossary-derived protected terms,
   frozen lines verbatim, glossary-derived red-line words,
   no-acquisition promises); and any world facts the
   lines touch, one plain line each (facts don't contaminate; register
   does). NO craft docs, NO style guides, NO design artifacts, NO
   exemplar prose, NO file access. The worker rewrites the whole passage
   in one breath（一口氣）— not line-by-line patching — reads it aloud,
   and returns lines only, plus at most two flags.
   - Frozen lines = creative-layer decreed lines AND lines whose current
     text is already an owner repair (those are the script's current
     text, not teaching material).
2. **Canon back-check gate**（canon-aware, separate context）— it reads the
   glossary when available and runs `scripts/glossary_check.py` on the fluent
   artifact (with `--baseline` whenever separate before/after artifacts are
   available). Mechanical diff on the fluent text: protected terms present, frozen
   lines verbatim, red-line words absent, every line's job delivered;
   PLUS the world-model collocation check (imagery imposing structure a
   canon entity does not have — see the freeze-list carve-out). A
   violation bounces back to the clean room with ONE plain line naming
   only the violated constraint. Checking constraints on fluent text is
   cheap and mechanical; checking fluency on constraint-correct text
   needs the owner's ear — this ordering is the whole point.
3. **Owner's ear** — the cut. Owner repairs enter the project exemplar
   library as taste calibration (economy, word preferences), not as
   grammar rescue.

The per-line repair procedure below remains for landed runtime files
(where only the touched dialogue fields may change) and for small
touch-ups where a whole-passage rewrite is disproportionate.

The clean-room worker never reads `GLOSSARY.csv`, a style guide, shipped locale
catalogs, or any design file. The wrapper's extraction and the back-check are
what make glossary discipline mechanical without reintroducing design
register into the language context. Blank locale mappings and newly observed
world terms are reported as pending nominations; no worker may promote them.

## The work (per-line repair mode)

Go line by line through every quoted line, in every locale present.

1. **Read the line aloud（唸稿）.** Actually vocalize it — this is the
   writer's step, not a reviewer courtesy. If it knots, breaks breathing,
   or sounds like reading an annotation, it fails.
2. **Rewrite at sentence granularity.** The minimal unit of repair is the
   sentence, not the word. Patch-editing a broken sentence produces
   another broken sentence: split it, restore what speech needs, rebuild
   the clause.
3. Repair moves, in order of frequency:
   - split one overloaded sentence into two or three, with full stops
   - restore elided subjects and prepositions (who, from where, toward
     what)
   - unstack modifier clauses piled before a noun; drop zero-information
     modifiers entirely
   - swap invented verb collocations for the ones people actually say
4. Re-read the repaired line aloud. Then check it against the freeze
   list — if the repair moved a beat, a function, or a voice marker,
   back up and repair again within the freeze.

## Generic spoken-grammar rules

Derived from real owner-repair precedents (2026-07-13); project-agnostic —
the examples below are neutral constructions, not any project's content. A
project's own STYLE_GUIDE spoken-grammar section (and its exemplar
library) takes precedence and may extend these.

1. **Subjects and prepositions may not be elided past what speech
   allows.** Speech says who, from where, toward what.「你把窗簾拉開
   往外看」cannot compress to「窗簾拉開看出去」— the latter is
   annotation ellipsis, not something a mouth produces.
2. **At most ONE modifier clause before a noun; drop it if it carries no
   information.**「你住的這間房」— the listener already lives there;
   zero information, front-heavy sentence. Just「你的房間」.
3. **One information focus per sentence.** Two foci → two sentences,
   split with a full stop — never commas and dashes stringing three
   things into one line.
4. **Verb-object collocations must be ones heard in daily speech.**
   「亮出」takes a physical object (亮劍、亮牌), never「亮出喜歡」.
   When unsure, use the plainest verb (說、講、給你看). Self-test: have
   you heard this verb-object pair in a real conversation? If not, it's
   invented.
5. **Every locale gets its own native reading.** en / ko / any shipped
   locale passes through the same read-aloud repair under THAT language's
   native-speaker grammar intuition — this pass is not a Chinese-only fix.
   A locale must not come out more explanatory or more compressed than
   the others.

## The project exemplar library (the anchor)

Each project keeps its owner's repair precedents as paired lines
(original → repaired) in its OWN adapter — inside or beside the
STYLE_GUIDE spoken-grammar section (e.g. a「判例庫」subsection). Project
content never lives in this factory-side doc.

Before touching a line, the worker reads the project's ENTIRE exemplar
library aloud, pair by pair, and hears what changed. Rules are an
abstraction of the owner's ear; the exemplars ARE the ear.

**Exemplars are teaching data, NOT decreed content.** The worker derives
every repair itself from rules + exemplars. When a line under repair is
literally an exemplar's original, applying the exemplar reproduces the
owner's repair — that is the mechanism working, not authority being
copied. Never mark such repairs as "owner-decreed lines" in the output:
decreed lines exist only at the CREATIVE layer (a destination line a beat
sheet locks by design), never at the quality layer. An owner correction
enters the library and generalizes; it does not become a pasted quotation
with the owner's name on it.

A neutral illustration of what one exemplar pair teaches:

- original:「你住的這間房在走廊底——左邊是廚房，窗簾拉開看出去，就是山。」
- repaired:「你的房間在走廊底——左邊是廚房。你把窗簾拉開往外看，就是山。」

Same beat, same pragmatic function, same information, same voice. What
changed: one sentence became two, the elided subject and preposition came
back, the zero-information relative clause dropped. That is this craft's
entire scope.

## Output

1. The artifact with quoted lines revised in place (or, when the caller
   asks for a non-destructive dry-run, a copy at the caller-named path).
2. A fluency log at the caller-given path, containing:
   - one entry per changed line: original sentence → repaired sentence,
     plus ONE plain-language line stating the grammatical reason
     (e.g. "restored elided subject + split two foci") — this is what the
     review gate uses to verify the meaning was NOT changed;
   - a count of lines read and left unchanged;
   - honesty loop: end by naming the one or two repairs you are least
     confident about, so the next gate adjudicates them explicitly.
   - when a glossary exists: the mechanically extracted protected/banned
     forms, checker result, any speaker/register judgment, and any new-term
     `status=pending` nomination.

## Self-check before output

- Did I read every quoted line aloud, in every locale?
- Is every change syntactic — could someone diff the log and find a
  changed meaning, a moved beat, a softened function, a flattened voice?
  If yes, revert that change and repair within the freeze.
- Does every repaired line pass the project STYLE_GUIDE spoken-grammar
  rules (or the five generic rules above)?
- Does every changed line have its comparison entry in the log?

Never edit the sovereignty files (`WORLD_RULES.md`, `NARRATIVE_DELIVERY.md`,
or a legacy `WORKFLOW_CORE_VARIABLES.md`).
