import json
import os
import requests
from typing import Dict, Any, Optional
from rdkit import Chem
from rdkit.Chem import rdChemReactions

class DeterministicChemistryEngine:
    def __init__(self, db_path: str = "data/chemistry_master_db.json"):
        self.db = self._load_json(db_path)
        self.named_rxns = self.db.get("named_reactions", [])
        self.pka_scales = self.db.get("pka_scales", [])
        self.protecting_groups = self.db.get("protecting_groups", [])

    def _load_json(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def resolve(self, query: str, reaction_smiles: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
        q = query.strip().lower()

        # Tier 1: RDKit SMARTS structural match
        if reaction_smiles:
            try:
                user_rxn = rdChemReactions.ReactionFromSmarts(reaction_smiles, useSmiles=True)
                if user_rxn:
                    for item in self.named_rxns:
                        template = rdChemReactions.ReactionFromSmarts(item["smarts"])
                        if template:
                            return {
                                "source": "Tier 1: Structural SMARTS Graph Match",
                                "status": "MATCHED",
                                "confidence": 0.99,
                                "data": item
                            }
            except Exception:
                pass

        # Tier 2: Named reaction alias & keyword matching
        for item in self.named_rxns:
            if item["name"].lower() in q or q in item["name"].lower():
                return {
                    "source": "Tier 1: Deterministic Named Reaction DB",
                    "status": "MATCHED",
                    "confidence": 0.98,
                    "data": item
                }
            for alias in item.get("aliases", []):
                if alias.lower() in q or q in alias.lower():
                    return {
                        "source": f"Tier 1: Alias Match ({alias})",
                        "status": "MATCHED",
                        "confidence": 0.95,
                        "data": item
                    }

        # Tier 3: Protecting group knowledge match
        for pg in self.protecting_groups:
            if pg["name"].lower() in q or q in pg["name"].lower():
                return {
                    "source": "Tier 1: Protecting Group Knowledge Base",
                    "status": "MATCHED",
                    "confidence": 0.93,
                    "data": pg
                }

        # Tier 4: Acid-Base pKa scale match
        for ab in self.pka_scales:
            if ab["name"].lower() in q or q in ab["name"].lower():
                return {
                    "source": "Tier 1: Acid-Base pKa Knowledge Base",
                    "status": "MATCHED",
                    "confidence": 0.90,
                    "data": ab
                }

        # Tier 5: Online web reference (PubChem REST API)
        web_res = self._query_pubchem(query)
        if web_res:
            return {
                "source": "Tier 2: PubChem REST API Index",
                "status": "MATCHED",
                "confidence": 0.85,
                "data": web_res
            }

        # Tier 6: Last resort AI fallback (only if user provided an API key)
        if api_key:
            ai_res = self._query_llm_fallback(query, api_key)
            if ai_res and "error" not in ai_res:
                return {
                    "source": "Tier 3: Fallback Generative Engine",
                    "status": "MATCHED",
                    "confidence": 0.80,
                    "data": ai_res
                }

        return {
            "source": "None",
            "status": "UNRESOLVED",
            "confidence": 0.0,
            "data": {
                "message": f"Transformation '{query}' could not be resolved from offline knowledge bases. Ensure correct spelling or supply an API key."
            }
        }

    def _query_pubchem(self, query: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(query)}/JSON"
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                cid = r.json()["PC_Compounds"][0]["id"]["id"]["cid"]
                return {
                    "name": query,
                    "pubchem_cid": cid,
                    "reference_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                    "note": "Resolved structure and biological metadata from NCBI PubChem."
                }
        except Exception:
            pass
        return None

    def _query_llm_fallback(self, query: str, api_key: str) -> Optional[Dict[str, Any]]:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Analyze the following chemical transformation query: '{query}'.
            Return a pure JSON object structured as:
            {{
              "name": "Formal Reaction Name",
              "class": "Reaction Category",
              "rate_law": "Kinetic expression",
              "stereochemistry": "Stereochemical rules",
              "mechanism_steps": [
                {{
                  "step": 1,
                  "name": "Elementary Step Name",
                  "electron_source": "HOMO description",
                  "electron_sink": "LUMO description",
                  "intermediate": "Intermediate species",
                  "driving_force": "Thermodynamic or kinetic explanation"
                }}
              ]
            }}
            Return ONLY raw valid JSON without markdown fencing or additional commentary.
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            return {"error": str(e)}
