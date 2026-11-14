# Strategy and Recommendations

## Why these two tests

The choice follows the same rule as the test plan: automate first where a defect costs
the most and where the check has to be repeated on every change.

**UI: place a single bet (TC-01).** It is the core money flow and the only journey that
crosses every part of the feature: match list, bet slip, placement, receipt and balance.
It has to be re-checked on every release, and doing that by hand means comparing the
bet slip, the receipt and the balance value by value each time. The manual run found three defects on this path
(BUG-03, BUG-04, BUG-05), and the test now reports all three by ID.

**API: stake limits at the boundaries (TC-03).** The limits are a business rule, and the
server is the only place where the rule is binding, because the UI can be bypassed. The
check is fast, deterministic and data-driven: one test, five boundary values. It passes
today, so it works as a regression guard from the first run.

**Candidates not chosen:**

| Candidate | Why not now |
| --------- | ----------- |
| Insufficient balance through the API (TC-02) | The most important rule after the main flow, but it fails today (BUG-01). With it, both tests would be expected failures and the suite would give no passing signal. It is the first test to add next. |
| Bet on a past match through the API | Same situation (BUG-02). Second test to add. |
| Invalid requests (TC-05) | Lower risk: a user cannot produce these requests through the UI. |

**Known defects in automated tests.** The UI test is marked `xfail(strict=True)` and
accepts only one exception, raised for deviations already reported as bugs. A green run
therefore means "nothing new is broken". When the defects are fixed, the test turns red
and the marker has to be removed. Any other failure in the journey fails the test.

## What stays manual, and why

- **Failed placement and `Rebet` (TC-04).** The application offers no deterministic way to
  make placement fail. Forcing it from the browser needs network interception, which is
  fragile in Selenium. It stays manual until a failure can be triggered through a test
  hook or a mocked backend.
- **Double submission of `Place Bet`.** The result depends on timing. In the UI it would be
  a flaky test. The rule behind it (409 for a second bet in progress) is better checked at
  the API with two concurrent requests.
- **Receipt content and layout.** A person noticed at once that the receipt has no
  selection field (BUG-06) and that the timestamp has no date. A script only checks what
  it was told to look for.
- **Filters (TC-06).** Low risk, no money involved, and the specification does not define
  how the odds filter treats the three odds of a match. Automating before that is settled
  would fix a guess in code.
- **Exploratory testing.** Four of the nine defects (BUG-02, BUG-07, BUG-08, BUG-09) were
  found outside the scripted steps:
  by reloading the page, calling the API directly and reading every field of a response.

## Recommendations if the project scales

### 1. Give the tests data they control

The suite depends on shared, ageing data. Today 91 of 103 matches are in the past, and
the tests pick the first upcoming one; when the last kickoff date passes, they stop
working. All runs share one user and one balance, so tests cannot run in parallel, and
the only reset endpoint stores a different amount than it reports (BUG-07).

What is needed: matches seeded per environment with dates relative to today, a user
created per test run, and a reset that can be trusted. This is the precondition for
everything else in this section.

### 2. Move rule checks to the API and keep the UI layer thin

Both Critical defects (BUG-01, BUG-02) are in the server and can be shown with a single
request. Balance, limits, match status and input validation belong in a broad API suite
that runs in seconds on every commit, together with a contract check of responses
against the OpenAPI document; that check would have caught the `USD` currency (BUG-09).
The UI suite should stay at a few journeys that prove the layers are connected. CI
already runs lint and both tests on every push; the next steps are a scheduled run
against the deployed environment and a test report published with each run.

### 3. Resolve the open points in the specification before automating further

A test can only be as correct as the rule it encodes. Four points need a decision:

- minimum stake: €1.00 (sections 3 and 4.4) or €1.01 (section 4.1);
- how a payout with more than two decimals is rounded (the UI rounds, the API cuts);
- the status and error code for insufficient balance;
- whether a match passes the odds filter on one of its odds or on all three.

Each open point is currently a place where the UI, the API and the tests can each be
"right" in a different way.
