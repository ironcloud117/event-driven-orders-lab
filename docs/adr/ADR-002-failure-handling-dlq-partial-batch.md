# ADR-002 — Failure handling: retries, dead-letter queues and partial batch response

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-15 |
| Deciders | Cloud architect (author), service owners, operations |
| Related | [ADR-001](ADR-001-messaging-backbone-sns-sqs.md), [Runbook](../runbook-dlq-redrive.md), [Technical debt register](../technical-debt-register.md) |

## Context

Consumers depend on external systems (payment provider, warehouse system) that can be slow or unavailable.
A failed order must be retried a limited number of times, then parked for investigation without blocking the queue,
and replayed once the cause is fixed. One bad record in a batch must not force the whole batch to be reprocessed.

## Options considered

1. **Retry inside the function** (loops, sleeps). Burns billed duration, hides the failure, and still loses the message if the function times out.
2. **Whole-batch retry** (default Lambda behaviour with SQS). One failure makes every message of the batch visible again: duplicates and wasted work.
3. **Partial batch response + SQS redrive policy + DLQ + managed redrive.** The function reports only failed records; SQS counts receives,
   moves a message to the DLQ after N failures and keeps it there for analysis; an operator replays it with a managed task.

## Decision

Option 3, with these parameters:

| Parameter | Value | Reason |
|---|---|---|
| `maxReceiveCount` | 3 | Enough to absorb transient errors, short enough to park a broken flow in minutes |
| Visibility timeout | 60 s | At least 6× the function timeout (10 s); also acts as the backoff between attempts |
| DLQ retention | 14 days (maximum) | Longer than the 4 days of the source queue: the original enqueue timestamp is kept, so a shorter retention could expire messages before analysis |
| Function response type | `ReportBatchItemFailures` | Only failed records are retried |
| Redrive allow policy | By queue, own source queue only | A DLQ cannot be used by other queues by mistake |
| Redrive | `aws sqs start-message-move-task` | Managed, auditable, rate-controlled; no custom script |
| Event source mapping maximum concurrency | 2 | Protects downstream systems and budget during a backlog |

## Rationale

Verified in the lab: a failing consumer received each message three times about 60 s apart, then the messages appeared in the DLQ with the original body;
after the fix, the redrive task moved them back and they were processed. A disabled trigger, by contrast, left messages waiting in the main queue without retries.

## Consequences

**Positive**
- No message loss during an outage of a downstream system shorter than the retention.
- Failures are visible as a number (DLQ depth) and as data (the parked messages).

**Negative / risks**
- Redriven messages are new messages (new MessageId, receive count reset): tracing must rely on a business key or correlation ID.
- Retries and redrive produce duplicates: consumers must be idempotent (TD-001).
- Fixed backoff (visibility timeout), no exponential backoff: acceptable here, to revisit for rate-limited downstream APIs.
- Without alarms on DLQ depth, parked messages can go unnoticed until retention expires (TD-003).

## Review triggers

- Downstream outages typically longer than about 3 minutes: raise `maxReceiveCount` or the visibility timeout.
- Rate-limited downstream API: add exponential backoff (change visibility per message) or a throttled consumer.
