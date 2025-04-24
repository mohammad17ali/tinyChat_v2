import PyPDF2
import requests
from bs4 import BeautifulSoup
from typing import List

class DocumentProcessor:
    @staticmethod
    def process_file(path: str) -> List[str]:
        ext = path.split('.')[-1].lower()
        if ext == 'txt':
            text = DocumentProcessor.process_text_file(path)
        elif ext == 'pdf':
            text = DocumentProcessor.process_pdf_file(path)
        elif ext in ['doc', 'docx']:
            return [f"Doc file support not implemented: {path}"]
        else:
          raise ValueError(f"Unsupported file type: {ext}")

        # Split the text into chunks of about 500 characters
        chunks = [text[i:i + 500] for i in range(0, len(text), 500)]
        return chunks
        raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def process_text_file(path: str) -> str:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()        

    @staticmethod
    def process_pdf_file(path: str) -> str:
        text = ""
        with open(path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    @staticmethod
    def process_webpage(url: str) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        return '\n'.join(chunk.strip() for chunk in soup.get_text().splitlines() if chunk.strip())
