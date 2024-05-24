# ClearURLs Rules Merger

This is a script project that offers a `merger.py`
for merging your local custom rules (json file) with
github public rules.

When conflict occured, your local rules have a priority
than the public.

## Prerequisites

- python 3.12 or higher

## Installation

`git clone` this project

This project has no 3rd party dependencies.

## Usage

### Preparation

Replace `LOCAL_RULES_PATH: LiteralString = ...`
and `MERGED_PATH: LiteralString = ...` with yours.

### After ready

There are 2 ways to run:

1. Simply `python merger.py`

2. Or with args `python merger.py <path-to-your-custom-rules.json> <path-to-merged-rules.json>`
