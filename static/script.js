document.addEventListener("DOMContentLoaded", () => {
  // --- 1. CÁC HẰNG SỐ VÀ BIẾN ---
  const CONSTANTS = {
    MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
    ALLOWED_FILE_TYPES: ["image/jpeg", "image/png", "image/jpg"],
  };

  // Lấy các element trên trang
  const ui = {
    dropzone: document.getElementById("dropzone"),
    previewState: document.getElementById("previewState"), // Thêm state mới
    processingState: document.getElementById("processingState"),
    resultsState: document.getElementById("resultsState"),
    fileInput: document.getElementById("fileInput"),
    selectBtn: document.getElementById("selectBtn"),
    resetBtn: document.getElementById("resetBtn"),
    resultImage: document.getElementById("resultImage"),
    downloadBtn: document.getElementById("downloadBtn"),
    resultsTitle: document.getElementById("resultsTitle"),
    resultMessage: document.getElementById("resultMessage"),
    previewImage: document.getElementById("previewImage"), // Thêm ảnh preview
    createContractBtn: document.getElementById("createContractBtn"), // Thêm nút tạo hợp đồng
    cancelBtn: document.getElementById("cancelBtn"), // Thêm nút hủy
  };

  let selectedFile = null; // Biến để lưu file đã chọn

  // --- 2. QUẢN LÝ TRẠNG THÁI GIAO DIỆN ---

  /** Hiển thị một section và ẩn các section khác */
  const showSection = (sectionToShow) => {
    [
      ui.dropzone,
      ui.previewState,
      ui.processingState,
      ui.resultsState,
    ].forEach((section) => {
      section.classList.toggle("hidden", section !== sectionToShow);
    });
  };

  // --- 3. ĐĂNG KÝ SỰ KIỆN ---

  // Mở hộp thoại chọn file
  ui.selectBtn.addEventListener("click", () => ui.fileInput.click());
  ui.dropzone.addEventListener("click", (e) => {
    if (e.target.id !== "selectBtn" && !e.target.closest("#selectBtn")) {
      ui.fileInput.click();
    }
  });

  // Xử lý khi chọn file
  ui.fileInput.addEventListener("change", (e) =>
    handleFileSelect(e.target.files)
  );

  // Xử lý kéo/thả file
  ui.dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    ui.dropzone.classList.add("dragover");
  });
  ui.dropzone.addEventListener("dragleave", () =>
    ui.dropzone.classList.remove("dragover")
  );
  ui.dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    ui.dropzone.classList.remove("dragover");
    handleFileSelect(e.dataTransfer.files);
  });

  // Xử lý nút "Tạo hợp đồng" từ màn hình preview
  ui.createContractBtn.addEventListener("click", () => {
    if (selectedFile) {
      processFile(selectedFile);
    }
  });

  // Xử lý nút "Chọn ảnh khác" (hủy)
  ui.cancelBtn.addEventListener("click", () => {
    resetFileInput();
    showSection(ui.dropzone);
  });

  // Xử lý nút "Tạo hợp đồng khác"
  ui.resetBtn.addEventListener("click", () => {
    resetFileInput();
    ui.resultImage.src = "#";
    ui.downloadBtn.href = "#";
    showSection(ui.dropzone);
  });

  // --- 4. CÁC HÀM XỬ LÝ LOGIC ---

  /** Reset input file */
  function resetFileInput() {
    ui.fileInput.value = "";
    selectedFile = null;
  }

  /**
   * Kiểm tra và hiển thị preview cho file được chọn.
   * @param {FileList} files - Danh sách file người dùng chọn.
   */
  function handleFileSelect(files) {
    if (files.length === 0) return;
    const file = files[0];

    // Kiểm tra tính hợp lệ của file
    if (file.size > CONSTANTS.MAX_FILE_SIZE) {
      alert(
        `Tệp quá lớn. Kích thước tối đa là ${
          CONSTANTS.MAX_FILE_SIZE / 1024 / 1024
        }MB.`
      );
      return;
    }
    if (!CONSTANTS.ALLOWED_FILE_TYPES.includes(file.type)) {
      alert("Định dạng tệp không hợp lệ. Vui lòng chọn ảnh JPG hoặc PNG.");
      return;
    }

    selectedFile = file; // Lưu file lại

    // Hiển thị ảnh preview
    const reader = new FileReader();
    reader.onload = (e) => {
      ui.previewImage.src = e.target.result;
      showSection(ui.previewState);
    };
    reader.readAsDataURL(file);
  }

  /**
   * Gửi file đến server và chờ kết quả.
   * @param {File} file - File ảnh hợp lệ.
   */
  function processFile(file) {
    showSection(ui.processingState);
    const formData = new FormData();
    formData.append("file", file);

    fetch("/upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          // Nếu server trả về lỗi, cố gắng đọc nội dung lỗi
          return response.json().then((err) => {
            throw new Error(err.error || `Lỗi Server: ${response.statusText}`);
          });
        }
        return response.json();
      })
      .then((data) => {
        if (data.error) throw new Error(data.error);
        displayResults(data.result_url);
      })
      .catch((error) => {
        console.error("Lỗi xử lý:", error);
        alert(`Đã xảy ra lỗi: ${error.message}`);
        showSection(ui.dropzone); // Quay lại uploader nếu có lỗi
      });
  }

  /**
   * Hiển thị kết quả lên giao diện.
   * @param {string} resultUrl - URL của ảnh hợp đồng đã tạo.
   */
  function displayResults(resultUrl) {
    ui.resultImage.src = resultUrl;
    ui.downloadBtn.href = resultUrl;

    // Đảm bảo ảnh đã tải xong trước khi hiển thị section kết quả
    ui.resultImage.onload = () => {
      showSection(ui.resultsState);
    };
    // Nếu ảnh đã được cache, onload có thể không được gọi, nên set src lại lần nữa
    ui.resultImage.src = resultUrl;
  }
});