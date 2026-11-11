from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path

out = Path(r'D:\projects\DBMS_PROJECT\exoplanet-habitability-catalog\exoplanet-habitability-catalog-copy\docs\project-changes-and-remaining-risks.docx')
out.parent.mkdir(parents=True, exist_ok=True)
doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(.7); sec.bottom_margin = Inches(.7); sec.left_margin = Inches(.78); sec.right_margin = Inches(.78)
styles = doc.styles
styles['Normal'].font.name = 'Aptos'; styles['Normal'].font.size = Pt(10); styles['Normal'].font.color.rgb = RGBColor(45,55,68)
styles['Normal'].paragraph_format.space_after = Pt(6)
for name, size, color in [('Title', 25, '18324A'), ('Heading 1', 16, '18324A'), ('Heading 2', 12, '176B73')]:
    s=styles[name]; s.font.name='Aptos Display'; s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor.from_string(color)
    s.paragraph_format.space_before=Pt(11); s.paragraph_format.space_after=Pt(5)

p=doc.add_paragraph(style='Title'); p.add_run('Project Changes and Remaining Risks')
p=doc.add_paragraph(); r=p.add_run('Exoplanet Habitability Catalog'); r.bold=True; r.font.size=Pt(13); r.font.color.rgb=RGBColor.from_string('176B73')
p=doc.add_paragraph('A plain-language record of what the current project copy has changed in response to the identified concerns, what those changes improve, and what still needs work.')
p.paragraph_format.space_after=Pt(12)

def shade(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)

def set_cell(cell, text, bold=False, color=None):
    cell.text=''; p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(2)
    run=p.add_run(text); run.bold=bold; run.font.size=Pt(9)
    if color: run.font.color.rgb=RGBColor.from_string(color)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

h=doc.add_heading('What changed at a glance', level=1)
p=doc.add_paragraph('The nested project copy contains a more organized backend, shared database helpers, a defined model input contract, and a bulk endpoint for identifying score drift. The NASA import and deployment safeguards remain incomplete. The workspace also still contains two project copies, so the team should confirm which copy is the maintained one before treating either as the single source of truth.')

t=doc.add_table(rows=1, cols=3); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Light Shading Accent 1'
for c,txt in zip(t.rows[0].cells,['Concern','Current change','Status']): set_cell(c,txt,True,'FFFFFF'); shade(c,'18324A')
rows=[
('Mixed route responsibilities','Routes, services, repositories, and predictor now have separate roles.','Improved'),
('Database connections and cursors','Shared pool/transaction helpers manage reuse, rollback, and cursor closing.','Improved'),
('Schema and model contract drift','Canonical names and model feature mapping are documented and centralized in the nested copy.','Improved; verify SQL set together'),
('Per-planet drift requests','A bulk drifted-planets endpoint supports a single catalog query; detail history loads when selected.','Improved'),
('Synchronous NASA import','Still fetches and inserts directly inside the HTTP request.','Open'),
('Security and validation','Input checks exist and debug defaults off, but CORS is unrestricted.','Partial'),
('Duplicate project copy','Both a top-level project and nested copy exist.','Open')]
for row in rows:
    cells=t.add_row().cells
    for c,txt in zip(cells,row): set_cell(c,txt)


doc.add_heading('Changes explained simply', level=1)

def section(title, paragraphs, evidence):
    doc.add_heading(title, level=2)
    for text in paragraphs: doc.add_paragraph(text)
    p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(.16); r=p.add_run('Where to see it: ' + evidence); r.italic=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string('526579')

section('1. Backend code has clearer jobs',[
'Before, a route could receive a web request, validate its fields, run the model, write SQL, and format the response in one place. The current copy divides those jobs: route files handle HTTP, services validate and coordinate work, repositories contain SQL, and the predictor loads and calls the model.',
'This makes it easier for a student to find the code responsible for a bug. For example, input rules belong in services.py, while a database query belongs in repositories.py. The route still coordinates the request, so the separation is a practical improvement rather than a fully independent enterprise architecture.'
],'backend/routes/, backend/services.py, backend/repositories.py, backend/predictor.py')

