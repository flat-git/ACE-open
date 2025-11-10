#!/usr/bin/env python
"""
Example script demonstrating the PATENTMATCH task with ACE framework.

This script shows how to use the adapted ACE framework for patent novelty assessment,
where the task is to classify whether a prior art paragraph breaks the novelty of
a patent claim.
"""

import json
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


def create_sample_data():
    """Create sample PATENTMATCH data for demonstration."""
    samples = [
        PatentSample(
            claim="A method for processing data comprising: (a) receiving input data; (b) applying a neural network to transform the input data; and (c) outputting the transformed data.",
            paragraph="The disclosed system receives data, processes it through a deep learning model consisting of multiple neural network layers, and outputs the processed results.",
            ground_truth="X",  # Match - breaks novelty
            context="Computer Science - Machine Learning",
        ),
        PatentSample(
            claim="A device comprising a processor, a memory, and a display screen configured to show real-time notifications.",
            paragraph="The invention includes a computing unit with storage capability. It can display information to users.",
            ground_truth="A",  # No match - missing real-time notification feature
            context="Computer Hardware",
        ),
        PatentSample(
            claim="A pharmaceutical composition comprising compound X in combination with compound Y for treating disease Z.",
            paragraph="The formulation contains compound X and compound Y. These compounds work synergistically to treat disease Z.",
            ground_truth="X",  # Match - all key features present
            context="Pharmaceutical",
        ),
    ]
    return samples


def setup_dummy_llm():
    """Set up dummy LLM with pre-queued responses for demonstration."""
    client = DummyLLMClient()

    # Response set 1: For sample 1 (correct X classification)
    client.queue(
        json.dumps(
            {
                "reasoning": "The claim describes three key steps: receiving input, applying neural network, outputting transformed data. The paragraph mentions receiving data, processing through neural network layers, and outputting results. All three key features are present in equivalent form. This constitutes a match.",
                "bullet_ids": [],
                "final_answer": "X",
            }
        )
    )
    client.queue(
        json.dumps(
            {
                "reasoning": "The classification was correct. The examiner properly identified all three claim features in the prior art.",
                "error_identification": "",
                "root_cause_analysis": "",
                "correct_approach": "Systematic feature-by-feature comparison was performed.",
                "key_insight": "When all claim limitations are disclosed in the prior art, novelty is destroyed (X classification).",
                "bullet_tags": [],
            }
        )
    )
    client.queue(
        json.dumps(
            {
                "reasoning": "Adding guidance on feature identification.",
                "operations": [
                    {
                        "type": "ADD",
                        "section": "feature_identification",
                        "content": "Break down claims into individual limitations and verify each limitation is present in the prior art.",
                        "metadata": {"helpful": 1},
                    }
                ],
            }
        )
    )

    # Response set 2: For sample 2 (correct A classification)
    client.queue(
        json.dumps(
            {
                "reasoning": "The claim requires: processor, memory, display, AND real-time notification capability. The paragraph mentions processor (computing unit), memory (storage), and display. However, the real-time notification feature is missing. Not all features are present.",
                "bullet_ids": [],
                "final_answer": "A",
            }
        )
    )
    client.queue(
        json.dumps(
            {
                "reasoning": "Correct classification. The examiner identified the missing feature.",
                "error_identification": "",
                "root_cause_analysis": "",
                "correct_approach": "Checked for completeness of all claim features.",
                "key_insight": "If even one claim limitation is absent from prior art, novelty is maintained (A classification).",
                "bullet_tags": [],
            }
        )
    )
    client.queue(
        json.dumps(
            {
                "reasoning": "Adding guidance on completeness checking.",
                "operations": [
                    {
                        "type": "ADD",
                        "section": "common_errors",
                        "content": "Avoid classifying as X if any claim limitation is missing from the prior art, even if most features match.",
                        "metadata": {"helpful": 1},
                    }
                ],
            }
        )
    )

    # Response set 3: For sample 3 (correct X classification)
    client.queue(
        json.dumps(
            {
                "reasoning": "Claim elements: compound X + compound Y + treats disease Z. Paragraph discloses: compound X, compound Y, synergistic treatment of disease Z. All elements present including the functional relationship (treating the disease). This is a match.",
                "bullet_ids": [],
                "final_answer": "X",
            }
        )
    )
    client.queue(
        json.dumps(
            {
                "reasoning": "Correct classification. All components and their functional relationship were identified.",
                "error_identification": "",
                "root_cause_analysis": "",
                "correct_approach": "Considered both structural and functional aspects of the claim.",
                "key_insight": "In pharmaceutical claims, verify both the composition components and their intended use/function.",
                "bullet_tags": [],
            }
        )
    )
    client.queue(
        json.dumps(
            {
                "reasoning": "Adding domain-specific guidance.",
                "operations": [
                    {
                        "type": "ADD",
                        "section": "domain_specific",
                        "content": "For pharmaceutical claims, check both composition (compounds) and function (therapeutic use).",
                        "metadata": {"helpful": 1},
                    }
                ],
            }
        )
    )

    return client


def main():
    """Run the PATENTMATCH demonstration."""
    print("=" * 80)
    print("PATENTMATCH Task Demonstration with ACE Framework")
    print("=" * 80)
    print()

    # Create sample data
    samples = create_sample_data()
    print(f"Created {len(samples)} patent examination samples")
    print()

    # Set up components
    client = setup_dummy_llm()
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

    environment = PatentMatchEnvironment()

    # Run adaptation
    print("Running ACE adaptation loop...")
    results = adapter.run(samples, environment, epochs=1)
    print(f"Completed {len(results)} adaptations")
    print()

    # Display results
    print("=" * 80)
    print("Results Summary")
    print("=" * 80)
    print()

    for i, result in enumerate(results, 1):
        sample = result.sample
        print(f"Sample {i}:")
        print(f"  Claim: {sample.claim[:80]}...")
        print(f"  Prediction: {result.generator_output.final_answer}")
        print(f"  Ground Truth: {sample.ground_truth}")
        print(f"  Correct: {result.generator_output.final_answer == sample.ground_truth}")
        print(f"  Metrics: {result.environment_result.metrics}")
        print()

    # Display playbook stats
    print("=" * 80)
    print("Playbook Evolution")
    print("=" * 80)
    print()
    print(f"Playbook Statistics: {playbook.stats()}")
    print()
    print("Learned Strategies:")
    for bullet in playbook.bullets():
        print(f"  [{bullet.section}] {bullet.content}")
    print()

    # Display aggregate metrics
    print("=" * 80)
    print("Aggregate Metrics")
    print("=" * 80)
    print()
    final_metrics = environment.metrics_calculator.compute()
    print(f"  Accuracy:   {final_metrics['accuracy']:.3f}")
    print(f"  Precision:  {final_metrics['precision']:.3f}")
    print(f"  Recall:     {final_metrics['recall']:.3f}")
    print(f"  F1 Score:   {final_metrics['f1']:.3f}")
    print(f"  Perplexity: {final_metrics['perplexity']:.3f}")
    print()

    print("=" * 80)
    print("Demonstration Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
