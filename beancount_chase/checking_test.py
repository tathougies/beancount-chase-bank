import io
import textwrap

import pytest  # NOQA, pylint: disable=unused-import
from beancount.ingest import extract

from . import CheckingImporter


def _unindent(indented):
    return textwrap.dedent(indented).lstrip()


def _stringify_directives(directives):
    f = io.StringIO()
    extract.print_extracted_entries(directives, f)
    return f.getvalue()


def test_identifies_chase_file(tmp_path):
    chase_file = tmp_path / 'Chase1234_Activity_20211019.CSV'
    chase_file.write_text(
        _unindent("""
            Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
            DEBIT,09/13/2021,"Online Transfer 12582403448 to Schwab Personal Checking ########1078 transaction #: 12582403448 09/13",-2500.00,ACCT_XFER,4325.75,,
            """))

    with chase_file.open() as f:
        assert CheckingImporter(account='Assets:Checking:Chase',
                                lastfour='1234').identify(f)


def test_extracts_outbound_transfer(tmp_path):
    chase_file = tmp_path / 'Chase1234_Activity_20211019.CSV'
    chase_file.write_text(
        _unindent("""
            Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
            DEBIT,09/13/2021,"Online Transfer 12345678901 to Schwab Personal Checking ########9876 transaction #: 12345678901 09/13",-2500.00,ACCT_XFER,4325.75,,
            """))

    with chase_file.open() as f:
        directives = CheckingImporter(account='Assets:Checking:Chase',
                                      lastfour='1234').extract(f)

    assert _unindent("""
        2021-09-13 * "Schwab Personal Checking ########9876" "Online Transfer 12345678901 to Schwab Personal Checking ########9876 Transaction #: 12345678901 09/13"
          Assets:Checking:Chase  -2500.00 USD
        """.rstrip()) == _stringify_directives(directives).strip()


def test_extracts_credit(tmp_path):
    chase_file = tmp_path / 'Chase1234_Activity_20211019.CSV'
    chase_file.write_text(
        _unindent("""
            Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
            CREDIT,09/03/2021,"ORIG CO NAME:gumroad.com            ORIG ID:1234567890 DESC DATE:       CO ENTRY DESCR:Gumroad   SEC:CCD    TRACE#:987654321987654 EED:112233   IND ID:ST-JAABBCCDDEEF              IND NAME:MICHAEL CUSTOMER TRN: 1122334455TC",63.84,ACH_CREDIT,7687.53,,
            """))

    with chase_file.open() as f:
        directives = CheckingImporter(account='Assets:Checking:Chase',
                                      lastfour='1234').extract(f)

    assert _unindent("""
        2021-09-03 * "gumroad.com" "Gumroad"
          Assets:Checking:Chase  63.84 USD
        """.rstrip()) == _stringify_directives(directives).strip()