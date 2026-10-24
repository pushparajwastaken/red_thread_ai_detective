
# Submission

Name: Richa Bharti

## Assigned Module

Case Engine

## Function Implemented

load_case(case_id: str) -> CaseState

## Work Done

Implemented a case loading module based on the shared project contract.

The module:

- Loads CASE_001
- Stores canonical facts
- Stores fact metadata
- Stores evidence records
- Stores NPC grants
- Validates invalid case IDs using ContractError

## Files Submitted

- case_engine.py
- test_case_engine.py
- README.md
- SUBMISSION.md

## Run Command

python -m pytest members/richa/test_case_engine.py

## Test Results

5 passed in 0.15s

## Dependencies

pytest

No additional dependencies were required.

## Challenges Faced

- Understanding the relationship between facts, evidence and NPC grants.
- Matching implementation with the shared contracts.

## Known Limitations

- Only CASE_001 is implemented.
- Timeline data is minimal.
- Additional mystery cases can be added later.

## Status

Completed and tested successfully.