"""Decision flow (broker choice) and message lifecycle (failure handling).

Run from the repository root:
    python docs/diagrams/flows.py
Produces docs/decision-flow.{png,svg} and docs/message-lifecycle.{png,svg}.
Plain Graphviz, no cloud icons: these are logical flows, not architecture.
"""

from pathlib import Path

import graphviz

DOCS = Path(__file__).resolve().parents[1]

FONT = "DejaVu Sans"
START = {"shape": "box", "style": "rounded,filled", "fillcolor": "#F2F0EB", "color": "#8C8578"}
QUESTION = {"shape": "diamond", "style": "filled", "fillcolor": "#E6F0FA", "color": "#1F5FA8"}
REJECT = {"shape": "box", "style": "rounded,filled", "fillcolor": "#FBEDE7", "color": "#A33A1A"}
CHOSEN = {"shape": "box", "style": "rounded,filled", "fillcolor": "#E3F4EC", "color": "#1E7350"}
STATE = {"shape": "box", "style": "rounded,filled", "fillcolor": "#E6F0FA", "color": "#1F5FA8"}


def new_graph(name: str, rankdir: str = "TB") -> graphviz.Digraph:
    g = graphviz.Digraph(name)
    g.attr(rankdir=rankdir, fontname=FONT, pad="0.4", nodesep="0.5", ranksep="0.6")
    g.attr("node", fontname=FONT, fontsize="12")
    g.attr("edge", fontname=FONT, fontsize="11", color="#555555")
    return g


def decision_flow() -> graphviz.Digraph:
    g = new_graph("decision_flow")
    g.node("start", "One order event, several independent\nconsumers (payments, inventory)", **START)
    g.node("q1", "Millions of events/s, replay\nor strict per-key ordering\nas a core requirement?", **QUESTION)
    g.node("msk", "Amazon MSK (Kafka):\nreplay and ordering,\ncluster to size and operate", **REJECT)
    g.node("q2", "Routing on event content\nacross many producers\nand SaaS sources?", **QUESTION)
    g.node("eb", "Amazon EventBridge:\ncontent rules, schema registry;\nno per-consumer buffer by itself", **REJECT)
    g.node("q3", "Each consumer must survive\nits own outage without\nlosing or blocking others?", **QUESTION)
    g.node("direct", "Direct async Lambda invoke:\ncoupled, no buffer to inspect", **REJECT)
    g.node("chosen", "SNS fan-out + one SQS queue\nper consumer + DLQ:\nbuffer, retry, isolation, serverless", **CHOSEN)

    g.edge("start", "q1")
    g.edge("q1", "msk", label="yes")
    g.edge("q1", "q2", label="no")
    g.edge("q2", "eb", label="yes, primary need")
    g.edge("q2", "q3", label="no / not yet")
    g.edge("q3", "direct", label="no")
    g.edge("q3", "chosen", label="yes")
    return g


def message_lifecycle() -> graphviz.Digraph:
    g = new_graph("message_lifecycle", rankdir="LR")
    g.node("pub", "Published\nto SNS topic", **START)
    g.node("queued", "Visible in\nconsumer queue", **STATE)
    g.node("inflight", "In flight\n(received, invisible 60s)", **STATE)
    g.node("done", "Deleted:\nprocessed once", **CHOSEN)
    g.node("dlq", "In DLQ\n(kept 14 days)", **REJECT)
    g.node("fix", "Consumer fixed\n(terraform apply)", **START)

    g.edge("pub", "queued", label="fan-out copy")
    g.edge("queued", "inflight", label="Lambda poll\n(trigger enabled)")
    g.edge("inflight", "done", label="success")
    g.edge("inflight", "queued", label="failure, receive < 3:\nvisible again after 60s", color="#A33A1A", style="dashed")
    g.edge("inflight", "dlq", label="after 3 failed receives", color="#A33A1A", style="dashed")
    g.edge("dlq", "fix", label="investigate", style="dotted")
    g.edge("fix", "queued", label="start-message-move-task\n(new MessageId)", color="#1E7350")
    g.edge("queued", "queued", label="trigger disabled:\naccumulates, nothing lost", style="dotted")
    return g


if __name__ == "__main__":
    for graph, name in ((decision_flow(), "decision-flow"), (message_lifecycle(), "message-lifecycle")):
        for fmt in ("png", "svg"):
            graph.format = fmt
            graph.render(filename=name, directory=str(DOCS), cleanup=True)
