"""
Auto-migration script để update database schema
Chạy khi backend khởi động
"""
from sqlalchemy import text
from .core.database import engine
import logging

logger = logging.getLogger(__name__)

def run_migrations():
    """Chạy các migrations cần thiết."""
    try:
        with engine.connect() as conn:
            # Add rank columns nếu chưa có
            conn.execute(text("""
                ALTER TABLE institution_master 
                ADD COLUMN IF NOT EXISTS rank_2025 INTEGER,
                ADD COLUMN IF NOT EXISTS rank_type VARCHAR(255);
            """))
            conn.commit()
            logger.info("✅ Migrations completed successfully")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        # Không raise exception để không crash app
        pass

