# Execution Report: Single Bet Placement

Results of the three highest-priority scenarios from the [test plan](test-plan.md), the
exploratory checks made around them, and the defects found.

- **Date:** 2026-11-14
- **Environment:** `https://qae-assignment-tau.vercel.app`, macOS. The scenarios were run
  in Safari; the UI defects (BUG-03, BUG-04, BUG-05, BUG-06) and the UI balance check
  (BUG-01) were then confirmed in Google Chrome 157.0.8103.79
- **API calls:** `curl` with the `x-user-id` header

## Summary

| Scenario | Result | Defects found |
| -------- | ------ | ------------- |
| TC-01 Place a single bet | **Fail** (steps 6 and 8) | BUG-02, BUG-03, BUG-04, BUG-05, BUG-06 |
| TC-02 Stake above the balance | **Fail** (steps 1 to 4) | BUG-01 |
| TC-03 Stake limits at the boundaries | **Pass** | none against the stake limits |

| ID     | Defect                                                              | Severity |
| ------ | ------------------------------------------------------------------- | -------- |
| BUG-01 | Bet is accepted when the stake exceeds the balance                  | Critical |
| BUG-02 | Bets are accepted on matches that have already been played          | Critical |
| BUG-03 | Balance in the header and bet slip is not updated after a bet       | High     |
| BUG-04 | Receipt shows a different potential payout than the bet slip        | High     |
| BUG-05 | Receipt shows the home and away teams in reversed order             | High     |
| BUG-06 | Receipt does not show the selection                                 | Medium   |
| BUG-07 | `reset-balance` reports €125.50 but stores €120.00                  | Medium   |
| BUG-08 | `place-bet` returns a payout €0.01 lower than stake × odds          | Medium   |
| BUG-09 | `place-bet` returns currency `USD` instead of `EUR`                 | Low      |

The two Critical defects let a user bet money they do not have and bet on a result that
is already known. Both are accepted by the API itself, so fixing the UI alone would not
close them.

## Scenario results

### TC-01: Place a single bet

Match used: Manchester Utd vs Chelsea, selection `1` (home win), odds 2.45, stake €10.00.

| Step | Result | Actual |
| ---- | ------ | ------ |
| 1 | Pass | Header and bet slip showed €125.50. |
| 3 | Pass | Bet slip showed the match, the home-win selection and odds 2.45. |
| 4 | Pass | Potential payout showed €24.50. |
| 5 | Pass | `Placing...`, then the success receipt. |
| 6 | **Fail** | Receipt showed "Chelsea vs Manchester Utd" (BUG-05), payout €20.00 (BUG-04) and no selection (BUG-06). Bet ID, stake, odds and time were correct. |
| 7 | Pass | Bet slip was empty after closing the receipt. |
| 8 | **Fail** | Header and bet slip still showed €125.50 (BUG-03). The stored balance was reduced. |

The match used here has a kickoff date of 2026-02-27, which led to BUG-02.

### TC-02: Stake above the balance

Deviation from the plan: the balance was not reset before this scenario, so the €10.00
bet from TC-01 still counted. After the €100.00 bet in step 1 the stored balance was
€15.50, not €25.50. The stake of €25.51 was still above the balance, so the rule under
test was exercised.

| Step | Result | Actual |
| ---- | ------ | ------ |
| 1 | **Fail** | The €100.00 bet was placed, but the UI balance did not change (BUG-03). |
| 2 | **Fail** | No `Insufficient balance` message. `Place Bet` was enabled. |
| 3 | **Fail** | The bet was placed and a receipt appeared. `GET /api/balance` returned −10.01 (BUG-01). |
| 4 | **Fail** | With the balance at −10.01, `POST /api/place-bet` with `stake: 25.51` returned 200. The balance became −35.52 (BUG-01). |
| 5, 6 | Not executed | The balance rule is not enforced at all, so the "stake equal to the balance" boundary gives no information until BUG-01 is fixed. |

### TC-03: Stake limits at the boundaries

