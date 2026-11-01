import fractions

from wolframclient.utils.dispatch import Dispatch

encoder = Dispatch()


@encoder.dispatch(fractions.Fraction)
def encode_faction(serializer, o):
    return serializer.serialize_fraction(o)
