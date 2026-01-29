"""
ChatterFix Database Schema Generator
====================================
Generates Firestore collection schemas, indexes, and security rules.

Features:
- Schema validation definitions
- Firestore index configurations
- Security rules generation
- Migration scripts
- Data seeding utilities
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FieldType(Enum):
    """Firestore field types"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    GEOPOINT = "geopoint"
    REFERENCE = "reference"
    ARRAY = "array"
    MAP = "map"
    NULL = "null"


class IndexDirection(Enum):
    """Index sort direction"""
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


@dataclass
class FieldSchema:
    """Schema definition for a field"""
    name: str
    field_type: FieldType
    required: bool = True
    default: Any = None
    description: str = ""
    indexed: bool = False
    unique: bool = False
    reference_collection: Optional[str] = None  # For reference types
    array_type: Optional[FieldType] = None  # For array types
    map_schema: Optional[Dict] = None  # For map types
    validators: List[str] = field(default_factory=list)


@dataclass
class IndexSchema:
    """Firestore composite index definition"""
    collection: str
    fields: List[tuple]  # [(field_name, direction), ...]
    query_scope: str = "COLLECTION"


@dataclass
class CollectionSchema:
    """Complete collection schema"""
    name: str
    display_name: str
    description: str
    fields: List[FieldSchema]
    indexes: List[IndexSchema] = field(default_factory=list)
    subcollections: List[str] = field(default_factory=list)
    timestamps: bool = True
    soft_delete: bool = True
    audit_trail: bool = False