UI pass on Napoli vs Lazio (odds 1.95). API pass on `ligue-1-marseille-psg-2026-11-17`
(odds 4.10) after a balance reset.

| Stake    | UI                                                  | API                         | Result |
| -------- | --------------------------------------------------- | --------------------------- | ------ |
| `0.99`   | `Minimum stake is €1.00`, `Place Bet` disabled      | 422, `invalid_stake_min`    | Pass   |
| `100.01` | `Maximum stake is €100.00`, `Place Bet` disabled    | 422, `invalid_stake_max`    | Pass   |
| `1.00`   | Accepted                                            | 200                         | Pass   |
| `1.01`   | Accepted                                            | 200                         | Pass   |
| `100.00` | Accepted                                            | 200                         | Pass   |

In the API pass a rejected stake left the balance unchanged and an accepted stake reduced
it by exactly that stake (120.00, 119.00, 117.99, 17.99).

The minimum stake is €1.00 in both layers. Section 4.1 of the specification, which says
€1.01, is the part that needs correcting.

The receipts and API responses seen during this scenario showed BUG-04, BUG-05, BUG-08
and BUG-09 again.

### Exploratory checks

| Check | Finding |
| ----- | ------- |
| Reload the page after several bets | The UI then shows the stored balance. It reads the balance on load only (BUG-03). |
| Place a bet through the API with a negative balance | Accepted (BUG-01). |
| Compare the `reset-balance` response with `GET /api/balance` | They differ (BUG-07). |
| Inspect the match list returned by `GET /api/matches` | 91 of 103 matches are in the past (BUG-02). |
| Read every field of the `place-bet` response | Wrong currency (BUG-09), payout one cent low (BUG-08). |
| `POST /api/place-bet` with an unknown `matchId` | 422 `invalid_match`, as specified. |

Not covered in this session: double submission of `Place Bet`, the error modal
(`Rebet`, `Close`), the date and odds filters, and replacing or removing a selection.

---

## Defects

### BUG-01: Bet is accepted when the stake exceeds the balance

**Severity:** Critical

**Reproduction steps:**

1. Start from a balance of €125.50.
2. Place a bet of €10.00, then a bet of €100.00. The stored balance is now €15.50.
3. Select any odds, enter stake `25.51` and click `Place Bet`.
4. Call `GET /api/balance`.
5. Send `POST /api/place-bet` with a valid `matchId`, `selection: "HOME"` and
   `stake: 25.51`.

**Expected:** Step 3 shows `Insufficient balance` and blocks placement. Step 5 is
rejected with a validation error. The balance never goes below zero.

**Actual:** Step 3 shows no message and the bet is placed. Step 4 returns
`{"balance":-10.01,"currency":"EUR"}`. Step 5 returns 200 and the balance becomes −35.52.

**Business impact:** Users can bet without funds and the operator carries every stake
placed below zero.

**Evidence:** [bet slip before placement](evidence/tc02-bet-slip-before.png),
[receipt](evidence/tc02-receipt.png),
[negative balance in the UI](evidence/balance-negative-after-reload.png). API response
from step 5:

```json
{"message":"Bet placed successfully","matchId":"premier-league-manutd-chelsea","selection":"HOME","stake":25.51,"odds":2.45,"payout":62.49,"balance":-35.52,"currency":"USD"}
```

**Note:** The UI does have this check: after a page reload, with a displayed balance of
€7.99, a stake of €8.00 shows `Insufficient balance` and disables `Place Bet`
([screenshot](evidence/bug01-ui-insufficient-balance-message.png)). In step 3 the check
passed because the UI was comparing against a stale balance of €125.50 (BUG-03). The API
has no such check and accepts the bet either way. The request in step 5 happened to use the past match from BUG-02, so that
one response shows both defects.

### BUG-02: Bets are accepted on matches that have already been played

**Severity:** Critical

**Reproduction steps:**

1. Open the application on 2026-11-14.
2. Find Manchester Utd vs Chelsea (Premier League, "Fri, Feb 27"). The card carries a
   `PAST` badge.
