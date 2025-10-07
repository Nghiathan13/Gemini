import json
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont


# --- CẤU HÌNH ---
# Vui lòng thay thế bằng API key của bạn
try:
    genai.configure(api_key="AIzaSyA-S8j2_bqSw9GvwFU_BLK4Uh6OLQ8yyfM")
except Exception as e:
    print(f"Lỗi cấu hình API: {e}")
    # Trong ứng dụng web, bạn có thể muốn ghi log thay vì thoát


# --- CÁC HÀM XỬ LÝ ---
def extract_text_info(image_path):
    """
    Sử dụng Gemini để trích xuất thông tin văn bản từ CCCD.
    Trả về một dictionary chứa thông tin.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        img = Image.open(image_path)

        prompt = """
        Phân tích hình ảnh thẻ Căn cước công dân Việt Nam này.
        Trích xuất các thông tin sau: Số CCCD, Họ và tên, Ngày sinh, Giới tính, Quốc tịch, Quê quán, Nơi thường trú.
        
        Trả về kết quả dưới dạng một đối tượng JSON duy nhất có cấu trúc như sau:
        {
          "so_cccd": "<số cccd>",
          "ho_va_ten": "<họ và tên>",
          "ngay_sinh": "<ngày sinh>",
          "gioi_tinh": "<giới tính>",
          "quoc_tich": "<quốc tịch>",
          "que_quan": "<quê quán>",
          "noi_thuong_tru": "<nơi thường trú>"
        }
        Nếu không tìm thấy trường nào, giá trị của nó phải là một chuỗi rỗng.
        """
        
        response = model.generate_content([prompt, img])
        
        # Dọn dẹp và phân tích chuỗi JSON từ phản hồi của model
        json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
        data = json.loads(json_str)
        return data

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp hình ảnh tại '{image_path}'")
        return None
    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình trích xuất thông tin bằng AI: {e}")
        return None

def crop_portrait_hardcoded(image_path):
    """Cắt ảnh chân dung từ ảnh CCCD bằng tọa độ cố định."""
    try:
        img = Image.open(image_path)
        # Tọa độ cắt cũ (left, top, right, bottom)
        x, y, w, h = 6, 148, 132, 162
        box = (x, y, x + w, y + h)
        cropped = img.crop(box)
        return cropped
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp '{image_path}' để cắt.")
        return None
    except Exception as e:
        print(f"Đã xảy ra lỗi khi cắt ảnh: {e}")
        return None

def fill_contract_from_id(id_card_path, output_path):
    """
    Hàm chính: Nhận đường dẫn ảnh CCCD, xử lý và điền thông tin vào hợp đồng.
    Trả về True nếu thành công, False nếu thất bại.
    """
    print("--- Bắt đầu quy trình điền hợp đồng tự động ---")

    # B1: Trích xuất thông tin văn bản bằng Gemini
    print("Bước 1: Đang trích xuất thông tin từ CCCD...")
    info = extract_text_info(id_card_path)
    if not info:
        print(" -> Lỗi: Không thể trích xuất dữ liệu từ ảnh.")
        return False
    print(f" -> Trích xuất thành công: {info}")

    # B2: Cắt ảnh chân dung bằng tọa độ cố định
    print("Bước 2: Đang cắt ảnh chân dung...")
    portrait_photo = crop_portrait_hardcoded(id_card_path)
    if not portrait_photo:
        print(" -> Lỗi: Không thể cắt ảnh chân dung.")
        return False
    
    # Scale ảnh chân dung về 80%
    scale_factor = 0.8
    new_width = int(portrait_photo.width * scale_factor)
    new_height = int(portrait_photo.height * scale_factor)
    portrait_photo = portrait_photo.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(" -> Cắt và scale ảnh chân dung thành công.")

    # B3: Điền thông tin và ảnh vào mẫu hợp đồng
    print("Bước 3: Đang điền thông tin vào hợp đồng...")
    try:
        # --- TÙY CHỈNH TỌA ĐỘ VÀ FONT (Giá trị cũ) ---
        template_path = "assets/hop_dong.jpg"
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Cần đảm bảo font này tồn tại
        font_size = 12
        text_color = "black"

        # Tọa độ dán ảnh chân dung (x, y)
        photo_coords = (10, 10)

        # Tọa độ điền thông tin
        coordinate_map = {
            'so_cccd': (110, 350),
            'ho_va_ten': (145, 312),
            'ngay_sinh': (80, 332),
            'gioi_tinh': (350, 332),
            'que_quan': (100, 390),
            'noi_thuong_tru': (175, 370)
        }

        # Mở ảnh mẫu
        contract = Image.open(template_path).convert("RGB")

        # Dán ảnh chân dung
        contract.paste(portrait_photo, photo_coords)

        # Viết chữ
        draw = ImageDraw.Draw(contract)
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Cảnh báo: Không tìm thấy font '{font_path}'. Sử dụng font mặc định.")
            font = ImageFont.load_default()

        for key, coords in coordinate_map.items():
            text = info.get(key, '').upper() # Lấy text, chuyển thành chữ hoa
            draw.text(coords, text, font=font, fill=text_color)

        # Lưu ảnh kết quả
        contract.save(output_path)
        print(f" -> Đã tạo hợp đồng thành công: {output_path}")
        print("--- Hoàn thành! ---")
        return True

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp ảnh mẫu '{template_path}' hoặc tệp font '{font_path}'.")
        return False
    except Exception as e:
        print(f"Đã xảy ra lỗi khi tạo hợp đồng: {e}")
        return False
