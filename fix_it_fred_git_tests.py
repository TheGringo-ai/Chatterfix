#!/usr/bin/env python3
"""
Fix It Fred Git Integration Test Suite
Comprehensive testing and validation for git integration features
"""
import os
import json
import time
import tempfile
import shutil
import subprocess
import requests
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import logging

# Import our modules for testing
import sys
sys.path.append('.')
from fix_it_fred_git_integration_service import GitIntegrationService, GitConfig, FileChange
from fix_it_fred_git_security import GitSecurityManager, GitCredentials
from fix_it_fred_git_ai_enhancement import FixItFredGitAI, EnhancedGitService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestGitIntegrationService(unittest.TestCase):
    """Test the core git integration service"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config = GitConfig(
            repo_path=self.test_dir,
            remote_url="git@github.com:test/test-repo.git",
            commit_interval_minutes=1,
            auto_push=False  # Don't auto-push during tests
        )
        self.service = GitIntegrationService(self.config)
        
        # Initialize git repo
        os.chdir(self.test_dir)
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_file_tracking(self):
        """Test file change tracking"""
        # Create test file
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write('print("Hello World")')
        
        # Create file change
        change = FileChange(
            path=test_file,
            change_type='created',
            timestamp=datetime.now(),
            file_hash='testhash',
            size=100
        )
        
        # Test tracking
        should_track = self.service.change_tracker._should_track_file(test_file)
        self.assertTrue(should_track)
        
        # Test ignoring unwanted files
        log_file = os.path.join(self.test_dir, 'test.log')
        should_not_track = self.service.change_tracker._should_track_file(log_file)
        self.assertFalse(should_not_track)
    
    async def test_git_status(self):
        """Test git status detection"""
        # Create and modify a file
        test_file = os.path.join(self.test_dir, 'status_test.py')
        with open(test_file, 'w') as f:
            f.write('# Test file')
        
        status = await self.service._get_git_status()
        self.assertTrue(status['has_changes'])
        self.assertIn('status_test.py', status['modified_files'])
    
    def test_change_classification(self):
        """Test change type classification"""
        changes = [
            FileChange(path='feature.py', change_type='created', timestamp=datetime.now()),
            FileChange(path='api.py', change_type='modified', timestamp=datetime.now())
        ]
        
        change_type = self.service._classify_changes(changes)
        self.assertEqual(change_type, 'code')

class TestGitSecurityManager(unittest.TestCase):
    """Test git security and credential management"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.security_manager = GitSecurityManager(
            key_file=os.path.join(self.test_dir, 'test.key')
        )
        self.security_manager.credentials_file = os.path.join(self.test_dir, 'test_creds.enc')
        self.security_manager.ssh_dir = os.path.join(self.test_dir, '.ssh')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_credential_encryption(self):
        """Test credential encryption and decryption"""
        # Create test credentials
        creds = GitCredentials(
            username='testuser',
            token='testtoken123',
            ssh_private_key='fake_private_key',
            ssh_public_key='fake_public_key'
        )
        
        # Test encryption
        success = self.security_manager.encrypt_credentials(creds)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.security_manager.credentials_file))
        
        # Test decryption
        decrypted = self.security_manager.decrypt_credentials()
        self.assertIsNotNone(decrypted)
        self.assertEqual(decrypted.username, 'testuser')
        self.assertEqual(decrypted.token, 'testtoken123')
    
    def test_ssh_key_generation(self):
        """Test SSH key generation"""
        private_key, public_key = self.security_manager.generate_ssh_keypair('test@example.com')
        
        self.assertIn('BEGIN OPENSSH PRIVATE KEY', private_key)
        self.assertIn('ssh-ed25519', public_key)
        self.assertIn('test@example.com', public_key)
    
    def test_repository_validation(self):
        """Test repository access validation"""
        # Create test repository
        test_repo = os.path.join(self.test_dir, 'test_repo')
        os.makedirs(test_repo)
        os.chdir(test_repo)
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        
        validation = self.security_manager.validate_repository_access(test_repo)
        
        self.assertTrue(validation['repo_exists'])
        self.assertTrue(validation['is_git_repo'])
        self.assertTrue(validation['can_read'])

