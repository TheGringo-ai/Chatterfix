"""
🧠 AI Memory System
Designed with AI Team collaboration to prevent coding mistakes and remember solutions

Features:
- API contract memory
- Parameter mapping patterns
- Integration debugging history
- Successful solution patterns
- Automatic learning from errors
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class APIContractMemory:
    """Memory for API contract information"""

    service_name: str
    endpoint: str
    expected_parameters: Dict[str, Any]
    response_format: Dict[str, Any]
    parameter_mappings: Dict[str, str]  # mapping from other service formats
    last_updated: str
    usage_count: int = 0
    success_rate: float = 1.0


@dataclass
class IntegrationError:
    """Memory for integration errors and their solutions"""

    error_id: str
    error_type: str  # "parameter_mismatch", "format_error", "timeout", etc.
    source_service: str
    target_service: str
    error_description: str
    original_request: Dict[str, Any]
    expected_format: Dict[str, Any]
    solution_applied: str
    resolution_time_minutes: float
    timestamp: str
    resolved: bool = True


@dataclass
class SuccessPattern:
    """Memory for successful integration patterns"""

    pattern_id: str
    pattern_type: str  # "data_transformation", "retry_logic", "fallback", etc.
    source_service: str
    target_service: str
    pattern_description: str
    implementation_code: str
    success_count: int
    last_used: str


class AIMemorySystem:
    """
    Comprehensive memory system for AI Services
    Designed with AI Team collaboration to prevent repeat mistakes
    """

    def __init__(self, memory_dir: str = "ai_memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)

        # Memory stores
        self.api_contracts: Dict[str, APIContractMemory] = {}
        self.integration_errors: Dict[str, IntegrationError] = {}
        self.success_patterns: Dict[str, SuccessPattern] = {}

        # Files
        self.contracts_file = self.memory_dir / "api_contracts.json"
        self.errors_file = self.memory_dir / "integration_errors.json"
        self.patterns_file = self.memory_dir / "success_patterns.json"

        # Load existing memory
        self.load_memory()

        # Initialize with our recent CMMS-Fix it Fred issue
        self._initialize_with_current_knowledge()

    def _initialize_with_current_knowledge(self):
        """Initialize memory with current known patterns and fixes"""

        # Record the CMMS → Fix it Fred parameter mapping issue we just fixed
        error_id = self._generate_error_id("cmms", "fix_it_fred", "parameter_mismatch")

        if error_id not in self.integration_errors:
            self.integration_errors[error_id] = IntegrationError(
                error_id=error_id,
                error_type="parameter_mismatch",
                source_service="cmms",
                target_service="fix_it_fred",
                error_description="CMMS sends 'description'/'priority' but Fix it Fred expects 'issue_description'/'severity'",
                original_request={
                    "description": "Pump motor running hot",
                    "priority": "high",
                    "asset_id": "PUMP001",
                },
                expected_format={
                    "issue_description": "Pump motor running hot",
                    "severity": "high",
                    "category": "maintenance",
                },
                solution_applied="Added parameter transformation in CMMS AI client",
                resolution_time_minutes=15.0,
                timestamp=datetime.now().isoformat(),
                resolved=True,
            )

        # Record Fix it Fred API contract
        fix_it_fred_contract_id = "fix_it_fred_analyze"
        if fix_it_fred_contract_id not in self.api_contracts:
            self.api_contracts[fix_it_fred_contract_id] = APIContractMemory(
                service_name="fix_it_fred",
                endpoint="/fix-it-fred/analyze",
                expected_parameters={
                    "issue_description": "string",
                    "severity": "string (low|medium|high|critical)",
                    "category": "string (maintenance|performance|bug|enhancement)",
                    "system_context": "string (optional)",
                    "auto_apply": "boolean (optional)",
                },
                response_format={
                    "fix_id": "string",
                    "success": "boolean",
                    "ai_analysis": "string",
                    "recommended_actions": "array of strings",
                    "fix_confidence": "float",
                    "estimated_time": "string",
                    "risk_assessment": "string",
                },
                parameter_mappings={
                    "cmms.description": "issue_description",
                    "cmms.priority": "severity",
                    "cmms.asset_id": "system_context",
                },
                last_updated=datetime.now().isoformat(),
                usage_count=1,
                success_rate=1.0,
            )

        # Record the successful transformation pattern
        pattern_id = "cmms_to_fix_it_fred_transform"
        if pattern_id not in self.success_patterns:
            self.success_patterns[pattern_id] = SuccessPattern(
                pattern_id=pattern_id,
                pattern_type="data_transformation",
                source_service="cmms",
                target_service="fix_it_fred",
                pattern_description="Transform CMMS maintenance issue format to Fix it Fred API format",
                implementation_code="""
