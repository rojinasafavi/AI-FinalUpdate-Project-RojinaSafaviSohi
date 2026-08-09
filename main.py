import os
import time
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Upgrade logging to be highly detailed and production-ready
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("main_pipeline")

async def run_pipeline():
    logger.info("Starting Async Social Media Analytics Pipeline...")
    
    # 1. Load configuration
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        logger.warning("GEMINI_API_KEY is missing or invalid in .env file.")
        logger.warning("Please configure it before running the script against real data.")
        return

    # Importing dynamically purely to ensure env vars are checked first
    try:
        from services.data_processing import process_social_media_file
        from services.analysis_aggregator import aggregate_social_media_data
        from services.report_generator import generate_management_report
    except ImportError as e:
        logger.error(f"Failed to load internal services: {e}")
        return

    # Paths
    input_file = Path("data/sample_input.json")
    output_report_file = Path("reports/management_report.md")

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return

    # 2. Process and Clean Data
    logger.info(f"Loading and validating data from {input_file}...")
    try:
        clean_texts = process_social_media_file(input_file)
        logger.info(f"Successfully extracted and cleaned {len(clean_texts)} posts.")
    except Exception as e:
        logger.error(f"Data processing failed: {e}")
        return

    if not clean_texts:
        logger.warning("No valid text data found to process. Exiting.")
        return

    # 3. Analyze and Aggregate (Fully Asynchronous)
    logger.info("Sending tasks to Async OpenAI (with smart rate limiting and API retries)...")
    start_time = time.time()
    try:
        aggregated_data = await aggregate_social_media_data(clean_texts, max_concurrent=10)
        
        if "error" in aggregated_data:
            logger.error(f"Aggregation failed: {aggregated_data['error']}")
            return
            
        elapsed_time = time.time() - start_time
        logger.info(f"Aggregation complete! Processed {aggregated_data.get('total_processed')} items in {elapsed_time:.2f} seconds.")
    except Exception as e:
        logger.error(f"Analysis aggregation failed: {e}")
        return

    # 4. Generate Final Management Report (Asynchronous)
    logger.info("Generating high-level management report...")
    try:
        final_report = await generate_management_report(aggregated_data)
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return

    # 5. Output Results
    print("\n" + "="*60)
    print("                    MANAGEMENT REPORT")
    print("="*60 + "\n")
    print(final_report)
    print("\n" + "="*60 + "\n")

    # Save to file
    try:
        output_report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_report_file, "w", encoding="utf-8") as f:
            f.write(final_report)
        logger.info(f"Report successfully saved to {output_report_file}")
    except Exception as e:
        logger.error(f"Failed to save report to file: {e}")

def main():
    """Application entry point handling the asyncio event loop."""
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        logger.warning("Pipeline manually interrupted by user.")
    except Exception as e:
        logger.critical(f"Fatal error encountered: {e}")

if __name__ == "__main__":
    main()
