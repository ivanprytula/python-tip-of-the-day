# import csv
import time
import random
from copy import deepcopy
from collections import namedtuple, deque
from typing import NoReturn, Any
from itertools import cycle
from browser import ajax, document, bind, DOMNode

TIP_SECTION_ID = "tipzone"
TIMEOUT = 4
NUM_TIPS_HEADERS = 4

tip_zone = document[TIP_SECTION_ID]

class Node:
    def __init__(self, data: Any):
        self.data = data
        self.next = None
        self.previous = None


class DoublyLinkedCircularList:
    def __init__(self, nodes: list = None):
        self.head = None
        self.nodes = nodes
        self.native_length: int = len(nodes)
        if nodes is not None:
            node_left = Node(data=nodes.pop(0))
            self.head = node_left

            # Will become 2nd/[1]-element
            node_right = Node(data=nodes.pop(0))

            # Let's do first cross-refs pair
            node_left.next = node_right
            node_right.previous = node_left

            # Continue making references starting from 3rd elem
            for _, elem in enumerate(nodes, start=2):
                node_right.next = Node(data=elem)
                node_right.next.previous = node_right

                node_right = node_right.next

            # The last node points back to the head to make list circular
            node_right.next = self.head
            self.head.previous = node_right

    def __len__(self) -> int:
        return self.native_length

    def __getitem__(self, node_key: int) -> Node:
        """Support indexing and slicing."""
        # To compensate first popped out element on __init__()
        self.nodes.insert(0, self.head)
        nodes = (node for node in self.traverse())
        for index, node in enumerate(nodes):
            if index == node_key:
                return node

    def __repr__(self, starting_point=None) -> str:
        nodes = []
        for node in self.traverse(starting_point):
            nodes.append(repr(node.data))
        print(" -> ".join(nodes))

    def traverse(self, starting_point=None) -> Node:
        if starting_point is None:
            starting_point = self.head
        node = starting_point
        while node is not None and (node.next != starting_point):
            yield node
            node = node.next
        yield node

    def index(self, node) -> int:
        return self.nodes.index(node)


def fake_qs():
    return f"?foo={time.time()}"


def divide_chunks(data: list, start_index: int, n: int):
    """Yield successive n-sized chunks from data list."""
    for i in range(start_index, len(data), n):
        yield data[i : i + n]


def set_text_on_page(element: DOMNode, text_to_show: str) -> NoReturn:
    element.text = text_to_show


def get_parsed_tips(req: ajax) -> DoublyLinkedCircularList:
    tips_data: list = [
        phrase.strip("\n") for phrase in req.read().split("\t") if phrase
    ]
    tips_headers: list = [
        header.lower().replace(" ", "_") for header in tips_data[:NUM_TIPS_HEADERS]
    ]
    Tip = namedtuple(
        "Tip",
        tips_headers,
        rename=True,
        module=__name__,
        defaults=["import __hello__", "import this", "...", "Guido van Rossum"],
    )
    tips = [
        Tip._make(tip_fields)
        for tip_fields in divide_chunks(tips_data, NUM_TIPS_HEADERS, NUM_TIPS_HEADERS)
    ]
    return DoublyLinkedCircularList(tips)


def get_random_tip(req: ajax) -> NoReturn:
    if req.status == 200 or req.status == 0:
        global tips
        global last_showed_tip

        tips = get_parsed_tips(req)
        any_tip = random.choice(tips)

        # Set value for later usage with prev/next buttons
        last_showed_tip = any_tip
        set_text_on_page(tip_zone, any_tip.data[0])
    else:
        set_text_on_page(tip_zone, f"ERROR: {req.text}")


def err_msg():
    set_text_on_page(tip_zone, f"Server didn't reply after {TIMEOUT} seconds")


def get_tips_from_file(url: str):
    req = ajax.Ajax()
    req.bind("complete", get_random_tip)
    req.set_timeout(TIMEOUT, err_msg)
    req.open("GET", url, True)
    req.send()


get_tips_from_file(f"tips_data.tsv{fake_qs()}")


@bind("button[data-direction]", "click")
def loop_over_tips(event):
    global last_showed_tip
    current_tip = last_showed_tip
    match event.target.getAttribute("data-direction"):
        case "previous":
            last_showed_tip = current_tip.previous
            set_text_on_page(tip_zone, current_tip.previous.data[0])
        case "next":
            last_showed_tip = current_tip.next
            set_text_on_page(tip_zone, current_tip.next.data[0])
        case _:
            set_text_on_page(tip_zone, "I dunno where to go.")
