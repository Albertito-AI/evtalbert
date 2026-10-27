# Public software and private data boundary

## Public material

The repository may contain original source code, synthetic fixtures, documentation, tests and non-confidential examples that the contributor has the right to publish.

## Material that must not be committed publicly

- identifiable training or performance logs;
- health, psychological, emotional-state or biometric information;
- names, contact details, account identifiers or exact private locations;
- client, student, research-participant or employer records;
- unpublished research data or restricted third-party material;
- passwords, tokens, API keys, private keys or connection strings;
- production databases, exports or backups.

## Operational rule

Store real records in a separate private workspace. Collect only what is needed, document the purpose, restrict access, define retention and deletion, and remove direct identifiers where appropriate. An anonymisation option in software does not by itself prove that a dataset cannot be reidentified.

Before publishing an example, establish that it is synthetic or lawfully public, contains no confidential data, and does not expose a real person's history through combinations of indirect identifiers.

Removing a file from the current branch does not remove it from Git history. Suspected exposure requires containment, credential rotation where relevant, and a separate history-remediation decision.
