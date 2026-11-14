# Test Plan: Single Bet Placement

Six scenarios for the Single Bet Placement feature, ordered by priority. Expected results
come from the Feature Specification and the API documentation (`/api/docs`), not from the
current behaviour of the application.

## How priority was assigned

Priority is the cost of a defect multiplied by how likely it is to be there.

- **Cost**: a defect that moves money incorrectly (wrong deduction, bet without funds,
  wrong receipt) ranks above one that only makes the product harder to use.
- **Likelihood**: boundaries, failure paths and places where the specification
  contradicts itself are more likely to hide a defect than the main path.

## Summary

| ID    | Scenario                                                              | Priority | Type                  |
| ----- | --------------------------------------------------------------------- | -------- | --------------------- |
| TC-01 | Place a single bet: receipt matches the bet slip, balance is reduced  | Critical | Happy path            |
| TC-02 | Stake above the balance is rejected, stake equal to it is accepted    | Critical | Negative + boundary   |
| TC-03 | Stake limits at the boundaries, in the UI and the API                 | High     | Boundary              |
| TC-04 | Failed placement: no deduction, one deduction after `Rebet`           | High     | Failure handling      |
| TC-05 | API rejects invalid bet requests and leaves the balance unchanged     | Medium   | Validation            |
| TC-06 | Odds filter: inclusive bounds, invalid range rejected                 | Low      | Boundary + validation |

TC-01, TC-02 and TC-03 are the three scenarios selected for execution.

## Common preconditions

- Latest desktop Chrome.
- Application open at `https://qae-assignment-tau.vercel.app/?user-id=<user-id>`.
- API requests carry the header `x-user-id: <user-id>`.
- Each scenario starts from a reset balance: call `POST /api/reset-balance`, then confirm
  with `GET /api/balance` that the stored balance is €125.50. The reset response alone is
  not taken as proof, so that a defect in the reset cannot distort another scenario.

## Assumptions and open questions on the specification

1. **Minimum stake.** Section 3 and the UI message in section 4.4 say €1.00; section 4.1
   says €1.01. This plan assumes €1.00, which the API documentation also states
   (`minimum: 1`, "Stake must be at least 1.00"). TC-03 tests both values so the result
   shows which rule the application follows.
2. **Status code for insufficient balance.** The specification lists 422 for stake
   validation failures but does not name insufficient balance. This plan assumes 422.
3. **Odds filter semantics.** The specification does not say whether a match passes the
   filter when one of its three odds is in range or only when all three are. TC-06
   assumes one is enough.

---

## TC-01: Place a single bet: receipt matches the bet slip, balance is reduced

**Priority:** Critical

**Risk rationale:** This is the core money flow, and every other scenario depends on it.
A receipt that differs from what the user confirmed (team order, odds, stake or payout),
or a deduction that differs from the stake, is a direct financial error and a source of
disputes.

**Steps:**

1. Confirm the balance shown in the header and in the bet slip.
2. Choose a match. Note the home team, the away team, the kickoff label and the odds on
   button `1`.
3. Click button `1` of that match.
4. Enter stake `10.00`.
5. Click `Place Bet`.
6. Compare the receipt with the values noted in steps 2 to 4.
7. Close the receipt.
8. Read the balance in the header, in the bet slip and from `GET /api/balance`.

**Expected result:**

- Step 1: header and bet slip both show €125.50.
- Step 3: the bet slip shows one selection: the chosen match with the home team first,
  the home-win selection and the odds noted in step 2.
- Step 4: potential payout equals 10.00 × the noted odds, shown with two decimals.
- Step 5: the button shows `Placing...`, then exactly one outcome appears: the success
  receipt.
- Step 6: the receipt shows a Bet ID, the match with the home team first, the home-win
  selection, stake €10.00, the odds noted in step 2, the payout shown in step 4 and a
  placement timestamp matching the current date and time.
- Step 7: the bet slip has no active selection and no stake.
- Step 8: the balance is €115.50 in all three places.

---

## TC-02: Stake above the balance is rejected, stake equal to it is accepted

**Priority:** Critical

**Risk rationale:** If a stake larger than the balance is accepted, the user bets money
they do not have and the operator carries the loss. The starting balance (€125.50) is
higher than the maximum stake (€100.00), so this rule can only be reached after an
earlier bet, which makes it easy to leave untested.

**Steps:**

1. Place a bet with stake `100.00` on any selection and close the receipt.
2. Select any odds and enter stake `25.51`.
3. Try to place the bet.
4. Send `POST /api/place-bet` with a valid `matchId`, a valid `selection` and
   `stake: 25.51`, then call `GET /api/balance`.
5. In the UI, change the stake to `25.50` and click `Place Bet`.
6. Read the balance in the header, in the bet slip and from `GET /api/balance`.

**Expected result:**

- Step 1: the balance is €25.50.
- Step 2: the bet slip shows `Insufficient balance`.
- Step 3: no bet is placed, no receipt appears and the balance stays €25.50.
- Step 4: the API rejects the request with 422 and an insufficient balance error; the
  stored balance stays €25.50.
