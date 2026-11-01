import hashlib
import hmac
import json
from typing import Dict, Any

class ProjectIntegrityEngine:
    """
    Cryptographic Checksum & Immutability Engine for AegisLPS Projects.
    Ensures that approved calculation records and project revisions are tamper-evident.
    """
    SECRET_SALT = b"AegisLPS_Engineering_Integrity_Salt_2026"

    @classmethod
    def compute_project_checksum(cls, project_dict: Dict[str, Any]) -> str:
        """
        Generates deterministic SHA-256 HMAC digest over canonicalized JSON representation.
        Excludes transient/metadata keys like 'checksum' and 'updated_at'.
        """
        clean_dict = {k: v for k, v in project_dict.items() if k not in ["checksum", "updated_at"]}
        canonical_json = json.dumps(clean_dict, sort_keys=True, separators=(",", ":"))
        return hmac.new(cls.SECRET_SALT, canonical_json.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def verify_project_integrity(cls, project_dict: Dict[str, Any], expected_checksum: str) -> bool:
        computed = cls.compute_project_checksum(project_dict)
        return hmac.compare_digest(computed, expected_checksum)
