# pylint: disable=missing-module-docstring, w0401, w0614, r0912, r1702, c0301, r0914, r1710, r0911, r0915

from copy import deepcopy

from igraph import *

from evaluate import Token
from formula_functions import (
    depth_formula,
    formula_to_str,
    minimize_formula,
    negate_formula,
)
from graph_functions import *
from parse import parse


def synthesis(graph_list, formula):
    """Returns a list of graphs that are altered version of the input graphs that satisfy the input formula.

    Parameters:
        graph_list ([igraph.Graph]): A list of graphs
        formula (Token): A formula

    Returns:
        return_list ([igraph.Graph]): A list of graphs satisfying the input formula
    """

    if formula.ident == Token.ID_TRUE:
        # no changes needed, return unchanged LTSs
        return graph_list

    if formula.ident == Token.ID_FALSE:
        # yields no results
        return []

    if formula.ident == Token.ID_OR:
        # try both parts seperately, return union of the resulting lists
        left_results = list(filter(None, synthesis(graph_list, formula.first)))
        for result in left_results:
            result = remove_disconnected_vertices(result)

        for graph in graph_list:
            reset_edge_attributes(graph)

        right_results = list(filter(None, synthesis(graph_list, formula.second)))
        for result in right_results:
            result = remove_disconnected_vertices(result)

        result_list = []
        for result in left_results:
            if not isomorphic_in_list(result, result_list):
                result_list.append(result)
        for result in right_results:
            if not isomorphic_in_list(result, result_list):
                result_list.append(result)

        return result_list

    if formula.ident == Token.ID_AND:
        result_list = list(filter(None, synthesis(graph_list, formula.first)))
        for result in result_list:
            result = remove_disconnected_vertices(result)
            reset_edge_attributes(result)

        if not result_list:
            return []

        while True:
            second_result_list = list(
                filter(None, synthesis(graph_list, formula.second))
            )
            for result in second_result_list:
                result = remove_disconnected_vertices(result)

            if not second_result_list:
                return []

            # lists are same, which means we're finished
            if lists_same(result_list, second_result_list):
                return result_list

            # lists are not same, another iteration
            for second_result in second_result_list:
                reset_edge_attributes(second_result)

            third_result_list = list(filter(None, synthesis(graph_list, formula.first)))
            for result in third_result_list:
                result = remove_disconnected_vertices(result)
                reset_edge_attributes(result)

            if not third_result_list:
                return []

            # lists are same, which means we're finished
            if lists_same(second_result_list, third_result_list):
                return second_result_list

            # now comparing result_list and third_result_list - if same, then we're stuck in an endless loop and formula is not satisfyable
            if lists_same(result_list, third_result_list):
                return []

            # list are not same, another iteration
            result_list = deepcopy(third_result_list)

    if formula.ident == Token.ID_NECESSARY:
        # Try each e step, if none is successful remove edge, otherwise change edge recursively if needed
        queue = deepcopy(graph_list)
        return_list = []
        while queue:
            current_graph = queue[0]
            for edge in current_graph.es[
                current_graph.incident(current_graph["initial"], mode="out")
            ]:
                if edge["label"] == formula.first and not edge["processed"]:
                    edge["processed"] = True
                    changed_graph = deepcopy(current_graph)
                    changed_graph["initial"] = edge.target
                    result_list = synthesis([changed_graph], formula.second)
                    if result_list:
                        result_list = list(filter(None, result_list))
                    else:
                        result_list = []
                    if result_list:
                        for result in result_list:
                            result["initial"] = current_graph["initial"]
                            if (not isomorphic_in_list(result, queue)) and (
                                not isomorphic_in_list(result, return_list)
                            ):
                                queue.append(result)
                                if current_graph in queue:
                                    queue.remove(current_graph)
                    else:
                        edge["remove"] = True
            if current_graph in queue:
                edges_remove = []
                for edge in current_graph.es:
                    if edge["remove"]:
                        edges_remove.append(edge.index)
                current_graph.delete_edges(edges_remove)
                if not isomorphic_in_list(current_graph, return_list):
                    return_list.append(current_graph)
                queue.remove(current_graph)

        return return_list

    if formula.ident == Token.ID_POSSIBLE:
        # Try each e step, if none is successful, treat it as a false, include modified and non-modified version
        queue = deepcopy(graph_list)
        return_list = []
        while queue:
            current_graph = queue[0]
            for edge in current_graph.es[
                current_graph.incident(current_graph["initial"], mode="out")
            ]:
                if edge["label"] == formula.first and not edge["processed"]:
                    edge["processed"] = True
                    changed_graph = deepcopy(current_graph)
                    changed_graph["initial"] = edge.target
                    result_list = synthesis([changed_graph], formula.second)
                    if result_list:
                        result_list = list(filter(None, result_list))
                    else:
                        result_list = []
                    if result_list:
                        for result in result_list:
                            subgraph = remove_disconnected_vertices(result)
                            if not subgraph_exists_in_graph(
                                subgraph, current_graph, edge["label"]
                            ):
                                return_list.append(
                                    add_subgraph_to_graph(
                                        subgraph, current_graph, edge["label"]
                                    )
                                )
                            elif not isomorphic_in_list(current_graph, return_list):
                                return_list.append(current_graph)
            queue.remove(current_graph)

        return return_list


