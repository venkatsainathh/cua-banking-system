import asyncio
from typing import Any, Dict
from playwright.async_api import async_playwright
from core.guardrails import SafetyGuardrails
from core.hitl import HITLController
from core.locators import LocatorResolver
from core.models import ActionType, CapabilityArtifact, ExecutionResult, OutcomeCategory
from core.tracer import Tracer

class DeterministicReplayEngine:
    def __init__(self, artifact: CapabilityArtifact, headless: bool = True):
        self.artifact = artifact
        self.headless = headless
        self.tracer = Tracer(f"replay_{artifact.capability_name}")

    async def execute(self, inputs: Dict[str, Any]) -> ExecutionResult:
        self.tracer.log("REPLAY_INITIALIZING", {"inputs": inputs})
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            hitl = HITLController(page, self.tracer)
            extracted_outputs: Dict[str, Any] = {}

            try:
                for step in self.artifact.steps:
                    self.tracer.log("STEP_START", {"step_id": step.step_id, "action": step.action})
                    SafetyGuardrails.validate_action(step.action, step.is_irreversible)

                    # 1. Proactive check for business outcome exceptions
                    for branch in self.artifact.business_branches:
                        try:
                            loc = await LocatorResolver.resolve(page, branch.condition_locator, timeout=500)
                            if await loc.is_visible():
                                self.tracer.log("BUSINESS_OUTCOME_DETECTED", {"outcome": branch.outcome_code})
                                await browser.close()
                                return ExecutionResult(
                                    status=OutcomeCategory.BUSINESS_OUTCOME,
                                    outcome_code=branch.outcome_code,
                                    message=branch.message,
                                    outputs=extracted_outputs
                                )
                        except Exception:
                            pass

                    # 2. Replay step actions
                    if step.action == ActionType.NAVIGATE:
                        url = step.static_value or self.artifact.target_origin
                        SafetyGuardrails.validate_navigation(url)
                        await page.goto(url)

                    elif step.action == ActionType.FILL:
                        val = inputs.get(step.param_binding, step.static_value)
                        try:
                            el = await LocatorResolver.resolve(page, step.target)
                            await el.fill(str(val))
                        except Exception:
                            await hitl.escalate(f"Failed to resolve fill target on step {step.step_id}", {"step_id": step.step_id})

                    elif step.action == ActionType.SELECT:
                        val = inputs.get(step.param_binding, step.static_value)
                        try:
                            el = await LocatorResolver.resolve(page, step.target)
                            await el.select_option(value=str(val))
                        except Exception:
                            await hitl.escalate(f"Failed to select dropdown on step {step.step_id}", {"step_id": step.step_id})

                    elif step.action == ActionType.CLICK:
                        try:
                            el = await LocatorResolver.resolve(page, step.target)
                            await el.click()
                        except Exception:
                            await hitl.escalate(f"Failed to click target on step {step.step_id}", {"step_id": step.step_id})

                    elif step.action == ActionType.EXTRACT:
                        el = await LocatorResolver.resolve(page, step.target)
                        extracted_text = (await el.inner_text()).strip()
                        extracted_outputs[step.extract_key] = extracted_text

                    await page.wait_for_load_state("domcontentloaded")

                # 3. Checkpoint Assertion
                try:
                    checkpoint = await LocatorResolver.resolve(page, self.artifact.success_checkpoint)
                    if await checkpoint.is_visible():
                        self.tracer.log("REPLAY_SUCCESS", {"outputs": extracted_outputs})
                        await browser.close()
                        return ExecutionResult(
                            status=OutcomeCategory.SUCCESS,
                            outputs=extracted_outputs,
                            message="Flow verified successfully against checkpoint."
                        )
                except Exception:
                    pass

                # Re-verify business branches on failure
                for branch in self.artifact.business_branches:
                    try:
                        loc = await LocatorResolver.resolve(page, branch.condition_locator, timeout=500)
                        if await loc.is_visible():
                            await browser.close()
                            return ExecutionResult(
                                status=OutcomeCategory.BUSINESS_OUTCOME,
                                outcome_code=branch.outcome_code,
                                message=branch.message,
                                outputs=extracted_outputs
                            )
                    except Exception:
                        pass

                err_screenshot = await self.tracer.capture_screenshot(page, "replay_hard_failure")
                await browser.close()
                return ExecutionResult(
                    status=OutcomeCategory.HARD_FAILURE,
                    message="Terminal checkpoint not met.",
                    evidence_path=err_screenshot
                )

            except Exception as e:
                err_screenshot = await self.tracer.capture_screenshot(page, "replay_exception")
                await browser.close()
                return ExecutionResult(
                    status=OutcomeCategory.HARD_FAILURE,
                    message=f"Runtime exception: {str(e)}",
                    evidence_path=err_screenshot
                )

if __name__ == "__main__":
    with open("capabilities/open_subaccount_v1.json") as f:
        artifact = CapabilityArtifact.model_validate_json(f.read())
    
    engine = DeterministicReplayEngine(artifact, headless=True)
    
    # Run 1: Happy Path
    success_res = asyncio.run(engine.execute({
        "member_id": "12345",
        "product_type": "CD_12M",
        "initial_deposit": "1000.00"
    }))
    with open("evidence/replay_success.json", "w") as f:
        f.write(success_res.model_dump_json(indent=2))
    print("[+] Successful replay -> evidence/replay_success.json")

    # Run 2: Business Outcome (Member Not Found)
    business_err_res = asyncio.run(engine.execute({
        "member_id": "99999",
        "product_type": "MONEY_MARKET",
        "initial_deposit": "500.00"
    }))
    with open("evidence/replay_business_error.json", "w") as f:
        f.write(business_err_res.model_dump_json(indent=2))
    print("[+] Business error replay -> evidence/replay_business_error.json")