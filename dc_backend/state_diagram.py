import graphviz
from constants import TIME_ACTIVE, TIME_COUNTDOWN, TIME_REST

dot = graphviz.Digraph(
    comment="DCP state transition diagram",
    graph_attr={
        "rankdir": "LR",
        "nodesep": "0.3",
        "ranksep": "0.3",
        "fontname": "Helvetica",
        "dpi": "300",
    },
    node_attr={
        "fontname": "Helvetica",
        "fontsize": "8",
    },
)


def format_node_str(label, time, status):
    return f"{label}\n({time}s)\n{status}\n"


active_nodeattr = {
    "shape": "circle",
    "style": "filled",
    "width": "1.3",
    "fixedsize": "true",
    "color": "lightblue",
}

countdown_nodeattr = {
    "shape": "rect",
    "width": "1.5",
    "height": "1",
    "fixedsize": "true",
    "label": format_node_str("Countdown", 3, "STATUS_TRANSITION"),
    "group": "countdown",
}

start_nodeattr = {
    "shape": "rectangle",
    "style": "filled",
    "width": "2",
    "fixedsize": "true",
    "color": "lime",
}

rest_nodeattr = {
    "shape": "rectangle",
    "style": "filled",
    "width": "2",
    "fixedsize": "true",
    "color": "pink",
}


dot.node("wait", format_node_str("Wait", 5, "STATUS_TRANSITION"), **start_nodeattr)

with dot.subgraph() as s:
    # s.attr(rank="same")
    s.node("countdown0", **countdown_nodeattr)
    s.node("baseline/rest", format_node_str("Baseline/rest", TIME_ACTIVE, "STATUS_BASELINE"), **active_nodeattr)
    s.node("countdown1", **countdown_nodeattr)
    s.node("imagine", format_node_str("Imagine", TIME_ACTIVE, "STATUS_IMAGINE"), **active_nodeattr)
    s.node("countdown2", **countdown_nodeattr)
    s.node("look", format_node_str("Look", TIME_ACTIVE, "STATUS_LOOK"), **active_nodeattr)
    s.node("countdown3", **countdown_nodeattr)
    s.node(
        "imagine_eyes_closed",
        format_node_str("Imagine Eyes Closed", TIME_ACTIVE, "STATUS_IMAGINE_EYES_CLOSED"),
        **active_nodeattr,
    )
    s.node("rest", format_node_str("Rest", TIME_REST, "STATUS_TRANSITION"), **rest_nodeattr)

    s.edge("countdown0", "baseline/rest")
    s.edge("baseline/rest", "countdown1")
    s.edge("countdown1", "imagine")
    s.edge("imagine", "countdown2")
    s.edge("countdown2", "look")
    s.edge("look", "countdown3")
    s.edge("countdown3", "imagine_eyes_closed")
    s.edge("imagine_eyes_closed", "rest")
    dot.edge("rest", "countdown0")



    # alignment edges
    dot.edge("countdown0", "countdown1", style="invis")
    dot.edge("countdown1", "countdown2", style="invis")
    dot.edge("countdown2", "countdown3", style="invis")
    dot.edge("countdown3", "rest", style="invis")

    dot.edge("look", "imagine_eyes_closed", style="invis")




dot.edge("wait", "countdown0")
dot.node("done", "Done", **start_nodeattr)
dot.edge("imagine_eyes_closed", "done")

dot.render("state_diagram", format="png")
