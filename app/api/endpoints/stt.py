import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.stt_service import STTService

router = APIRouter()
stt_service = STTService(model_name="base") # Using 'base' model by default

@router.post("/transcribe", summary="Transcribe Audio to Text", description="Converts an uploaded audio file to text using Whisper, preserving filler words.")
async def transcribe_audio(audio: UploadFile = File(...)):
    # Basic validation
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Create a temporary file to save the uploaded audio
    # Whisper needs a file path
    temp_file_path = f"temp_{audio.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        # Transcribe the audio
        transcribed_text = stt_service.transcribe(temp_file_path)
        
        return JSONResponse(content={"text": transcribed_text})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
