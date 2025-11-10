"""Agentic Context Engineering (ACE) reproduction framework."""

from .playbook import Bullet, Playbook
from .delta import DeltaOperation, DeltaBatch
from .llm import LLMClient, DummyLLMClient, TransformersLLMClient
from .roles import (
    Generator,
    Reflector,
    Curator,
    GeneratorOutput,
    ReflectorOutput,
    CuratorOutput,
)
from .adaptation import (
    OfflineAdapter,
    OnlineAdapter,
    Sample,
    TaskEnvironment,
    EnvironmentResult,
    AdapterStepResult,
)
from .metrics import MetricsCalculator
from .patent import (
    PatentSample,
    PatentMatchEnvironment,
    PatentEnvironmentResult,
)

__all__ = [
    "Bullet",
    "Playbook",
    "DeltaOperation",
    "DeltaBatch",
    "LLMClient",
    "DummyLLMClient",
    "TransformersLLMClient",
    "Generator",
    "Reflector",
    "Curator",
    "GeneratorOutput",
    "ReflectorOutput",
    "CuratorOutput",
    "OfflineAdapter",
    "OnlineAdapter",
    "Sample",
    "TaskEnvironment",
    "EnvironmentResult",
    "AdapterStepResult",
    "MetricsCalculator",
    "PatentSample",
    "PatentMatchEnvironment",
    "PatentEnvironmentResult",
]
