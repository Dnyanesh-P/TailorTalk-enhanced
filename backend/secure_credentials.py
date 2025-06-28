"""
Secure credential management for TailorTalk
"""
import os
import json
import pickle
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

class SecureCredentialManager:
    """Secure credential management with encryption"""
    
    def __init__(self):
        self.credentials_dir = Path("config")
        self.credentials_dir.mkdir(exist_ok=True)
        
        # Initialize encryption key
        self.key_file = self.credentials_dir / "key.key"
        self.encrypted_token_file = self.credentials_dir / "token.encrypted"
        
        self._ensure_encryption_key()
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists"""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            logger.info("Generated new encryption key")
        
        with open(self.key_file, 'rb') as f:
            self.cipher = Fernet(f.read())
    
    def encrypt_credentials(self, credentials: Credentials) -> bool:
        """Encrypt and store Google credentials"""
        try:
            # Convert credentials to dict
            creds_dict = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            # Serialize and encrypt
            serialized = json.dumps(creds_dict).encode()
            encrypted = self.cipher.encrypt(serialized)
            
            # Store encrypted credentials
            with open(self.encrypted_token_file, 'wb') as f:
                f.write(encrypted)
            
            logger.info("Credentials encrypted and stored securely")
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            return False
    
    def decrypt_credentials(self) -> Optional[Credentials]:
        """Decrypt and load Google credentials"""
        try:
            if not self.encrypted_token_file.exists():
                return None
            
            # Read and decrypt
            with open(self.encrypted_token_file, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.cipher.decrypt(encrypted)
            creds_dict = json.loads(decrypted.decode())
            
            # Reconstruct credentials
            credentials = Credentials(
                token=creds_dict['token'],
                refresh_token=creds_dict['refresh_token'],
                token_uri=creds_dict['token_uri'],
                client_id=creds_dict['client_id'],
                client_secret=creds_dict['client_secret'],
                scopes=creds_dict['scopes']
            )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            return None
    
    def get_secure_credentials(self) -> Optional[Credentials]:
        """Get credentials with automatic refresh"""
        try:
            # Try to load encrypted credentials first
            creds = self.decrypt_credentials()
            
            if creds and creds.valid:
                return creds
            
            # Try to refresh if expired
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.encrypt_credentials(creds)  # Re-encrypt updated credentials
                    logger.info("Credentials refreshed successfully")
                    return creds
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
            
            # Fall back to OAuth flow
            return self._perform_oauth_flow()
            
        except Exception as e:
            logger.error(f"Error getting secure credentials: {e}")
            return None
    
    def _perform_oauth_flow(self) -> Optional[Credentials]:
        """Perform OAuth flow for new credentials"""
        try:
            credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'config/credentials.json')
            
            if not os.path.exists(credentials_path):
                logger.error(f"Credentials file not found: {credentials_path}")
                return None
            
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Encrypt and store new credentials
            self.encrypt_credentials(creds)
            
            logger.info("OAuth flow completed and credentials secured")
            return creds
            
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            return None

# Global instance
secure_credential_manager = SecureCredentialManager()
