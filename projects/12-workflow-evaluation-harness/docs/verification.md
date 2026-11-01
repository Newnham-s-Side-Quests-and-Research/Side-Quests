# Verification record

The initial local implementation was checked with Python 3.13 on Windows. The test suite was also run from a clean temporary copy without network access. All six tests passed.

The tests cover case validation and canonical hashing. They check that both adapters receive independent copies of the same inputs. They check field and abstention scoring against known answers. They exercise incomplete gates when an adapter fails or required data is missing.

The command line was run through the tests with four candidates. The sound candidate passed. The candidates with a wrong field, an incorrect acceptance and an incorrect abstention each failed the gate. The tests also check report creation and command exit codes.

These are synthetic checks of the initial mechanism. They do not establish accuracy on real documents. No model, remote service, performance target or deployment decision was tested. Independent human review remains outstanding.
