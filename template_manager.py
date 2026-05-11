import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QTreeWidget, QTreeWidgetItem, QLabel, 
                             QTextEdit, QSplitter, QWidget, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import base_datos

class EditorDePlantilla(QDialog):
    """Mini-ventana para Crear o Editar una plantilla directamente en el gestor"""
    def __init__(self, parent=None, id_plantilla=None, titulo="", html=""):
        super().__init__(parent)
        self.setWindowTitle("Editor de Plantillas Maestras")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #f8f9fa;")
        self.id_plantilla = id_plantilla

        layout = QVBoxLayout(self)

        # Caja de Título
        f_titulo = QHBoxLayout()
        f_titulo.addWidget(QLabel("<b>Título de la Plantilla:</b>"))
        self.ent_titulo = QLineEdit(titulo)
        self.ent_titulo.setStyleSheet("padding: 5px; background: white; border: 1px solid #ccc;")
        f_titulo.addWidget(self.ent_titulo)
        layout.addLayout(f_titulo)

        # Diccionario de Variables Mágicas (Estilo Lex Doctor)
        lbl_ayuda = QLabel(
            "<b>Etiquetas Inteligentes (Copiá y pegá estas etiquetas en tu texto, se llenarán solas al insertar):</b><br>"
            "<span style='color: #d32f2f;'>[@CARATULA] | [@NRO_EXP] | [@JUZGADO] | [@ACTOR_NOMBRE] | [@ACTOR_DNI] | [@ACTOR_DOMICILIO] | [@DEMANDADO_NOMBRE] | [@DEMANDADO_DNI] | [@DEMANDADO_DOMICILIO]</span>"
        )
        lbl_ayuda.setStyleSheet("background-color: #fff9c4; padding: 8px; border: 1px dashed #fbc02d;")
        lbl_ayuda.setWordWrap(True)
        layout.addWidget(lbl_ayuda)

        # Editor de HTML
        self.editor = QTextEdit()
        self.editor.setHtml(html)
        self.editor.setStyleSheet("background: white; border: 1px solid #ccc; font-family: Arial; font-size: 11pt;")
        layout.addWidget(self.editor)

        # Botones
        f_btn = QHBoxLayout()
        btn_guardar = QPushButton("💾 Guardar Plantilla")
        btn_guardar.setStyleSheet("background-color: #0078d7; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        btn_guardar.clicked.connect(self.guardar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        f_btn.addStretch()
        f_btn.addWidget(btn_cancelar)
        f_btn.addWidget(btn_guardar)
        layout.addLayout(f_btn)

    def guardar(self):
        t = self.ent_titulo.text().strip()
        h = self.editor.toHtml()
        if not t:
            QMessageBox.warning(self, "Aviso", "El título no puede estar vacío.")
            return

        conn = base_datos.conectar()
        if self.id_plantilla:
            conn.execute("UPDATE plantillas SET titulo=?, contenido=? WHERE id=?", (t, h, self.id_plantilla))
        else:
            conn.execute("INSERT INTO plantillas (titulo, contenido) VALUES (?, ?)", (t, h))
        conn.commit(); conn.close()
        self.accept()


class GestorPlantillas(QDialog):
    def __init__(self, editor_padre, id_exp_actual):
        super().__init__(editor_padre)
        self.editor_padre = editor_padre
        self.id_exp_actual = id_exp_actual
        
        self.setWindowTitle("Gestor de Plantillas Dinámicas - IUSer")
        
        # == TAMAÑO CORREGIDO: Más ancha según lo pedido ==
        self.resize(1300, 550)
        self.setStyleSheet("background-color: #fffde7;") 
        
        layout = QVBoxLayout(self)
        
        # Barra de Herramientas Superior
        barra_sup = QHBoxLayout()
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar plantilla por título o contenido...")
        self.buscador.setStyleSheet("background-color: white; padding: 8px; border: 1px solid #ccc; border-radius: 3px; font-size: 10pt;")
        self.buscador.textChanged.connect(self.cargar_lista)
        
        btn_nueva = QPushButton("📄 Crear Nueva Plantilla")
        btn_nueva.setStyleSheet("background-color: #0078d7; color: white; padding: 8px; border-radius: 3px; font-weight: bold;")
        btn_nueva.clicked.connect(self.crear_plantilla)
        
        barra_sup.addWidget(self.buscador)
        barra_sup.addWidget(btn_nueva)
        layout.addLayout(barra_sup)

        # Panel Dividido (Splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # PANEL IZQUIERDO: Lista de Plantillas Limpia
        w_izq = QWidget(); l_izq = QVBoxLayout(w_izq); l_izq.setContentsMargins(0,0,0,0)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Título de la Plantilla", "ID"])
        self.tree.hideColumn(1)
        
        # == CORRECCIÓN DEL MARGEN IZQUIERDO ==
        self.tree.setRootIsDecorated(False) # Esto saca el espacio invisible de la flechita
        
        self.tree.setStyleSheet("""
            QTreeWidget { background-color: white; border: 1px solid #ccc; font-size: 10pt; } 
            QTreeWidget::item { padding: 8px; } /* Un poquito más de aire arriba y abajo */
            QTreeWidget::item:selected { background-color: #b3e5fc; color: black; font-weight: bold; }
        """)
        self.tree.itemSelectionChanged.connect(self.mostrar_preview)
        l_izq.addWidget(self.tree)
        
        # Botonera Inferior Izquierda (Editar / Eliminar)
        f_btn_izq = QHBoxLayout()
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 6px; font-weight: bold;")
        btn_editar.clicked.connect(self.editar_plantilla)
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet("background-color: #fce4e4; color: #c62828; border: 1px solid #ffcdd2; padding: 6px; font-weight: bold;")
        btn_eliminar.clicked.connect(self.eliminar_plantilla)
        
        f_btn_izq.addWidget(btn_editar)
        f_btn_izq.addWidget(btn_eliminar)
        l_izq.addLayout(f_btn_izq)

        # PANEL DERECHO: Vista Previa y Botón Insertar
        w_der = QWidget(); l_der = QVBoxLayout(w_der); l_der.setContentsMargins(0,0,0,0)
        lbl_prev = QLabel("<b>Vista Previa de la Plantilla (Mostrando etiquetas reales):</b>")
        l_der.addWidget(lbl_prev)
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 15px; font-family: Arial; font-size: 11pt;")
        l_der.addWidget(self.preview)
        
        btn_insertar = QPushButton("✔️ AUTO-COMPLETAR E INSERTAR EN EL ESCRITO")
        btn_insertar.setStyleSheet("background-color: #4CAF50; color: white; padding: 12px; border-radius: 4px; font-weight: bold; font-size: 11pt;")
        btn_insertar.clicked.connect(self.insertar_plantilla)
        l_der.addWidget(btn_insertar)

        # Armado del Splitter con la nueva distribución
        splitter.addWidget(w_izq)
        splitter.addWidget(w_der)
        splitter.setSizes([450, 850]) 
        layout.addWidget(splitter)
        
        self.cargar_lista()

    def cargar_lista(self):
        self.tree.clear()
        filtro = self.buscador.text()
        conn = base_datos.conectar(); cursor = conn.cursor()
        if filtro:
            cursor.execute("SELECT id, titulo FROM plantillas WHERE titulo LIKE ? OR contenido LIKE ?", ('%'+filtro+'%', '%'+filtro+'%'))
        else:
            cursor.execute("SELECT id, titulo FROM plantillas")
            
        for fila in cursor.fetchall():
            item = QTreeWidgetItem([fila[1], str(fila[0])])
            self.tree.addTopLevelItem(item)
        conn.close()

    def mostrar_preview(self):
        item = self.tree.currentItem()
        if item:
            conn = base_datos.conectar()
            res = conn.execute("SELECT contenido FROM plantillas WHERE id=?", (item.text(1),)).fetchone()
            conn.close()
            if res: self.preview.setHtml(res[0])
        else:
            self.preview.clear()

    def crear_plantilla(self):
        dlg = EditorDePlantilla(self)
        if dlg.exec():
            self.cargar_lista()

    def editar_plantilla(self):
        item = self.tree.currentItem()
        if not item: return
        conn = base_datos.conectar()
        res = conn.execute("SELECT titulo, contenido FROM plantillas WHERE id=?", (item.text(1),)).fetchone()
        conn.close()
        if res:
            dlg = EditorDePlantilla(self, id_plantilla=item.text(1), titulo=res[0], html=res[1])
            if dlg.exec():
                self.cargar_lista()
                self.mostrar_preview()

    def eliminar_plantilla(self):
        item = self.tree.currentItem()
        if item:
            reply = QMessageBox.question(self, 'Borrar', '¿Eliminar plantilla definitivamente?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                conn = base_datos.conectar()
                conn.execute("DELETE FROM plantillas WHERE id=?", (item.text(1),))
                conn.commit(); conn.close()
                self.cargar_lista()
                self.preview.clear()

    def autocompletar_variables(self, html):
        conn = base_datos.conectar()
        exp = conn.execute("SELECT caratula, nro_exp, juzgado, act_nom, act_cuit, act_dom, dem_nom, dem_cuit, dem_dom FROM expedientes WHERE id=?", (self.id_exp_actual,)).fetchone()
        conn.close()
        
        if not exp: return html

        reemplazos = {
            "[@CARATULA]": exp[0] or "...", "[@NRO_EXP]": exp[1] or "...", "[@JUZGADO]": exp[2] or "...",
            "[@ACTOR_NOMBRE]": exp[3] or "...", "[@ACTOR_DNI]": exp[4] or "...", "[@ACTOR_DOMICILIO]": exp[5] or "...",
            "[@DEMANDADO_NOMBRE]": exp[6] or "...", "[@DEMANDADO_DNI]": exp[7] or "...", "[@DEMANDADO_DOMICILIO]": exp[8] or "..."
        }
        
        html_final = html
        for etiqueta, dato_real in reemplazos.items():
            html_final = html_final.replace(etiqueta, f"<span style='background-color:#e8f5e9;'><b>{dato_real}</b></span>")
            
        return html_final

    def insertar_plantilla(self):
        if not self.preview.toPlainText().strip(): return
        html_crudo = self.preview.toHtml()
        html_procesado = self.autocompletar_variables(html_crudo)
        self.editor_padre.insertHtml(html_procesado)
        self.accept()
