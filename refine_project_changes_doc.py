from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
p=r'D:\projects\DBMS_PROJECT\exoplanet-habitability-catalog\exoplanet-habitability-catalog-copy\docs\project-changes-and-remaining-risks.docx'
d=Document(p)
style=d.styles['Title']._element
pPr=style.find(qn('w:pPr'))
if pPr is not None:
    bdr=pPr.find(qn('w:pBdr'))
    if bdr is not None: pPr.remove(bdr)
for para in d.paragraphs:
    if para.style.name=='Title':
        pPr=para._p.get_or_add_pPr(); bdr=pPr.find(qn('w:pBdr'))
        if bdr is not None: pPr.remove(bdr)
# Explain the labels used in the status summary.
d.add_heading('How to read the status labels', level=1)
for label, expl in [('Improved','The current copy includes a concrete code or documentation change that addresses the concern.'),('Partial','Some safeguards are present, but an important gap remains.'),('Open','The concern remains in the current implementation and needs a future change or team decision.')]:
    para=d.add_paragraph(); run=para.add_run(label + ': '); run.bold=True; run.font.color.rgb=__import__('docx').shared.RGBColor.from_string('176B73'); para.add_run(expl)
d.save(p)
