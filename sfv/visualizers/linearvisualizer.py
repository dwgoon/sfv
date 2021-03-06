from typing import Dict


import numpy as np
from numpy.typing import ArrayLike
import networkx as nx

from qtpy.QtGui import QFont
from qtpy.QtGui import QColor
from qtpy.QtCore import QPointF
from qtpy.QtCore import Qt

import nezzle
from nezzle.graphics import LabelClassFactory
from nezzle.graphics import ArrowClassFactory

NegHead = ArrowClassFactory.create('HAMMER')
PosHead = ArrowClassFactory.create('TRIANGLE')
TextLabel = LabelClassFactory.create('TEXT_LABEL')


from sfv.visualizers.visualizer import Visualizer



def _update_edges(net, A, F, i2n, pct_edge, lw_min, lw_max):
    log_flows = np.log10(np.abs(F[np.array(F).nonzero()]))
    flow_max = log_flows.max()
    flow_min = log_flows.min()
    flow_thr = np.percentile(log_flows, pct_edge)

    ir, ic = np.array(A).nonzero()  # F.to_numpy().nonzero()
    for i, j in zip(ir, ic):
        tgt = i2n[i]
        src = i2n[j]
        f = F[i, j]

        edge = net.nxgraph[src][tgt]['GRAPHICS']

        head_old = edge.head
        args_head = head_old.width, head_old.height, head_old.offset
        if f > 0:
            head = PosHead(*args_head)
            color_edge = QColor(255, 10, 10, 70)
        elif f < 0:
            head = NegHead(*args_head)
            color_edge = QColor(10, 10, 255, 70)
        else:  # When flow is zero, show the sign of the original edge.
            if A[i, j] > 0:
                head = PosHead(*args_head)
            elif A[i, j] < 0:
                head = NegHead(*args_head)
            else:
                raise RuntimeError("The logic is abnormal.")

            color_edge = QColor(100, 100, 100, 100)

        edge.head = head
        edge['FILL_COLOR'] = color_edge

        if f == 0:
            edge.width = lw_min
        elif (flow_max - flow_min) == 0:
            edge.width = 0.5 * (lw_max + lw_min)
        else:
            log_f = np.log10(np.abs(f))
            log_f = np.clip(log_f, a_min=flow_min, a_max=flow_thr)
            lw = (log_f - flow_min) / (flow_max - flow_min) * (lw_max - lw_min) + lw_min
            edge.width = lw


def _update_single_label_name(net,
                              node,
                              name,
                              fix_node_size,
                              font):
    
    label_name = net.labels[name]

    lightness = QColor(node['FILL_COLOR']).lightness()
    label_name['TEXT_COLOR'] = Qt.black

    label_name['FONT'] = font

    if lightness < 200:
        label_name['TEXT_COLOR'] = Qt.white
        label_name['FONT_BOLD'] = True
    else:
        label_name['TEXT_COLOR'] = Qt.black
        label_name['FONT_BOLD'] = False

    rect = label_name.boundingRect()
    label_name.setPos(-rect.width() / 2, -rect.height() / 2)  # center
    if not fix_node_size:
        node.width = 1.1 * rect.width()
        node.height = 1.1 * rect.height()


def _update_single_label_activity(net, node, activity, fix_act_label, fmt, font):
    iden = '%s_act' % node.iden.upper()
    str_x = fmt % (activity)
    if iden not in net.labels:
        label_act = TextLabel(node, text=str_x)
        label_act.iden = iden
    else:
        label_act = net.labels[iden]
        label_act.text = str_x % (activity)

    if not fix_act_label:
        label_act['FONT'] = font
        label_act['TEXT_COLOR'] = QColor(20, 20, 20)
        rect = label_act.boundingRect()
        pos_x = node.width / 2 + 0.5
        label_act.setPos(pos_x, -rect.height() / 2)

    if iden not in net.labels:
        net.add_label(label_act)

