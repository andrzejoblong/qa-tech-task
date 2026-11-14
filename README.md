# qa-tech-task

QA take-home assignment for the **Single Bet Placement** feature of a demo sports betting app:
a test plan, execution results with bug reports, and a small automation framework
(Selenium WebDriver + Pytest for the UI, `requests` for the API).

## Deliverables

| Part | File |
| ---- | ---- |
| A.1 Test plan | [docs/test-plan.md](docs/test-plan.md) |
| A.2 Execution results and bug reports | [docs/execution-report.md](docs/execution-report.md) |
| B Automation framework and two tests | [framework/](framework/), [tests/](tests/) |
| C Strategy and recommendations | [docs/strategy.md](docs/strategy.md) |

## Requirements

- Python 3.11 or newer
- [Poetry](https://python-poetry.org/) 2.x
- Google Chrome (latest desktop version)

No separate chromedriver install is needed: Selenium Manager, built into Selenium 4,
downloads the driver that matches the installed Chrome.

## Setup

```bash
poetry install
export QA_USER_ID=<your-user-id>
```

## Configuration

Settings come from environment variables.

| Variable     | Required | Default                                 | Purpose                                                        |
| ------------ | -------- | --------------------------------------- | -------------------------------------------------------------- |
| `QA_USER_ID` | yes      | none                                    | User id issued with the assignment. A run without it fails at once. |
| `BASE_URL`   | no       | `https://qae-assignment-tau.vercel.app` | Application under test.                                        |
| `HEADLESS`   | no       | `1`                                     | Set to `0` to watch the browser.                               |

The user id identifies one person's balance, so it is not stored in the repository.
In CI it is a GitHub Actions secret.

## Running the tests

```bash
poetry run pytest               # both tests
poetry run pytest tests/api     # API test only
poetry run pytest tests/ui      # UI test only
HEADLESS=0 poetry run pytest tests/ui   # watch the browser
```

Expected result today: `5 passed, 1 xfailed`.

- `tests/api/test_stake_limits.py` is one test with five boundary values.
- `tests/ui/test_place_bet_e2e.py` is marked `xfail(strict=True)`. The journey works, but
  the receipt and the header balance deviate from the specification (BUG-03, BUG-04 and
  BUG-05 in the execution report). Only those known deviations count as an expected
  failure; any other failure fails the test. Once the defects are fixed the test turns
  red, which is the signal to remove the marker.

The tests reset the balance of the given user and place bets, so do not run two sessions
with the same user id at the same time.

## Static analysis

```bash
poetry run ruff check .
poetry run ruff format --check .
```

## Project layout

```
docs/                 test plan, execution report, screenshots
framework/
  config.py           settings read from the environment
  driver.py           Chrome WebDriver factory
  money.py            Decimal helpers for amounts
  api/client.py       HTTP client, one method per API endpoint
  pages/              page objects: main page, bet slip, receipt
tests/
  conftest.py         fixtures: settings, API client, test data, browser
  api/                API test
  ui/                 E2E UI test
.github/workflows/
  ci.yml              lint, then tests, on every push
```

A UI test that fails saves a screenshot to `artifacts/`.

## Use of AI

I worked on this assignment with Claude Code as a pair.

- **AI:** proposed candidate scenarios from the specification, drafted the framework
  code and the three documents, and suggested API commands.
- **Me:** chose the scope and tooling, ran every manual test and exploratory check in
  the application, confirmed each defect before it went into the report, and reviewed
  and approved every file.

## Tooling choices

- **Poetry**: the lock file gives a reviewer and CI the same dependency versions I ran locally.
- **Ruff**: one tool for linting and formatting, configured in `pyproject.toml`.
- **GitHub Actions**: runs the static checks and both tests on every push.
