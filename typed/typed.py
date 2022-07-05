from typing import get_args
from types import GenericAlias
from inspect import getfullargspec
from typed.decorator_types import *


class TypedDecorator(object):
    def __init__(self, func):
        self._func = func
        self._func_name = self._func.__name__
        self._argspec = getfullargspec(self._func)
        self._annotations = self._argspec.annotations
        self._func_args = self._argspec.args
        self._defaults = self._argspec.defaults
        self._returns = self._get_returns_types

    @property
    def _get_returns_types(self):
        try:
            returns = self._annotations['return']
            del self._annotations['return']
        except KeyError:
            returns = None
        return returns

    @staticmethod
    def _get_type(type_) -> Any:
        try:
            return AllTypes[type_]
        except KeyError:
            return type_

    @staticmethod
    def _get_type_name(type_) -> str:
        try:
            type_name = str(type_.__name__)
        except AttributeError:
            type_name = str(type_)
        try:
            return AllNames[type_name]
        except KeyError:
            return type_name

    def _get_generic_type(self, type_):
        return self._get_type(str(type_).split('[')[0])

    def _check_generic(self, kwarg, args, _generic_args):
        if type(_generic_args) == GenericAlias:
            _generic_types = get_args(_generic_args)
            if len(args) > len(_generic_types):
                types_ = []
                for generic_type in _generic_types:
                    if type(generic_type) == GenericAlias:
                        types_.append(self._get_generic_type(generic_type))
                    else:
                        types_.append(generic_type)
                is_all_correct = {
                    self._get_type_name(type_arg)
                    for type_arg in (type(arg) for arg in args)
                    if type_arg not in types_
                }
                if len(is_all_correct):
                    raise Warning(f'{self._func_name} {_generic_args} in {kwarg} has no {" and ".join(is_all_correct)} type')
            for arg, _generic_type in zip(args, _generic_types):
                if type(_generic_type) == GenericAlias:
                    self._check_generic(kwarg, arg, _generic_type)
                else:
                    if _generic_type == AnyType: continue
                    if _generic_type == Iterator: continue
                    try:
                        assert isinstance(arg, _generic_type), \
                            f'{self._func_name} {_generic_args} in {kwarg} takes {self._get_type_name(_generic_type)}, ' \
                            f'not {self._get_type_name(type(arg))}'
                    except TypeError as e:
                        print(self._func_name, e)
            _generic_args = self._get_generic_type(_generic_args)
        if _generic_args == Iterator: return
        try:
            assert isinstance(args, _generic_args), \
                f'{self._func_name}  {kwarg} - parameter must be an {self._get_type_name(_generic_args)}, ' \
                f'not a {self._get_type_name(type(args))}.'
        except TypeError as e:
            print(self._func_name, e, args, _generic_args)

    def check_anotations(self, *args, **kwargs):
        for arg, func_arg in zip(args, self._func_args):
            if func_arg == 'self':
                self._func_args.remove('self')
                try:
                    del self._annotations['self']
                except KeyError:
                    ...
                continue
            status = True if func_arg in self._annotations else False
            if status:
                raise Warning(f'{self._func_name}: {func_arg}({arg}) - this argument is not conveyed explicitly.')
            else:
                raise Warning(
                    f'{self._func_name} {func_arg} - the argument has no annotation type. '
                    f'In parameter, data type is a {self._get_type_name(type(arg))}.'
                )
        if len(kwargs) > len(self._func_args):
            raise Warning(f'{self._func_name} The number of parameters passed is more than the function accepts')
        for kwarg, func_arg in zip(kwargs, self._func_args):
            if kwarg != func_arg:
                if not self._defaults:
                    raise Warning(f'{self._func_name} ERROR')
                else:
                    continue
            status = True if kwarg in self._annotations else False
            arg = kwargs[kwarg]
            if status:
                if (_annotation_arg := self._annotations[kwarg]) == Any: continue
                self._check_generic(kwarg, arg, _annotation_arg)
            else:
                raise Warning(
                    f'{self._func_name} {kwarg} - argument has no annotation type. '
                    f'In parameter, data type is a {self._get_type_name(type(arg))}.'
                )

    def check_returns(self, results):
        self._check_generic('results', results, self._returns)

    def main(self, *args, **kwargs):
        self.check_anotations(*args, **kwargs)
        results = self._func(*args, **kwargs)
        if self._returns:
            self.check_returns(results)
        return results

    def __call__(self, *args, **kwargs):
        return self.main(*args, **kwargs)

    @staticmethod
    def typed(func):
        def wrapper(*args, **kwargs):
            return TypedDecorator(func)(*args, **kwargs)
        return wrapper
