# Reading an item analysis

What the numbers mean, and what to do about them. `_tools/item_analysis.py` names the conditions that fired; this file holds the remedies.

Each entry says what to do if you **own** the eval and can change it, and what to do if you **do not** — an audit cannot fix someone else's benchmark, only decide how to use it. Every entry also names the trap, because most of these have an obvious fix that makes things worse.

Thresholds are classical test theory conventions, not laws. Discrimination below 0.2 is weak and at or below 0 is broken; KR-20 above 0.8 is acceptable. Treat them as the start of an argument.

---

## `low-discrimination`

**Means.** Many items fail to separate stronger models from weaker ones. An item at or below zero discrimination contributes nothing to the ranking, or actively works against it.

**Usually caused by** mislabelled reference answers, genuine ambiguity, items so easy or hard that everyone converges, or items quietly measuring a different construct from the rest of the set.

**If you own it.** Read the zero-discrimination items before deleting anything. That inspection is worth more than the pruning — it typically surfaces a content bug that affects items you were about to keep. Then check whether they cluster: by category, by answer length, by source. A cluster is a systematic defect; scattered items are usually noise.

**If you don't.** Report per-category rather than in aggregate, and say in the findings that a named fraction of the instrument is inert. That is a concrete, checkable claim about the benchmark rather than a vague complaint.

**Trap.** Pruning to maximise discrimination narrows the construct. Keep only the items that separate today's models and you will optimise your way into a reliable measure of something nobody asked for. An item that does not discriminate among *these* models may discriminate among others.

---

## `reliability-from-length`

**Means.** KR-20 looks healthy but mean discrimination is low. The scale hangs together because it is long, not because its items are good. Reliability rises with item count almost regardless of item quality.

**If you own it.** A shorter set chosen for discrimination will usually rank better *and* cost less to run. Test it: compute the ranking on your best-discriminating half and compare to the full set. If they agree, you are paying for items that buy nothing.

**If you don't.** Do not quote KR-20 as evidence the benchmark is good. It is evidence the benchmark is internally consistent, which is a weaker claim than it sounds.

**Trap.** Reporting reliability as though it licensed the ranking. High KR-20 with low discrimination is exactly the profile of a benchmark that measures something stable and ranks badly.

---

## `unresolvable-ranking`

**Means.** The score difference needed to separate two models exceeds the differences actually observed. Leaderboard positions are not supported by the data.

**If you own it.** Standard error falls as 1/√n, so **halving the separating gap requires four times the items.** Usually the honest conclusion is that the eval is a screen rather than a ranker, and saying so costs less than chasing resolution you cannot afford. If ranking genuinely matters, the cheaper lever is better items, not more of them — see `low-discrimination`.

**If you don't.** Report intervals rather than ranks, and treat any gap below the threshold as a tie. This single change prevents most misuse.

**Trap.** Averaging several benchmarks to break ties. Combining noisy measures compounds their errors rather than cancelling them, and the composite hides which component drove the result.

---

## `unstable-ranking`

**Means.** Split the item set at random and the two halves order models differently. The swap rate is the plain reading: how often a model pair changes places between halves.

**Usually caused by** low discrimination, or by the item set being multidimensional — different items measuring genuinely different things, so which half you draw decides what you measured.

**If you own it.** Check dimensionality before adding items. If the set is measuring two constructs, more items make the instability worse, not better; the fix is to split the benchmark in two and report both.

**If you don't.** Treat the ranking as indicative only, and never as evidence for a decision between adjacent candidates.

**Trap.** Assuming instability means noise. A consistently *bimodal* split is structure, not noise, and it is telling you the benchmark has two constructs in it.

---

## `saturated` / `floored`

**Means.** A large share of items sit above 0.95 (everyone passes) or below 0.05 (everyone fails). Neither carries information about differences between models.

**If you own it.** Saturation is the normal end of a benchmark's life. Replace the ceiling items with harder ones or retire the eval; a benchmark that everything passes is a regression test, which is a legitimate but different job. Floor items are more often broken than hard — check them before assuming difficulty.

**If you don't.** Report on the discriminating subset and say what fraction you dropped.

**Trap.** Reading saturation as models having acquired the capability. It means the *items* no longer distinguish, which is a claim about the instrument.

---

## `gameable-primary`

**Means.** A second construct in the records correlates negatively with the rank penalty models take when it is required. Models low on that construct are being flattered by the primary score alone.

**The classic case** is truthfulness paired with informativeness: refusing to answer is perfectly truthful, so a cautious model scores well on a truthfulness-only metric while being useless.

**If you own it.** Report the pair, always, and gate on both. If you must have one number, define the composite explicitly and justify the weighting — do not let the primary metric stand in for a construct it only half covers.

**If you don't.** Recompute using both constructs before comparing candidates. This is usually cheap and it is the single highest-value correction available to a benchmark user.

**Trap.** Assuming the effect is a population-wide trade-off. It is often concentrated in a minority tail, which makes it invisible in aggregate statistics and worse in practice, because it strikes unpredictably.

---

## `capability-unmeasured`

**Means.** A capability the eval claims to measure has items tagged to it that do not discriminate. It is named in the design and absent from the measurement.

**If you own it.** Either write items that actually elicit it, or drop the claim. A capability in the worksheet with no discriminating items is the traceability failure ECBD exists to catch — the design says the eval measures three things and the data says it measures two.

**If you don't.** Name it in the findings. "The benchmark claims X and its items provide no evidence about X" is among the strongest things an audit can say.

**Trap.** Accepting item count as coverage. Twenty items tagged to a capability prove nothing if none of them separate models.

---

## `thin-matrix`

**Means.** Too few models to compute discrimination, reliability or stability. The tool skips them rather than reporting numbers that cannot bear weight.

**If you own it.** Add models before adding items. Item statistics are estimated *across* models — twenty mediocre baselines buy more analytic power here than a thousand extra items.

**If you don't.** Check the archive; a benchmark with sparse coverage locally may be well covered publicly.

**Trap.** Computing the statistics anyway on a handful of models. They will be printed to the same number of decimal places as a trustworthy estimate.

---

## `unreliable-scale`

**Means.** KR-20 below roughly 0.7. The items do not behave as a single coherent measure at all.

**If you own it.** Before treating this as a defect, ask whether the eval was ever meant to be one scale. A suite spanning several capabilities *should* have low internal consistency; the fix is to report per-capability reliability instead of one number.

**If you don't.** Do not aggregate. Report components.

**Trap.** Raising reliability by adding near-duplicate items. It works, and it measures nothing new.

---

## When nothing fires

Say so explicitly in the analysis. A clean run means the instrument discriminates, ranks stably, and is not obviously gameable — which is a real and reportable finding, and rarer than you would expect.

It does not mean the eval is valid. These statistics say nothing about whether the construct is well defined, whether items were justified, or whether the intended use is served. That is what the worksheet is for.
