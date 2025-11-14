import io
import os
import tempfile
import chardet
import magic
from pathlib import Path

import pdfplumber

from docx import Document

from odf import text, teletype
from odf.opendocument import load as odf_load

from bs4 import BeautifulSoup

import pandas as pd

try:
    import ebooklib
    from ebooklib import epub
    HAS_EPUB = True
except ImportError:
    HAS_EPUB = False


class DocumentTextExtractor:
    """
    Универсальный парсер текста из байтов документа.
    Поддерживает: txt, pdf, docx, odt, rtf, html, xml, csv, xlsx, epub (опционально), doc (ограниченно).
    """

    def __call__(self, file_bytes: bytes, filename: str = None) -> str:
        """
        Основной метод: принимает байты документа и возвращает извлечённый текст.
        :param file_bytes: содержимое файла в виде bytes
        :param filename: опционально — имя файла (для уточнения формата, если mime не определяется)
        :return: извлечённый текст в виде строки
        """
        if not isinstance(file_bytes, bytes):
            raise TypeError("Input must be bytes")

        # Определяем MIME-тип через python-magic
        mime = magic.from_buffer(file_bytes, mime=True)

        # Если mime не определился, попробуем по расширению (если filename есть)
        if mime == 'application/octet-stream' and filename:
            suffix = Path(filename).suffix.lower()
            mime_map = {
                '.doc': 'application/msword',
                '.rtf': 'text/rtf',
                '.epub': 'application/epub+zip',
            }
            mime = mime_map.get(suffix, mime)

        try:
            if mime == 'text/plain':
                return self._extract_txt(file_bytes)
            elif mime == 'application/pdf':
                return self._extract_pdf(file_bytes)
            elif mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return self._extract_docx(file_bytes)
            elif mime == 'application/vnd.oasis.opendocument.text':
                return self._extract_odt(file_bytes)
            elif mime in ('text/html', 'application/xhtml+xml'):
                return self._extract_html(file_bytes)
            elif mime == 'text/xml' or mime == 'application/xml':
                return self._extract_xml(file_bytes)
            elif mime == 'text/rtf':
                return self._extract_rtf(file_bytes)
            elif mime == 'text/csv':
                return self._extract_csv(file_bytes)
            elif mime in (
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ):
                return self._extract_xlsx(file_bytes)
            elif mime == 'application/epub+zip' and HAS_EPUB:
                return self._extract_epub(file_bytes)
            elif mime == 'application/msword':
                return self._extract_doc(file_bytes)
            else:
                # fallback: попробуем как plain text
                return self._extract_txt(file_bytes)
        except Exception as e:
            raise ValueError(f"Failed to extract text from document (MIME: {mime}): {e}")

    def _extract_txt(self, data: bytes) -> str:
        encoding = chardet.detect(data)['encoding'] or 'utf-8'
        return data.decode(encoding, errors='replace')

    def _extract_pdf(self, data: bytes) -> str:
        text = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    text.append(txt)
        return '\n\n'.join(text)

    def _extract_docx(self, data: bytes) -> str:
        doc = Document(io.BytesIO(data))
        return '\n\n'.join([para.text for para in doc.paragraphs if para.text.strip()])

    def _extract_odt(self, data: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            doc = odf_load(tmp_path)
            paragraphs = [teletype.extract_text(p) for p in doc.getElementsByType(text.P)]
            return '\n\n'.join(paragraphs)
        finally:
            os.unlink(tmp_path)

    def _extract_html(self, data: bytes) -> str:
        soup = BeautifulSoup(data, 'html.parser')
        return soup.get_text(separator='\n\n', strip=True)

    def _extract_xml(self, data: bytes) -> str:
        soup = BeautifulSoup(data, 'xml')
        return soup.get_text(separator='\n\n', strip=True)

    def _extract_rtf(self, data: bytes) -> str:
        # Простая замена: RTF читается как текст с кодами, но без полноценного парсера
        # Можно улучшить с pyth или striprtf, но для базовой задачи — fallback на текст
        return self._extract_txt(data)

    def _extract_csv(self, data: bytes) -> str:
        encoding = chardet.detect(data)['encoding'] or 'utf-8'
        df = pd.read_csv(io.BytesIO(data), encoding=encoding, on_bad_lines='skip')
        return df.to_string(index=False)

    def _extract_xlsx(self, data: bytes) -> str:
        dfs = pd.read_excel(io.BytesIO(data), sheet_name=None, dtype=str)
        parts = []
        for sheet_name, df in dfs.items():
            parts.append(f"=== Sheet: {sheet_name} ===")
            parts.append(df.to_string(index=False))
        return '\n\n'.join(parts)

    def _extract_epub(self, data: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            book = epub.read_epub(tmp_path)
            text = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                    text.append(soup.get_text(separator='\n\n', strip=True))
            return '\n\n'.join(text)
        finally:
            os.unlink(tmp_path)

    def _extract_doc(self, data: bytes) -> str:
        # Для .doc используем внешнюю утилиту, если она есть
        # Альтернатива: падаем на текст (не идеально)
        try:
            import subprocess
            with tempfile.NamedTemporaryFile(delete=False, suffix='.doc') as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                # Попробуем antiword
                result = subprocess.run(['antiword', tmp_path], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout
                # Или catdoc
                result = subprocess.run(['catdoc', tmp_path], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout
            finally:
                os.unlink(tmp_path)
        except Exception:
            pass
        # Fallback
        return self._extract_txt(data)


# Пример использования:
# extractor = DocumentTextExtractor()
# with open('example.pdf', 'rb') as f:
#     text = extractor(f.read(), filename='example.pdf')
# print(text)