from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from types_ import EnvType


@dataclass(kw_only=True)
class ResourceConfig:
    stack: str
    env: EnvType
    region: str
    project_id: str
    tag: str


@dataclass(kw_only=True)
class AbstractResource(ABC):
    config: ResourceConfig

    def __post_init__(self):
        self._create()

    @abstractmethod
    def _create(self):
        raise NotImplementedError("Please Implement this method")

    def resource_name(self, template: str, trimmable: str | None):
        """
        Generate a name for a resource.

        Length is limited to 63
        @trimmable will be trimmed if necessary

        @template: the name template in format "prefix-$-suffix"
        Where $ will be replaced with @trimmable
        """

        commit_hash_length = 7
        max_length = 63 - len(template) - commit_hash_length
        max_length -= 2  # some contingency
        trimmed = trimmable[:max_length] if trimmable else ""

        return template.replace("$", trimmed).replace("/", "-")
