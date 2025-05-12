import os
import shutil
from typing import Tuple, Optional
from werkzeug.utils import secure_filename
import logging
from document_processor import DocumentProcessor
from flask_socketio import SocketIO

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileUploadHandler:
    def __init__(self, upload_folder: str = "docs", socketio: Optional[SocketIO] = None):
        self.upload_folder = upload_folder
        self.allowed_extensions = {'.pdf', '.txt', '.docx', '.json'}
        self.socketio = socketio
        
        # 确保上传目录存在
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            logger.info(f"Created upload directory: {upload_folder}")

    def _emit_progress(self, message: str):
        """发送进度消息到前端"""
        if self.socketio:
            self.socketio.emit('upload_progress', {'message': message})
            logger.info(f"Progress: {message}")

    def is_allowed_file(self, filename: str) -> bool:
        """检查文件类型是否允许"""
        return os.path.splitext(filename)[1].lower() in self.allowed_extensions

    def get_safe_filename(self, filename: str) -> str:
        """获取安全的文件名"""
        return secure_filename(filename)

    def file_exists(self, filename: str) -> bool:
        """检查文件是否已存在"""
        safe_filename = self.get_safe_filename(filename)
        return os.path.exists(os.path.join(self.upload_folder, safe_filename))

    def save_file(self, file) -> Tuple[bool, str, Optional[str]]:
        """
        保存上传的文件
        
        Returns:
            Tuple[bool, str, Optional[str]]: (是否成功, 消息, 文件路径)
        """
        if not file:
            return False, "No file provided", None

        if not self.is_allowed_file(file.filename):
            return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}", None

        safe_filename = self.get_safe_filename(file.filename)
        
        # 检查文件是否已存在
        if self.file_exists(safe_filename):
            return False, f"File '{safe_filename}' already exists", None

        try:
            # 保存文件
            file_path = os.path.join(self.upload_folder, safe_filename)
            file.save(file_path)
            self._emit_progress(f"File '{safe_filename}' saved successfully")
            logger.info(f"File saved successfully: {file_path}")
            return True, f"File '{safe_filename}' uploaded successfully", file_path
        except Exception as e:
            error_msg = f"Error saving file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def process_new_document(self, file_path: str, doc_processor: DocumentProcessor) -> Tuple[bool, str]:
        """
        处理新上传的文档
        
        Args:
            file_path: 文件路径
            doc_processor: DocumentProcessor 实例
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 处理文档
            filename = os.path.basename(file_path)
            self._emit_progress(f"Starting to process document: {filename}")
            logger.info(f"Processing new document: {file_path}")
            
            # 加载文档
            self._emit_progress(f"Loading document content...")
            documents = doc_processor.load_document(file_path)
            
            # 处理文档
            self._emit_progress(f"Processing document...")
            doc_processor.process_documents(documents)
            
            success_msg = f"Document processed successfully: {filename}"
            self._emit_progress(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(error_msg)
            self._emit_progress(f"Error: {error_msg}")
            return False, error_msg

    def handle_upload(self, file, doc_processor: DocumentProcessor) -> Tuple[bool, str]:
        """
        处理文件上传的完整流程
        
        Args:
            file: 上传的文件对象
            doc_processor: DocumentProcessor 实例
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 保存文件
        success, message, file_path = self.save_file(file)
        if not success:
            return False, message

        # 处理文档
        return self.process_new_document(file_path, doc_processor) 