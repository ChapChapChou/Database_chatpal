import os
from dotenv import load_dotenv
from document_processor import DocumentProcessor
import argparse
from pathlib import Path

def process_directory(directory: str, processor: DocumentProcessor):
    """Process all supported documents in a directory."""
    supported_extensions = {'.pdf', '.txt', '.docx', '.json'}
    
    for file_path in Path(directory).rglob('*'):
        if file_path.suffix.lower() in supported_extensions:
            print(f"Processing {file_path}...")
            try:
                processor.load_document(str(file_path))
                print(f"Successfully processed {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

def main():
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process documents and create FAISS index')
    parser.add_argument('--input', '-i', required=True, help='Input file or directory path')
    parser.add_argument('--output', '-o', default='faiss_index', help='Output directory for FAISS index')
    args = parser.parse_args()
    
    # Initialize document processor
    processor = DocumentProcessor(openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    # Process input
    input_path = Path(args.input)
    if input_path.is_file():
        print(f"Processing single file: {input_path}")
        processor.load_document(str(input_path))
    elif input_path.is_dir():
        print(f"Processing directory: {input_path}")
        process_directory(str(input_path), processor)
    else:
        print(f"Error: {input_path} does not exist")
        return
    
    # Save the vector store
    print(f"Saving FAISS index to {args.output}...")
    processor.save_vectorstore(args.output)
    print("Done!")

if __name__ == "__main__":
    main() 