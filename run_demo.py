import asyncio
import json
from core.catalog import CapabilityCatalog

async def main():
    print("=" * 70)
    print("1. AGENT CAPABILITY CATALOG (DISCOVERY SURFACE)")
    print("=" * 70)
    catalog = CapabilityCatalog()
    tools = catalog.list_capabilities()
    print("[+] Registered agent tools:\n", json.dumps(tools, indent=2))

    print("\n" + "=" * 70)
    print("2. INVOKE CAPABILITY VIA AGENT TOOL CALL")
    print("=" * 70)
    result = await catalog.invoke(
        capability_name="open_member_subaccount",
        arguments={"member_id": "12345", "product_type": "CD_12M", "initial_deposit": "1500.00"}
    )
    print("[+] Invocation result:\n", result.model_dump_json(indent=2))

    print("\n" + "=" * 70)
    print("3. MULTI-RUN STABILITY BENCHMARK (N=5 RUNS)")
    print("=" * 70)
    stability = await catalog.evaluate_stability(
        capability_name="open_member_subaccount",
        sample_inputs={"member_id": "12345", "product_type": "CD_12M", "initial_deposit": "500.00"},
        runs=5
    )
    print("[+] Stability report:\n", json.dumps(stability, indent=2))

    with open("evidence/stability_report.json", "w") as f:
        json.dump(stability, f, indent=2)
    print("\n[+] Saved stability report to evidence/stability_report.json")

if __name__ == "__main__":
    asyncio.run(main())