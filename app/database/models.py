import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import logging
from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)

# Database path in project directory
DB_PATH = Path(__file__).parent.parent.parent / "data" / "etl_database.db"


class URLInstruction:
    """Model for URL-specific instructions stored in SQLite"""
    
    def __init__(self, id: Optional[int] = None, url_pattern: str = "", 
                 instructions: List[Dict[str, Any]] = None, 
                 return_format: str = "html", max_chars: Optional[int] = None,
                 description: str = "", created_at: Optional[datetime] = None):
        self.id = id
        self.url_pattern = url_pattern
        self.instructions = instructions or []
        self.return_format = return_format  # html, text, json
        self.max_chars = max_chars
        self.description = description
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url_pattern": self.url_pattern,
            "instructions": self.instructions,
            "return_format": self.return_format,
            "max_chars": self.max_chars,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class TransformRule:
    """Model for HTML-to-XML transformation rules"""
    
    def __init__(self, id: Optional[int] = None, rule_name: str = "",
                 rules: List[Dict[str, Any]] = None, output_format: str = "xml",
                 description: str = "", created_at: Optional[datetime] = None):
        self.id = id
        self.rule_name = rule_name
        self.rules = rules or []
        self.output_format = output_format
        self.description = description
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "rules": self.rules,
            "output_format": self.output_format,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SSHTransferRoute:
    """Model for SSH transfer routes with encrypted credentials"""
    
    def __init__(self, id: Optional[int] = None, route_id: str = "",
                 hostname: str = "", port: int = 22, username: str = "",
                 password: str = "", private_key: str = "", 
                 target_directory: str = "", description: str = "",
                 created_at: Optional[datetime] = None):
        self.id = id
        self.route_id = route_id
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password  # Will be encrypted when stored
        self.private_key = private_key  # Will be encrypted when stored
        self.target_directory = target_directory
        self.description = description
        self.created_at = created_at or datetime.now()
    
    def to_dict(self, include_credentials: bool = False) -> Dict[str, Any]:
        """Convert to dict, optionally including credentials (for admin use)"""
        result = {
            "id": self.id,
            "route_id": self.route_id,
            "hostname": self.hostname,
            "port": self.port,
            "username": self.username,
            "target_directory": self.target_directory,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_credentials:
            result.update({
                "password": "***" if self.password else None,
                "private_key": "***" if self.private_key else None
            })
        
        return result
    
    def get_decrypted_credentials(self) -> Dict[str, str]:
        """Get decrypted credentials for SSH connection"""
        try:
            return {
                "password": encryption_service.decrypt(self.password) if self.password else "",
                "private_key": encryption_service.decrypt(self.private_key) if self.private_key else ""
            }
        except Exception as e:
            logger.error(f"Failed to decrypt SSH credentials: {e}")
            return {"password": "", "private_key": ""}


class ETLDatabase:
    """Database service for ETL operations (URL instructions and Transform rules)"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the data directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create URL instructions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS url_instructions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url_pattern TEXT NOT NULL UNIQUE,
                        instructions TEXT NOT NULL,
                        return_format TEXT DEFAULT 'html',
                        max_chars INTEGER,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create transform rules table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transform_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_name TEXT NOT NULL UNIQUE,
                        rules TEXT NOT NULL,
                        output_format TEXT DEFAULT 'xml',
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create SSH transfer routes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ssh_transfer_routes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        route_id TEXT NOT NULL UNIQUE,
                        hostname TEXT NOT NULL,
                        port INTEGER DEFAULT 22,
                        username TEXT NOT NULL,
                        password TEXT,
                        private_key TEXT,
                        target_directory TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_url_pattern 
                    ON url_instructions(url_pattern)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_rule_name 
                    ON transform_rules(rule_name)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_route_id 
                    ON ssh_transfer_routes(route_id)
                """)
                
                conn.commit()
                logger.info("ETL Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def add_instruction(self, instruction: URLInstruction) -> int:
        """Add a new URL instruction to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO url_instructions 
                    (url_pattern, instructions, return_format, max_chars, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    instruction.url_pattern,
                    json.dumps(instruction.instructions),
                    instruction.return_format,
                    instruction.max_chars,
                    instruction.description
                ))
                
                instruction_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added URL instruction for pattern: {instruction.url_pattern}")
                return instruction_id
                
        except Exception as e:
            logger.error(f"Failed to add URL instruction: {e}")
            raise
    
    def get_instruction_for_url(self, url: str) -> Optional[URLInstruction]:
        """Get instruction for a specific URL"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First try exact match
                cursor.execute("""
                    SELECT * FROM url_instructions 
                    WHERE url_pattern = ? 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (url,))
                
                row = cursor.fetchone()
                
                # If no exact match, try pattern matching
                if not row:
                    cursor.execute("""
                        SELECT * FROM url_instructions 
                        WHERE ? LIKE '%' || url_pattern || '%' 
                        ORDER BY LENGTH(url_pattern) DESC, updated_at DESC 
                        LIMIT 1
                    """, (url,))
                    row = cursor.fetchone()
                
                if row:
                    return self._row_to_instruction(row)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get URL instruction: {e}")
            return None
    
    def get_all_instructions(self) -> List[URLInstruction]:
        """Get all URL instructions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM url_instructions 
                    ORDER BY updated_at DESC
                """)
                
                rows = cursor.fetchall()
                return [self._row_to_instruction(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all URL instructions: {e}")
            return []
    
    def delete_instruction(self, instruction_id: int) -> bool:
        """Delete a URL instruction"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM url_instructions WHERE id = ?
                """, (instruction_id,))
                
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    logger.info(f"Deleted URL instruction with ID: {instruction_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete URL instruction: {e}")
            return False
    
    def _row_to_instruction(self, row) -> URLInstruction:
        """Convert database row to URLInstruction object"""
        return URLInstruction(
            id=row[0],
            url_pattern=row[1],
            instructions=json.loads(row[2]) if row[2] else [],
            return_format=row[3] or "html",
            max_chars=row[4],
            description=row[5] or "",
            created_at=datetime.fromisoformat(row[6]) if row[6] else None
        )


    # === TRANSFORM RULES METHODS ===
    
    def add_transform_rule(self, rule: TransformRule) -> int:
        """Add a new transform rule to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO transform_rules 
                    (rule_name, rules, output_format, description)
                    VALUES (?, ?, ?, ?)
                """, (
                    rule.rule_name,
                    json.dumps(rule.rules),
                    rule.output_format,
                    rule.description
                ))
                
                rule_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added transform rule: {rule.rule_name}")
                return rule_id
                
        except Exception as e:
            logger.error(f"Failed to add transform rule: {e}")
            raise
    
    def get_transform_rule(self, rule_name: str) -> Optional[TransformRule]:
        """Get transform rule by name"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM transform_rules 
                    WHERE rule_name = ? 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (rule_name,))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_transform_rule(row)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get transform rule: {e}")
            return None
    
    def get_all_transform_rules(self) -> List[TransformRule]:
        """Get all transform rules"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM transform_rules 
                    ORDER BY updated_at DESC
                """)
                
                rows = cursor.fetchall()
                return [self._row_to_transform_rule(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all transform rules: {e}")
            return []
    
    def delete_transform_rule(self, rule_id: int) -> bool:
        """Delete a transform rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM transform_rules WHERE id = ?
                """, (rule_id,))
                
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    logger.info(f"Deleted transform rule with ID: {rule_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete transform rule: {e}")
            return False
    
    def _row_to_transform_rule(self, row) -> TransformRule:
        """Convert database row to TransformRule object"""
        return TransformRule(
            id=row[0],
            rule_name=row[1],
            rules=json.loads(row[2]) if row[2] else [],
            output_format=row[3] or "xml",
            description=row[4] or "",
            created_at=datetime.fromisoformat(row[5]) if row[5] else None
        )
    
    
    # === SSH TRANSFER ROUTES METHODS ===
    
    def add_ssh_route(self, route: SSHTransferRoute) -> int:
        """Add a new SSH transfer route with encrypted credentials"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Encrypt sensitive fields
                encrypted_password = encryption_service.encrypt(route.password) if route.password else ""
                encrypted_private_key = encryption_service.encrypt(route.private_key) if route.private_key else ""
                
                cursor.execute("""
                    INSERT OR REPLACE INTO ssh_transfer_routes 
                    (route_id, hostname, port, username, password, private_key, target_directory, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    route.route_id,
                    route.hostname,
                    route.port,
                    route.username,
                    encrypted_password,
                    encrypted_private_key,
                    route.target_directory,
                    route.description
                ))
                
                route_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added SSH transfer route: {route.route_id}")
                return route_id
                
        except Exception as e:
            logger.error(f"Failed to add SSH route: {e}")
            raise
    
    def get_ssh_route(self, route_id: str) -> Optional[SSHTransferRoute]:
        """Get SSH transfer route by route_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM ssh_transfer_routes 
                    WHERE route_id = ? 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (route_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_ssh_route(row)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get SSH route: {e}")
            return None
    
    def get_all_ssh_routes(self) -> List[SSHTransferRoute]:
        """Get all SSH transfer routes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM ssh_transfer_routes 
                    ORDER BY updated_at DESC
                """)
                
                rows = cursor.fetchall()
                return [self._row_to_ssh_route(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all SSH routes: {e}")
            return []
    
    def delete_ssh_route(self, route_db_id: int) -> bool:
        """Delete SSH transfer route by database ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM ssh_transfer_routes WHERE id = ?
                """, (route_db_id,))
                
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    logger.info(f"Deleted SSH route with ID: {route_db_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete SSH route: {e}")
            return False
    
    def _row_to_ssh_route(self, row) -> SSHTransferRoute:
        """Convert database row to SSHTransferRoute object with encrypted credentials"""
        return SSHTransferRoute(
            id=row[0],
            route_id=row[1],
            hostname=row[2],
            port=row[3],
            username=row[4],
            password=row[5] or "",  # Keep encrypted
            private_key=row[6] or "",  # Keep encrypted
            target_directory=row[7],
            description=row[8] or "",
            created_at=datetime.fromisoformat(row[9]) if row[9] else None
        )


# Global database instance
etl_db = ETLDatabase()
