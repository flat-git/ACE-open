"""Evaluation metrics for PATENTMATCH and other classification tasks."""

from typing import Dict, List, Optional
import math


class MetricsCalculator:
    """Calculate classification metrics including accuracy, precision, recall, F1, and perplexity."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Reset all tracked predictions and labels."""
        self.predictions: List[str] = []
        self.labels: List[str] = []
        self.probabilities: List[float] = []

    def add(
        self,
        prediction: str,
        label: str,
        probability: Optional[float] = None,
    ) -> None:
        """
        Add a single prediction-label pair.

        Args:
            prediction: The predicted class (e.g., "X" or "A")
            label: The ground truth class
            probability: Optional probability/confidence score for the prediction
        """
        self.predictions.append(prediction)
        self.labels.append(label)
        if probability is not None:
            self.probabilities.append(probability)

    def compute(self) -> Dict[str, float]:
        """
        Compute all metrics.

        Returns:
            Dictionary containing accuracy, precision, recall, f1, and perplexity
        """
        if not self.predictions or not self.labels:
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "perplexity": float("inf"),
            }

        metrics = {}

        # Accuracy
        correct = sum(1 for p, l in zip(self.predictions, self.labels) if p == l)
        metrics["accuracy"] = correct / len(self.predictions)

        # For binary classification, we treat the first unique class as positive
        # In PATENTMATCH context, "X" is typically the positive class (novelty-breaking)
        unique_classes = sorted(set(self.labels))
        if len(unique_classes) >= 2:
            positive_class = unique_classes[0]  # Will be "A" if both A and X present
            # But for PATENTMATCH, X is the positive class, so we prioritize it
            if "X" in unique_classes:
                positive_class = "X"
            elif len(unique_classes) == 2:
                positive_class = unique_classes[1]
        elif len(unique_classes) == 1:
            positive_class = unique_classes[0]
        else:
            positive_class = "X"

        # Calculate TP, FP, TN, FN
        tp = sum(
            1
            for p, l in zip(self.predictions, self.labels)
            if p == positive_class and l == positive_class
        )
        fp = sum(
            1
            for p, l in zip(self.predictions, self.labels)
            if p == positive_class and l != positive_class
        )
        fn = sum(
            1
            for p, l in zip(self.predictions, self.labels)
            if p != positive_class and l == positive_class
        )
        tn = sum(
            1
            for p, l in zip(self.predictions, self.labels)
            if p != positive_class and l != positive_class
        )

        # Precision
        metrics["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        # Recall
        metrics["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # F1 Score
        if metrics["precision"] + metrics["recall"] > 0:
            metrics["f1"] = (
                2
                * metrics["precision"]
                * metrics["recall"]
                / (metrics["precision"] + metrics["recall"])
            )
        else:
            metrics["f1"] = 0.0

        # Perplexity (requires probabilities)
        if self.probabilities and len(self.probabilities) == len(self.predictions):
            log_likelihood = 0.0
            for prob, pred, label in zip(
                self.probabilities, self.predictions, self.labels
            ):
                # Use the probability as confidence for correct predictions
                # For incorrect predictions, use 1 - probability
                if pred == label:
                    # Correct prediction
                    actual_prob = max(prob, 1e-10)  # Avoid log(0)
                else:
                    # Incorrect prediction
                    actual_prob = max(1.0 - prob, 1e-10)  # Avoid log(0)

                log_likelihood += math.log(actual_prob)

            # Perplexity is exp of average negative log likelihood
            avg_neg_log_likelihood = -log_likelihood / len(self.probabilities)
            metrics["perplexity"] = math.exp(avg_neg_log_likelihood)
        else:
            # If no probabilities provided, estimate from accuracy
            # Higher accuracy -> lower perplexity
            if metrics["accuracy"] > 0:
                # Approximate perplexity from error rate
                error_rate = 1.0 - metrics["accuracy"]
                # Add smoothing to avoid log(0)
                metrics["perplexity"] = math.exp(-math.log(max(metrics["accuracy"], 0.01)))
            else:
                metrics["perplexity"] = float("inf")

        return metrics

    def compute_aggregate(self, step_results: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Compute aggregate statistics from multiple step results.

        Args:
            step_results: List of metrics dictionaries from individual steps

        Returns:
            Dictionary with mean and std for each metric
        """
        if not step_results:
            return {}

        metrics_keys = step_results[0].keys()
        aggregates = {}

        for key in metrics_keys:
            values = [r[key] for r in step_results if key in r and not math.isinf(r[key])]
            if values:
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                std = math.sqrt(variance)
                aggregates[f"{key}_mean"] = mean
                aggregates[f"{key}_std"] = std
            else:
                aggregates[f"{key}_mean"] = 0.0
                aggregates[f"{key}_std"] = 0.0

        return aggregates
