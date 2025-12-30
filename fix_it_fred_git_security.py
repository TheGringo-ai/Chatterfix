#!/usr/bin/env python3
"""
Fix It Fred Git Security Manager
Secure credential management and access control for git integration
"""
import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GitCredentials:
    """Secure git credentials container"""
    username: Optional[str] = None
    token: Optional[str] = None
    ssh_private_key: Optional[str] = None
    ssh_public_key: Optional[str] = None
    passphrase: Optional[str] = None
    
class GitSecurityManager:
    """Manages secure git operations and credential handling"""
    
    def __init__(self, key_file: str = "/tmp/fix_it_fred_git.key"):
        self.key_file = key_file
        self.credentials_file = "/tmp/fix_it_fred_git_creds.enc"
        self.ssh_dir = "/home/yoyofred_gringosgambit_com/.ssh"
        self.encryption_key = self._get_or_create_key()
        
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for credentials"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Secure key file permissions
        with open(self.key_file, 'wb') as f:
            f.write(key)
        os.chmod(self.key_file, 0o600)
        
        logger.info(f"Generated new encryption key: {self.key_file}")
        return key
    
    def encrypt_credentials(self, credentials: GitCredentials) -> bool:
        """Encrypt and store git credentials"""
        try:
            fernet = Fernet(self.encryption_key)
            
            # Serialize credentials
            cred_data = {
                'username': credentials.username,
                'token': credentials.token,
                'ssh_private_key': credentials.ssh_private_key,
                'ssh_public_key': credentials.ssh_public_key,
                'passphrase': credentials.passphrase
            }
            
            # Encrypt
            encrypted_data = fernet.encrypt(json.dumps(cred_data).encode())
            
            # Store securely
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.credentials_file, 0o600)
            
            logger.info("Git credentials encrypted and stored")
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            return False
    
    def decrypt_credentials(self) -> Optional[GitCredentials]:
        """Decrypt and load git credentials"""
        try:
            if not os.path.exists(self.credentials_file):
                return None
                
            fernet = Fernet(self.encryption_key)
            
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt
            decrypted_data = fernet.decrypt(encrypted_data)
            cred_data = json.loads(decrypted_data.decode())
            
            return GitCredentials(
                username=cred_data.get('username'),
                token=cred_data.get('token'),
                ssh_private_key=cred_data.get('ssh_private_key'),
                ssh_public_key=cred_data.get('ssh_public_key'),
                passphrase=cred_data.get('passphrase')
            )
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            return None
    
    def setup_ssh_keys(self, private_key: str, public_key: str, passphrase: Optional[str] = None) -> bool:
        """Setup SSH keys for git authentication"""
        try:
            # Ensure SSH directory exists
            os.makedirs(self.ssh_dir, mode=0o700, exist_ok=True)
            
            # Write private key
            private_key_path = os.path.join(self.ssh_dir, "fix_it_fred_git")
            with open(private_key_path, 'w') as f:
                f.write(private_key)
            os.chmod(private_key_path, 0o600)
            
            # Write public key
            public_key_path = os.path.join(self.ssh_dir, "fix_it_fred_git.pub")
            with open(public_key_path, 'w') as f:
                f.write(public_key)
            os.chmod(public_key_path, 0o644)
            
            # Update SSH config
            self._update_ssh_config()
            
            logger.info("SSH keys configured for git authentication")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup SSH keys: {e}")
            return False
    
    def _update_ssh_config(self):
        """Update SSH config for git operations"""
        ssh_config_path = os.path.join(self.ssh_dir, "config")
        
        config_entry = """
# Fix It Fred Git Integration
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/fix_it_fred_git
    IdentitiesOnly yes
    
Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/fix_it_fred_git
    IdentitiesOnly yes
"""
        
        # Check if config already has our entry
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, 'r') as f:
                content = f.read()
            if "Fix It Fred Git Integration" in content:
                return  # Already configured
        
        # Append our config
        with open(ssh_config_path, 'a') as f:
            f.write(config_entry)
        os.chmod(ssh_config_path, 0o600)
    
    def generate_ssh_keypair(self, email: str) -> tuple[str, str]:
        """Generate SSH key pair for git authentication"""
        try:
            key_path = "/tmp/fix_it_fred_temp_key"
            
            # Generate SSH key pair
            subprocess.run([
                'ssh-keygen', '-t', 'ed25519', '-C', email,
                '-f', key_path, '-N', ''
            ], check=True, capture_output=True)
            
            # Read keys
            with open(key_path, 'r') as f:
                private_key = f.read()
            with open(f"{key_path}.pub", 'r') as f:
                public_key = f.read()
            
            # Clean up temp files
            os.remove(key_path)
            os.remove(f"{key_path}.pub")
            
            logger.info("Generated new SSH key pair")
            return private_key, public_key
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate SSH key: {e}")
            raise
    
    def configure_git_with_token(self, repo_url: str, username: str, token: str) -> str:
        """Configure git remote URL with authentication token"""
        try:
            # Parse the repository URL
            if repo_url.startswith('https://github.com/'):
                auth_url = f"https://{username}:{token}@github.com/{repo_url.split('github.com/')[1]}"
            elif repo_url.startswith('https://gitlab.com/'):
                auth_url = f"https://{username}:{token}@gitlab.com/{repo_url.split('gitlab.com/')[1]}"
            else:
                # Generic HTTPS URL
                auth_url = repo_url.replace('https://', f'https://{username}:{token}@')
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to configure git URL: {e}")
            raise
    
    def test_git_authentication(self, repo_url: str, auth_method: str = "ssh") -> bool:
        """Test git authentication"""
        try:
            if auth_method == "ssh":
                # Test SSH connection
                host = "github.com" if "github.com" in repo_url else "gitlab.com"
                result = subprocess.run([
                    'ssh', '-T', f'git@{host}', '-o', 'ConnectTimeout=10'
                ], capture_output=True, text=True, timeout=15)
                
                # SSH test is successful if return code is 1 (not 255)
                return result.returncode in [0, 1]
                
            elif auth_method == "https":
                # Test HTTPS connection with ls-remote
                result = subprocess.run([
                    'git', 'ls-remote', '--heads', repo_url
                ], capture_output=True, text=True, timeout=15)
                
                return result.returncode == 0
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Git authentication test failed: {e}")
            return False
    
    def secure_git_operation(self, operation: callable, *args, **kwargs):
        """Execute git operation with security context"""
        try:
            # Set secure environment
            env = os.environ.copy()
            env['GIT_SSH_COMMAND'] = 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
            env['GIT_TERMINAL_PROMPT'] = '0'  # Disable interactive prompts
            
            # Execute operation
            return operation(*args, **kwargs, env=env)
            
        except Exception as e:
            logger.error(f"Secure git operation failed: {e}")
            raise
    
    def audit_git_access(self, operation: str, repo_path: str, result: bool):
        """Log git access for security auditing"""
        audit_log = "/tmp/fix_it_fred_git_audit.log"
        
        audit_entry = {
            'timestamp': os.time.time(),
            'operation': operation,
            'repo_path': repo_path,
            'result': 'success' if result else 'failure',
            'user': os.getenv('USER', 'unknown')
        }
        
        with open(audit_log, 'a') as f:
            f.write(f"{json.dumps(audit_entry)}\n")
    
    def rotate_credentials(self) -> bool:
        """Rotate git credentials for security"""
        try:
            # Load current credentials
            current_creds = self.decrypt_credentials()
            if not current_creds:
                logger.warning("No credentials to rotate")
                return False
            
            # Generate new SSH key if using SSH
            if current_creds.ssh_private_key:
                email = "fix-it-fred@chatterfix.com"
                private_key, public_key = self.generate_ssh_keypair(email)
                
                # Update credentials
                current_creds.ssh_private_key = private_key
                current_creds.ssh_public_key = public_key
                
                # Store updated credentials
                self.encrypt_credentials(current_creds)
                
                # Setup new SSH keys
                self.setup_ssh_keys(private_key, public_key)
                
                logger.info("Git SSH credentials rotated successfully")
                return True
            
            # For token-based auth, would need external token refresh
            logger.info("Token rotation requires manual intervention")
            return False
            
        except Exception as e:
            logger.error(f"Credential rotation failed: {e}")
            return False
    
    def validate_repository_access(self, repo_path: str) -> Dict[str, Any]:
        """Validate repository access and permissions"""
        validation_result = {
            'repo_exists': False,
            'is_git_repo': False,
            'has_remote': False,
            'can_read': False,
            'can_write': False,
            'branch_info': {},
            'security_issues': []
        }
        
        try:
            # Check if directory exists
            if not os.path.exists(repo_path):
                validation_result['security_issues'].append("Repository path does not exist")
                return validation_result
            validation_result['repo_exists'] = True
            
            # Check if it's a git repository
            git_dir = os.path.join(repo_path, '.git')
            if not os.path.exists(git_dir):
                validation_result['security_issues'].append("Not a git repository")
                return validation_result
            validation_result['is_git_repo'] = True
            
            # Change to repo directory
            original_cwd = os.getcwd()
            os.chdir(repo_path)
            
            try:
                # Check for remote
                result = subprocess.run(['git', 'remote', '-v'], 
                                      capture_output=True, text=True, check=True)
                validation_result['has_remote'] = len(result.stdout.strip()) > 0
                
                # Check read access
                result = subprocess.run(['git', 'status'], 
                                      capture_output=True, text=True, check=True)
                validation_result['can_read'] = True
                
                # Get branch info
                result = subprocess.run(['git', 'branch', '-v'], 
                                      capture_output=True, text=True, check=True)
                validation_result['branch_info']['local_branches'] = result.stdout.strip()
                
                # Check write access (try to add a test file)
                test_file = os.path.join(repo_path, '.fix_it_fred_test')
                with open(test_file, 'w') as f:
                    f.write("test")
                
                subprocess.run(['git', 'add', test_file], check=True, capture_output=True)
                subprocess.run(['git', 'reset', 'HEAD', test_file], check=True, capture_output=True)
                os.remove(test_file)
                validation_result['can_write'] = True
                
            except subprocess.CalledProcessError as e:
                validation_result['security_issues'].append(f"Git operation failed: {e}")
            finally:
                os.chdir(original_cwd)
            
            # Check file permissions
            if not os.access(repo_path, os.R_OK | os.W_OK):
                validation_result['security_issues'].append("Insufficient file system permissions")
            
        except Exception as e:
            validation_result['security_issues'].append(f"Validation error: {e}")
        
        return validation_result
    
    def cleanup_credentials(self):
        """Securely clean up credential files"""
        try:
            # Remove encrypted credentials
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
            
            # Remove encryption key
            if os.path.exists(self.key_file):
                os.remove(self.key_file)
            
            # Remove SSH keys
            ssh_private = os.path.join(self.ssh_dir, "fix_it_fred_git")
            ssh_public = os.path.join(self.ssh_dir, "fix_it_fred_git.pub")
            
            for key_file in [ssh_private, ssh_public]:
                if os.path.exists(key_file):
                    os.remove(key_file)
            
            logger.info("Git credentials cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Credential cleanup failed: {e}")

