# Agentic Context Engineering (ACE) Reproduction Framework

This repository contains an implementation scaffold for reproducing the **Agentic Context Engineering (ACE)** method from *Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models* (arXiv:2510.04618).

The code follows the paper’s design:

- Contexts are structured playbooks made of bullet entries with helpful/harmful counters.
- Three agentic roles (Generator, Reflector, Curator) interact through incremental delta updates.
- Offline and online adaptation loops support multi-epoch training and test-time continual learning.

Refer to `docs/method_outline.md` for a distilled summary of the methodology extracted from the paper.

**NEW: PATENTMATCH Task Support** - The framework has been adapted to support patent novelty assessment tasks. See [PATENTMATCH documentation](docs/PATENTMATCH.md) for details.

## Repository Layout

- `ace/`: core library modules (playbook store, delta operations, roles, adaptation drivers, prompts, LLM abstractions).
- `tests/`: lightweight regression tests using a dummy LLM and a toy environment.
- `docs/`: engineering notes on the paper’s method.

## Quick Start

1. **Ensure Python 3.9+** (development used 3.12). No third-party dependencies are required for the core scaffold.
2. (Optional) Create a virtual environment and activate it.
3. Run the unit tests:
   
   ```bash
   python -m unittest discover -s tests
   ```

## Example Usage

Here is a minimal offline adaptation loop with the dummy LLM:

```python
import json
from ace import (
    Playbook, DummyLLMClient, Generator, Reflector, Curator,
    OfflineAdapter, Sample, TaskEnvironment, EnvironmentResult
)

class ToyEnv(TaskEnvironment):
    def evaluate(self, sample, generator_output):
        gt = sample.ground_truth or ""
        pred = generator_output.final_answer
        feedback = "correct" if pred == gt else f"expected {gt} but got {pred}"
        return EnvironmentResult(feedback=feedback, ground_truth=gt)

client = DummyLLMClient()
client.queue(json.dumps({"reasoning": "...", "bullet_ids": [], "final_answer": "42"}))
client.queue(json.dumps({"reasoning": "...", "error_identification": "", "root_cause_analysis": "",
                         "correct_approach": "", "key_insight": "Remember 42.", "bullet_tags": []}))
client.queue(json.dumps({"reasoning": "...", "operations": [{"type": "ADD", "section": "defaults",
                         "content": "Answer 42 when in doubt.", "metadata": {"helpful": 1}}]}))

adapter = OfflineAdapter(
    playbook=Playbook(),
    generator=Generator(client),
    reflector=Reflector(client),
    curator=Curator(client),
)

samples = [Sample(question="Life?", ground_truth="42")]
adapter.run(samples, ToyEnv(), epochs=1)
```

Replace `DummyLLMClient` with a production LLM client (e.g., OpenAI, DeepSeek) and implement a task-specific `TaskEnvironment` to integrate real execution feedback from AppWorld or domain benchmarks.

### PATENTMATCH Example

For patent novelty assessment tasks:

```bash
PYTHONPATH=. python examples/patentmatch_demo.py
```

See [PATENTMATCH documentation](docs/PATENTMATCH.md) for detailed usage.

## Extending to Full Experiments

- Implement an `LLMClient` subclass that wraps your chosen model API.
- Provide task-specific prompts (see `ace/prompts.py`) or customize them per domain.
- Build `TaskEnvironment` adapters that run the benchmark workflow (e.g., AppWorld ReAct agent, FiNER/Formula evaluation).
- Configure offline (`OfflineAdapter.run`) and online (`OnlineAdapter.run`) loops with up to 5 epochs and reflector refinement rounds as reported in the paper.
- Swap in a real LLM by using `ace.TransformersLLMClient`. For example, to use the local gpt-oss-20b weights on GPUs 2 and 3:
  
  ```bash
  CUDA_VISIBLE_DEVICES=2,3 python scripts/run_local_adapter.py
  ```
  
  (See the script in `scripts/` for a minimal setup that wires the model into ACE.)

*Note that this is not official implementation, just due to they do not release the official version, I repreduce it. Once the official version released, I will link to that.*
