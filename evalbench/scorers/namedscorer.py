"""NamedScorer class to wrap any base comparator with a custom metric name."""

from typing import Any, Tuple
from scorers import comparator


class NamedScorer(comparator.Comparator):
    """Wraps an underlying base comparator with a custom metric name."""

    def __init__(self, name: str, base_scorer: comparator.Comparator):
        super().__init__({})
        self.name = name
        self.base_scorer = base_scorer

    def compare(
        self,
        nl_prompt: Any,
        golden_query: Any,
        query_type: Any,
        golden_execution_result: Any,
        golden_eval_result: Any,
        golden_error: Any,
        generated_query: Any,
        generated_execution_result: Any,
        generated_eval_result: Any,
        generated_error: Any,
        database: str = "",
        **kwargs,
    ) -> Tuple[float, str]:
        """Delegate comparison to the underlying base scorer."""
        return self.base_scorer.compare(
            nl_prompt,
            golden_query,
            query_type,
            golden_execution_result,
            golden_eval_result,
            golden_error,
            generated_query,
            generated_execution_result,
            generated_eval_result,
            generated_error,
            database=database,
            **kwargs,
        )
