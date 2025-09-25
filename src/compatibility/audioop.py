"""
Mock audioop module for Python 3.13 compatibility
This module provides stub implementations to allow speech_recognition to work
"""

# Mock audioop functions that speech_recognition expects
def add(fragment1, fragment2, width):
    """Mock add function"""
    return fragment1

def bias(fragment, width, bias):
    """Mock bias function"""
    return fragment

def byteswap(fragment, width):
    """Mock byteswap function"""
    return fragment

def cross(fragment, width):
    """Mock cross function"""
    return 0.0

def findfactor(fragment, reference):
    """Mock findfactor function"""
    return 1.0

def findfit(fragment, reference):
    """Mock findfit function"""
    return (1.0, 0)

def findmax(fragment, width):
    """Mock findmax function"""
    return 0

def getsample(fragment, width, index):
    """Mock getsample function"""
    return 0

def lin2lin(fragment, width, newwidth):
    """Mock lin2lin function"""
    return fragment

def lin2adpcm(fragment, width, state):
    """Mock lin2adpcm function"""
    return (fragment, (0, 0))

def adpcm2lin(fragment, width, state):
    """Mock adpcm2lin function"""
    return (fragment, (0, 0))

def lin2ulaw(fragment, width):
    """Mock lin2ulaw function"""
    return fragment

def ulaw2lin(fragment, width):
    """Mock ulaw2lin function"""
    return fragment

def lin2alaw(fragment, width):
    """Mock lin2alaw function"""
    return fragment

def alaw2lin(fragment, width):
    """Mock alaw2lin function"""
    return fragment

def lin2lin(fragment, width, newwidth):
    """Mock lin2lin function"""
    return fragment

def max(fragment, width):
    """Mock max function"""
    return 0

def minmax(fragment, width):
    """Mock minmax function"""
    return (0, 0)

def avg(fragment, width):
    """Mock avg function"""
    return 0.0

def rms(fragment, width):
    """Mock rms function"""
    return 0.0

def mul(fragment, width, factor):
    """Mock mul function"""
    return fragment

def ratecv(fragment, width, nchannels, inrate, outrate, state, weightA=1, weightB=0):
    """Mock ratecv function"""
    return (fragment, (0, 0))

def reverse(fragment, width):
    """Mock reverse function"""
    return fragment

def tomono(fragment, width, lfactor, rfactor):
    """Mock tomono function"""
    return fragment

def tostereo(fragment, width, lfactor, rfactor):
    """Mock tostereo function"""
    return fragment

def error2string(code):
    """Mock error2string function"""
    return "No error"

# Mock constants that might be expected
ERROR = -1
