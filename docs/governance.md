# How this work maps to TOGAF and ITIL

A light mapping, to show where each artifact of this repository would sit in an enterprise process. Not a full framework implementation.

## TOGAF ADM

| ADM phase | In this repository |
|---|---|
| A — Architecture Vision | The request and constraints (README, sections 1–2) |
| B/C/D — Business, Information Systems, Technology Architecture | Target architecture and message lifecycle (README, section 4) |
| E — Opportunities and Solutions | Options considered and decision flow (README, section 3; ADR-001) |
| F — Migration Planning | Terraform stack as the implementation plan; lab 2 outline (README, section 8) |
| G — Implementation Governance | Tests performed against the decisions (README, section 5) |
| H — Architecture Change Management | Review triggers in the ADRs, technical debt register |
| Architecture Repository | `docs/adr/` and `docs/technical-debt-register.md` |

## ITIL

- **Standard change:** DLQ redrive following the [runbook](runbook-dlq-redrive.md) once the cause is fixed; enabling or disabling a consumer trigger for maintenance.
- **Normal change:** changes to retry parameters (`maxReceiveCount`, visibility timeout), to the key policy, or adding a consumer. Evidence: `terraform plan` output, ADR reference, test results.
- **Incident management:** DLQ depth above zero is an incident signal for the owning service; the runbook gives triage, fix and verification steps.
- **Emergency changes** made in the console or CLI are detected by the next `terraform plan` (tested in this lab) and must be reconciled in code.
