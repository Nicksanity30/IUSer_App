import sys
import os
import base64
from PyQt6.QtWidgets import (QMainWindow, QTextEdit, QToolBar, QHBoxLayout, 
                             QWidget, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
                             QColorDialog, QLabel, QInputDialog, QFontComboBox, 
                             QStatusBar, QMessageBox, QMenuBar, QFileDialog)
from PyQt6.QtGui import (QAction, QFont, QShortcut, QKeySequence, QColor, 
                         QTextListFormat, QTextBlockFormat, QTextCursor, QPageLayout)
from PyQt6.QtCore import Qt, QSize, QMarginsF
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
        
        btn_guardar = QPushButton("💾 GUARDAR Y CERRAR")
        btn_guardar.setStyleSheet("background-color: #0078d7; color: white; font-weight: bold; padding: 5px; border-radius: 3px;")
        btn_guardar.clicked.connect(self.guardar_mov)

        self.btn_plantillas = QPushButton("📄 Plantillas")
        self.btn_pdf = QPushButton("📕 Generar PDF")
        self.btn_importar = QPushButton("📥 Importar")
        
        estilo_botones = "background-color: #e0e0e0; color: #333; padding: 5px; border: 1px solid #ccc; border-radius: 3px; font-weight: bold;"
        self.btn_plantillas.setStyleSheet(estilo_botones)
        self.btn_importar.setStyleSheet(estilo_botones)
        self.btn_pdf.setStyleSheet("background-color: #ffcdd2; color: #b71c1c; padding: 5px; border: 1px solid #ef9a9a; border-radius: 3px; font-weight: bold;")
        
        self.btn_plantillas.clicked.connect(self.abrir_buscador_plantillas)
        self.btn_pdf.clicked.connect(self.exportar_a_pdf)
        self.btn_importar.clicked.connect(self.importar_archivo)

        f_datos.addWidget(self.ent_fecha)
        f_datos.addWidget(self.cmb_origen)
        f_datos.addWidget(self.ent_titulo)
        f_datos.addStretch() 
        f_datos.addWidget(self.btn_plantillas)
        f_datos.addWidget(self.btn_pdf)
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

    # === EL CEREBRO DEL PDF COMERCIAL ===
    def exportar_a_pdf(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar a PDF", "", "PDF Files (*.pdf)")
        if not ruta: return

        try:
            conn = base_datos.conectar()
            exp = conn.execute("SELECT caratula, nro_exp, juzgado FROM expedientes WHERE id=?", (self.id_exp,)).fetchone()
            usr = conn.execute("SELECT nombre, matricula, telefono, email, domicilio, usar_membrete, posicion FROM usuario WHERE id=1").fetchone()
            conn.close()

            doc_clon = self.editor.document().clone()
            cursor = QTextCursor(doc_clon)
            cursor.movePosition(QTextCursor.MoveOperation.Start)

            # Lógica para mostrar/ocultar y alinear el membrete
            if usr and usr[5] == 1: # Si 'usar_membrete' está activado
                alineacion = "right"
                if usr[6] == "Izquierda": alineacion = "left"
                elif usr[6] == "Centro": alineacion = "center"

                # Partes del texto, si están vacías no se imprimen feo
                txt_nombre = f"<b>{usr[0]}</b><br>" if usr[0] else ""
                txt_mat = f"Matrícula: {usr[1]} | " if usr[1] else ""
                txt_tel = f"Tel: {usr[2]} | " if usr[2] else ""
                txt_mail = f"Email: {usr[3]}" if usr[3] else ""
                txt_dom = f"<br>{usr[4]}" if usr[4] else ""

                encabezado_html = f"""
                <div align="{alineacion}" style="font-family: Arial; font-size: 9pt; color: #555;">
                    {txt_nombre}
                    {txt_mat}{txt_tel}{txt_mail}
                    {txt_dom}
                </div>
                <hr style="border: 1px solid #ccc;">
                """
            else:
                encabezado_html = "" # Si el usuario lo apagó, no imprime nada arriba

            # Carátula del expediente
            txt_caratula = exp[0] if exp else "..."
            txt_nro = exp[1] if exp else "..."
            txt_juzgado = exp[2] if exp else "..."

            encabezado_html += f"""
            <div style="font-family: Arial; font-size: 11pt;">
                <b>CARÁTULA:</b> {txt_caratula}<br>
                <b>EXPTE N°:</b> {txt_nro}<br>
                <b>JUZGADO:</b> {txt_juzgado}
            </div>
            <br>
            """
            
            cursor.insertHtml(encabezado_html)

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(ruta)
            printer.setPageMargins(QMarginsF(25.0, 15.0, 20.0, 20.0), QPageLayout.Unit.Millimeter)

            doc_clon.print(printer)
            QMessageBox.information(self, "PDF Generado", f"El archivo se guardó correctamente.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el PDF: {str(e)}")

    def importar_archivo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar Archivo", "", "Textos e Imágenes (*.txt *.png *.jpg *.jpeg)")
        if not path: return
        ext = os.path.splitext(path)[1].lower()
        if ext == '.txt':
            with open(path, 'r', encoding='utf-8') as f: self.editor.insertPlainText(f.read())
        elif ext in ['.png', '.jpg', '.jpeg']:
            with open(path, "rb") as img_file: b64 = base64.b64encode(img_file.read()).decode('utf-8')
            self.editor.insertHtml(f'<br><img src="data:image/{ext[1:]};base64,{b64}" /><br>')

    def crear_acciones(self):
        self.act_imprimir = QAction("🖨️ Imprimir...", self)
        self.act_imprimir.triggered.connect(self.file_print)

    def crear_menus(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("&Archivo")
        file_menu.addAction(self.act_imprimir)

    def crear_cintas_herramientas(self):
        tb = QToolBar("Formato"); self.addToolBar(tb)
        self.combo_font = QFontComboBox(); self.combo_font.currentFontChanged.connect(self.editor.setCurrentFont)
        tb.addWidget(self.combo_font)
        self.combo_size = QComboBox(); self.combo_size.addItems([str(s) for s in FONT_SIZES]); self.combo_size.setCurrentText("11")
        self.combo_size.currentTextChanged.connect(lambda s: self.editor.setFontPointSize(float(s)))
        tb.addWidget(self.combo_size)
        
        tb.addAction(QAction("B", self, triggered=lambda: self.editor.setFontWeight(QFont.Weight.Bold if self.editor.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)))
        tb.addAction(QAction("I", self, triggered=lambda: self.editor.setFontItalic(not self.editor.fontItalic())))
        tb.addAction(QAction("U", self, triggered=lambda: self.editor.setFontUnderline(not self.editor.fontUnderline())))

    def elegir_color(self, tipo):
        c = QColorDialog.getColor()
        if c.isValid():
            if tipo == "txt": self.editor.setTextColor(c)
            else: self.editor.setTextBackgroundColor(c)

    def actualizar_contador(self):
        t = self.editor.toPlainText()
        self.status.showMessage(f"Palabras: {len(t.split())} | Caracteres: {len(t)}")

    def file_print(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if QPrintDialog(printer, self).exec() == QPrintDialog.DialogCode.Accepted: self.editor.print(printer)

    def cargar_datos(self):
        if self.id_mov:
            conn = base_datos.conectar()
            datos = conn.execute("SELECT fecha, titulo, contenido, origen FROM movimientos WHERE id=?", (self.id_mov,)).fetchone()
            conn.close()
            if datos:
                self.ent_fecha.setText(datos[0]); self.ent_titulo.setText(datos[1]); self.editor.setHtml(datos[2]); self.cmb_origen.setCurrentText(datos[3] if datos[3] else "Otros")

    def guardar_mov(self):
        fecha = self.ent_fecha.text(); titulo = self.ent_titulo.text(); origen = self.cmb_origen.currentText(); html = self.editor.toHtml() 
        conn = base_datos.conectar()
        if self.id_mov: conn.execute("UPDATE movimientos SET fecha=?, hora='00:00', titulo=?, contenido=?, origen=? WHERE id=?", (fecha, titulo, html, origen, self.id_mov))
        else: conn.execute("INSERT INTO movimientos (id_exp, fecha, hora, titulo, contenido, origen) VALUES (?,?,'00:00',?,?,?)", (self.id_exp, fecha, titulo, html, origen))
        conn.commit(); conn.close()
        if self.callback_actualizar: self.callback_actualizar()
        self.close()
