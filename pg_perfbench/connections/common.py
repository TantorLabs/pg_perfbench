from abc import ABC
from abc import abstractmethod
from types import TracebackType
from typing import Protocol
from typing import Self


class HasLifeCycle(Protocol):
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


class Runnable(Protocol):
    @abstractmethod
    async def run(self, cmd: str) -> str:
        ...

    @abstractmethod
    async def bash_command(self, cmd: str) -> str:
        ...

    @abstractmethod
    async def drop_cache(self) -> None:
        ...



class IsAsyncContextManager(Protocol):
    @abstractmethod
    async def __aenter__(self) -> Self:
        # TODO: add support for Python < 3.11, where Self is not implemented yet
        ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...


class Connectable(Runnable, IsAsyncContextManager, HasLifeCycle, ABC):
    ...
