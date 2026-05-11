import sys
import os
import base64
from PyQt6.QtWidgets import (QMainWindow, QTextEdit, QToolBar, QHBoxLayout, 
                             QWidget, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
                             QColorDialog, QLabel, QInputDialog, QFontComboBox, 
                             QStatusBar, QMessageBox, QMenuBar, QFileDialog)
from PyQt6.QtGui import (QAction, QFont, QShortcut, QKeySequence, QColor, 
                         QTextListFormat, QTextBlockFormat, QTextCursor)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
import base_datos
from datetime import datetime

from template_manager import GestorPlantillas

FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]

class EditorProfesional(QMainWindow):
    def __init__(self, id_exp, id_mov=None, callback_actualizar=None):
        super().__init__()
        self.setWindowTitle("Procesador de Textos IUSer")
        
        self.resize(950, 650) 
        self.centrar_ventana()
        
        self.id_exp = id_exp
        self.id_mov = id_mov
        self.callback_actualizar = callback_actualizar

        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)
        atajo_guardar = QShortcut(QKeySequence("Ctrl+Return"), self)
        atajo_guardar.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        atajo_guardar.activated.connect(self.guardar_mov)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)

        f_datos = QHBoxLayout()
        self.ent_fecha = QLineEdit(datetime.now().strftime("%d/%m/%Y")); self.ent_fecha.setFixedWidth(100)
        self.cmb_origen = QComboBox(); self.cmb_origen.addItems(["Juzgado", "Actor/a", "Demandado/a", "Otros"])
        self.ent_titulo = QLineEdit("Título del Escrito")
        
        # == BOTON ACTUALIZADO ==
        btn_guardar = QPushButton("💾 GUARDAR Y CERRAR")
        btn_guardar.setStyleSheet("background-color: #0078d7; color: white; font-weight: bold; padding: 5px; border-radius: 3px;")
        btn_guardar.clicked.connect(self.guardar_mov)

        self.btn_plantillas = QPushButton("📄 Plantillas")
        self.btn_importar = QPushButton("📥 Importar Archivo")
        
        estilo_botones = "background-color: #e0e0e0; color: #333; padding: 5px; border: 1px solid #ccc; border-radius: 3px; font-weight: bold;"
        self.btn_plantillas.setStyleSheet(estilo_botones)
        self.btn_importar.setStyleSheet(estilo_botones)
        
        self.btn_plantillas.clicked.connect(self.abrir_buscador_plantillas)
        self.btn_importar.clicked.connect(self.importar_archivo)

        f_datos.addWidget(self.ent_fecha)
        f_datos.addWidget(self.cmb_origen)
        f_datos.addWidget(self.ent_titulo)
        f_datos.addStretch() 
        f_datos.addWidget(self.btn_plantillas)
        f_datos.addWidget(self.btn_importar)
        f_datos.addWidget(btn_guardar)
        layout_principal.addLayout(f_datos)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Arial", 11))
        self.editor.setViewportMargins(60, 40, 60, 40)
        self.editor.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        self.crear_acciones()
        self.crear_menus()
        self.crear_cintas_herramientas()

        layout_principal.addWidget(self.editor)
        
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.editor.textChanged.connect(self.actualizar_contador)

        self.cargar_datos()

    def centrar_ventana(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def abrir_buscador_plantillas(self):
        dlg = GestorPlantillas(self.editor, self.id_exp)
        dlg.exec()

    def importar_archivo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar Archivo", "", "Textos e Imágenes soportados (*.txt *.png *.jpg *.jpeg);;Word, PDF, Excel (*.docx *.pdf *.xls)")
        if not path: return
        ext = os.path.splitext(path)[1].lower()
        if ext == '.txt':
            try:
                with open(path, 'r', encoding='utf-8') as f: self.editor.insertPlainText(f.read())
            except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo leer txt:\n{str(e)}")
        elif ext in ['.png', '.jpg', '.jpeg']:
            try:
                with open(path, "rb") as img_file: b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                self.editor.insertHtml(f'<br><img src="data:image/{ext[1:]};base64,{b64_string}" /><br>')
            except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen:\n{str(e)}")
        elif ext in ['.docx', '.pdf', '.xls']:
            QMessageBox.information(self, "Formato Complejo Requerido", "Para importar Word o PDF instalaremos las librerías necesarias en la próxima fase de desarrollo.")

    def crear_acciones(self):
        self.act_imprimir = QAction("🖨️ Imprimir...", self)
        self.act_imprimir.setShortcut(QKeySequence.StandardKey.Print)
        self.act_imprimir.triggered.connect(self.file_print)

    def crear_menus(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("&Archivo")
        file_menu.addAction(self.act_imprimir)

    def crear_cintas_herramientas(self):
        tb_clip = QToolBar("Portapapeles"); self.addToolBar(tb_clip)
        tb_clip.addAction(QAction("✂️", self, triggered=self.editor.cut))
        tb_clip.addAction(QAction("📄", self, triggered=self.editor.copy))
        tb_clip.addAction(QAction("📋", self, triggered=self.editor.paste))
        self.addToolBarBreak() 

        tb_font = QToolBar("Fuente"); self.addToolBar(tb_font)
        self.combo_font = QFontComboBox(); self.combo_font.currentFontChanged.connect(self.editor.setCurrentFont)
        tb_font.addWidget(self.combo_font)
        self.combo_size = QComboBox(); self.combo_size.addItems([str(s) for s in FONT_SIZES]); self.combo_size.setCurrentText("11")
        self.combo_size.currentTextChanged.connect(lambda s: self.editor.setFontPointSize(float(s)))
        tb_font.addWidget(self.combo_size)
        tb_font.addSeparator()

        act_bold = QAction("B", self, checkable=True); act_bold.setFont(QFont("Arial", 10, QFont.Weight.Bold)); act_bold.triggered.connect(lambda x: self.editor.setFontWeight(QFont.Weight.Bold if x else QFont.Weight.Normal))
        tb_font.addAction(act_bold)

        act_italic = QAction("I", self, checkable=True); f_it = QFont("Arial", 10); f_it.setItalic(True); act_italic.setFont(f_it); act_italic.triggered.connect(self.editor.setFontItalic)
        tb_font.addAction(act_italic)

        act_under = QAction("U", self, checkable=True); f_un = QFont("Arial", 10); f_un.setUnderline(True); act_under.setFont(f_un); act_under.triggered.connect(self.editor.setFontUnderline)
        tb_font.addAction(act_under)
        tb_font.addSeparator()

        act_color_txt = QAction("A🎨", self); act_color_txt.triggered.connect(lambda: self.elegir_color("txt"))
        tb_font.addAction(act_color_txt)
        act_color_bg = QAction("🖍️", self); act_color_bg.triggered.connect(lambda: self.elegir_color("bg"))
        tb_font.addAction(act_color_bg)

        tb_parrafo = QToolBar("Párrafo"); self.addToolBar(tb_parrafo)
        tb_parrafo.addAction(QAction("• Lista", self, triggered=lambda: self.editor.textCursor().createList(QTextListFormat.Style.ListDisc)))
        tb_parrafo.addAction(QAction("1. Nros", self, triggered=lambda: self.editor.textCursor().createList(QTextListFormat.Style.ListDecimal)))
        tb_parrafo.addSeparator()
        tb_parrafo.addAction(QAction("⇐", self, triggered=lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft)))
        tb_parrafo.addAction(QAction("⇔", self, triggered=lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignCenter)))
        tb_parrafo.addAction(QAction("⇒", self, triggered=lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignRight)))
        tb_parrafo.addAction(QAction("≡", self, triggered=lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignJustify)))

    def elegir_color(self, tipo):
        if tipo == "txt":
            c = QColorDialog.getColor(self.editor.textColor(), self)
            if c.isValid(): self.editor.setTextColor(c)
        else:
            c = QColorDialog.getColor(self.editor.textBackgroundColor(), self)
            if c.isValid(): self.editor.setTextBackgroundColor(c)

    def actualizar_contador(self):
        t = self.editor.toPlainText()
        self.status.showMessage(f"Palabras: {len(t.split())} | Caracteres: {len(t)}")

    def file_print(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if QPrintDialog(printer, self).exec() == QPrintDialog.DialogCode.Accepted: self.editor.print(printer)

    def cargar_datos(self):
        if self.id_mov:
            conn = base_datos.conectar(); datos = conn.execute("SELECT fecha, titulo, contenido, origen FROM movimientos WHERE id=?", (self.id_mov,)).fetchone(); conn.close()
            if datos:
                self.ent_fecha.setText(datos[0]); self.ent_titulo.setText(datos[1]); self.editor.setHtml(datos[2]); self.cmb_origen.setCurrentText(datos[3] if datos[3] else "Otros")

    # == GUARDADO REPARADO ==
    def guardar_mov(self):
        try:
            fecha = self.ent_fecha.text(); titulo = self.ent_titulo.text(); origen = self.cmb_origen.currentText(); html = self.editor.toHtml() 
            conn = base_datos.conectar()
            
            if self.id_mov: 
                conn.execute("UPDATE movimientos SET fecha=?, hora='00:00', titulo=?, contenido=?, origen=? WHERE id=?", (fecha, titulo, html, origen, self.id_mov))
            else: 
                conn.execute("INSERT INTO movimientos (id_exp, fecha, hora, titulo, contenido, origen) VALUES (?,?,'00:00',?,?,?)", (self.id_exp, fecha, titulo, html, origen))
                
            conn.commit(); conn.close()
            
            if self.callback_actualizar: 
                self.callback_actualizar()
                
            # AHORA SÍ CIERRA LA VENTANA
            self.close() 
            
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar el documento:\n{str(e)}")
