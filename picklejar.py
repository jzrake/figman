from pickle import dump, load
from functools import wraps



def picklejar(pk_name, force_reload=False):
    """Function decorator, which causes the result of the decorated function to be
    cached to disk, if not already cached. The name of the pickle file will be
    `pk_name`, if that variable is of type str. Otherwise, if `pk_name` is
    callable, the pickle file name will be pk_name(*args, **kwargs).

    """
    def decorator_function(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if callable(pk_name):
                pkn = pk_name(*args, **kwargs)
            else:
                pkn = pk_name
            def do_reload():
                res = f(*args, **kwargs)
                with open(pkn, 'w') as fout:
                    dump(res, fout)
                return res
            class Reload(Exception): pass
            try:
                if force_reload:
                    raise Reload
                with open(pkn, 'r') as fin:
                    print "[picklejar] loading result from {0}".format(pkn)
                    res = load(fin)
            except IOError:
                print "[picklejar] no result cached; create {0}".format(pkn)
                res = do_reload()
            except Reload:
                print "[picklejar] force_reload=True; regen {0}".format(pkn)
                res = do_reload()
            return res
        return wrapper
    return decorator_function



if __name__ == "__main__":
    import os

    @picklejar('test.pk', force_reload=False)
    def testfunc1():
        """the docs"""
        return 'success'

    @picklejar(lambda a: "{0}.pk".format(a))
    def testfunc2(a):
        return a + ' and eggs'

    assert(testfunc1() == 'success')
    assert(testfunc1.__doc__ == "the docs")
    assert(testfunc2('spam') == 'spam and eggs')
    assert(testfunc2('spam') == 'spam and eggs')
    assert(os.path.isfile('spam.pk'))

    os.remove('test.pk')
    os.remove('spam.pk')
