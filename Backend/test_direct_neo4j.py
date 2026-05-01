#!/usr/bin/env python
"""Direct Neo4j connection test with provided credentials."""

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j+s://78a8f877.databases.neo4j.io"
AUTH = ("78a8f877", "jcPMK1I-f6UnheRdEaxBlribeUJOz4PGCuZOyVk_6ZI")

def test_connection():
    logger.info(f"Testing connection to: {URI}")
    logger.info(f"Username: {AUTH[0]}")
    logger.info(f"Password: {'*' * len(AUTH[1])}")
    
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            logger.info("✅ Connection successful!")
            
            # Test a simple query
            with driver.session() as session:
                result = session.run("RETURN 1 as num")
                record = result.single()
                logger.info(f"Query test: {record['num']}")
            
            return True
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
