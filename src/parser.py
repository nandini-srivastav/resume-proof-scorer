"""
Resume parsing: extract raw text and structure from an uploaded resume file.

TODO (yours to implement):
- extract_text(): pull raw text out of a PDF or DOCX file
- segment_sections(): split raw text into skills / experience / projects / education
- extract_github_link(): regex out a GitHub profile URL if present

This is boilerplate scaffolding only — the actual parsing logic,
including how you handle messy layouts (see Edge Cases in DESIGN.md),
is on you.
"""

from docx.opc.exceptions import PackageNotFoundError
from docx import Document
from rapidfuzz import fuzz
import zipfile
import pdfplumber 

MINIMUM_TEXT_LENGTH = 250 # minimum text threshold of a resume

# expanded as tested against real resume     
CANONICAL_SECTIONS = {
    "skills": ["skills", "technical skills", "core competencies"],
    "experience": ["experience", "work experience", "professional experience", "employment history"],
    "projects": ["projects", "personal projects", "academic projects"],
    "education": ["education", "academic beckground"],
    "certifications": ["certifications", "certificates", "licenses"]
}

# ----------------------------- EXTRACT TEXT FROM RESUME -------------------------------
def extract_text(file_object: BinaryIO, file_name: str) -> str:
    """
    Extract plain text from a resume file.

    Supports PDF and DOCX formats. Detects the file type from the
    filename extension and routes to the appropriate extraction
    library. Files that are password-protected, corrupted, an
    unsupported format, or contain no extractable text (e.g., a
    scanned image PDF) are rejected with a clear error rather than
    returning empty or partial text silently.

    Args:
        file_object (BinaryIO): Binary file-like object containing the resume
            (e.g., an opened file or a Streamlit UploadedFile).
        file_name (str): Original filename, used to determine whether the
            file is a PDF or DOCX.

    Returns:
        str: The extracted text content of the resume as a single string.
        
    Raises:
        ValueError: If the file extension is not .pdf or .docx.
        IOError: If the file cannot be opened (corrupted or
            password-protected).
        ValueError: If no readable text is found (e.g., scanned PDF).
    """
    # ------------ Step 1: Determine file type via header byte ------------
    header_bytes = file_object.read(8) # read and return first 
    file_object.seek(0) # rewind before anything else touches the stream 
    
    # a. if document is a PDF 
    if header_bytes.startswith(b"%PDF"):
        file_type = "pdf"
    # b. if document is a zip file
    elif header_bytes.startswith(b"PK"):
        # open the zip file 
        # if DOCX
        if is_valid_docx(file_object):
            file_type = "docx"
        # file is a zip but not a docx partcularly
        else:
            raise ValueError(f"File is a zip archive but not a valid DOCX: {file_name}")
            
    # if it's a JPG, PNEG, scanned PDF/image or any other format 
    else:
        raise ValueError(f"Unrecognized file type: {file_name}, please enter a PDF or DOCX file only.")
        
    # ------------ Step 2: Extract text, catching corrupted/password-protected files ------------
    try:
        # a. resume is PDF format
        if file_type == "pdf":
            text = extract_text_from_pdf(file_object)
        # b. resume is DOCX format
        else:
            text = extract_text_from_docx(file_object)
    
    # password-protected/corrupted file error 
    except PackageNotFoundError as e:
        raise ValueError(f"File could not be opened (corrupted or invalid): {filename}") from e
    # deals with anything else that goes wrong  - whatever weird error pdfplumber throws
    except Exception as e:
        raise ValueError(f"File could not be opened: {filename}") from e
    
    # ------------ Step 3: Reject scanned/image PDFs (no real text layer) ------------
    # Case: file looks like resume visually but there is no actual layer of text - no real characters that a computer can read
    if len(text.strip()) < MINIMUM_TEXT_LENGTH:
        raise ValueError(f"No readable text found - possible a scanned PDF: {file_name}")
    
    # ------------ Step 4: Success ------------
    return text

