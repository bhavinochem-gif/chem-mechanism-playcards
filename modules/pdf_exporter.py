import os
from weasyprint import HTML
from modules.chem_renderer import smarts_reaction_to_svg, svg_to_b64

def generate_mechanism_dossier_pdf(target_name: str, resolution_source: str, data: dict, output_path: str):
    rxn_svg_tag = ""
    if "smarts" in data:
        svg_code = smarts_reaction_to_svg(data["smarts"])
        if svg_code:
            b64 = svg_to_b64(svg_code)
            rxn_svg_tag = f'<div style="text-align:center; margin:10px 0;"><img src="data:image/svg+xml;base64,{b64}" style="max-width:100%; height:auto;" /></div>'

    steps_html = ""
    if "mechanism_steps" in data:
        for s in data["mechanism_steps"]:
            steps_html += f"""
            <tr>
              <td style="font-weight:bold; width:20%;">Step {s.get('step', 1)}: {s.get('name', 'Step')}</td>
              <td style="width:30%;"><strong>Intermediate:</strong><br>{s.get('intermediate', 'N/A')}</td>
              <td style="width:50%;">
                <strong>Flow:</strong> {s.get('electron_source', 'N/A')} &rarr; {s.get('electron_sink', 'N/A')}<br>
                <span style="color:#2563eb; font-size:7.5pt;">&bull; Driving Force: {s.get('driving_force', 'N/A')}</span>
              </td>
            </tr>
            """

    html = f"""<!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{target_name} Mechanism Dossier</title>
      <style>
        @page {{ size: A4; margin: 15mm 12mm; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 8.8pt; color: #1e293b; line-height: 1.45; }}
        .banner {{ background: #0f172a; color: white; padding: 14px 18px; border-radius: 6px; margin-bottom: 12px; }}
        .card {{ border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; margin-bottom: 12px; page-break-inside: avoid; }}
        .badge {{ background: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 7.5pt; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 8pt; }}
        th {{ background: #1e293b; color: white; padding: 5px; text-align: left; }}
        td {{ padding: 5px; border: 1px solid #cbd5e1; vertical-align: top; }}
        .meta-table td {{ border: 1px solid #e2e8f0; padding: 4px; }}
      </style>
    </head>
    <body>
      <div class="banner">
        <h2 style="margin:0; font-size:14pt;">Chemical Mechanism Dossier: {target_name}</h2>
        <p style="margin:4px 0 0; color:#94a3b8; font-size:8pt;">Resolved via: <span class="badge">{resolution_source}</span></p>
      </div>

      <div class="card">
        <div style="display:flex; justify-content:space-between;">
          <strong style="font-size:10pt;">{data.get('name', target_name)}</strong>
          <span class="badge">{data.get('class', 'Organic Transformation')}</span>
        </div>
        
        {rxn_svg_tag}

        <table class="meta-table">
          <tr><td style="width:25%;"><strong>Rate Law:</strong></td><td><code>{data.get('rate_law', 'Not Specified')}</code></td></tr>
          <tr><td><strong>Stereochemistry:</strong></td><td>{data.get('stereochemistry', 'Not Specified')}</td></tr>
          <tr><td><strong>Solvents:</strong></td><td>{', '.join(data.get('solvents', ['N/A'])) if isinstance(data.get('solvents'), list) else data.get('solvents', 'N/A')}</td></tr>
          <tr><td><strong>Kinetics / Notes:</strong></td><td>{data.get('kinetics', data.get('driving_force', 'Deterministic Reference'))}</td></tr>
        </table>

        <h4 style="margin:8px 0 4px; font-size:8.5pt;">Elementary Step Mechanism & Electron Pushing:</h4>
        <table>
          <thead>
            <tr><th>Step</th><th>Intermediate</th><th>Electron Flow & Driving Force</th></tr>
          </thead>
          <tbody>
            {steps_html if steps_html else '<tr><td colspan="3">Detailed step breakdown available in master database.</td></tr>'}
          </tbody>
        </table>
      </div>
    </body>
    </html>"""

    HTML(string=html).write_pdf(output_path)
