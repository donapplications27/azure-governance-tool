#!/usr/bin/env python3
"""
policy_evaluator.py — Azure Compliance Data Synthesis Engine

This script simulates the core data translation layer described in the
Project Manifesto.  It takes mocked Azure Resource Graph responses
(non-compliant resources), enriches each one with AI-generated remediation
metadata via the Google Gemini Pro API, and outputs the final scored JSON.

Usage:
    export GEMINI_API_KEY="your-key-here"   # Linux / macOS
    set GEMINI_API_KEY=your-key-here         # Windows
    python policy_evaluator.py
"""

import json
import os
import sys

import google.generativeai as genai

# ──────────────────────────────────────────────────
#  1. MOCK AZURE RESOURCE GRAPH DATA
# ──────────────────────────────────────────────────

MOCK_AZURE_RESOURCES: list[dict] = [
    {
        "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg-prod-storage/providers/Microsoft.Storage/storageAccounts/stproddata01",
        "name": "stproddata01",
        "type": "Microsoft.Storage/storageAccounts",
        "location": "eastus",
        "policy_assignment": "Deny-PublicBlobAccess",
        "compliance_state": "NonCompliant",
        "policy_definition": "Storage accounts should disable public blob access",
        "properties": {
            "allowBlobPublicAccess": True,
            "minimumTlsVersion": "TLS1_0",
            "supportsHttpsTrafficOnly": True,
        },
    },
    {
        "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg-prod-compute/providers/Microsoft.Compute/virtualMachines/vm-web-frontend-01",
        "name": "vm-web-frontend-01",
        "type": "Microsoft.Compute/virtualMachines",
        "location": "westeurope",
        "policy_assignment": "Audit-MissingMonitoringExtension",
        "compliance_state": "NonCompliant",
        "policy_definition": "Virtual machines should have the Azure Monitor Agent extension installed",
        "properties": {
            "vmSize": "Standard_D4s_v3",
            "osType": "Linux",
            "extensions_installed": ["CustomScriptExtension"],
        },
    },
    {
        "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg-prod-security/providers/Microsoft.KeyVault/vaults/kv-prod-secrets",
        "name": "kv-prod-secrets",
        "type": "Microsoft.KeyVault/vaults",
        "location": "eastus",
        "policy_assignment": "Audit-KeyVaultDiagnostics",
        "compliance_state": "NonCompliant",
        "policy_definition": "Key Vault should have diagnostic settings configured",
        "properties": {
            "sku": "standard",
            "enableSoftDelete": True,
            "diagnosticSettings": None,
        },
    },
]


# ──────────────────────────────────────────────────
#  2. GEMINI PRO REMEDIATION EVALUATOR
# ──────────────────────────────────────────────────

def evaluate_remediation(policy_name: str, resource_type: str) -> dict:
    """
    Call the Google Gemini Pro API to generate a structured remediation
    assessment for a given Azure Policy violation.

    Args:
        policy_name:   The display name of the violated Azure Policy.
        resource_type: The ARM resource type (e.g. Microsoft.Storage/storageAccounts).

    Returns:
        A dict with keys: complexity_score, estimated_hours, remediation_summary.
    """

    prompt = (
        "You are a Senior Azure Architect with 10+ years of experience in "
        "cloud compliance and remediation.\n\n"
        f"A resource of type **{resource_type}** is non-compliant with the "
        f"following Azure Policy:\n"
        f'  "{policy_name}"\n\n'
        "Evaluate the remediation effort and return ONLY a valid JSON object "
        "(no markdown fences, no commentary) with exactly these keys:\n"
        '  - "complexity_score": one of "Low", "Medium", or "High"\n'
        '  - "estimated_hours": an integer representing the estimated hours to remediate\n'
        '  - "remediation_summary": a concise 2-sentence summary of the remediation steps\n\n'
        "Example response format:\n"
        '{\n'
        '  "complexity_score": "Low",\n'
        '  "estimated_hours": 1,\n'
        '  "remediation_summary": "Disable public blob access via the storage account configuration. '
        'This can be done through the Azure Portal, CLI, or an ARM/Bicep template update."\n'
        '}'
    )

    model = genai.GenerativeModel("gemini-2.0-flash")

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Strip markdown code fences if the model wraps the output
        if raw_text.startswith("```"):
            raw_text = "\n".join(raw_text.split("\n")[1:])
        if raw_text.endswith("```"):
            raw_text = raw_text[: raw_text.rfind("```")].strip()

        result = json.loads(raw_text)

        # Validate expected keys
        for key in ("complexity_score", "estimated_hours", "remediation_summary"):
            if key not in result:
                raise KeyError(f"Missing expected key: {key}")

        return result

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"  ⚠  LLM response parse error: {exc}", file=sys.stderr)
        return {
            "complexity_score": "Unknown",
            "estimated_hours": -1,
            "remediation_summary": "Unable to parse LLM response. Manual review required.",
        }
    except Exception as exc:
        print(f"  ⚠  Gemini API error: {exc}", file=sys.stderr)
        return {
            "complexity_score": "Error",
            "estimated_hours": -1,
            "remediation_summary": f"API call failed: {exc}",
        }


# ──────────────────────────────────────────────────
#  3. MAIN — ENRICHMENT LOOP
# ──────────────────────────────────────────────────

def main() -> None:
    """Enrich each mock resource with AI-generated remediation metadata."""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "ERROR: GEMINI_API_KEY environment variable is not set.\n"
            "  export GEMINI_API_KEY='your-key'   # Linux/macOS\n"
            "  set GEMINI_API_KEY=your-key         # Windows",
            file=sys.stderr,
        )
        sys.exit(1)

    genai.configure(api_key=api_key)

    enriched_resources: list[dict] = []

    print("=" * 60)
    print("  Azure Policy Remediation Evaluator — Data Synthesis Engine")
    print("=" * 60)
    print(f"  Processing {len(MOCK_AZURE_RESOURCES)} non-compliant resources...\n")

    for idx, resource in enumerate(MOCK_AZURE_RESOURCES, start=1):
        print(f"  [{idx}/{len(MOCK_AZURE_RESOURCES)}] {resource['name']}")
        print(f"        Policy : {resource['policy_definition']}")
        print(f"        Type   : {resource['type']}")

        remediation = evaluate_remediation(
            policy_name=resource["policy_definition"],
            resource_type=resource["type"],
        )

        enriched = {
            **resource,
            "ai_remediation": remediation,
        }
        enriched_resources.append(enriched)

        print(f"        Score  : {remediation['complexity_score']}")
        print(f"        Hours  : {remediation['estimated_hours']}")
        print()

    # ── Final output ──
    print("=" * 60)
    print("  ENRICHED COMPLIANCE REPORT (JSON)")
    print("=" * 60)
    print(json.dumps(enriched_resources, indent=2, default=str))


if __name__ == "__main__":
    main()
