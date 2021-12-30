# pylint: disable=missing-module-docstring, w0614, w0401, c0116
from igraph import *

from evaluate import evaluate
from lts import *
from main import generate_distinguished_graphs_testing
from parse import parse


def transform_graph_to_lts(graph):
    lts = LTS()
    for edge in graph.es():
        lts.add_transition(str(edge.source), edge["label"], str(edge.target))
    return lts


def test(formula_str, graph_filename):
    (
        graph,
        _,
        input_formula,
        negated_formula,
        results,
        non_results,
    ) = generate_distinguished_graphs_testing(formula_str, graph_filename)

    # If the results are empty, check if the original input did already satisfy the formula
    if not results:
        lts = transform_graph_to_lts(graph)
        satisfying_vertices = evaluate(parse(input_formula), lts)
        if str(graph["initial"]) in satisfying_vertices:
            return False

    # Check that every result satisfies the input formula
    for result in results:
        lts = transform_graph_to_lts(result)
        satisfying_vertices = evaluate(parse(input_formula), lts)
        if satisfying_vertices and not str(result["initial"]) in satisfying_vertices:
            return False

    # If non-results are empty, check if the original input did already satisfy the negated formula
    if not non_results:
        lts = transform_graph_to_lts(graph)
        satisfying_vertices = evaluate(parse(negated_formula), lts)
        if str(graph["initial"]) in satisfying_vertices:
            return False

    # Check that every non-result satisfies the negated input formula
    for result in non_results:
        lts = transform_graph_to_lts(result)
        satisfying_vertices = evaluate(parse(negated_formula), lts)
        if satisfying_vertices and not str(result["initial"]) in satisfying_vertices:
            return False

    return True


files = [
    "default_graph",
    "synthesis_example_1",
    "synthesis_example_2",
    "synthesis_example_3",
    "synthesis_example_4",
    "synthesis_example_5",
    "unfolding_example_1",
    "unfolding_example_2",
    "unfolding_example_3",
    "unfolding_example_4",
]
basic_formulas = [
    "true",
    "false",
    "(true or false)",
    "(false or true)",
    "(true or true)",
    "(false or false)",
    "(true and true)",
    "(true and false)",
    "(false and true)",
    "(false and false)",
    "<a>true",
    "<a>false",
    "<b>true",
    "<b>false",
    "[a]true",
    "[a]false",
    "[b]true",
    "[b]false",
]
advanced_formulas = [
    "<a><a>true",
    "<a><b>true",
    "<b><a>true",
    "<b><b>true",
    "[a]<a>true",
    "[a]<b>true",
    "[b]<a>true",
    "[b]<b>true",
    "<a>[a]true",
    "<a>[b]true",
    "<b>[a]true",
    "<b>[b]true",
    "(<a>true and <a>true)",
    "(<a>true and <b>true)",
    "(<b>true and <a>true)",
    "(<b>true and <b>true)",
    "(<a>true and [a]false)",
    "(<a>true and [b]false)",
    "(<b>true and [a]false)",
    "(<b>true and [b]false)",
    "([a]true and [a]false)",
    "([a]true and [b]false)",
    "([b]true and [a]false)",
    "([b]true and [b]false)",
    "(<a>true or <a>true)",
    "(<a>true or <b>true)",
    "(<b>true or <a>true)",
    "(<b>true or <b>true)",
    "(<a>true or [a]false)",
    "(<a>true or [b]false)",
    "(<b>true or [a]false)",
    "(<b>true or [b]false)",
    "([a]true or [a]false)",
    "([a]true or [b]false)",
    "([b]true or [a]false)",
    "([b]true or [b]false)",
]
edgecase_formulas = [
    "(<a>[b]false and [a]<b>true)",
]

for file in files:
    for formula in basic_formulas:
        assert test(formula, file), (
            "Test with formula " + formula + " and file " + file + " failed."
        )
print("Done with simple tests.")

for file in files:
    for formula in advanced_formulas:
        assert test(formula, file), (
            "Test with formula " + formula + " and file " + file + " failed."
        )
print("Done with advanced tests.")

for file in files:
    for formula in edgecase_formulas:
        assert test(formula, file), (
            "Test with formula " + formula + " and file " + file + " failed."
        )
print("Done with edge case tests.")
