from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseDatasetSchema(ABC):
    """
    Clase base abstracta para esquemas de datos sintéticos.
    Permite desacoplar el dominio de negocio del motor de generación.
    """

    @abstractmethod
    def generate_record(self) -> Dict[str, Any]:
        """Genera un único registro estructurado con anidamiento."""
        pass

    @abstractmethod
    def get_collection_name(self) -> str:
        """Retorna el nombre sugerido de la colección/tabla."""
        pass

