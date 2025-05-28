
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Регистрируем шрифт с поддержкой кириллицы и Unicode
pdfmetrics.registerFont(TTFont("DejaVu", "./fonts/ttf/DejaVuSans.ttf"))

def create_pdf_report(user_id: int, summary_text: str, image_path_caption_list: list) -> str:
    pdf_path = f"report_{user_id}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # Шрифт для текста
    c.setFont("DejaVu", 10)

    # Страница 1: текст отчёта
    textobject = c.beginText(2 * cm, height - 2 * cm)
    for line in summary_text.split("\n"):
        textobject.textLine(line)
        if textobject.getY() < 2 * cm:
            c.drawText(textobject)
            c.showPage()
            c.setFont("DejaVu", 10)
            textobject = c.beginText(2 * cm, height - 2 * cm)
    c.drawText(textobject)
    c.showPage()

    # Остальные страницы: изображения с подписями
    for img_path, caption in image_path_caption_list:
        if not os.path.exists(img_path):
            continue

        c.setFont("DejaVu", 12)
        c.drawCentredString(width / 2, height - 2 * cm, caption)

        img = ImageReader(img_path)
        iw, ih = img.getSize()
        aspect = ih / iw

        img_width = width - 4 * cm
        img_height = img_width * aspect
        x = 2 * cm
        y = height - img_height - 4 * cm

        if y < 2 * cm:
            c.showPage()
            c.setFont("DejaVu", 12)
            c.drawCentredString(width / 2, height - 2 * cm, caption)
            y = 2 * cm

        c.drawImage(img, x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
        c.showPage()

    c.save()
    return pdf_path
