import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, 
                           QSpinBox, QMessageBox)
from PyQt5.QtCore import Qt
from PIL import Image
import os

class ImageCompressor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_file = None
        
    def initUI(self):
        self.setWindowTitle('图片压缩工具')
        self.setGeometry(300, 300, 500, 300)
        
        # 创建主窗口部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # 文件选择部分
        file_layout = QHBoxLayout()
        self.file_label = QLabel('未选择文件')
        self.select_btn = QPushButton('选择图片')
        self.select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_btn)
        
        # 质量设置部分
        quality_layout = QHBoxLayout()
        quality_label = QLabel('压缩质量(1-100):')
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(80)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_spin)
        
        # 压缩按钮
        self.compress_btn = QPushButton('开始压缩')
        self.compress_btn.clicked.connect(self.compress_image)
        self.compress_btn.setEnabled(False)
        
        # 状态标签
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # 添加所有组件到主布局
        layout.addLayout(file_layout)
        layout.addLayout(quality_layout)
        layout.addWidget(self.compress_btn)
        layout.addWidget(self.status_label)
        
        main_widget.setLayout(layout)
        
    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp)"
        )
        
        if file_name:
            self.selected_file = file_name
            self.file_label.setText(os.path.basename(file_name))
            self.compress_btn.setEnabled(True)
            self.status_label.setText('')
            
    def compress_image(self):
        if not self.selected_file:
            return
            
        try:
            # 打开图片
            img = Image.open(self.selected_file)
            
            # 获取原始文件大小
            original_size = os.path.getsize(self.selected_file) / 1024  # KB
            
            # 保存压缩后的图片
            output_path = self.get_output_path(self.selected_file)
            
            # 如果是PNG格式，先转换为RGB
            if img.format == 'PNG':
                img = img.convert('RGB')
                
            img.save(
                output_path,
                quality=self.quality_spin.value(),
                optimize=True
            )
            
            # 获取压缩后的文件大小
            compressed_size = os.path.getsize(output_path) / 1024  # KB
            
            # 显示结果
            self.status_label.setText(
                f'压缩完成！\n'
                f'原始大小: {original_size:.2f} KB\n'
                f'压缩后大小: {compressed_size:.2f} KB\n'
                f'压缩率: {((original_size - compressed_size) / original_size * 100):.2f}%'
            )
            
            QMessageBox.information(self, '成功', f'图片已保存至：\n{output_path}')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'压缩过程中出现错误：{str(e)}')
            
    def get_output_path(self, input_path):
        # 生成输出文件路径
        directory = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        
        # 创建新的文件名
        output_filename = f"{name}_compressed{ext}"
        return os.path.join(directory, output_filename)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageCompressor()
    ex.show()
    sys.exit(app.exec_()) 