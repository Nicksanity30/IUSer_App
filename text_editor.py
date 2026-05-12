import sys
import os
import base64
import json
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLineEdit, 
                             QComboBox, QPushButton, QHBoxLayout, QMessageBox, QFileDialog, QStatusBar)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt, QMarginsF
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPageLayout

import base_datos
from datetime import datetime

# IMPORTAMOS TUS PLANTILLAS
from template_manager import GestorPlantillas

class ProxyEditorQuill:
    """Esta clase actúa como un 'traductor' entre el GestorPlantillas y Quill"""
    def __init__(self, main_window):
        self.main_window = main_window

    def insertHtml(self, html):
        self.main_window.insertar_html_en_editor(html)

    def setHtml(self, html):
        html_limpio = html.replace("'", "\\'").replace("\n", "")
        self.main_window.web_view.page().runJavaScript(f"setEditorHtml('{html_limpio}');")

    def insertPlainText(self, text):
        self.main_window.insertar_texto_en_editor(text)
        
    def append(self, text):
        self.main_window.insertar_texto_en_editor(text)


class EditorProfesional(QMainWindow):
    def __init__(self, id_exp, id_mov=None, callback_actualizar=None):
        super().__init__()
        self.setWindowTitle("Procesador de Textos IUSer Pro (Quill)")
        self.resize(1000, 800)
        
        self.id_exp = id_exp
        self.id_mov = id_mov
        self.callback_actualizar = callback_actualizar

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)

        # --- BARRA SUPERIOR ---
        f_datos = QHBoxLayout()
        self.ent_fecha = QLineEdit(datetime.now().strftime("%d/%m/%Y")); self.ent_fecha.setFixedWidth(100)
        self.cmb_origen = QComboBox(); self.cmb_origen.addItems(["Juzgado", "Actor/a", "Demandado/a", "Otros"])
        self.ent_titulo = QLineEdit("Título del Escrito")
        
        btn_guardar = QPushButton("💾 GUARDAR")
        btn_guardar.setStyleSheet("background-color: #0078d7; color: white; font-weight: bold; padding: 8px; border-radius: 3px;")
        btn_guardar.clicked.connect(self.guardar_mov)

        # RECUPERAMOS LOS BOTONES
        self.btn_plantillas = QPushButton("📄 Plantillas")
        self.btn_importar = QPushButton("📥 Importar")
        self.btn_pdf = QPushButton("📕 Generar PDF")
        
        estilo_gris = "background-color: #e0e0e0; color: #333; font-weight: bold; padding: 8px; border: 1px solid #ccc; border-radius: 3px;"
        self.btn_plantillas.setStyleSheet(estilo_gris)
        self.btn_importar.setStyleSheet(estilo_gris)
        self.btn_pdf.setStyleSheet("background-color: #ffcdd2; color: #b71c1c; font-weight: bold; padding: 8px; border: 1px solid #ef9a9a; border-radius: 3px;")
        
        self.btn_plantillas.clicked.connect(self.abrir_buscador_plantillas)
        self.btn_importar.clicked.connect(self.importar_archivo)
        self.btn_pdf.clicked.connect(self.exportar_a_pdf)

        f_datos.addWidget(self.ent_fecha)
        f_datos.addWidget(self.cmb_origen)
        f_datos.addWidget(self.ent_titulo)
        f_datos.addStretch()
        f_datos.addWidget(self.btn_plantillas)
        f_datos.addWidget(self.btn_importar)
        f_datos.addWidget(self.btn_pdf)
        f_datos.addWidget(btn_guardar)
        layout_principal.addLayout(f_datos)

        # --- EL NAVEGADOR (EDITOR WEB QUILL) ---
        self.web_view = QWebEngineView()
        
        ajustes = self.web_view.settings()
        ajustes.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        ajustes.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        ajustes.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        ruta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_html = os.path.join(ruta_base, "assets", "editor.html").replace('\\', '/')
        
        if not os.path.exists(ruta_html):
            QMessageBox.critical(self, "Error Fatal", f"No se encontró el archivo:\n{ruta_html}")
            
        self.web_view.setUrl(QUrl.fromLocalFile(ruta_html))
        layout_principal.addWidget(self.web_view)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        self.web_view.loadFinished.connect(self.cargar_datos_al_editor)

    # ==========================================
    # FUNCIONES DE INYECCIÓN JAVASCRIPT SEGURAS
    # ==========================================
    def insertar_html_en_editor(self, html):
        html_seguro = json.dumps(html)
        script = f"""
            var range = quill.getSelection();
            var index = range ? range.index : quill.getLength();
            quill.clipboard.dangerouslyPasteHTML(index, {html_seguro});
        """
        self.web_view.page().runJavaScript(script)

    def insertar_texto_en_editor(self, text):
        texto_seguro = json.dumps(text)
        script = f"""
            var range = quill.getSelection();
            var index = range ? range.index : quill.getLength();
            quill.insertText(index, {texto_seguro});
        """
        self.web_view.page().runJavaScript(script)

    # ==========================================
    # ACCIONES DE LOS BOTONES
    # ==========================================
    def abrir_buscador_plantillas(self):
        proxy = ProxyEditorQuill(self)
        dlg = GestorPlantillas(proxy, self.id_exp)
        dlg.exec()

    def importar_archivo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar Archivo", "", "Archivos Soportados (*.docx *.txt *.png *.jpg *.jpeg)")
        if not path: return
        
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == '.docx':
                import docx
                doc = docx.Document(path)
                full_text = []
                for para in doc.paragraphs:
                    full_text.append(para.text)
                self.insertar_texto_en_editor("\n".join(full_text))
                self.status.showMessage("Archivo Word importado", 3000)

            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f: 
                    self.insertar_texto_en_editor(f.read())
            
            elif ext in ['.png', '.jpg', '.jpeg']:
                with open(path, "rb") as img_file: 
                    b64 = base64.b64encode(img_file.read()).decode('utf-8')
                self.insertar_html_en_editor(f'<br><img src="data:image/{ext[1:]};base64,{b64}" /><br>')
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar: {str(e)}")

    def cargar_datos_al_editor(self, ok):
        if not ok: return
        if self.id_mov:
            conn = base_datos.conectar()
            datos = conn.execute("SELECT fecha, titulo, contenido, origen FROM movimientos WHERE id=?", (self.id_mov,)).fetchone()
            conn.close()
            if datos:
                self.ent_fecha.setText(datos[0])
                self.ent_titulo.setText(datos[1])
                self.cmb_origen.setCurrentText(datos[3] if datos[3] else "Otros")
                
                contenido_limpio = datos[2].replace("'", "\\'").replace("\n", "")
                self.web_view.page().runJavaScript(f"setEditorHtml('{contenido_limpio}');")

    def guardar_mov(self):
        self.web_view.page().runJavaScript("getEditorHtml();", self._finalizar_guardado)

    def _finalizar_guardado(self, html_content):
        fecha = self.ent_fecha.text()
        titulo = self.ent_titulo.text()
        origen = self.cmb_origen.currentText()
        
        if html_content == "<p><br></p>": html_content = ""
            
        conn = base_datos.conectar()
        if self.id_mov:
            conn.execute("UPDATE movimientos SET fecha=?, titulo=?, contenido=?, origen=? WHERE id=?", 
                         (fecha, titulo, html_content, origen, self.id_mov))
        else:
            conn.execute("INSERT INTO movimientos (id_exp, fecha, hora, titulo, contenido, origen) VALUES (?,?,'00:00',?,?,?)", 
                         (self.id_exp, fecha, titulo, html_content, origen))
        conn.commit()
        conn.close()
        
        if self.callback_actualizar: self.callback_actualizar()
        self.close()

    def exportar_a_pdf(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar a PDF", "", "PDF Files (*.pdf)")
        if not ruta: return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(ruta)
        printer.setPageMargins(QMarginsF(25.0, 15.0, 20.0, 20.0), QPageLayout.Unit.Millimeter)

        self.web_view.page().print(printer, lambda ok: QMessageBox.information(self, "Éxito", "PDF generado") if ok else None)
