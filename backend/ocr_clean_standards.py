import os
import json
import time
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Define paths to input PDFs
pdf_paths = {
    "IS_694_2010": "/Users/vidhibhateja/.gemini/antigravity/brain/18149211-abb0-424b-9ad5-09dab74529c5/.user_uploaded/media__1784887825950.pdf",
    "IS_8130_1984": "/Users/vidhibhateja/.gemini/antigravity/brain/18149211-abb0-424b-9ad5-09dab74529c5/.user_uploaded/media__1784887825997.pdf",
    "IS_5831_1984": "/Users/vidhibhateja/.gemini/antigravity/brain/18149211-abb0-424b-9ad5-09dab74529c5/.user_uploaded/media__1784887847862.pdf"
}

output_dir = "/Users/vidhibhateja/Desktop/BIS_project"

# Set up pipeline options to force full page OCR (highly recommended for scanned/corrupted standards)
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

for name, path in pdf_paths.items():
    print(f"Starting conversion for {name} ({path})...")
    start_time = time.time()
    try:
        result = converter.convert(path)
        
        # Paths for output files
        json_path = os.path.join(output_dir, f"{name}.json")
        md_path = os.path.join(output_dir, f"{name}.md")
        
        # Save as JSON and Markdown
        print(f"Saving JSON for {name} to {json_path}...")
        result.document.save_as_json(json_path)
        
        print(f"Saving Markdown for {name} to {md_path}...")
        result.document.save_as_markdown(md_path)
        
        elapsed = time.time() - start_time
        print(f"Successfully processed {name} in {elapsed:.2f} seconds.\n")
    except Exception as e:
        print(f"Error converting {name}: {e}\n")

print("All conversions complete!")
