import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from document_processor import DocumentProcessor
from geo_db_toolkit import GeoDatabaseToolkit
from langchain.memory import ConversationBufferMemory
import logging

logger = logging.getLogger(__name__)

class GeoRAGAgent:
    def __init__(self):
        load_dotenv()
        
        # Initialize OpenAI
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0
        )
        
        # Initialize document processor with FAISS
        self.doc_processor = DocumentProcessor(openai_api_key=os.getenv("OPENAI_API_KEY"))
        
        # Try to load existing vector store
        self.doc_processor.load_vectorstore()
        
        # Initialize database toolkit
        self.db_toolkit = GeoDatabaseToolkit()
        
        # Create tools
        self.tools = self._create_tools()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create agent
        self.agent_executor = self._create_agent()

    def _create_tools(self) -> List[Tool]:
        """Create the tools for the agent."""
        # RAG Tool for document search
        rag_tool = Tool(
            name="Document_Search",
            description="Search for relevant information in documents using semantic search",
            func=self._search_documents
        )
        
        # SQL Generation Tool
        sql_tool = Tool(
            name="Generate_SQL",
            description="Generate SQL query based on natural language input",
            func=self._generate_sql
        )
        
        # Database Execution Tool
        db_tool = Tool(
            name="Execute_SQL",
            description="Execute SQL query on the database",
            func=self._execute_sql
        )
        
        return [rag_tool, sql_tool, db_tool]

    def _create_agent(self) -> AgentExecutor:
        """Create the agent executor."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized SQL generation assistant that helps users query a geospatial database.
            Your primary tasks are:
            1. Generate SQL queries based on user questions
            2. Search relevant documents for context
            3. Execute SQL queries and return results
            
            The database has a 'places' table with the following key columns:
            - name, name_en, name_zh: Place names in different languages
            - latitude, longitude: Geographic coordinates
            - pop_max: Maximum population
            - adm0name: Country name
            - adm1name: Region/State name
            - geom: PostGIS geometry point
            
            When generating SQL:
            1. Use appropriate PostGIS functions for spatial queries
            2. Include proper error handling
            3. Optimize queries for performance
            4. Use parameterized queries when possible
            
            Always follow this process:
            1. First, search documents for relevant context
            2. Then, generate the appropriate SQL query
            3. Finally, execute the query and return results
            
            For spatial queries, use these common patterns:
            - Distance queries: ST_DistanceSphere(geom, (SELECT geom FROM places WHERE name_en = 'City'))
            - Within radius: ST_DistanceSphere(geom, point) <= distance_in_meters
            - Name searches: name ILIKE '%term%' OR name_en ILIKE '%term%' OR name_zh ILIKE '%term%'
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def _search_documents(self, query: str) -> str:
        """Search for relevant documents using FAISS."""
        try:
            results = self.doc_processor.search_documents(query)
            formatted_results = []
            for result in results:
                formatted_results.append(
                    f"Content: {result['content']}\n"
                    f"Source: {result['metadata'].get('source', 'Unknown')}\n"
                )
            return "\n".join(formatted_results)
        except ValueError as e:
            return str(e)

    def _generate_sql(self, query: str) -> str:
        """Generate SQL query based on natural language input for the public.places table."""
        try:
            # 使用 LLM 生成 SQL
            # 注意：在实际应用中，为了防止SQL注入，应该对 query 进行清理或使用参数化查询，
            # 但这里假设 LLM 生成的 SQL 会被进一步审查或在安全的环境中执行。
            prompt = f"""
            You are an expert SQL query generator, specializing in PostgreSQL with the PostGIS extension.
            Your task is to convert natural language questions into precise SQL queries for a table named "public.places".

            Table Description:
            The "public.places" table contains information about populated places around the world,
            including names, administrative hierarchy, geographic coordinates, population data,
            timezones, and other relevant attributes. The geometry is stored using PostGIS.

            Table Schema "public.places":
            - gid (integer, primary key): Unique identifier for each place.
            - name (text, up to 100 chars): Common name of the place.
            - nameascii (text, up to 100 chars): ASCII version of the name.
            - name_en (text, up to 100 chars): English name.
            - name_zh (text, up to 100 chars): Simplified Chinese name.
            - name_zht (text, up to 80 chars): Traditional Chinese name.
            - (Include other relevant name_xx columns if frequently queried, e.g., name_es, name_fr)
            - featurecla (text, up to 50 chars): Feature classification (e.g., 'Admin-0 capital', 'Populated place', 'Port', 'Airport').
            - scalerank (smallint): Scale rank for map display (lower means more important, shown earlier).
            - labelrank (smallint): Label display rank (lower means higher priority).
            - adm0name (text, up to 50 chars): Sovereign country name where the place is located. (e.g., 'China', 'United States')
            - adm0_a3 (text, 3 chars): ISO 3166-1 alpha-3 country code for adm0name. (e.g., 'CHN', 'USA')
            - adm1name (text, up to 100 chars): Name of the first-level administrative unit (e.g., province, state). (e.g., 'Shanghai Shi', 'Illinois')
            - latitude (float/double precision): Latitude in decimal degrees (WGS84).
            - longitude (float/double precision): Longitude in decimal degrees (WGS84).
            - pop_max (float/double precision): Maximum recorded population (numeric, number of persons).
            - pop_min (float/double precision): Minimum recorded population (numeric, number of persons).
            - (Include other popYYYY columns if historical/projected population queries are needed, e.g., pop2000, pop2025)
            - timezone (text, up to 50 chars): Olson timezone name (e.g., 'Asia/Shanghai', 'America/Chicago').
            - wikidataid (text, up to 30 chars): Wikidata entity ID.
            - geom (geometry(Point, 4326)): PostGIS point geometry representing the location. SRID is 4326 (WGS84, latitude/longitude).

            Query Generation Guidelines:
            1.  Always refer to the table as "public.places".
            2.  Use ONLY the columns listed above. If a question implies a column not listed, state that the information is not available or make a best guess based on related columns.
            3.  For spatial queries involving latitude and longitude from user input, construct a PostGIS point using `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)`.
            4.  When comparing with the "geom" column, use appropriate PostGIS functions like:
                - `ST_DWithin(geom1, geom2, distance_meters)`: For finding places within a certain distance (ensure `geom1` and `geom2` are cast to `geography` for meter-based distance, e.g., `ST_DWithin(places.geom::geography, ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography, radius_meters)`).
                - `ST_Distance(geom1::geography, geom2::geography)`: To calculate distance in meters.
                - `ST_Contains(polygon_geom, places.geom)`: To find places within a given polygon.
                - `ST_Intersects(geom1, geom2)`: To check for intersection.
            5.  When filtering by place names (name, name_en, name_zh, etc.), use `ILIKE` for case-insensitive matching if appropriate, e.g., `name_en ILIKE '%New York%'`.
            6.  Handle potential NULL values explicitly if the query logic depends on it (e.g., `WHERE column_name IS NOT NULL` or `COALESCE(column_name, default_value)`). However, for simple selections, filtering out NULLs is often implied if not specified.
            7.  If the question asks for something like "capital city", use the `featurecla` column (e.g., `featurecla LIKE 'Admin-0 capital%'`) or `adm0cap = 1`.
            8.  If a specific number of results is requested (e.g., "top 5"), use `LIMIT`. If ordering is implied, use `ORDER BY` (e.g., by `pop_max DESC` for most populated).
            9.  The generated SQL should be a single, complete, and executable PostgreSQL statement.
            10. you should extremly catious about the unit of the distance, you should convert the unit to meters if the user input is in kilometers or miles.

            Generate ONLY the SQL query based on the following question. Do not include any explanations, comments, markdown, or any text other than the SQL query itself.

            Question: {query}

            SQL Query:
            """
            # ... (LLM call and result processing) ...
            # For example:
            # response = call_llm_service(prompt)
            # sql_query = response.text.strip()
            # return sql_query

        except Exception as e:
            # Log the error appropriately
            print(f"Error generating SQL: {e}")
            # Depending on requirements, you might raise the error,
            # return a default/error SQL, or return an error message.
            return "SELECT 'Error generating SQL query due to an internal issue.';"

    def _execute_sql(self, sql: str) -> str:
        """Execute SQL query on the database."""
        try:
            # 使用数据库工具包执行查询
            results = self.db_toolkit.execute_query(sql)
            
            # 格式化结果
            if not results:
                return "No results found."
            
            # 获取列名
            columns = results[0].keys()
            
            # 格式化输出
            formatted_results = []
            for row in results:
                formatted_row = []
                for col in columns:
                    formatted_row.append(f"{col}: {row[col]}")
                formatted_results.append(" | ".join(formatted_row))
            
            return "\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            return f"Error executing SQL: {str(e)}"

    def run(self, query: str) -> str:
        """Run the agent on a query."""
        try:
            return self.agent_executor.invoke({"input": query})["output"]
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            return f"Error: {str(e)}" 