from typing import Any, Iterator


class Types:
    def method(self):
        ...

    @staticmethod
    def function():
        ...

AnyType = type(Any)
NoneType = type(None)
Iterator = Iterator[str]
EllipsisType = type(...)

ClassType = type(Types)
MethodType = type(Types().method)
FunctionType = type(Types().function)

AllTypes = {
    'list': list,
    'dict': dict,
    'tuple': tuple,
    'set': set,
    'frozenset': frozenset,
}

AllNames = {
    'type': 'ClassType',
    'class': 'ClassType',
    'method': 'MethodType',
    'function': 'FunctionType'
}
