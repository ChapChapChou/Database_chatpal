from typing import List, Dict, Any
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger(__name__)

class GeoDatabaseToolkit:
    def __init__(self):
        load_dotenv()
        
        # Initialize database connection
        self.engine = self._create_engine()
        
        # Initialize SQLDatabase
        self.db = SQLDatabase(engine=self.engine)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0
        )
        
        # Create base toolkit
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        # Add custom tools
        self.tools = self._create_tools()

    def _create_engine(self) -> Engine:
        """create the database connection"""
        try:
            connection_string = (
                f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
                f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
            )
            return create_engine(connection_string)
        except Exception as e:
            logger.error(f"create database connection failed: {str(e)}")
            raise

    def _create_tools(self) -> List[Tool]:
        """Create custom tools for geospatial queries."""
        base_tools = self.toolkit.get_tools()
        
        # Add custom geospatial tools
        custom_tools = [
            Tool(
                name="Find_Nearby_Places",
                description="Find places within a certain distance of a point",
                func=self.find_nearby_places
            ),
            Tool(
                name="Search_Places_By_Name",
                description="Search places by name in multiple languages",
                func=self.search_places_by_name
            ),
            Tool(
                name="Get_Place_Details",
                description="Get detailed information about a specific place",
                func=self.get_place_details
            )
        ]
        
        return base_tools + custom_tools

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """execute the sql query and return the result"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql))
                # get the column names
                columns = result.keys()
                # convert the result to a list of dictionaries, ensuring each value is serializable
                return [dict(zip(columns, [str(val) if val is not None else None for val in row])) 
                       for row in result]
        except Exception as e:
            logger.error(f"execute query failed: {str(e)}")
            raise

    def find_nearby_places(self, place_name: str, distance_km: float) -> str:
        """find the places within a certain distance of a point"""
        return f"""
        SELECT name, name_en, name_zh, latitude, longitude, pop_max, adm0name, adm1name
        FROM places
        WHERE ST_DistanceSphere(geom, (SELECT geom FROM places WHERE name_en = '{place_name}')) <= {distance_km * 1000};
        """

    def search_places_by_name(self, name: str) -> str:
        """search the places by name in multiple languages"""
        return f"""
        SELECT name, name_en, name_zh, latitude, longitude, pop_max, adm0name, adm1name
        FROM places
        WHERE name ILIKE '%{name}%' OR name_en ILIKE '%{name}%' OR name_zh ILIKE '%{name}%';
        """

    def get_place_details(self, place_name: str) -> str:
        """get the detailed information about a specific place"""
        return f"""
        SELECT name, name_en, name_zh, latitude, longitude, pop_max, adm0name, adm1name
        FROM places
        WHERE name = '{place_name}' OR name_en = '{place_name}' OR name_zh = '{place_name}';
        """

    def get_tools(self) -> List[Tool]:
        """Get all available tools."""
        return self.tools

    def get_table_info(self) -> str:
        """Get information about the database tables."""
        return self.db.get_table_info() 