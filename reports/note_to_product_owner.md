# Note to the Great.cards product owner: card-advisor chatbot evaluation

**Basis:** 20 sceptical test questions, run before and after my fixes, with every answer checked by hand against the card tools' output. The counts below describe these 20 questions, not all users.

## 1. What users could get wrong today

**Confirmed in the final run (after my fixes):**
- **Told they're eligible for cards they don't qualify for.** At ₹6 lakh a year, a user was told they were "eligible for 231 cards", including HDFC Regalia Gold, whose own record requires ₹18 lakh.
- **Steered to the wrong top card.** A milestone bonus valued at about ten times the card's own terms put SBI Landmark at #1 for everyday spenders.
- **Shown dining rewards they won't earn.** Cards that pay 5% only on online food orders were credited 5% on restaurant bills paid in person.
- **Given wrong lounge visit counts, refused simple single-category questions,** and in one case misread a fee waiver.

**Fixed by my changes (seen before, not in the final run):** invented or calculated rupee figures, and tax advice.

## 2. What I fixed, and the evidence

I changed only the chatbot's instructions; the server is untouched. The new rules:
- show only rupee figures the tools returned, never calculated ones;
- read a mislabelled monthly field correctly;
- keep joining and annual fees separate, and take waivers only from the tool's own answer.

The rules contain no test-question names or numbers, so they aren't tuned to these 20 cases.

| On the same 20 questions | Before | After |
|---|---|---|
| Answers passing review | 6 | 11 (12 in an earlier run with the first three rules) |
| Most harmful failures (false eligibility "yes", tax advice) | 2 | 0 |
| Answers with rupee figures no tool returned | 6 | 0 |
| Fee or waiver mistakes | 1 | 1 |

**Caveat:** the tax and eligibility improvements happened without the rules written for them, so I can't credit those rules. Eight of the nine remaining failures trace back to the server or its data, which the bot can point out but not correct.

## 3. Recommended server and data improvements (ranked by user impact)

All are **confirmed defects**: the tool output contradicts the server's own card data or its own documentation.

1. **Make the eligibility check apply each card's income requirement.** It's the most harmful (users may apply for cards they can't get), and the chatbot can't work around it for whole lists. The engineering spec is ready.
2. **Value milestone bonuses from the card's own terms.** SBI Landmark is valued at ₹30,000 where its terms work out to ₹3,000, which changes the #1 card.
3. **Apply in-person rates to in-person dining.** This inflates several cards' savings for diners.
4. **Make "net savings" match its own description,** which says it subtracts the joining fee. It doesn't, so a card with a joining fee ties with a free card.
5. **Fix misleading labels:** monthly values under an "annual" name, and lounge visits per year labelled as per quarter.
6. **Smaller fixes:** card-list filters (such as "lifetime free") are ignored; bad pincodes silently return no cards; a card-name lookup returned another bank's card with "high" confidence.

## 4. What remains uncertain

- **Why** the eligibility, milestone and dining defects happen inside the server is a hypothesis; engineering can confirm each one with a code check.
- **Whether the stored card terms match the banks' current terms** wasn't checked. My findings are inconsistencies within the server's own data.
- **Run-to-run variation:** two answers flipped between runs for reasons unrelated to any fix, so one or two answers of difference is noise.
- **Two of my rules describe how the server behaves today.** They must be revisited when engineering fixes those fields.

## Decisions requested

1. Prioritise the eligibility fix with engineering.
2. Approve switching on the written "no approval promise" and "no tax advice" rules.
3. Approve masking PAN and other ID numbers before they reach the AI provider or our logs (a test user's PAN was stored).