class GitSecurityPolicy:
    """Defines security policies for git operations"""
    
    @staticmethod
    def validate_commit_content(file_paths: list) -> Dict[str, Any]:
        """Validate commit content for security issues"""
        issues = []
        risk_level = "low"
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check for sensitive patterns
                sensitive_patterns = [
                    'password', 'secret', 'api_key', 'private_key',
                    'token', 'auth', 'credential', 'mysql://', 'postgresql://'
                ]
                
                for pattern in sensitive_patterns:
                    if pattern.lower() in content.lower():
                        issues.append(f"Potential sensitive data in {file_path}: {pattern}")
                        risk_level = "high"
                
                # Check file size (avoid committing large files)
                if len(content) > 1024 * 1024:  # 1MB
                    issues.append(f"Large file detected: {file_path}")
                    if risk_level == "low":
                        risk_level = "medium"
                        
            except Exception as e:
                issues.append(f"Could not analyze {file_path}: {e}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'risk_level': risk_level
        }
    
    @staticmethod
    def validate_repository_url(repo_url: str) -> bool:
        """Validate repository URL for security"""
        if not repo_url:
            return False
        
        # Allow only trusted domains
        trusted_domains = ['github.com', 'gitlab.com', 'bitbucket.org']
        
        for domain in trusted_domains:
            if domain in repo_url:
                return True
        
        # For enterprise repositories, check URL format
        if repo_url.startswith('https://') or repo_url.startswith('git@'):
            return True
        
        return False
    
    @staticmethod
    def get_security_recommendations() -> List[str]:
        """Get security recommendations for git integration"""
        return [
            "Use SSH keys instead of passwords for authentication",
            "Rotate credentials regularly (monthly recommended)",
            "Enable two-factor authentication on git provider",
            "Review commit content before pushing to remote",
            "Use dedicated service account for automated commits",
            "Monitor git operations for unusual activity",
            "Keep SSH keys encrypted with strong passphrases",
            "Restrict repository access to necessary personnel only"
        ]

