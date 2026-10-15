"""Architecture diagram for the event-driven orders lab.

Run from the repository root:
    python docs/diagrams/architecture.py
Produces docs/architecture.png and docs/architecture.svg (icons embedded).
"""

from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.general import GenericSDK
from diagrams.aws.integration import SimpleNotificationServiceSnsTopic, SimpleQueueServiceSqsQueue
from diagrams.aws.management import CloudwatchLogs
from diagrams.aws.security import IdentityAndAccessManagementIamRole, KeyManagementService

from embed_icons import embed_icons

OUT = Path(__file__).resolve().parents[1] / "architecture"

graph_attr = {
    "fontsize": "20",
    "fontname": "DejaVu Sans",
    "pad": "0.5",
    "nodesep": "0.7",
    "ranksep": "1.2",
    "splines": "spline",
}
node_attr = {"fontname": "DejaVu Sans", "fontsize": "12"}
edge_attr = {"fontname": "DejaVu Sans", "fontsize": "11", "color": "#555555"}

ok = {"color": "#232F3E", "penwidth": "1.6"}
failure = {"color": "#C7511F", "style": "dashed", "penwidth": "1.4"}
crypto = {"color": "#7AA116", "style": "dotted", "penwidth": "1.2", "constraint": "false"}

for fmt in ("png", "svg"):
    with Diagram(
        "Event-driven orders: SNS fan-out to SQS with DLQ and Lambda consumers",
        filename=str(OUT),
        outformat=fmt,
        show=False,
        direction="LR",
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ):
        producer = GenericSDK("Orders service\n(simulated: aws sns publish)")

        with Cluster("AWS account - eu-west-1"):
            kms = KeyManagementService("KMS customer managed key\nalias/edo-lab-messaging")
            topic = SimpleNotificationServiceSnsTopic("SNS topic\nedo-lab-orders\n(SSE-KMS)")

            with Cluster("Payments service"):
                pay_q = SimpleQueueServiceSqsQueue("edo-lab-payments\nvisibility 60s")
                pay_dlq = SimpleQueueServiceSqsQueue("edo-lab-payments-dlq\nretention 14d")
                pay_fn = Lambda("edo-lab-payments\npython3.13 arm64")
                pay_role = IdentityAndAccessManagementIamRole("payments role\nown queue only")
                pay_logs = CloudwatchLogs("/aws/lambda/\nedo-lab-payments")

            with Cluster("Inventory service"):
                inv_q = SimpleQueueServiceSqsQueue("edo-lab-inventory\nvisibility 60s")
                inv_dlq = SimpleQueueServiceSqsQueue("edo-lab-inventory-dlq\nretention 14d")
                inv_fn = Lambda("edo-lab-inventory\npython3.13 arm64")
                inv_role = IdentityAndAccessManagementIamRole("inventory role\nown queue only")
                inv_logs = CloudwatchLogs("/aws/lambda/\nedo-lab-inventory")

        producer >> Edge(label="publish order", **ok) >> topic
        topic >> Edge(label="raw delivery", **ok) >> pay_q
        topic >> Edge(label="raw delivery", **ok) >> inv_q

        pay_q >> Edge(label="poll, batch 10\npartial failures", **ok) >> pay_fn
        inv_q >> Edge(label="poll, batch 10\npartial failures", **ok) >> inv_fn
        pay_fn >> Edge(**ok) >> pay_logs
        inv_fn >> Edge(**ok) >> inv_logs

        pay_q >> Edge(label="after 3 receives", **failure) >> pay_dlq
        inv_q >> Edge(label="after 3 receives", **failure) >> inv_dlq
        pay_dlq >> Edge(label="redrive", **failure) >> pay_q

        pay_role >> Edge(style="dotted", color="#888888") >> pay_fn
        inv_role >> Edge(style="dotted", color="#888888") >> inv_fn

        kms >> Edge(label="encrypts", **crypto) >> topic
        kms >> Edge(**crypto) >> pay_q
        kms >> Edge(**crypto) >> inv_q

    if fmt == "svg":
        embed_icons(OUT.with_suffix(".svg"))