3. Click `1`, enter stake `10.00` and click `Place Bet`.
4. Send `POST /api/place-bet` with `matchId: "premier-league-manutd-chelsea"`.

**Expected:** Only upcoming matches are listed (specification sections 1 and 3). A bet
on a past match is rejected by the UI and by the API.

**Actual:** The match is listed and its odds are selectable. The bet in step 3 is placed
and the stake is deducted. The request in step 4 returns 200. `GET /api/matches` returns
103 matches, 91 of them with a `kickoffDate` before today.

**Business impact:** A user can bet on a match whose result is already known, which is a
guaranteed win paid by the operator.

**Evidence:** [match list with `PAST` badges](evidence/bug02-past-matches-listed.png).
`GET /api/matches` entry for the match:

```json
{"id":"premier-league-manutd-chelsea","competition":"Premier League","kickoffDate":"2026-02-27","homeTeam":"Manchester Utd","awayTeam":"Chelsea","odds":{"home":2.45,"draw":3.1,"away":2.8}}
```

**Note:** The UI already identifies the match as past, since it renders the `PAST`
badge, but does not act on it.

### BUG-03: Balance in the header and bet slip is not updated after a bet

**Severity:** High

**Reproduction steps:**

1. Open the application. Header and bet slip show €125.50.
2. Place a bet of €10.00 and close the receipt.
3. Read the balance in the header and in the bet slip.
4. Reload the page.

**Expected:** After step 2 both places show €115.50 (specification section 2.3: on
success the stake is deducted).

**Actual:** After step 2 both places still show €125.50. The stored balance is reduced,
and the UI shows it only after the reload in step 4.

**Business impact:** Users see funds they no longer have and keep betting against them;
with BUG-01 this takes the balance below zero without any warning.

**Evidence:** [balance after the bet](evidence/tc01-balance-after-bet.png),
[balance after reload](evidence/balance-negative-after-reload.png).

### BUG-04: Receipt shows a different potential payout than the bet slip

**Severity:** High

**Reproduction steps:**

1. Select Napoli vs Lazio, `1` (odds 1.95).
2. Enter stake `100.00`. The bet slip shows potential payout €195.00.
3. Click `Place Bet` and read the receipt.

**Expected:** The receipt shows €195.00, the value the user confirmed (stake × odds).

**Actual:** The receipt shows €200.00. In all six receipts observed, the payout equals
stake × 2.00, whatever the odds:

| Stake  | Odds | Bet slip | Receipt |
| ------ | ---- | -------- | ------- |
| 1.00   | 4.10 | €4.10    | €2.00   |
| 10.00  | 2.45 | €24.50   | €20.00  |
| 25.51  | 1.95 | €49.74   | €51.02  |
| 1.00   | 1.95 | €1.95    | €2.00   |
| 1.01   | 1.95 | €1.97    | €2.02   |
| 100.00 | 1.95 | €195.00  | €200.00 |

**Business impact:** The receipt is the user's record of the bet; a wrong amount on it
leads to payout disputes, in either direction.

**Evidence:** [bet slip](evidence/tc03-stake-100.00-bet-slip.png),
[receipt](evidence/tc03-stake-100.00-receipt.png),
[bet slip from TC-01](evidence/tc01-bet-slip-before.png),
[receipt from TC-01](evidence/tc01-receipt.png).

**Note:** The bet at odds 4.10 rules out rounded odds: the receipt uses a fixed
multiplier of 2 ([bet slip](evidence/bug04-bet-slip-odds-4.10.png),
[receipt](evidence/bug04-receipt-odds-4.10.png)). The `place-bet` response carries a
payout based on the real odds, which suggests the defect is in how the receipt is
rendered.

### BUG-05: Receipt shows the home and away teams in reversed order

**Severity:** High

**Reproduction steps:**

1. Select Juventus vs AC Milan, `1`. The bet slip shows "Juventus vs AC Milan",
   "Match Winner: Home".
2. Enter a valid stake and click `Place Bet`.
3. Read the match line on the receipt.

