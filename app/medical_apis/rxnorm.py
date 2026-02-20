import httpx

RXNORM_BASE = "https://rxnav.nlm.nih.gov/REST"


async def get_rxcui(drug_name: str) -> str | None:
    """Look up the RxNorm concept ID (RxCUI) for a drug name."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{RXNORM_BASE}/rxcui.json",
            params={"name": drug_name, "search": 1},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        ids = data.get("idGroup", {}).get("rxnormId", [])
        return ids[0] if ids else None


async def get_drug_interactions(rxcuis: list[str]) -> list[dict]:
    """Get interactions between a list of drugs (by RxCUI)."""
    if len(rxcuis) < 2:
        return []
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{RXNORM_BASE}/interaction/list.json",
            params={"rxcuis": "+".join(rxcuis)},
        )
        if resp.status_code != 200:
            return []
        data = resp.json()

    interactions = []
    for group in data.get("fullInteractionTypeGroup", []):
        for itype in group.get("fullInteractionType", []):
            for pair in itype.get("interactionPair", []):
                interactions.append({
                    "severity": pair.get("severity", "N/A"),
                    "description": pair.get("description", ""),
                    "drugs": [
                        c.get("minConceptItem", {}).get("name", "")
                        for c in pair.get("interactionConcept", [])
                    ],
                })
    return interactions


async def lookup_drug_info(drug_names: list[str]) -> dict:
    """Look up drug info and interactions for a list of drug names."""
    rxcuis = []
    name_map = {}
    for name in drug_names:
        rxcui = await get_rxcui(name)
        if rxcui:
            rxcuis.append(rxcui)
            name_map[rxcui] = name

    interactions = await get_drug_interactions(rxcuis) if len(rxcuis) >= 2 else []

    return {
        "resolved_drugs": {name: rxcui for rxcui, name in name_map.items()},
        "interactions": interactions,
    }
