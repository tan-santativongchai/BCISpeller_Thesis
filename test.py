import multiprocessing
from functools import partial
from contextlib import contextmanager

@contextmanager
def poolcontext(*args, **kwargs):
    pool = multiprocessing.Pool(*args, **kwargs)
    yield pool
    pool.terminate()

def merge_names(a, b):
    return a+b

if __name__ == '__main__':
    names = range(10)
    with poolcontext(processes=3) as pool:
        results = pool.map(partial(merge_names, b=2), names)
    print(results)