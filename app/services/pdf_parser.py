import io
# pyrefly: ignore [missing-import]
from pypdf import PdfReader
from fastapi import HTTPException

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts text content from PDF binary data using pypdf.
    """
    try:
        # Wrap bytes in a file-like stream
        pdf_stream = io.BytesIO(pdf_bytes)
        
        # Initialize PdfReader
        reader = PdfReader(pdf_stream)
        
        extracted_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_text.append(text)
                
        # Combine pages with a newline
        full_text = "\n".join(extracted_text).strip()
        
        if not full_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract any text from the PDF file. Please ensure it is not a scanned image PDF."
            )
            
        return full_text
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while parsing the PDF: {str(e)}"
        )
