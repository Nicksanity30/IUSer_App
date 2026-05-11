import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem, 
                             QLabel, QFrame, QSplitter, QDialog, QFormLayout, 
                             QComboBox, QTabWidget, QCalendarWidget, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import base_datos
from folder_view import VentanaCarpeta
from agenda_view import VentanaAgenda
from datetime import datetime

JUZGADOS_NQN = ["JUZGADO CIVIL N° 1 - NEUQUÉN", "JUZGADO CIVIL N° 2 - NEUQUÉN", "JUZGADO CIVIL N° 3 - NEUQUÉN", "JUZGADO CIVIL N° 1 - CUTRAL CO", "JUZGADO FEDERAL - NEUQUÉN"]

BG_POSTIT = "#fffde7"      
BG_PANEL_IZQ = "#ffffff"   
BG_BLANCO = "#ffffff"      
SELECCION_AZUL = "#b3e5fc" 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IUSer - Gestión Jurídica Profesional")
        self.setMinimumSize(1100, 750)
        self.showMaximized()
        self.setStyleSheet(f"QMainWindow {{ background-color: {BG_POSTIT}; }}")

        self.carpetas_abiertas = {}
        self.agenda_abierta = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet(f"background-color: {BG_POSTIT};")
        self.layout_principal = QHBoxLayout(self.central_widget)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout_principal.addWidget(self.splitter)

        self.setup_panel_izquierdo()
        self.setup_panel_derecho()
        self.actualizar_lista()
        
        # == EJECUCIÓN DE ALERTA AL INICIAR ==
        self.verificar_alertas_hoy()

    def verificar_alertas_hoy(self):
        """Escanea tareas pendientes de hoy y lanza una alerta rojo pastel"""
        hoy_str = datetime.now().strftime("%d/%m/%Y")
        conn = base_datos.conectar()
        tareas_hoy = conn.execute("SELECT hora, descripcion FROM tareas WHERE fecha=? AND completada=0", (hoy_str,)).fetchall()
        conn.close()

        if tareas_hoy:
            msg = QMessageBox(self)
            msg.setWindowTitle("Vencimientos de Hoy")
            msg.setIcon(QMessageBox.Icon.Warning)
            
            texto_html = "<h3>¡Atención! Tienes tareas pendientes para hoy:</h3><ul>"
            for t in tareas_hoy:
                texto_html += f"<li><b>{t[0]} hs:</b> {t[1]}</li>"
            texto_html += "</ul><br>Revisa 'Mi Agenda' para más detalles."
            
            msg.setText(texto_html)
            # Estética Rojo Pastel requerida
            msg.setStyleSheet("""
                QMessageBox { background-color: #ffcdd2; } 
                QLabel { color: #b71c1c; font-size: 11pt; } 
                QPushButton { background-color: white; color: black; border: 1px solid #b71c1c; padding: 6px; font-weight: bold; border-radius: 4px;}
                QPushButton:hover { background-color: #ffebee; }
            """)
            msg.exec()

    def setup_panel_izquierdo(self):
        self.panel_izq = QFrame()
        self.panel_izq.setFixedWidth(260)
        self.panel_izq.setStyleSheet(f"background-color: {BG_PANEL_IZQ}; border-right: 1px solid #e0e0e0;")
        layout = QVBoxLayout(self.panel_izq)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl_trabajando = QLabel("TRABAJANDO EN:")
        lbl_trabajando.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        lbl_trabajando.setStyleSheet("border: none; color: #333;")
        lbl_trabajando.setToolTip("Panel de acceso rápido a sus ventanas abiertas.")
        layout.addWidget(lbl_trabajando)

        self.contenedor_botones = QWidget()
        self.contenedor_botones.setStyleSheet("border: none;")
        self.layout_botones = QVBoxLayout(self.contenedor_botones)
        self.layout_botones.setContentsMargins(0, 0, 0, 0)
        self.layout_botones.setSpacing(5)
        
        scroll_izq = QScrollArea()
        scroll_izq.setWidgetResizable(True)
        scroll_izq.setStyleSheet("border: none;")
        scroll_izq.setWidget(self.contenedor_botones)
        layout.addWidget(scroll_izq)

        self.actualizar_panel_izquierdo() 

        self.mini_cal = QCalendarWidget()
        self.mini_cal.setGridVisible(True)
        self.mini_cal.setFixedHeight(180)
        self.mini_cal.setToolTip("Calendario rápido de consulta.")
        self.mini_cal.setStyleSheet(f"""
            QCalendarWidget QWidget {{ alternate-background-color: {BG_BLANCO}; }}
            QCalendarWidget QAbstractItemView:enabled {{ font-size: 8pt; background-color: {BG_BLANCO}; selection-background-color: {SELECCION_AZUL}; selection-color: black; }}
        """)
        layout.addWidget(self.mini_cal)
        self.splitter.addWidget(self.panel_izq)

    def actualizar_panel_izquierdo(self):
        while self.layout_botones.count():
            item = self.layout_botones.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        btn_agenda = QPushButton("📅 MI AGENDA")
        btn_agenda.setToolTip("Abre su agenda principal de tareas y vencimientos procesales.")
        btn_agenda.setStyleSheet("QPushButton { background-color: #ffe0b2; color: #e65100; border: 1px solid #ffcc80; padding: 8px; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #ffcc80; }")
        btn_agenda.clicked.connect(self.abrir_agenda)
        self.layout_botones.addWidget(btn_agenda)

        for id_exp, ventana in self.carpetas_abiertas.items():
            conn = base_datos.conectar()
            res = conn.execute("SELECT caratula FROM expedientes WHERE id=?", (id_exp,)).fetchone()
            conn.close()
            nombre = (res[0][:28] + "...") if res and len(res[0]) > 28 else (res[0] if res else "Expediente")
            
            btn_exp = QPushButton(f"📂 {nombre}")
            btn_exp.setToolTip(f"Volver a la carpeta del expediente: {res[0]}")
            btn_exp.setStyleSheet("QPushButton { background-color: white; color: #333; border: 1px solid #ccc; padding: 6px; text-align: left; border-radius: 4px; } QPushButton:hover { background-color: #e3f2fd; }")
            btn_exp.clicked.connect(lambda checked, v=ventana: v.activateWindow())
            self.layout_botones.addWidget(btn_exp)
            
        self.layout_botones.addStretch()

    def setup_panel_derecho(self):
        self.panel_der = QWidget()
        layout = QVBoxLayout(self.panel_der)

        barra_sup = QHBoxLayout()
        self.btn_nuevo = QPushButton("+ NUEVO EXPEDIENTE")
        self.btn_nuevo.setToolTip("Inicia la carga de una nueva ficha de expediente completo.")
        self.btn_nuevo.setStyleSheet("background-color: #c8e6c9; color: #2e7d32; border: 1px solid #a5d6a7; padding: 8px; font-weight: bold; border-radius: 4px;")
        self.btn_nuevo.clicked.connect(self.formulario_expediente)
        
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar por carátula o número...")
        self.buscador.setToolTip("Escriba para filtrar automáticamente la lista de abajo.")
        self.buscador.setStyleSheet(f"background-color: {BG_BLANCO}; padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        self.buscador.textChanged.connect(self.actualizar_lista)

        barra_sup.addWidget(self.btn_nuevo)
        barra_sup.addWidget(self.buscador)
        layout.addLayout(barra_sup)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Nro Expediente", "Carátula", "ID"])
        self.tree.setColumnWidth(0, 150)
        self.tree.hideColumn(2)
        self.tree.setToolTip("Haga doble clic sobre una fila para abrir la carpeta del expediente.")
        self.tree.setStyleSheet(f"QTreeWidget {{ background-color: {BG_BLANCO}; alternate-background-color: #fcfcfc; border: 1px solid #ccc; font-size: 10pt; }} QTreeWidget::item:selected {{ background-color: {SELECCION_AZUL}; color: black; font-weight: bold; }} QHeaderView::section {{ background-color: #e0e0e0; padding: 4px; border: 1px solid #ccc; font-weight: bold; }}")
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self.abrir_carpeta)
        self.tree.itemSelectionChanged.connect(self.mostrar_previa)
        layout.addWidget(self.tree)

        self.panel_inf = QFrame()
        self.panel_inf.setFixedHeight(100)
        self.panel_inf.setStyleSheet(f"background-color: {BG_BLANCO}; border: 1px solid #b3d7ff; border-radius: 4px;")
        layout_inf = QVBoxLayout(self.panel_inf)
        self.lbl_previa = QLabel("Seleccione un expediente para ver detalles...")
        self.lbl_previa.setFont(QFont("Arial", 10))
        layout_inf.addWidget(self.lbl_previa)
        layout.addWidget(self.panel_inf)

        self.splitter.addWidget(self.panel_der)

    def actualizar_lista(self):
        self.tree.clear()
        filtro = self.buscador.text()
        conn = base_datos.conectar(); cursor = conn.cursor()
        query = "SELECT id, nro_exp, caratula FROM expedientes"
        if filtro: query += f" WHERE caratula LIKE '%{filtro}%' OR nro_exp LIKE '%{filtro}%'"
        cursor.execute(query)
        for fila in cursor.fetchall(): self.tree.addTopLevelItem(QTreeWidgetItem([str(fila[1]), str(fila[2]), str(fila[0])]))
        conn.close()

    def mostrar_previa(self):
        item = self.tree.currentItem()
        if item:
            conn = base_datos.conectar()
            res = conn.execute("SELECT caratula, juzgado FROM expedientes WHERE id=?", (item.text(2),)).fetchone()
            conn.close()
            if res: self.lbl_previa.setText(f"<b>EXPEDIENTE:</b> {res[0]}<br><b>JUZGADO:</b> {res[1]}")

    def abrir_carpeta(self, item, column):
        self.abrir_carpeta_por_id(item.text(2))

    def abrir_carpeta_por_id(self, id_exp):
        id_exp = str(id_exp)
        if id_exp in self.carpetas_abiertas:
            self.carpetas_abiertas[id_exp].activateWindow()
            return
            
        conn = base_datos.conectar()
        info = conn.execute("SELECT caratula, nro_exp FROM expedientes WHERE id=?", (id_exp,)).fetchone()
        conn.close()
        
        if info:
            def al_cerrar_carpeta(id_e):
                if id_e in self.carpetas_abiertas: del self.carpetas_abiertas[id_e]
                self.actualizar_panel_izquierdo()

            carpeta = VentanaCarpeta(id_exp, info, callback_cerrar=al_cerrar_carpeta)
            self.carpetas_abiertas[id_exp] = carpeta
            carpeta.show()
            self.actualizar_panel_izquierdo() 

    def abrir_agenda(self):
        if self.agenda_abierta is None: self.agenda_abierta = VentanaAgenda(callback_abrir_carpeta=self.abrir_carpeta_por_id)
        self.agenda_abierta.show()
        self.agenda_abierta.activateWindow()

    def formulario_expediente(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Ficha de Expediente")
        dlg.resize(650, 500)
        dlg.setStyleSheet(f"background-color: {BG_POSTIT};")
        layout = QVBoxLayout(dlg)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"QTabBar::tab {{ background: #e0e0e0; padding: 8px; }} QTabBar::tab:selected {{ background: {BG_BLANCO}; font-weight: bold; }} QWidget {{ background: {BG_BLANCO}; }}")
        layout.addWidget(tabs)

        campos = {}

        tab_gen = QWidget(); form_gen = QFormLayout(tab_gen)
        campos['caratula'] = QLineEdit(); campos['nro_exp'] = QLineEdit(); campos['juzgado'] = QComboBox(); campos['juzgado'].addItems(JUZGADOS_NQN)
        campos['responsable'] = QLineEdit(); campos['fecha_inicio'] = QLineEdit(); campos['monto_reclamo'] = QLineEdit()
        form_gen.addRow("Carátula:", campos['caratula']); form_gen.addRow("Nro Expediente:", campos['nro_exp']); form_gen.addRow("Juzgado:", campos['juzgado'])
        form_gen.addRow("Responsable/Abogado:", campos['responsable']); form_gen.addRow("Fecha de Inicio:", campos['fecha_inicio']); form_gen.addRow("Monto de Reclamo ($):", campos['monto_reclamo'])
        tabs.addTab(tab_gen, "General")

        tab_act = QWidget(); form_act = QFormLayout(tab_act)
        campos['act_nom'] = QLineEdit(); campos['act_cuit'] = QLineEdit(); campos['act_dom'] = QLineEdit(); campos['act_loc'] = QLineEdit(); campos['act_tel'] = QLineEdit(); campos['act_mail'] = QLineEdit()
        form_act.addRow("Nombre Completo:", campos['act_nom']); form_act.addRow("DNI / CUIT:", campos['act_cuit']); form_act.addRow("Domicilio:", campos['act_dom']); form_act.addRow("Ciudad/Localidad:", campos['act_loc']); form_act.addRow("Teléfono:", campos['act_tel']); form_act.addRow("E-mail:", campos['act_mail'])
        tabs.addTab(tab_act, "Parte Actora")

        tab_dem = QWidget(); form_dem = QFormLayout(tab_dem)
        campos['dem_nom'] = QLineEdit(); campos['dem_cuit'] = QLineEdit(); campos['dem_dom'] = QLineEdit(); campos['dem_loc'] = QLineEdit(); campos['dem_tel'] = QLineEdit(); campos['dem_mail'] = QLineEdit()
        form_dem.addRow("Nombre Completo:", campos['dem_nom']); form_dem.addRow("DNI / CUIT:", campos['dem_cuit']); form_dem.addRow("Domicilio:", campos['dem_dom']); form_dem.addRow("Ciudad/Localidad:", campos['dem_loc']); form_dem.addRow("Teléfono:", campos['dem_tel']); form_dem.addRow("E-mail:", campos['dem_mail'])
        tabs.addTab(tab_dem, "Parte Demandada")

        btn_guardar = QPushButton("💾 GUARDAR FICHA COMPLETA")
        btn_guardar.setToolTip("Guarda la información en la base de datos (Atajo: Presione Enter)")
        btn_guardar.setStyleSheet("background-color: #0078d7; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        layout.addWidget(btn_guardar)

        def guardar():
            if not campos['caratula'].text(): return
            conn = base_datos.conectar(); cursor = conn.cursor()
            valores = (campos['caratula'].text(), campos['nro_exp'].text(), campos['juzgado'].currentText(), campos['responsable'].text(), campos['act_nom'].text(), campos['act_cuit'].text(), campos['act_dom'].text(), campos['act_loc'].text(), campos['act_tel'].text(), campos['act_mail'].text(), campos['dem_nom'].text(), campos['dem_cuit'].text(), campos['dem_dom'].text(), campos['dem_loc'].text(), campos['dem_tel'].text(), campos['dem_mail'].text(), campos['monto_reclamo'].text(), campos['fecha_inicio'].text())
            cursor.execute('''INSERT INTO expedientes (caratula, nro_exp, juzgado, responsable, act_nom, act_cuit, act_dom, act_loc, act_tel, act_mail, dem_nom, dem_cuit, dem_dom, dem_loc, dem_tel, dem_mail, monto_reclamo, fecha_inicio) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', valores)
            conn.commit(); conn.close(); self.actualizar_lista(); dlg.accept()

        btn_guardar.clicked.connect(guardar)

        for widget in campos.values():
            if isinstance(widget, QLineEdit): widget.returnPressed.connect(guardar)

        dlg.exec()
