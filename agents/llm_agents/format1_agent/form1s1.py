import os
import logging
import fitz  # PyMuPDF
from PIL import Image
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class Form1S1Agent:
    """
    Form1S1 Agent - Page Extraction
    Extracts first page from PDF and converts to image
    """

    def __init__(self):
        self.name = "form1s1"
        self.short_name = "form1s1"
        self.output_dir = "io/fullorder_output"
        logger.info(f"[{self.short_name.upper()}] Agent initialized - Format 1 Step 1 processor")

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def process_order(self, file_path):
        """
        Process an order file - extract first page and convert to image

        Args:
            file_path (str): Path to the input PDF file

        Returns:
            dict: Processing results including output file path
        """
        try:
            logger.info(f"[{self.short_name.upper()}] Starting processing for: {file_path}")

            # Get file info
            file_name = os.path.basename(file_path)
            order_name = os.path.splitext(file_name)[0]

            result = {
                "status": "processing",
                "input_file": file_path,
                "order_name": order_name,
                "agent": self.name,
                "short_name": self.short_name
            }

            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"[{self.short_name.upper()}] File not found: {file_path}")
                result["status"] = "error"
                result["error"] = f"File not found: {file_path}"
                return result

            # Check if it's a PDF
            if not file_path.lower().endswith('.pdf'):
                logger.warning(f"[{self.short_name.upper()}] Not a PDF file, copying as is: {file_path}")
                # If it's already an image, just copy it
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    output_path = os.path.join(self.output_dir, f"{order_name}_page1.png")
                    img = Image.open(file_path)
                    img.save(output_path, 'PNG')
                    result["status"] = "success"
                    result["output_file"] = output_path
                    result["message"] = "Image file copied successfully"
                    logger.info(f"[{self.short_name.upper()}] Image saved to: {output_path}")
                    return result
                else:
                    result["status"] = "error"
                    result["error"] = "File is not a PDF or supported image format"
                    return result

            # Convert PDF to image (first page only)
            logger.info(f"[{self.short_name.upper()}] Converting PDF first page to image...")

            try:
                # Open PDF with PyMuPDF
                pdf_document = fitz.open(file_path)

                if len(pdf_document) == 0:
                    logger.error(f"[{self.short_name.upper()}] No pages found in PDF")
                    result["status"] = "error"
                    result["error"] = "No pages found in PDF"
                    pdf_document.close()
                    return result

                # Get first page
                first_page = pdf_document[0]

                # Convert to image at 300 DPI
                mat = fitz.Matrix(300/72, 300/72)  # 300 DPI scaling
                pix = first_page.get_pixmap(matrix=mat)

                # Convert to PIL Image
                import io
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # Save the image
                output_filename = f"{order_name}_page1.png"
                output_path = os.path.join(self.output_dir, output_filename)
                img.save(output_path, 'PNG')

                # Close PDF document
                pdf_document.close()

                logger.info(f"[{self.short_name.upper()}] First page saved to: {output_path}")

                # Get image dimensions
                width, height = img.size

                result["status"] = "success"
                result["output_file"] = output_path
                result["output_filename"] = output_filename
                result["image_width"] = width
                result["image_height"] = height
                result["dpi"] = 300
                result["page_number"] = 1
                result["message"] = f"Successfully extracted page 1 from {file_name}"

                # Save result to JSON
                json_output_path = os.path.join(self.output_dir, f"{order_name}_{self.short_name}_result.json")
                with open(json_output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"[{self.short_name.upper()}] Results saved to: {json_output_path}")

            except Exception as e:
                logger.error(f"[{self.short_name.upper()}] Error converting PDF: {str(e)}")
                result["status"] = "error"
                result["error"] = f"PDF conversion error: {str(e)}"
                return result

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Unexpected error: {str(e)}")
            result["status"] = "error"
            result["error"] = f"Unexpected error: {str(e)}"
            return result

        return result

    def process_batch(self, input_dir="io/input"):
        """
        Process all PDF files in the input directory

        Args:
            input_dir (str): Directory containing input files

        Returns:
            list: Results for all processed files
        """
        logger.info(f"[{self.short_name.upper()}] Starting batch processing from: {input_dir}")

        results = []

        # Get all PDF files
        pdf_files = []
        if os.path.exists(input_dir):
            for file in os.listdir(input_dir):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(input_dir, file))

        if not pdf_files:
            logger.warning(f"[{self.short_name.upper()}] No PDF files found in {input_dir}")
            return results

        logger.info(f"[{self.short_name.upper()}] Found {len(pdf_files)} PDF file(s)")

        for pdf_file in pdf_files:
            logger.info(f"[{self.short_name.upper()}] Processing: {pdf_file}")
            result = self.process_order(pdf_file)
            results.append(result)

            if result["status"] == "success":
                logger.info(f"[{self.short_name.upper()}] Successfully processed: {os.path.basename(pdf_file)}")
            else:
                logger.error(f"[{self.short_name.upper()}] Failed to process: {os.path.basename(pdf_file)}")

        logger.info(f"[{self.short_name.upper()}] Batch processing complete. Processed {len(results)} file(s)")
        return results