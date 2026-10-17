# Snapshot Diff Reporter

Diffs two dicts and reports what was added, removed, and changed. Nested changed keys are
flattened with dot notation; added and removed keys keep their whole subtree.

```python
from snapshot_diff_reporter import diff_snapshots

old = {"user": {"name": "Ada", "email": "ada@example.org"}, "role": "admin"}
new = {"user": {"name": "Ada", "email": "ada@elsewhere.org", "active": True}, "role": "admin"}

report = diff_snapshots(old, new)
# report["added"]    == {}
# report["removed"]  == {}
# report["changed"]  == {"user.email": ["ada@example.org", "ada@elsewhere.org"],
#                         "user.active": [None, True]}
```

Exported names: `diff_snapshots(old, new) -> {"added": dict, "removed": dict, "changed": dict}`,
and the constant `KEY_PATH_SEPARATOR` (currently `"."`).

## Why this exists

It exists to turn a pair of JSON-like snapshots into a small, addressable report you can
print, assert on, or feed into a reviewer. The trade-off: lists are compared as opaque
values, not element-by-element. If you swap two items in a list, this library reports the
whole list as changed rather than producing a per-element diff. That keeps the output
predictable and avoids the ambiguity of ordering, insertion, and deletion inside sequences.

## The awkward edge

When a key exists on both sides but one value is a dict and the other is a scalar, the
whole key is reported as changed under its top-level name (e.g. `"a"`), not flattened. This
is intentional: there is no nested structure on one side to flatten into.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

