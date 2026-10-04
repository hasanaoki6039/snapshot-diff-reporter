import copy
import unittest

from snapshot_diff_reporter import diff_snapshots, KEY_PATH_SEPARATOR


class TestDiffSnapshots(unittest.TestCase):
    def test_empty_dicts(self):
        self.assertEqual(
            diff_snapshots({}, {}),
            {"added": {}, "removed": {}, "changed": {}},
        )

    def test_identical_dicts(self):
        snap = {"a": 1, "b": {"x": 2}}
        self.assertEqual(
            diff_snapshots(snap, copy.deepcopy(snap)),
            {"added": {}, "removed": {}, "changed": {}},
        )

    def test_top_level_addition(self):
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        report = diff_snapshots(old, new)
        self.assertEqual(report["added"], {"b": 2})
        self.assertEqual(report["removed"], {})
        self.assertEqual(report["changed"], {})

    def test_top_level_removal(self):
        old = {"a": 1, "b": 2}
        new = {"a": 1}
        report = diff_snapshots(old, new)
        self.assertEqual(report["added"], {})
        self.assertEqual(report["removed"], {"b": 2})
        self.assertEqual(report["changed"], {})

    def test_top_level_change(self):
        old = {"a": 1}
        new = {"a": 2}
        report = diff_snapshots(old, new)
        self.assertEqual(report["added"], {})
        self.assertEqual(report["removed"], {})
        self.assertEqual(report["changed"], {"a": [1, 2]})

    def test_nested_change_flattened_with_dot(self):
        old = {"a": {"b": {"c": 1}}}
        new = {"a": {"b": {"c": 2}}}
        report = diff_snapshots(old, new)
        self.assertEqual(report["added"], {})
        self.assertEqual(report["removed"], {})
        self.assertEqual(report["changed"], {"a.b.c": [1, 2]})

    def test_added_nested_subtree_kept_whole(self):
        old = {"a": 1}
        new = {"a": 1, "b": {"x": 2, "y": {"z": 3}}}
        report = diff_snapshots(old, new)
        self.assertEqual(report["added"], {"b": {"x": 2, "y": {"z": 3}}})
        self.assertEqual(report["removed"], {})
        self.assertEqual(report["changed"], {})

    def test_removed_nested_subtree_kept_whole(self):
        old = {"a": 1, "b": {"x": 2, "y": {"z": 3}}}
        new = {"a": 1}
        report = diff_snapshots(old, new)
        self.assertEqual(report["added"], {})
        self.assertEqual(report["removed"], {"b": {"x": 2, "y": {"z": 3}}})
        self.assertEqual(report["changed"], {})

    def test_nested_addition_and_removal_inside_changed_branch(self):
        old = {"a": {"x": 1, "y": 2}}
        new = {"a": {"x": 1, "z": 3}}
        report = diff_snapshots(old, new)
        # Within a branch that exists on both sides, per-leaf reporting applies.
        self.assertEqual(report["added"], {})
        self.assertEqual(report["removed"], {})
        self.assertEqual(report["changed"], {"a.y": [2, None], "a.z": [None, 3]})

    def test_dict_to_scalar_change(self):
        old = {"a": {"b": 1}}
        new = {"a": 7}
        report = diff_snapshots(old, new)
        self.assertEqual(report["changed"], {"a": [{"b": 1}, 7]})

    def test_scalar_to_dict_change(self):
        old = {"a": 7}
        new = {"a": {"b": 1}}
        report = diff_snapshots(old, new)
        self.assertEqual(report["changed"], {"a": [7, {"b": 1}]})

    def test_list_change_is_value_based(self):
        old = {"items": [1, 2, 3]}
        new = {"items": [1, 2, 4]}
        report = diff_snapshots(old, new)
        self.assertEqual(report["changed"], {"items": [[1, 2, 3], [1, 2, 4]]})

    def test_list_equal_unchanged(self):
        old = {"items": [1, 2, 3]}
        new = {"items": [1, 2, 3]}
        report = diff_snapshots(old, new)
        self.assertEqual(report["changed"], {})

    def test_none_values_handled(self):
        old = {"a": None, "b": 1}
        new = {"a": 1, "b": None}
        report = diff_snapshots(old, new)
        self.assertEqual(report["changed"], {"a": [None, 1], "b": [1, None]})

    def test_key_order_is_deterministic(self):
        old = {"b": 1, "a": 2, "c": 3}
        new = {"a": 9, "b": 8, "c": 3}
        report = diff_snapshots(old, new)
        self.assertEqual(list(report["changed"].keys()), ["a", "b"])

    def test_non_dict_old_raises(self):
        with self.assertRaises(TypeError):
            diff_snapshots([1, 2, 3], {"a": 1})

    def test_non_dict_new_raises(self):
        with self.assertRaises(TypeError):
            diff_snapshots({"a": 1}, "not a dict")

    def test_separator_constant(self):
        self.assertEqual(KEY_PATH_SEPARATOR, ".")


if __name__ == "__main__":
    unittest.main()
