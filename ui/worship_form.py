from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont

class WorshipForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Culto")
        # Abrir como página interna: não modal e expansível
        try:
            self.setModal(False)
        except Exception:
            pass
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Estilo global do diálogo
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #2a2a2a;
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #4a4a4a;
                background-color: #2d2d2d;
            }
        """)
        
        # Layout principal com margens
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # Título
        title_label = QLabel("Novo Culto")
        title_font = QFont("Segoe UI", 28, QFont.Light)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; background: transparent; margin-bottom: 8px;")
        title_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(title_label)
        
        # Subtítulo (sem fundo adicional)
        subtitle_label = QLabel("Preencha as informações abaixo")
        subtitle_font = QFont("Segoe UI", 12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #ffffff; background: transparent; margin-bottom: 8px;")
        subtitle_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(subtitle_label)
        
        # Linha separadora
        # Removido separador pesado para visual mais limpo
        
        # Container dos campos
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(24)
        
        # Campo Nome
        name_label = QLabel("Nome do Culto")
        name_font = QFont("Segoe UI", 12)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #ffffff; background: transparent; margin-bottom: 6px;")
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Digite o nome do culto")
        self.name_input.setMinimumHeight(50)
        
        fields_layout.addWidget(name_label)
        fields_layout.addWidget(self.name_input)
        
        # Campo Data
        date_label = QLabel("Data do Culto")
        date_label.setFont(name_font)
        date_label.setStyleSheet("color: #ffffff; background: transparent; margin-bottom: 6px;")
        
        # Campo de data como entrada direta (sem calendário)
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("dd/mm/aaaa")
        self.date_input.setMinimumHeight(50)
        self.date_input.setText(QDate.currentDate().toString("dd/MM/yyyy"))
        # Máscara para facilitar a digitação no formato dd/mm/aaaa
        try:
            self.date_input.setInputMask("00/00/0000")
        except Exception:
            pass
        
        # Calendário removido — usuário digita diretamente a data
        
        fields_layout.addWidget(date_label)
        fields_layout.addWidget(self.date_input)
        
        main_layout.addLayout(fields_layout)
        main_layout.addStretch()
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setFont(QFont("Segoe UI", 11))
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setMinimumHeight(44)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #333333;
                border: 2px solid #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #252525;
            }
        """)
        
        self.ok_button = QPushButton("Criar Culto")
        self.ok_button.setFont(QFont("Segoe UI", 11))
        self.ok_button.setCursor(Qt.PointingHandCursor)
        self.ok_button.setMinimumHeight(44)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #ffffff;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
                color: #000000;
                border: 2px solid #f2f2f2;
            }
            QPushButton:pressed {
                background-color: #e6e6e6;
                color: #000000;
                border: 2px solid #e6e6e6;
            }
        """)
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def get_data(self):
        """Retorna os dados do culto como dicionário"""
        return {
            "name": self.name_input.text(),
            "date": self.date_input.text()
        }
