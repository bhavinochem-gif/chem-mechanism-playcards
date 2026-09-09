from pypdf import PdfReader
from typing import List, Dict, Any

def extract_pdf_text(uploaded_file, max_pages: int = 5) -> str:
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for i, page in enumerate(reader.pages[:max_pages]):
            content = page.extract_text()
            if content:
                text += f"\n--- Page {i+1} ---\n" + content
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def detect_candidate_reactions(extracted_text: str, named_reactions: List[Dict[str, Any]]) -> List[str]:
    text_lower = extracted_text.lower()
    candidates = []
    for rxn in named_reactions:
        name = rxn["name"]
        if name.lower() in text_lower:
            candidates.append(name)
            continue
        for alias in rxn.get("aliases", []):
            if alias.lower() in text_lower:
                candidates.append(name)
                break
    return list(dict.fromkeys(candidates))
