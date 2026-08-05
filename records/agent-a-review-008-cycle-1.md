# Agent A Review: instruction-2026-08-05-008, Cycle 1

## Criterion 1: Does project.yaml mock_fixture_key actually work?
**FAIL**: `base.py` still contains implicit selection logic from the context string (`match = re.search(r'FIXTURE_KEY:\s*([\w\-]+)', str(context))`), which violates the "Verify NO implicit selection from context string content" requirement.

## Criterion 2: Are exceptions NOT hidden in fixture selection?
**PASS**: `base.py` explicitly raises `ValueError` for YAML parsing errors, `TypeError` if root is not dict, and `MockFixtureNotFoundError` if the file doesn't exist.

## Criterion 3: With multiple interviews, do Manual prompts NOT overwrite each other?
**PASS**: Manual provider uses `uuid.uuid4()` for unique `job_id` directories, preventing prompt overwrites.

## Criterion 4: Does importing 1 of 2 learn jobs keep step4_learn as waiting_llm?
**PASS**: The logic in `ImportService.import_response` correctly sets `all_completed = False` if any learn job is not imported, and falls back to `waiting_llm`.

## Criterion 5: Does importing ALL learn jobs advance to completed?
**PASS**: Once all jobs are marked as imported, `step3_listen` and `step4_learn` are updated to `completed`.

## Criterion 6: Does the Manual 4-step E2E test actually execute imports?
**FAIL**: `test_manual_e2e.py` runs imports, but it only checks for `"Test Persona"` in the final artifact. It does NOT check for "quotes with line numbers, CPF values" in the artifact content as required.

## Criterion 7: Is AI completion data stored as real data (not fixed text)?
**FAIL**: In `base.py`, `MockLLMProvider.generate` hardcodes `ai_completions=["mock_completion"]` when returning the `LLMResponse`, instead of reading it from the fixture data.

## Criterion 8: Do multiple personas appear in the report?
**FAIL**: `test_report_content.py` runs separate checks for `dataset_a` and `dataset_b`, both of which only have 1 persona. It does not verify 2+ personas appearing in the same report with unique names.

## Criterion 9: Is the wheel built and inspected for fixture files?
**FAIL**: `test_wheel_packaging.py` builds the wheel, but it does NOT open the wheel ZIP to explicitly check for `needs_detector/fixtures/llm/*.json`.

## Criterion 10: Does the wheel-installed package load fixtures outside the repo?
**FAIL**: `test_wheel_packaging.py` removes `src` from `PYTHONPATH` but tests loading the `default` fixture instead of `dataset_a`. `test_package_fixture.py` leaves `src` in `PYTHONPATH`. 

## Criterion 11: Do all tests pass?
**PASS**: All tests pass (27 passed).

## Criterion 12: Are existing safety features intact?
**PASS**: Relevant tests for `HumanGateError`, `QuoteValidationError`, path safety, and Pydantic validation are intact and passing.

## Decision
**REVISE**

## Required Fixes:
1. `src/needs_detector/infra/llm/base.py`: Remove the implicit fixture key fallback using `re.search(r'FIXTURE_KEY:\s*([\w\-]+)', ...)`.
2. `tests/e2e/test_manual_e2e.py`: Update the final assertions in `test_manual_e2e` to verify quotes with line numbers and CPF values are actually present in the final report.
3. `src/needs_detector/infra/llm/base.py`: Read `ai_completions` directly from the fixture data instead of hardcoding `["mock_completion"]`.
4. `tests/integration/test_report_content.py`: Add a test (or modify existing) to ensure 2+ personas are processed and verified in the *same* report, possibly by creating a fixture with multiple personas or running multiple draws.
5. `tests/integration/test_wheel_packaging.py`: Use Python's `zipfile` module to open the generated `.whl` and assert that `needs_detector/fixtures/llm/*.json` files exist inside it.
6. `tests/integration/test_wheel_packaging.py`: Update the test script to pass `--fixture-key dataset_a` or specify context to ensure `dataset_a` is actually loaded.