def generate_distinguished_graphs(formula_str, graph_filename="default_graph"):
    """Returns the results of synthesis with satisfying and non satisfying formulas.

    Parameters:
        graph_filename (str): Name of file where graph is saved
        formula_str (str): A formula in string representation

    Returns:
        satisfying_results ([igraph.Graph]): A list of graphs satisfying the input formula combined with shallower formulas with and
        non_satisfying_results ([igraph.Graph]): A list of graphs satisfying the negation of the input formula combined with shallower formulas with and
    """

    (
        _,
        _,
        _,
        _,
        satisfying_results,
        non_satisfying_results,
    ) = generate_distinguished_graphs_testing(formula_str, graph_filename)

    return satisfying_results, non_satisfying_results


def generate_distinguished_graphs_testing(formula_str, graph_filename="default_graph"):
    """Returns the results of synthesis with satisfying and non satisfying formulas and other things for testing/printing.

    Parameters:
        graph_filename (str): Name of file where graph is saved
        formula_str (str): A formula in string representation

    Returns:
        input_graph (igraph.Graph): The input graph
        unfolded_graph (igraph.Graph): Unfolded version of the input graph
        formula (String): Input formula
        negated_formula (String): Negated input formula
        final_satisfying_results ([igraph.Graph]): A list of graphs satisfying the satisfying formulas
        final_non_satisfying_results ([igraph.Graph]): A list of graphs satisfying the not satisfying formulas
    """

    formula = parse(formula_str)
    formula = minimize_formula(formula)
    negated_formula = negate_formula(formula)
    negated_formula_str = formula_to_str(negated_formula)

    depth = depth_formula(formula)

    input_graph = open_graph(graph_filename)
    color_graph(input_graph)
    unfolded_graph = unfold_graph(input_graph, depth)
    reset_edge_attributes(unfolded_graph)

    unfiltered_satisfying_results = []
    unfiltered_non_satisfying_results = []

    for result in synthesis([unfolded_graph], formula):
        if not isomorphic_in_list(result, unfiltered_satisfying_results):
            unfiltered_satisfying_results.append(result)
    for result in synthesis([unfolded_graph], negated_formula):
        if not isomorphic_in_list(result, unfiltered_satisfying_results):
            unfiltered_non_satisfying_results.append(result)

    satisfying_results = list(filter(None, unfiltered_satisfying_results))
    non_satisfying_results = list(filter(None, unfiltered_non_satisfying_results))

    final_satisfying_results = []
    final_non_satisfying_results = []
    # post-processing: removing unreachable vertices and coloring graphs
    for graph in satisfying_results:
        graph = remove_disconnected_vertices(graph)
        color_graph(graph)
        final_satisfying_results.append(graph)
    for graph in non_satisfying_results:
        graph = remove_disconnected_vertices(graph)
        color_graph(graph)
        final_non_satisfying_results.append(graph)

    return (
        input_graph,
        unfolded_graph,
        formula_str,
        negated_formula_str,
        final_satisfying_results,
        final_non_satisfying_results,
    )
