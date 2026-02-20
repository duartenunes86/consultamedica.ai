import httpx

OPENFDA_BASE = "https://api.fda.gov"


async def get_adverse_events(drug_name: str, limit: int = 5) -> list[dict]:
    """Query OpenFDA for adverse event reports for a drug."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{OPENFDA_BASE}/drug/event.json",
            params={
                "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                "limit": limit,
            },
        )
        if resp.status_code != 200:
            return []
        data = resp.json()

    events = []
    for result in data.get("results", []):
        reactions = [
            r.get("reactionmeddrapt", "")
            for r in result.get("patient", {}).get("reaction", [])
        ]
        events.append({
            "serious": result.get("serious", "0") == "1",
            "reactions": reactions[:5],
        })
    return events


async def get_drug_label(drug_name: str) -> dict | None:
    """Get drug label information from OpenFDA."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{OPENFDA_BASE}/drug/label.json",
            params={
                "search": f'openfda.brand_name:"{drug_name}"',
                "limit": 1,
            },
        )
        if resp.status_code != 200:
            return None
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return None
    label = results[0]
    return {
        "warnings": (label.get("warnings") or ["N/A"])[0][:500],
        "drug_interactions": (label.get("drug_interactions") or ["N/A"])[0][:500],
        "adverse_reactions": (label.get("adverse_reactions") or ["N/A"])[0][:500],
    }


async def lookup_drug_safety(drug_names: list[str]) -> dict:
    """Get safety info for a list of drugs from OpenFDA."""
    results = {}
    for name in drug_names:
        label = await get_drug_label(name)
        events = await get_adverse_events(name, limit=3)
        results[name] = {"label": label, "adverse_events": events}
    return results
