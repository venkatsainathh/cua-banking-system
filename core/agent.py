import asyncio
from typing import Any, Dict, List
from playwright.async_api import Page, async_playwright
from core.guardrails import SafetyGuardrails
from core.models import (
    ActionType,
    BusinessOutcomeBranch,
    CapabilityArtifact,
    MultiTierLocator,
    StepDefinition,
)
from core.tracer import Tracer

class LocalDiscoveryAgent:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.tracer = Tracer("discovery_run")
        self.recorded_steps: List[StepDefinition] = []

    async def _observe_state(self, page: Page) -> Dict[str, Any]:
        await page.wait_for_load_state("domcontentloaded")
        return await page.evaluate("""
            () => {
                const inputs = Array.from(document.querySelectorAll('input, select, button')).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.name || null,
                    type: el.type || null,
                    value: el.value || null,
                    text: el.innerText || null
                }));
                return { url: window.location.href, elements: inputs };
            }
        """)

    async def run_discovery_loop(self, goal: str) -> CapabilityArtifact:
        SafetyGuardrails.validate_navigation(self.base_url)
        print(f"\n[*] Starting Discovery Loop for Goal: '{goal}'")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=250)
            page = await browser.new_page()

            # Step 1: Navigate
            self.tracer.log("AGENT_OBSERVE", {"action": "navigate", "target": self.base_url})
            await page.goto(self.base_url)
            self.recorded_steps.append(
                StepDefinition(step_id=1, action=ActionType.NAVIGATE, static_value=self.base_url, description="Navigate to banking console.")
            )

            # Step 2: Fill Member ID
            await self._observe_state(page)
            self.tracer.log("AGENT_DECIDE_ACT", {"action": "fill", "target": "#f_mem_id", "value": "12345"})
            await page.fill("#f_mem_id", "12345")
            self.recorded_steps.append(
                StepDefinition(
                    step_id=2,
                    action=ActionType.FILL,
                    target=MultiTierLocator(role="textbox", accessible_name="Member Account ID:", css_fallback="#f_mem_id", xpath_fallback="//input[@id='f_mem_id']"),
                    param_binding="member_id",
                    description="Enter Member ID into lookup input."
                )
            )

            # Step 3: Click Search
            self.tracer.log("AGENT_DECIDE_ACT", {"action": "click", "target": "Query Database"})
            await page.click("input[value='Query Database']")
            self.recorded_steps.append(
                StepDefinition(
                    step_id=3,
                    action=ActionType.CLICK,
                    target=MultiTierLocator(role="button", accessible_name="Query Database", css_fallback="input[value='Query Database']", xpath_fallback="//input[@value='Query Database']"),
                    description="Execute member query."
                )
            )

            # Step 4: Click Open Sub-Account
            await self._observe_state(page)
            self.tracer.log("AGENT_DECIDE_ACT", {"action": "click", "target": "Open Sub-Account"})
            await page.click("input[value='Open Sub-Account']")
            self.recorded_steps.append(
                StepDefinition(
                    step_id=4,
                    action=ActionType.CLICK,
                    target=MultiTierLocator(role="button", accessible_name="Open Sub-Account", css_fallback="input[value='Open Sub-Account']", xpath_fallback="//input[@value='Open Sub-Account']"),
                    description="Proceed to sub-account module."
                )
            )

            # Step 5: Select Product Type
            await self._observe_state(page)
            self.tracer.log("AGENT_DECIDE_ACT", {"action": "select", "target": "#sel_prod", "value": "CD_12M"})
            await page.select_option("#sel_prod", "CD_12M")
            self.recorded_steps.append(
                StepDefinition(
                    step_id=5,
                    action=ActionType.SELECT,
                    target=MultiTierLocator(role="combobox", css_fallback="#sel_prod", xpath_fallback="//select[@id='sel_prod']"),
                    param_binding="product_type",
                    description="Select product variant."
                )
            )

            # Step 6: Fill Deposit
            self.tracer.log("AGENT_DECIDE_ACT", {"action": "fill", "target": "#txt_deposit", "value": "500.00"})
            await page.fill("#txt_deposit", "500.00")
            self.recorded_steps.append(
                StepDefinition(
                    step_id=6,
                    action=ActionType.FILL,
                    target=MultiTierLocator(role="textbox", css_fallback="#txt_deposit", xpath_fallback="//input[@id='txt_deposit']"),
                    param_binding="initial_deposit",
                    description="Provide initial deposit."
                )
            )

            # Step 7: Click Submit
            self.tracer.log("AGENT_DECIDE_ACT", {"action": "click", "target": "Submit & Authorize", "irreversible": True})
            await page.click("input[value='Submit & Authorize']")
            self.recorded_steps.append(
                StepDefinition(
                    step_id=7,
                    action=ActionType.CLICK,
                    target=MultiTierLocator(role="button", accessible_name="Submit & Authorize", css_fallback="input[value='Submit & Authorize']", xpath_fallback="//input[@value='Submit & Authorize']"),
                    is_irreversible=True,
                    description="Authorize sub-account creation."
                )
            )

            # Step 8 & 9: Extract Outputs
            await page.wait_for_selector("#confirmation_header")
            self.recorded_steps.append(
                StepDefinition(
                    step_id=8,
                    action=ActionType.EXTRACT,
                    target=MultiTierLocator(css_fallback="#val_conf_no", xpath_fallback="//td[@id='val_conf_no']"),
                    extract_key="confirmation_number"
                )
            )
            self.recorded_steps.append(
                StepDefinition(
                    step_id=9,
                    action=ActionType.EXTRACT,
                    target=MultiTierLocator(css_fallback="#val_product", xpath_fallback="//td[@id='val_product']"),
                    extract_key="assigned_product"
                )
            )

            screenshot_path = await self.tracer.capture_screenshot(page, "discovery_run_checkpoint")
            print(f"[+] Discovery verification screenshot captured: {screenshot_path}")

            artifact = CapabilityArtifact(
                capability_name="open_member_subaccount",
                description="Discovered flow: Look up member ID, submit creation form, verify confirmation.",
                target_origin=self.base_url,
                input_schema={"member_id": "string", "product_type": "string", "initial_deposit": "string"},
                output_schema={"confirmation_number": "string", "assigned_product": "string"},
                steps=self.recorded_steps,
                business_branches=[
                    BusinessOutcomeBranch(
                        condition_locator=MultiTierLocator(text_content="BUSINESS EXCEPTION: Record not found"),
                        outcome_code="MEMBER_NOT_FOUND",
                        message="The requested member account does not exist."
                    ),
                    BusinessOutcomeBranch(
                        condition_locator=MultiTierLocator(text_content="PERMISSION DENIAL: Member account status is LOCKED"),
                        outcome_code="ACCOUNT_LOCKED",
                        message="Member account is locked; servicing prohibited."
                    )
                ],
                success_checkpoint=MultiTierLocator(
                    text_content="SUB-ACCOUNT CREATION AUTHORIZED",
                    css_fallback="#confirmation_header"
                )
            )

            await browser.close()
            return artifact

if __name__ == "__main__":
    agent = LocalDiscoveryAgent("http://127.0.0.1:8000")
    artifact = asyncio.run(agent.run_discovery_loop(
        goal="Look up member 12345, open a new sub-account, and reach the confirmation screen."
    ))
    
    with open("capabilities/open_subaccount_v1.json", "w") as f:
        f.write(artifact.model_dump_json(indent=2))
    print("[+] Artifact generated at capabilities/open_subaccount_v1.json")