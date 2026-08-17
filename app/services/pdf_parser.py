import io
import re
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
            
        return _normalize_pdf_text(full_text)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"PDF ayrıştırılırken bir hata oluştu: {str(e)}"
        )


def _normalize_pdf_text(text: str) -> str:
    """
    pypdf kütüphanesinin bazı PDF tasarımlarında (Canva, Word vb.)
    harfler arasına attığı boşlukları (örn: 'P y t h o n') düzeltir.
    """
    lines = text.splitlines()
    normalized_lines = []
    for line in lines:
        if not line.strip():
            normalized_lines.append("")
            continue
        # Kelimeleri 2 veya daha fazla boşluğa göre ayır (kelime sınırlarını koru)
        tokens = re.split(r"\s{2,}", line.strip())
        new_tokens = []
        for token in tokens:
            chars = token.split(" ")
            # Eğer token'daki tüm elemanlar tek harf ise ('P', 'y', 't', 'h', 'o', 'n') birleştir
            if len(chars) > 1 and all(len(c) == 1 for c in chars):
                new_tokens.append("".join(chars))
            else:
                new_tokens.append(token)
        normalized_lines.append(" ".join(new_tokens))
    return "\n".join(normalized_lines)
