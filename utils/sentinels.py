"""
classes that produce sentinel values (e.g., missing types etc)
"""


__all__ = [
    'MissingType'
]


class MissingType:
    """
    Missing type. The value `MissingType(NAME)` is a singleton.
    """

    def __new__(cls, name=None, *args, **kwargs):
        instance_name = f'_instance_{name}'
        if not hasattr(cls, instance_name):
            instance = super().__new__(cls, *args, **kwargs)
            instance.name = name
            setattr(cls, instance_name, instance)
        return getattr(cls, instance_name)

    def __copy__(self):
        return self

    def __deepcopy__(self, memodict={}):  # noqa
        return self

    def __repr__(self) -> str:
        name = self.name if self.name is not None else ''
        return f'{type(self).__name__}({name})'

    def __str__(self) -> str:
        name = f'[{self.name}]' if self.name is not None else ''
        return f'Missing{name}'


def _main():
    # TODO: move to tests/

    import copy

    missing1 = MissingType()
    missing2 = MissingType('hello')

    # should be True
    print(missing1)
    print(missing1 == MissingType())
    print(missing1 is MissingType())
    print(missing1 is copy.copy(MissingType()))
    print(missing1 is copy.deepcopy(MissingType()))
    print()

    # should be False
    print(missing2)
    print(missing1 == missing2)
    print(missing1 is missing2)
    print(missing1 is copy.copy(missing2))
    print(missing1 is copy.deepcopy(missing2))
    print()


if __name__ == '__main__':
    _main()
