"""This is a module for functions I consider to be designed to work around
Python doing entirely the wrong thing.

You can imagine how grumpy I was when I wrote it.

"""

from hypothesis.internal.compat import text_type, binary_type, integer_types
import math
from hypothesis.internal.extmethod import ExtMethod


equality = ExtMethod()


unordered_collections = [set, frozenset]
dict_like_collections = [dict]
primitives = [
    int, float, bool, type, text_type, binary_type
] + list(integer_types)


@equality.extend(object)
@equality.extend(type)
def generic_equality(x, y, fuzzy):
    return x == y


@equality.extend(float)
def float_equality(x, y, fuzzy=False):
    if math.isnan(x) and math.isnan(y):
        return True
    if fuzzy:
        return repr(x) == repr(y)
    return x == y


@equality.extend(complex)
def complex_equality(x, y, fuzzy=False):
    return (
        float_equality(x.real, y.real, fuzzy) and
        float_equality(x.imag, y.imag, fuzzy)
    )


@equality.extend(tuple)
@equality.extend(list)
def sequence_equality(x, y, fuzzy=False):
    if len(x) != len(y):
        return False
    for u, v in zip(x, y):
        if not actually_equal(u, v, fuzzy):
            return False
    return True


@equality.extend(set)
@equality.extend(frozenset)
def set_equality(x, y, fuzzy=False):
    if len(x) != len(y):
        return False
    for u in x:
        if not actually_in(u, y):
            return False
    return True


@equality.extend(dict)
def dict_equality(x, y, fuzzy=False):
    if len(x) != len(y):
        return False
    for k, v in x.items():
        if k not in y:
            return False
        if not actually_equal(x[k], y[k], fuzzy):
            return False
    return True


def actually_equal(x, y, fuzzy=False):
    """
    Look, this function is terrible. I know it's terrible. I'm sorry.
    Hypothesis relies on a more precise version of equality than python uses
    and in particular is broken by things like frozenset() == set() because
    that behaviour is just broken.

    Unfortunately this means that we have to define our own equality. We do
    our best to respect the equality defined on types but there's only so much
    we can do.

    If fuzzy is True takes a slightly laxer approach around e.g. floating point
    equality.
    """
    if x is y:
        return True
    if type(x) != type(y):
        return False
    return equality(type(x), x, y, fuzzy)


def actually_in(x, ys, fuzzy=False):
    return any(actually_equal(x, y, fuzzy) for y in ys)


def real_index(xs, y, fuzzy=False):
    i = xs.index(y)
    if actually_equal(xs[i], y, fuzzy):
        return i
    else:
        i = 0
        while i < len(xs):
            if actually_equal(xs[i], y, fuzzy):
                return i
            i += 1
        raise ValueError('%r is not in list' % (y))
