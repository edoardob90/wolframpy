import zoneinfo

from wolframclient.utils.dispatch import Dispatch

encoder = Dispatch()


@encoder.dispatch(zoneinfo.ZoneInfo)
def encode_zoneinfo(serializer, o):
    return serializer.serialize_tzinfo(o)
