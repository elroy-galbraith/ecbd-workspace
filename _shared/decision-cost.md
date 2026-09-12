# Decision cost

The bar for the cost questions at design stage 1, the operating point at design stage 6, and the cost row in the validity register. A house addition — see below for why it is not ECBD and why it is here anyway.

## What ECBD leaves out

ECBD asks whether results can be interpreted as intended. It stops there deliberately: validity is its subject and it says so. It does not ask what happens when someone acts on that interpretation and the interpretation is wrong.

That gap matters because most evals in this workspace exist to gate something. An eval used as a gate has a loss ratio whether or not anyone writes one down, and that ratio is what decides where the line sits. Leaving it unwritten does not avoid the decision — it makes the decision silently, at one to one, on behalf of whoever gets harmed.

This is the second house addition to the framework. The first was `03-measure/` and `_tools/`, which compute reliability — also named out of scope by ECBD, also built because a real run needed it. Both are marked as house rather than presented as ECBD, and the out-of-scope list in [ecbd-framework.md](ecbd-framework.md) names what is still genuinely uncovered.

## Three terms

**Cost of failure.** What a wrong result costs, in both directions, and who carries each. Two answers, never one. A false pass and a false block land on different people, and often only one of those people is in the room.

**Cost asymmetry.** The ratio between those two costs, written as a ratio and a direction: "a false pass costs roughly twenty false blocks." An order of magnitude is enough. Precision here is false comfort; what a threshold needs is which way, and roughly how far.

**Operating point.** The score at which someone acts, the loss ratio that justifies it, and the switching condition — what would move the line or retire the eval. All three, or it is a number someone typed.

## Labels

Every cost asymmetry carries one, recorded at stage 1 and carried forward to stage 6 and the register. Same discipline as the strength labels in [validity-evidence.md](validity-evidence.md): never round upward.

| Label | Means |
|---|---|
| `elicited` | A named decision-maker gave the ratio. Record who. |
| `derived` | Computed from documented consequences — incident costs, review time, contractual penalties. Cite them. |
| `assumed` | A default someone wrote down and owns. Record who owns it. |
| `absent` | Nobody asked. A finding, not an embarrassment. |

## Silence is not `assumed`

The rule that makes the rest of this work.

`assumed` means a person chose a ratio, wrote it down, and put their name on it. That is defensible and often correct. Silence means the eval asserts one to one anyway and nobody owns the assertion. The two are indistinguishable in a worksheet with no field for them, which is the whole reason for the field.

So an eval that gates a decision and carries `absent` holds a gap of the same kind as a SUPPORT answer of `none`. It goes in the gaps table with a next step. That next step is usually a fifteen-minute conversation — which makes it the cheapest gap in the register and the one least excusable to leave open.

## Eliciting a ratio when nobody has one

Decision-makers rarely hold the number and usually hold the judgement. Two questions get most of the way:

1. **Which error would you rather make?** This gets the direction, which is the half that matters more. A threshold pointed the wrong way is worse than one merely placed badly.
2. **How many of the cheap error would you trade for one of the expensive one?** Ten? A hundred? People answer this readily even when they cannot state a cost, and an order of magnitude is all a threshold needs.

If the answer to the first question is "they are the same", that is a real answer. Record it as `elicited` at one to one, with the name attached. It is not the same as silence.

## The binding constraint

Stage 1 also records which budget is scarce: money or human time. The two behave differently, and the scarce one is rarely the one named in the request.

Compute is cheap and getting cheaper. Labels, expert review capacity and the calendar are not. An assembly decision presented as a methodological choice is usually a review-capacity decision in better clothes, which is why stage 5 asks which it is. Recording the binding constraint at stage 1 means stage 5 checks an answer instead of inventing one.

## Where this lands

| Stage | What it records |
|---|---|
| design 1 | Cost of failure in both directions, the asymmetry and its label, the binding constraint |
| design 6 | The operating point, the loss ratio behind it, the switching condition |
| design 7 | The cost row in the register; `absent` and `assumed` become gaps |

The audit line does not load this file. A benchmark whose creators never considered cost currently produces a silence rather than a finding.
