from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
from werkzeug.utils import secure_filename
import sys
import io
from contextlib import redirect_stdout
import threading
import queue
import time
from geo_rag_agent import GeoRAGAgent
import logging
import re
from document_processor import DocumentProcessor
from file_upload_handler import FileUploadHandler
from dotenv import load_dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'docs'
socketio = SocketIO(app)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 创建输出队列
output_queue = queue.Queue()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ANSI 颜色代码的正则表达式
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# 加载环境变量
load_dotenv()

# 初始化处理器
upload_handler = FileUploadHandler(socketio=socketio)
doc_processor = DocumentProcessor(openai_api_key=os.getenv("OPENAI_API_KEY"))
agent = GeoRAGAgent()

class TerminalOutputCapture:
    def __init__(self, queue):
        self.queue = queue
        self.buffer = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, text):
        # 移除 ANSI 颜色代码
        clean_text = ansi_escape.sub('', text)
        self.buffer.write(clean_text)
        self.queue.put(clean_text)
        self.original_stdout.write(text)

    def flush(self):
        self.buffer.flush()
        self.original_stdout.flush()

    def __enter__(self):
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

def process_output():
    """process the output queue and send to web socket"""
    while True:
        try:
            message = output_queue.get()
            if message:
                socketio.emit('terminal_output', {'data': message})
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error processing output: {str(e)}")

# 启动输出处理线程
output_thread = threading.Thread(target=process_output, daemon=True)
output_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    # 处理文件上传
    success, message = upload_handler.handle_upload(file, doc_processor)
    return jsonify({'success': success, 'message': message})

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'success': False, 'message': 'No query provided'})
    
    try:
        # 执行查询
        result = agent.run(data['query'])
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@socketio.on('query')
def handle_query(data):
    query = data.get('query', '')
    if not query:
        return
    
    try:
        # 创建新的输出捕获器
        with TerminalOutputCapture(output_queue):
            # 执行查询
            response = agent.run(query)
            # 发送最终响应
            emit('query_response', {'data': response})
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        emit('error', {'data': str(e)})

if __name__ == '__main__':
    socketio.run(app, debug=True) 