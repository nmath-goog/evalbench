import sys
from unittest.mock import patch, MagicMock

# Mock optional/missing mcp submodules for unit tests if not installed in env
for mod in [
    'mcp', 'mcp.types', 'mcp.client', 'mcp.client.session',
    'mcp.client.stdio', 'mcp.client.streamable_http', 'mcp.client.sse'
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

import json
import unittest

from scorers import score
from scorers.namedscorer import NamedScorer
from scorers.pythonscorer import PythonScorer


class TestNamedPythonScorer(unittest.TestCase):

    @patch('scorers.pythonscorer.subprocess.run')
    def test_type_python_scorer_and_nested_dict(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "score": 1.0,
            "reason": "OK"
        })
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        eval_output_item = {
            "id": 101,
            "nl_prompt": "test prompt",
            "golden_sql": "SELECT 1",
            "query_type": "DQL",
            "golden_result": None,
            "golden_error": None,
            "generated_sql": "SELECT 1",
            "generated_result": None,
            "generated_error": None,
            "dialects": ["sqlite"],
            "database": "test_db",
            "job_id": "job123",
        }

        experiment_config = {
            "scorers": {
                "rubric_pass_fail": {
                    "type": "python_scorer",
                    "script_path": "script_pf.py"
                },
                "rubric_validator": {
                    "python_scorer": {
                        "script_path": "script_val.py"
                    }
                }
            }
        }

        scoring_results = []
        score.compare(
            eval_output_item=eval_output_item,
            experiment_config=experiment_config,
            scoring_results=scoring_results,
            global_models={},
        )

        comparators = [r["comparator"] for r in scoring_results]
        self.assertIn("rubric_pass_fail", comparators)
        self.assertIn("rubric_validator", comparators)
        self.assertEqual(len(scoring_results), 2)

    def test_named_scorer_wrapper(self):
        base_mock = MagicMock(spec=PythonScorer)
        base_mock.compare.return_value = (85.0, "Good performance")

        wrapper = NamedScorer(name="custom_metric", base_scorer=base_mock)
        self.assertEqual(wrapper.name, "custom_metric")

        res_score, res_logs = wrapper.compare(
            nl_prompt="p", golden_query="g", query_type="DQL",
            golden_execution_result=None, golden_eval_result=None, golden_error=None,
            generated_query="gen", generated_execution_result=None,
            generated_eval_result=None, generated_error=None, database="db"
        )
        self.assertEqual(res_score, 85.0)
        self.assertEqual(res_logs, "Good performance")
        base_mock.compare.assert_called_once()


if __name__ == '__main__':
    unittest.main()
