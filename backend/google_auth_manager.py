"""
Google Authentication Manager for TailorTalk Enhanced
Handles OAuth2 flow, credential storage, and user session management
"""
import os
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
from pathlib import Path

# Google OAuth2 imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class GoogleAuthManager:
    """Secure Google OAuth2 authentication manager"""
    
    def __init__(self, credentials_path: str = 'config/credentials.json'):
        self.credentials_path = credentials_path
        self.auth_data_dir = Path('auth_data')
        self.auth_data_dir.mkdir(exist_ok=True)
        
        # OAuth2 configuration
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_credentials: Dict[str, Credentials] = {}
        self.user_info_cache: Dict[str, Dict[str, Any]] = {}
        
        # Encryption for secure storage
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Load existing sessions
        self._load_existing_sessions()
        
        logger.info("Google Auth Manager initialized")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secure storage"""
        key_file = self.auth_data_dir / 'encryption.key'
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _load_existing_sessions(self):
        """Load existing user sessions from storage"""
        try:
            sessions_file = self.auth_data_dir / 'sessions.json'
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    encrypted_data = f.read()
                
                if encrypted_data:
                    decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
                    sessions_data = json.loads(decrypted_data.decode())
                    
                    # Restore sessions and validate credentials
                    for user_id, session_data in sessions_data.items():
                        if self._validate_session(session_data):
                            self.active_sessions[user_id] = session_data
                            
                            # Restore credentials
                            creds_data = session_data.get('credentials')
                            if creds_data:
                                credentials = Credentials.from_authorized_user_info(creds_data)
                                self.user_credentials[user_id] = credentials
                    
                    logger.info(f"Loaded {len(self.active_sessions)} existing sessions")
        
        except Exception as e:
            logger.error(f"Error loading existing sessions: {e}")
    
    def _validate_session(self, session_data: Dict[str, Any]) -> bool:
        """Validate if session is still valid"""
        try:
            expires_at = datetime.fromisoformat(session_data.get('expires_at', ''))
            return datetime.now(pytz.timezone('Asia/Kolkata')) < expires_at
        except:
            return False
    
    def _save_sessions(self):
        """Save current sessions to encrypted storage"""
        try:
            sessions_data = {}
            
            for user_id, session_data in self.active_sessions.items():
                # Include credentials in session data
                if user_id in self.user_credentials:
                    credentials = self.user_credentials[user_id]
                    session_data['credentials'] = {
                        'token': credentials.token,
                        'refresh_token': credentials.refresh_token,
                        'token_uri': credentials.token_uri,
                        'client_id': credentials.client_id,
                        'client_secret': credentials.client_secret,
                        'scopes': credentials.scopes
                    }
                
                sessions_data[user_id] = session_data
            
            # Encrypt and save
            json_data = json.dumps(sessions_data)
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            
            sessions_file = self.auth_data_dir / 'sessions.json'
            with open(sessions_file, 'w') as f:
                f.write(encrypted_data.decode())
            
            logger.debug(f"Saved {len(sessions_data)} sessions")
            
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def create_auth_flow(self, redirect_uri: str = 'http://localhost:8001/auth/callback') -> Flow:
        """Create OAuth2 flow for authentication"""
        try:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"Google credentials not found at: {self.credentials_path}")
            
            flow = Flow.from_client_secrets_file(
                self.credentials_path,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            return flow
            
        except Exception as e:
            logger.error(f"Error creating auth flow: {e}")
            raise
    
    def get_auth_url(self, state: str = None) -> str:
        """Get authorization URL for OAuth2 flow"""
        try:
            flow = self.create_auth_flow()
            
            if not state:
                state = secrets.token_urlsafe(32)
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state
            )
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error getting auth URL: {e}")
            raise
    
    def handle_auth_callback(self, authorization_code: str, state: str = None) -> str:
        """Handle OAuth2 callback and create user session"""
        try:
            flow = self.create_auth_flow()
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # Get user info
            user_info = self._get_user_info_from_credentials(credentials)
            user_id = self._generate_user_id(user_info['email'])
            
            # Create session
            session_data = {
                'user_id': user_id,
                'email': user_info['email'],
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'created_at': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                'expires_at': (datetime.now(pytz.timezone('Asia/Kolkata')) + timedelta(days=30)).isoformat(),
                'last_activity': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            }
            
            # Store session and credentials
            self.active_sessions[user_id] = session_data
            self.user_credentials[user_id] = credentials
            self.user_info_cache[user_id] = user_info
            
            # Save to storage
            self._save_sessions()
            
            logger.info(f"User authenticated successfully: {user_info['email']}")
            
            return user_id
            
        except Exception as e:
            logger.error(f"Error handling auth callback: {e}")
            raise
    
    def _get_user_info_from_credentials(self, credentials: Credentials) -> Dict[str, Any]:
        """Get user information from Google credentials"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            return {
                'id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'given_name': user_info.get('given_name'),
                'family_name': user_info.get('family_name'),
                'picture': user_info.get('picture'),
                'locale': user_info.get('locale')
            }
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise
    
    def _generate_user_id(self, email: str) -> str:
        """Generate consistent user ID from email"""
        return hashlib.sha256(email.encode()).hexdigest()[:16]
    
    def get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get user credentials by user ID"""
        credentials = self.user_credentials.get(user_id)
        
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                self._save_sessions()
                logger.info(f"Refreshed credentials for user: {user_id}")
            except Exception as e:
                logger.error(f"Error refreshing credentials for user {user_id}: {e}")
                return None
        
        return credentials
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information by user ID"""
        if user_id in self.user_info_cache:
            return self.user_info_cache[user_id]
        
        # Try to get from session data
        session = self.active_sessions.get(user_id)
        if session:
            return {
                'email': session.get('email'),
                'name': session.get('name'),
                'picture': session.get('picture')
            }
        
        return None
    
    def is_user_authenticated(self, user_id: str) -> bool:
        """Check if user is authenticated"""
        if user_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[user_id]
        if not self._validate_session(session):
            self.revoke_user_access(user_id)
            return False
        
        # Update last activity
        session['last_activity'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
        self._save_sessions()
        
        return True
    
    def revoke_user_access(self, user_id: str) -> bool:
        """Revoke user access and cleanup session"""
        try:
            # Remove from active sessions
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
            
            # Remove credentials
            if user_id in self.user_credentials:
                del self.user_credentials[user_id]
            
            # Remove from cache
            if user_id in self.user_info_cache:
                del self.user_info_cache[user_id]
            
            # Save updated sessions
            self._save_sessions()
            
            logger.info(f"Revoked access for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking access for user {user_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions"""
        expired_users = []
        
        for user_id, session_data in self.active_sessions.items():
            if not self._validate_session(session_data):
                expired_users.append(user_id)
        
        for user_id in expired_users:
            self.revoke_user_access(user_id)
        
        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired sessions")
        
        return len(expired_users)
    
    def list_authenticated_users(self) -> List[Dict[str, Any]]:
        """Get list of authenticated users"""
        users = []
        
        for user_id, session_data in self.active_sessions.items():
            if self._validate_session(session_data):
                users.append({
                    'user_id': user_id,
                    'email': session_data.get('email'),
                    'name': session_data.get('name'),
                    'created_at': session_data.get('created_at'),
                    'last_activity': session_data.get('last_activity')
                })
        
        return users
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication system status"""
        return {
            'total_sessions': len(self.active_sessions),
            'active_users': len([s for s in self.active_sessions.values() if self._validate_session(s)]),
            'credentials_file_exists': os.path.exists(self.credentials_path),
            'auth_data_dir': str(self.auth_data_dir),
            'scopes': self.scopes
        }

# Global authentication manager
google_auth_manager = GoogleAuthManager()
