import functools
import logging
import os

import graphviz as gv
import sys
from logzero import logger as log
from mock import Mock

import util
from core import MessageUnderstanding, States
from core.dialogstates import DialogStates
from core.recorder import RECORDING_PATH
from logic.rules.controller import Context, SentenceComposer, application_router
from model import User

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
        handler = application_router.get_state_handler(state, u)

        if handler is None:
            continue

        return handler.callback(composer_mock(), context), handler.callback
    return None, None


def get_state_machine():
    return DialogStates(States.SMALLTALK)


visualization_path = os.path.join(RECORDING_PATH, 'visualization')

if not os.path.exists(visualization_path):
    os.makedirs(visualization_path)


def get_recording(index=0):
    path = os.path.join(RECORDING_PATH, 'valid')
    files = os.listdir(path)
    idx = - (index + 1)
    print(files[idx])
    return os.path.join(path, files[idx])


def visualize_recording(filepath):
    rec = util.load_yaml_as_dict(filepath)

    g = gv.Digraph(format='svg', strict=True)

    last_state = 'Start'
    add_nodes(g, [last_state])

    for r in rec:
        label = "yes" if r['intent'] is True else r['intent']
        label = ' ' + label
        state = str(r['new_states'][0])
        print("label: ", label)
        add_edges(
            add_nodes(g, [state]),
            [((last_state, state), {'label': label})]
        )
        last_state = state

    g.render(os.path.splitext(os.path.split(filepath)[-1])[0], visualization_path)


if __name__ == '__main__':
    file = get_recording(0)
    visualize_recording(file)
