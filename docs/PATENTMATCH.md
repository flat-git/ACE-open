# PATENTMATCH Task Adaptation

This document describes how the ACE framework has been adapted to support the **PATENTMATCH** task, which simulates patent examiner assessment of novelty.

## Overview

PATENTMATCH is a text pair binary classification task designed to simulate the core work of patent examiners evaluating the "novelty" of a new invention. The task evaluates whether prior art (existing patents) breaks the novelty of a new patent claim.

### Task Definition

**Input:** A pair of texts:
- **Claim**: Text from a patent application being filed, using legal language to precisely define the scope of protection for a new invention
- **Paragraph**: Text from an already published, earlier patent document (called "prior art")

**Core Question:** "Does this prior art paragraph describe the exact same invention as the claim, thereby breaking the novelty of the claim?"

**Output:** A binary label based on classifications used by European Patent Office (EPO) examiners:
- **Positive Sample (X-class document)**: The paragraph content is sufficient to break the novelty of the claim (MATCH)
- **Negative Sample (A-class document)**: The paragraph is merely related technical background and does not affect novelty or inventiveness (NO MATCH)

### Task Difficulty

This task is extremely challenging because it requires far more than simple keyword matching:
- Understanding patent domain legal terminology and technical vocabulary
- Deep semantic reasoning to judge whether two technical descriptions are legally equivalent
- Handling complex language patterns and legal terminology

## Framework Adaptations

### 1. Data Structure: PatentSample

A new `PatentSample` class extends the base `Sample` to handle text pairs:

```python
from ace import PatentSample

sample = PatentSample(
    claim="A method for processing data comprising...",
    paragraph="The system processes information using...",
    ground_truth="X",  # or "A"
    context="Computer Science domain"
)
```

**Key fields:**
- `claim`: The patent claim text
- `paragraph`: The prior art paragraph text  
- `ground_truth`: Expected classification ("X" for match, "A" for no match)
- `context`: Optional domain context

### 2. Task Environment: PatentMatchEnvironment

Specialized environment for binary classification evaluation:

```python
from ace import PatentMatchEnvironment

environment = PatentMatchEnvironment()
result = environment.evaluate(sample, generator_output)
```

**Features:**
- Binary classification validation (X/A labels)
- Comprehensive metric tracking (accuracy, precision, recall, F1, perplexity)
- Detailed feedback messages for correct/incorrect classifications
- Aggregate statistics across multiple samples

### 3. Evaluation Metrics

The `MetricsCalculator` class provides comprehensive evaluation:

**Primary Performance:**
- **Accuracy**: Overall correctness rate (standard metric for direct comparison)

**Classification Performance:**
- **Precision**: Accuracy of "classifying X as X" (core task metric)
- **Recall**: Ability to "find all X cases"
- **F1 Score**: Harmonic mean of precision and recall (standard metric)

**Model Confidence:**
- **Perplexity**: Measures decision confidence and stability

### 4. Patent-Specific Prompts

Three specialized prompts for patent examination:

**Generator Prompt** (`PATENTMATCH_GENERATOR_PROMPT`):
- Guides step-by-step feature comparison
- Emphasizes legal and semantic equivalence
- Outputs structured reasoning and X/A classification

**Reflector Prompt** (`PATENTMATCH_REFLECTOR_PROMPT`):
- Analyzes feature identification correctness
- Identifies missed similarities or differences
- Extracts insights for improving patent examination

**Curator Prompt** (`PATENTMATCH_CURATOR_PROMPT`):
- Focuses on patent-specific strategies
- Maintains sections for feature identification, common errors, legal principles
- Updates playbook with domain-specific guidance

## Usage Examples

### Basic Usage

```python
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

# Create samples
samples = [
    PatentSample(
        claim="A device with feature X and feature Y",
        paragraph="The invention includes feature X and Y",
        ground_truth="X"
    )
]

# Set up ACE components with patent prompts
client = DummyLLMClient()  # Replace with real LLM
playbook = Playbook()

generator = Generator(client, prompt_template=PATENTMATCH_GENERATOR_PROMPT)
reflector = Reflector(client, prompt_template=PATENTMATCH_REFLECTOR_PROMPT)
curator = Curator(client, prompt_template=PATENTMATCH_CURATOR_PROMPT)

adapter = OfflineAdapter(
    playbook=playbook,
    generator=generator,
    reflector=reflector,
    curator=curator,
)

# Run adaptation
environment = PatentMatchEnvironment()
results = adapter.run(samples, environment, epochs=1)

# Get metrics
metrics = environment.metrics_calculator.compute()
print(f"Accuracy: {metrics['accuracy']:.3f}")
print(f"F1 Score: {metrics['f1']:.3f}")
print(f"Perplexity: {metrics['perplexity']:.3f}")
```

### Running the Demo

A complete demonstration is available:

```bash
cd /home/runner/work/ACE-open/ACE-open
PYTHONPATH=. python examples/patentmatch_demo.py
```

This demonstrates:
- Three patent examination scenarios across different domains
- ACE adaptation loop with playbook evolution
- Comprehensive metrics reporting
- Learned strategies display

## Key Design Decisions

1. **Backward Compatibility**: PatentSample extends Sample, allowing seamless integration with existing ACE infrastructure

2. **Flexible Field Passing**: The Generator and Reflector roles support both generic `question` format and patent-specific `claim/paragraph` fields

3. **Comprehensive Metrics**: All standard classification metrics plus perplexity for confidence measurement

4. **Domain-Specific Playbook Sections**: 
   - `feature_identification`: Strategies for identifying claim features
   - `common_errors`: Patterns of frequent mistakes
   - `legal_principles`: Patent law guidelines
   - `domain_specific`: Technical domain guidance

5. **Detailed Feedback**: Environment provides actionable feedback explaining why classifications are correct/incorrect

## File Structure

```
ace/
├── patent.py              # PatentSample, PatentMatchEnvironment
├── prompts_patent.py      # Patent-specific prompts
├── metrics.py             # MetricsCalculator for evaluation
└── ...                    # Existing ACE components

examples/
└── patentmatch_demo.py    # Demonstration script

tests/
└── test_patent.py         # Comprehensive test suite

docs/
└── PATENTMATCH.md         # This document
```

## Testing

Run the test suite:

```bash
python -m unittest tests.test_patent
```

Tests cover:
- PatentSample creation and initialization
- Environment evaluation (correct/incorrect classifications)
- Metrics calculation (accuracy, precision, recall, F1, perplexity)
- Full ACE adaptation loop with patent prompts

## Future Enhancements

Potential improvements:
1. Multi-class classification (X, Y, A categories from EPO)
2. Partial matching scores for claims with multiple limitations
3. Citation network analysis for prior art relationships
4. Domain-specific embeddings for technical feature matching
5. Integration with real patent databases

## References

- European Patent Office (EPO) classification system
- Patent claim construction principles
- ACE framework: Agentic Context Engineering (arXiv:2510.04618)
