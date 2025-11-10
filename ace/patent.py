"""PATENTMATCH task-specific components for ACE framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .adaptation import Sample, TaskEnvironment, EnvironmentResult
from .metrics import MetricsCalculator
from .roles import GeneratorOutput


@dataclass
class PatentSample(Sample):
    """
    Sample for PATENTMATCH task containing a claim-paragraph pair.
    
    Attributes:
        claim: The patent claim from a new application (defines invention scope)
        paragraph: The paragraph from prior art document
        ground_truth: Expected classification ("X" for match, "A" for no match)
        context: Additional context about the patent domain or case
        metadata: Optional metadata (e.g., patent IDs, technical domain)
    """

    claim: str = ""
    paragraph: str = ""
    question: str = ""  # Make question optional for PatentSample

    def __post_init__(self):
        """Set the question field to maintain compatibility with base Sample."""
        # For compatibility with base ACE framework, we use 'question' field
        # In PATENTMATCH, the "question" is implicit: "Does this match?"
        if not self.question:
            self.question = f"Claim: {self.claim}\n\nParagraph: {self.paragraph}"


@dataclass
class PatentEnvironmentResult(EnvironmentResult):
    """
    Extended environment result for PATENTMATCH with additional metrics.
    
    Adds patent-specific evaluation metrics beyond basic feedback.
    """

    prediction: str = ""
    probability: Optional[float] = None


class PatentMatchEnvironment(TaskEnvironment):
    """
    Task environment for PATENTMATCH binary classification.
    
    Evaluates whether a patent examiner correctly classified if a prior art
    paragraph breaks the novelty of a patent claim.
    """

    def __init__(self) -> None:
        self.metrics_calculator = MetricsCalculator()
        self.step_metrics: list[Dict[str, float]] = []

    def evaluate(
        self, sample: Sample, generator_output: GeneratorOutput
    ) -> EnvironmentResult:
        """
        Evaluate the generator's patent classification decision.

        Args:
            sample: PatentSample with claim, paragraph, and ground truth
            generator_output: Generator's classification and reasoning

        Returns:
            EnvironmentResult with feedback and metrics
        """
        if not isinstance(sample, PatentSample):
            # Try to convert if it's a regular Sample
            sample = PatentSample(
                claim=sample.metadata.get("claim", ""),
                paragraph=sample.metadata.get("paragraph", ""),
                ground_truth=sample.ground_truth,
                context=sample.context,
                metadata=sample.metadata,
            )

        ground_truth = (sample.ground_truth or "").strip().upper()
        prediction = generator_output.final_answer.strip().upper()

        # Extract probability if available in the raw output
        probability = None
        if "confidence" in generator_output.raw:
            probability = float(generator_output.raw["confidence"])
        elif "probability" in generator_output.raw:
            probability = float(generator_output.raw["probability"])

        # Validate classification
        valid_labels = {"X", "A"}
        if prediction not in valid_labels:
            feedback = f"Invalid classification '{prediction}'. Must be 'X' (match) or 'A' (no match)."
            return EnvironmentResult(
                feedback=feedback,
                ground_truth=ground_truth,
                metrics={"accuracy": 0.0, "error": 1.0},
            )

        # Check correctness
        correct = prediction == ground_truth

        # Build detailed feedback
        if correct:
            if prediction == "X":
                feedback = "Correct: The paragraph does break novelty (X classification)"
            else:
                feedback = "Correct: The paragraph does not break novelty (A classification)"
        else:
            if prediction == "X":
                feedback = (
                    f"Incorrect: Classified as X (match) but should be A (no match). "
                    f"The paragraph does not contain all key features of the claim."
                )
            else:
                feedback = (
                    f"Incorrect: Classified as A (no match) but should be X (match). "
                    f"The paragraph actually describes the same invention and breaks novelty."
                )

        # Update metrics
        self.metrics_calculator.add(prediction, ground_truth, probability)

        # Compute current metrics
        current_metrics = self.metrics_calculator.compute()
        self.step_metrics.append(current_metrics)

        return PatentEnvironmentResult(
            feedback=feedback,
            ground_truth=ground_truth,
            metrics=current_metrics,
            prediction=prediction,
            probability=probability,
        )

    def get_aggregate_metrics(self) -> Dict[str, float]:
        """
        Get aggregate metrics across all evaluated samples.

        Returns:
            Dictionary with mean and std for each metric
        """
        return self.metrics_calculator.compute_aggregate(self.step_metrics)

    def reset_metrics(self) -> None:
        """Reset all accumulated metrics."""
        self.metrics_calculator.reset()
        self.step_metrics = []
