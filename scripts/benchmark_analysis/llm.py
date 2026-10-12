"""Evidence-led explanations for the published 2026-09-27 LLM evaluations.

Published points always come from site_data.  Worker narratives explain observed
outcomes, not replacement scores.  The five relative Proficiency metrics are
cross-checked against the exact reused generation records before raw facts are
displayed.  A different run requires a fresh review of the authored observations.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


RUN_ID = "2026-09-27-38b7137-gh31"
REPOSITORY = "https://github.com/quidra-lang/quidra"


def _observation(explanation: str, facts: dict[str, str], *caveats: str) -> dict:
    return {
        "explanation": [explanation],
        "facts": [{"label": label, "value": value} for label, value in facts.items()],
        "caveats": list(caveats),
    }


LEARNABILITY = {
    "condition.i1_keyword_anonymization": {
        "title": "Keyword anonymization",
        "description": "Apply grammar rules after familiar keywords have been replaced by supplied pseudo-words.",
        "count": "three independent seeds",
        "group": "i1-i2",
        "note": "The observed first-attempt successes alone do not explain Quidra's four-point gap: its worker applied an additional discount. The individual records below preserve that distinction.",
        "languages": {
            "Quidra": _observation(
                "All three recorded sum-above-threshold programs compiled and printed 26 on the first attempt. The worker nevertheless reported 96 after applying a four-point discount for token efficiency that it had not separately measured.",
                {"First-attempt successes": "3 / 3", "Recorded seed scores": "100, 100, 100", "Repairs used": "0"},
                "The seed scores average 100, while the published condition is 96. The fixed token-efficiency weights total only three points; the worker's four-point discount is not an independently reproducible application of the specified formula.",
            ),
            "Python": _observation(
                "Each of three keyword mappings produced a working top_two function on the first attempt. Every function passed all five held-out tests, so the worker awarded 100 to every seed and reported their mean as 100.",
                {"First-attempt successes": "3 / 3", "Held-out tests": "15 / 15", "Seed scores": "100, 100, 100"},
                "The worker treated short, correct single-function solutions as ceiling token efficiency; it did not publish comparative token measurements for this condition.",
            ),
            "C++": _observation(
                "The keyword-anonymized sumEven, maxOfThree and countPositive tasks all compiled on the first attempt and produced their expected outputs, 30, 7 and 4. No repair was needed, and all three recorded seed scores were 100.",
                {"First-attempt successes": "3 / 3", "Expected outputs matched": "30; 7; 4", "Repairs used": "0"},
                "The worker described token efficiency as nominal from completion lengths; a separate twelve-component numeric record is not committed.",
            ),
            "Rust": _observation(
                "All three translations from pseudo-keywords compiled and ran without repair. The tasks exercised a sum and parity check, a slice maximum, and enum matching for areas; the worker assigned 100 to each seed.",
                {"First-attempt successes": "3 / 3", "Seed scores": "100, 100, 100", "Example result": "Maximum of slice: 9"},
                "For the geometry seed, the expected result was re-derived from the generated source rather than listed as an independently frozen oracle. The full component arithmetic is not recorded.",
            ),
            "Go": _observation(
                "The three reverse-mapped programs built and matched the expected SumEven, MaxOf and ReverseString outputs: 12, 9 and olleh. The worker converted each compile-and-output pass to a seed score of 100.",
                {"Compile and output passes": "3 / 3", "Seed scores": "100, 100, 100", "Expected outputs matched": "12; 9; olleh"},
                "The worker explicitly used one binary pass/fail result as a proxy for all twelve metrics; repair, token and other component scores were not independently measured.",
            ),
            "Java": _observation(
                "All three programs correctly translated the keyword glossary, compiled with javac and printed 30 for the even-number sum. They used the real standard output call and required no repair, which the worker scored as 100 for each seed.",
                {"First-attempt successes": "3 / 3", "Output per seed": "30", "Repairs used": "0"},
                "The worker states that all twelve components received full credit, but does not supply comparative token counts or separate unseen-case results.",
            ),
            "TypeScript": _observation(
                "Each of three translated solve functions returned distinct even numbers in ascending order. All compiled with tsc and passed five unseen cases covering empty input, negatives, duplicates, odd-only input and descending order.",
                {"First-attempt successes": "3 / 3", "Unseen tests": "15 / 15", "Seed scores": "100, 100, 100"},
                "Token efficiency was assigned a 100 baseline for short single-shot completions rather than calculated from comparative token counts.",
            ),
            "Kotlin": _observation(
                "All three clampValue implementations translated the pseudo-keywords correctly, compiled, and printed 5 0 10. No pseudo-keyword leaked into the Kotlin source and no repair was needed; each seed received 100.",
                {"First-attempt successes": "3 / 3", "Output per seed": "5 0 10", "Repairs used": "0"},
                "The worker declares every applicable component maximal but does not preserve a separate numeric record for all twelve components.",
            ),
            "Swift": _observation(
                "The primality, factorial and digit-reversal programs all compiled and matched their expected outputs on the first attempt. The record shows three seed scores of 100 and no repair calls.",
                {"First-attempt successes": "3 / 3", "Tasks": "Primality; factorial; digit reversal", "Repairs used": "0"},
                "The record supports the build and output successes, but does not itemize all twelve weighted component scores.",
            ),
        },
    },
    "condition.i2_vocabulary_anonymization": {
        "title": "Vocabulary anonymization",
        "description": "Learn renamed standard-library and builtin operations as well as renamed grammar keywords.",
        "count": "three independent seeds",
        "group": "i1-i2",
        "note": "Quidra eventually solved all three tasks, but its initial attempts and additional repairs lowered the published composite. The six tied leaders recorded first-attempt success for all three of their seeds.",
        "languages": {
            "Quidra": _observation(
                "All three initial sortedEvens attempts failed to compile. The model invented free-function append/sorted calls instead of methods; two seeds also introduced Python-style colons or C-style braces and loops. All three became correct after 1, 1 and 2 repairs. The recorded seed totals 62, 62 and 48 average to 57.33.",
                {"Initial successes": "0 / 3", "Final successes": "3 / 3", "Repairs by seed": "1, 1, 2", "Seed scores": "62, 62, 48"},
                "The record supplies seed totals and qualitative penalties, but not the twelve numeric component scores needed to verify how 62 and 48 were derived.",
            ),
            "Python": _observation(
                "The three vocabulary-anonymized top_two solutions all parsed and passed five held-out tests on the first attempt. No repair or invented API was reported, and every seed received 100.",
                {"First-attempt successes": "3 / 3", "Held-out tests": "15 / 15", "Repairs used": "0"},
                "The worker awarded ceiling token efficiency for concise correct solutions without publishing comparative token measurements.",
            ),
            "Rust": _observation(
                "The model correctly translated the supplied vocabulary into vector sorting, word counting with a hash map, and descending collection operations. All three programs compiled and ran on the first attempt, with no repairs and three recorded scores of 100.",
                {"First-attempt successes": "3 / 3", "Seed scores": "100, 100, 100", "Example result": "[6, 5, 4, 3, 2, 1]"},
                "The worker describes successful programs, but does not publish the separate twelve-metric arithmetic behind the composite.",
            ),
            "Java": _observation(
                "All three programs mapped the renamed output and modulo operations back to System.out.println and %. They compiled and printed 30 without using invented zant.blenk or wibmod APIs, earning three recorded scores of 100.",
                {"First-attempt successes": "3 / 3", "Output per seed": "30", "Repairs used": "0"},
                "All components were declared maximal; comparative token counts and separate unseen-case results are not recorded.",
            ),
            "TypeScript": _observation(
                "The model correctly reconstructed length, deduplication, sorting and filtering from behavioral descriptions. All three solve functions compiled and passed all five unseen edge-case tests on their first attempt, so each seed received 100.",
                {"First-attempt successes": "3 / 3", "Unseen tests": "15 / 15", "Repairs used": "0"},
                "Token efficiency was assigned a 100 baseline for short single-shot code, without comparative token measurements.",
            ),
            "Kotlin": _observation(
                "All three sumOfSortedRange implementations used real Kotlin operations for the renamed printing, length, range, sort and map vocabulary. They compiled and printed [0, 1, 2, 3, 4] followed by 10 without repair.",
                {"First-attempt successes": "3 / 3", "Seed scores": "100, 100, 100", "Repairs used": "0"},
                "The worker declares every applicable component maximal but does not provide a separate twelve-component numeric record.",
            ),
            "Swift": _observation(
                "The model reconstructed filtering, sorting, counting, ranges and mapping from renamed vocabulary. Each of the three programs compiled and matched its expected result on the first attempt, including the filtered and sorted even values [2, 8].",
                {"First-attempt successes": "3 / 3", "Seed scores": "100, 100, 100", "Repairs used": "0"},
                "The build and output results are recorded; all twelve weighted component values are not itemized.",
            ),
        },
    },
    "condition.i3_structural_surface_perturbation": {
        "title": "Structural surface perturbation",
        "description": "Follow unfamiliar delimiters, separators or operator spellings while preserving the original program meaning.",
        "count": "two independently generated transformation sets",
        "group": "i3-i4",
        "note": "Quidra ties the four highest comparison languages. All five records report two first-attempt successes, although the transformations and validation detail differ between workers.",
        "languages": {
            "Quidra": _observation(
                "Both transformation sets used three reversible substitutions involving call separators, grouping and an operator. After reverse mapping, the generated programs ran successfully and printed 25 and then 1 followed by 0. Both recorded scores were 100.",
                {"Successful sets": "2 / 2", "Substitutions per set": "3", "Repairs used": "0"},
                "The worker records output checks but does not supply every component needed to reproduce the twelve-metric composite.",
            ),
            "Python": _observation(
                "The two perturbed programs were correctly translated into clamp and sum_evens functions. The clamp tests covered an interior value and both bounds; sum_evens passed an ordinary input and an empty list. Both sets passed without repair.",
                {"Successful sets": "2 / 2", "Recorded function assertions": "5 / 5", "Repairs used": "0"},
                "No complete twelve-component score breakdown is committed for these two sets.",
            ),
            "C++": _observation(
                "Both ordinary C++ translations compiled and preserved the specified computation after delimiter and declaration-marker perturbations. The sum-of-squares task printed 91 and the product task printed 120, with no repairs.",
                {"Successful sets": "2 / 2", "Expected outputs matched": "91; 120", "Repairs used": "0"},
                "The worker says the runner will compute the complete composite, but its committed record contains no twelve-component runner input.",
            ),
            "TypeScript": _observation(
                "Both sets changed three surface elements. The translations passed strict tsc checks on the first attempt, and the worker marked both as preserving the intended semantics, leading to the reported 100.",
                {"Strict compile checks": "2 / 2", "Substitutions per set": "3", "Repairs used": "0"},
                "The record gives compile commands and semantic-preservation flags, but no executed-case results or complete twelve-component calculation.",
            ),
            "Swift": _observation(
                "Both translations compiled and produced the required sums and products, 7 and 30, without repair. The worker recorded 100 for each set.",
                {"Successful sets": "2 / 2", "Expected outputs matched": "7; 30", "Repairs used": "0"},
                "The worker describes three transformation axes in one set and four in the other, and notes partial retention of ordinary surface forms in the second. It does not publish the complete component calculation.",
            ),
        },
    },
    "condition.i4_novel_rule_generalization": {
        "title": "Novel-rule generalization",
        "description": "Apply a newly invented marker or naming rule that is supplied in the reference pack and removed before ordinary execution.",
        "count": "one primary trial",
        "group": "i3-i4",
        "note": "Quidra and all four tied leaders satisfied their recorded synthetic rule on the first attempt. This condition preserves recognizable language syntax, so structural familiarity can still help.",
        "languages": {
            "Quidra": _observation(
                "The generated program correctly marked the reassigned total_mut binding and left the unchanged threshold unmarked. The worker validated the overlay before stripping it; the resulting Quidra program printed 5 and 100 on the first attempt.",
                {"Primary trials": "1", "Marker validation": "Passed", "Output after stripping": "5; 100"},
                "The successful rule and output checks are explicit; a complete twelve-component numeric derivation of 100 is absent.",
            ),
            "Python": _observation(
                "The accumulate function obeyed the new mutation-marker rule and produced 7 for inputs 3 and 4. An AST validator checked the marker, and the worker also records positive and deliberately unmarked negative controls.",
                {"Primary trials": "1", "Marker validation": "Passed", "Positive and negative controls": "Passed"},
                "The committed record documents functional and marker success, but does not itemize the twelve weighted component values.",
            ),
            "C++": _observation(
                "The square function received the required PURE-RETURN comment and the reference-mutating increment function received MUTATING. The program compiled and printed 36; removing the comments preserved its meaning.",
                {"Primary trials": "1", "Marker checks": "2 / 2", "Expected output matched": "36"},
                "The record supports rule compliance and execution but does not include the full twelve-component arithmetic.",
            ),
            "TypeScript": _observation(
                "The model added qz_ to the numeric function containing mutable let state and correctly withheld it from the pure function. The rule checker and strict tsc compilation both passed on the first attempt.",
                {"Primary trials": "1", "Functions classified correctly": "2 / 2", "Strict compile check": "Passed"},
                "The worker records the rule checker and compilation, but no complete twelve-component calculation or runtime-case details.",
            ),
            "Swift": _observation(
                "The model placed return-type marker comments above square and isEven, and omitted one above the Void-returning greet function. The mechanical checker passed, and the compiled program produced 16, Hello, World! and false.",
                {"Primary trials": "1", "Function marker checks": "3 / 3", "Repairs used": "0"},
                "The complete twelve-component score calculation is not itemized in the committed summary.",
            ),
        },
    },
    "condition.i5_held_out_rule_composition": {
        "title": "Held-out rule composition",
        "description": "Combine individually taught rules in combinations that were withheld from the worked examples.",
        "count": "one primary trial",
        "group": "i5-i6",
        "note": "Quidra's worker describes a failed composition and a successful one, while the four tied leaders report successful combinations. The reported 34 and 100 totals have specific replication or arithmetic limitations identified below.",
        "languages": {
            "Quidra": _observation(
                "One recorded task combined mutable references, elif branches and compound assignment successfully, printing 45, 70, 95 and 25. The other attempted those rules but invented a to-based loop and an implicit main entrypoint. The worker penalized that syntax failure and reported a composite of 34.",
                {"Recorded successful trials": "1 / 2", "Successful combination": "Mutable reference + elif + compound assignment", "Failed attempt": "Invented loop and entrypoint syntax"},
                "The record lists two trials although the frozen primary configuration specifies one. The first failure was judged from source inspection without a compiler invocation, and the twelve numeric component scores behind 34 are missing.",
            ),
            "Rust": _observation(
                "The single program correctly combined doubling, filter-and-reverse, and windowed sums into the withheld A+C, B+C and A+B+C cases. It compiled and produced the hand-checked outputs without repair; the worker published 100.",
                {"Recorded trials": "1", "Withheld combinations passed": "3 / 3", "Repairs used": "0"},
                "The listed components give source and total token efficiency 90, with every other component 100. Applying the specified weights yields 99.70, not the published 100; the discrepancy is retained as an evidence limitation.",
            ),
            "Go": _observation(
                "Both recorded programs correctly composed the separately taught INC, DBL and NEG operations. Each printed 6, -1 and -3 for the three held-out programs, leading the worker to assign 100.",
                {"Recorded successful trials": "2 / 2", "Compositions per trial": "3", "Expected outputs matched": "6; -1; -3"},
                "Two trials are recorded where the primary configuration specifies one. The worker also redistributed repair weights instead of giving no-repair trials the specified full repair credit; all remaining values were 100, so this shortcut did not change its reported total.",
            ),
            "Java": _observation(
                "The single trial combined negation-hoisting, sum-flattening and product-order rules into the previously unseen A+B+C case. The Java harness compiled and verified the exact canonical expression mul(j, add(neg(g), h, i)), supporting the reported 100.",
                {"Primary trials": "1", "Held-out A+B+C combination": "Passed", "Compile and harness checks": "Passed"},
                "Repair components are marked not needed rather than given numeric values. The record reports 100 for all other components, without separate comparative token evidence.",
            ),
            "Swift": _observation(
                "The single trial correctly combined repeatCollect, filterKeep and joinDash into A+C, B+C and A+B+C functions. The generated Swift passed assertions for all three combinations and printed I5_OK without repair.",
                {"Primary trials": "1", "Withheld combinations passed": "3 / 3", "Repairs used": "0"},
                "The worker explicitly calculated this total as Correct@1 × 100. That is a reported shortcut, not an independently recorded twelve-metric composite.",
            ),
        },
    },
    "condition.i6_prior_conflict_resistance": {
        "title": "Prior-conflict resistance",
        "description": "Follow a supplied counterfactual mapping when familiar tokens or names suggest a conflicting meaning.",
        "count": "one primary trial",
        "group": "i5-i6",
        "note": "Quidra's recorded attempts reverted to foreign syntax under keyword swaps. The leaders followed their respective counterfactual rules, but the records use different kinds of mapping and do not support treating every 100 as an identical test.",
        "languages": {
            "Quidra": _observation(
                "Neither recorded attempt produced valid Quidra. A for/while swap led to C-style braces, semicolons and loops; an int/string swap produced func declarations, arrow return types and toString calls. The worker awarded 12 for partial task engagement and algorithmic intent despite those failures.",
                {"Recorded compile successes": "0 / 2", "Mappings": "for/while; int/string", "Observed failure": "Reversion to foreign syntax"},
                "Two trials are recorded where the primary configuration specifies one, and the component values behind 12 are missing. A worker's manual rewrite only checked algorithmic intent; it was not a successful model completion.",
            ),
            "Rust": _observation(
                "The model followed deliberately misleading function names: sum_all returned the maximum, filter_max negated values, and identity_map sorted descending. The single program compiled and produced all four expected results without repair, and the worker reported 100.",
                {"Primary trials": "1", "Counterfactual functions checked": "4", "Repairs used": "0"},
                "The listed token components are 92 with all others 100, which weights to 99.76 rather than 100. This task remapped function meanings rather than permuting Rust grammar keywords.",
            ),
            "Go": _observation(
                "Both programs obeyed the swapped plus/minus meanings and strict left-to-right evaluation. Each produced the four expected results, 7, 13, 17 and 11, with no observed prior-conflict failure; the worker assigned 100.",
                {"Recorded successful trials": "2 / 2", "Checks per trial": "4", "Expected outputs matched": "7; 13; 17; 11"},
                "The primary configuration specifies one trial, while this record includes two. The task swaps arithmetic operations in a small interpreter, so its surface challenge differs from Quidra's grammar-keyword swaps.",
            ),
            "Java": _observation(
                "The model correctly treated the toy language's if token as a loop and its for token as a conditional. The translated Java compiled and printed 0, 1 and 2, matching the supplied counterfactual specification on the single trial.",
                {"Primary trials": "1", "Expected output matched": "0; 1; 2", "Compile and run checks": "Passed"},
                "Repair components are marked not needed and the remaining components 100; separate comparative token evidence is not supplied.",
            ),
            "Swift": _observation(
                "The model followed conflicting meanings assigned to loop, branch, sum and product in the task wording. The generated compute function matched an independent reference on two arrays, producing 30 for each, without repair.",
                {"Primary trials": "1", "Reference comparisons": "2 / 2", "Repairs used": "0"},
                "The mapping was applied only to English task wording, not to Swift source tokens. The worker calculated Correct@1 × 100 rather than preserving the complete twelve-metric composite.",
            ),
        },
    },
}


PROFICIENCY = {
    "metric.generation_success_rate": (
        "Generation success rate",
        "Whether the model returns a non-empty, complete initial answer.",
        "100 × qualifying initial completions / 18 trials. Compilation and correctness are evaluated separately.",
        "All ten languages tie at 100. Producing an answer earns this row's credit even when that answer cannot compile.",
    ),
    "metric.compile_parse_success_rate": (
        "Compile / parse success rate",
        "Whether the initial generated program passes the frozen build or parse command.",
        "100 × first completions that compile or parse / 18 trials. A later successful repair does not change this first-attempt metric.",
        "Java leads this requirement even though Python leads the overall proficiency evaluation.",
    ),
    "metric.correct_at_1": (
        "Correct@1",
        "Whether the first program passes every public and hidden oracle case.",
        "100 × fully correct first completions / 18 trials. A public example alone is insufficient.",
        "The gap comes from first-attempt working programs: Python passed 16 of 18, while no initial Quidra program compiled.",
    ),
    "metric.correct_at_n": (
        "Correct@N",
        "Whether a trial produces a fully correct program within the fixed attempt budget.",
        "100 × trials with a fully correct source at any allowed attempt / 18. N is at most four: one initial answer and three repairs.",
        "All six tied leaders eventually produced a fully correct source in every trial. Quidra exhausted the same repair allowance without one.",
    ),
    "metric.test_pass_rate": (
        "Test pass rate",
        "The proportion of oracle cases passed across all scored initial and repair calls.",
        "100 × passed public and hidden cases / all scored public and hidden cases. Failed attempts remain in the denominator.",
        "This rate is below Python's final success rate because earlier failed attempts still count. The case totals below are reconstructed from the frozen case counts and recorded repair history.",
    ),
    "metric.repair_success_rate": (
        "Repair success rate",
        "How often an initially failing program reaches the public repair gate after feedback.",
        "100 × later public-gate successes / trials that initially failed compilation or public tests. Hidden cases never create a repair opportunity; no needed repairs would score 100.",
        "The six tied leaders repaired every eligible failure, but they needed different numbers of turns. Repair efficiency and diagnosis efficiency show that difference.",
    ),
    "metric.repair_efficiency": (
        "Repair efficiency",
        "Reward successful completion earlier within the repair budget.",
        "Per trial: first-attempt public-gate success scores 100; success after repair k scores 100 × (1 − k/4); an unrepaired failure scores 0. Average all 18 trials.",
        "Python's two repaired trials cost one and two turns. Quidra never crossed the public repair gate, so every trial contributed zero.",
    ),
    "metric.diagnosis_efficiency": (
        "Diagnosis efficiency",
        "Whether the first trusted diagnostic is enough for a successful repair.",
        "100 × trials passing the public repair gate on the first repair / trials initially needing repair. No needed repairs would score 100.",
        "Rust and Go fixed every eligible failure on their first repair. Their observed failures were mostly source-formatting defects.",
    ),
    "metric.silent_bug_resistance": (
        "Silent-bug resistance",
        "Avoid programs that run successfully but return an incorrect oracle result.",
        "Among first completions that compile and execute oracle cases: 100 × (eligible trials − silent-bug trials) / eligible trials. With no eligible trials, score 0.",
        "Quidra's zero is the specified no-eligible-program result. It does not mean that every Quidra program ran and silently returned a wrong answer.",
    ),
    "metric.syntax_hallucination_resistance": (
        "Syntax hallucination resistance",
        "Avoid inventing language constructs or APIs that do not exist in the evaluated language.",
        "Worker judgment from preserved source and diagnostics. This is one of the two proficiency metrics that are not computed entirely by the runner.",
        "TypeScript ties Python here despite failing every initial build: its worker attributed those errors to Node typing gaps rather than fabricated syntax.",
    ),
    "metric.specification_compliance": (
        "Specification compliance",
        "Honor the task's protocol and requirements, including constraints beyond a single output example.",
        "Worker judgment from preserved programs and task evidence; the published score is not a separately complete mechanical compliance checklist.",
        "Python, C++ and Kotlin receive full credit in this judged row. Their final programs succeeded even when initial programs required repair.",
    ),
    "metric.prompt_robustness": (
        "Prompt robustness",
        "Maintain first-attempt correctness when the same task is presented in different orders.",
        "For each of three equivalent prompt layouts, compute full-oracle first-attempt successes across six workload/scenario cells; publish the lowest of the three rates.",
        "Java's weakest layout still passed five of six cells. All three Quidra layouts had zero successful first attempts.",
    ),
    "metric.unseen_case_generalization": (
        "Unseen-case generalization",
        "Pass hidden inputs that were not supplied as prompt examples.",
        "100 × hidden cases passed by first completions / 42 frozen hidden cases. The denominator is six trials each for two SVM, two GMM and three LightGrad hidden inputs.",
        "This first-attempt metric excludes repair gains. Python's published full-precision score corresponds to 38 of 42 hidden cases; Quidra passed none.",
    ),
    "metric.source_token_efficiency": (
        "Source token efficiency",
        "How compact the terminal source completion is in provider-counted output tokens.",
        "For each exact trial cell, score 100 × lowest source-token count / this language's count; average the 18 cell scores. Count failed terminal attempts as well as successful ones.",
        "Normalize each matched trial before averaging. A ratio of overall mean token counts would produce a different result, and a short failed program can still receive token-efficiency points.",
    ),
    "metric.total_token_efficiency": (
        "Total token efficiency",
        "How many model-visible tokens the complete task consumes, including feedback and repairs.",
        "For each trial, sum provider input, cache and output tokens through stopping; score 100 × lowest task-token count / this language's count; average all 18 trials.",
        "Quidra used all three repairs in every trial. Python needed repairs in only two trials, producing a much lower recorded task-token cost.",
    ),
    "metric.generated_code_performance": (
        "Generated code performance",
        "Runtime of the first fully correct program produced in each trial.",
        "Use median oracle-case wall time for each fully correct source, normalize as 100 × fastest valid time / measured time in that trial, then average 18 trials. A trial with no fully correct source scores 0.",
        "Quidra's zero is a failure to produce a measurable correct program. It is not a runtime-speed measurement of the language itself.",
    ),
    "metric.generated_code_memory_efficiency": (
        "Generated code memory efficiency",
        "Peak memory of the fully correct generated programs under the frozen harness.",
        "Use median child peak RSS from separate oracle-case replays; normalize 100 × lowest valid memory / measured memory per trial, then average all 18 trials. No fully correct source gives 0.",
        "Rust leads by a small measured margin. Quidra has no valid generated-program memory sample because none of its trials produced a fully correct source.",
    ),
    "metric.generated_code_compile_performance": (
        "Generated code compile performance",
        "Time spent in the frozen build or parse step for fully correct generated programs.",
        "Normalize each successful build/parse wall time as 100 × fastest valid time / measured time, then average all 18 trials. No fully correct source gives 0.",
        "Python's parse/build command was fastest in all 18 matched cells. This compares the prescribed commands, whose work differs across compiled and interpreted languages.",
    ),
}


# These counts summarize the cited worker records; full-oracle final success is
# independently checked against the immutable per-trial raw records below.
TRIALS = {
    "Quidra": {"first": 0, "repair": 18, "final": 0, "detail": "All initial programs failed compilation, and all 18 trials consumed three repairs without reaching the public repair gate."},
    "Python": {"first": 16, "repair": 2, "final": 18, "detail": "Sixteen initial programs passed; the SVM specification trial needed one repair and the GMM specification trial needed two."},
    "C++": {"first": 12, "repair": 6, "final": 18, "detail": "Six initial sources included Markdown fences that caused compile errors. All six repeated the formatting error once and passed on their second repair."},
    "Rust": {"first": 14, "repair": 4, "final": 18, "detail": "Four initial sources included Markdown fences that rustc rejected; all four passed after the first repair removed the formatting defect."},
    "Go": {"first": 13, "repair": 5, "final": 18, "detail": "Five initial sources failed the package-declaration parse check because of leading stray tokens. All five passed on their first repair."},
    "Java": {"first": 15, "repair": 3, "final": 16, "detail": "One initial GMM source contained Markdown fences; two SVM programs compiled but disagreed with the required numeric output."},
    "TypeScript": {"first": 0, "repair": 18, "final": 11, "detail": "Every initial build failed; the worker attributed the failures to Node typing gaps. Eleven trials eventually produced a fully correct source."},
    "Kotlin": {"first": 13, "repair": 5, "final": 18, "detail": "Five initial sources included Markdown fences that caused top-level declaration errors. All five passed on their second repair."},
    "Swift": {"first": 9, "repair": 9, "final": 18, "detail": "Nine trials needed repair after initial compile or public-output failures. All ultimately passed within the three-turn repair budget."},
    "Zig": {"first": 0, "repair": 18, "final": 0, "detail": "All trials produced candidate source, but obsolete standard-library calls and occasional Markdown fences kept them from compiling even after repair."},
}

RELATIVE = {
    "metric.source_token_efficiency": "source_tokens",
    "metric.total_token_efficiency": "task_completion_tokens",
    "metric.generated_code_performance": "generated_code_performance_seconds",
    "metric.generated_code_memory_efficiency": "generated_code_memory_bytes",
    "metric.generated_code_compile_performance": "generated_code_compile_seconds",
}


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _slug(name: str) -> str:
    return "c" if name == "C++" else name.lower()


def _source(label: str, path: str, ref: str) -> dict:
    return {"label": label, "url": f"{REPOSITORY}/blob/{ref}/{path}"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"LLM benchmark analysis: {message}")


def _load_raw(core: Path, site: dict) -> tuple[dict, dict]:
    """Follow this run's cache references; never select an arbitrary generation."""
    run = core / "benchmark" / site["run_id"]
    usage = _load(run / "cache_usage.json")["hits"]
    versioned = _load(run / "versioned_scores.json")["evaluations"]["llm_proficiency"]
    provenance = _load(run / "provenance.json")
    config_path = core / "benchmark/template/config/primary.json"
    _require(hashlib.sha256(config_path.read_bytes()).hexdigest() == provenance["primary_config_sha256"], "primary configuration does not match this run")
    workload_path = core / "benchmark/template/methodology-assets/llm_proficiency/workloads.json"
    workload_hash = hashlib.sha256(workload_path.read_bytes()).hexdigest()
    result = {}
    trial_identity = None
    for language in site["languages"]:
        name, language_id = language["name"], language["id"]
        _require(versioned["current_generations"].get(name) == language_id, f"generation differs for {name}")
        hit = usage[f"proficiency-trials--{_slug(name)}"]
        _require(hit["scope"] == language_id, f"cache scope differs for {name}")
        record_path = core / "benchmark/cache" / hit["record"]
        retained = _load(record_path)
        projected = _load(record_path.with_name(hit["fingerprint"] + ".json"))
        generation_path = record_path.with_name("generation.json")
        generation = _load(generation_path)
        _require(retained["fingerprint"] == record_path.stem, f"retained fingerprint differs for {name}")
        _require(projected["fingerprint"] == hit["fingerprint"], f"run fingerprint differs for {name}")
        _require(projected["provenance"]["run_id"] == site["run_id"], f"projected record is not from this run for {name}")
        _require(generation["generation_id"] == language_id, f"raw generation differs for {name}")
        _require(generation["source_run_id"] == retained["provenance"]["run_id"], f"raw source run differs for {name}")
        raw = generation["normalization_raw"]
        for key in ("workload_contract_sha256", "primary_trial_set_sha256"):
            _require(raw[key] == retained["certification"]["proficiency_" + key] == projected["certification"]["proficiency_" + key], f"certified {key} differs for {name}")
        _require(raw["workload_contract_sha256"] == workload_hash, f"workload asset differs for {name}")
        if trial_identity is None:
            trial_identity = raw["primary_trial_set_sha256"]
        _require(raw["primary_trial_set_sha256"] == trial_identity, f"trial set differs for {name}")
        _require(len(raw["trials"]) == 18, f"expected 18 raw trials for {name}")
        correct = sum(row["fully_correct_source_available"] is True for row in raw["trials"].values())
        _require(correct == TRIALS[name]["final"], f"fully correct trial count changed for {name}")
        result[language_id] = {"trials": raw["trials"], "path": generation_path.relative_to(core).as_posix(), "source_run_id": generation["source_run_id"]}

    # Reproduce explanatory arithmetic without ever replacing published points.
    ids = [language["id"] for language in site["languages"]]
    trial_ids = set(result[ids[0]]["trials"])
    _require(all(set(result[language_id]["trials"]) == trial_ids for language_id in ids), "raw trial identifiers differ")
    for metric, key in RELATIVE.items():
        totals = {language_id: [] for language_id in ids}
        for trial_id in sorted(trial_ids):
            values = {language_id: result[language_id]["trials"][trial_id][key] for language_id in ids}
            available = [value for value in values.values() if isinstance(value, (int, float)) and value > 0]
            _require(bool(available), f"no valid {key} measurement for {trial_id}")
            best = min(available)
            for language_id, value in values.items():
                if value is None:
                    _require(metric.startswith("metric.generated_code_") and result[language_id]["trials"][trial_id]["fully_correct_source_available"] is False, f"unexplained missing {key} for {language_id}/{trial_id}")
                    totals[language_id].append(0.0)
                else:
                    _require(isinstance(value, (int, float)) and value > 0, f"invalid {key} for {language_id}/{trial_id}")
                    totals[language_id].append(100.0 * best / value)
        for language_id in ids:
            published = versioned["normalized_metric_scores"][metric][language_id]
            _require(math.isclose(sum(totals[language_id]) / 18, published, abs_tol=1e-8), f"raw measurements do not reproduce {metric}/{language_id}")
    return result, versioned


