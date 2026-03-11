# Product Manifesto: Azure Migration Assessment & Compliance Prioritization Engine

## 1. Core Vision & Value Proposition
A multi-tenant, AI-enriched operational platform that extracts raw Azure Policy/Initiative data and translates it into prioritized, effort-estimated remediation plans. 
Native Azure tooling identifies non-compliance but lacks business context (complexity, time, change control impact). This platform bridges that gap, acting as a critical decision-support tool during client migrations and operational reviews to immediately surface "low-hanging fruit."

## 2. Core Modules & UI Tiers
* **Tier 1: Executive Migration Snapshot:** Minimalist view. One page per Application (Subscription). Displays starting baseline, deviation from target state, and aggregate estimated effort/cost to remediate.
* **Tier 2: Operational Prioritization Dashboard:** The core pivot engine. Sorts non-compliant items by Resource Category or Initiative. Intelligently surfaces low-complexity, low-time remediation items first.
* **Tier 3: Deep-Dive Remediation Matrix:** Hierarchical drill-down (Initiative -> Policy -> Resource). Displays specific required technical fixes, AI-calculated complexity scores, and change control impact.

## 3. Architecture Stack
* **Orchestration (The Skeleton):** n8n handles deterministic, scheduled API polling against Azure Resource Graph (KQL) or REST APIs via Service Principal authentication.
* **Intelligence (The Muscle):** Google Antigravity/Python agents intercept raw Azure JSON. LLM nodes evaluate violated policies against standard matrices to generate complexity, priority, and effort metadata.
* **Presentation (The Glass):** React/Tailwind frontend (prototyped via Lovable/Stitch) displaying the enriched JSON payloads.

## 4. Operating Principles for "The Architect" (Gem Persona)
When advising on this platform, you must prioritize the data translation layer. Focus on how raw JSON is parsed, how the LLM maintains consistency in scoring "effort," and how the data schema natively supports the UI filtering requirements. Default to self-hosted, scalable architectural patterns.