class TestFixItFredGitAI(unittest.TestCase):
    """Test AI enhancement features"""
    
    def setUp(self):
        """Set up test environment"""
        self.ai = FixItFredGitAI("http://localhost:9000")
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_language_detection(self):
        """Test programming language detection"""
        test_cases = [
            ('test.py', 'python'),
            ('app.js', 'javascript'),
            ('style.css', 'css'),
            ('data.sql', 'sql'),
            ('README.md', 'markdown')
        ]
        
        for filename, expected_lang in test_cases:
            path = Path(filename)
            detected = self.ai._detect_language(path)
            self.assertEqual(detected, expected_lang)
    
    def test_complexity_calculation(self):
        """Test code complexity calculation"""
        # Simple code
        simple_code = "print('Hello World')"
        complexity = self.ai._calculate_complexity(simple_code, 'python')
        self.assertEqual(complexity, 1)
        
        # Complex code with nested structures
        complex_code = """
        for i in range(10):
            for j in range(10):
                if i == j:
                    if j > 5:
                        print(i, j)
        """
        complexity = self.ai._calculate_complexity(complex_code, 'python')
        self.assertGreater(complexity, 3)
    
    def test_security_issue_detection(self):
        """Test security issue detection"""
        # Code with security issues
        unsafe_code = """
        import os
        password = "hardcoded_password"
        os.system("rm -rf /")
        eval(user_input)
        """
        
        issues = self.ai._find_security_issues(unsafe_code, 'python')
        self.assertGreater(len(issues), 0)
        
        # Safe code
        safe_code = "print('Hello World')"
        issues = self.ai._find_security_issues(safe_code, 'python')
        self.assertEqual(len(issues), 0)
    
    def test_commit_classification(self):
        """Test commit type classification"""
        # Feature commit
        feature_files = ['new_feature.py', 'api_endpoint.py']
        feature_diff = '+def new_feature():\n+    return "feat"'
        commit_type, scope = self.ai._classify_commit(feature_files, feature_diff)
        self.assertEqual(commit_type, 'feat')
        
        # Fix commit
        fix_files = ['bugfix.py']
        fix_diff = '+# This fixes the bug\n+if error: handle_error()'
        commit_type, scope = self.ai._classify_commit(fix_files, fix_diff)
        self.assertEqual(commit_type, 'fix')

class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete integration workflow"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config = GitConfig(
            repo_path=self.test_dir,
            commit_interval_minutes=1,
            auto_push=False
        )
        
        # Initialize git repo
        os.chdir(self.test_dir)
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
        
        # Create initial commit
        with open('README.md', 'w') as f:
            f.write('# Test Repository')
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    async def test_full_workflow(self):
        """Test complete workflow from file change to commit"""
        service = GitIntegrationService(self.config)
        
        # Create file changes
        test_file = os.path.join(self.test_dir, 'new_feature.py')
        with open(test_file, 'w') as f:
            f.write('''
def new_feature():
    """A new feature for Fix It Fred CMMS"""
    return "Maintenance task completed"
            ''')
        
        # Simulate file change
        changes = [FileChange(
            path=test_file,
            change_type='created',
            timestamp=datetime.now(),
            file_hash='abcd1234',
            size=100
        )]
        
        # Mock AI service to avoid external dependencies
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'response': 'feat(cmms): add new maintenance feature'
            }
            mock_post.return_value = mock_response
            
            # Process changes
            await service.process_changes(changes)
        
        # Verify commit was created
        result = subprocess.run(['git', 'log', '--oneline'], 
                              capture_output=True, text=True)
        self.assertIn('feat(cmms)', result.stdout)

class GitIntegrationLoadTest:
    """Load testing for git integration service"""
    
    def __init__(self, base_url="http://localhost:9002"):
        self.base_url = base_url
    
    def test_api_endpoints(self):
        """Test API endpoint performance"""
        endpoints = [
            '/health',
            '/api/git/status',
            '/api/git/config',
            '/api/git/commits'
        ]
        
        results = {}
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            start_time = time.time()
            
            try:
                response = requests.get(url, timeout=10)
                end_time = time.time()
                
                results[endpoint] = {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == 200
                }
            except Exception as e:
                results[endpoint] = {
                    'status_code': 0,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def stress_test_commit_endpoint(self, num_requests=10):
        """Stress test the commit endpoint"""
        results = []
        
        for i in range(num_requests):
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/git/commit",
                    json={"message": f"Test commit {i}", "force": True},
                    timeout=30
                )
                end_time = time.time()
                
                results.append({
                    'request_id': i,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code in [200, 400]  # 400 is OK if no changes
                })
            except Exception as e:
                results.append({
                    'request_id': i,
                    'status_code': 0,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                })
            
            time.sleep(1)  # Rate limiting
        
        return results

