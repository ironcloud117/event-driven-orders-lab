# Technical debt register

Debt accepted consciously, with an owner, a reason and an exit condition. Each entry links to the decision that created it or the lab finding that revealed it.

| ID | Item | Reason accepted | Risk | Compensating controls | Owner | Exit trigger | Review | Status |
|---|---|---|---|---|---|---|---|---|
| TD-001 | Consumers are not idempotent | Lab scope: focus on transport and failure handling ([ADR-002](adr/ADR-002-failure-handling-dlq-partial-batch.md)) | High in production: duplicates from at-least-once delivery and redrive cause double payments or double reservations. Observed in the lab: the same order processed several times | None in the lab | Service owners | Conditional write on `orderId` per service (DynamoDB or Powertools Idempotency) | Lab 2 | Open |
| TD-002 | DLQs have no deny-insecure-transport statement | Main queues were prioritised; DLQs receive only from SQS redrive | Low: access still needs IAM permissions | IAM least privilege, KMS encryption | Cloud architect | Same queue policy statement applied to DLQs | Lab 2 | Open |
| TD-003 | No alarms on DLQ depth or age of oldest message | Lab scope | High in production: parked orders unnoticed until retention expires (14 days) | Manual checks in the runbook | Operations | CloudWatch alarms on `ApproximateNumberOfMessagesVisible` (DLQ) and `ApproximateAgeOfOldestMessage` (main queues) with notification | Lab 2 | Open |
| TD-004 | No end-to-end tracing or correlation ID | Lab scope | Medium: redrive changes the MessageId; troubleshooting relies on `orderId` in logs | Structured JSON logs with `orderId` | Service owners | X-Ray tracing and a correlation ID carried in the event body | Lab 2 | Open |
| TD-005 | Producer simulated with the CLI, no system of record | Lab scope | Medium: the dual-write problem (save order, then publish) is not addressed | None | Cloud architect | Orders API + DynamoDB with outbox or DynamoDB Streams | Lab 2 | Open |
| TD-006 | Event schema not versioned or validated | Lab scope | Medium: a producer change can break consumers silently; malformed events end in the DLQ | DLQ catches poison messages | Service owners | Versioned schema (field `version`) and validation at the consumer or EventBridge schema registry | Before production | Open |
| TD-007 | Terraform state is local | Single-person disposable lab | Medium: state not shared, not locked, not backed up | State never committed (`.gitignore`) | Cloud architect | Encrypted S3 backend with native locking | Before shared use | Open |
| TD-008 | Failure path tested only on the payments consumer | Same code path for both consumers | Low | Identical configuration through `for_each` | Cloud architect | Repeat test 3 on inventory, or automate the tests | Lab 2 | Open |

## How to use it

- Every **Accepted** decision or test finding that leaves a known gap creates an entry here.
- Entries are reviewed on the stated cadence; the status moves to *Closed* only when the exit trigger is met.
