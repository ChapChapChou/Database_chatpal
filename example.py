from document_processor import DocumentProcessor
from geo_rag_agent import GeoRAGAgent
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize document processor
    doc_processor = DocumentProcessor(openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    # Example: Process documents
    # Uncomment and modify these lines to process your documents
    # doc_processor.load_document("path/to/your/document1.pdf")
    # doc_processor.load_document("path/to/your/document2.txt")
    
    # Save the vector store (this is done automatically in load_document, but you can also do it manually)
    doc_processor.save_vectorstore()
    
    # Initialize the agent
    agent = GeoRAGAgent()
    
    # Example queries
    queries = [
        "What are the main points about urban development in the documents?",
        "Find all buildings within 1km of the city center",
        "What are the environmental regulations mentioned in the documents and how do they affect the buildings in the downtown area?"
    ]
    
    # Run queries
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        response = agent.run(query)
        print(f"Response: {response}")
        print("-" * 50)

if __name__ == "__main__":
    main() 