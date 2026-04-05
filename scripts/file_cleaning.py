import os
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader


def read_pdf(file_path):

    loader = PyPDFLoader(str(file_path))

    data = loader.load()

    text = "\n".join([doc.page_content for doc in data])

    return text


def read_docx(file_path):

    loader = Docx2txtLoader(str(file_path))

    data = loader.load()

    text = "\n".join([doc.page_content for doc in data])

    return text


def clean_text(text):

    if not text:
        return ""

    # remove non-ascii characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # fix spaced letters like "h t t p s"
    text = re.sub(r'(?<=\b\w)\s(?=\w\b)', '', text)

    # fix broken words like "Pr oduct"
    text = re.sub(r'(?<=\w)\s(?=\w)', '', text)

    # restore URLs
    text = re.sub(r'h\s*t\s*t\s*p\s*s?\s*:\s*/\s*/', 'https://', text)

    # normalize emails
    text = re.sub(r'\s*@\s*', '@', text)
    text = re.sub(r'\s*\.\s*', '.', text)

    # normalize phone numbers
    text = re.sub(r'\s*-\s*', '-', text)

    # remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    # remove duplicate punctuation
    text = re.sub(r'([.,])\1+', r'\1', text)

    return text.strip()


def process_resume(file_path):

    ext = os.path.splitext(file_path)[1].lower()

    text = ""

    if ext == ".pdf":
        text = read_pdf(file_path)

    elif ext == ".docx":
        text = read_docx(file_path)

    else:
        print("Unsupported file type:", file_path)
        return None

    cleaned_text = clean_text(text)

    result = {
        "file": os.path.basename(file_path),
        "text": cleaned_text
    }

    return result