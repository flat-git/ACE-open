"""Test suite for PATENTMATCH task components."""

import json
import unittest

from ace import (
    DummyLLMClient,
    Generator,
    Reflector,
    Curator,
    OfflineAdapter,
    Playbook,
    PatentSample,
    PatentMatchEnvironment,
)
from ace.prompts_patent import (
    PATENTMATCH_GENERATOR_PROMPT,
    PATENTMATCH_REFLECTOR_PROMPT,
    PATENTMATCH_CURATOR_PROMPT,
)


class PatentMatchTest(unittest.TestCase):
    """Test PATENTMATCH-specific functionality."""

    def test_patent_sample_creation(self) -> None:
        """Test that PatentSample properly initializes."""
        sample = PatentSample(
            claim="A method for processing data using a neural network",
            paragraph="The system uses machine learning to process information",
            ground_truth="A",
            context="Computer Science domain",
        )
        self.assertEqual(sample.claim, "A method for processing data using a neural network")
        self.assertEqual(sample.ground_truth, "A")
        self.assertIn("Claim:", sample.question)

    def test_patent_environment_correct_classification(self) -> None:
        """Test environment evaluation with correct classification."""
        env = PatentMatchEnvironment()
        sample = PatentSample(
            claim="A device with feature X and feature Y",
            paragraph="The invention includes feature X and feature Y",
            ground_truth="X",
        )

        # Mock generator output
        from ace.roles import GeneratorOutput

        output = GeneratorOutput(
            reasoning="Both features are present",
            final_answer="X",
            bullet_ids=[],
            raw={"confidence": 0.9},
        )

        result = env.evaluate(sample, output)
        self.assertIn("Correct", result.feedback)
        self.assertEqual(result.metrics["accuracy"], 1.0)

    def test_patent_environment_incorrect_classification(self) -> None:
        """Test environment evaluation with incorrect classification."""
        env = PatentMatchEnvironment()
        sample = PatentSample(
            claim="A device with feature X and feature Y",
            paragraph="The invention includes only feature X",
            ground_truth="A",
        )

        from ace.roles import GeneratorOutput

        output = GeneratorOutput(
            reasoning="Feature X is present",
            final_answer="X",
            bullet_ids=[],
            raw={},
        )

        result = env.evaluate(sample, output)
        self.assertIn("Incorrect", result.feedback)
        self.assertEqual(result.metrics["accuracy"], 0.0)

    def test_patent_metrics_calculation(self) -> None:
        """Test that metrics are properly calculated across multiple samples."""
        env = PatentMatchEnvironment()

        from ace.roles import GeneratorOutput

        # Sample 1: Correct X classification
        sample1 = PatentSample(
            claim="Feature A and B", paragraph="Has A and B", ground_truth="X"
        )
        output1 = GeneratorOutput(
            reasoning="Match", final_answer="X", bullet_ids=[], raw={}
        )
        env.evaluate(sample1, output1)

        # Sample 2: Correct A classification
        sample2 = PatentSample(
            claim="Feature A and B", paragraph="Has only A", ground_truth="A"
        )
        output2 = GeneratorOutput(
            reasoning="No match", final_answer="A", bullet_ids=[], raw={}
        )
        env.evaluate(sample2, output2)

        # Sample 3: Incorrect classification
        sample3 = PatentSample(
            claim="Feature A and B", paragraph="Has A and B", ground_truth="X"
        )
        output3 = GeneratorOutput(
            reasoning="Wrong", final_answer="A", bullet_ids=[], raw={}
        )
        env.evaluate(sample3, output3)

        # Check aggregate metrics
        metrics = env.metrics_calculator.compute()
        self.assertAlmostEqual(metrics["accuracy"], 2.0 / 3.0, places=2)
        self.assertGreater(metrics["precision"], 0.0)
        self.assertGreater(metrics["recall"], 0.0)

    def test_full_adaptation_loop_with_patent_prompts(self) -> None:
        """Test complete ACE adaptation loop with PATENTMATCH task."""
        client = DummyLLMClient()

        # Queue generator response
        client.queue(
            json.dumps(
                {
                    "reasoning": "The claim describes features X and Y. The paragraph contains both features in equivalent form.",
                    "bullet_ids": [],
                    "final_answer": "X",
                }
            )
        )

        # Queue reflector response
        client.queue(
            json.dumps(
                {
                    "reasoning": "Classification was correct. Both technical features were properly identified.",
                    "error_identification": "",
                    "root_cause_analysis": "",
                    "correct_approach": "Always verify all claim features are present in prior art.",
                    "key_insight": "Feature-by-feature comparison is essential for novelty assessment.",
                    "bullet_tags": [],
                }
            )
        )

        # Queue curator response
        client.queue(
            json.dumps(
                {
                    "reasoning": "Adding a strategy for feature comparison.",
                    "operations": [
                        {
                            "type": "ADD",
                            "section": "feature_identification",
                            "content": "Always perform systematic feature-by-feature comparison between claim and prior art.",
                            "metadata": {"helpful": 1},
                        }
                    ],
                }
            )
        )

        playbook = Playbook()
        generator = Generator(client, prompt_template=PATENTMATCH_GENERATOR_PROMPT)
        reflector = Reflector(client, prompt_template=PATENTMATCH_REFLECTOR_PROMPT)
        curator = Curator(client, prompt_template=PATENTMATCH_CURATOR_PROMPT)

        adapter = OfflineAdapter(
            playbook=playbook,
            generator=generator,
            reflector=reflector,
            curator=curator,
            max_refinement_rounds=1,
        )

        sample = PatentSample(
            claim="A system comprising component X and component Y configured to perform task Z",
            paragraph="The disclosed system includes component X and component Y that jointly execute task Z",
            ground_truth="X",
        )

        environment = PatentMatchEnvironment()
        results = adapter.run([sample], environment, epochs=1)

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].generator_output.final_answer, "X")
        self.assertGreaterEqual(playbook.stats()["sections"], 1)
        self.assertTrue(
            any("feature" in bullet.content.lower() for bullet in playbook.bullets())
        )

        # Verify metrics were computed
        self.assertIn("accuracy", results[0].environment_result.metrics)
        self.assertIn("precision", results[0].environment_result.metrics)


