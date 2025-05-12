import os
from dotenv import load_dotenv
from document_processor import DocumentProcessor
from geo_rag_agent import GeoRAGAgent
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_document_processing():
    """测试文档处理功能"""
    try:
        logger.info("=== 开始文档处理测试 ===")
        
        # 初始化文档处理器
        processor = DocumentProcessor(openai_api_key=os.getenv("OPENAI_API_KEY"))
        
        # 处理文档目录中的所有文档
        docs_dir = "docs"
        if not os.path.exists(docs_dir):
            logger.error(f"文档目录不存在: {docs_dir}")
            return
        
        for filename in os.listdir(docs_dir):
            if filename.endswith(('.pdf', '.txt', '.docx', '.json')):
                file_path = os.path.join(docs_dir, filename)
                try:
                    logger.info(f"处理文档: {file_path}")
                    processor.load_document(file_path)
                    logger.info(f"文档处理成功: {filename}")
                except Exception as e:
                    logger.error(f"处理文档失败: {filename} - {str(e)}")
        
        logger.info("=== 文档处理测试完成 ===")
        
    except Exception as e:
        logger.error(f"文档处理测试失败: {str(e)}")

def test_database_queries():
    """测试数据库查询功能"""
    try:
        logger.info("=== 开始数据库查询测试 ===")
        
        # 初始化数据库工具包
        from geo_db_toolkit import GeoDatabaseToolkit
        db_toolkit = GeoDatabaseToolkit()
        
        # 测试查询
        test_queries = [
            "查找距离上海100公里内的所有城市",
            "搜索名称包含'北京'的地点",
            "获取上海的详细信息"
        ]
        
        for query in test_queries:
            try:
                logger.info(f"执行查询: {query}")
                result = db_toolkit.run_query(query)
                logger.info(f"查询结果: {result}")
            except Exception as e:
                logger.error(f"查询失败: {query} - {str(e)}")
        
        logger.info("=== 数据库查询测试完成 ===")
        
    except Exception as e:
        logger.error(f"数据库查询测试失败: {str(e)}")

def test_agent():
    """测试完整代理功能"""
    try:
        logger.info("=== 开始代理测试 ===")
        
        # 初始化代理
        agent = GeoRAGAgent()
        
        # 测试查询
        test_queries = [
            "上海有哪些著名的旅游景点？",
            "距离北京100公里内有哪些城市？",
            "请介绍一下上海的历史"
        ]
        
        for query in test_queries:
            try:
                logger.info(f"执行查询: {query}")
                response = agent.run(query)
                logger.info(f"代理响应: {response}")
            except Exception as e:
                logger.error(f"查询失败: {query} - {str(e)}")
        
        logger.info("=== 代理测试完成 ===")
        
    except Exception as e:
        logger.error(f"代理测试失败: {str(e)}")

def interactive_mode():
    """交互式测试模式"""
    try:
        logger.info("=== 进入交互式测试模式 ===")
        
        # 初始化代理
        agent = GeoRAGAgent()
        
        while True:
            print("\n可用命令:")
            print("d - 测试文档处理")
            print("q - 测试数据库查询")
            print("a - 测试代理")
            print("i - 输入自定义查询")
            print("x - 退出")
            
            command = input("\n请输入命令或问题: ").strip().lower()
            
            if command == 'x':
                break
            elif command == 'd':
                test_document_processing()
            elif command == 'q':
                test_database_queries()
            elif command == 'a':
                test_agent()
            elif command == 'i':
                query = input("请输入您的问题: ").strip()
                if query:
                    try:
                        response = agent.run(query)
                        print(f"\n回答: {response}")
                    except Exception as e:
                        logger.error(f"处理查询失败: {str(e)}")
            else:
                print("无效的命令，请重试")
        
        logger.info("=== 退出交互式测试模式 ===")
        
    except Exception as e:
        logger.error(f"交互式测试失败: {str(e)}")

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 检查必要的环境变量
    required_vars = ["OPENAI_API_KEY", "POSTGRES_USER", 
                    "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB"]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        exit(1)
    
    # 运行交互式模式
    interactive_mode() 