from __future__ import absolute_import, print_function, unicode_literals

import datetime
import decimal
import fractions
import os
import unittest
from collections import OrderedDict
from contextlib import contextmanager

from wolframclient.language import Global, System, wl, wlexpr
from wolframclient.serializers import export
from wolframclient.utils import six
from wolframclient.utils.api import timezone
from wolframclient.utils.datastructures import Association
from wolframclient.utils.encoding import force_bytes, force_text
from unittest import TestCase as BaseTestCase
from tests.configure import path_to_file_in_data_dir

PLUS_ONE_HOUR = datetime.timezone(datetime.timedelta(hours=1))


@contextmanager
def with_version(n):

    prev = os.environ.get("WOLFRAM_KERNEL_VERSION", None)

    os.environ["WOLFRAM_KERNEL_VERSION"] = force_text(n)

    yield n

    if prev:
        os.environ["WOLFRAM_KERNEL_VERSION"] = prev
    else:
        del os.environ["WOLFRAM_KERNEL_VERSION"]


def sample_datetime():
    return datetime.datetime(year=2000, month=1, day=1, hour=11, minute=15, second=20)


# you can run those tests by doing
# > python wolfram.py test wolfram.tests.serialization


class TestCase(BaseTestCase):
    def dumps(self, data, target_format="wl", **opts):
        return export(data, target_format=target_format, **opts)

    def compare(self, data, output=None, **opts):

        if isinstance(output, six.binary_type):
            self.assertEqual(self.dumps(data, **opts), output)
        else:
            self.assertEqual(self.dumps(data, **opts), self.dumps(output, **opts))

    def test_serialization(self):

        self.compare([1, 2, 3], b"{1, 2, 3}")

        # instances of dict are converted using RuleDelayed

        self.compare(
            OrderedDict(enumerate([2, True, False])), b"<|0 -> 2, 1 -> True, 2 -> False|>"
        )

        # instances of Association are converted using Rule, in WXF they use WXFFunction

        self.compare(Association(enumerate("abc")), b'<|0 -> "a", 1 -> "b", 2 -> "c"|>')

        self.compare({"a": 2}, b'<|"a" -> 2|>')

        self.compare(wl.YetAnotherSymbol, b"YetAnotherSymbol")
        self.compare(wl.Expression(1, 2, 3), b"Expression[1, 2, 3]")
        self.compare(
            wl.CurriedExpression(1, 2, 3)(4, 5, 6), b"CurriedExpression[1, 2, 3][4, 5, 6]"
        )

        self.compare(System.YetAnotherSymbol, b"System`YetAnotherSymbol")
        self.compare(System.Expression(1, 2, 3), b"System`Expression[1, 2, 3]")
        self.compare(
            System.CurriedExpression(1, 2, 3)(4, 5, 6),
            b"System`CurriedExpression[1, 2, 3][4, 5, 6]",
        )

        self.compare(System.Expression(1, a=2), b"System`Expression[1, Rule[a, 2]]")

        self.compare(Global.YetAnotherSymbol, b"Global`YetAnotherSymbol")
        self.compare(Global.Expression(1, 2, 3), b"Global`Expression[1, 2, 3]")
        self.compare(
            Global.CurriedExpression(1, 2, 3)(4, 5, 6),
            b"Global`CurriedExpression[1, 2, 3][4, 5, 6]",
        )

        self.compare(Global.Expression(1, a=2), b"Global`Expression[1, Rule[a, 2]]")

    def test_datetime(self):

        self.compare(
            sample_datetime(),
            b'DateObject[{2000, 1, 1, 11, 15, 20.}, "Instant", "Gregorian", None]',
        )

        with with_version(11):
            self.compare(
                sample_datetime(),
                b'DateObject[{2000, 1, 1, 11, 15, 20.}, "Instant", "Gregorian", $TimeZone]',
            )

        self.compare(
            sample_datetime().replace(tzinfo=PLUS_ONE_HOUR),
            b'DateObject[{2000, 1, 1, 11, 15, 20.}, "Instant", "Gregorian", 1.]',
        )

        self.compare(
            sample_datetime().replace(tzinfo=timezone.ZoneInfo("Europe/Rome")),
            b'DateObject[{2000, 1, 1, 11, 15, 20.}, "Instant", "Gregorian", "Europe/Rome"]',
        )

    def test_date(self):

        self.compare(
            sample_datetime().date(), b'DateObject[{2000, 1, 1}, "Day", "Gregorian", None]'
        )

    def test_timedelta(self):

        self.compare(datetime.timedelta(minutes=1, seconds=30), b'Quantity[90., "Seconds"]')

    def test_time(self):

        self.compare(sample_datetime().time(), b"TimeObject[{11, 15, 20.}]")
        self.compare(
            sample_datetime().replace(tzinfo=PLUS_ONE_HOUR).timetz(),
            b"TimeObject[{11, 15, 20.}, TimeZone -> 1.]",
        )

    def test_symbol_factory(self):

        self.compare(wl.Map, b"Map")
        self.compare(wl.Map(wl.PrimeQ, (1, 2, 3)), b"Map[PrimeQ, {1, 2, 3}]")
        self.compare(wl.System.Map, b"System`Map")
        self.compare(wl.System.Symbol(1, 2), b"System`Symbol[1, 2]")
        self.compare(wl.This.Thing.Just.Works, b"This`Thing`Just`Works")
        self.compare(wl.This.Thing.Just.Works(1, 2), b"This`Thing`Just`Works[1, 2]")

    def test_encoding(self):

        self.compare("\t", b'"\\t"')
        self.compare("\n", b'"\\n"')
        self.compare("a\\", b'"a\\\\"')

    def test_numeric(self):

        prec = decimal.getcontext().prec

        self.compare(decimal.Decimal(10**20), force_bytes("100000000000000000000``%i" % prec))
        self.compare(decimal.Decimal("100"), force_bytes("100``%i" % prec))
        self.compare(decimal.Decimal("100.00"), force_bytes("100.00``%i" % prec))
        self.compare(decimal.Decimal("0.010"), force_bytes("0.010``%i" % prec))
        self.compare(decimal.Decimal("0.1534"), force_bytes("0.1534``%i" % prec))
        self.compare(decimal.Decimal("0.0000000010"), force_bytes("0.0000000010``%i" % prec))

        self.compare(decimal.Decimal("0"), force_bytes("0``%i" % prec))
        self.compare(decimal.Decimal("0.0"), force_bytes("0.0``%i" % prec))
        self.compare(decimal.Decimal("0.0000000000"), force_bytes("0.0000000000``%i" % prec))

        self.compare(fractions.Fraction(1, 2), wl.Rational(1, 2))

        self.compare(float("0.150000"), b"0.15")

        for special, result in (
            [float("inf"), self.dumps(wl.DirectedInfinity(1))],
            [float("-inf"), self.dumps(wl.DirectedInfinity(-1))],
            [float("nan"), self.dumps(wl.Indeterminate)],
        ):
            self.compare(special, result)
            self.compare(decimal.Decimal(special), result)

    def test_buffer(self):

        self.compare(memoryview(b"Hello world"), b'ByteArray["SGVsbG8gd29ybGQ="]')

    def test_hashing(self):

        # testing that expressions class is hashable

        self.compare(
            Association(
                [[wl.a, wl.a(2)], [wl.a, wl.a(3)], [wl.a(2), wl.a(2)], [wl.a(2), wl.a(3)]]
            ),
            b"<|a -> a[3], a[2] -> a[3]|>",
        )

        self.assertEqual(wl.a == wl.a, True)
        self.assertEqual(wl.a(2) == wl.a(2), True)
        self.assertEqual(wl.a(2, wl.b) == wl.a(2, wl.b), True)

    def test_input_form(self):

        self.compare(wlexpr('<|"2" -> 2|>'), b'(<|"2" -> 2|>)')

        self.compare(
            wl.Foo(2, wlexpr("#foo &")(wlexpr('<|"foo" -> 2|>'))),
            b'Foo[2, (#foo &)[(<|"foo" -> 2|>)]]',
        )