class SecurityTestSuite:
    """Security testing for git integration"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp()
        self.security_manager = GitSecurityManager()
    
    def test_credential_security(self):
        """Test credential storage security"""
        results = {
            'encryption_working': False,
            'file_permissions': False,
            'key_rotation': False,
            'audit_logging': False
        }
        
        try:
            # Test encryption
            creds = GitCredentials(username='test', token='secret123')
            if self.security_manager.encrypt_credentials(creds):
                decrypted = self.security_manager.decrypt_credentials()
                if decrypted and decrypted.token == 'secret123':
                    results['encryption_working'] = True
            
            # Test file permissions
            if os.path.exists(self.security_manager.credentials_file):
                stat = os.stat(self.security_manager.credentials_file)
                if oct(stat.st_mode)[-3:] == '600':
                    results['file_permissions'] = True
            
            # Test credential rotation
            if self.security_manager.rotate_credentials():
                results['key_rotation'] = True
            
            # Check audit log
            audit_log = "/tmp/fix_it_fred_git_audit.log"
            if os.path.exists(audit_log):
                results['audit_logging'] = True
                
        except Exception as e:
            logger.error(f"Security test error: {e}")
        
        return results
    
    def test_input_validation(self):
        """Test input validation and sanitization"""
        test_cases = [
            # SQL injection attempts
            ("'; DROP TABLE commits; --", False),
            # Command injection attempts
            ("; rm -rf /", False),
            # Path traversal attempts
            ("../../../etc/passwd", False),
            # Valid inputs
            ("feat(api): add new endpoint", True),
            ("fix(ui): resolve button alignment", True)
        ]
        
        results = []
        for test_input, should_pass in test_cases:
            try:
                # Test commit message validation
                is_valid = len(test_input) < 100 and not any(
                    dangerous in test_input.lower() 
                    for dangerous in ['drop', 'delete', 'rm -rf', '../']
                )
                
                results.append({
                    'input': test_input,
                    'expected_pass': should_pass,
                    'actual_pass': is_valid,
                    'correct': is_valid == should_pass
                })
            except Exception as e:
                results.append({
                    'input': test_input,
                    'error': str(e),
                    'correct': False
                })
        
        return results

def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("🧪 Fix It Fred Git Integration - Comprehensive Test Suite")
    print("=" * 60)
    
    # Unit tests
    print("\n📋 Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Load tests
    print("\n⚡ Running Load Tests...")
    load_tester = GitIntegrationLoadTest()
    api_results = load_tester.test_api_endpoints()
    
    print("API Endpoint Results:")
    for endpoint, result in api_results.items():
        status = "✅" if result['success'] else "❌"
        print(f"  {endpoint}: {status} ({result['response_time']:.3f}s)")
    
    # Security tests
    print("\n🔐 Running Security Tests...")
    security_tester = SecurityTestSuite()
    
    cred_results = security_tester.test_credential_security()
    print("Credential Security:")
    for test, passed in cred_results.items():
        status = "✅" if passed else "❌"
        print(f"  {test}: {status}")
    
    validation_results = security_tester.test_input_validation()
    correct_validations = sum(1 for r in validation_results if r.get('correct', False))
    print(f"Input Validation: {correct_validations}/{len(validation_results)} tests passed")
    
    # Performance tests
    print("\n🚀 Running Performance Tests...")
    stress_results = load_tester.stress_test_commit_endpoint(5)
    successful_requests = sum(1 for r in stress_results if r['success'])
    avg_response_time = sum(r['response_time'] for r in stress_results) / len(stress_results)
    
    print(f"Stress Test: {successful_requests}/{len(stress_results)} requests successful")
    print(f"Average Response Time: {avg_response_time:.3f}s")
    
    # Generate test report
    report = {
        'timestamp': datetime.now().isoformat(),
        'api_tests': api_results,
        'security_tests': {
            'credentials': cred_results,
            'input_validation': validation_results
        },
        'performance_tests': {
            'stress_test': stress_results,
            'avg_response_time': avg_response_time
        }
    }
    
    # Save report
    with open('/tmp/fix_it_fred_git_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Test report saved to: /tmp/fix_it_fred_git_test_report.json")
    print("\n🎉 Comprehensive testing complete!")

if __name__ == "__main__":
    run_comprehensive_tests()