**Expected:** "Juventus vs AC Milan". The home team is listed first everywhere,
including the receipt.

**Actual:** "AC Milan vs Juventus". The same happened for Napoli vs Lazio and for
Manchester Utd vs Chelsea.

**Business impact:** The receipt names the wrong team as home, so a user who bet on the
home win reads it as a bet on the other team.

**Evidence:** [bet slip](evidence/tc02-bet-slip-before.png),
[receipt](evidence/tc02-receipt.png).

### BUG-06: Receipt does not show the selection

**Severity:** Medium

**Reproduction steps:**

1. Place any bet.
2. Read the receipt.

**Expected:** The receipt shows the selection (specification section 2.4).

**Actual:** The receipt shows Bet ID, match, stake, odds, potential payout and time. The
selection is missing.

**Business impact:** The user has no record of which outcome they bet on; together with
BUG-05 the receipt cannot be used to verify the bet.

**Evidence:** [receipt](evidence/tc01-receipt.png).

### BUG-07: `reset-balance` reports €125.50 but stores €120.00

**Severity:** Medium

**Reproduction steps:**

1. Send `POST /api/reset-balance`.
2. Send `GET /api/balance`.

**Expected:** Both return 125.50. The specification requires the response body and the
persisted state to be consistent.

**Actual:** Step 1 returns `"balance":125.5`. Step 2 returns `"balance":120`.
Reproduced twice.

**Business impact:** The endpoint reports a balance that was not stored, so any client or
test that trusts the response works with a wrong amount.

**Evidence:**

```
{"message":"Balance reset successfully","balance":125.5,"currency":"EUR"}
{"balance":120,"currency":"EUR"}
```

### BUG-08: `place-bet` returns a payout €0.01 lower than stake × odds

**Severity:** Medium

**Reproduction steps:**

1. Send `POST /api/place-bet` with `matchId: "ligue-1-marseille-psg-2026-11-17"`,
   `selection: "HOME"` (odds 4.10) and `stake: 1.00`.
2. Read `payout` in the response.

**Expected:** 4.10.

**Actual:** 4.09.

| Stake  | Odds | Stake × odds | Returned payout |
| ------ | ---- | ------------ | --------------- |
| 1.00   | 4.10 | 4.10         | 4.09            |
| 100.00 | 4.10 | 410.00       | 409.99          |
| 25.51  | 2.45 | 62.4995      | 62.49           |
| 1.01   | 4.10 | 4.141        | 4.14            |

**Business impact:** The API understates the payout by one cent on many bets; if
settlement uses this value, users are underpaid.

**Evidence:**

```json
{"message":"Bet placed successfully","matchId":"ligue-1-marseille-psg-2026-11-17","selection":"HOME","stake":1,"odds":4.1,"payout":4.09,"balance":119,"currency":"USD"}
```

**Note:** All four values match the result of cutting a binary floating-point product
down to two decimals instead of rounding it (4.1 is stored as 4.0999...). The bet slip in
the UI rounds, so the UI and the API can differ by one cent for the same bet. The
specification does not define a rounding rule.

### BUG-09: `place-bet` returns currency `USD` instead of `EUR`

**Severity:** Low

**Reproduction steps:**

1. Send a valid `POST /api/place-bet`.
2. Read `currency` in the response.

**Expected:** `"EUR"` (specification sections 3 and 5.3).

**Actual:** `"USD"`. `GET /api/balance` returns `"EUR"` for the same user.

**Business impact:** A client that displays the currency from this response would show
dollar amounts for a euro account.

**Evidence:** see the response under BUG-08.

---

## Questions for the specification

1. **Minimum stake:** section 4.1 says €1.01; sections 3 and 4.4 and the application say
   €1.00.
2. **Payout rounding:** no rule is given for a product with more than two decimals.
3. **Insufficient balance:** the status code and error code are not listed.
4. **Receipt timestamp:** the receipt shows "TODAY, 09:16 PM". The specification does not
   say whether a full date is required; without one a saved receipt loses its date.
