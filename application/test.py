from collections.abc import MutableMapping
import typing as T


def flatten_dict2(d: MutableMapping, parent_key: str = '', sep: str = '.') -> MutableMapping:
    items = dict()
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            _data = flatten_dict(v, new_key, sep=sep)
            items = {**items, **_data}
            # items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items[new_key] = v
            # items.append((new_key, v))
    return items


def _flatten_dict_generator(d: MutableMapping, parent_key, seperator: str):
    for key, v in d.items():
        new_kew = f"{parent_key}{seperator}{key}" if parent_key else key
        if isinstance(v, MutableMapping):

            for k, val in flatten_dict(v, new_kew, seperator).items():
                yield k, val

            # yield from flatten_dict(v, new_kew, seperator).items()
        else:
            yield new_kew, v


def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str = '.'):
    return dict(_flatten_dict_generator(d, parent_key, sep))


a = flatten_dict({'a': 1, 'c': {'a': 2, 'b': {'x': 3, 'y': 4, 'z': 5}}, 'd': [{'x': 3, 'y': 4, 'z': 5}, 7, 8]})
print(a)
b = 0
