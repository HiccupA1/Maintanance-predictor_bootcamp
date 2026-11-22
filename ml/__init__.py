"""Machine-learning pipelines for failure-risk scoring (WP3, ADR-0006).

Install with ``pip install -e ".[ml]"``. Feature code in ``ml.features`` is
shared by training and the scoring worker so that there is no train/serve skew.
"""
