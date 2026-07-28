"""Unit tests for Objective Model."""

import unittest
from core.objective import (
    Objective,
    Priority,
    ObjectiveStatus,
)


class TestObjectiveModel(unittest.TestCase):
    """Test Objective creation, constraint management, and progress updates."""

    def test_objective_lifecycle(self):
        obj = Objective(goal="Summarize research paper", priority=Priority.HIGH)
        self.assertTrue(obj.objective_id.startswith("obj_"))
        self.assertEqual(obj.status, ObjectiveStatus.NOT_STARTED)

        obj.add_constraint("no_external_api", "Must not send data outside sandbox", is_hard=True)
        self.assertEqual(len(obj.constraints), 1)

        obj.progress.update_progress(completed=2, total=4)
        self.assertEqual(obj.progress.percentage, 50.0)

        obj.update_status(ObjectiveStatus.COMPLETED)
        self.assertEqual(obj.status, ObjectiveStatus.COMPLETED)

        d = obj.to_dict()
        self.assertEqual(d["goal"], "Summarize research paper")
        self.assertEqual(d["priority"], "high")
        self.assertEqual(d["status"], "completed")
        self.assertEqual(d["progress"]["percentage"], 50.0)


if __name__ == "__main__":
    unittest.main()
