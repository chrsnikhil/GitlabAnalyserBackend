import json
import os
from threading import Lock

OPERATIONS_FILE = os.path.join(os.path.dirname(__file__), "operations.json")
_lock = Lock()

def _read_operations():
    if not os.path.exists(OPERATIONS_FILE):
        return {}
    with _lock, open(OPERATIONS_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def _write_operations(ops):
    with _lock, open(OPERATIONS_FILE, "w") as f:
        json.dump(ops, f)

def get_operation(op_id):
    ops = _read_operations()
    return ops.get(op_id)

def set_operation(op_id, data):
    ops = _read_operations()
    ops[op_id] = data
    _write_operations(ops)

def delete_operation(op_id):
    ops = _read_operations()
    if op_id in ops:
        del ops[op_id]
        _write_operations(ops) 