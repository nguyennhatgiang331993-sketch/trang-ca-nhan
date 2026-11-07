# Cờ Caro (phần mềm desktop)

Phần mềm chơi cờ caro 15x15 viết bằng Python + pygame. Ai có 5 quân liên tiếp trước là thắng.

## Cài và chạy
```bash
pip install pygame
python caro.py
```

## Tính năng
- Chơi với máy (AI) hoặc 2 người cùng máy
- Đi lại (undo), ván mới, đổi bên đi trước, đếm tỉ số
- Phím tắt: `N` ván mới, `U` đi lại, `M` đổi chế độ, `Esc` thoát

## Đóng gói thành file .exe (Windows)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name CoCaro caro.py
```
File chạy nằm trong thư mục `dist/`.