section('2. Database connections have shared management',[
'The shared db.py module obtains connections from a configurable MySQL connection pool. Its transaction helper commits if work succeeds and rolls back if it fails. Query helpers also close cursors in finally blocks, including the stored-procedure helper, and return connections to the pool when finished.',
'This reduces repeated connection setup and makes cleanup behavior consistent. It does not by itself guarantee that every multi-step business operation is one transaction: current helper calls can each open their own transaction.'
],'backend/db.py and DB_POOL_SIZE in the project setup documentation')

section('3. Database and model field names are documented',[
'The current schema and application use exoplanets.name, while planet_name is not the database column. Prediction history uses predicted_habitability and prediction_timestamp. The model feature contract defines a fixed input order and translates API names such as radius and stellar_flux into the training names expected by the model.',
'Stellar flux is passed to P_FLUX. Orbital distance is kept as its own value and is not used as a replacement. The saved model pipeline performs its own median imputation, so prediction uses the same saved preprocessing pipeline instead of filling missing features with unrelated API defaults.',
'The nested copy documents a recommended SQL setup order and includes schema, log trigger, and procedure files that agree on the log field names. Keep that file set together when creating or upgrading a database; do not mix it with the older top-level schema plan without checking names.'
],'docs/architecture-and-data-contract.md, model/feature_contract.py, model/train_model.py, database/schema.sql, database/habitability_log.sql, database/procedures.sql')

section('4. Drift checks can be requested in bulk',[
'The API has a /api/exoplanets/drifted endpoint that returns the planets whose adjacent recorded scores changed by more than a requested threshold. The scientist dashboard can fetch this list once and then mark the matching catalog rows. It requests the detailed score timeline for a planet when that planet is selected.',
'This changes the expensive catalog-wide pattern from one drift request for every planet to one bulk drift request plus detail requests as needed. The score history itself is still per planet when opened.'
],'backend/routes/exoplanets.py, backend/repositories.py, frontend/js/scientist.js')

section('5. Input checking and app startup are partly improved',[
'Service functions check that names are present, numeric inputs are finite numbers, year-like values are whole numbers, and boolean flags are 0, 1, or empty. Routes return clear client errors for invalid input and missing records, and model-unavailable errors receive a service-unavailable response.',
'The Flask app enables debug mode only when FLASK_DEBUG is set to 1, so debug is off by default. However, CORS(app) still allows broad cross-origin access. Before deployment, restrict allowed origins, set production configuration deliberately, and review errors and request limits.'
],'backend/services.py, backend/routes/, backend/app.py')

section('6. NASA import and duplicate copies still need decisions',[
'The NASA route currently makes a synchronous request with a 10-second timeout, processes a small top-five query, checks for duplicate planet names, and inserts records one at a time. It does not create or associate host stars, calculate every derived field, or run as a background job. A future version could fetch into a staging area, validate and link records, then import them in a controlled batch.',
'The repository root also contains an older project alongside the nested project copy. The nested copy has the more complete backend and documentation, but the folder structure alone does not prove which copy the team intends to maintain. Agree on one authoritative project location and move or archive the other only after that decision.'
],'backend/routes/fetch.py, backend/repositories.py; compare the repository root with exoplanet-habitability-catalog-copy/')

doc.add_heading('Suggested next steps', level=1)
for item in [
'Confirm which project copy is authoritative, then keep setup instructions and future code changes in that copy.',
'Run a database setup against the documented schema, log, and procedure files as one matched set; record the database version used by the running app.',
'Limit CORS to the actual frontend address and add production deployment settings before exposing the API beyond a local machine.',
'Plan an asynchronous or staged NASA import that links host stars, validates records, computes required derived values, and reports partial failures.',
'Consider making a single service-level transaction for workflows that write multiple related records, and add tests when the team is ready to verify these behaviors.'
]: doc.add_paragraph(item, style='List Number')

# Footer with document label and page number field
for sec in doc.sections:
    footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    run=footer.add_run('Exoplanet Habitability Catalog  |  Project notes'); run.font.size=Pt(8); run.font.color.rgb=RGBColor.from_string('718096')

doc.save(out)
print(out)
