# pylint: disable=missing-module-docstring, w0401, w0614, c0301

from copy import deepcopy
from igraph import *


def isomorphic_in_list(graph, graph_list):
    """Returns if the graph is isomorphic to any of the graphs in the given list.

    Parameters:
        graph (igraph.Graph): A graph
        graph_list ([igraph.Graph]): A list of graphs

    Returns:
        True if graph is isomorphic to a graph in graph_list
        False otherwise
    """

    if not graph_list:
        return False

    edge_color1 = []
    for edge in graph.es:
        edge_color1.append(ord(edge["label"]) - 97)

    for compare_graph in graph_list:
        edge_color2 = []
        for edge in compare_graph.es:
            edge_color2.append(ord(edge["label"]) - 97)

        if graph.isomorphic_vf2(
            compare_graph, edge_color1=edge_color1, edge_color2=edge_color2
        ):
            return True
    return False


def lists_same(graph_list_1, graph_list_2):
    """Returns if for every graph in graph_list_1 there is one isomorphic to it in graph_list_2.

    Parameters:
        graph_list_1 ([igraph.Graph]): A list of graphs
        graph_list_2 ([igraph.Graph]): A second list of graphs

    Returns:
        True if lists are same
        False otherwise
    """
    for graph in graph_list_1:
        if not isomorphic_in_list(graph, graph_list_2):
            return False
    for graph in graph_list_2:
        if not isomorphic_in_list(graph, graph_list_1):
            return False
    return True


def remove_disconnected_vertices(graph):
    """Returns a graph where all nodes are reachable from the initial node.

    Parameters:
        graph (igraph.Graph): A graph, possibly disconnected

    Returns:
        new_graph (igraph.Graph): input graph with all nodes (and associated edges) removed that aren't reachable from the initial node
    """

    new_graph = deepcopy(graph)
    connected_vertices = new_graph.subcomponent(graph["initial"], mode="out")
    if set(new_graph.vs.indices) - set(connected_vertices):
        for vertex in new_graph.vs:
            vertex["initial"] = False
        new_graph.vs[new_graph["initial"]]["initial"] = True
        new_graph.delete_vertices(set(new_graph.vs.indices) - set(connected_vertices))
        for vertex in new_graph.vs:
            if vertex["initial"]:
                new_graph["initial"] = vertex.index
                break
    return new_graph


def reset_edge_attributes(graph):
    """Sets all attributes of the graph to False.

    Parameters:
        graph (igraph.Graph): A graph

    Returns:
        Nothing
    """

    for edge in graph.es():
        edge["processed"] = False
        edge["remove"] = False


def color_graph(graph):
    """Colors the input graph: initial node red and all others white.

    Parameters:
        graph (igraph.Graph): A graph

    Returns:
        Nothing
    """

    colors = ["white"] * graph.vcount()
    colors[int(graph["initial"])] = "red"
    graph.vs["color"] = colors


def open_graph(filename):
    """Returns a graph read from a file.

    Parameters:
        filename (str): Name of the file where graph description is saved

    Returns:
        graph (igraph.Graph): Graph from file
    """

    graph = Graph.Read_GraphML("input_files/" + filename + ".GraphML")
    graph["initial"] = int(graph["initial"])
    return graph


def subgraph_exists_in_graph(subgraph, original_graph, label):
    """Returns True if the subgraph is a part of the original graph.

    Parameters:
        subgraph (igraph.Graph): A graph
        original_graph (igraph.Graph): Graph that might contain subgraph
        label (str): Label of the edge possibly connecting initial node of original graph and subgraph

    Returns:
        True if subgraph is actually a subgraph of original graph, but only if its initial node is the target of an edge starting at the initial node of the original graph with the label input label
        False otherwise
    """

    other_subgraphs = []
    for edge in original_graph.es[
        original_graph.incident(original_graph["initial"], mode="out")
    ]:
        if edge["label"] == label:
            other_subgraph = deepcopy(original_graph)
            other_subgraph["initial"] = edge.target
            other_subgraph = remove_disconnected_vertices(other_subgraph)
            other_subgraphs.append(other_subgraph)
    return isomorphic_in_list(subgraph, other_subgraphs)


def add_subgraph_to_graph(subgraph, main_graph, label):
    """Returns a graph that is the subgraph attached to the main graph by an edge from the initial node of the main graph to the initial node of the subgraph by a given label.

    Parameters:
        subgraph (igraph.Graph): A graph
        main_graph (igraph.Graph): Graph that the subgraph should be attached to
        label (str): Label of the edge that will connect initial node of original graph and initial node of subgraph

    Returns:
        combined_graph (igraph.Graph): Combination of the two given graphs
    """

    combined_graph = deepcopy(main_graph)
    combined_graph.add_vertices(subgraph.vcount())
    for subgraph_edge in subgraph.es():
        new_edge = combined_graph.add_edge(
            subgraph_edge.source + main_graph.vcount(),
            subgraph_edge.target + main_graph.vcount(),
        )
        new_edge["label"] = subgraph_edge["label"]
        new_edge["processed"] = subgraph_edge["processed"]
    new_edge = combined_graph.add_edge(
        combined_graph["initial"],
        subgraph["initial"] + main_graph.vcount(),
    )
    new_edge["label"] = label
    new_edge["processed"] = True
    return combined_graph


def unfold_graph(graph, depth=1):
    """Returns a graph that is unfolded up to depth into a partial tree representation and then the original graph.

    Parameters:
        graph (igraph.Graph): A graph
        depth (int): Depth the graph should be unfolded to

    Returns:
        unfolded_graph (igraph.Graph): Up to depth unfolded graph combined with input graph as leaves
    """

    unfolded_graph = deepcopy(graph)
    representatives = {}
    depths = {}
    for vertex in unfolded_graph.vs:
        representatives[vertex.index] = vertex.index
        depths[vertex.index] = 0
    current_state = unfolded_graph.add_vertex().index
    representatives[current_state] = int(unfolded_graph["initial"])
    depths[current_state] = 1
    queue = [current_state]
    unfolded_graph["initial"] = current_state

    # tree needs to be of |depth| heigth
    while queue and depth > depths[current_state]:
        # iterates through outgoing edges of current state
        for edge in graph.es[
            graph.incident(representatives[current_state], mode="out")
        ]:
            new_vertex = unfolded_graph.add_vertex()
            new_edge = unfolded_graph.add_edge(current_state, new_vertex)
            new_edge["label"] = edge["label"]
            representatives[new_vertex.index] = edge.target
            queue.append(new_vertex.index)
            depths[new_vertex.index] = depths[current_state] + 1
        queue.remove(current_state)
        if queue:
            current_state = queue[0]

    # if queue is not empty we connect the vertices in the queue with the original vertices
    if queue:
        for vertex in queue:
            for edge in graph.es[graph.incident(representatives[vertex], mode="out")]:
                new_edge = unfolded_graph.add_edge(vertex, edge.target)
                new_edge["label"] = edge["label"]

    unfolded_graph = remove_disconnected_vertices(unfolded_graph)

    # color unfolded graph
    color_graph(unfolded_graph)

    return unfolded_graph