def _raw_facts(metric: str, language_id: str, raw: dict) -> dict:
    key = RELATIVE[metric]
    trials = raw[language_id]["trials"]
    values = [row[key] for row in trials.values() if row[key] is not None]
    correct = sum(row["fully_correct_source_available"] for row in trials.values())
    if not values:
        return _observation(
            "None of the 18 trials produced a fully correct source. The runner therefore assigns zero to every trial in this physical-efficiency metric; the raw measurement fields are empty because there is no valid program to time or profile.",
            {"Fully correct generated programs": f"{correct} / 18", "Valid physical measurements": "0", "Score rule applied": "18 failed trials × 0"},
            "This zero does not measure the speed, memory use or build latency of a correct Quidra implementation.",
        )
    best_cells = 0
    for trial_id, row in trials.items():
        candidates = [block["trials"][trial_id][key] for block in raw.values() if block["trials"][trial_id][key] is not None]
        best_cells += row[key] == min(candidates)
    low, high, mean = min(values), max(values), sum(values) / len(values)
    if key.endswith("tokens"):
        range_value = f"{low:,.0f}–{high:,.0f} tokens"
        mean_value = f"{mean:,.2f} tokens"
    elif key.endswith("seconds"):
        range_value = f"{low * 1000:.3f}–{high * 1000:.3f} ms"
        mean_value = f"{mean * 1000:.3f} ms"
    else:
        range_value = f"{low:,.0f}–{high:,.0f} bytes"
        mean_value = f"{mean:,.2f} bytes"
    facts = {"Raw range across trials": range_value, "Mean raw measurement": mean_value, "Lowest raw value in matched cell": f"{best_cells} / 18", "Fully correct generated programs": f"{correct} / 18"}
    if metric == "metric.source_token_efficiency":
        text = "The terminal source completions used " + range_value + ". The requirement averages the source-token ratios within all 18 matched trials; each final attempt is counted even when it is incorrect."
    elif metric == "metric.total_token_efficiency":
        text = "The complete trials consumed " + range_value + " each, including prompts, repeated context, feedback and outputs. The score averages the 18 comparisons with the cheapest language in each matching trial."
    elif metric == "metric.generated_code_performance":
        text = f"All 18 trials produced correct programs. Their median oracle-case wall times ranged from {range_value}; the language was fastest in {best_cells} of 18 matched cells, which explains its high mean normalized runtime score."
    elif metric == "metric.generated_code_memory_efficiency":
        text = f"All 18 correct programs had recorded memory measurements between {range_value}. The language had the lowest peak-RSS value in {best_cells} cells and stayed close to the minimum in the rest, producing the highest mean score."
    else:
        text = f"The frozen build/parse command took {range_value} for the 18 correct programs. It was fastest in every matched cell, so each cell scored 100 and the average is 100."
    return _observation(text, facts)


