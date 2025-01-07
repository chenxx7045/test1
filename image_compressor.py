import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, 
                           QSpinBox, QMessageBox, QProgressBar, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
from PIL import Image

class CompressWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str, str)

    def __init__(self, files, quality, parent=None):
        super().__init__(parent)
        self.files = files
        self.quality = quality
        
    def run(self):
        results = []
        for i, file_path in enumerate(self.files):
            try:
                # 压缩单个文件
                img = Image.open(file_path)
                original_size = os.path.getsize(file_path) / 1024  # KB
                
                output_path = self.get_output_path(file_path)
                
                if img.format == 'PNG':
                    img = img.convert('RGB')
                    
                img.save(output_path, quality=self.quality, optimize=True)
                
                compressed_size = os.path.getsize(output_path) / 1024  # KB
                compression_ratio = ((original_size - compressed_size) / original_size * 100)
                
                results.append({
                    'file': os.path.basename(file_path),
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'ratio': compression_ratio,
                    'output_path': output_path
                })
                
            except Exception as e:
                self.error.emit(file_path, str(e))
                
            self.progress.emit(int((i + 1) / len(self.files) * 100))
            
        self.finished.emit(results)
    
    def get_output_path(self, input_path):
        directory = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_compressed{ext}"
        return os.path.join(directory, output_filename)

class ImageCompressor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('图片压缩工具')
        self.setGeometry(300, 300, 600, 400)
        
        # 创建主窗口部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # 文件选择部分
        file_layout = QHBoxLayout()
        self.file_label = QLabel('未选择文件')
        self.select_btn = QPushButton('选择图片')
        self.select_btn.clicked.connect(self.select_files)
        self.batch_mode = QCheckBox('批量模式')
        self.batch_mode.stateChanged.connect(self.toggle_batch_mode)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.batch_mode)
        file_layout.addWidget(self.select_btn)
        
        # 质量设置部分
        quality_layout = QHBoxLayout()
        quality_label = QLabel('压缩质量(1-100):')
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(80)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_spin)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # 压缩按钮
        self.compress_btn = QPushButton('开始压缩')
        self.compress_btn.clicked.connect(self.compress_images)
        self.compress_btn.setEnabled(False)
        
        # 状态标签
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # 添加所有组件到主布局
        layout.addLayout(file_layout)
        layout.addLayout(quality_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.compress_btn)
        layout.addWidget(self.status_label)
        
        main_widget.setLayout(layout)
    
    def toggle_batch_mode(self, state):
        if not state and len(self.selected_files) > 1:
            self.selected_files = self.selected_files[:1]
            self.update_file_label()
    
    def select_files(self):
        if self.batch_mode.isChecked():
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "选择图片",
                "",
                "图片文件 (*.jpg *.jpeg *.png *.bmp)"
            )
        else:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "选择图片",
                "",
                "图片文件 (*.jpg *.jpeg *.png *.bmp)"
            )
            files = [file_name] if file_name else []
            
        if files:
            self.selected_files = files
            self.update_file_label()
            self.compress_btn.setEnabled(True)
            self.status_label.setText('')
    
    def update_file_label(self):
        if len(self.selected_files) > 1:
            self.file_label.setText(f'已选择 {len(self.selected_files)} 个文件')
        elif len(self.selected_files) == 1:
            self.file_label.setText(os.path.basename(self.selected_files[0]))
        else:
            self.file_label.setText('未选择文件')
    
    def compress_images(self):
        if not self.selected_files:
            return
            
        self.compress_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText('压缩中...')
        
        # 创建工作线程
        self.worker = CompressWorker(self.selected_files, self.quality_spin.value())
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.compression_finished)
        self.worker.error.connect(self.compression_error)
        self.worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def compression_finished(self, results):
        self.compress_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        
        # 显示结果摘要
        total_original = sum(r['original_size'] for r in results)
        total_compressed = sum(r['compressed_size'] for r in results)
        avg_ratio = sum(r['ratio'] for r in results) / len(results)
        
        summary = (f'压缩完成！\n'
                  f'处理文件数: {len(results)}\n'
                  f'总原始大小: {total_original:.2f} KB\n'
                  f'总压缩后大小: {total_compressed:.2f} KB\n'
                  f'平均压缩率: {avg_ratio:.2f}%')
        
        self.status_label.setText(summary)
        
        # 显示详细结果
        detail_msg = "压缩详情：\n\n" + "\n".join(
            f"{r['file']}: {r['original_size']:.2f}KB -> {r['compressed_size']:.2f}KB ({r['ratio']:.2f}%)"
            for r in results
        )
        
        QMessageBox.information(self, '压缩完成', detail_msg)
    
    def compression_error(self, file_path, error_msg):
        QMessageBox.warning(self, '错误',
                          f'处理文件 {os.path.basename(file_path)} 时出错：\n{error_msg}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageCompressor()
    ex.show()
    sys.exit(app.exec_()) 