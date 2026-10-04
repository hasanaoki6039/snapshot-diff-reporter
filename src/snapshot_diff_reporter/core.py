"""Core implementation of snapshot diffing.

Design decisions:
- Lists are compared by value, not structurally. Deep, order-insensitive list diffing
  is a different problem and pretending to support it invites bugs. We treat a list like a
  scalar: same value -> unchanged, different value -> changed.
- Changed keys are flattened with dot notation so the caller can address the exact nested
  field. Only "changed" is flattened; "added" and "removed" keep the whole subtree, because
  when something appears or disappears wholesale the caller usually wants the whole value,
  not per-leaf noise.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

KEY_PATH_SEPARATOR = "."


def _is_dict(value: Any) -> bool:
    # isinstance check covers subclasses of dict too, which is the common case in JSON
    # snapshots; we do not want to special-case OrderedDict separately.
    return isinstance(value, dict)


def _key_path(parts: Tuple[str, ...]) -> str:
    return KEY_PATH_SEPARATOR.join(parts)


def _flatten_changed(
    old: Any,
    new: Any,
    path: Tuple[str, ...],
    out: Dict[str, Tuple[Any, Any]],
) -> None:
    """Populate ``out`` with changed leaf paths.

    When both sides are dicts we recurse so the caller gets precise dotted keys. When either
    side is not a dict we compare values directly; the key is recorded only if they differ.
    """
    if _is_dict(old) and _is_dict(new):
        # Recurse on the union of keys so that keys present on only one side are attributed
        # correctly as added/removed, not silently misclassified as changed.
        all_keys = set(old.keys()) | set(new.keys())
        for k in all_keys:
            child = path + (k,)
            in_old = k in old
            in_new = k in new
            if in_old and in_new:
                _flatten_changed(old[k], new[k], child, out)
            elif in_new:
                out[_key_path(child)] = (None, new[k])
            else:  # in_old only
                out[_key_path(child)] = (old[k], None)
        return

    if old != new:
        out[_key_path(path)] = (old, new)


def diff_snapshots(old: Any, new: Any) -> Dict[str, Dict[str, Any]]:
    """Diff two snapshots and return a report.

    The report is a dict with three keys: ``added``, ``removed``, ``changed``.

    - ``added``: keys present in ``new`` but absent in ``old``, mapped to the whole added
      value (preserving nested structure).
    - ``removed``: keys present in ``old`` but absent in ``new``, mapped to the whole
      removed value.
    - ``changed``: keys present in both whose values differ, flattened to dot-notation
      paths mapping to ``[old_value, new_value]``.

    Top-level inputs must be dicts. If either is not a dict we raise ``TypeError``, because a
    snapshot diff between two non-dict scalars is not what this library is for.
    """
    if not _is_dict(old):
        raise TypeError("diff_snapshots expects a dict for `old`")
    if not _is_dict(new):
        raise TypeError("diff_snapshots expects a dict for `new`")

    old_keys = set(old.keys())
    new_keys = set(new.keys())

    added: Dict[str, Any] = {k: new[k] for k in sorted(new_keys - old_keys)}
    removed: Dict[str, Any] = {k: old[k] for k in sorted(old_keys - new_keys)}

    changed: Dict[str, Tuple[Any, Any]] = {}
    for k in sorted(old_keys & new_keys):
        _flatten_changed(old[k], new[k], (k,), changed)

    # Convert tuples to lists for a JSON-friendly, convention-free return shape. We keep a
    # list (not a dict) so callers can rely on positional [old, new] ordering.
    changed_out: Dict[str, Any] = {
        k: [v[0], v[1]] for k, v in changed.items()
    }

    return {"added": added, "removed": removed, "changed": changed_out}
