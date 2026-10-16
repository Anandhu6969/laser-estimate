"""Create a printable, one-page client quotation from saved estimate data."""

from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


class QuotationPdfService:
    """Render saved estimate amounts with configurable company quotation details."""

    @staticmethod
    def _money(value):
        # Use selectable ASCII currency text; Indian grouping is kept for amounts.
        value = float(value or 0)
        whole, fraction = f"{abs(value):.2f}".split(".")
        if len(whole) > 3:
            whole = whole[:-3] + "," + whole[-3:]
            prefix, rest = whole.split(",", 1)
            while len(prefix) > 2:
                rest = prefix[-2:] + "," + rest
                prefix = prefix[:-2]
            whole = prefix + "," + rest
        return ("-" if value < 0 else "") + "Rs. " + whole + "." + fraction

    @staticmethod
    def _wrap(text, max_width, font="Helvetica", size=8):
        words = str(text or "").replace("\n", " ").split()
        lines, line = [], ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and stringWidth(candidate, font, size) > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines or [""]

    @classmethod
    def generate(cls, estimate, settings, output_path):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not estimate.estimate_number:
            raise ValueError("Estimate number is missing.")

        c = canvas.Canvas(str(path), pagesize=A4)
        c.setTitle(f"Quotation {estimate.estimate_number}")
        c.setAuthor("UNIVERSAL AGRICO")
        page_width, page_height = A4
        left, right = 34, page_width - 34
        width = right - left
        top = page_height - 28
        ink = colors.HexColor("#333333")
        pale = colors.HexColor("#F2F4F7")

        def box(x, y_top, box_width, box_height, fill=None):
            c.setStrokeColor(ink)
            c.setLineWidth(0.55)
            if fill:
                c.setFillColor(fill)
                c.rect(x, y_top - box_height, box_width, box_height, fill=1, stroke=1)
            else:
                c.rect(x, y_top - box_height, box_width, box_height, fill=0, stroke=1)

        def text(x, y, value, size=8, bold=False):
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            c.drawString(x, y, str(value or ""))

        def wrap_lines(value, max_width, font="Helvetica", size=8):
            result = []
            for paragraph in str(value or "").splitlines() or [""]:
                result.extend(cls._wrap(paragraph, max_width, font, size))
            return result

        # Fixed company template and configurable contact details.
        header_height = 94
        box(left, top, width, header_height)
        text(left + 12, top - 22, "UNIVERSAL AGRICO", 15, True)
        for index, line in enumerate((
            "SIDCO INDUSTRIAL ESTATE",
            "KULAPPULLY,SHORNUR-2",
            "PALAKKAD",
        )):
            text(left + 12, top - 39 - index * 11, line, 8)

        contact_x = left + width * 0.62
        contact_rows = (
            ("GSTIN :", settings.get("company_gstin", "")),
            ("Mob   :", settings.get("company_mobile", "")),
            ("Ph    :", settings.get("company_phone", "")),
            ("Email :", settings.get("company_email", "")),
        )
        for index, (label, value) in enumerate(contact_rows):
            y = top - 22 - index * 15
            text(contact_x, y, label, 8, True)
            text(contact_x + 48, y, value, 8)

        y = top - header_height
        title_height = 30
        box(left, y, width, title_height, pale)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString((left + right) / 2, y - 20, "QUOTATION")
        y -= title_height

        reference_height = 30
        box(left, y, width, reference_height)
        text(left + 10, y - 19, "Quotation No:", 8, True)
        text(left + 88, y - 19, estimate.estimate_number, 9, True)
        text(right - 145, y - 19, "Date:", 8, True)
        text(right - 112, y - 19, estimate.date or "", 9)
        y -= reference_height

        terms_height = 34
        box(left, y, width, terms_height)
        text(left + 9, y - 13, "Terms Of Delivery & Payment", 8, True)
        text(left + 9, y - 26, settings.get("quotation_terms", ""), 8)
        y -= terms_height

        customer_height = 83
        box(left, y, width, customer_height)
        text(left + 9, y - 14, "Name & Address of Purchasing Dealer:", 8, True)
        text(left + 9, y - 29, getattr(estimate, "customer_name", ""), 9, True)
        address_lines = wrap_lines(getattr(estimate, "customer_address", ""), width - 18, size=8)
        address_y = y - 42
        for line in address_lines[:2]:
            text(left + 9, address_y, line, 8)
            address_y -= 10
        text(left + 9, y - 72, "Phone :", 8, True)
        text(left + 52, y - 72, estimate.phone or "", 8)
        y -= customer_height

        # A single customer-facing table populated only from saved estimate
        # amounts. Internal weight, kilo-rate, and time details stay private.
        columns = [
            ("Sl No", 34), ("Material", 118), ("Material Rate", 73),
            ("Cutting Rate", 73), ("Rate Per Unit", 76), ("Quantity", 48),
            ("Total Rate", width - 422),
        ]
        header_height, row_height = 34, 58
        box(left, y, width, header_height, pale)
        x = left
        for label, column_width in columns:
            box(x, y, column_width, header_height, pale)
            label_lines = wrap_lines(label, column_width - 6, "Helvetica-Bold", 7)
            for index, line in enumerate(label_lines[:2]):
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 7)
                c.drawCentredString(x + column_width / 2, y - 13 - index * 9, line)
            x += column_width
        y -= header_height

        material = " ".join(part for part in (
            (estimate.material or "").strip(),
            f"{estimate.thickness:g} {estimate.thickness_unit}" if estimate.thickness else "",
        ) if part)
        row_values = [
            "1", material, cls._money(estimate.material_amount),
            cls._money(estimate.cutting_amount), cls._money(estimate.per_piece_amount),
            str(estimate.quantity), cls._money(estimate.final_amount),
        ]
        box(left, y, width, row_height)
        x = left
        for (_, column_width), value in zip(columns, row_values):
            box(x, y, column_width, row_height)
            lines = wrap_lines(value, column_width - 8, size=7)
            for index, line in enumerate(lines[:4]):
                text(x + 4, y - 14 - index * 10, line, 7.5)
            x += column_width
        y -= row_height

        net_height = 30
        box(left, y, width, net_height, pale)
        text(right - 176, y - 20, "Net Amount :", 10, True)
        text(right - 95, y - 20, cls._money(estimate.final_amount), 10, True)
        y -= net_height

        # Bank details and signatory use a fixed bottom footer like the sample.
        footer_height = 112
        footer_top = 34 + footer_height
        box(left, footer_top, width, footer_height)
        text(left + 9, footer_top - 15, "BANK DETAILS :", 8, True)
        bank_rows = (
            ("ACCOUNT NAME:", "bank_account_name"),
            ("BANK NAME:", "bank_name"),
            ("ACC NO:", "bank_account_number"),
            ("BRANCH NAME:", "bank_branch"),
            ("IFSC CODE:", "bank_ifsc"),
        )
        for index, (label, key) in enumerate(bank_rows):
            text(left + 9, footer_top - 29 - index * 13, f"{label} {settings.get(key, '')}", 7)
        text(right - 160, footer_top - 34, "Generated by :", 8, True)
        text(right - 97, footer_top - 34, getattr(estimate, "employee_name", "") or "", 8)
        text(right - 160, footer_top - 52, "FOR UNIVERSAL AGRICO", 8, True)
        c.line(right - 155, footer_top - 80, right - 12, footer_top - 80)
        c.setFont("Helvetica", 8)
        c.drawRightString(right - 12, footer_top - 96, "Authorised signatory")

        c.save()
        return str(path)


def quotation_filename(estimate_number):
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", estimate_number or "quotation").strip("._")
    return (safe or "quotation") + ".pdf"


def ensure_pdf_extension(filename):
    """Return a path with exactly one PDF extension."""
    path = Path(filename)
    if path.suffix.lower() == ".pdf":
        return path
    return path.with_suffix(".pdf") if path.suffix else Path(f"{path}.pdf")
