# Reading an item analysis

Written to ASD-STE100 (lite). Short sentences, active voice, one term per idea. See `_shared/language.md`.

`_tools/item_analysis.py` names the conditions that fired. This file tells you what each one means and what to do.

Each entry gives you two paths. **If you own the eval**, you can change it. **If you do not own it**, you can only decide how to use it — an audit cannot repair someone else's benchmark. Each entry also names a trap, because most of these problems have an obvious fix that makes things worse.

The thresholds come from classical test theory. They are conventions, not laws. Discrimination below 0.2 is weak. Discrimination at or below 0 is broken. KR-20 above 0.8 is acceptable. Use these numbers to start an argument, not to end one.

---

## `low-discrimination`

**What it means.** Many items do not separate strong models from weak ones. An item with discrimination at or below 0 adds nothing to the ranking. Some items make the ranking worse.

**Usual causes.** The reference answer is wrong. The item is ambiguous. The item is so easy or so hard that all models give the same answer. Or the item measures a different thing from the rest of the set.

**If you own it.** Read the items that fail before you remove them. This reading is worth more than the removal, because it usually finds a content defect in items you planned to keep. Then look for a pattern. Do the failed items share a category, an answer length, or a source? A pattern shows a systematic defect. Scattered items are usually noise.

**If you do not own it.** Report each category on its own, not as one number. Say in your findings what share of the benchmark is inert. This is a specific claim that someone can check.

**Trap.** If you remove items to raise discrimination, you make the construct narrower. Keep only the items that separate today's models, and you get a reliable measure of something nobody asked for. An item that fails to separate *these* models can still separate others.

---

## `reliability-from-length`

**What it means.** KR-20 looks good, but mean discrimination is low. The item set holds together because it is long, not because the items are good. Reliability rises with item count almost whatever the item quality is.

**If you own it.** A shorter set of high-discrimination items usually ranks better and costs less to run. Test this. Rank the models on your best half, then compare that ranking to the full set. If the two agree, the extra items give you nothing.

**If you do not own it.** Do not cite KR-20 as proof that the benchmark is good. KR-20 shows that the benchmark is consistent. That is a weaker claim than it sounds.

**Trap.** Do not let a high KR-20 make the ranking look safe. High reliability with low discrimination is exactly what a benchmark looks like when it measures something stable and ranks badly.

---

## `unresolvable-ranking`

**What it means.** Two models must differ by more than the scores actually differ. The positions on the leaderboard are not supported by the data.

**Good items do not fix this.** Two benchmarks in this workspace fail to rank, for opposite reasons. TruthfulQA is noisy: half its items hardly separate models, and its two halves disagree about a quarter of model pairs. GPQA is close to ideal. Its mean discrimination is 0.457, its KR-20 is 0.993, and its two halves agree on 95.5% of model pairs. It still cannot separate neighbouring models. With 446 items the standard error is 2.0 points, and the models sit 0.45 points apart.

Resolution comes from the item count and the size of the real difference, not from item quality. If you see a high KR-20 and high discrimination, do not conclude that the ranking is safe. Check the separating gap.

**If you own it.** Standard error falls as 1 over the square root of the item count. **To halve the gap you need four times as many items.** Usually the honest conclusion is different: your eval is a screen, not a ranker. Say so. It costs less than buying resolution you cannot afford. If you must rank, better items help more than more items. See `low-discrimination`.

**If you do not own it.** Report intervals, not positions. Treat any gap below the threshold as a tie. This one change prevents most misuse.

**Trap.** Do not average several benchmarks to break a tie. Noisy measures add their errors together, and the combined score hides which part caused the result.

---

## `unstable-ranking`

**What it means.** Divide the items at random into two halves. Each half ranks the models differently. The swap rate tells you how often a pair of models changes places between the halves.

**Usual causes.** Low discrimination. Or the item set measures more than one thing, so the half you draw decides what you measured.

**If you own it.** Test how many things the set measures before you add items. If it measures two things, more items make it less stable, not more. Divide the benchmark in two and report both parts.

**If you do not own it.** Treat the ranking as a rough guide. Never use it to choose between two models that are close together.

**Trap.** Do not assume instability is noise. A split that divides the same way each time shows structure. It tells you the benchmark contains two different measures.

