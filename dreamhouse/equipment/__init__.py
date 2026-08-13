"""Equipment-envelope catalogue and layout coordination."""

from .models import EquipmentCatalog, ProductEnvelope, load_catalog
from .validators import validate_equipment

__all__ = ["EquipmentCatalog", "ProductEnvelope", "load_catalog", "validate_equipment"]
