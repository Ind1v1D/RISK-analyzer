from io import BytesIO

import pytest

import extraction
from extraction import ExtractionError, extract_text, prepare_pasted_text

LONG = "This agreement is made between the parties for services rendered. " * 2


def test_txt_utf8_is_decoded():
    assert extract_text("a.txt", ("Договор: " + LONG).encode("utf-8")).startswith("Договор")


def test_txt_with_bom_has_bom_removed():
    assert extract_text("a.txt", b"\xef\xbb\xbf" + LONG.encode()).startswith("This")


def test_txt_cp1252_fallback_is_decoded():
    text = extract_text("a.txt", ("Café " + LONG).encode("cp1252"))
    assert text.startswith("Café")


def test_txt_undecodable_bytes_raise_bad_encoding():
    # 0x81 is invalid in utf-8 and undefined in cp1252
    with pytest.raises(ExtractionError) as err:
        extract_text("a.txt", b"\x81\x8d\x8f" * 40)
    assert err.value.key == "bad_encoding"


def test_unsupported_type_is_rejected_with_extension():
    with pytest.raises(ExtractionError) as err:
        extract_text("pic.png", b"xxxx")
    assert err.value.key == "unsupported_type"
    assert err.value.params["ext"] == "png"


def test_file_without_extension_is_unsupported():
    with pytest.raises(ExtractionError) as err:
        extract_text("README", b"xxxx")
    assert err.value.key == "unsupported_type"


def test_too_short_text_raises_no_text():
    with pytest.raises(ExtractionError) as err:
        extract_text("a.txt", b"too short")
    assert err.value.key == "no_text"


def test_pasted_text_too_short_raises_text_too_short():
    with pytest.raises(ExtractionError) as err:
        prepare_pasted_text("  short  ")
    assert err.value.key == "text_too_short"


def test_pasted_text_is_cleaned_like_uploads():
    text = prepare_pasted_text("Line one.   \r\n\r\n\r\n\r\n" + LONG)
    assert "\r" not in text
    assert "\n\n\n" not in text
    assert "one.\n\nThis" in text


def _docx_bytes(paragraphs, table=None):
    from docx import Document

    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    if table:
        t = doc.add_table(rows=len(table), cols=len(table[0]))
        for r, row in enumerate(table):
            for c, val in enumerate(row):
                t.cell(r, c).text = val
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_docx_paragraphs_are_extracted():
    text = extract_text("c.docx", _docx_bytes([LONG, "Second paragraph here."]))
    assert "Second paragraph here." in text


def test_docx_table_cells_are_included():
    data = _docx_bytes([LONG], table=[["Fee", "$500"], ["Due", "Net 60"]])
    text = extract_text("c.docx", data)
    assert "Fee | $500" in text
    assert "Due | Net 60" in text


def test_broken_docx_raises_docx_unreadable():
    with pytest.raises(ExtractionError) as err:
        extract_text("c.docx", b"not a zip")
    assert err.value.key == "docx_unreadable"


def test_broken_pdf_raises_pdf_unreadable():
    with pytest.raises(ExtractionError) as err:
        extract_text("c.pdf", b"%PDF-garbage")
    assert err.value.key == "pdf_unreadable"


def test_password_protected_pdf_raises_pdf_encrypted():
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(200, 200)
    try:
        writer.encrypt("secret", algorithm="RC4-128")
    except Exception:
        pytest.skip("encryption backend unavailable")
    buf = BytesIO()
    writer.write(buf)
    with pytest.raises(ExtractionError) as err:
        extract_text("c.pdf", buf.getvalue())
    assert err.value.key == "pdf_encrypted"


# ---- PDF cleanup helpers ------------------------------------------------------

def test_hyphenated_line_break_is_joined():
    assert extraction.join_hyphenated("the termi-\nnation clause") == "the termination clause"


def test_hyphen_before_uppercase_is_kept():
    assert extraction.join_hyphenated("Smith-\nJones") == "Smith-\nJones"


def test_wrapped_lines_are_rejoined_into_one_paragraph():
    out = extraction.rejoin_lines(["The Contractor shall deliver", "the work on time and", "in full."])
    assert out == "The Contractor shall deliver the work on time and in full."


def test_blank_line_is_kept_as_paragraph_break():
    out = extraction.rejoin_lines(["First paragraph ends.", "", "Second one starts."])
    assert out == "First paragraph ends.\n\nSecond one starts."


@pytest.mark.parametrize(
    "start", ["1. Payment is due", "2.1 The client shall", "(a) the first", "- a bullet", "• a bullet"]
)
def test_numbered_clauses_and_bullets_start_new_lines(start):
    out = extraction.rejoin_lines(["The text continues without a period", start])
    assert out.split("\n")[1] == start


def test_heading_stays_on_its_own_line():
    out = extraction.rejoin_lines(["TERMINATION", "Either party may end this agreement."])
    assert out == "TERMINATION\nEither party may end this agreement."


def test_short_numbered_title_is_not_merged_with_body():
    out = extraction.rejoin_lines(["3. Payment", "The client pays monthly."])
    assert out == "3. Payment\nThe client pays monthly."


@pytest.mark.parametrize("line", ["Page 3 of 10", "page 3", "- 3 -", "3", "3 / 10", "Стр. 4 из 9"])
def test_page_number_lines_are_detected(line):
    assert extraction.is_page_number_line(line)


def test_normal_text_is_not_a_page_number():
    assert not extraction.is_page_number_line("Section 3 applies")


def test_page_numbers_removed_from_page_edges():
    lines = ["Body text here.", "More body.", "Page 2 of 9"]
    assert extraction.strip_page_numbers(lines) == ["Body text here.", "More body."]


def test_bare_number_in_page_middle_is_kept():
    lines = ["a", "b", "c", "d", "42", "e", "f", "g", "h"]
    assert "42" in extraction.strip_page_numbers(lines)


def test_repeated_header_and_footer_removed_across_pages():
    def body(i):
        return [f"Clause text {i}.{n} says something unique." for n in range(4)]

    pages = [["ACME Confidential", *body(i), f"Footer v1 - {i}"] for i in range(1, 5)]
    cleaned = extraction.remove_repeated_edges(pages)
    assert cleaned == [body(i) for i in range(1, 5)]


def test_header_repetition_needs_three_pages():
    pages = [["Header", "Body 1."], ["Header", "Body 2."]]
    assert extraction.remove_repeated_edges(pages) == pages


def test_unique_edge_lines_are_kept():
    names = ["Payment", "Term", "Liability", "Notices"]
    pages = [[f"{n} heading", f"Body of {n}.", f"More about {n}.", f"End of {n}."] for n in names]
    assert extraction.remove_repeated_edges(pages) == pages


def test_full_pdf_cleanup_pipeline():
    pages = [
        "ACME Corp\n1. Services\nThe contractor shall pro-\nvide services and\nkeep records.\nPage 1 of 3",
        "ACME Corp\nThe fee is payable\nwithin 30 days.\n- 2 -",
        "ACME Corp\n2. Term\nThis runs one year.\n3",
    ]
    out = extraction.clean_pdf_pages(pages)
    assert out == (
        "1. Services\n"
        "The contractor shall provide services and keep records.\n"
        "The fee is payable within 30 days.\n"
        "2. Term\n"
        "This runs one year."
    )
