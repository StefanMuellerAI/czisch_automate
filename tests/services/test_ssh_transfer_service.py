import os
import io
import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock
import subprocess

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pytest
import paramiko

# Ensure encryption service initializes
os.environ.setdefault("ENCRYPTION_PASSWORD", "testpassword")

from app.services.ssh_transfer_service import SSHTransferService, etl_db, paramiko as ssh_paramiko


class MockRoute:
    def __init__(self):
        self.route_id = "route1"
        self.hostname = "example.com"
        self.port = 22
        self.username = "user"
        self.target_directory = "/remote"

    def get_decrypted_credentials(self):
        return {"password": "secret", "private_key": ""}


def test_transfer_xml_file_success(monkeypatch):
    route = MockRoute()
    monkeypatch.setattr(etl_db, "get_ssh_route", lambda rid: route)

    ssh_client = MagicMock()
    sftp_client = MagicMock()
    ssh_client.open_sftp.return_value = sftp_client
    remote_file = MagicMock()
    sftp_client.open.return_value.__enter__.return_value = remote_file

    class Stat:
        st_size = 15

    sftp_client.stat.return_value = Stat()

    monkeypatch.setattr(ssh_paramiko, "SSHClient", lambda: ssh_client)
    monkeypatch.setattr(SSHTransferService, "_ensure_remote_directory", MagicMock())

    content = "<data>ok</data>"
    result = asyncio.run(SSHTransferService.transfer_xml_file(content, "route1", filename="test.xml"))

    assert result["success"] is True
    assert result["remote_path"] == "/remote/test.xml"
    remote_file.write.assert_called_once_with(content)
    ssh_client.connect.assert_called_once()
    sftp_client.stat.assert_called_once_with("/remote/test.xml")


def test_transfer_xml_file_route_missing(monkeypatch):
    monkeypatch.setattr(etl_db, "get_ssh_route", lambda rid: None)
    result = asyncio.run(SSHTransferService.transfer_xml_file("<data/>", "missing"))
    assert result["success"] is False
    assert "not found" in result["error"].lower()


def _key_to_str(key):
    buf = io.StringIO()
    key.write_private_key(buf)
    return buf.getvalue()


def _generate_ed25519_key_str():
    import tempfile
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, 'key')
    subprocess.run(['ssh-keygen','-t','ed25519','-f',path,'-N',''], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(path) as f:
        key = f.read()
    os.remove(path)
    os.remove(path + '.pub')
    os.rmdir(tmpdir)
    return key


def test_load_private_key_rsa():
    key_str = _key_to_str(paramiko.RSAKey.generate(1024))
    loaded = SSHTransferService._load_private_key(key_str)
    assert isinstance(loaded, paramiko.RSAKey)


def test_load_private_key_ed25519():
    key_str = _generate_ed25519_key_str()
    loaded = SSHTransferService._load_private_key(key_str)
    from paramiko.ed25519key import Ed25519Key
    assert isinstance(loaded, Ed25519Key)


def test_load_private_key_ecdsa():
    key_str = _key_to_str(paramiko.ECDSAKey.generate(bits=256))
    loaded = SSHTransferService._load_private_key(key_str)
    assert isinstance(loaded, paramiko.ECDSAKey)


def test_load_private_key_dss():
    key_str = _key_to_str(paramiko.DSSKey.generate(1024))
    loaded = SSHTransferService._load_private_key(key_str)
    assert isinstance(loaded, paramiko.DSSKey)
