from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTreeWidget, QTreeWidgetItem, QLabel, QFrame, QMessageBox)
from PyQt6.QtGui import QFont, QColor, QShortcut, QKeySequence
import base_datos
import traceback 
from text_editor import EditorProfesional

class VentanaCarpeta(QWidget):
    def __init__(self, id_exp, info_exp, callback_cerrar=None):
        super().__init__()
        try:
            self.id_exp = id_exp
            self.callback_cerrar = callback_cerrar
            self.setWindowTitle(f"Carpeta: {info_exp[1]}")
            self.resize(950, 600)
            self.setStyleSheet("background-color: #f8f9fa;")

            # Atajo de Salida: Al tocar 'Esc' vuelve a la pestaña anterior (cierra carpeta)
            atajo_esc = QShortcut(QKeySequence("Esc"), self)
            atajo_esc.activated.connect(self.close)

            self.editor_abierto = None
            layout = QVBoxLayout(self)

            f_azul = QFrame()
            f_azul.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; border-radius: 4px;")
            l_azul = QVBoxLayout(f_azul)
            
            lbl_caratula = QLabel(str(info_exp[0] or "Sin Carátula"))
            lbl_caratula.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            lbl_caratula.setStyleSheet("color: #333; border: none;")
            l_azul.addWidget(lbl_caratula)
            
            lbl_nro = QLabel(f"Expediente N° {info_exp[1] or 'S/N'}")
            lbl_nro.setStyleSheet("border: none;")
            l_azul.addWidget(lbl_nro)
            layout.addWidget(f_azul)

            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["Fecha", "Origen", "Título", "ID"])
            self.tree.hideColumn(3)
            self.tree.setColumnWidth(0, 100)
            self.tree.setColumnWidth(1, 100)
            self.tree.setToolTip("Doble clic en un movimiento para ver o editar su escrito.")
            self.tree.setStyleSheet("background-color: white; border: 1px solid #ccc; font-size: 10pt;")
            self.tree.itemDoubleClicked.connect(self.editar_mov)
            layout.addWidget(self.tree)

            f_botones = QHBoxLayout()
            btn_nuevo = QPushButton("+ NUEVO MOVIMIENTO")
            btn_nuevo.setToolTip("Inicia el editor de textos para cargar un nuevo escrito o proveído.")
            btn_nuevo.setStyleSheet("background-color: #c8e6c9; color: #2e7d32; font-weight: bold; padding: 8px; border-radius: 4px;")
            btn_nuevo.clicked.connect(lambda: self.lanzar_editor())
            
            btn_resaltar = QPushButton("⭐ RESALTAR")
            btn_resaltar.setToolTip("Destaca el movimiento seleccionado en color rojo y negrita.")
            btn_resaltar.setStyleSheet("background-color: #fff9c4; color: #f57f17; font-weight: bold; padding: 8px; border-radius: 4px;")
            btn_resaltar.clicked.connect(self.resaltar_mov)
            
            btn_borrar = QPushButton("🗑️ BORRAR")
            btn_borrar.setToolTip("Elimina definitivamente el movimiento seleccionado.")
            btn_borrar.setStyleSheet("background-color: #fce4e4; color: #c62828; font-weight: bold; padding: 8px; border-radius: 4px;")
            btn_borrar.clicked.connect(self.borrar_mov)

            f_botones.addWidget(btn_nuevo)
            f_botones.addWidget(btn_resaltar)
            f_botones.addWidget(btn_borrar)
            layout.addLayout(f_botones)

            self.refrescar_movimientos()
            
        except Exception as e:
            error_msg = traceback.format_exc()
            QMessageBox.critical(self, "Error Crítico", f"Falló al abrir la carpeta:\n\n{error_msg}")

    def closeEvent(self, event):
        if self.callback_cerrar:
            self.callback_cerrar(self.id_exp)
        super().closeEvent(event)

    def refrescar_movimientos(self):
        try:
            self.tree.clear()
            conn = base_datos.conectar(); cursor = conn.cursor()
            cursor.execute("SELECT id, fecha, origen, titulo, resaltado FROM movimientos WHERE id_exp=? ORDER BY id ASC", (self.id_exp,))
            for fila in cursor.fetchall():
                val_fecha = str(fila[1] if fila[1] is not None else "")
                val_origen = str(fila[2] if fila[2] is not None else "Otros")
                val_titulo = str(fila[3] if fila[3] is not None else "Sin Título")
                val_id = str(fila[0])
                item = QTreeWidgetItem([val_fecha, val_origen, val_titulo, val_id])
                if fila[4] == 1: 
                    for col in range(3): item.setBackground(col, QColor("#eaeaea")); item.setForeground(col, QColor("#d32f2f")); font = item.font(col); font.setBold(True); item.setFont(col, font)
                self.tree.addTopLevelItem(item)
            conn.close()
        except Exception as e:
            error_msg = traceback.format_exc()
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudieron cargar los movimientos:\n\n{error_msg}")

    def resaltar_mov(self):
        item = self.tree.currentItem()
        if item:
            id_mov = item.text(3)
            conn = base_datos.conectar()
            estado = conn.execute("SELECT resaltado FROM movimientos WHERE id=?", (id_mov,)).fetchone()[0]
            conn.execute("UPDATE movimientos SET resaltado=? WHERE id=?", (0 if estado == 1 else 1, id_mov))
            conn.commit(); conn.close()
            self.refrescar_movimientos()

    def borrar_mov(self):
        item = self.tree.currentItem()
        if item:
            reply = QMessageBox.question(self, 'Borrar', '¿Eliminar movimiento?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                conn = base_datos.conectar(); conn.execute("DELETE FROM movimientos WHERE id=?", (item.text(3),)); conn.commit(); conn.close()
                self.refrescar_movimientos()

    def editar_mov(self, item, column):
        self.lanzar_editor(item.text(3))

    def lanzar_editor(self, id_mov=None):
        self.editor_abierto = EditorProfesional(self.id_exp, id_mov, callback_actualizar=self.refrescar_movimientos)
        self.editor_abierto.show()
