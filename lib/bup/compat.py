
from __future__ import absolute_import, print_function
from array import array
from traceback import print_exception
import sys

# Please see CODINGSTYLE for important exception handling guidelines
# and the rationale behind add_ex_tb(), add_ex_ctx(), etc.

py_maj = sys.version_info[0]
py3 = py_maj >= 3

if py3:

    from shlex import quote
    range = range
    str_type = str

    def add_ex_tb(ex):
        """Do nothing (already handled by Python 3 infrastructure)."""
        return ex

    def add_ex_ctx(ex, context_ex):
        """Do nothing (already handled by Python 3 infrastructure)."""
        return ex

    def items(x):
        return x.items()

    def bytes_from_uint(i):
        return bytes((i,))

    byte_int = lambda x: x

    def buffer(object, offset=None, size=None):
        if size:
            assert offset is not None
            return memoryview(object)[offset:offset + size]
        if offset:
            return memoryview(object)[offset:]
        return memoryview(object)

    def buffer_concat(b1, b2):
        if isinstance(b1, memoryview):
            b1 = b1.tobytes()
        if isinstance(b1, memoryview):
            b2 = b2.tobytes()
        return b1 + b2

else:  # Python 2

    from pipes import quote
    range = xrange
    str_type = basestring

    def add_ex_tb(ex):
        """Add a traceback to ex if it doesn't already have one.  Return ex.

        """
        if not getattr(ex, '__traceback__', None):
            ex.__traceback__ = sys.exc_info()[2]
        return ex

    def add_ex_ctx(ex, context_ex):
        """Make context_ex the __context__ of ex (unless it already has one).
        Return ex.

        """
        if context_ex:
            if not getattr(ex, '__context__', None):
                ex.__context__ = context_ex
        return ex

    def dump_traceback(ex):
        stack = [ex]
        next_ex = getattr(ex, '__context__', None)
        while next_ex:
            stack.append(next_ex)
            next_ex = getattr(next_ex, '__context__', None)
        stack = reversed(stack)
        ex = next(stack)
        tb = getattr(ex, '__traceback__', None)
        print_exception(type(ex), ex, tb)
        for ex in stack:
            print('\nDuring handling of the above exception, another exception occurred:\n',
                  file=sys.stderr)
            tb = getattr(ex, '__traceback__', None)
            print_exception(type(ex), ex, tb)

    def items(x):
        return x.iteritems()

    def bytes_from_uint(i):
        return chr(i)

    byte_int = ord

    def buffer_concat(b1, b2):
        return b1 + b2


def wrap_main(main):
    """Run main() and raise a SystemExit with the return value if it
    returns, pass along any SystemExit it raises, convert
    KeyboardInterrupts into exit(130), and print a Python 3 style
    contextual backtrace for other exceptions in both Python 2 and
    3)."""
    try:
        sys.exit(main())
    except KeyboardInterrupt as ex:
        sys.exit(130)
    except SystemExit as ex:
        raise
    except BaseException as ex:
        if py3:
            raise
        add_ex_tb(ex)
        dump_traceback(ex)
        sys.exit(1)


# Excepting wrap_main() in the traceback, these should produce similar output:
#   python2 lib/bup/compat.py
#   python3 lib/bup/compat.py
# i.e.:
#   diff -u <(python2 lib/bup/compat.py 2>&1) <(python3 lib/bup/compat.py 2>&1)
#
# Though the python3 output for 'second' will include a stacktrace
# starting from wrap_main, rather than from outer().

if __name__ == '__main__':

    def inner():
        raise Exception('first')

    def outer():
        try:
            inner()
        except Exception as ex:
            add_ex_tb(ex)
            try:
                raise Exception('second')
            except Exception as ex2:
                raise add_ex_ctx(add_ex_tb(ex2), ex)

    wrap_main(outer)
