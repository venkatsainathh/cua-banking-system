import asyncio
import glob
import json
import os
import time
from typing import Any, Dict, List, Optional
from core.engine import DeterministicReplayEngine
from core.models import CapabilityArtifact, ExecutionResult, OutcomeCategory

class CapabilityCatalog:
    """
    Exposes saved capability artifacts as an agent-callable tool registry.
    Allows upstream AI agents to discover tools, inspect schemas, and invoke them by name.
    """
    def __init__(self, capabilities_dir: str = "capabilities"):
        self.capabilities_dir = capabilities_dir
        self.registry: Dict[str, CapabilityArtifact] = {}
        self._load_catalog()

    def _load_catalog(self):
        for filepath in glob.glob(os.path.join(self.capabilities_dir, "*.json")):
            with open(filepath, "r") as f:
                artifact = CapabilityArtifact.model_validate_json(f.read())
                self.registry[artifact.capability_name] = artifact

    def list_capabilities(self) -> List[Dict[str, Any]]:
        """Returns a list of all callable capabilities in OpenAI/Claude tool-definition format."""
        tools = []
        for name, artifact in self.registry.items():
            properties = {}
            for param, ptype in artifact.input_schema.items():
                properties[param] = {"type": ptype, "description": f"Input parameter: {param}"}

            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": artifact.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": list(artifact.input_schema.keys())
                    }
                }
            })
        return tools

    async def invoke(self, capability_name: str, arguments: Dict[str, Any], headless: bool = True) -> ExecutionResult:
        """Invokes a registered capability deterministically with typed arguments."""
        if capability_name not in self.registry:
            return ExecutionResult(
                status=OutcomeCategory.HARD_FAILURE,
                message=f"Capability '{capability_name}' not found in catalog."
            )

        artifact = self.registry[capability_name]
        engine = DeterministicReplayEngine(artifact, headless=headless)
        return await engine.execute(arguments)

    async def evaluate_stability(self, capability_name: str, sample_inputs: Dict[str, Any], runs: int = 5) -> Dict[str, Any]:
        """Replays N times and computes a stability/flakiness metric."""
        if capability_name not in self.registry:
            raise ValueError(f"Capability '{capability_name}' does not exist.")

        successes = 0
        durations = []
        outcomes = []

        for _ in range(runs):
            start = time.time()
            res = await self.invoke(capability_name, sample_inputs, headless=True)
            elapsed = time.time() - start

            durations.append(round(elapsed, 2))
            outcomes.append(res.status)
            if res.status == OutcomeCategory.SUCCESS:
                successes += 1

        stability_rate = (successes / runs) * 100.0
        return {
            "capability_name": capability_name,
            "total_runs": runs,
            "successful_runs": successes,
            "stability_score": f"{stability_rate:.1f}%",
            "is_approved_for_unattended": stability_rate == 100.0,
            "avg_execution_time_sec": round(sum(durations) / len(durations), 2),
            "run_outcomes": outcomes
        }