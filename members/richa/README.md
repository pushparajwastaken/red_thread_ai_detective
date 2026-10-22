# Case Engine

Author: Richa Bharti

## Overview

This module is responsible for loading mystery case data into the system.

The Case Engine loads a case using a case ID and returns a valid CaseState object.

## Features

- Loads case data
- Stores canonical facts
- Stores fact metadata
- Stores evidence records
- Stores NPC grants
- Handles invalid case IDs

## Main Function

load_case(case_id: str)

Returns a valid CaseState object.

## Files Included

- case_engine.py
- test_case_engine.py

## Running Tests

python -m pytest members/richa/test_case_engine.py

## Test Status

5 passed

## Limitations

- Only CASE_001 is implemented.
- Timeline data is minimal.
- More cases can be added later.

## Notes

This implementation follows the shared contracts provided for the Red Thread project.