class DatabaseGenerator:
    """
    Generates Firestore database schemas and configurations.

    Produces:
    - Collection schema definitions
    - Firestore index configurations (firestore.indexes.json)
    - Security rules (firestore.rules)
    - Data validation utilities
    - Migration scripts
    - Seed data templates
    """

    # Python to Firestore type mapping
    TYPE_MAP = {
        "str": FieldType.STRING,
        "string": FieldType.STRING,
        "int": FieldType.NUMBER,
        "float": FieldType.NUMBER,
        "number": FieldType.NUMBER,
        "bool": FieldType.BOOLEAN,
        "boolean": FieldType.BOOLEAN,
        "datetime": FieldType.TIMESTAMP,
        "timestamp": FieldType.TIMESTAMP,
        "date": FieldType.TIMESTAMP,
        "list": FieldType.ARRAY,
        "array": FieldType.ARRAY,
        "dict": FieldType.MAP,
        "map": FieldType.MAP,
        "object": FieldType.MAP,
        "reference": FieldType.REFERENCE,
        "geopoint": FieldType.GEOPOINT,
    }

    def __init__(self):
        self.collections: Dict[str, CollectionSchema] = {}
        self.indexes: List[IndexSchema] = []

    def _to_snake_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _get_firestore_type(self, python_type: str) -> FieldType:
        return self.TYPE_MAP.get(python_type.lower(), FieldType.STRING)

    def generate_collection_schema(
        self,
        name: str,
        fields: List[Dict[str, Any]],
        display_name: Optional[str] = None,
        description: str = "",
        **kwargs
    ) -> CollectionSchema:
        """Generate a complete collection schema"""

        field_schemas = []
        for f in fields:
            field_type = self._get_firestore_type(f.get("type", "str"))

            field_schema = FieldSchema(
                name=f.get("name"),
                field_type=field_type,
                required=f.get("required", True),
                default=f.get("default"),
                description=f.get("description", ""),
                indexed=f.get("indexed", False),
                unique=f.get("unique", False),
                reference_collection=f.get("reference_collection"),
                validators=f.get("validators", []),
            )
            field_schemas.append(field_schema)

        collection = CollectionSchema(
            name=name,
            display_name=display_name or name.replace("_", " ").title(),
            description=description,
            fields=field_schemas,
            timestamps=kwargs.get("timestamps", True),
            soft_delete=kwargs.get("soft_delete", True),
            audit_trail=kwargs.get("audit_trail", False),
        )

        self.collections[name] = collection
        return collection

    def generate_firestore_indexes(self, collections: List[CollectionSchema] = None) -> str:
        """Generate firestore.indexes.json content"""

        if collections is None:
            collections = list(self.collections.values())

        indexes = []

        for collection in collections:
            # Auto-generate common indexes
            # Index for soft delete + created_at (common query pattern)
            if collection.soft_delete and collection.timestamps:
                indexes.append({
                    "collectionGroup": collection.name,
                    "queryScope": "COLLECTION",
                    "fields": [
                        {"fieldPath": "is_deleted", "order": "ASCENDING"},
                        {"fieldPath": "created_at", "order": "DESCENDING"}
                    ]
                })

            # Add indexes for explicitly indexed fields
            indexed_fields = [f for f in collection.fields if f.indexed]
            for field in indexed_fields:
                if collection.soft_delete:
                    indexes.append({
                        "collectionGroup": collection.name,
                        "queryScope": "COLLECTION",
                        "fields": [
                            {"fieldPath": "is_deleted", "order": "ASCENDING"},
                            {"fieldPath": field.name, "order": "ASCENDING"}
                        ]
                    })

        return json.dumps({
            "indexes": indexes,
            "fieldOverrides": []
        }, indent=2)

    def generate_security_rules(self, collections: List[CollectionSchema] = None) -> str:
        """Generate Firestore security rules"""

        if collections is None:
            collections = list(self.collections.values())

        rules = '''rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Helper functions
    function isAuthenticated() {
      return request.auth != null;
    }

    function isOwner(userId) {
      return request.auth.uid == userId;
    }

    function hasRole(role) {
      return request.auth.token.role == role;
    }

    function isAdmin() {
      return hasRole('admin');
    }

    function isValidTimestamp(field) {
      return request.resource.data[field] is timestamp;
    }

'''
        for collection in collections:
            rules += self._generate_collection_rules(collection)

        rules += '''
    // Catch-all: deny everything else
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
'''
        return rules

    def _generate_collection_rules(self, collection: CollectionSchema) -> str:
        """Generate rules for a single collection"""

        # Build validation for required fields
        validations = []
        for field in collection.fields:
            if field.required:
                type_check = self._get_type_validation(field)
                if type_check:
                    validations.append(type_check)

        validation_str = " && ".join(validations) if validations else "true"

        return f'''
    // {collection.display_name} collection
    match /{collection.name}/{{docId}} {{
      // Read: authenticated users
      allow read: if isAuthenticated() &&
                     (!resource.data.keys().hasAny(['is_deleted']) || resource.data.is_deleted == false);

      // Create: authenticated users with valid data
      allow create: if isAuthenticated() &&
                       {validation_str};

      // Update: authenticated users (owner or admin)
      allow update: if isAuthenticated() &&
                       (isOwner(resource.data.created_by) || isAdmin());

      // Delete: admin only (use soft delete instead)
      allow delete: if isAdmin();
    }}
'''

    def _get_type_validation(self, field: FieldSchema) -> str:
        """Get Firestore rules type validation"""

        type_checks = {
            FieldType.STRING: f"request.resource.data.{field.name} is string",
            FieldType.NUMBER: f"request.resource.data.{field.name} is number",
            FieldType.BOOLEAN: f"request.resource.data.{field.name} is bool",
            FieldType.TIMESTAMP: f"request.resource.data.{field.name} is timestamp",
            FieldType.ARRAY: f"request.resource.data.{field.name} is list",
            FieldType.MAP: f"request.resource.data.{field.name} is map",
        }
        return type_checks.get(field.field_type, "")

    def generate_validation_schema(self, collection: CollectionSchema) -> str:
        """Generate Python validation schema for a collection"""

        name = collection.name.replace("_", " ").title().replace(" ", "")

        validators = []
        for field in collection.fields:
            v = self._generate_field_validator(field)
            if v:
                validators.append(v)

        return f'''"""
Validation schema for {collection.display_name}
Auto-generated by ChatterFix Database Generator
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


class {name}Validator:
    """Validates {collection.display_name} documents before database operations"""

    REQUIRED_FIELDS = {[f.name for f in collection.fields if f.required]}

    @classmethod
    def validate(cls, data: Dict[str, Any], partial: bool = False) -> tuple[bool, List[str]]:
        """
        Validate document data.

        Args:
            data: Document data to validate
            partial: If True, skip required field checks (for updates)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not partial:
            for field in cls.REQUIRED_FIELDS:
                if field not in data or data[field] is None:
                    errors.append(f"Missing required field: {{field}}")

        # Type validations
{chr(10).join("        " + v for v in validators)}

        return len(errors) == 0, errors

    @classmethod
    def sanitize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and normalize document data"""
        sanitized = {{}}

        for key, value in data.items():
            # Strip strings
            if isinstance(value, str):
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value

        return sanitized
'''

    def _generate_field_validator(self, field: FieldSchema) -> str:
        """Generate validation code for a field"""

        checks = {
            FieldType.STRING: f'''if "{field.name}" in data and data["{field.name}"] is not None:
            if not isinstance(data["{field.name}"], str):
                errors.append("{field.name} must be a string")''',
            FieldType.NUMBER: f'''if "{field.name}" in data and data["{field.name}"] is not None:
            if not isinstance(data["{field.name}"], (int, float)):
                errors.append("{field.name} must be a number")''',
            FieldType.BOOLEAN: f'''if "{field.name}" in data and data["{field.name}"] is not None:
            if not isinstance(data["{field.name}"], bool):
                errors.append("{field.name} must be a boolean")''',
        }
        return checks.get(field.field_type, "")

    def generate_seed_data(self, collection: CollectionSchema, count: int = 5) -> str:
        """Generate seed data template for a collection"""

        samples = []
        for i in range(1, count + 1):
            sample = {"id": f"{collection.name[:3].upper()}{i:03d}"}

            for field in collection.fields:
                sample[field.name] = self._generate_sample_value(field, i)

            if collection.timestamps:
                sample["created_at"] = "datetime.now(timezone.utc)"
                sample["updated_at"] = "datetime.now(timezone.utc)"

            if collection.soft_delete:
                sample["is_deleted"] = False

            samples.append(sample)

        return f'''"""
Seed data for {collection.display_name}
Auto-generated by ChatterFix Database Generator
"""

from datetime import datetime, timezone

{collection.name.upper()}_SEED_DATA = {json.dumps(samples, indent=4, default=str)}


async def seed_{collection.name}(db):
    """Seed {collection.display_name} collection"""
    collection = db.collection("{collection.name}")

    for item in {collection.name.upper()}_SEED_DATA:
        item["created_at"] = datetime.now(timezone.utc)
        item["updated_at"] = datetime.now(timezone.utc)

        doc_ref = collection.document(item.pop("id"))
        await doc_ref.set(item)

    print(f"Seeded {{len({collection.name.upper()}_SEED_DATA)}} {collection.display_name} documents")
'''

    def _generate_sample_value(self, field: FieldSchema, index: int) -> Any:
        """Generate sample value for a field"""

        samples = {
            FieldType.STRING: f"Sample {field.name} {index}",
            FieldType.NUMBER: index * 100,
            FieldType.BOOLEAN: index % 2 == 0,
            FieldType.ARRAY: [f"item{index}"],
            FieldType.MAP: {"key": f"value{index}"},
        }

        if field.default is not None:
            return field.default

        return samples.get(field.field_type, f"value_{index}")

    def generate_migration(self, collection: CollectionSchema, version: str = "001") -> str:
        """Generate migration script for a collection"""

        return f'''"""
Migration {version}: Create {collection.display_name} collection
Auto-generated by ChatterFix Database Generator
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MIGRATION_VERSION = "{version}"
COLLECTION_NAME = "{collection.name}"


async def up(db):
    """Apply migration - create collection structure"""
    logger.info(f"Applying migration {{MIGRATION_VERSION}}: Create {collection.display_name}")

    # Create a placeholder document to establish collection
    # Firestore creates collections implicitly, but this ensures indexes work
    placeholder_ref = db.collection(COLLECTION_NAME).document("_schema")
    await placeholder_ref.set({{
        "_migration_version": MIGRATION_VERSION,
        "_created_at": datetime.now(timezone.utc),
        "_schema_fields": {[f.name for f in collection.fields]},
        "_is_placeholder": True
    }})

    logger.info(f"Migration {{MIGRATION_VERSION}} applied successfully")


async def down(db):
    """Rollback migration - remove collection"""
    logger.warning(f"Rolling back migration {{MIGRATION_VERSION}}: Delete {collection.display_name}")

    # Delete all documents in collection
    collection_ref = db.collection(COLLECTION_NAME)
    docs = await collection_ref.limit(500).get()

    for doc in docs:
        await doc.reference.delete()

    logger.info(f"Migration {{MIGRATION_VERSION}} rolled back")


async def status(db) -> dict:
    """Check migration status"""
    try:
        schema_doc = await db.collection(COLLECTION_NAME).document("_schema").get()
        if schema_doc.exists:
            return {{"applied": True, "version": MIGRATION_VERSION}}
    except Exception:
        pass
    return {{"applied": False, "version": MIGRATION_VERSION}}
'''

    def generate_all(
        self,
        name: str,
        fields: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, str]:
        """Generate all database artifacts for a collection"""

        collection = self.generate_collection_schema(name, fields, **kwargs)

        return {
            "schema": self.generate_collection_schema(name, fields, **kwargs),
            "indexes_json": self.generate_firestore_indexes([collection]),
            "security_rules": self.generate_security_rules([collection]),
            "validator": self.generate_validation_schema(collection),
            "seed_data": self.generate_seed_data(collection),
            "migration": self.generate_migration(collection),
        }


def get_database_generator() -> DatabaseGenerator:
    """Get a DatabaseGenerator instance"""
    return DatabaseGenerator()