# Transform CMMS format to Fix it Fred format
fix_it_fred_request = {
    "issue_description": issue_data.get("description", ""),
    "severity": issue_data.get("priority", "medium"),
    "category": issue_data.get("category", "maintenance"),
    "system_context": f"Asset ID: {issue_data.get('asset_id', 'N/A')}, Work Order: {issue_data.get('work_order_id', 'N/A')}",
    "auto_apply": False
}
                """.strip(),
                success_count=1,
                last_used=datetime.now().isoformat(),
            )

        logger.info("🧠 AI Memory initialized with current knowledge")

    def _generate_error_id(self, source: str, target: str, error_type: str) -> str:
        """Generate unique error ID"""
        content = f"{source}_{target}_{error_type}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:12]

    async def record_integration_error(
        self,
        source_service: str,
        target_service: str,
        error_type: str,
        error_description: str,
        original_request: Dict[str, Any],
        expected_format: Dict[str, Any] = None,
        solution_applied: str = "",
        resolution_time_minutes: float = 0,
    ) -> str:
        """Record a new integration error and its solution"""

        error_id = self._generate_error_id(source_service, target_service, error_type)

        self.integration_errors[error_id] = IntegrationError(
            error_id=error_id,
            error_type=error_type,
            source_service=source_service,
            target_service=target_service,
            error_description=error_description,
            original_request=original_request,
            expected_format=expected_format or {},
            solution_applied=solution_applied,
            resolution_time_minutes=resolution_time_minutes,
            timestamp=datetime.now().isoformat(),
            resolved=bool(solution_applied),
        )

        await self.save_memory()
        logger.info(f"🧠 Recorded integration error: {error_id}")
        return error_id

    async def record_api_contract(
        self,
        service_name: str,
        endpoint: str,
        expected_parameters: Dict[str, Any],
        response_format: Dict[str, Any],
        parameter_mappings: Dict[str, str] = None,
    ) -> str:
        """Record or update API contract information"""

        contract_id = f"{service_name}_{endpoint.replace('/', '_').replace('-', '_')}"

        self.api_contracts[contract_id] = APIContractMemory(
            service_name=service_name,
            endpoint=endpoint,
            expected_parameters=expected_parameters,
            response_format=response_format,
            parameter_mappings=parameter_mappings or {},
            last_updated=datetime.now().isoformat(),
            usage_count=self.api_contracts.get(
                contract_id, APIContractMemory("", "", {}, {})
            ).usage_count
            + 1,
        )

        await self.save_memory()
        logger.info(f"🧠 Recorded API contract: {contract_id}")
        return contract_id

    async def record_success_pattern(
        self,
        pattern_type: str,
        source_service: str,
        target_service: str,
        pattern_description: str,
        implementation_code: str,
    ) -> str:
        """Record a successful integration pattern"""

        pattern_id = f"{pattern_type}_{source_service}_{target_service}".replace(
            "-", "_"
        )

        if pattern_id in self.success_patterns:
            # Update existing pattern
            self.success_patterns[pattern_id].success_count += 1
            self.success_patterns[pattern_id].last_used = datetime.now().isoformat()
        else:
            # Create new pattern
            self.success_patterns[pattern_id] = SuccessPattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                source_service=source_service,
                target_service=target_service,
                pattern_description=pattern_description,
                implementation_code=implementation_code,
                success_count=1,
                last_used=datetime.now().isoformat(),
            )

        await self.save_memory()
        logger.info(f"🧠 Recorded success pattern: {pattern_id}")
        return pattern_id

    async def check_for_known_issues(
        self, source_service: str, target_service: str, request_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if we've seen this integration issue before"""

        # Look for API contract information
        contract_info = None
        for contract in self.api_contracts.values():
            if contract.service_name == target_service:
                contract_info = contract
                break

        if not contract_info:
            return None

        # Check for parameter mismatches
        missing_params = []
        incorrect_mappings = []

        for param, param_type in contract_info.expected_parameters.items():
            if param not in request_data:
                # Check if we have a known mapping
                mapping_key = f"{source_service}.{param}"
                reverse_mappings = {
                    v: k for k, v in contract_info.parameter_mappings.items()
                }

                if mapping_key in reverse_mappings:
                    source_param = reverse_mappings[mapping_key].split(".", 1)[1]
                    if source_param in request_data:
                        incorrect_mappings.append(
                            {
                                "source_param": source_param,
                                "target_param": param,
                                "suggested_mapping": f"'{source_param}' → '{param}'",
                            }
                        )
                else:
                    missing_params.append(param)

        if missing_params or incorrect_mappings:
            return {
                "potential_issue_detected": True,
                "contract_info": asdict(contract_info),
                "missing_parameters": missing_params,
                "incorrect_mappings": incorrect_mappings,
                "suggested_fix": "Use parameter transformation based on known mappings",
            }

        return None

    async def get_success_pattern(
        self, pattern_type: str, source_service: str, target_service: str
    ) -> Optional[SuccessPattern]:
        """Get a known success pattern"""
        pattern_id = f"{pattern_type}_{source_service}_{target_service}".replace(
            "-", "_"
        )
        return self.success_patterns.get(pattern_id)

    async def get_integration_history(
        self, source_service: str, target_service: str
    ) -> List[IntegrationError]:
        """Get integration error history between two services"""
        return [
            error
            for error in self.integration_errors.values()
            if error.source_service == source_service
            and error.target_service == target_service
        ]

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        total_errors = len(self.integration_errors)
        resolved_errors = sum(1 for e in self.integration_errors.values() if e.resolved)

        return {
            "total_api_contracts": len(self.api_contracts),
            "total_integration_errors": total_errors,
            "resolved_errors": resolved_errors,
            "resolution_rate": (
                resolved_errors / total_errors if total_errors > 0 else 1.0
            ),
            "success_patterns": len(self.success_patterns),
            "memory_files": {
                "contracts": str(self.contracts_file),
                "errors": str(self.errors_file),
                "patterns": str(self.patterns_file),
            },
            "last_updated": datetime.now().isoformat(),
        }

    async def save_memory(self):
        """Save memory to persistent storage"""
        try:
            # Save API contracts
            with open(self.contracts_file, "w") as f:
                contracts_data = {k: asdict(v) for k, v in self.api_contracts.items()}
                json.dump(contracts_data, f, indent=2)

            # Save integration errors
            with open(self.errors_file, "w") as f:
                errors_data = {k: asdict(v) for k, v in self.integration_errors.items()}
                json.dump(errors_data, f, indent=2)

            # Save success patterns
            with open(self.patterns_file, "w") as f:
                patterns_data = {k: asdict(v) for k, v in self.success_patterns.items()}
                json.dump(patterns_data, f, indent=2)

            logger.info("🧠 AI Memory saved successfully")

        except Exception as e:
            logger.error(f"Failed to save AI memory: {e}")

    def load_memory(self):
        """Load memory from persistent storage"""
        try:
            # Load API contracts
            if self.contracts_file.exists():
                with open(self.contracts_file, "r") as f:
                    contracts_data = json.load(f)
                    self.api_contracts = {
                        k: APIContractMemory(**v) for k, v in contracts_data.items()
                    }

            # Load integration errors
            if self.errors_file.exists():
                with open(self.errors_file, "r") as f:
                    errors_data = json.load(f)
                    self.integration_errors = {
                        k: IntegrationError(**v) for k, v in errors_data.items()
                    }

            # Load success patterns
            if self.patterns_file.exists():
                with open(self.patterns_file, "r") as f:
                    patterns_data = json.load(f)
                    self.success_patterns = {
                        k: SuccessPattern(**v) for k, v in patterns_data.items()
                    }

            logger.info("🧠 AI Memory loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load AI memory: {e}")


# Global memory system instance
ai_memory = AIMemorySystem()


async def get_ai_memory() -> AIMemorySystem:
    """Get the global AI memory system"""
    return ai_memory