def _proficiency_observation(metric: str, name: str, language_id: str, raw: dict, counts: dict) -> dict:
    trials = TRIALS[name]
    if metric in RELATIVE:
        result = _raw_facts(metric, language_id, raw)
        if name == "Quidra" and metric == "metric.source_token_efficiency":
            result["explanation"].append("The model's compact failed attempts still receive some token credit; none of these 18 trials produced a correct program.")
        if name == "Quidra" and metric == "metric.total_token_efficiency":
            result["explanation"].append("All 18 trials consumed the initial call plus three repairs: 72 calls in total. That repeated cost drives the score close to zero.")
            result["caveats"].append("The worker estimated roughly 10,000–20,000 tokens per trial. The retained provider-counted raw values are substantially higher and are the measurements used here.")
        if name == "Python" and metric == "metric.source_token_efficiency":
            result["explanation"].append("The successful terminal programs are comparatively short. This row measures their completion size; repair overhead is included separately in total token efficiency.")
        if name == "Python" and metric == "metric.total_token_efficiency":
            result["explanation"].append("Sixteen trials needed only one completion; just two needed repairs. That limited the repeated prompts, diagnostics and outputs included in total task cost.")
        if metric == "metric.generated_code_memory_efficiency" and name == "Rust":
            result["caveats"].append("The runner reports 99.77 for Rust and 99.75 for Python. This small margin describes the frozen harness measurements, not an established general memory advantage.")
        return result

    if metric == "metric.generation_success_rate":
        return _observation(
            "All 18 initial requests returned a qualifying non-empty completion, giving 100 × 18/18 = 100. " + trials["detail"],
            {"Qualifying initial completions": "18 / 18", "Scored workloads": "SVM; GMM; LightGrad", "Scenarios per workload": "2"},
        )
    if metric == "metric.compile_parse_success_rate":
        if name == "Quidra":
            return _observation(
                "None of the 18 initial sources passed the real Quidra build/parse gate. The worker reports invented C/Rust-style forms, inappropriate imports and entrypoint or declaration syntax errors. The first-attempt fraction is therefore 0/18.",
                {"Initial compile / parse successes": "0 / 18", "Repair allowance": "3 turns per trial"},
                "Some later attempts compiled but produced no required output. The worker gives an inconsistent count for those attempts, so that count is not used here.",
            )
        return _observation(
            "Seventeen of the 18 initial Java programs compiled. The sole reported compile failure was a GMM source containing literal Markdown fences, which javac rejected. The two SVM output mismatches did compile and therefore do not lower this row.",
            {"Initial compilations": "17 / 18", "Initial compile failures": "1", "Calculation": "100 × 17/18 = 94.44"},
        )
    if metric == "metric.correct_at_1":
        if name == "Quidra":
            return _observation("All 18 first completions failed compilation, so none could pass the complete oracle. The recorded syntax and declaration failures prevented any first-attempt correctness credit.", {"Fully correct initial programs": "0 / 18", "Initial compile successes": "0 / 18"})
        return _observation("Sixteen of the 18 initial Python programs passed the complete oracle. The two specification-to-implementation trials that needed repair were SVM trial 2 and GMM trial 2, giving 100 × 16/18 = 88.89.", {"Fully correct initial programs": "16 / 18", "Trials initially needing repair": "2", "Calculation": "100 × 16/18 = 88.89"})
    if metric == "metric.correct_at_n":
        return _observation(
            f"The retained raw record marks {trials['final']} of 18 trials as having a fully correct source within the allowed attempts. " + trials["detail"],
            {"Trials with a fully correct source": f"{trials['final']} / 18", "Maximum attempts per trial": "4"},
        )
    if metric == "metric.test_pass_rate":
        if name == "Quidra":
            return _observation(
                f"No attempt produced an oracle-passing output. All four allowed calls were consumed in every trial, so the frozen case counts imply {counts['initial_cases'] * 4} scored cases and zero passes.",
                {"Reconstructed oracle cases passed": f"0 / {counts['initial_cases'] * 4}", "Recorded model calls": "72", "Final successful trials": "0 / 18"},
                "The complete per-call oracle traces are not committed; the denominator is reconstructed from the frozen case set and the documented full repair budget.",
            )
        denominator = counts["initial_cases"] + counts["SVM"] + 2 * counts["GMM"]
        return _observation(
            f"Python's 18 initial calls cover {counts['initial_cases']} cases. One additional SVM call and two additional GMM calls add {denominator - counts['initial_cases']}; the final published ratio corresponds to {counts['initial_cases']} of {denominator} passing case executions. Earlier compile failures remain in that denominator even though every trial was eventually solved.",
            {"Reconstructed case executions passed": f"{counts['initial_cases']} / {denominator}", "Recorded model calls": "21", "Calculation": f"100 × {counts['initial_cases']}/{denominator} = 86.96"},
            "The worker's prose describes final public success as 100, but that is not the published all-attempt case metric. Full case traces are not committed; the displayed counts are reconstructed from the task and repair records.",
        )
    if metric == "metric.repair_success_rate":
        success = 0 if name == "Quidra" else trials["repair"]
        return _observation(
            f"Of {trials['repair']} trials that failed the initial public repair gate, {success} reached it on a later allowed completion. " + trials["detail"],
            {"Eligible trials repaired": f"{success} / {trials['repair']}", "Maximum repair turns": "3"},
        )
    if metric == "metric.repair_efficiency":
        if name == "Quidra":
            return _observation("Every trial remained below the public repair gate after all three repairs. Each unrepaired failure contributes zero, so the mean of the 18 trial scores is zero.", {"Unrepaired trials": "18 / 18", "Repair calls consumed": "54", "Mean trial credit": "0"})
        return _observation(
            "Sixteen first-attempt successes contribute 100 each. The SVM repair succeeds at k=1 for 75 points, and the GMM repair at k=2 for 50 points. Their mean is (16 × 100 + 75 + 50) / 18 = 95.83.",
            {"First-attempt trial credits": "16 × 100", "Repaired trial credits": "75; 50", "Calculation": "1,725 / 18 = 95.83"},
            "The worker's explanatory sentence incorrectly prints 98.06 for this arithmetic. Its listed inputs and the published score agree on 95.83.",
        )
    if metric == "metric.diagnosis_efficiency":
        success = 0 if name == "Quidra" else trials["repair"]
        return _observation(
            f"The first repair succeeded in {success} of {trials['repair']} eligible trials. " + trials["detail"],
            {"Successful first repairs": f"{success} / {trials['repair']}", "Diagnostic source": "Compiler errors and public test failures"},
        )
    if metric == "metric.silent_bug_resistance":
        if name == "Quidra":
            return _observation("No initial source compiled, leaving zero first completions eligible for a silent-bug check. The frozen formula explicitly returns zero in that situation rather than awarding unearned full resistance.", {"Eligible initial programs": "0", "Observed initial runtime population": "No compiled programs", "No-eligible-trials rule": "Score 0"})
        return _observation(
            f"The worker reports no successful-exit wrong-output run among {trials['first']} compiling first completions. The published runner score gives full resistance for that eligible population; initial formatting or compile failures are excluded from it.",
            {"Eligible first completions reported": str(trials["first"]), "Silent-bug trials reported": "0", "Calculation": f"100 × ({trials['first']} − 0)/{trials['first']} = 100"},
            "Worker summaries expose public outcomes, while the complete hidden-oracle traces are not committed for independent case-by-case inspection.",
        )
    if metric == "metric.syntax_hallucination_resistance":
        if name == "Quidra":
            return _observation("The worker judged resistance as zero after observing invented foreign-language syntax, imports of automatically available standard namespaces, entrypoint misuse and incorrect declaration forms. Those source-level mistakes explain the judgment beyond the numeric compile-failure rate.", {"Judged score": "0 / 100", "Initial build failures": "18 / 18", "Observed defect types": "Invented syntax; namespace and declaration misuse"}, "This is a worker judgment; no separate numeric hallucination rubric is committed.")
        if name == "TypeScript":
            return _observation("The worker found real TypeScript/Node constructs rather than fabricated syntax or APIs in the initial completions. It attributed their build failures to missing Node type declarations and assigned 100 for hallucination resistance.", {"Judged score": "100 / 100", "Initial build successes": "0 / 18", "Worker's explanation": "Typing gaps rather than invented syntax"}, "The qualitative distinction is recorded by the worker; a formal cross-language hallucination predicate is not available.")
        return _observation("The worker assigned Python 100 and described the solutions as compact, idiomatic single-file programs. Sixteen initially passed and all eighteen eventually succeeded; the record does not attribute the two initial failures to invented Python constructs.", {"Judged score": "100 / 100", "Initially correct trials": "16 / 18", "Eventually correct trials": "18 / 18"}, "The worker does not provide a separate per-trial hallucination checklist, so this 100 cannot be reconstructed as an independent mechanical count.")
    if metric == "metric.specification_compliance":
        if name == "Quidra":
            return _observation("The worker awarded zero because no trial produced a program with the required output or a successful public repair result. Invented declarations and incomplete working bodies prevented the attempted solutions from satisfying the task contract.", {"Judged compliance": "0 / 100", "Trials with a fully correct source": "0 / 18"}, "The worker uses observed program failure as its compliance basis; no separate non-output constraint checklist is committed.")
        return _observation(
            "The worker awarded full compliance after the final solutions met the workload protocol. " + trials["detail"],
            {"Judged compliance": "100 / 100", "Trials with a fully correct source": "18 / 18", "Initially correct trials": f"{trials['first']} / 18"},
            "No separate checklist of every non-output constraint is committed. The final-success evidence supports the judgment but does not independently reproduce the complete compliance rubric.",
        )
    if metric == "metric.prompt_robustness":
        if name == "Quidra":
            return _observation("Canonical, scenario-first and contract-first prompts each had zero fully correct initial programs across their six cells. Taking the minimum of those three zero rates produces zero.", {"Canonical layout": "0 / 6", "Scenario-first layout": "0 / 6", "Contract-first layout": "0 / 6"})
        return _observation("Each of Java's three prompt layouts passed five of six cells. The two SVM numeric-output failures and the GMM fenced-source failure were spread across the three layouts, so the weakest rate is also 5/6 = 83.33.", {"Canonical layout": "5 / 6", "Scenario-first layout": "5 / 6", "Contract-first layout": "5 / 6"}, "Some other totals in the worker's narrative are inconsistent. These layout results agree with the published first-attempt total of 15/18 and robustness score.")
    if metric == "metric.unseen_case_generalization":
        if name == "Quidra":
            return _observation("No first completion compiled, so none passed a hidden case. The frozen denominator still includes all 42 hidden inputs across the 18 trials; build failures do not remove cases or earn generalization credit.", {"Hidden cases passed": f"0 / {counts['hidden_cases']}", "Initial compilations": "0 / 18"})
        return _observation("The published full-precision ratio and the frozen 42-case denominator give 38 hidden passes. The two initially failing specification trials account for the four missing SVM/GMM hidden-case passes; successful repairs do not change this first-attempt metric.", {"Hidden cases passed": f"38 / {counts['hidden_cases']}", "Calculation": "100 × 38/42 = 90.48", "Measurement point": "First completion only"}, "The numerator is reconstructed from the published full-precision score and fixed denominator. Complete hidden-case execution logs are not committed.")
    raise ValueError(f"No reviewed proficiency explanation for {metric}/{name}")


