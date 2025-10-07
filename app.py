import os
import gemini as gemini_processor
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename


# --- CẤU HÌNH ---
UPLOAD_FOLDER = 'uploads'
GENERATED_FOLDER = 'generated'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.json.ensure_ascii = False # Đảm bảo tiếng Việt hiển thị đúng trong JSON

# Tạo các thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Kiểm tra xem file có phần mở rộng được cho phép không."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render trang chủ."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Xử lý việc tải lên file CCCD và tạo hợp đồng."""
    if 'file' not in request.files:
        return jsonify({'error': 'Không có phần tệp nào trong yêu cầu'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Không có tệp nào được chọn'}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            id_card_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(id_card_path)

            # Gọi module gemini để xử lý ảnh
            output_filename = f"hop_dong_{os.path.splitext(filename)[0]}.jpg"
            output_path = os.path.join(app.config['GENERATED_FOLDER'], output_filename)

            success = gemini_processor.fill_contract_from_id(id_card_path, output_path)

            if not success:
                raise Exception("Không thể xử lý ảnh CCCD hoặc tạo hợp đồng.")

            return jsonify({'result_url': f'/{GENERATED_FOLDER}/{output_filename}'})

        except Exception as e:
            # Ghi lại lỗi để debug
            print(f"Đã xảy ra lỗi: {e}")
            return jsonify({'error': f'Đã xảy ra lỗi trong quá trình xử lý: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Loại tệp không được phép'}), 400

@app.route('/generated/<filename>')
def send_generated_file(filename):
    """Phục vụ các tệp hợp đồng đã được tạo."""
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
