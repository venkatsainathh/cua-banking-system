import asyncio
from playwright.async_api import Page
from core.tracer import Tracer

class HITLController:
    def __init__(self, page: Page, tracer: Tracer):
        self.page = page
        self.tracer = tracer

    async def escalate(self, reason: str, context: dict) -> bool:
        screenshot_file = await self.tracer.capture_screenshot(self.page, f"hitl_escalation_{context.get('step_id', 'unknown')}")
        
        self.tracer.log("ESCALATION_TRIGGERED", {
            "reason": reason,
            "url": self.page.url,
            "context": context,
            "evidence_screenshot": screenshot_file
        })

        print("\n" + "="*80)
        print("[!] HUMAN INTERVENTION REQUIRED")
        print(f"[!] Reason: {reason}")
        print(f"[!] Live URL: {self.page.url}")
        print(f"[!] Screenshot: {screenshot_file}")
        print("[!] Execution paused on live session. Complete the action in the browser.")
        print("="*80)

        # Await console input to resume
        await asyncio.to_thread(input, "\n>>> Press [ENTER] once manual intervention is complete: ")

        self.tracer.log("ESCALATION_RESOLVED", {"resumed_url": self.page.url})
        return True