# CLI tool for credential management
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix It Fred Git Security Manager")
    parser.add_argument('action', choices=['setup', 'test', 'rotate', 'cleanup', 'validate'])
    parser.add_argument('--repo-url', help='Repository URL')
    parser.add_argument('--repo-path', help='Repository path')
    parser.add_argument('--username', help='Git username')
    parser.add_argument('--token', help='Git token')
    parser.add_argument('--email', help='Email for SSH key generation')
    
    args = parser.parse_args()
    
    security_manager = GitSecurityManager()
    
    if args.action == 'setup':
        if args.username and args.token:
            # Setup with token
            credentials = GitCredentials(username=args.username, token=args.token)
            security_manager.encrypt_credentials(credentials)
            print("Credentials stored securely")
        elif args.email:
            # Setup with SSH
            private_key, public_key = security_manager.generate_ssh_keypair(args.email)
            credentials = GitCredentials(ssh_private_key=private_key, ssh_public_key=public_key)
            security_manager.encrypt_credentials(credentials)
            security_manager.setup_ssh_keys(private_key, public_key)
            print("SSH keys generated and configured")
            print("Add this public key to your git provider:")
            print(public_key)
        else:
            print("Please provide either --username and --token, or --email")
    
    elif args.action == 'test':
        if args.repo_url:
            auth_method = "ssh" if "git@" in args.repo_url else "https"
            success = security_manager.test_git_authentication(args.repo_url, auth_method)
            print(f"Authentication test: {'PASSED' if success else 'FAILED'}")
        else:
            print("Please provide --repo-url")
    
    elif args.action == 'rotate':
        success = security_manager.rotate_credentials()
        print(f"Credential rotation: {'SUCCESS' if success else 'FAILED'}")
    
    elif args.action == 'cleanup':
        security_manager.cleanup_credentials()
        print("Credentials cleaned up")
    
    elif args.action == 'validate':
        if args.repo_path:
            result = security_manager.validate_repository_access(args.repo_path)
            print(json.dumps(result, indent=2))
        else:
            print("Please provide --repo-path")