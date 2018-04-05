import functools
import inspect
import logging
import sys
from typing import List

import graphviz as gv
from logzero import logger as log
from mock import Mock

import logic
from core import MessageUnderstanding, States
from core.dialogstates import DialogStates
from core.routing import BaseHandler
from logic import intents
from logic.rules.controller import Context, SentenceComposer, application_router, pprint
from model import User
from nludata.allintents import ALL_INTENTS

log.setLevel(logging.INFO)

Digraph = functools.partial(gv.Digraph, format='svg')


def add_nodes(graph, nodes) -> gv.Digraph:
    for n in nodes:
        if isinstance(n, tuple):
            graph.node(n[0], **n[1])
        else:
            graph.node(n)
    return graph


def add_edges(graph, edges) -> gv.Digraph:
    for e in edges:
        if isinstance(e[0], tuple):
            graph.edge(*e[0], **e[1])
        else:
            graph.edge(*e)
    return graph


styles = {
    'graph': {
        'label': 'A Fancy Graph',
        'fontsize': '16',
        'fontcolor': 'white',
        'bgcolor': '#333333',
        'rankdir': 'BT',
    },
    'nodes': {
        'fontname': 'Helvetica',
        'shape': 'hexagon',
        'fontcolor': 'white',
        'color': 'white',
        'style': 'filled',
        'fillcolor': '#006699',
    },
    'edges': {
        'style': 'dashed',
        'color': 'white',
        'arrowhead': 'open',
        'fontname': 'Courier',
        'fontsize': '12',
        'fontcolor': 'white',
    }
}


def apply_styles(graph, styles):
    graph.graph_attr.update(
        ('graph' in styles and styles['graph']) or {}
    )
    graph.node_attr.update(
        ('nodes' in styles and styles['nodes']) or {}
    )
    graph.edge_attr.update(
        ('edges' in styles and styles['edges']) or {}
    )
    return graph


def turn(intent=None, parameters=None):
    return MessageUnderstanding(intent=intent, parameters=parameters, text="")


def context_mock(state, u):
    ctx = Context(user_mock(), initial_state=state)
    ctx.add_user_utterance(u)
    return ctx


def composer_mock():
    return Mock(SentenceComposer)


def user_mock():
    return Mock(User)


def step(current_state, context, u):
    for state in current_state.iter_states():
        handler = application_router.find_matching_state_handler(state, u)

        if handler is None:
            continue

        return handler.callback(composer_mock(), context), handler.callback
    return None, None
    # callback = None
    # next_state = None
    # # Dialog states are a priority queue
    # for state in current_state.iter_states():
    #     # Find exactly one handler in any of the prioritized states
    #     handler = application_router.find_matching_state_handler(state, u)
    #
    #     if handler is None:
    #         continue
    #
    #     callback = handler.callback
    #     next_state = handler.callback(composer_mock(), context)
    #     handler_found = True
    #     break
    # else:
    #     # If no handler was found in any of the states, try the fallbacks
    #     handler = application_router.get_fallback_handler(u)
    #
    #     if handler is not None:
    #         callback = handler.callback
    #         next_state = handler.callback(composer_mock(), context)
    #         handler_found = True
    #     else:
    #         handler_found = False
    #
    # if not handler_found:
    #     if u.intent == 'fallback':
    #         return None, None
    #     else:
    #         return None, None
    #
    # if isinstance(next_state, SentenceComposer):
    #     # Lambdas return the senctence composer, which we don't need (call by reference)
    #     next_state = None
    #
    # return next_state, callback


sys.path.append('../src')


def get_state_machine():
    return DialogStates(States.SMALLTALK)


current_state = States.SMALLTALK

# initial state
g = gv.Digraph(format='svg')

for k, handlers in application_router.states.items():
    current_state_name = str(k)
    add_nodes(g, [current_state_name])

    mapping = {}
    for handler in handlers:
        u = turn(handler.intents)
        ctx = context_mock(k, u)
        next_state, callback = step(get_state_machine(), ctx, u)

        if next_state:
            if isinstance(next_state, tuple):
                next_state = next_state[0]
            # TODO: self-references when it's None?
            mapping.setdefault((callback.__name__, str(next_state)), []).append(intent)

    pprint(mapping)

    intent_groups = inspect.getmembers(logic.intents)
    aggregated = {}
    for k, v in mapping.items():
        v_intents = []
        for l in intent_groups:
            if all(x in v for x in l):
                v_intents.append(l.__name__)
        v_intents.extend([x for x in v if x not in v_intents])
        aggregated[k] = v_intents

    pprint(aggregated)

    for tpl, its in mapping.items():
        cb_name, state_name = tpl
        cb_name = 'do ' + cb_name
        label = ',\n'.join(its)
        add_edges(
            add_nodes(g, [cb_name, state_name]),
            [
                ((current_state_name, cb_name), {'label': label}),
                (cb_name, state_name),
            ]
        )

g.render("statemachine", directory="/home/joscha/bachelorarbeit/diagrams")

# add_edges(
#     add_nodes(Digraph(), ['A', 'B', 'C']),
#     [('A', 'B'), ('A', 'C'), ('B', 'C')]
# ).render('img/g4')
#
# add_edges(
#     add_nodes(Digraph(), [
#         ('A', {'label': 'Node A'}),
#         ('B', {'label': 'Node B'}),
#         'C'
#     ]),
#     [
#         (('A', 'B'), {'label': 'Edge 1'}),
#         (('A', 'C'), {'label': 'Edge 2'}),
#         ('B', 'C')
#     ]
# ).render('img/g5')
#
# g6 = add_edges(
#     add_nodes(Digraph(), [
#         ('A', {'label': 'Node A'}),
#         ('B', {'label': 'Node B'}),
#         'C'
#     ]),
#     [
#         (('A', 'B'), {'label': 'Edge 1'}),
#         (('A', 'C'), {'label': 'Edge 2'}),
#         ('B', 'C')
#     ]
# )
#
# g6 = apply_styles(g6, styles)
# g6.render('img/g6')
#
# g7 = add_edges(
#     add_nodes(Digraph(), [
#         ('A', {'label': 'Node A'}),
#         ('B', {'label': 'Node B'}),
#         'C'
#     ]),
#     [
#         (('A', 'B'), {'label': 'Edge 1'}),
#         (('A', 'C'), {'label': 'Edge 2'}),
#         ('B', 'C')
#     ]
# )
#
# g8 = apply_styles(
#     add_edges(
#         add_nodes(Digraph(), [
#             ('D', {'label': 'Node D'}),
#             ('E', {'label': 'Node E'}),
#             'F'
#         ]),
#         [
#             (('D', 'E'), {'label': 'Edge 3'}),
#             (('D', 'F'), {'label': 'Edge 4'}),
#             ('E', 'F')
#         ]
#     ),
#     {
#         'nodes': {
#             'shape': 'square',
#             'style': 'filled',
#             'fillcolor': '#cccccc',
#         }
#     }
# )
#
# g7.subgraph(g8)
# g7.edge('B', 'E', color='red', weight='2')
#
# g7.render('img/g7')
