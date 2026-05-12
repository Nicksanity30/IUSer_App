import base_datos
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QLabel, QMessageBox, QLineEdit, QTextEdit)
from PyQt6.QtCore import Qt
from jinja2 import Environment
from datetime import datetime

class GestorPlantillas(QDialog):
    def __init__(self, editor_proxy=None, id_exp=None):
        super().__init__()
        self.setWindowTitle("Administrador de Plantillas Inteligentes")
        self.resize(800, 500) # Lo hicimos más grande para poder redactar cómodo
        self.editor_proxy = editor_proxy
        self.id_exp = id_exp
        
        self.plantilla_actual_id = None

        # ¡Magia! Esta línea auto-repara la base de datos para que no tire error
        self.reparar_base_datos()

        layout_principal = QHBoxLayout(self)

        # --- PANEL IZQUIERDO: LISTA DE PLANTILLAS ---
        panel_izq = QVBoxLayout()
        panel_izq.addWidget(QLabel("Tus Plantillas Guardadas:"))
        
        self.lista_plantillas = QListWidget()
        self.lista_plantillas.itemClicked.connect(self.cargar_plantilla_en_editor)
        panel_izq.addWidget(self.lista_plantillas)

        botones_lista = QHBoxLayout()
        btn_nueva = QPushButton("➕ Nueva")
        btn_nueva.clicked.connect(self.limpiar_editor)
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet("color: #d32f2f;")
        btn_eliminar.clicked.connect(self.eliminar_plantilla)
        
        botones_lista.addWidget(btn_nueva)
        botones_lista.addWidget(btn_eliminar)
        panel_izq.addLayout(botones_lista)

        # --- PANEL DERECHO: EDITOR DE PLANTILLA ---
        panel_der = QVBoxLayout()
        
        self.ent_nombre = QLineEdit()
        self.ent_nombre.setPlaceholderText("Nombre (ej: Presenta Bono y Tasa)")
        panel_der.addWidget(QLabel("Nombre de la Plantilla:"))
        panel_der.addWidget(self.ent_nombre)

        self.ent_contenido = QTextEdit()
        self.ent_contenido.setPlaceholderText("Escriba aquí el modelo usando las variables:\n/// caratula ///\n/// nro_exp ///\n/// juzgado ///\n/// actor ///\n/// abogado_nombre ///\n/// abogado_matricula ///")
        panel_der.addWidget(QLabel("Contenido del Escrito:"))
        panel_der.addWidget(self.ent_contenido)

        botones_editor = QHBoxLayout()
        btn_guardar = QPushButton("💾 Guardar Plantilla")
        btn_guardar.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px; border-radius: 3px;")
        btn_guardar.clicked.connect(self.guardar_plantilla)
        botones_editor.addStretch()
        botones_editor.addWidget(btn_guardar)

        # Botón Insertar (Solo aparece si estamos dentro de un expediente)
        if self.editor_proxy:
            btn_insertar = QPushButton("🚀 Insertar en Escrito")
            btn_insertar.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px; border-radius: 3px;")
            btn_insertar.clicked.connect(self.procesar_y_enviar)
            botones_editor.addWidget(btn_insertar)

        panel_der.addLayout(botones_editor)

        # Unimos los dos paneles (1/3 de ancho para la lista, 2/3 para el editor)
        layout_principal.addLayout(panel_izq, 1) 
        layout_principal.addLayout(panel_der, 2) 

        self.cargar_lista()

    # ==========================================
    # LÓGICA DE BASE DE DATOS Y CRUD
    # ==========================================
    def reparar_base_datos(self):
        """Asegura que la tabla exista y tenga las columnas correctas sin borrar datos"""
        conn = base_datos.conectar()
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS plantillas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, contenido TEXT)")
            try: conn.execute("ALTER TABLE plantillas ADD COLUMN nombre TEXT")
            except: pass
            try: conn.execute("ALTER TABLE plantillas ADD COLUMN contenido TEXT")
            except: pass
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def cargar_lista(self):
        self.lista_plantillas.clear()
        conn = base_datos.conectar()
        try:
            plantillas = conn.execute("SELECT id, nombre FROM plantillas ORDER BY nombre").fetchall()
            for p in plantillas:
                from PyQt6.QtWidgets import QListWidgetItem
                item = QListWidgetItem(p[1])
                item.setData(Qt.ItemDataRole.UserRole, p[0]) # Escondemos el ID en el item
                self.lista_plantillas.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar: {e}")
        finally:
            conn.close()

    def limpiar_editor(self):
        self.plantilla_actual_id = None
        self.ent_nombre.clear()
        self.ent_contenido.clear()
        self.lista_plantillas.clearSelection()

    def cargar_plantilla_en_editor(self, item):
        self.plantilla_actual_id = item.data(Qt.ItemDataRole.UserRole)
        conn = base_datos.conectar()
        res = conn.execute("SELECT nombre, contenido FROM plantillas WHERE id=?", (self.plantilla_actual_id,)).fetchone()
        conn.close()
        
        if res:
            self.ent_nombre.setText(res[0])
            self.ent_contenido.setPlainText(res[1])

    def guardar_plantilla(self):
        nombre = self.ent_nombre.text().strip()
        contenido = self.ent_contenido.toPlainText().strip()
        
        if not nombre:
            QMessageBox.warning(self, "Atención", "El nombre no puede estar vacío.")
            return

        conn = base_datos.conectar()
        if self.plantilla_actual_id:
            conn.execute("UPDATE plantillas SET nombre=?, contenido=? WHERE id=?", (nombre, contenido, self.plantilla_actual_id))
        else:
            conn.execute("INSERT INTO plantillas (nombre, contenido) VALUES (?, ?)", (nombre, contenido))
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "Éxito", "Plantilla guardada correctamente.")
        self.cargar_lista()
        self.limpiar_editor()

    def eliminar_plantilla(self):
        if not self.plantilla_actual_id: return
        
        rta = QMessageBox.question(self, "Confirmar", "¿Seguro que desea eliminar esta plantilla?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rta == QMessageBox.StandardButton.Yes:
            conn = base_datos.conectar()
            conn.execute("DELETE FROM plantillas WHERE id=?", (self.plantilla_actual_id,))
            conn.commit()
            conn.close()
            self.cargar_lista()
            self.limpiar_editor()

    # ==========================================
    # LÓGICA DE INYECCIÓN (JINJA2 -> QUILL)
    # ==========================================
    def procesar_y_enviar(self):
        texto_plantilla = self.ent_contenido.toPlainText()
        if not texto_plantilla.strip():
            QMessageBox.warning(self, "Atención", "El contenido está vacío.")
            return

        conn = base_datos.conectar()
        exp = conn.execute("SELECT * FROM expedientes WHERE id=?", (self.id_exp,)).fetchone()
        usu = conn.execute("SELECT * FROM configuracion LIMIT 1").fetchone()