def is_valid_docx(file_object: BinaryIO) -> bool:
    """Once the document has been validated as a zip archive format we go a layer deeper to check the if it's the DOCX format
    We open the zip file, list the file names in it and check if it particularly follows "word/document.xml" format or not to qualify as a DOCX.

    Args:
        file_object (BinaryIO): Binary file-like object containing the resume
            (e.g., an opened file or a Streamlit UploadedFile).

    Returns:
        bool: if DOCX - True, else - False 
    """
    try:
        # Step 1: Open file as zip file
        with zipfile.ZipFile(file_object) as zf:
        # Step 2: list file names inside zip file
        entry_names = zf.namelist()
        # Step 3: check if the file name has "word/document.xml" in it
        # result = True/False
        result = "word/document.xml" in entry_names
    
    # if file doesnt open this exception is raised
    except zipfile.BadZipFile:
        result = False
        
    file_object.seek(0) # rewind to 0 - Zipfile consmed the stream
    
    return result

def extract_text_from_pdf(file_object: BinaryIO) -> str:
    """
    Extract and combine text from every page of a PDF file.

    Opens the PDF with pdfplumber and pulls text from each page in
    order. Pages with no extractable text (e.g., a blank or
    image-only page within an otherwise valid PDF) contribute an
    empty string rather than causing a failure.
    
    Args:
        file_object (BinaryIO): Binary file-like object containing the PDF.

    Returns:
        str: The combined text of all pages, joined with newlines.
    """
    pages_text = []
    # Step 1 : open file with pdfplumber
    with pdfplumber.open(file_object) as pdf:
        # Step 2 : loop over every page
        for page in pdf.pages:
            pages_text = page.extract_text() or ""
            # Step 3 : join pages together
            pages_text.append(pages_text)
    combines_text = "\n".join(pages_text) # every new page will begin with a new-line     
    # Step 4 : return combined text
    combines_text
    
def extract_text_from_docx(file_object: BinaryIO) -> str:
    """
    Extract and combine text from every paragraph of a DOCX file.

    Opens the file with python-docx and pulls the text of each
    paragraph in order.

    Args:
        file_object: Binary file-like object containing the DOCX.

    Returns:
        The combined text of all paragraphs, joined with newlines.
    """
    # Step 1 : open file with python-docx as a Document
    document = Document(file_object)
    # Step 2 : loop over document.paragraph, collect .text from each
    paragraph_text = [paragraph.text for paragraph in document.paragraphs]
    # Step 3 : join paragraphs with new lines 
    combined_text = "\n".join(paragraph_text)
    # Step 4 : return combined text
    return combined_text

# ------------------------ DIVIDE RAW TEXT INTO SECTIONS ---------------------------------
def segment_sections(raw_text: str) -> dict:
    # Step 1 : Every key starts as an empty list
    sections = {name: [] for name in CANONICAL_SECTIONS}
    current_section = None
    # Step 2 : Split raw text into individual lines 
    lines = raw_text.splitlines() 
    # Step 3 : strip white spaces 
    for line in lines:
        cleaned_lines = line.strip()
        # a. skip the blank lines
        if not cleaned_lines:
            continue
        # b.  if this line is a heading - save as current seection, skip to next line
        #     else - already inside a section
        matched_section = is_heading(cleaned_lines)
        
        if matched_section is not None:
            current_section = matched_section
            continue
        
        if current_section is not None:
            sections[current_section].append(cleaned_lines)
        
    # Step 4 : return filled-up dictionary    
    return sections
        
def is_heading(line: str) -> str | None:
    """_Check whether a line of resume text is a section heading.

    Rejects lines longer than a few words (real headings are short),
    then fuzzy-matches the line against known heading synonyms for
    each canonical section.

    Args:
        line: A single line of resume text.

    Returns:
        The canonical section name if the line matches a known
        heading, otherwise None.
    """
    # If the line has more than 4 words it is not a heading(probably)
    if len(line.split()) > 4:
        return None
    # else - compare the line against every known heading name/synonym 
    for canonical_name, synonym_list in CANONICAL_SECTIONS.items():
        for synonym in synonym_list:
            # if similarity >= 80, return matched section
            similarity = fuzz.ratio(line.lower(), synonym)
            if similarity >= 80:
                return canonical_name
    # else - return nothing        
    return None
    
    

def extract_github_link(raw_text: str) -> str | None:
    raise NotImplementedError
