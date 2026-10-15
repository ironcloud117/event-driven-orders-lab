# Runbook — DLQ triage and redrive

Procedure tested in this lab (test 3 and 4). Replace `<service>` with `payments` or `inventory` and `<account-id>` with the account ID.

## 1. Recognise the situation

| Signal | Meaning | Go to |
|---|---|---|
| Main queue depth growing, DLQ empty | Consumer stopped (trigger disabled or throttled): no retries, nothing lost yet | Re-enable the trigger, check concurrency |
| DLQ depth growing | Consumer receives and fails: messages are being parked after 3 attempts | Step 2 |

```bash
aws sqs get-queue-attributes --queue-url https://sqs.eu-west-1.amazonaws.com/<account-id>/edo-lab-<service> \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible ApproximateAgeOfOldestMessage
aws sqs get-queue-attributes --queue-url https://sqs.eu-west-1.amazonaws.com/<account-id>/edo-lab-<service>-dlq \
  --attribute-names ApproximateNumberOfMessages
```

The counters are approximate: read them twice a few seconds apart before acting.

## 2. Find the cause

```bash
aws logs tail /aws/lambda/edo-lab-<service> --since 30m --format short | grep FAILED   # PowerShell: | Select-String FAILED
```

Inspect one parked message without consuming it for long: SQS console → DLQ → *Send and receive messages* → *Poll for messages*.
Polling makes the message invisible for the DLQ visibility timeout (30 s), then it returns.

## 3. Fix, then verify the configuration

Fix the consumer or the downstream system. If anything was changed by hand during the incident, bring the stack back to its declared state:

```bash
terraform plan -out tfplan    # must show only the expected changes
terraform apply tfplan
aws lambda wait function-updated --function-name edo-lab-<service>
```

Do not redrive before the fix is live: the messages would fail three more times and return to the DLQ.

## 4. Redrive

```bash
aws sqs start-message-move-task --source-arn arn:aws:sqs:eu-west-1:<account-id>:edo-lab-<service>-dlq
aws sqs list-message-move-tasks --source-arn arn:aws:sqs:eu-west-1:<account-id>:edo-lab-<service>-dlq \
  --query "Results[0].[Status,ApproximateNumberOfMessagesMoved]"
```

The destination is the original source queue (allowed by the redrive allow policy). For large backlogs add `--max-number-of-messages-per-second` to protect the downstream system.

## 5. Close

- DLQ and main queue at 0, success events in the logs for the redriven orders.
- Redriven messages have **new MessageIds**: reconcile by `orderId`.
- Check for duplicates in the downstream system until consumers are idempotent (TD-001).
- Record the incident: cause, number of orders affected, time parked.
