"""Tests for score.py module and DEFAULT_SCORERS registration."""

import unittest
from unittest.mock import MagicMock, patch

from scorers import score
from scorers.namedscorer import NamedScorer
from scorers.exactmatcher import ExactMatcher
from scorers.pythonscorer import PythonScorer
from scorers.turncount import TurnCount


class TestScoreModule(unittest.TestCase):

    def test_default_scorers_map_contents(self):
        """Verify that all standard registered scorers are present in DEFAULT_SCORERS."""
        expected_keys = [
            "exact_match", "recall_match", "set_match", "llmrater",
            "regexp_matcher", "returned_sql", "executable_sql",
            "trajectory_matcher", "skills_trajectory", "skills_best_practices",
            "goal_completion", "behavioral_metrics", "parameter_analysis",
            "turn_count", "agent_steps", "end_to_end_latency",
            "tool_call_latency", "token_consumption", "tokens_processed",
            "effective_billed_tokens", "binary_rubric_scorer", "python_scorer",
            "dataform_compile", "dataform_run", "dataform_cloud_compile",
            "dataform_cloud_run", "dbt_compile", "dbt_run"
        ]
        for key in expected_keys:
            self.assertIn(key, score.DEFAULT_SCORERS, f"Key '{key}' missing from DEFAULT_SCORERS")

    def test_get_scorer_instance_default_scorers(self):
        """Verify get_scorer_instance resolves direct matches from DEFAULT_SCORERS."""
        eval_output_item = {"id": 1, "eval_results": ""}
        experiment_config = {"database_configs": []}
        global_models = {}

        # 1. exact_match
        instances = score.get_scorer_instance(
            "exact_match", {}, experiment_config, eval_output_item, global_models
        )
        self.assertEqual(len(instances), 1)
        self.assertIsInstance(instances[0], ExactMatcher)
        self.assertEqual(instances[0].name, "exact_match")

        # 2. turn_count
        instances = score.get_scorer_instance(
            "turn_count", {}, experiment_config, eval_output_item, global_models
        )
        self.assertEqual(len(instances), 1)
        self.assertIsInstance(instances[0], TurnCount)

        # 3. python_scorer
        instances = score.get_scorer_instance(
            "python_scorer", {"script_path": "my_script.py"}, experiment_config, eval_output_item, global_models
        )
        self.assertEqual(len(instances), 1)
        self.assertIsInstance(instances[0], PythonScorer)
        self.assertEqual(instances[0].name, "my_script")

    def test_get_scorer_instance_named_scorer_type_attr(self):
        """Verify get_scorer_instance wraps custom metric names using type attribute."""
        eval_output_item = {"id": 1, "eval_results": ""}
        experiment_config = {"database_configs": []}
        global_models = {}

        # rubric_pass_fail -> type: python_scorer
        instances = score.get_scorer_instance(
            "rubric_pass_fail",
            {"type": "python_scorer", "script_path": "rubric.py"},
            experiment_config,
            eval_output_item,
            global_models,
        )
        self.assertEqual(len(instances), 1)
        self.assertIsInstance(instances[0], NamedScorer)
        self.assertEqual(instances[0].name, "rubric_pass_fail")
        self.assertIsInstance(instances[0].base_scorer, PythonScorer)

    def test_get_scorer_instance_named_scorer_nested_dict(self):
        """Verify get_scorer_instance wraps custom metric names using nested type dict."""
        eval_output_item = {"id": 1, "eval_results": ""}
        experiment_config = {"database_configs": []}
        global_models = {}

        # rubric_validator -> python_scorer: { script_path: ... }
        instances = score.get_scorer_instance(
            "rubric_validator",
            {"python_scorer": {"script_path": "rubric_val.py"}},
            experiment_config,
            eval_output_item,
            global_models,
        )
        self.assertEqual(len(instances), 1)
        self.assertIsInstance(instances[0], NamedScorer)
        self.assertEqual(instances[0].name, "rubric_validator")
        self.assertIsInstance(instances[0].base_scorer, PythonScorer)

    @patch("scorers.pythonscorer.subprocess.run")
    def test_score_compare_execution(self, mock_run):
        """Verify score.compare runs both standard and NamedScorer comparators."""
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = '{"score": 100.0, "reason": "Passed"}'
        mock_res.stderr = ""
        mock_run.return_value = mock_res

        eval_output_item = {
            "id": 1,
            "nl_prompt": "prompt",
            "golden_sql": "SELECT 1",
            "query_type": "DQL",
            "golden_result": None,
            "golden_error": None,
            "generated_sql": "SELECT 1",
            "generated_result": None,
            "generated_error": None,
            "dialects": ["sqlite"],
            "database": "db",
            "job_id": "j1",
        }

        experiment_config = {
            "scorers": {
                "exact_match": {},
                "rubric_pass_fail": {
                    "type": "python_scorer",
                    "script_path": "rubric.py",
                },
            }
        }

        scoring_results = []
        score.compare(
            eval_output_item=eval_output_item,
            experiment_config=experiment_config,
            scoring_results=scoring_results,
            global_models={},
        )

        results_by_comp = {r["comparator"]: r for r in scoring_results}
        self.assertIn("exact_match", results_by_comp)
        self.assertIn("rubric_pass_fail", results_by_comp)
        self.assertEqual(results_by_comp["exact_match"]["score"], 100)
        self.assertEqual(results_by_comp["rubric_pass_fail"]["score"], 100.0)


if __name__ == "__main__":
    unittest.main()