- Step 5: the bet is accepted and the receipt shows stake €25.50.
- Step 6: the balance is €0.00 in all three places and is never negative.

---

## TC-03: Stake limits at the boundaries, in the UI and the API

**Priority:** High

**Risk rationale:** The stake limits are a business rule on how much one bet may risk.
Boundary values are where off-by-one errors occur, and the specification itself gives
two different minimums, so the implementation may follow either. The UI check alone is
not enough, because the API can be called directly.

**Steps:**

1. In the UI, for each stake in the table: select any odds, enter the stake, read the
   message in the bet slip and try to place the bet. Close the receipt after an accepted
   bet. Use the order of the table, rejected values first.
2. Reset the balance (accepted stakes add up to €102.01 per pass).
3. Through the API, send `POST /api/place-bet` with a valid `matchId` and `selection`
   for each stake in the table, in the same order.
4. After every attempt in both passes, read the balance.

| Stake    | UI                                                    | API                          |
| -------- | ----------------------------------------------------- | ---------------------------- |
| `0.99`   | `Minimum stake is €1.00`, placement blocked           | 422, `invalid_stake_min`     |
| `100.01` | `Maximum stake is €100.00`, placement blocked         | 422, `invalid_stake_max`     |
| `1.00`   | Accepted                                              | 200                          |
| `1.01`   | Accepted                                              | 200                          |
| `100.00` | Accepted                                              | 200                          |

**Expected result:**

- Each stake gives the result in the table, and the UI and the API agree for every value.
- A rejected stake leaves the balance unchanged.
- An accepted stake reduces the balance by exactly that stake.

---

## TC-04: Failed placement: no deduction, one deduction after `Rebet`

**Priority:** High

**Risk rationale:** On the failure path the application handles money while the outcome
is uncertain. A deduction without a bet, or a second deduction when the user retries,
costs the user money. This path runs rarely, so a defect in it can stay unnoticed for a
long time.

**Preconditions:** a way to make placement fail, for example blocking the
`/api/place-bet` request in Chrome DevTools (Network, request blocking).

**Steps:**

1. Select any odds and enter stake `10.00`.
2. Block the `/api/place-bet` request and click `Place Bet`.
3. Read the balance in the header, in the bet slip and from `GET /api/balance`.
4. Remove the block and click `Rebet`.
5. Close the receipt and read the balance in all three places.
6. Repeat steps 1 and 2, then click `Close`.
7. Repeat steps 1 and 2, then click the top-right `X`.

**Expected result:**

- Step 2: the button shows `Placing...`, then an error modal titled
  `Something went wrong` appears. Its text says the bet could not be processed and
  suggests trying again. It offers `Rebet`, `Close` and a top-right `X`.
- Step 3: the balance is unchanged at €125.50.
- Step 4: the modal closes, placement is retried and the success receipt shows the same
  match, selection, stake and odds as the bet slip.
- Step 5: the balance is €115.50: the stake was deducted exactly once.
- Step 6: the modal closes, the selection and the stake are cleared, the balance is
  unchanged.
- Step 7: same result as step 6.

---

## TC-05: API rejects invalid bet requests and leaves the balance unchanged

**Priority:** Medium

**Risk rationale:** The UI can be bypassed by calling the API directly, so the server has
to enforce the rules itself. An accepted bet on an unknown match or an undefined
selection cannot be settled. The priority is Medium because a user cannot produce these
requests through the UI.

**Steps:**

1. Call `GET /api/matches` and take a valid match id.
2. Send each request in the table to `POST /api/place-bet`. Fields not named in the
   table hold valid values.
3. After each request, call `GET /api/balance`.

| Request                              | Status | Error code                |
| ------------------------------------ | ------ | ------------------------- |
| `selection: "WIN"`                   | 422    | `invalid_selection`       |
| `matchId: "no-such-match"`           | 422    | `invalid_match`           |
| `stake: 10.555`                      | 422    | `invalid_stake_precision` |
| Valid body, no `x-user-id` header    | 401    | `missing_user_id`         |

**Expected result:**

- Each request returns the status and the error code in the table.
- No response contains a bet confirmation.
- The balance is €125.50 after every request.

---

## TC-06: Odds filter: inclusive bounds, invalid range rejected

**Priority:** Low

**Risk rationale:** A wrong filter hides matches the user is looking for or shows matches
they excluded. That makes matches harder to find, but no money is at risk and the user
can still bet from the unfiltered list.

**Steps:**

1. Choose a match and note one of its three odds values, `V`.
2. Set the odds filter to minimum `V` and maximum `V`.
3. Set the minimum above the maximum, for example minimum `3.00` and maximum `2.00`.
4. Clear the filter.

**Expected result:**

- Step 2: the chosen match is listed, which shows that both bounds are inclusive. Every
  listed match has an odds value equal to `V`.
- Step 3: the range is rejected with a clear message. The list is not silently emptied.
- Step 4: the full match list is shown again.
