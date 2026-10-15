# ADR-003 — Encryption at rest with a customer managed KMS key

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-15 |
| Deciders | Cloud architect (author), security |
| Related | [ADR-001](ADR-001-messaging-backbone-sns-sqs.md) |

## Context

Order messages contain customer and payment-related data and must be encrypted at rest in the topic and in every queue,
with access to the data controllable per service and auditable.

## Options considered

1. **SSE-SQS** (keys managed by SQS). Free and transparent, but no key policy as a second layer of control, no per-call audit in CloudTrail,
   and it does not cover the SNS topic.
2. **AWS managed key `aws/sqs`.** Its key policy cannot be changed, so SNS cannot be allowed to use it: an SNS topic cannot deliver to queues encrypted with it.
3. **Customer managed KMS key.** Key policy under our control, CloudTrail record of every use, automatic rotation, usable by SNS when allowed in the key policy.

## Decision

One **customer managed symmetric key** (`alias/edo-lab-messaging`) for the topic and all queues, with automatic rotation and a 7-day deletion window.

Key policy: account administration delegated to IAM; SNS allowed `GenerateDataKey*` and `Decrypt` only when the source is the orders topic (`aws:SourceArn`),
which prevents the confused deputy problem. Consumer roles get `kms:Decrypt` only through SQS (`kms:ViaService`).

## Consequences

**Positive**
- Two independent layers of control on the data: queue policy / IAM and key policy.
- Every decrypt is logged in CloudTrail.

**Negative / risks**
- Monthly fee per key and per-request charges; mitigated by data key reuse (300 s) on the queues.
- Deleting the key makes any remaining data unreadable: the 7-day pending-deletion window is the safety net.
- One key shared by all services: per-service keys would be the next step if data classification differs between services.
