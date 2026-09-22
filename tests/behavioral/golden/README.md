# Golden Reference Governance

`v1.json` was created from the first reviewed packaged model after training against the checksum-pinned dataset snapshot. It records the exact dataset and model hashes, command, model version, expected policy output, and a small numeric tolerance for platform-level floating-point differences.

A failing golden test is a change signal. Do not regenerate this file merely to make CI pass. First identify whether data, feature processing, model dependencies, serialization, or policy changed. Update the golden reference only after intentional change review, explain the reason in the provenance block, and increment the schema/reference version when compatibility changes.

