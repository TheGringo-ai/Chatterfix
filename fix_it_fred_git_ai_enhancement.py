#!/usr/bin/env python3
"""
Fix It Fred Git AI Enhancement
Advanced AI capabilities for intelligent git operations and code analysis
"""
import os
import json
import re
import ast
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import requests
import logging

logger = logging.getLogger(__name__)

@dataclass
class CodeAnalysis:
    """Code analysis results"""
    file_path: str
    language: str
    complexity_score: int
    quality_issues: List[str]
    security_concerns: List[str]
    maintainability_score: int
    test_coverage_estimated: float
    dependencies: List[str]

@dataclass
class CommitAnalysis:
    """Comprehensive commit analysis"""
    commit_type: str  # feat, fix, refactor, docs, style, test, chore
    scope: str
    breaking_change: bool
    risk_assessment: str  # low, medium, high, critical
    quality_score: int  # 1-10
    recommended_message: str
    deployment_impact: str
    rollback_plan: str
    testing_recommendations: List[str]

class FixItFredGitAI:
    """Enhanced AI capabilities for git operations"""
    
    def __init__(self, fix_it_fred_url: str = "http://localhost:9000"):
        self.fix_it_fred_url = fix_it_fred_url
        self.code_patterns = self._load_code_patterns()
        self.cmms_context = self._load_cmms_context()
        
    def _load_code_patterns(self) -> Dict[str, Any]:
        """Load code pattern recognition rules"""
        return {
            'python': {
                'complexity_indicators': [
                    r'for.*for.*for',  # Nested loops
                    r'if.*if.*if',     # Nested conditions
                    r'try.*except.*finally',  # Exception handling
                    r'class.*\(.*\):',  # Class inheritance
                ],
                'quality_patterns': [
                    r'TODO|FIXME|HACK',  # Code debt
                    r'print\(',          # Debug statements
                    r'import \*',        # Wild imports
                ],
                'security_patterns': [
                    r'eval\(',
                    r'exec\(',
                    r'subprocess\.call',
                    r'os\.system',
                    r'sql.*\+.*\+',     # SQL injection risk
                ]
            },
            'javascript': {
                'complexity_indicators': [
                    r'function.*function.*function',
                    r'if.*if.*if',
                    r'for.*for.*for',
                ],
                'quality_patterns': [
                    r'console\.log',
                    r'alert\(',
                    r'document\.write',
                ],
                'security_patterns': [
                    r'eval\(',
                    r'innerHTML\s*=',
                    r'document\.cookie',
                ]
            }
        }
    
    def _load_cmms_context(self) -> Dict[str, Any]:
        """Load CMMS-specific context for better analysis"""
        return {
            'critical_systems': [
                'work_orders', 'assets', 'parts', 'maintenance', 
                'database', 'authentication', 'api', 'security'
            ],
            'business_impact_files': [
                'app.py', 'main.py', 'api.py', 'database.py',
                'auth.py', 'models.py', 'services.py'
            ],
            'deployment_files': [
                'Dockerfile', 'docker-compose.yml', 'requirements.txt',
                'package.json', '.env', 'startup.sh'
            ]
        }
    
    async def analyze_code_changes(self, file_paths: List[str]) -> List[CodeAnalysis]:
        """Analyze code changes with AI assistance"""
        analyses = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            try:
                analysis = await self._analyze_single_file(file_path)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
        
        return analyses
    
    async def _analyze_single_file(self, file_path: str) -> CodeAnalysis:
        """Analyze a single file"""
        path = Path(file_path)
        language = self._detect_language(path)
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Basic analysis
        complexity_score = self._calculate_complexity(content, language)
        quality_issues = self._find_quality_issues(content, language)
        security_concerns = self._find_security_issues(content, language)
        maintainability_score = self._calculate_maintainability(content, language)
        dependencies = self._extract_dependencies(content, language)
        
        # AI-enhanced analysis
        ai_insights = await self._get_ai_code_insights(file_path, content, language)
        
        return CodeAnalysis(
            file_path=file_path,
            language=language,
            complexity_score=complexity_score,
            quality_issues=quality_issues + ai_insights.get('quality_issues', []),
            security_concerns=security_concerns + ai_insights.get('security_concerns', []),
            maintainability_score=maintainability_score,
            test_coverage_estimated=ai_insights.get('test_coverage', 0.0),
            dependencies=dependencies
        )
    
    def _detect_language(self, path: Path) -> str:
        """Detect programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'bash',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.md': 'markdown'
        }
        return extension_map.get(path.suffix.lower(), 'text')
    
    def _calculate_complexity(self, content: str, language: str) -> int:
        """Calculate code complexity score (1-10)"""
        if language not in self.code_patterns:
            return 1
        
        patterns = self.code_patterns[language]['complexity_indicators']
        complexity = 1
        
        for pattern in patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            complexity += matches
        
        # Additional complexity factors
        lines = content.count('\n')
        if lines > 500:
            complexity += 2
        elif lines > 200:
            complexity += 1
        
        return min(complexity, 10)
    
    def _find_quality_issues(self, content: str, language: str) -> List[str]:
        """Find code quality issues"""
        issues = []
        
        if language not in self.code_patterns:
            return issues
        
        patterns = self.code_patterns[language]['quality_patterns']
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                issues.append(f"Quality issue: {pattern} found {len(matches)} times")
        
        # Check line length
        long_lines = [i for i, line in enumerate(content.split('\n'), 1) 
                     if len(line) > 120]
        if long_lines:
            issues.append(f"Long lines found at: {long_lines[:5]}")
        
        return issues
    
    def _find_security_issues(self, content: str, language: str) -> List[str]:
        """Find potential security issues"""
        concerns = []
        
        if language not in self.code_patterns:
            return concerns
        
        patterns = self.code_patterns[language]['security_patterns']
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                concerns.append(f"Security concern: {pattern} usage detected")
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                concerns.append("Potential hardcoded secret detected")
        
        return concerns
    
    def _calculate_maintainability(self, content: str, language: str) -> int:
        """Calculate maintainability score (1-10)"""
        score = 10
        
        # Penalty for long functions/classes
        if language == 'python':
            functions = re.findall(r'def\s+\w+.*?(?=\ndef|\nclass|\n\S|\Z)', 
                                 content, re.DOTALL)
            long_functions = [f for f in functions if f.count('\n') > 50]
            score -= len(long_functions)
        
        # Penalty for lack of comments
        comment_ratio = len(re.findall(r'#.*|//.*|/\*.*?\*/', content)) / max(content.count('\n'), 1)
        if comment_ratio < 0.1:
            score -= 2
        
        # Penalty for code duplication (simple check)
        lines = content.split('\n')
        duplicate_lines = len(lines) - len(set(lines))
        if duplicate_lines > 10:
            score -= 1
        
        return max(score, 1)
    
    def _extract_dependencies(self, content: str, language: str) -> List[str]:
        """Extract dependencies from code"""
        dependencies = []
        
        if language == 'python':
            # Extract imports
            import_patterns = [
                r'import\s+(\w+)',
                r'from\s+(\w+)\s+import',
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
        
        elif language == 'javascript':
            # Extract requires and imports
            import_patterns = [
                r'require\(["\']([^"\']+)["\']\)',
                r'import.*from\s+["\']([^"\']+)["\']',
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
        
        return list(set(dependencies))
    
    async def _get_ai_code_insights(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """Get AI insights about code quality and issues"""
        try:
            # Truncate content for AI analysis (to avoid token limits)
            truncated_content = content[:2000] if len(content) > 2000 else content
            
            prompt = f"""
            Analyze this {language} code from {file_path} for Fix It Fred CMMS system:
            
            ```{language}
            {truncated_content}
            ```
            
            Provide analysis for:
            1. Code quality issues
            2. Security concerns
            3. Estimated test coverage (0.0-1.0)
            4. CMMS-specific considerations
            5. Improvement recommendations
            
            Focus on maintenance management system requirements.
            Respond in JSON format.
            """
            
            response = requests.post(f"{self.fix_it_fred_url}/api/chat",
                                   json={
                                       "message": prompt,
                                       "context": "Code analysis",
                                       "provider": "ollama",
                                       "model": "mistral:7b"
                                   }, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json().get('response', '')
                # Try to extract structured data from AI response
                return self._parse_ai_insights(ai_response)
            
        except Exception as e:
            logger.error(f"AI code insights error: {e}")
        
        return {'quality_issues': [], 'security_concerns': [], 'test_coverage': 0.5}
    
    def _parse_ai_insights(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response for structured insights"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback parsing
        insights = {'quality_issues': [], 'security_concerns': [], 'test_coverage': 0.5}
        
        if 'quality' in ai_response.lower():
            insights['quality_issues'].append("AI detected potential quality issues")
        if 'security' in ai_response.lower():
            insights['security_concerns'].append("AI detected potential security concerns")
        if 'test' in ai_response.lower():
            insights['test_coverage'] = 0.7
        
        return insights
    
    async def generate_intelligent_commit_message(self, 
                                                file_changes: List[str], 
                                                git_diff: str) -> CommitAnalysis:
        """Generate intelligent commit message with comprehensive analysis"""
        
        # Analyze changed files
        code_analyses = await self.analyze_code_changes(file_changes)
        
        # Determine commit type and scope
        commit_type, scope = self._classify_commit(file_changes, git_diff)
        
        # Assess risk and impact
        risk_assessment = self._assess_risk(code_analyses, file_changes)
        breaking_change = self._detect_breaking_changes(git_diff)
        
        # Generate AI-powered commit message
        ai_message = await self._generate_ai_commit_message(
            file_changes, git_diff, commit_type, scope, risk_assessment
        )
        
        # Calculate quality score
        quality_score = self._calculate_commit_quality(code_analyses, ai_message)
        
        # Generate deployment and testing recommendations
        deployment_impact = self._assess_deployment_impact(file_changes, code_analyses)
        rollback_plan = self._generate_rollback_plan(commit_type, scope, file_changes)
        testing_recommendations = self._generate_testing_recommendations(code_analyses, commit_type)
        
        return CommitAnalysis(
            commit_type=commit_type,
            scope=scope,
            breaking_change=breaking_change,
            risk_assessment=risk_assessment,
            quality_score=quality_score,
            recommended_message=ai_message,
            deployment_impact=deployment_impact,
            rollback_plan=rollback_plan,
            testing_recommendations=testing_recommendations
        )
    
    def _classify_commit(self, file_changes: List[str], git_diff: str) -> Tuple[str, str]:
        """Classify commit type and scope"""
        # Analyze file patterns
        has_features = any('feat' in diff_line for diff_line in git_diff.split('\n') if diff_line.startswith('+'))
        has_fixes = any('fix' in diff_line or 'bug' in diff_line for diff_line in git_diff.split('\n') if diff_line.startswith('+'))
        has_docs = any(f.endswith('.md') for f in file_changes)
        has_tests = any('test' in f for f in file_changes)
        has_config = any(f in ['Dockerfile', 'requirements.txt', '.env', 'docker-compose.yml'] for f in file_changes)
        
        # Determine commit type
        if has_features:
            commit_type = 'feat'
        elif has_fixes:
            commit_type = 'fix'
        elif has_docs:
            commit_type = 'docs'
        elif has_tests:
            commit_type = 'test'
        elif has_config:
            commit_type = 'chore'
        else:
            commit_type = 'refactor'
        
        # Determine scope
        if any('ai' in f.lower() or 'fred' in f.lower() for f in file_changes):
            scope = 'ai'
        elif any('git' in f.lower() for f in file_changes):
            scope = 'git'
        elif any('auth' in f.lower() or 'security' in f.lower() for f in file_changes):
            scope = 'security'
        elif any('api' in f.lower() for f in file_changes):
            scope = 'api'
        elif any('ui' in f.lower() or 'frontend' in f.lower() for f in file_changes):
            scope = 'ui'
        else:
            scope = 'core'
        
        return commit_type, scope
    
    def _assess_risk(self, code_analyses: List[CodeAnalysis], file_changes: List[str]) -> str:
        """Assess risk level of changes"""
        max_complexity = max([a.complexity_score for a in code_analyses], default=1)
        security_issues = sum(len(a.security_concerns) for a in code_analyses)
        
        # Check for critical system changes
        critical_changes = any(
            any(critical in f.lower() for critical in self.cmms_context['critical_systems'])
            for f in file_changes
        )
        
        business_impact_changes = any(
            any(f.endswith(business_file) for business_file in self.cmms_context['business_impact_files'])
            for f in file_changes
        )
        
        if security_issues > 0 or critical_changes:
            return 'high'
        elif max_complexity > 7 or business_impact_changes:
            return 'medium'
        else:
            return 'low'
    
    def _detect_breaking_changes(self, git_diff: str) -> bool:
        """Detect if changes might be breaking"""
        breaking_patterns = [
            r'-\s*def\s+\w+',      # Function removal
            r'-\s*class\s+\w+',    # Class removal
            r'-\s*@app\.route',    # API endpoint removal
            r'BREAKING CHANGE',     # Explicit breaking change
        ]
        
        for pattern in breaking_patterns:
            if re.search(pattern, git_diff, re.MULTILINE):
                return True
        
        return False
    
    async def _generate_ai_commit_message(self, file_changes: List[str], 
                                        git_diff: str, commit_type: str, 
                                        scope: str, risk_assessment: str) -> str:
        """Generate AI-powered commit message"""
        try:
            # Truncate diff for AI processing
            truncated_diff = git_diff[:1500] if len(git_diff) > 1500 else git_diff
            
            prompt = f"""
            Generate a professional git commit message for Fix It Fred CMMS system:
            
            Commit Type: {commit_type}
            Scope: {scope}
            Risk Level: {risk_assessment}
            Files Changed: {', '.join(file_changes[:5])}
            
            Git Diff (partial):
            {truncated_diff}
            
            Requirements:
            1. Follow conventional commits format: type(scope): description
            2. Keep under 72 characters for the first line
            3. Be specific about CMMS functionality
            4. Include impact on maintenance operations
            
            Examples:
            - feat(ai): add real-time commit analysis for Fix It Fred
            - fix(api): resolve work order creation endpoint error
            - refactor(security): improve git credential encryption
            
            Generate only the commit message, no explanation.
            """
            
            response = requests.post(f"{self.fix_it_fred_url}/api/chat",
                                   json={
                                       "message": prompt,
                                       "context": "Commit message generation",
                                       "provider": "ollama",
                                       "model": "mistral:7b"
                                   }, timeout=20)
            
            if response.status_code == 200:
                ai_message = response.json().get('response', '').strip()
                # Clean up AI response
                if ai_message and len(ai_message) < 100:
                    return ai_message
            
        except Exception as e:
            logger.error(f"AI commit message generation error: {e}")
        
        # Fallback message
        return f"{commit_type}({scope}): update {len(file_changes)} files"
    
    def _calculate_commit_quality(self, code_analyses: List[CodeAnalysis], commit_message: str) -> int:
        """Calculate overall commit quality score (1-10)"""
        score = 10
        
        # Penalty for complexity
        avg_complexity = sum(a.complexity_score for a in code_analyses) / max(len(code_analyses), 1)
        if avg_complexity > 7:
            score -= 2
        elif avg_complexity > 5:
            score -= 1
        
        # Penalty for security issues
        total_security_issues = sum(len(a.security_concerns) for a in code_analyses)
        score -= min(total_security_issues, 3)
        
        # Penalty for quality issues
        total_quality_issues = sum(len(a.quality_issues) for a in code_analyses)
        score -= min(total_quality_issues // 2, 2)
        
        # Bonus for good commit message
        if len(commit_message) < 72 and ':' in commit_message:
            score += 1
        
        return max(score, 1)
    
    def _assess_deployment_impact(self, file_changes: List[str], code_analyses: List[CodeAnalysis]) -> str:
        """Assess deployment impact"""
        deployment_files = self.cmms_context['deployment_files']
        
        if any(f in deployment_files for f in file_changes):
            return "Requires infrastructure restart and validation"
        elif any('database' in f.lower() or 'migration' in f.lower() for f in file_changes):
            return "Database changes - requires backup and migration"
        elif any(a.complexity_score > 7 for a in code_analyses):
            return "Complex changes - requires thorough testing"
        else:
            return "Standard deployment - minimal impact expected"
    
    def _generate_rollback_plan(self, commit_type: str, scope: str, file_changes: List[str]) -> str:
        """Generate rollback plan"""
        if commit_type == 'feat':
            return f"Rollback: Revert {scope} feature changes, test core functionality"
        elif commit_type == 'fix':
            return f"Rollback: Restore previous version, monitor for original issue"
        elif scope == 'security':
            return "Rollback: Immediate revert required, security review needed"
        else:
            return f"Rollback: Standard git revert, verify {scope} functionality"
    
    def _generate_testing_recommendations(self, code_analyses: List[CodeAnalysis], 
                                        commit_type: str) -> List[str]:
        """Generate testing recommendations"""
        recommendations = []
        
        # Based on commit type
        if commit_type == 'feat':
            recommendations.append("Test new feature functionality thoroughly")
            recommendations.append("Verify integration with existing CMMS workflows")
        elif commit_type == 'fix':
            recommendations.append("Verify bug fix resolves reported issue")
            recommendations.append("Test regression scenarios")
        
        # Based on code analysis
        if any(a.complexity_score > 7 for a in code_analyses):
            recommendations.append("Perform unit tests for complex logic")
        
        if any(len(a.security_concerns) > 0 for a in code_analyses):
            recommendations.append("Security testing required")
            recommendations.append("Penetration testing recommended")
        
        # CMMS-specific tests
        recommendations.append("Test work order creation and updates")
        recommendations.append("Verify parts inventory tracking")
        recommendations.append("Validate asset management functionality")
        
        return recommendations

# Integration with existing git service
class EnhancedGitService:
    """Enhanced git service with AI capabilities"""
    
    def __init__(self, fix_it_fred_url: str = "http://localhost:9000"):
        self.ai = FixItFredGitAI(fix_it_fred_url)
    
    async def analyze_and_commit(self, file_changes: List[str], git_diff: str) -> Dict[str, Any]:
        """Analyze changes and create intelligent commit"""
        # Get comprehensive analysis
        commit_analysis = await self.ai.generate_intelligent_commit_message(file_changes, git_diff)
        
        # Create commit recommendation
        recommendation = {
            'should_commit': commit_analysis.quality_score >= 7,
            'commit_message': commit_analysis.recommended_message,
            'risk_level': commit_analysis.risk_assessment,
            'quality_score': commit_analysis.quality_score,
            'deployment_impact': commit_analysis.deployment_impact,
            'rollback_plan': commit_analysis.rollback_plan,
            'testing_recommendations': commit_analysis.testing_recommendations,
            'breaking_change': commit_analysis.breaking_change
        }
        
        return recommendation
    
    async def pre_commit_review(self, file_paths: List[str]) -> Dict[str, Any]:
        """Perform pre-commit code review"""
        code_analyses = await self.ai.analyze_code_changes(file_paths)
        
        # Aggregate results
        total_quality_issues = sum(len(a.quality_issues) for a in code_analyses)
        total_security_concerns = sum(len(a.security_concerns) for a in code_analyses)
        avg_complexity = sum(a.complexity_score for a in code_analyses) / max(len(code_analyses), 1)
        avg_maintainability = sum(a.maintainability_score for a in code_analyses) / max(len(code_analyses), 1)
        
        # Determine if commit should proceed
        should_commit = (
            total_security_concerns == 0 and
            total_quality_issues < 5 and
            avg_complexity <= 8
        )
        
        return {
            'should_commit': should_commit,
            'quality_issues': total_quality_issues,
            'security_concerns': total_security_concerns,
            'complexity_score': avg_complexity,
            'maintainability_score': avg_maintainability,
            'file_analyses': [
                {
                    'file': a.file_path,
                    'language': a.language,
                    'complexity': a.complexity_score,
                    'issues': len(a.quality_issues) + len(a.security_concerns)
                }
                for a in code_analyses
            ],
            'recommendations': self._generate_commit_recommendations(code_analyses)
        }
    
    def _generate_commit_recommendations(self, analyses: List[CodeAnalysis]) -> List[str]:
        """Generate recommendations based on code analysis"""
        recommendations = []
        
        high_complexity_files = [a for a in analyses if a.complexity_score > 7]
        if high_complexity_files:
            recommendations.append(f"Consider refactoring high complexity files: {[a.file_path for a in high_complexity_files]}")
        
        security_issues = [a for a in analyses if a.security_concerns]
        if security_issues:
            recommendations.append("Address security concerns before committing")
        
        low_maintainability = [a for a in analyses if a.maintainability_score < 5]
        if low_maintainability:
            recommendations.append("Improve code maintainability with comments and refactoring")
        
        if not recommendations:
            recommendations.append("Code quality looks good - ready to commit")
        
        return recommendations