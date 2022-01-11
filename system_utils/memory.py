import ctypes

def malloc_trim():
    ctypes.CDLL('libc.so.6').malloc_trim(0) 