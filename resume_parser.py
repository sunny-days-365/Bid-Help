"""
resume_parser.py
Reads resume from .docx or .txt, plus free-text situation and hope inputs.
Returns a unified profile dict for the job matcher.
"""

import os
from pathlib import Path


def read_docx(path: str) -> str:
    """Extract plain text from a .docx file."""
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def read_txt(path: str) -> str:
    """Read plain-text resume."""
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_resume(file_path: str) -> str:
    """Parse resume from docx or txt. Returns raw text."""
    ext = Path(file_path).suffix.lower()
    if ext == ".docx":
        return read_docx(file_path)
    elif ext in (".txt", ".md"):
        return read_txt(file_path)
    else:
        raise ValueError(f"Unsupported resume format: {ext}. Use .docx or .txt")


def build_profile(resume_path: str, situation: str, hope: str) -> dict:
    """
    Build a profile dict from resume + free text inputs.

    Args:
        resume_path: Path to resume file (.docx / .txt)
        situation:   Current situation description (e.g. "5 years backend engineer, currently unemployed")
        hope:        Job hope description (e.g. "remote Python job, 700万円+, Tokyo or remote")

    Returns:
        dict with keys: resume_text, situation, hope
    """
    resume_text = parse_resume(resume_path)
    return {
        "resume_text": resume_text,
        "situation": situation.strip(),
        "hope": hope.strip(),
    }