class MetricsCalculatorTest(unittest.TestCase):
    """Test the metrics calculation module."""

    def test_metrics_calculator_accuracy(self) -> None:
        """Test accuracy calculation."""
        from ace.metrics import MetricsCalculator

        calc = MetricsCalculator()
        calc.add("X", "X")
        calc.add("A", "A")
        calc.add("X", "A")

        metrics = calc.compute()
        self.assertAlmostEqual(metrics["accuracy"], 2.0 / 3.0, places=2)

    def test_metrics_calculator_precision_recall_f1(self) -> None:
        """Test precision, recall, and F1 calculation."""
        from ace.metrics import MetricsCalculator

        calc = MetricsCalculator()
        # TP: 2, FP: 1, FN: 1, TN: 1
        calc.add("X", "X")  # TP
        calc.add("X", "X")  # TP
        calc.add("X", "A")  # FP
        calc.add("A", "X")  # FN
        calc.add("A", "A")  # TN

        metrics = calc.compute()

        # Precision = TP / (TP + FP) = 2 / 3
        self.assertAlmostEqual(metrics["precision"], 2.0 / 3.0, places=2)

        # Recall = TP / (TP + FN) = 2 / 3
        self.assertAlmostEqual(metrics["recall"], 2.0 / 3.0, places=2)

        # F1 = 2 * P * R / (P + R) = 2 * (2/3) * (2/3) / (4/3) = 2/3
        self.assertAlmostEqual(metrics["f1"], 2.0 / 3.0, places=2)

    def test_metrics_calculator_perplexity_with_probabilities(self) -> None:
        """Test perplexity calculation with probability scores."""
        from ace.metrics import MetricsCalculator

        calc = MetricsCalculator()
        calc.add("X", "X", 0.9)  # Correct with high confidence
        calc.add("A", "A", 0.8)  # Correct with high confidence
        calc.add("X", "A", 0.6)  # Incorrect

        metrics = calc.compute()
        self.assertGreater(metrics["perplexity"], 0)
        self.assertLess(metrics["perplexity"], 10)  # Should be reasonable

    def test_metrics_calculator_reset(self) -> None:
        """Test that reset clears all data."""
        from ace.metrics import MetricsCalculator

        calc = MetricsCalculator()
        calc.add("X", "X")
        calc.add("A", "A")

        calc.reset()

        self.assertEqual(len(calc.predictions), 0)
        self.assertEqual(len(calc.labels), 0)


if __name__ == "__main__":
    unittest.main()
