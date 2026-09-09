# ChemMechAI: Chemical Reaction Mechanism Play Card Engine

An automated synthesis pathway ingestion, deterministic mechanism deduction, and PDF Play Card generation platform built with Streamlit, RDKit, and WeasyPrint.

## System Capabilities
* **PDF Literature Ingestion:** Automatically extracts synthetic text and identifies named reactions.
* **Deterministic Knowledge Graph:** Resolves elementary electron-pushing mechanisms, transition states, and driving forces offline.
* **Vector Chemical Rendering:** Generates 2D molecular SVGs using RDKit.
* **Publication Dossier Generator:** Compiles standardized A4 Mechanism Dossiers with WeasyPrint.

## Local Installation

1. **System Dependencies (Linux/Debian):**
```bash
sudo apt-get update && sudo apt-get install -y \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev shared-mime-info fonts-dejavu-core
