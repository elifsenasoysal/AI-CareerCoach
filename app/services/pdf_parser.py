import io
# pyrefly: ignore [missing-import]
from pypdf import PdfReader
from fastapi import HTTPException

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    PDF ikili verisinden pypdf kullanarak metin içeriğini çıkarır.
    """
    try:
        # Baytları dosya benzeri bir akışa sar
        pdf_stream = io.BytesIO(pdf_bytes)
        
        # PdfReader'ı başlat
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
                detail="PDF dosyasından metin çıkarılamadı. Lütfen taranmış resim PDF'si olmadığından emin olun."
            )
            
        return full_text
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"PDF ayrıştırılırken bir hata oluştu: {str(e)}"
        )
