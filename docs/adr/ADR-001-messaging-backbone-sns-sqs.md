# ADR-001 — Messaging backbone: SNS fan-out to SQS queues

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-15 |
| Deciders | Cloud architect (author), service owners |
| Related | [ADR-002](ADR-002-failure-handling-dlq-partial-batch.md), [ADR-003](ADR-003-encryption-customer-managed-kms.md), [Technical debt register](../technical-debt-register.md) |

## Context

An order must trigger independent work in several services (payments, inventory, later notifications and analytics).
Synchronous calls couple the order flow to the slowest and least available service, and a failed call is lost.

Constraints: no message loss, failure isolation between consumers, encryption with a customer controlled key,
least privilege per service, serverless and managed services only, everything as code.
Expected volume is in the order of thousands of orders per hour, with peaks; no requirement for replay of history or strict global ordering.

## Options considered

1. **Synchronous calls or direct asynchronous Lambda invocation.** Simple, but the producer must know every consumer,
   and there is no buffer an operator can inspect, pause or drain.
2. **Amazon MSK (Kafka).** Consumer groups, replay from any offset, per-partition ordering, very high throughput.
   Requires sizing brokers and partitions, upgrades and capacity management; no dead-letter queue out of the box.
3. **Amazon EventBridge.** Serverless bus with content-based routing rules, schema registry, archive and replay, many native targets.
   Retries and a DLQ are configured per target, but there is no per-consumer queue to pause, inspect or throttle unless SQS is added as the target.
4. **SNS topic with one SQS queue per consumer.** The topic copies every order to each subscribed queue; each queue buffers,
   retries and parks failures (DLQ) for its own consumer, independently of the others.

## Decision

Use **one SNS standard topic for order events and one SQS standard queue per consuming service**, each with its own DLQ.
Consumers are Lambda functions triggered by an event source mapping on their queue.

## Rationale

- Fan-out without the producer knowing the consumers: adding a service is a new subscription and queue.
- Each consumer has its own buffer and failure domain: verified in the lab by stopping and breaking the payments consumer while inventory kept processing.
- Retry, DLQ and redrive are native features of SQS (see ADR-002).
- Fully serverless, pay per request, no capacity to plan at this volume.
- MSK capabilities (replay, ordering, very high throughput) are not required and would add operational load.

## Consequences

**Positive**
- Loose coupling and independent scaling and deployment of each service.
- Clear operational signals per service: queue depth, age of oldest message, DLQ depth.

**Negative / risks**
- Standard queues and topics deliver at least once and without strict ordering: consumers must be idempotent (TD-001) and must not rely on order.
- No content-based routing beyond SNS filter policies on message attributes or body; complex routing would favour EventBridge.
- No replay of past events beyond what is still in the queues (SNS message archiving exists only for FIFO topics).

## Review triggers

- Strict ordering per order or per customer becomes a requirement: evaluate SNS FIFO + SQS FIFO with message group per `orderId`.
- Routing rules multiply, or events come from SaaS sources: evaluate EventBridge with SQS queues as targets.
- Replay of history or sustained very high throughput becomes a requirement: evaluate MSK or Kinesis.
