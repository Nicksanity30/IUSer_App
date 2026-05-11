import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTreeWidget, QTreeWidgetItem, QLabel, QFrame, 
                             QTextEdit, QComboBox, QCalendarWidget, 
                             QMessageBox, QDateEdit, QTimeEdit)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QShortcut, QKeySequence
import base_datos

class VentanaAgenda(QWidget):
    def __init__(self, callback_abrir_carpeta=None):
        super().__init__()
        self.setWindowTitle("Mi Agenda Profesional - IUSer")
        self.resize(1100, 750)
        self.setStyleSheet("background-color: #f8f9fa;")
        
        self.callback_abrir_carpeta = callback_abrir_carpeta
        self.id_tarea_editando = None

        # == ATAJOS DE TECLADO INTELIGENTES ==
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)
        
        atajo_enter1 = QShortcut(QKeySequence("Return"), self)
        atajo_enter1.activated.connect(self.intentar_guardar)
        atajo_enter2 = QShortcut(QKeySequence("Enter"), self)
        atajo_enter2.activated.connect(self.intentar_guardar)

        layout = QHBoxLayout(self)

        panel_izq = QVBoxLayout()
        self.calendario = QCalendarWidget()
        self.calendario.setGridVisible(True)
        self.calendario.setToolTip("Haga clic en un día para filtrar las tareas de esa fecha específica.")
        self.calendario.setStyleSheet("background-color: white; selection-background-color: #1976d2;")
        self.calendario.clicked.connect(self.filtrar_por_dia)
        self.calendario.selectionChanged.connect(self.sincronizar_fecha_inputs)
        panel_izq.addWidget(self.calendario)

        lbl_add = QLabel("Nueva Tarea:")
        lbl_add.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        panel_izq.addWidget(lbl_add)

        self.combo_exp = QComboBox()
        self.combo_exp.setToolTip("Vincule esta tarea a un expediente (Opcional).")
        self.combo_exp.setStyleSheet("background-color: white; padding: 4px;")
        self.cargar_expedientes_combo()
        panel_izq.addWidget(self.combo_exp)

        self.txt_desc = QTextEdit()
        self.txt_desc.setFixedHeight(80)
        self.txt_desc.setToolTip("Escriba el detalle de la tarea.")
        self.txt_desc.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        panel_izq.addWidget(self.txt_desc)

        f_fecha_hora = QHBoxLayout()
        self.dt_fecha = QDateEdit(QDate.currentDate())
        self.dt_fecha.setCalendarPopup(True)
        self.dt_fecha.setToolTip("Modifique la fecha de la tarea.")
        self.dt_fecha.setStyleSheet("background-color: white; padding: 5px;")
        
        self.tm_hora = QTimeEdit(QTime(0, 0)) 
        self.tm_hora.setToolTip("Modifique la hora de vencimiento/alerta.")
        self.tm_hora.setStyleSheet("background-color: white; padding: 5px;")
        
        f_fecha_hora.addWidget(QLabel("<b>Fecha:</b>"))
        f_fecha_hora.addWidget(self.dt_fecha)
        f_fecha_hora.addWidget(QLabel("<b>Hora:</b>"))
        f_fecha_hora.addWidget(self.tm_hora)
        panel_izq.addLayout(f_fecha_hora)

        self.btn_guardar = QPushButton("➕ GUARDAR TAREA")
        self.btn_guardar.setToolTip("Guarda la tarea (Atajo: Presione Enter).")
        self.btn_guardar.setStyleSheet("QPushButton { background-color: #0078d7; color: white; font-weight: bold; padding: 10px; border-radius: 4px; } QPushButton:hover { background-color: #005a9e; }")
        self.btn_guardar.clicked.connect(self.guardar_tarea)
        panel_izq.addWidget(self.btn_guardar)

        layout.addLayout(panel_izq, 1)

        panel_der = QVBoxLayout()
        f_header_der = QHBoxLayout()
        self.lbl_filtro = QLabel("Mostrando TODAS las tareas")
        self.lbl_filtro.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        btn_todas = QPushButton("Ver Todas")
        btn_todas.setToolTip("Limpia el filtro del calendario y muestra todas las tareas.")
        btn_todas.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 4px;")
        btn_todas.clicked.connect(self.quitar_filtro)
        
        f_header_der.addWidget(self.lbl_filtro)
        f_header_der.addStretch()
        f_header_der.addWidget(btn_todas)
        panel_der.addLayout(f_header_der)

        self.f_info = QFrame()
        self.f_info.setStyleSheet("background-color: white; border: 2px solid #333; border-radius: 4px;")
        l_info = QVBoxLayout(self.f_info)
        
        self.lbl_info_caratula = QLabel("SELECCIONE UNA TAREA...")
        self.lbl_info_caratula.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.lbl_info_caratula.setStyleSheet("color: #d32f2f; border: none;")
        self.lbl_info_caratula.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_info.addWidget(self.lbl_info_caratula)

        f_info_bot = QHBoxLayout()
        self.lbl_info_nro = QLabel("Nro: -")
        self.lbl_info_nro.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.lbl_info_nro.setStyleSheet("color: #d32f2f; border: none;")
        
        self.btn_ir_carpeta = QPushButton("IR A LA CARPETA")
        self.btn_ir_carpeta.setToolTip("Abre la carpeta del expediente vinculado a esta tarea.")
        self.btn_ir_carpeta.setStyleSheet("QPushButton { background-color: white; color: black; font-weight: bold; border: 2px solid black; padding: 6px; } QPushButton:hover { background-color: #f0f0f0; }")
        self.btn_ir_carpeta.setEnabled(False)
        self.btn_ir_carpeta.clicked.connect(self.abrir_carpeta_desde_tarea)
        
        f_info_bot.addWidget(self.lbl_info_nro)
        f_info_bot.addStretch()
        f_info_bot.addWidget(self.btn_ir_carpeta)
        l_info.addLayout(f_info_bot)
        panel_der.addWidget(self.f_info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Fecha", "Hora", "Descripción", "ID", "ID_Exp"])
        self.tree.hideColumn(3)
        self.tree.hideColumn(4)
        self.tree.setColumnWidth(0, 90)
        self.tree.setColumnWidth(1, 60)
        self.tree.setToolTip("Haga clic en una tarea para ver sus acciones u opciones de expediente.")
        self.tree.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.tree.itemSelectionChanged.connect(self.tarea_seleccionada)
        panel_der.addWidget(self.tree)

        f_botones = QHBoxLayout()
        btn_edit = QPushButton("✏️ Editar")
        btn_edit.setToolTip("Sube la tarea seleccionada al panel de la izquierda para editarla.")
        btn_edit.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 8px; color: #d32f2f; font-weight: bold;")
        btn_edit.clicked.connect(self.cargar_para_editar)
        
        btn_comp = QPushButton("✔️ Completar")
        btn_comp.setToolTip("Marca la tarea como finalizada (cambia de color).")
        btn_comp.setStyleSheet("background-color: #eaf2e3; border: 1px solid #c8e6c9; padding: 8px; color: #2e7d32; font-weight: bold;")
        btn_comp.clicked.connect(self.completar_tarea)
        
        btn_borrar = QPushButton("🗑️ Borrar")
        btn_borrar.setToolTip("Elimina la tarea definitivamente.")
        btn_borrar.setStyleSheet("background-color: #fce4e4; border: 1px solid #ffcdd2; padding: 8px; color: #c62828; font-weight: bold;")
        btn_borrar.clicked.connect(self.borrar_tarea)
        
        f_botones.addWidget(btn_edit)
        f_botones.addStretch()
        f_botones.addWidget(btn_comp)
        f_botones.addWidget(btn_borrar)
        panel_der.addLayout(f_botones)

        layout.addLayout(panel_der, 2)
        self.dia_filtrado = None
        self.refrescar_tareas()

    # == LOGICA DEL ENTER INTELIGENTE ==
    def intentar_guardar(self):
        # Evita guardar si el usuario está abriendo la lista desplegable de expedientes
        if self.combo_exp.view().isVisible():
            return
            
        # Si está escribiendo la descripción, el Enter hace un PUNTO Y APARTE
        if self.txt_desc.hasFocus():
            self.txt_desc.textCursor().insertBlock()
        else:
            # Si tocó enter en CUALQUIER otro lado (fecha, hora, etc), GUARDA LA TAREA.
            self.guardar_tarea()

    def cargar_expedientes_combo(self):
        conn = base_datos.conectar()
        exps = conn.execute("SELECT id, nro_exp, caratula FROM expedientes").fetchall()
        conn.close()
        self.lista_exp = {"Ninguno (Tarea General)": None}
        self.combo_exp.addItem("Ninguno (Tarea General)")
        for exp in exps:
            texto = f"{exp[1]} - {exp[2]}"[:60]
            self.lista_exp[texto] = exp[0]
            self.combo_exp.addItem(texto)

    def sincronizar_fecha_inputs(self): self.dt_fecha.setDate(self.calendario.selectedDate())

    def resaltar_calendario(self):
        self.calendario.setDateTextFormat(QDate(), QTextCharFormat())
        conn = base_datos.conectar(); tareas = conn.execute("SELECT fecha FROM tareas WHERE completada = 0").fetchall(); conn.close()
        formato = QTextCharFormat(); formato.setBackground(QColor("#ffcc80")); formato.setFontWeight(QFont.Weight.Bold)
        for t in tareas:
            try: p = t[0].split("/"); qdate = QDate(int(p[2]), int(p[1]), int(p[0])); self.calendario.setDateTextFormat(qdate, formato)
            except: pass

    def filtrar_por_dia(self, qdate):
        self.dia_filtrado = qdate.toString("dd/MM/yyyy")
        self.lbl_filtro.setText(f"Tareas para el: {self.dia_filtrado}")
        self.refrescar_tareas()

    def quitar_filtro(self):
        self.dia_filtrado = None
        self.lbl_filtro.setText("Mostrando TODAS las tareas")
        self.refrescar_tareas()

    def guardar_tarea(self):
        desc = self.txt_desc.toPlainText().strip()
        if not desc: return
        fecha_str = self.dt_fecha.date().toString("dd/MM/yyyy")
        hora_str = self.tm_hora.time().toString("HH:mm")
        id_exp = self.lista_exp.get(self.combo_exp.currentText())
        
        conn = base_datos.conectar()
        if self.id_tarea_editando:
            conn.execute("UPDATE tareas SET fecha=?, hora=?, descripcion=?, id_exp=? WHERE id=?", (fecha_str, hora_str, desc, id_exp, self.id_tarea_editando))
            self.id_tarea_editando = None
            self.btn_guardar.setText("➕ GUARDAR TAREA")
            self.btn_guardar.setStyleSheet("QPushButton { background-color: #0078d7; color: white; font-weight: bold; padding: 10px; border-radius: 4px; } QPushButton:hover { background-color: #005a9e; }")
        else:
            conn.execute("INSERT INTO tareas (fecha, hora, descripcion, completada, id_exp) VALUES (?, ?, ?, 0, ?)", (fecha_str, hora_str, desc, id_exp))
            
        conn.commit(); conn.close()
        self.txt_desc.clear(); self.combo_exp.setCurrentIndex(0); self.tm_hora.setTime(QTime(0, 0))
        self.refrescar_tareas()

    def cargar_para_editar(self):
        item = self.tree.currentItem()
        if not item: return
        self.id_tarea_editando = item.text(3)
        conn = base_datos.conectar(); tarea = conn.execute("SELECT fecha, hora, descripcion, id_exp FROM tareas WHERE id=?", (self.id_tarea_editando,)).fetchone(); conn.close()
        if tarea:
            p = tarea[0].split("/"); self.dt_fecha.setDate(QDate(int(p[2]), int(p[1]), int(p[0])))
            h = tarea[1].split(":"); 
            if len(h) == 2: self.tm_hora.setTime(QTime(int(h[0]), int(h[1])))
            self.txt_desc.setText(tarea[2])
            self.combo_exp.setCurrentIndex(0)
            if tarea[3]:
                for text, id_val in self.lista_exp.items():
                    if id_val == tarea[3]: self.combo_exp.setCurrentText(text); break
            self.btn_guardar.setText("🔄 GUARDAR CAMBIOS")
            self.btn_guardar.setStyleSheet("background-color: #f57c00; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")

    def tarea_seleccionada(self):
        item = self.tree.currentItem()
        if not item: return
        id_exp = item.text(4)
        if id_exp and id_exp != "None":
            conn = base_datos.conectar(); exp = conn.execute("SELECT caratula, nro_exp FROM expedientes WHERE id=?", (id_exp,)).fetchone(); conn.close()
            if exp:
                self.lbl_info_caratula.setText(exp[0].upper())
                self.lbl_info_nro.setText(f"NRO: {exp[1]}")
                self.btn_ir_carpeta.setEnabled(True)
        else:
            self.lbl_info_caratula.setText("TAREA GENERAL")
            self.lbl_info_nro.setText("Nro: -")
            self.btn_ir_carpeta.setEnabled(False)

    def abrir_carpeta_desde_tarea(self):
        item = self.tree.currentItem()
        if item and self.callback_abrir_carpeta:
            id_exp = item.text(4)
            if id_exp and id_exp != "None": self.callback_abrir_carpeta(int(id_exp))

    def completar_tarea(self):
        item = self.tree.currentItem()
        if item:
            conn = base_datos.conectar(); conn.execute("UPDATE tareas SET completada = 1 WHERE id=?", (item.text(3),)); conn.commit(); conn.close()
            self.refrescar_tareas()

    def borrar_tarea(self):
        item = self.tree.currentItem()
        if item:
            reply = QMessageBox.question(self, 'Borrar', '¿Eliminar tarea definitivamente?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                conn = base_datos.conectar(); conn.execute("DELETE FROM tareas WHERE id=?", (item.text(3),)); conn.commit(); conn.close()
                self.refrescar_tareas()

    def refrescar_tareas(self):
        self.tree.clear()
        conn = base_datos.conectar()
        if self.dia_filtrado: res = conn.execute("SELECT id, fecha, hora, descripcion, completada, id_exp FROM tareas WHERE fecha=? ORDER BY completada ASC, id DESC", (self.dia_filtrado,)).fetchall()
        else: res = conn.execute("SELECT id, fecha, hora, descripcion, completada, id_exp FROM tareas ORDER BY completada ASC, id DESC").fetchall()
        for fila in res:
            item = QTreeWidgetItem([fila[1], fila[2], fila[3], str(fila[0]), str(fila[5])])
            if fila[4] == 1: 
                for col in range(3): item.setBackground(col, QColor("#eaf2e3")); item.setForeground(col, QColor("#7a8b75"))
            self.tree.addTopLevelItem(item)
        conn.close()
        self.resaltar_calendario()
        self.lbl_info_caratula.setText("SELECCIONE UNA TAREA...")
        self.lbl_info_nro.setText("Nro: -")
        self.btn_ir_carpeta.setEnabled(False)
