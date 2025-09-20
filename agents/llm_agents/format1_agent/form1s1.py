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
    Extracts ALL pages from PDF and converts them to images
    Saves all pages to order_to_image folder
    Also saves first page to main output folder for backward compatibility
    """

    def __init__(self):
        self.name = "form1s1"
        self.short_name = "form1s1"
        self.output_dir = "io/fullorder_output"
        self.order_to_image_dir = "io/fullorder_output/order_to_image"
        self.original_order_dir = "io/fullorder_output/original_order"
        logger.info(f"[{self.short_name.upper()}] Agent initialized - Format 1 Step 1 processor")

        # Create output directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.order_to_image_dir, exist_ok=True)
        os.makedirs(self.original_order_dir, exist_ok=True)

    def process_order(self, file_path):
        """
        Process an order file - extract ALL pages and convert to images

        Args:
            file_path (str): Path to the input PDF file

        Returns:
            dict: Processing results including output file paths for all pages
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
                    output_path = os.path.join(self.order_to_image_dir, f"{order_name}_page1.png")
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

            # Convert PDF to images (all pages)
            logger.info(f"[{self.short_name.upper()}] Converting PDF to images...")

            try:
                # Open PDF with PyMuPDF
                pdf_document = fitz.open(file_path)

                if len(pdf_document) == 0:
                    logger.error(f"[{self.short_name.upper()}] No pages found in PDF")
                    result["status"] = "error"
                    result["error"] = "No pages found in PDF"
                    pdf_document.close()
                    return result

                total_pages = len(pdf_document)
                logger.info(f"[{self.short_name.upper()}] Found {total_pages} pages in PDF")

                page_files = []
                first_page_path = None
                first_page_width = None
                first_page_height = None

                # Convert all pages to images
                for page_num in range(total_pages):
                    page = pdf_document[page_num]

                    # Convert to image at 300 DPI
                    mat = fitz.Matrix(300/72, 300/72)  # 300 DPI scaling
                    pix = page.get_pixmap(matrix=mat)

                    # Convert to PIL Image
                    import io
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    # Save the image to order_to_image folder
                    page_filename = f"{order_name}_page{page_num + 1}.png"
                    page_path = os.path.join(self.order_to_image_dir, page_filename)
                    img.save(page_path, 'PNG')

                    page_files.append({
                        "filename": page_filename,
                        "path": page_path,
                        "page_number": page_num + 1,
                        "width": img.size[0],
                        "height": img.size[1]
                    })

                    # Keep track of first page details
                    if page_num == 0:
                        first_page_width = img.size[0]
                        first_page_height = img.size[1]

                    logger.info(f"[{self.short_name.upper()}] Page {page_num + 1} saved to: {page_path}")

                # Close PDF document
                pdf_document.close()

                logger.info(f"[{self.short_name.upper()}] All {total_pages} pages converted successfully")

                # Copy original file to original_order directory
                import shutil
                original_filename = os.path.basename(file_path)
                original_destination = os.path.join(self.original_order_dir, original_filename)

                try:
                    shutil.copy2(file_path, original_destination)
                    logger.info(f"[{self.short_name.upper()}] Original file copied to: {original_destination}")
                    original_file_copied = True
                    original_file_path = original_destination
                except Exception as copy_error:
                    logger.warning(f"[{self.short_name.upper()}] Failed to copy original file: {str(copy_error)}")
                    original_file_copied = False
                    original_file_path = None

                result["status"] = "success"
                result["output_file"] = first_page_path  # Keep backward compatibility
                result["output_filename"] = f"{order_name}_page1.png"
                result["image_width"] = first_page_width
                result["image_height"] = first_page_height
                result["dpi"] = 300
                result["total_pages"] = total_pages
                result["page_files"] = page_files
                result["order_to_image_dir"] = self.order_to_image_dir
                result["original_file_copied"] = original_file_copied
                result["original_file_path"] = original_file_path
                result["original_order_dir"] = self.original_order_dir
                result["message"] = f"Successfully extracted all {total_pages} pages from {file_name}"

                # JSON result file creation disabled
                # logger.info(f"[{self.short_name.upper()}] Results saved to: {json_output_path}")

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