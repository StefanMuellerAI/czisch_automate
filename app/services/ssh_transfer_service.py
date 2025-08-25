import paramiko
import io
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
from app.database.models import etl_db, SSHTransferRoute

logger = logging.getLogger(__name__)


class SSHTransferService:
    """Service for secure file transfer via SSH/SFTP"""
    
    @staticmethod
    async def transfer_xml_file(xml_content: str, route_id: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Transfer XML content to remote server via SSH using route configuration"""
        
        try:
            # Get SSH route configuration from database
            ssh_route = etl_db.get_ssh_route(route_id)
            
            if not ssh_route:
                raise ValueError(f"SSH route '{route_id}' not found in database")
            
            logger.info(f"Starting SSH transfer using route '{route_id}' to {ssh_route.hostname}")
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"transfer_{timestamp}.xml"
            
            # Ensure filename has .xml extension
            if not filename.endswith('.xml'):
                filename += '.xml'
            
            # Get decrypted credentials
            credentials = ssh_route.get_decrypted_credentials()
            
            # Establish SSH connection
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                # Connect with password or private key
                if credentials["private_key"]:
                    # Use private key authentication
                    private_key_obj = SSHTransferService._load_private_key(credentials["private_key"])
                    ssh_client.connect(
                        hostname=ssh_route.hostname,
                        port=ssh_route.port,
                        username=ssh_route.username,
                        pkey=private_key_obj,
                        timeout=30
                    )
                elif credentials["password"]:
                    # Use password authentication
                    ssh_client.connect(
                        hostname=ssh_route.hostname,
                        port=ssh_route.port,
                        username=ssh_route.username,
                        password=credentials["password"],
                        timeout=30
                    )
                else:
                    raise ValueError("No valid authentication method found (password or private key required)")
                
                # Create SFTP client
                sftp_client = ssh_client.open_sftp()
                
                try:
                    # Ensure target directory exists
                    SSHTransferService._ensure_remote_directory(sftp_client, ssh_route.target_directory)
                    
                    # Construct full remote path
                    remote_path = f"{ssh_route.target_directory.rstrip('/')}/{filename}"
                    
                    # Transfer XML content
                    with sftp_client.open(remote_path, 'w') as remote_file:
                        remote_file.write(xml_content)
                    
                    # Verify file transfer
                    file_stats = sftp_client.stat(remote_path)
                    file_size = file_stats.st_size
                    
                    logger.info(f"Successfully transferred XML file to {remote_path} ({file_size} bytes)")
                    
                    return {
                        "success": True,
                        "route_id": route_id,
                        "hostname": ssh_route.hostname,
                        "remote_path": remote_path,
                        "filename": filename,
                        "file_size": file_size,
                        "transfer_time": datetime.now().isoformat(),
                        "message": f"XML file successfully transferred to {remote_path}"
                    }
                    
                finally:
                    sftp_client.close()
                    
            finally:
                ssh_client.close()
                
        except Exception as e:
            logger.error(f"SSH transfer failed: {e}")
            return {
                "success": False,
                "route_id": route_id,
                "error": str(e),
                "transfer_time": datetime.now().isoformat(),
                "message": f"Transfer failed: {str(e)}"
            }
    
    @staticmethod
    def _load_private_key(private_key_content: str) -> paramiko.PKey:
        """Load private key from string content"""
        try:
            # Try RSA key first
            key_file = io.StringIO(private_key_content)
            return paramiko.RSAKey.from_private_key(key_file)
        except paramiko.ssh_exception.SSHException:
            try:
                # Try Ed25519 key
                key_file = io.StringIO(private_key_content)
                return paramiko.Ed25519Key.from_private_key(key_file)
            except paramiko.ssh_exception.SSHException:
                try:
                    # Try ECDSA key
                    key_file = io.StringIO(private_key_content)
                    return paramiko.ECDSAKey.from_private_key(key_file)
                except paramiko.ssh_exception.SSHException:
                    # Try DSS key as last resort
                    key_file = io.StringIO(private_key_content)
                    return paramiko.DSSKey.from_private_key(key_file)
    
    @staticmethod
    def _ensure_remote_directory(sftp_client: paramiko.SFTPClient, remote_path: str):
        """Ensure remote directory exists, create if necessary"""
        try:
            # Try to stat the directory
            sftp_client.stat(remote_path)
        except FileNotFoundError:
            # Directory doesn't exist, create it
            try:
                # Create parent directories if needed
                parent_dir = str(Path(remote_path).parent)
                if parent_dir != remote_path and parent_dir != '/':
                    SSHTransferService._ensure_remote_directory(sftp_client, parent_dir)
                
                # Create the directory
                sftp_client.mkdir(remote_path)
                logger.info(f"Created remote directory: {remote_path}")
                
            except Exception as e:
                logger.warning(f"Could not create remote directory {remote_path}: {e}")
    
    @staticmethod
    async def test_ssh_connection(route_id: str) -> Dict[str, Any]:
        """Test SSH connection for a given route"""
        try:
            # Get SSH route configuration
            ssh_route = etl_db.get_ssh_route(route_id)
            
            if not ssh_route:
                return {
                    "success": False,
                    "route_id": route_id,
                    "error": f"SSH route '{route_id}' not found",
                    "test_time": datetime.now().isoformat()
                }
            
            # Get decrypted credentials
            credentials = ssh_route.get_decrypted_credentials()
            
            # Test SSH connection
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                # Connect with timeout
                if credentials["private_key"]:
                    private_key_obj = SSHTransferService._load_private_key(credentials["private_key"])
                    ssh_client.connect(
                        hostname=ssh_route.hostname,
                        port=ssh_route.port,
                        username=ssh_route.username,
                        pkey=private_key_obj,
                        timeout=10
                    )
                    auth_method = "private_key"
                elif credentials["password"]:
                    ssh_client.connect(
                        hostname=ssh_route.hostname,
                        port=ssh_route.port,
                        username=ssh_route.username,
                        password=credentials["password"],
                        timeout=10
                    )
                    auth_method = "password"
                else:
                    return {
                        "success": False,
                        "route_id": route_id,
                        "error": "No valid authentication method found",
                        "test_time": datetime.now().isoformat()
                    }
                
                # Test SFTP
                sftp_client = ssh_client.open_sftp()
                
                # Test directory access
                try:
                    sftp_client.stat(ssh_route.target_directory)
                    directory_accessible = True
                except FileNotFoundError:
                    directory_accessible = False
                
                sftp_client.close()
                
                return {
                    "success": True,
                    "route_id": route_id,
                    "hostname": ssh_route.hostname,
                    "port": ssh_route.port,
                    "username": ssh_route.username,
                    "auth_method": auth_method,
                    "target_directory": ssh_route.target_directory,
                    "directory_accessible": directory_accessible,
                    "test_time": datetime.now().isoformat(),
                    "message": "SSH connection test successful"
                }
                
            finally:
                ssh_client.close()
                
        except Exception as e:
            logger.error(f"SSH connection test failed: {e}")
            return {
                "success": False,
                "route_id": route_id,
                "error": str(e),
                "test_time": datetime.now().isoformat(),
                "message": f"Connection test failed: {str(e)}"
            }
