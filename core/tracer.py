import json
import os
import time
from playwright.async_api import Page
from core.guardrails import SafetyGuardrails

class Tracer:
    def __init__(self, trace_name: str, output_dir: str = "evidence"):
        self.trace_name = trace_name
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.log_file = os.path.join(output_dir, f"{trace_name}.log")

    def log(self, event_type: str, payload: dict):
        sanitized_payload = SafetyGuardrails.sanitize_data(payload)
        entry = {
            "timestamp": time.time(),
            "event": event_type,
            "data": sanitized_payload
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def capture_screenshot(self, page: Page, name_prefix: str) -> str:
        filename = f"{name_prefix}_{int(time.time())}.png"
        filepath = os.path.join(self.output_dir, filename)
        await page.screenshot(path=filepath, full_page=True)
        return filepath