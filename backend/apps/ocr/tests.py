from django.test import TestCase

from apps.ocr.extraction import parse_line_items


class LineItemExtractionTests(TestCase):
    def test_parses_a_clean_table(self):
        raw_text = (
            "TAX INVOICE\n"
            "Bluewave Office Supplies Pvt Ltd\n"
            "Invoice Number INV-2026-4821\n"
            "1 A4 Copier Paper (Ream, 500 sheets) 40 320.00 12,800.00\n"
            "2 Ergonomic Office Chair 6 4,800.00 28,800.00\n"
            "3 Whiteboard Markers (Box of 12) 15 180.00 2,700.00\n"
            "Subtotal 44,300.00\n"
            "CGST (9%) 3,987.00\n"
            "SGST (9%) 3,987.00\n"
            "Total Amount 52,274.00\n"
        )
        items = parse_line_items(raw_text)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["description"], "A4 Copier Paper (Ream, 500 sheets)")
        self.assertEqual(items[0]["quantity"], "40")
        self.assertEqual(items[0]["unit_price"], "320.00")
        self.assertEqual(items[0]["amount"], "12800.00")
        self.assertEqual(items[2]["line_no"], "3")

    def test_summary_rows_are_never_mistaken_for_line_items(self):
        raw_text = "Subtotal 44,300.00\nCGST (9%) 3,987.00\nSGST (9%) 3,987.00\nTotal Amount 52,274.00\n"
        self.assertEqual(parse_line_items(raw_text), [])

    def test_no_table_present_returns_empty_list(self):
        raw_text = "DEMO FALLBACK DOCUMENT\nNo OCR engine was available to read this file's contents.\n"
        self.assertEqual(parse_line_items(raw_text), [])

    def test_ignores_unrelated_numeric_lines(self):
        raw_text = "Page 1 of 2\nPhone: 987 654 3210\nGSTIN: 27AAACB1234C1Z5\n"
        self.assertEqual(parse_line_items(raw_text), [])
