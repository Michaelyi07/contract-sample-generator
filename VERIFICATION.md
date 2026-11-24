# VERIFICATION

All commands below were executed for real; outputs are pasted verbatim
from the captured runs (stdout; a pytest deprecation warning about
asyncio fixture scope was present on stderr and carries no information).
Environment: Windows (local machine), Python and pinned dependency
versions shown below.


## Environment

```
Python 3.13.14
```
```
python -m pip show reportlab Pillow pypdfium2 pytest | findstr /R "^Name ^Version"
Name: reportlab
Version: 5.1.0
Name: pillow
Version: 13.0.0
Name: pypdfium2
Version: 5.15.2
Name: pytest
Version: 9.2.0
```

## AC-0 delivered samples = seed-42 output (cross-check)

```
delivered samples files: 80
files differing from a fresh seed-42 run: 0
doc_01_standard_clause.pdf (delivered samples):
  938858025405143860425101284794b6d666be6d5e2ced8a26039abbba5880f0
```

## AC-1 determinism: two runs with seed 42, sha256 over all files

```
files compared: 80
mismatched files: 0
doc_01_standard_clause.pdf
  vr1: 938858025405143860425101284794b6d666be6d5e2ced8a26039abbba5880f0
  vr2: 938858025405143860425101284794b6d666be6d5e2ced8a26039abbba5880f0
doc_01_standard_clause.ground_truth.json
  vr1: 86fc7620ebcc117b6e6dfe93a5362b0e3120a125a6035fbc18ab9fad70c45f8a
  vr2: 86fc7620ebcc117b6e6dfe93a5362b0e3120a125a6035fbc18ab9fad70c45f8a
```

## AC-2 USCC: independent GB 32100 validator over all ground_truth files

```
ground_truth files: 40
uscc codes checked: 80
checksum pass: 80
digits 3-8 == 999999: 80
examples: 919999992JD10267GQ 919999996NLNHD7EJ6
```

## AC-3 snippet-in-page auto-validation (text-layer PDFs)

```
docs checked (text-layer): 16
snippets checked: 233
failures: []
```

## AC-4 spot-check set + no-real-subject gate

Spot-check PNGs exported from the delivered samples (committed under spotcheck/):
2 scan (rotation/noise/blur/red seal visible), 2 photo (perspective/shadow), 1 text.

```
doc_01_standard_clause_page1.png
doc_02_standard_clause_page1.png
doc_03_standard_clause_page1.png
doc_05_standard_clause_page1.png
doc_06_standard_clause_page1.png
```
```
............................                                             [100%]
```
