import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SERVICE = "payments"


def handler(event, context):
    simulate_failure = os.environ.get("SIMULATE_FAILURE", "false").lower() == "true"
    failures = []

    for record in event["Records"]:
        message_id = record["messageId"]
        receive_count = record["attributes"]["ApproximateReceiveCount"]
        try:
            order = json.loads(record["body"])
            if simulate_failure:
                raise RuntimeError("Simulated payment gateway outage")

            logger.info(json.dumps({
                "service": SERVICE,
                "event": "PAYMENT_AUTHORIZED",
                "orderId": order["orderId"],
                "amount": order["total"],
                "currency": order["currency"],
                "messageId": message_id,
                "receiveCount": receive_count,
            }))
        except Exception as exc:
            logger.error(json.dumps({
                "service": SERVICE,
                "event": "PAYMENT_FAILED",
                "messageId": message_id,
                "receiveCount": receive_count,
                "error": str(exc),
            }))
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}