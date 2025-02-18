import fitz  # PyMuPDF
import urllib.request
import json
from io import BytesIO

def handle(data):
    try:
        # 📌 Получаем параметры из входных данных
        pdf_url = data.get("pdf_url")
        api_url = data.get("api_url")
        access_token = data.get("access_token")
        acc_id = data.get("acc_id")

        if not all([pdf_url, api_url, access_token, acc_id]):
            return {"error": "Missing required parameters: pdf_url, api_url, access_token, acc_id"}

        # 🔹 Скачиваем PDF в память
        print("⏳ Скачиваем PDF в память...")
        req = urllib.request.Request(pdf_url, method="GET")
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                return {"error": f"Ошибка скачивания PDF: {response.status}"}
            pdf_bytes = BytesIO(response.read())

        # 🔍 Открываем PDF и извлекаем первое изображение
        doc = fitz.open("pdf", pdf_bytes.getvalue())  # Открываем PDF напрямую из памяти
        image_bytes = None

        for page_num in range(len(doc)):
            for img_index, img in enumerate(doc[page_num].get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                break  # Берем только первое изображение
            if image_bytes:
                break

        if not image_bytes:
            return {"error": "Фото кандидата не найдено в PDF"}

        # 📤 Загружаем фото в API
        print("⏳ Загружаем фото в API...")
        req = urllib.request.Request(f"{api_url}/{acc_id}", method="POST")
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Content-Type", "multipart/form-data; boundary=----WebKitFormBoundary")
        
        # Формируем multipart тело запроса
        boundary = "----WebKitFormBoundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="candidate_photo.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()

        req.data = body
        req.add_header("Content-Length", str(len(body)))

        with urllib.request.urlopen(req) as response:
            api_response = json.loads(response.read().decode())

        return {"result": "Фото успешно загружено", "api_response": api_response}

    except Exception as e:
        return {"error": str(e)}