---

## `saturated` and `floored`

**What it means.** Many items sit above 0.95, so every model passes them. Or many items sit below 0.05, so every model fails them. Neither group tells you how models differ.

**If you own it.** Saturation is how a benchmark ends its life. Replace the easy items with harder ones, or retire the eval. A benchmark that everything passes is a regression test. That is a real job, but a different one. Items at the floor are more often broken than hard, so read them before you call them difficult.

**If you do not own it.** Report the results for the items that still separate models, and say what share you removed.

**Trap.** Saturation does not mean the models have the capability. It means the items no longer tell models apart. That is a fact about the instrument.

---

## `gameable-primary`

**What it means.** The records hold a second measure. Models that score low on it rise in the ranking when you use the first measure alone. The first measure flatters them.

**The clearest case** is truthfulness and informativeness. A model that refuses to answer is completely truthful. So a cautious model scores well on truthfulness alone and helps nobody.

**If you own it.** Report both measures every time, and gate on both. If you must publish one number, define how you combine them and justify the weights. Do not let one measure stand for a construct it covers only in part.

**If you do not own it.** Use both measures before you compare models. This is usually cheap, and it is the most valuable correction available to someone who uses a benchmark.

**Trap.** Do not assume the effect applies to all models. It often affects a small group. That makes it invisible in the totals and worse in practice, because you cannot predict which model it hits.

---

## `facet-disagreement`

**What it means.** One group of items ranks models differently from the rest. The group can be one category, one construction method, or one source. The tool reports this only when the group disagrees **more than random groups of the same size do**.

**The size match is the whole finding.** Two groups of 30 items disagree a lot from sampling noise alone. If you compare them to a baseline built from 400-item halves, you will find a difference that is not there.

**If you own it.** You have two benchmarks under one name. Report the groups separately, or remove the group that does not belong. Adding items does not help, because you add them to both groups.

**If you do not own it.** Report each group separately. A combined score over groups that disagree averages two different measurements, and the order it produces belongs to neither.

**Trap.** Do not trust a comparison that is not size-matched. On TruthfulQA the raw comparison by category looked severe. One pair reached a correlation of −0.003, and 57% of model pairs changed places. Almost all of that disappeared against size-matched baselines. Only one category of 38 exceeded its baseline, and only by a little. Always ask what a random group of the same size would have done.

---

## `capability-unmeasured`

**What it means.** The eval claims to measure a capability. The items tagged to that capability do not separate models. The design names the capability and the data says nothing about it.

**If you own it.** Write items that draw out the capability, or remove the claim. A capability with no discriminating items is the traceability defect that ECBD exists to find. The design names three capabilities and the data supports two.

**If you do not own it.** Name it in your findings. "The benchmark claims X and its items give no evidence about X" is one of the strongest statements an audit can make.

**Trap.** Do not accept item count as coverage. Twenty items tagged to a capability prove nothing if none of them separate models.

---

## `thin-matrix`

**What it means.** There are too few models to calculate discrimination, reliability, or stability. The tool skips these numbers instead of reporting values you cannot trust.

**If you own it.** Add models before you add items. The tool calculates item statistics *across* models. Twenty ordinary baseline models help you more here than a thousand extra items.

**If you do not own it.** Check the archive. A benchmark with few models on your machine can have many models in public data.

**Trap.** Do not calculate the numbers anyway on a few models. They print to the same number of decimal places as numbers you can trust.

---

## `unreliable-scale`

**What it means.** KR-20 is below about 0.7. The items do not act as one measure.

**If you own it.** First ask whether the eval was ever meant to be one measure. A suite that covers several capabilities *should* have low internal consistency. If so, report reliability for each capability instead of one number for all.

**If you do not own it.** Do not combine the scores. Report the parts.

**Trap.** Do not raise reliability by adding items that repeat the ones you have. It works, and it measures nothing new.

---

## When nothing fires

Say so in the analysis. A clean result means three separate things. The instrument separates models. The ranking holds when you split the items. No second measure games the first. This is a real finding and it is rarer than you expect.

A clean result does not mean the eval is valid. These numbers say nothing about whether you defined the construct well, whether you justified the items, or whether the eval serves its intended use. The worksheet answers those questions.
