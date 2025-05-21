from functools import wraps
from flask import request, jsonify, g
from collections import Counter

def get_most_common_items(items_list, count):
    if not items_list:
        return []
    counter = Counter(items_list)
    return [item for item, _ in counter.most_common(count)]