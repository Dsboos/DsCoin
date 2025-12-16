from functools import singledispatch

@singledispatch
def hash_info(obj):
    raise TypeError(f"Hash info function not defined for {type(obj)}")