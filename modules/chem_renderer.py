from rdkit import Chem
from rdkit.Chem import rdChemReactions
from rdkit.Chem.Draw import rdMolDraw2D
import base64

def smiles_to_svg(smiles: str, width: int = 240, height: int = 120) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return ""
    d2d = rdMolDraw2D.MolDraw2DSVG(width, height)
    dopts = d2d.drawOptions()
    dopts.clearBackground = True
    dopts.bondLineWidth = 1.8
    dopts.padding = 0.08
    d2d.DrawMolecule(mol)
    d2d.FinishDrawing()
    return d2d.GetDrawingText()

def smarts_reaction_to_svg(smarts: str, width: int = 540, height: int = 120) -> str:
    try:
        rxn = rdChemReactions.ReactionFromSmarts(smarts, useSmiles=True)
        if not rxn:
            return ""
        d2d = rdMolDraw2D.MolDraw2DSVG(width, height)
        dopts = d2d.drawOptions()
        dopts.clearBackground = True
        dopts.bondLineWidth = 1.8
        dopts.padding = 0.08
        d2d.DrawReaction(rxn)
        d2d.FinishDrawing()
        return d2d.GetDrawingText()
    except Exception:
        return ""

def svg_to_b64(svg_str: str) -> str:
    if not svg_str:
        return ""
    return base64.b64encode(svg_str.encode("utf-8")).decode("utf-8")
