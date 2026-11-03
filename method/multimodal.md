# Sequential vs multimodal reasoning (from the author's two papers; operating rules for the engine)

Sources, kept in full in `method/papers/`: *Research Proposal: Identifying Multimodal Reasoning in LLMs
and Humans* (Taylor, Mar 2026) and *Atypical Reasoning Relationships: Multimodal Thinking* (Taylor,
Apr 2026).

## The distinction

Sequential reasoning holds one line at a time and reports it in order: "show the steps, do it in order,
break it down." Multimodal reasoning holds the relationships at once — space, time, scale, repetition,
sequence, geometry, pattern, linearity, angularity, process — and the order of a report is chosen
afterwards, for the listener. The sequence is an output format, not the structure. "Reason step by step"
is an instruction that changes how the information is processed in the first place; it is not neutral.

The finger problem. Asked to show 2 + 2 = 4 with hands: one student holds up four fingers (the result);
one holds two on each hand (the parts, counted); the author holds two on each hand, puts them together,
moves two fingers across and lowers the empty hand (the process, merged). All three land on four. Only
the third shows the operation. 5 − 2 and 1 + 4 also land on the same value by different processes; the
value can be reused later only if the process that produced it is preserved, because the inversions,
faces and turns of the tesseract act on the process, not on the number. A correct process read out of its
context is routinely labelled wrong ("5 + 6" for "5 of 7, plus 2 of 7, and 4 of 4").

Definition by range. A definition that pins a point needs constant revision; a definition that gives the
range the data can occupy includes the atypical cases and constrains them at the same time. "Too
literal" is what a hyper-literal reading of wording-as-constraint looks like from outside; it is also
the reading under which the wording is actually tested.

Unexpected results are where the structure shows. Anomalies in a study (inkblots seen in motion;
results that "conflict with the initial understanding") are not noise to average away; they are the
places where a different relationship to the data is visible. Behavior, not range, decides.

Relationship summaries are compressed. "Oh, it's the tortoise and the hare" for velocity–time graphs is a
correct understanding stated at low resolution; read out of context it looks nonsensical. A compressed
statement is unfolded before it is judged, never rejected for being compressed.

Fluency is not evidence. Trained agreement (RLHF, masking) makes an answer sound right without making
it right; models "deploy behavioral strategies based on learned priors rather than adapting to
problem-specific demands." Structural honesty beats fluency.

## What the engine does about it

1. **Structure before sequence.** The engine never asks the model to "reason step by step." It asks for
   the structure: the corner, the neighbours, the relations, the observables, the readings. The script
   serializes afterwards, for the log and the reader.
2. **Process is part of a route's identity.** Every route records how it reached its value. Two routes
   that agree by different processes are two routes; the same process twice is one. A value with its
   process stripped is not reusable downstream and is not counted.
3. **Readings, explicitly.** Where wording allows more than one alignment, each reading is written out and
   tested on its own, and the result is reported as "fits if you mean this; does not if you mean that,"
   with the number for each. The literal reading is one of the readings, never the only one.
4. **Unfold before judging.** A compressed or figurative statement is expanded to the relationships it
   stands for; the expansion is logged; the verdict is on the expansion.
5. **Anomalies first.** A datum that does not fit is checked against its neighbours before it is counted
   as a miss; a miss that survives the neighbours is reported as a finding, not buried as an outlier.
6. **No credit for sounding right.** A verdict with no route, no verbatim quote and no number is UNSTABLE
   however fluent the reason. The model's fluency rate is measured as the citations the script throws out.
7. **Explain every fit, every time.** Each verdict carries the script's deterministic account (routes
   found, processes, values against bands, agreements, disagreements, discards) and the model's one-line
   rationale per core. A verdict without its explanation is not a verdict.
8. **Say what the answer is in the reader's register, with the structure intact.** The reduced statement
   is for the reader; the kept terms are the structure; both are printed.