class LinearVisualizer(Visualizer):

    def __init__(self):
        pass

    def visualize(self,
                  net: nezzle.graphics.Network,
                  F: ArrayLike,
                  acts: ArrayLike,
                  A: ArrayLike,
                  n2i: Dict,
                  color_up=None,
                  color_dn=None,
                  lw_min=1.0,
                  lw_max=10.0,
                  pct_edge=90,
                  show_label=True,
                  show_act=True,
                  pct_act=50,
                  fmt_act='%.5f',
                  fix_node_size=False,
                  fix_act_label=False,
                  font=None):
        """Visualize signal flow using Nezzle.

        Args:
            net (nezzle.graphics.Network):
                Network object of Nezzle.

            F (numpy.ndarray):
                A matrix of signal flows.
                It is usually calculated as W2*x1 - W1*x1,
                where W is weight matrix and
                activity is a state at steady-state.

            acts (numpy.ndarray):
                Changes in the activities, which are usually calculated
                as x2 - x1. The x1 and x2 are the activities of different conditions.

            A (numpy.ndarray):
                Adjacency matrix of the network.

            n2i (dict):
                Name to index dictionary.

            color_up (numpy.ndarray or QtGui.QColor):
                Color for up-regulated or positive signal flow.
                Default is blue (i.e., QColor(0, 0, 255)).

            color_dn (numpy.ndarray or QtGui.QColor):
                Color for down-regulated or negative signal flow.
                Default is red (i.e., QColor(255, 0, 0)).

            lw_min (float):
                Minimum edge width, which is also used for unchanged flow.

            lw_max (float):
                Maximum edge width.

            pct_edge (int):
                Percentile of edge width, which is used to set
                the maximum value for setting edge widths.
                Default value is 90.

            show_label (bool):
                Show node label or not.

            show_act (bool):
                Show activity label or not.

            pct_act (int):
                Percentile of activity, which is used to set
                the maximum value for coloring nodes.
                Default value is 50.

            fmt_act (str):
                Format string for activity label.

            fix_node_size (bool):
                Change the size of node or not.
                Default is False.

            fix_act_label (bool):
                Change the graphics of activity label or not.
                The activity value is changed irrespective of
                this parameter. Default is False.

            font (QFont):
                Font for the name and activity labels.

        Returns:
            None
        """

        i2n = {val: key for key, val in n2i.items()}
        color_white = np.array([255, 255, 255])

        if not color_up:
            color_up = np.array([255, 0, 0])
        elif isinstance(color_up, QColor):
            color_up = np.array([color_up.red(),
                                 color_up.green(),
                                 color_up.blue()])
        else:
            raise ValueError("color_up should be 3-dimensional np.ndarray "
                             "or QtGui.QColor")

        if not color_dn:
            color_dn = np.array([0, 0, 255])
        elif isinstance(color_dn, QColor):
            color_dn = np.array([color_dn.red(),
                                 color_dn.green(),
                                 color_dn.blue()])
        else:
            raise ValueError("color_dn should be 3-dimensional np.ndarray "
                             "or QtGui.QColor")

        # Set the default font
        if not font:
            font = QFont('Arial', 10)

        abs_act = np.abs(acts)
        thr = np.percentile(abs_act, pct_act)
        thr = 1 if thr == 0 else thr

        arr_t = np.zeros_like(acts)

        for i, elem in enumerate(acts):
            t = np.clip(np.abs(elem) / thr, a_min=0, a_max=1)
            arr_t[i] = t

        for iden, node in net.nodes.items():
            idx = n2i[iden]

            if not fix_node_size:
                radius = 20
                node.width = node.height = radius

            act = acts[idx]

            if act > 0:
                color = color_white + arr_t[idx] * (color_up - color_white)
            elif act <= 0:
                color = color_white + arr_t[idx] * (color_dn - color_white)

            color = np.int32(color)
            node['FILL_COLOR'] = QColor(*color)
            node['BORDER_WIDTH'] = 2
            node['BORDER_COLOR'] = QColor(40, 40, 40)

            if show_label:
                _update_single_label_name(net, node, node.name,
                                          fix_node_size, font)

            if show_act:
                _update_single_label_activity(net,
                                              node,
                                              act,
                                              fix_act_label,
                                              fmt_act, font)
            else:
                iden_label = '%s_act' % iden.upper()
                if iden_label in net.labels:
                    net.remove_label(net.labels[iden_label])
        # end of for : update nodes and labels

        _update_edges(net, A, F, i2n, pct_edge, lw_min, lw_max)
