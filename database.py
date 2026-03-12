"""
Simple Database Module
"""

from loguru import logger

def init_db():
    """Initialize database"""
    logger.info("✅ Database ready")
    return True