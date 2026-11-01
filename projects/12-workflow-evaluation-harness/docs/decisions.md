# Design decisions for the first release

The case set uses JSON schema version 1. IDs are unique within a case set. The case hash uses UTF8 JSON with sorted keys and compact separators. The hash identifies the content rather than the formatting of the source file.

Both adapters receive independent copies of the same case and settings. The initial adapters are local and synchronous. There is no timeout in this release. A remote adapter must add a time limit and cancellation before it is introduced.

Expected fields are scored only for cases that should be accepted. A missing field, wrong value, adapter error or inappropriate abstention counts as an incorrect field. Field comparison requires the same JSON value type. Abstention is scored for every case. Execution errors make the gate incomplete rather than silently passing.

The demonstration rules require at least three cases. The candidate may not have a lower field accuracy than the baseline and must match every expected abstention. These values exercise the mechanism. They are not approved thresholds for real decisions.

The command returns zero for a passing gate, one for a failing gate, two for an incomplete gate and three for invalid input or an output error. The gate does not deploy anything. A person owns any release decision.
