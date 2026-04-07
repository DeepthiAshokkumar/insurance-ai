import io
import os
import json
import logging
import asyncio
from typing import Dict, Any
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
from .schemas import ClaimResult
from dotenv import load_dotenv

from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

def extract_text_from_file(file_content: bytes, mime_type: str) -> str:
    extracted_text = ""
    # Check if the document is a PDF
    if "pdf" in mime_type.lower():
        # Handle PDF using PyMuPDF
        pdf_document = fitz.open(stream=file_content, filetype="pdf")
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text = page.get_text()
            if text.strip(): # text-based PDF
                extracted_text += text + "\n"
            else:
                # If no text found, maybe it's a scanned PDF, convert to image and OCR
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                extracted_text += pytesseract.image_to_string(img) + "\n"
        pdf_document.close()
    else:
        # Handle images (png, jpeg, etc.) using Pytesseract
        image = Image.open(io.BytesIO(file_content))
        # Ensure image is in RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        extracted_text = pytesseract.image_to_string(image)
        
    return extracted_text

async def process_claim_document(file_content: bytes, mime_type: str) -> ClaimResult:
    try:
        # The genai.Client() automatically picks up GEMINI_API_KEY from environment variables
        if not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your terminal before running.")
            
        client = genai.Client()
        loop = asyncio.get_running_loop()
        
        # 1. OPTICAL CHARACTER RECOGNITION (OCR)
        try:
            extracted_text = await loop.run_in_executor(None, extract_text_from_file, file_content, mime_type)
        except Exception as e:
            logger.warning(f"Traditional OCR failed (Tesseract may be missing). Continuing with Vision-only. Error: {e}")
            extracted_text = "OCR Engine Offline."
        
        # 2. GENERATIVE AI (Vision + Text Hybrid)
        prompt = f"""
        You are an AI document verification bot for a motor insurance claim system.
        We are doing hybrid processing. Below is the raw OCR text extracted via Tesseract/PyMuPDF:
        
        [OCR OUTPUT START]
        {extracted_text}
        [OCR OUTPUT END]
        
        Using BOTH the provided image/pdf and this OCR text, output ONLY a valid JSON object with the following structure:
        {{
          "status": "Either 'approved' or 'rejected'. Reject if it's not relevant, or if it is missing any critical fields.",
          "extracted_details": {{
             "Policy Number": "Extracted policy number. Leave blank if missing or blocked out.",
             "Claim Number": "Extracted claim number. Leave blank if missing.",
             "Vehicle Number": "Extracted vehicle registration number. Leave blank if missing.",
             "Date of accident": "Extracted date and time. Leave blank if missing.",
             "Place of accident": "Extracted place. Leave blank if missing.",
             "Name": "Name of the insured person or company",
             "Address": "Full address, including city and pin code",
             "Mobile": "Mobile or landline phone number",
             "Email ID": "Email address if present",
             "Driving License No": "Driving license number from the driver details section"
          }},
          "missing_fields": ["List of critical fields that are missing or illegible (e.g., 'Policy Number', 'Date of accident', 'Place of accident'). Empty list if nothing is missing."]
        }}
        IMPORTANT RULE: Motor Insurance Claim Form documents MUST have a "Policy Number", "Date of accident", and "Place of accident". If any of these are missing, crossed out, or illegible, you MUST set status to "rejected" and include those field names in the "missing_fields" list.
        Do not wrap the output in markdown blocks, just return strictly the raw JSON.
        """
        
        # Use the new async client interface and Part.from_bytes class
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                prompt,
                types.Part.from_bytes(data=file_content, mime_type=mime_type)
            ]
        )
        
        try:
            resp_text = response.text.strip()
            if resp_text.startswith("```json"):
                resp_text = resp_text[7:]
            elif resp_text.startswith("```"):
                resp_text = resp_text[3:]
            if resp_text.endswith("```"):
                resp_text = resp_text[:-3]
                
            result_dict = json.loads(resp_text.strip())
            
            return ClaimResult(
                status=result_dict.get("status", "rejected"),
                extracted_details=result_dict.get("extracted_details"),
                missing_fields=result_dict.get("missing_fields", [])
            )
        except Exception as e:
            logger.error(f"Failed to parse Gemini JSON: {response.text if hasattr(response, 'text') else 'No Text'}")
            return ClaimResult(
                status="rejected",
            )

    except ValueError as ve:
        return ClaimResult(
            status="rejected"
        )
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return ClaimResult(
            status="rejected"
        )