def build(core: Path, site_data: dict, source_ref: str) -> list[dict]:
    """Build both evaluations, using published rounded scores to select all ties."""
    _require(site_data.get("run_id") == RUN_ID, "authored observations require review for a different run")
    core = Path(core)
    run_rel = f"benchmark/{site_data['run_id']}"
    run = core / run_rel
    manifest = _load(run / "import_manifest.json")["retained_files_sha256"]
    raw, versioned = _load_raw(core, site_data)
    config = _load(core / "benchmark/template/config/primary.json")
    prof_config = config["llm_proficiency"]
    _require(prof_config["max_repair_turns"] == 3 and prof_config["independent_trials_per_replicated_cell"] == 3, "proficiency trial budget changed")
    workloads = _load(core / "benchmark/template/methodology-assets/llm_proficiency/workloads.json")["workloads"]
    counts = {name: len(workloads[name]["trusted_tests"]) for name in prof_config["primary_workloads"]}
    per_workload = len(prof_config["primary_scenarios"]) * prof_config["independent_trials_per_replicated_cell"]
    counts["initial_cases"] = per_workload * sum(counts.values())
    counts["hidden_cases"] = per_workload * sum(sum(test["id"] != "public" for test in workloads[name]["trusted_tests"]) for name in prof_config["primary_workloads"])
    _require(counts["initial_cases"] == 60 and counts["hidden_cases"] == 42, "reviewed oracle-case universe changed")
    # Verify reconstructed counts against the authoritative full-precision ratios.
    score_map = versioned["normalized_metric_scores"]
    python_id = next(language["id"] for language in site_data["languages"] if language["name"] == "Python")
    _require(math.isclose(score_map["metric.test_pass_rate"][python_id], 100 * 60 / 69, abs_tol=1e-10), "Python reconstructed case count differs")
    _require(math.isclose(score_map["metric.unseen_case_generalization"][python_id], 100 * 38 / 42, abs_tol=1e-10), "Python reconstructed hidden count differs")
    result = []
    evidence_checked = set()
    for evaluation in site_data["evaluations"]:
        evaluation_id = evaluation["id"]
        if evaluation_id not in ("llm_learnability", "llm_proficiency"):
            continue
        learn = evaluation_id == "llm_learnability"
        requirement_rows = []
        for requirement in evaluation["requirements"]:
            requirement_id = requirement["id"]
            metadata = LEARNABILITY[requirement_id] if learn else PROFICIENCY[requirement_id]
            best = max(requirement["scores"][language["id"]] for language in site_data["languages"] if language["name"] != "Quidra" and language["id"] in requirement["scores"])
            selected = [language for language in site_data["languages"] if language["name"] == "Quidra" or requirement["scores"].get(language["id"]) == best]
            languages = []
            for language in selected:
                name, language_id = language["name"], language["id"]
                filename = f"worker-learnability-{metadata['group']}--{_slug(name)}.json" if learn else f"worker-proficiency-trials--{_slug(name)}.json"
                evidence_rel = f"evidence/{evaluation_id}/{filename}"
                if evidence_rel not in evidence_checked:
                    payload_bytes = (run / evidence_rel).read_bytes()
                    _require(hashlib.sha256(payload_bytes).hexdigest() == manifest[evidence_rel], f"committed evidence hash differs: {evidence_rel}")
                    payload = json.loads(payload_bytes)
                    _require(name in payload["assigned_languages"] and requirement_id in payload["requirements"], f"worker evidence assignment differs: {evidence_rel}")
                    evidence_checked.add(evidence_rel)
                if learn:
                    reviewed = metadata["languages"][name]
                    observation = {"explanation": list(reviewed["explanation"]), "facts": [dict(fact) for fact in reviewed["facts"]], "caveats": list(reviewed["caveats"])}
                else:
                    observation = _proficiency_observation(requirement_id, name, language_id, raw, counts)
                    _require(round(versioned["normalized_metric_scores"][requirement_id][language_id], site_data["precision_decimals"]) == requirement["scores"][language_id], f"published proficiency score differs: {requirement_id}/{name}")
                sources = [
                    _source("Published requirement scores", f"{run_rel}/breakdown/{evaluation_id}.json", source_ref),
                    _source(f"{name} trial observations", f"{run_rel}/{evidence_rel}", source_ref),
                    _source("Scoring methodology", f"benchmark/template/methodology/{evaluation_id}.md", source_ref),
                ]
                if learn and requirement_id.startswith(("condition.i5", "condition.i6")):
                    sources.append(_source("Frozen primary trial counts", "benchmark/template/config/primary.json", source_ref))
                if not learn and (requirement_id in RELATIVE or requirement_id == "metric.correct_at_n"):
                    sources.append(_source("Retained per-trial measurements", raw[language_id]["path"], source_ref))
                    sources.append(_source("This run's measurement reuse", f"{run_rel}/cache_usage.json", source_ref))
                if not learn and requirement_id in ("metric.test_pass_rate", "metric.unseen_case_generalization"):
                    sources.append(_source("Frozen oracle case counts", "benchmark/template/methodology-assets/llm_proficiency/workloads.json", source_ref))
                languages.append({"id": language_id, "name": name, "score": requirement["scores"][language_id], **observation, "sources": sources})
            if learn:
                method = f"The specified method uses {metadata['count']}. Each trial combines twelve task metrics with fixed weights; the condition is their mean. The records below state where the published worker arithmetic or trial count does not fully follow that specification."
                title, description, notes = metadata["title"], metadata["description"], [metadata["note"]]
            else:
                title, description, method, note = metadata
                notes = [note]
                if requirement_id in RELATIVE:
                    notes.append("These raw measurements were retained from the 25 September run for the same language versions and reused in this 27 September publication. Their certified workload and trial identities match, and recomputing the per-cell ratios reproduces the published score.")
            requirement_rows.append({"id": requirement_id, "title": title, "description": description, "method": method, "comparison_notes": notes, "languages": languages})
        if learn:
            introduction = "These six conditions test how the recorded model applies supplied language rules under renamed vocabulary, unfamiliar surfaces and new rules. The published comparisons use the frozen Quidra 0.3.0 run. The worker records also expose differing exercises, scoring shortcuts and missing arithmetic; those limits are stated alongside the concrete successes and failures."
            aggregation = "The published total is 20% keyword anonymization + 20% vocabulary anonymization + 15% surface perturbation + 20% novel rules + 15% held-out composition + 10% prior-conflict resistance. Each condition is specified as a twelve-metric composite: compile 7%, Correct@1 18%, Correct@N 8%, test pass 15%, repair success 8%, repair efficiency 6%, compliance 10%, hallucination resistance 8%, silent-bug resistance 10%, unseen cases 7%, source tokens 1%, total tokens 2%."
        else:
            introduction = "The recorded model implemented SVM, GMM and LightGrad in two scenarios, with three fresh prompt-layout trials per cell: 18 trials per language and at most three repairs each. Quidra returned an initial answer in every trial but never produced a fully correct program. The rows distinguish that observed outcome from token cost, worker judgments and physical measurements; they describe this model and frozen run rather than a general language limitation."
            aggregation = "Eighteen fixed weighted metrics produce the total. Correct@1 and silent-bug resistance each weigh 12%; test pass 10%; repair success, hallucination resistance and compliance 7% each; unseen cases 6%; Correct@N, repair efficiency, diagnosis efficiency and prompt robustness 5% each; generation and compile success 4% each; source tokens, total tokens and runtime 3% each; memory and compile performance 1% each. Sixteen metrics are runner-owned; hallucination resistance and compliance are worker judgments. Full conversation and oracle traces are not committed, while worker observations and the retained raw efficiency measurements are available."
        result.append({"id": evaluation_id, "introduction": introduction, "aggregation": aggregation, "requirements": requirement_rows})
    _require(len(result) == 2, "expected both LLM evaluations")
    return result
