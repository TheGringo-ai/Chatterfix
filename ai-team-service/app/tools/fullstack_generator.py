"""
ChatterFix Full-Stack Feature Generator
=======================================
AI-Powered full-stack code generation using the AI team.

Generates complete features with:
- Pydantic models (request/response)
- FastAPI routes with CRUD endpoints
- Firestore database operations
- UI components (forms, tables, cards)
- Integration code

Uses the AI team (Claude, ChatGPT, Gemini, Grok) for intelligent code generation.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FieldType(Enum):
    """Supported field types"""
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    DATETIME = "datetime"
    DATE = "date"
    LIST = "list"
    DICT = "dict"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    CURRENCY = "currency"


class FeatureType(Enum):
    """Types of features to generate"""
    CRUD = "crud"  # Basic Create, Read, Update, Delete
    READONLY = "readonly"  # Read-only (reports, analytics)
    WORKFLOW = "workflow"  # Stateful workflow (work orders, tickets)
    REFERENCE = "reference"  # Reference data (categories, statuses)


@dataclass
class FieldSpec:
    """Specification for a model field"""
    name: str
    field_type: str
    label: str = ""
    required: bool = True
    default: Any = None
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    choices: Optional[List[str]] = None
    example: Any = None
    searchable: bool = False
    filterable: bool = False
    sortable: bool = True
    show_in_list: bool = True
    show_in_form: bool = True


@dataclass
class FeatureSpec:
    """Complete feature specification"""
    name: str
    display_name: str
    description: str
    fields: List[FieldSpec]
    feature_type: FeatureType = FeatureType.CRUD
    collection_name: Optional[str] = None
    icon: str = "bi-folder"
    color: str = "primary"
    include_timestamps: bool = True
    include_soft_delete: bool = True
    include_search: bool = True
    include_pagination: bool = True
    include_export: bool = False
    parent_feature: Optional[str] = None  # For nested features
    tags: List[str] = field(default_factory=list)


class FullStackGenerator:
    """
    AI-Powered Full-Stack Feature Generator.

    Uses the AI team for intelligent code generation that understands:
    - ChatterFix patterns and conventions
    - Best practices for FastAPI, Pydantic, Firestore
    - Accessibility and UX patterns
    - The technician-first philosophy
    """

    # Type mappings
    PYTHON_TYPES = {
        "str": "str", "string": "str", "text": "str",
        "int": "int", "integer": "int", "number": "int",
        "float": "float", "decimal": "float", "currency": "float",
        "bool": "bool", "boolean": "bool",
        "datetime": "datetime", "timestamp": "datetime",
        "date": "date",
        "list": "List[Any]", "array": "List[Any]",
        "dict": "Dict[str, Any]", "object": "Dict[str, Any]",
        "email": "str", "phone": "str", "url": "str",
    }

    UI_INPUT_TYPES = {
        "str": "text", "string": "text", "text": "textarea",
        "int": "number", "integer": "number",
        "float": "number", "decimal": "number", "currency": "number",
        "bool": "checkbox", "boolean": "checkbox",
        "datetime": "datetime-local", "timestamp": "datetime-local",
        "date": "date",
        "email": "email", "phone": "tel", "url": "url",
        "list": "textarea", "array": "textarea",
    }

    def __init__(self):
        self.generated_features = {}
        self._ai_orchestrator = None

    async def _get_ai_orchestrator(self):
        """Lazy load AI orchestrator"""
        if self._ai_orchestrator is None:
            try:
                from app.services.ai_orchestrator import AIOrchestrator
                self._ai_orchestrator = AIOrchestrator()
                await self._ai_orchestrator.initialize()
                logger.info("✅ AI Orchestrator initialized for code generation")
            except Exception as e:
                logger.warning(f"⚠️ AI Orchestrator not available: {e}")
                self._ai_orchestrator = None
        return self._ai_orchestrator

    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower().replace('-', '_').replace(' ', '_')

    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase"""
        return ''.join(word.capitalize() for word in self._to_snake_case(name).split('_'))

    def _to_title_case(self, name: str) -> str:
        """Convert to Title Case"""
        return ' '.join(word.capitalize() for word in self._to_snake_case(name).split('_'))

    def _get_python_type(self, field_type: str, required: bool = True) -> str:
        """Get Python type annotation"""
        base_type = self.PYTHON_TYPES.get(field_type.lower(), "str")
        return base_type if required else f"Optional[{base_type}]"

    def _get_ui_input_type(self, field_type: str) -> str:
        """Get HTML input type"""
        return self.UI_INPUT_TYPES.get(field_type.lower(), "text")

    # =========================================================================
    # PYDANTIC MODEL GENERATION
    # =========================================================================

    def generate_models(self, feature: FeatureSpec) -> str:
        """Generate Pydantic models for a feature"""
        name = self._to_pascal_case(feature.name)
        snake = self._to_snake_case(feature.name)

        # Build field definitions
        base_fields = []
        update_fields = []

        for f in feature.fields:
            py_type = self._get_python_type(f.field_type, f.required)
            default = "None" if not f.required else "..."

            # Add validation constraints
            constraints = []
            if f.description:
                constraints.append(f'description="{f.description}"')
            if f.min_length:
                constraints.append(f"min_length={f.min_length}")
            if f.max_length:
                constraints.append(f"max_length={f.max_length}")
            if f.min_value is not None:
                constraints.append(f"ge={f.min_value}")
            if f.max_value is not None:
                constraints.append(f"le={f.max_value}")
            if f.pattern:
                constraints.append(f'pattern=r"{f.pattern}"')
            if f.example:
                ex = f'"{f.example}"' if isinstance(f.example, str) else f.example
                constraints.append(f"example={ex}")

            if constraints:
                base_fields.append(f"    {f.name}: {py_type} = Field({default}, {', '.join(constraints)})")
            else:
                base_fields.append(f"    {f.name}: {py_type} = {default}")

            # Update fields are all optional
            opt_type = f"Optional[{self.PYTHON_TYPES.get(f.field_type.lower(), 'str')}]"
            update_fields.append(f"    {f.name}: {opt_type} = None")

        # Timestamp and soft delete fields
        extra_response_fields = ""
        if feature.include_timestamps:
            extra_response_fields += "\n    created_at: Optional[datetime] = None"
            extra_response_fields += "\n    updated_at: Optional[datetime] = None"
        if feature.include_soft_delete:
            extra_response_fields += "\n    is_deleted: bool = False"

        return f'''"""
Pydantic models for {feature.display_name}
Auto-generated by ChatterFix Full-Stack Generator
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class {name}Base(BaseModel):
    """{feature.description}"""
{chr(10).join(base_fields) if base_fields else "    pass"}

    class Config:
        from_attributes = True


class {name}Create({name}Base):
    """Create request model"""
    pass


class {name}Update(BaseModel):
    """Update request model - all fields optional"""
{chr(10).join(update_fields) if update_fields else "    pass"}


class {name}Response({name}Base):
    """Response model with ID and metadata"""
    id: str{extra_response_fields}


class {name}ListResponse(BaseModel):
    """Paginated list response"""
    items: List[{name}Response]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class {name}SearchRequest(BaseModel):
    """Search and filter request"""
    query: Optional[str] = Field(None, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
'''

    # =========================================================================
    # FIRESTORE SERVICE GENERATION
    # =========================================================================

    def generate_service(self, feature: FeatureSpec) -> str:
        """Generate Firestore CRUD service"""
        name = self._to_pascal_case(feature.name)
        snake = self._to_snake_case(feature.name)
        collection = feature.collection_name or f"{snake}s"

        return f'''"""
Firestore service for {feature.display_name}
Auto-generated by ChatterFix Full-Stack Generator
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class {name}Service:
    """
    CRUD operations for {feature.display_name}.
    Collection: {collection}
    """

    COLLECTION = "{collection}"

    def __init__(self, db):
        self.db = db
        self.collection = db.collection(self.COLLECTION)

    async def create(self, data: dict, user_id: Optional[str] = None) -> dict:
        """Create a new {feature.display_name}"""
        try:
            doc_data = {{**data}}
            doc_data["created_at"] = datetime.now(timezone.utc)
            doc_data["updated_at"] = datetime.now(timezone.utc)
            doc_data["is_deleted"] = False
            if user_id:
                doc_data["created_by"] = user_id

            doc_ref = self.collection.document()
            await doc_ref.set(doc_data)
            doc_data["id"] = doc_ref.id

            logger.info(f"Created {snake}: {{doc_ref.id}}")
            return doc_data

        except Exception as e:
            logger.error(f"Error creating {snake}: {{e}}")
            raise

    async def get(self, id: str) -> Optional[dict]:
        """Get a {feature.display_name} by ID"""
        try:
            doc = await self.collection.document(id).get()
            if not doc.exists:
                return None

            data = doc.to_dict()
            if data.get("is_deleted"):
                return None

            data["id"] = doc.id
            return data

        except Exception as e:
            logger.error(f"Error getting {snake} {{id}}: {{e}}")
            raise

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        filters: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Get all {feature.display_name}s with pagination"""
        try:
            from google.cloud.firestore import Query

            query = self.collection.where("is_deleted", "==", False)

            if filters:
                for key, value in filters.items():
                    if value is not None:
                        query = query.where(key, "==", value)

            # Count total
            count_result = await query.count().get()
            total = count_result[0][0].value if count_result else 0

            # Sort and paginate
            direction = Query.DESCENDING if sort_order == "desc" else Query.ASCENDING
            query = query.order_by(sort_by, direction=direction)
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            docs = await query.get()
            items = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                items.append(data)

            return {{
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": (offset + len(items)) < total
            }}

        except Exception as e:
            logger.error(f"Error getting {snake}s: {{e}}")
            raise

    async def update(self, id: str, data: dict) -> Optional[dict]:
        """Update a {feature.display_name}"""
        try:
            doc_ref = self.collection.document(id)
            doc = await doc_ref.get()

            if not doc.exists or doc.to_dict().get("is_deleted"):
                return None

            update_data = {{k: v for k, v in data.items() if v is not None}}
            update_data["updated_at"] = datetime.now(timezone.utc)

            await doc_ref.update(update_data)

            updated = await doc_ref.get()
            result = updated.to_dict()
            result["id"] = doc_ref.id

            logger.info(f"Updated {snake}: {{id}}")
            return result

        except Exception as e:
            logger.error(f"Error updating {snake} {{id}}: {{e}}")
            raise

    async def delete(self, id: str, hard: bool = False) -> bool:
        """Delete a {feature.display_name}"""
        try:
            doc_ref = self.collection.document(id)
            doc = await doc_ref.get()

            if not doc.exists:
                return False

            if hard:
                await doc_ref.delete()
                logger.info(f"Hard deleted {snake}: {{id}}")
            else:
                await doc_ref.update({{"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}})
                logger.info(f"Soft deleted {snake}: {{id}}")

            return True

        except Exception as e:
            logger.error(f"Error deleting {snake} {{id}}: {{e}}")
            raise

    async def search(self, query: str = None, filters: dict = None, page: int = 1, page_size: int = 20) -> dict:
        """Search {feature.display_name}s"""
        return await self.get_all(page=page, page_size=page_size, filters=filters)
'''

    # =========================================================================
    # FASTAPI ROUTER GENERATION
    # =========================================================================

    def generate_router(self, feature: FeatureSpec) -> str:
        """Generate FastAPI router with CRUD endpoints"""
        name = self._to_pascal_case(feature.name)
        snake = self._to_snake_case(feature.name)
        plural = f"{snake}s"
        tag = feature.display_name

        return f'''"""
FastAPI router for {feature.display_name}
Auto-generated by ChatterFix Full-Stack Generator
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from .models import (
    {name}Create, {name}Update, {name}Response,
    {name}ListResponse, {name}SearchRequest
)
from .service import {name}Service

router = APIRouter(prefix="/{plural}", tags=["{tag}"])


def get_service():
    """Get {name} service - override with actual DB connection"""
    from app.core.firestore_db import get_firestore_client
    return {name}Service(get_firestore_client())


@router.post("", response_model={name}Response, status_code=status.HTTP_201_CREATED)
async def create_{snake}(data: {name}Create, service: {name}Service = Depends(get_service)):
    """Create a new {feature.display_name}"""
    result = await service.create(data.model_dump())
    return {name}Response(**result)


@router.get("", response_model={name}ListResponse)
async def list_{plural}(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    service: {name}Service = Depends(get_service)
):
    """List all {feature.display_name}s with pagination"""
    result = await service.get_all(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    return {name}ListResponse(**result)


@router.get("/{{id}}", response_model={name}Response)
async def get_{snake}(id: str, service: {name}Service = Depends(get_service)):
    """Get a {feature.display_name} by ID"""
    result = await service.get(id)
    if not result:
        raise HTTPException(status_code=404, detail="{feature.display_name} not found")
    return {name}Response(**result)


@router.put("/{{id}}", response_model={name}Response)
async def update_{snake}(id: str, data: {name}Update, service: {name}Service = Depends(get_service)):
    """Update a {feature.display_name}"""
    result = await service.update(id, data.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="{feature.display_name} not found")
    return {name}Response(**result)


@router.delete("/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{snake}(id: str, hard: bool = False, service: {name}Service = Depends(get_service)):
    """Delete a {feature.display_name}"""
    result = await service.delete(id, hard=hard)
    if not result:
        raise HTTPException(status_code=404, detail="{feature.display_name} not found")


@router.post("/search", response_model={name}ListResponse)
async def search_{plural}(request: {name}SearchRequest, service: {name}Service = Depends(get_service)):
    """Search {feature.display_name}s"""
    result = await service.search(
        query=request.query,
        filters=request.filters,
        page=request.page,
        page_size=request.page_size
    )
    return {name}ListResponse(**result)
'''

    # =========================================================================
    # UI COMPONENT GENERATION (Frontend Integration)
    # =========================================================================

    def generate_ui_form(self, feature: FeatureSpec) -> Dict[str, Any]:
        """Generate UI form configuration for UIToolkit"""
        fields = []
        for f in feature.fields:
            if not f.show_in_form:
                continue

            field_config = {
                "name": f.name,
                "label": f.label or self._to_title_case(f.name),
                "input_type": self._get_ui_input_type(f.field_type),
                "required": f.required,
            }

            if f.choices:
                field_config["input_type"] = "select"
                field_config["options"] = f.choices

            if f.description:
                field_config["placeholder"] = f.description

            # Helper text for validation constraints
            helper_parts = []
            if f.min_value is not None:
                helper_parts.append(f"Min: {f.min_value}")
            if f.max_value is not None:
                helper_parts.append(f"Max: {f.max_value}")
            if f.min_length:
                helper_parts.append(f"Min length: {f.min_length}")
            if f.max_length:
                helper_parts.append(f"Max length: {f.max_length}")
            if helper_parts:
                field_config["helper_text"] = ", ".join(helper_parts)

            fields.append(field_config)

        snake = self._to_snake_case(feature.name)
        return {
            "fields": fields,
            "action": f"/api/{snake}s",
            "method": "POST",
            "submit_text": f"Save {feature.display_name}",
        }

    def generate_ui_table(self, feature: FeatureSpec) -> Dict[str, Any]:
        """Generate UI table configuration for UIToolkit"""
        headers = ["ID"]
        row_fields = ["id"]

        for f in feature.fields:
            if f.show_in_list:
                headers.append(f.label or self._to_title_case(f.name))
                row_fields.append(f.name)

        if feature.include_timestamps:
            headers.append("Created")
            row_fields.append("created_at")

        headers.append("Actions")

        snake = self._to_snake_case(feature.name)
        return {
            "headers": headers,
            "row_fields": row_fields,
            "api_endpoint": f"/api/{snake}s",
            "actions": ["view", "edit", "delete"],
        }

    def generate_ui_card(self, feature: FeatureSpec) -> Dict[str, Any]:
        """Generate card display configuration"""
        display_fields = [f.name for f in feature.fields if f.show_in_list][:4]

        return {
            "title_field": display_fields[0] if display_fields else "id",
            "subtitle_field": display_fields[1] if len(display_fields) > 1 else None,
            "body_fields": display_fields[2:] if len(display_fields) > 2 else [],
            "icon": feature.icon,
            "color": feature.color,
        }

    # =========================================================================
    # FULL FEATURE GENERATION
    # =========================================================================

    def generate_feature(
        self,
        name: str,
        fields: List[Dict[str, Any]],
        display_name: Optional[str] = None,
        description: str = "",
        feature_type: str = "crud",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a complete full-stack feature.

        Args:
            name: Feature name (e.g., "budget", "work_order")
            fields: List of field definitions
            display_name: Human-readable name
            description: Feature description

        Returns:
            Dict with all generated code and configs
        """
        # Convert field dicts to FieldSpec
        field_specs = []
        for f in fields:
            field_specs.append(FieldSpec(
                name=f.get("name"),
                field_type=f.get("type", "str"),
                label=f.get("label", ""),
                required=f.get("required", True),
                default=f.get("default"),
                description=f.get("description", ""),
                min_value=f.get("min_value"),
                max_value=f.get("max_value"),
                min_length=f.get("min_length"),
                max_length=f.get("max_length"),
                pattern=f.get("pattern"),
                choices=f.get("choices"),
                example=f.get("example"),
                searchable=f.get("searchable", False),
                filterable=f.get("filterable", False),
                sortable=f.get("sortable", True),
                show_in_list=f.get("show_in_list", True),
                show_in_form=f.get("show_in_form", True),
            ))

        # Create feature spec
        feature = FeatureSpec(
            name=name,
            display_name=display_name or self._to_title_case(name),
            description=description or f"{display_name or self._to_title_case(name)} management",
            fields=field_specs,
            feature_type=FeatureType(feature_type) if isinstance(feature_type, str) else feature_type,
            collection_name=kwargs.get("collection_name"),
            icon=kwargs.get("icon", "bi-folder"),
            color=kwargs.get("color", "primary"),
            include_timestamps=kwargs.get("include_timestamps", True),
            include_soft_delete=kwargs.get("include_soft_delete", True),
            include_search=kwargs.get("include_search", True),
            include_pagination=kwargs.get("include_pagination", True),
        )

        snake = self._to_snake_case(name)

        # Generate all components
        result = {
            "feature_name": name,
            "display_name": feature.display_name,
            "description": feature.description,
            "collection_name": feature.collection_name or f"{snake}s",

            # Backend code
            "backend": {
                "models.py": self.generate_models(feature),
                "service.py": self.generate_service(feature),
                "router.py": self.generate_router(feature),
            },

            # Frontend configs (for UIToolkit)
            "frontend": {
                "form": self.generate_ui_form(feature),
                "table": self.generate_ui_table(feature),
                "card": self.generate_ui_card(feature),
            },

            # API endpoints
            "endpoints": [
                {"method": "POST", "path": f"/{snake}s", "operation": "create"},
                {"method": "GET", "path": f"/{snake}s", "operation": "list"},
                {"method": "GET", "path": f"/{snake}s/{{id}}", "operation": "get"},
                {"method": "PUT", "path": f"/{snake}s/{{id}}", "operation": "update"},
                {"method": "DELETE", "path": f"/{snake}s/{{id}}", "operation": "delete"},
                {"method": "POST", "path": f"/{snake}s/search", "operation": "search"},
            ],

            # Integration instructions
            "instructions": self._generate_instructions(feature),
        }

        self.generated_features[name] = result
        return result

    def _generate_instructions(self, feature: FeatureSpec) -> str:
        """Generate integration instructions"""
        snake = self._to_snake_case(feature.name)
        pascal = self._to_pascal_case(feature.name)

        return f'''
# Integration Instructions for {feature.display_name}

## 1. Create feature directory
mkdir -p app/features/{snake}
touch app/features/{snake}/__init__.py

## 2. Save generated files
# Copy models.py, service.py, router.py to app/features/{snake}/

## 3. Create __init__.py
# app/features/{snake}/__init__.py
from .router import router
from .models import {pascal}Create, {pascal}Update, {pascal}Response
from .service import {pascal}Service

## 4. Register router in main.py
from app.features.{snake} import router as {snake}_router
app.include_router({snake}_router, prefix="/api", tags=["{feature.display_name}"])

## 5. Generate frontend with UIToolkit
from app.tools import get_ui_toolkit
toolkit = get_ui_toolkit()

# Create form
form_html = toolkit.generate_form(**{self.generate_ui_form(feature)})

# Create listing page
table_html = toolkit.generate_data_table(
    headers={self.generate_ui_table(feature)['headers']},
    rows=[]  # Populated from API
)
'''

    async def generate_with_ai_team(
        self,
        name: str,
        description: str,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Use the AI team to intelligently design and generate a feature.

        The AI team will:
        1. Analyze the description to extract fields
        2. Suggest appropriate field types and validations
        3. Design the optimal data model
        4. Generate production-ready code
        """
        orchestrator = await self._get_ai_orchestrator()

        if orchestrator is None:
            logger.warning("AI team not available, using basic generation")
            return {"error": "AI team not available"}

        prompt = f"""
Design a complete feature for ChatterFix CMMS based on this description:

Feature Name: {name}
Description: {description}
Context: {context}

Please provide:
1. List of fields with types, validations, and descriptions
2. Any special business logic needed
3. Relationships to other features (work orders, assets, etc.)
4. UI/UX considerations for technicians (touch-friendly, voice-command ready)

Format your response as JSON:
{{
    "fields": [
        {{"name": "field_name", "type": "str|int|float|bool|datetime", "required": true, "description": "...", "label": "...", "choices": null}}
    ],
    "business_logic": ["rule1", "rule2"],
    "relationships": ["related_feature1"],
    "ui_notes": ["consideration1"]
}}
"""

        try:
            result = await orchestrator.execute_collaborative_task(
                prompt=prompt,
                context="ChatterFix CMMS feature design - technician-first, hands-free capable",
                project_context="ChatterFix"
            )

            # Parse AI response to extract field definitions
            # The AI team's response will be in result.final_answer
            return {
                "ai_response": result.final_answer,
                "confidence": result.confidence_score,
                "agents_consulted": [r.get("agent") for r in result.agent_responses],
            }

        except Exception as e:
            logger.error(f"AI team generation failed: {e}")
            return {"error": str(e)}


def get_fullstack_generator() -> FullStackGenerator:
    """Get a FullStackGenerator instance"""
    return FullStackGenerator()
