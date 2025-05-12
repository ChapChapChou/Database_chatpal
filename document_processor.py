import os
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    JSONLoader
)
from langchain_community.vectorstores import FAISS
import pickle
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, openai_api_key: str):
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # 减小块大小
            chunk_overlap=50,  # 减小重叠大小
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],  # 添加中文分隔符
            is_separator_regex=False
        )
        self.vectorstore = None

    def load_document(self, file_path: str) -> List[Any]:
        """Load and process a document based on its file extension."""
        try:
            logger.info(f"start loading document: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document not found: {file_path}")
            
            file_extension = os.path.splitext(file_path)[1].lower()
            logger.info(f"Document type: {file_extension}")
            
            # 选择适当的加载器
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')  # 添加 UTF-8 编码
            elif file_extension == '.docx':
                loader = Docx2txtLoader(file_path)
            elif file_extension == '.json':
                loader = JSONLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")

            # 加载文档
            logger.info("Loading document content...")
            documents = loader.load()
            
            if not documents:
                raise ValueError("Document loaded is empty")
            
            logger.info(f"Successfully loaded document, {len(documents)} pages/sections")
            
            # 打印文档内容示例（用于调试）
            if documents:
                logger.info("Document content example (first 500 characters):")
                logger.info(documents[0].page_content[:500])
            
            # 处理文档并返回原始文档对象
            return documents
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            raise

    def process_documents(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """Process documents into chunks and generate embeddings."""
        try:
            logger.info("Starting to split documents...")
            # 分割文档
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Document splitting completed, {len(chunks)} chunks")
            
            if not chunks:
                # 如果分割失败，尝试直接使用原始文档
                logger.warning("Document splitting failed, trying to use original document")
                chunks = documents
            
            # 创建或更新 FAISS 向量存储
            logger.info("Creating/updating vector store...")
            if self.vectorstore is None:
                self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
                logger.info("Created new vector store")
            else:
                self.vectorstore.add_documents(chunks)
                logger.info("Updated existing vector store")
            
            # 保存向量存储
            self.save_vectorstore()
            
            # 返回处理后的块
            processed_chunks = []
            for chunk in chunks:
                processed_chunks.append({
                    'text': chunk.page_content,
                    'metadata': chunk.metadata
                })
            
            logger.info(f"Document processing completed, returning {len(processed_chunks)} processed chunks")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error processing document chunks: {str(e)}", exc_info=True)
            raise

    def save_vectorstore(self, path: str = "faiss_index"):
        """Save the FAISS vector store to disk."""
        try:
            if self.vectorstore is not None:
                logger.info(f"saving vector store to: {path}")
                self.vectorstore.save_local(path)
                logger.info("vector store saved successfully")
            else:
                logger.warning("no vector store to save")
        except Exception as e:
            logger.error(f"error saving vector store: {str(e)}", exc_info=True)
            raise

    def load_vectorstore(self, path: str = "faiss_index") -> bool:
        """Load the FAISS vector store from disk."""
        try:
            if os.path.exists(path):
                logger.info(f"loading vector store from: {path}")
                # 添加 allow_dangerous_deserialization=True 参数
                self.vectorstore = FAISS.load_local(
                    path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True  # 允许反序列化
                )
                logger.info("vector store loaded successfully")
                return True
            else:
                logger.warning(f"vector store file not found: {path}")
                return False
        except Exception as e:
            logger.error(f"error loading vector store: {str(e)}", exc_info=True)
            return False

    def search_documents(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant documents using FAISS."""
        try:
            if self.vectorstore is None:
                raise ValueError("no documents processed, please load documents first")
            
            logger.info(f"searching for query: {query}")
            docs = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"found {len(docs)} relevant documents")
            
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
            
        except Exception as e:
            logger.error(f"error searching documents: {str(e)}", exc_info=True)
            raise 