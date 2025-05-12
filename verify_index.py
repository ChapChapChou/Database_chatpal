import os
from dotenv import load_dotenv
from document_processor import DocumentProcessor

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize document processor
    processor = DocumentProcessor(openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    # Try to load the vector store
    if processor.load_vectorstore():
        print("Successfully loaded FAISS index")
        
        # Test some queries
        test_queries = [
            "What are the main topics in the documents?",
            "Summarize the key points",
            "What are the important dates mentioned?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("-" * 50)
            results = processor.search_documents(query)
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"Content: {result['content'][:200]}...")  # Show first 200 chars
                print(f"Source: {result['metadata'].get('source', 'Unknown')}")
    else:
        print("No FAISS index found. Please process some documents first.")

if __name__ == "__main__":
    main() 