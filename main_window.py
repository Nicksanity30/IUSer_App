import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem, 
                             QLabel, QFrame, QSplitter, QDialog, QFormLayout, 
                             QComboBox, QTabWidget, QCalendarWidget, QScrollArea, 
                             QMessageBox, QMenuBar, QCheckBox, QTabBar, QListWidget, 
                             QGridLayout, QHeaderView, QGraphicsDropShadowEffect) # <--- Agregamos QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QUrl, QSettings
from PyQt6.QtGui import QFont, QColor, QAction, QDesktopServices, QPixmap, QPainter, QPen
import base_datos
from folder_view import VentanaCarpeta
from agenda_view import VentanaAgenda
from datetime import datetime

JUZGADOS_NQN = ["JUZGADO CIVIL N° 1 - NEUQUÉN", "JUZGADO CIVIL N° 2 - NEUQUÉN", "JUZGADO CIVIL N° 3 - NEUQUÉN", "JUZGADO CIVIL N° 1 - CUTRAL CO", "JUZGADO FEDERAL - NEUQUÉN"]

# === PALETA DE COLORES PREMIUM ===
BG_POSTIT = "#fffde7"      # Amarillo pastel (papel viejo para la lista de agenda)
BG_PANEL_IZQ = "#ffffff"   # Fondo de los contenedores
BG_BLANCO = "#ffffff"      # Color papel blanco hueso
SELECCION_AZUL = "#b3e5fc" # Selección azul suave

# === VENTANA: CONFIGURACIÓN DE USUARIO ===
class VentanaPerfil(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración del Perfil Profesional")
        self.resize(450, 400)
        self.setStyleSheet(f"background-color: {BG_POSTIT};")
        
        layout = QVBoxLayout(self)
        lbl_info = QLabel("<b>Complete sus datos para automatizar el Membrete en sus PDFs:</b>")
        layout.addWidget(lbl_info)
        
        form = QFormLayout()
        self.ent_nombre = QLineEdit()
        self.ent_mat = QLineEdit()
        self.ent_tel = QLineEdit()
        self.ent_mail = QLineEdit()
        self.ent_dom = QLineEdit()
        
        form.addRow("Nombre / Estudio:", self.ent_nombre)
        form.addRow("Matrícula:", self.ent_mat)
        form.addRow("Teléfono:", self.ent_tel)
        form.addRow("Email:", self.ent_mail)
        form.addRow("Domicilio Legal:", self.ent_dom)
        layout.addLayout(form)
        
        layout.addWidget(QLabel("<hr><b>Ajustes del Membrete:</b>"))
        
        self.chk_usar = QCheckBox("Incluir membrete automáticamente al exportar a PDF")
        layout.addWidget(self.chk_usar)
        
        f_pos = QHBoxLayout()
        f_pos.addWidget(QLabel("Posición en la hoja:"))
        self.cmb_posicion = QComboBox()
        self.cmb_posicion.addItems(["Izquierda", "Centro", "Derecha"])
        f_pos.addWidget(self.cmb_posicion)
        layout.addLayout(f_pos)
        
        btn_guardar = QPushButton("💾 GUARDAR CAMBIOS")
        btn_guardar.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        btn_guardar.clicked.connect(self.guardar_datos)
        layout.addWidget(btn_guardar)
        
        self.cargar_datos()

    def cargar_datos(self):
        conn = base_datos.conectar()
        usr = conn.execute("SELECT nombre, matricula, telefono, email, domicilio, usar_membrete, posicion FROM usuario WHERE id=1").fetchone()
        conn.close()
        if usr:
            self.ent_nombre.setText(usr[0])
            self.ent_mat.setText(usr[1])
            self.ent_tel.setText(usr[2])
            self.ent_mail.setText(usr[3])
            self.ent_dom.setText(usr[4])
            self.chk_usar.setChecked(bool(usr[5]))
            self.cmb_posicion.setCurrentText(usr[6])

    def guardar_datos(self):
        conn = base_datos.conectar()
        conn.execute("UPDATE usuario SET nombre=?, matricula=?, telefono=?, email=?, domicilio=?, usar_membrete=?, posicion=? WHERE id=1",
                     (self.ent_nombre.text(), self.ent_mat.text(), self.ent_tel.text(), self.ent_mail.text(), self.ent_dom.text(), 
                      int(self.chk_usar.isChecked()), self.cmb_posicion.currentText()))
        conn.commit(); conn.close()
        QMessageBox.information(self, "Guardado", "Perfil actualizado correctamente.")
        self.accept()

# === NUEVA VENTANA: CONFIGURAR ENLACES RÁPIDOS ===
class VentanaConfigEnlaces(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Accesos Rápidos")
        self.resize(500, 450)
        self.setStyleSheet(f"background-color: {BG_BLANCO};")
        self.settings = QSettings("IUSer", "Preferencias")
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Sitios Web
        tab_webs = QWidget()
        form_webs = QFormLayout(tab_webs)
        self.webs_inputs = []
        for i in range(1, 5):
            nom = QLineEdit(self.settings.value(f"web{i}_nom", f"Sitio Web {i}"))
            url = QLineEdit(self.settings.value(f"web{i}_url", "https://"))
            form_webs.addRow(f"Nombre Botón {i}:", nom)
            form_webs.addRow(f"URL {i}:", url)
            self.webs_inputs.append((nom, url))
        tabs.addTab(tab_webs, "🌐 Sitios Web")

        # Tab 2: Códigos y Leyes
        tab_codigos = QWidget()
        form_codigos = QFormLayout(tab_codigos)
        self.codigos_inputs = []
        for i in range(1, 5):
            nom = QLineEdit(self.settings.value(f"cod{i}_nom", f"Código {i}"))
            url = QLineEdit(self.settings.value(f"cod{i}_url", "https://"))
            form_codigos.addRow(f"Nombre Código {i}:", nom)
            form_codigos.addRow(f"URL {i}:", url)
            self.codigos_inputs.append((nom, url))
        tabs.addTab(tab_codigos, "📚 Códigos y Leyes")

        btn_guardar = QPushButton("💾 GUARDAR ENLACES")
        btn_guardar.setStyleSheet("background-color: #1976d2; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        btn_guardar.clicked.connect(self.guardar_enlaces)
        layout.addWidget(btn_guardar)

    def guardar_enlaces(self):
        for i, (nom, url) in enumerate(self.webs_inputs, 1):
            self.settings.setValue(f"web{i}_nom", nom.text())
            self.settings.setValue(f"web{i}_url", url.text())
        for i, (nom, url) in enumerate(self.codigos_inputs, 1):
            self.settings.setValue(f"cod{i}_nom", nom.text())
            self.settings.setValue(f"cod{i}_url", url.text())
            
        QMessageBox.information(self, "Éxito", "Enlaces actualizados correctamente.")
        self.accept()

# === NUEVO WIDGET: CALENDARIO CON REMARCO Y ANILLADO (EFECTO 3D) ===
class CalendarioAnilladoWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"background-color: {BG_BLANCO}; border-radius: 6px;")
        
        # MAGIA 3D: Sombra paralela para que parezca un taco de papel
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(12)
        sombra.setXOffset(3)
        sombra.setYOffset(5)
        sombra.setColor(QColor(0, 0, 0, 70)) # Sombra suave
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        # 20px arriba para dibujar los anillos
        layout.setContentsMargins(5, 20, 5, 5) 
        layout.setSpacing(0)

        # Calendario
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        layout.addWidget(self.calendar)

        # CSS Corregido
        self.calendar.setStyleSheet(f"""
            QCalendarWidget QWidget {{ 
                alternate-background-color: {BG_BLANCO}; 
            }} 
            #qt_calendar_navigationbar {{
                background-color: {BG_BLANCO};
                border: none;
            }}
            /* CORRECCIÓN: Damos padding a los botones para que no tape el texto la flecha */
            QCalendarWidget QToolButton {{
                color: #111111; 
                background-color: transparent;
                font-size: 11pt;
                font-weight: bold;
                padding-right: 15px; /* <--- MAGIA QUE ARREGLA LA FLECHITA */
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: #e0e0e0;
                border-radius: 4px;
            }}
            QCalendarWidget QSpinBox {{
                color: #111111;
                background-color: transparent;
                font-weight: bold;
                font-size: 11pt;
                padding-right: 15px;
            }}
            /* NUEVO COLOR DE BARRA DE DÍAS: Un Taupe / Gris cálido súper profesional */
            QCalendarWidget QHeaderView {{
                background-color: #D7CCC8; 
                color: #333333;
                font-weight: bold;
                font-size: 8pt;
                border: none;
                border-bottom: 2px solid #BCAAA4; /* Borde oscuro para dar volumen */
            }}
            QCalendarWidget QHeaderView::section {{
                background-color: #D7CCC8;
                color: #333333;
                border: none;
                padding: 4px;
            }}
            QCalendarWidget QAbstractItemView:enabled {{ 
                font-size: 8pt; 
                background-color: {BG_BLANCO}; 
                selection-background-color: {SELECCION_AZUL}; 
                selection-color: black; 
                border: none;
            }}
        """)

    # DIBUJO DE ANILLOS A MANO
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#999999"), 1.5)
        painter.setPen(pen)
        
        ancho = self.width()
        
        # Bucle que dibuja un anillo cada 20 píxeles
        for x in range(15, ancho - 15, 20):
            painter.setBrush(QColor("#e0e0e0"))
            painter.drawRoundedRect(x, 2, 6, 18, 3, 3)
            
            painter.setBrush(QColor("#222222"))
            painter.drawEllipse(x + 1, 14, 4, 4)

# === VENTANA PRINCIPAL ===
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IUSer - Gestión Jurídica Profesional")
        self.setMinimumSize(1100, 750)
        self.showMaximized()
        
        # === TAPETE CREMA NEUTRO Y DESCANSADO ===
        self.setStyleSheet("QMainWindow { background-color: #F4EFEA; }")
        
        self.settings = QSettings("IUSer", "Preferencias")
        self.inicializar_enlaces_por_defecto()

        self.carpetas_abiertas = {}
        self.agenda_abierta = None

        self.crear_menu_superior()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: transparent;") # Transparente para ver el tapete crema
        self.layout_principal = QHBoxLayout(self.central_widget)
        self.layout_principal.setContentsMargins(15, 15, 15, 15)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: transparent; width: 10px; }")
        self.layout_principal.addWidget(self.splitter)

        self.setup_panel_izquierdo()
        self.setup_panel_derecho()
        self.actualizar_lista()
        
        self.verificar_alertas_hoy()

    def inicializar_enlaces_por_defecto(self):
        if not self.settings.contains("web1_nom"):
            self.settings.setValue("web1_nom", "🏛️ Consulta Web (Jus Neuquén)")
            self.settings.setValue("web1_url", "https://www.jusneuquen.gov.ar/")
            self.settings.setValue("web2_nom", "⚖️ DEXTRA / Ingresos")
            self.settings.setValue("web2_url", "https://dextra.jusneuquen.gov.ar/")
            self.settings.setValue("web3_nom", "AFIP")
            self.settings.setValue("web3_url", "https://www.afip.gob.ar/")
            self.settings.setValue("web4_nom", "Boletín Oficial")
            self.settings.setValue("web4_url", "https://www.boletinoficial.gob.ar/")
            
            self.settings.setValue("cod1_nom", "CPCC\nNeuquén")
            self.settings.setValue("cod1_url", "http://biblioteca.jusneuquen.gov.ar/")
            self.settings.setValue("cod2_nom", "Código\nCivil y Com.")
            self.settings.setValue("cod2_url", "http://servicios.infoleg.gob.ar/infolegInternet/anexos/235000-239999/235975/norma.htm")
            self.settings.setValue("cod3_nom", "Código\nFiscal")
            self.settings.setValue("cod3_url", "https://dprneuquen.gob.ar/")
            self.settings.setValue("cod4_nom", "Const.\nNacional")
            self.settings.setValue("cod4_url", "http://servicios.infoleg.gob.ar/infolegInternet/anexos/0-4999/804/norma.htm")

    def crear_menu_superior(self):
        barra_menu = self.menuBar()
        barra_menu.setStyleSheet("QMenuBar { background-color: #eceff1; font-weight: bold; padding: 3px; border-bottom: 1px solid #ccc; } QMenuBar::item:selected { background-color: #cfd8dc; }")
        
        menu_perfil = barra_menu.addMenu("👤 Mi Perfil")
        act_configurar = QAction("⚙️ Configurar Datos y Membrete...", self)
        act_configurar.triggered.connect(self.abrir_perfil)
        menu_perfil.addAction(act_configurar)
        
        menu_herramientas = barra_menu.addMenu("🛠️ Herramientas Rápidas")
        menu_herramientas.addAction(QAction("Calculadora de Plazos (Próximamente)", self))
        menu_herramientas.addAction(QAction("Repositorio de Plantillas (Próximamente)", self))

        menu_enlaces = barra_menu.addMenu("🔗 Accesos y Enlaces")
        act_editar_enlaces = QAction("⚙️ Configurar Accesos Rápidos...", self)
        act_editar_enlaces.triggered.connect(self.abrir_config_enlaces)
        menu_enlaces.addAction(act_editar_enlaces)

    def abrir_perfil(self):
        dlg = VentanaPerfil(self)
        dlg.exec()

    def abrir_config_enlaces(self):
        dlg = VentanaConfigEnlaces(self)
        if dlg.exec():
            self.actualizar_botones_enlaces()

    def verificar_alertas_hoy(self):
        hoy_str = datetime.now().strftime("%d/%m/%Y")
        conn = base_datos.conectar()
        try:
            tareas_hoy = conn.execute("SELECT hora, descripcion FROM tareas WHERE fecha=? AND completada=0", (hoy_str,)).fetchall()
        except:
            tareas_hoy = []
        conn.close()

        if tareas_hoy:
            msg = QMessageBox(self)
            msg.setWindowTitle("Vencimientos de Hoy")
            msg.setIcon(QMessageBox.Icon.Warning)
            texto_html = "<h3>¡Atención! Tienes tareas pendientes para hoy:</h3><ul>"
            for t in tareas_hoy: texto_html += f"<li><b>{t[0]} hs:</b> {t[1]}</li>"
            texto_html += "</ul><br>Revisa 'Mi Agenda' para más detalles."
            msg.setText(texto_html)
            msg.setStyleSheet("QMessageBox { background-color: #ffcdd2; } QLabel { color: #b71c1c; font-size: 11pt; } QPushButton { background-color: white; color: black; border: 1px solid #b71c1c; padding: 6px; font-weight: bold; border-radius: 4px;} QPushButton:hover { background-color: #ffebee; }")
            msg.exec()

    # --- PANEL IZQUIERDO (DASHBOARD) ---
    def setup_panel_izquierdo(self):
        self.panel_izq = QFrame()
        self.panel_izq.setFixedWidth(280)
        # Hacemos que el panel izquierdo sea transparente para que las cosas "floten" en el tapete crema
        self.panel_izq.setStyleSheet("background-color: transparent; border: none;")
        layout = QVBoxLayout(self.panel_izq)
        layout.setContentsMargins(0, 0, 10, 0) # Margen derecho para separarlo de los expedientes
        layout.setSpacing(15) # Más espacio entre el calendario, agenda, y botones

        # 1. Calendario Anillado 3D
        self.widget_calendario = CalendarioAnilladoWidget()
        self.mini_cal = self.widget_calendario.calendar
        self.mini_cal.selectionChanged.connect(self.actualizar_mini_agenda)
        layout.addWidget(self.widget_calendario)

        # 2. Agenda Vademécum
        lbl_agenda = QLabel("📌 TAREAS DEL DÍA:")
        lbl_agenda.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_agenda.setStyleSheet("border: none; color: #555;")
        layout.addWidget(lbl_agenda)

        self.lista_tareas = QListWidget()
        self.lista_tareas.setFixedHeight(90)
        self.lista_tareas.setStyleSheet(f"background-color: {BG_POSTIT}; border: 1px solid #ccc; border-radius: 4px; font-size: 9pt;")
        
        # Efecto 3D sutil para la libretita amarilla
        sombra_agenda = QGraphicsDropShadowEffect(self)
        sombra_agenda.setBlurRadius(8)
        sombra_agenda.setXOffset(2)
        sombra_agenda.setYOffset(3)
        sombra_agenda.setColor(QColor(0, 0, 0, 40))
        self.lista_tareas.setGraphicsEffect(sombra_agenda)
        
        self.lista_tareas.doubleClicked.connect(self.abrir_agenda) 
        layout.addWidget(self.lista_tareas)

        btn_agenda = QPushButton("📅 ABRIR AGENDA COMPLETA")
        btn_agenda.setStyleSheet("QPushButton { background-color: #ffe0b2; color: #e65100; border: 1px solid #ffcc80; padding: 6px; font-weight: bold; border-radius: 4px; font-size: 9pt; } QPushButton:hover { background-color: #ffcc80; }")
        btn_agenda.clicked.connect(self.abrir_agenda)
        layout.addWidget(btn_agenda)

        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("border: 1px solid #dcd1c4;") # Línea suave acorde al crema
        layout.addWidget(linea)

        # 3. Enlaces y Códigos
        self.contenedor_enlaces = QWidget()
        self.layout_enlaces = QVBoxLayout(self.contenedor_enlaces)
        self.layout_enlaces.setContentsMargins(0, 0, 0, 0)
        self.layout_enlaces.setSpacing(5)
        layout.addWidget(self.contenedor_enlaces)

        self.actualizar_botones_enlaces()
        
        layout.addStretch()
        self.actualizar_mini_agenda() 
        self.splitter.addWidget(self.panel_izq)

    def actualizar_botones_enlaces(self):
        while self.layout_enlaces.count():
            item = self.layout_enlaces.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget(): child.widget().deleteLater()
                item.layout().deleteLater()

        # Botones de Webs
        lbl_links = QLabel("🔗 ACCESOS WEB:")
        lbl_links.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_links.setStyleSheet("border: none; color: #555;")
        self.layout_enlaces.addWidget(lbl_links)

        for i in range(1, 5):
            nom = self.settings.value(f"web{i}_nom", f"Sitio {i}")
            url = self.settings.value(f"web{i}_url", "https://")
            btn = QPushButton(nom)
            btn.setStyleSheet("text-align: left; padding: 5px; background: #ffffff; border: 1px solid #b0bec5; border-radius: 4px; font-size: 8pt; color: #1565c0;")
            btn.clicked.connect(lambda checked, u=url: QDesktopServices.openUrl(QUrl(u)))
            self.layout_enlaces.addWidget(btn)

        # Grilla 2x2 Códigos
        lbl_cod = QLabel("📚 CÓDIGOS Y LEYES:")
        lbl_cod.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_cod.setStyleSheet("border: none; color: #555; margin-top: 5px;")
        self.layout_enlaces.addWidget(lbl_cod)

        grid_codigos = QGridLayout()
        grid_codigos.setSpacing(4)
        
        posiciones = [(0,0), (0,1), (1,0), (1,1)]
        for i in range(1, 5):
            nom = self.settings.value(f"cod{i}_nom", f"Cod {i}")
            url = self.settings.value(f"cod{i}_url", "https://")
            btn_cod = QPushButton(nom)
            btn_cod.setMinimumHeight(45) 
            btn_cod.setStyleSheet("background: #f1f8e9; border: 1px solid #aed581; border-radius: 4px; font-size: 8pt; font-weight: bold; color: #33691e;")
            btn_cod.clicked.connect(lambda checked, u=url: QDesktopServices.openUrl(QUrl(u)))
            
            row, col = posiciones[i-1]
            grid_codigos.addWidget(btn_cod, row, col)

        self.layout_enlaces.addLayout(grid_codigos)

    def actualizar_mini_agenda(self):
        self.lista_tareas.clear()
        fecha_sel = self.mini_cal.selectedDate().toString("dd/MM/yyyy")
        
        conn = base_datos.conectar()
        try:
            tareas = conn.execute("SELECT hora, descripcion FROM tareas WHERE fecha=? AND completada=0 ORDER BY hora", (fecha_sel,)).fetchall()
            if not tareas:
                self.lista_tareas.addItem("✅ Sin tareas pendientes.")
            else:
                for t in tareas:
                    self.lista_tareas.addItem(f"⏰ {t[0]} hs - {t[1]}")
        except Exception:
            self.lista_tareas.addItem("No hay datos de agenda.")
        finally:
            conn.close()

    # --- PANEL DERECHO (CAJÓN DE FICHEROS) ---
    def setup_panel_derecho(self):
        self.panel_der = QWidget()
        layout_principal = QVBoxLayout(self.panel_der)
        layout_principal.setContentsMargins(0, 0, 0, 0) 

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.cerrar_pestana)
        
        # Efecto 3D para el cajón de ficheros completo
        sombra_fichero = QGraphicsDropShadowEffect(self)
        sombra_fichero.setBlurRadius(15)
        sombra_fichero.setXOffset(5)
        sombra_fichero.setYOffset(5)
        sombra_fichero.setColor(QColor(0, 0, 0, 50))
        self.tabs.setGraphicsEffect(sombra_fichero)

        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #B0A890; 
                background-color: #FAFAFA; 
                border-radius: 6px;
                top: -1px; 
            }
            QTabBar::tab {
                background-color: #E6E1D1; 
                border: 1px solid #B0A890;
                border-bottom-color: #B0A890; 
                border-top-left-radius: 12px;  
                border-top-right-radius: 4px;   
                padding: 8px 16px;
                margin-right: 3px; 
                color: #444;
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
            }
            QTabBar::tab:selected {
                background-color: #FAFAFA; 
                border-bottom-color: #FAFAFA; 
                border-top: 3px solid #8B0000; 
                color: black;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #F0EAD6; 
            }
        """)
        layout_principal.addWidget(self.tabs)

        self.tab_grilla = QWidget()
        layout_grilla = QVBoxLayout(self.tab_grilla)
        layout_grilla.setContentsMargins(10, 10, 10, 10)

        barra_sup = QHBoxLayout()
        self.btn_nuevo = QPushButton("+ NUEVO EXPEDIENTE")
        self.btn_nuevo.setStyleSheet("background-color: #c8e6c9; color: #2e7d32; border: 1px solid #a5d6a7; padding: 6px 12px; font-weight: bold; border-radius: 4px;")
        self.btn_nuevo.clicked.connect(self.formulario_expediente)
        
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("🔍 Buscar por carátula o número (Filtro en tiempo real)...")
        self.buscador.setStyleSheet(f"background-color: {BG_BLANCO}; padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 10pt;")
        self.buscador.textChanged.connect(self.actualizar_lista)

        barra_sup.addWidget(self.btn_nuevo)
        barra_sup.addWidget(self.buscador)
        layout_grilla.addLayout(barra_sup)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Nro Expediente", "Carátula", "ID"])
        self.tree.setColumnWidth(0, 150)
        self.tree.hideColumn(2)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{ background-color: {BG_BLANCO}; alternate-background-color: #f7f7f7; border: 1px solid #ccc; font-size: 9pt; border-radius: 4px; }}
            QTreeWidget::item {{ height: 22px; padding: 0px; }}
            QTreeWidget::item:selected {{ background-color: {SELECCION_AZUL}; color: black; font-weight: bold; }}
            QHeaderView::section {{ background-color: #e0e0e0; padding: 4px; border: 1px solid #ccc; font-weight: bold; font-size: 9pt; }}
        """)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self.abrir_carpeta)
        self.tree.itemSelectionChanged.connect(self.mostrar_previa)
        layout_grilla.addWidget(self.tree)

        self.panel_inf = QFrame()
        self.panel_inf.setFixedHeight(70)
        self.panel_inf.setStyleSheet(f"background-color: {BG_BLANCO}; border: 1px solid #b3d7ff; border-radius: 4px;")
        layout_inf = QVBoxLayout(self.panel_inf)
        layout_inf.setContentsMargins(5, 5, 5, 5)
        self.lbl_previa = QLabel("Seleccione un expediente para ver detalles...")
        self.lbl_previa.setFont(QFont("Segoe UI", 9))
        layout_inf.addWidget(self.lbl_previa)
        layout_grilla.addWidget(self.panel_inf)

        self.tabs.addTab(self.tab_grilla, "🏠 Listado de Causas")
        self.tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)
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
            widget_carpeta = self.carpetas_abiertas[id_exp]
            idx = self.tabs.indexOf(widget_carpeta)
            if idx != -1: self.tabs.setCurrentIndex(idx)
            return
            
        conn = base_datos.conectar()
        info = conn.execute("SELECT caratula, nro_exp FROM expedientes WHERE id=?", (id_exp,)).fetchone()
        conn.close()
        
        if info:
            def al_cerrar_carpeta(id_e):
                if id_e in self.carpetas_abiertas:
                    widget = self.carpetas_abiertas[id_e]
                    idx = self.tabs.indexOf(widget)
                    if idx != -1: self.tabs.removeTab(idx)
                    del self.carpetas_abiertas[id_e]

            carpeta = VentanaCarpeta(id_exp, info, callback_cerrar=al_cerrar_carpeta)
            carpeta.setStyleSheet(f"background-color: {BG_BLANCO}; border: none;")
            self.carpetas_abiertas[id_exp] = carpeta
            
            titulo_pestana = f"📂 {info[0][:15]}..." if len(info[0]) > 15 else f"📂 {info[0]}"
            idx = self.tabs.addTab(carpeta, titulo_pestana)
            
            self.tabs.setTabToolTip(idx, f"Expediente N°: {info[1]}\nCarátula: {info[0]}")
            self.tabs.setCurrentIndex(idx)

    def cerrar_pestana(self, index):
        if index == 0: return
        widget = self.tabs.widget(index)
        
        id_a_eliminar = None
        for id_exp, vent in self.carpetas_abiertas.items():
            if vent == widget:
                id_a_eliminar = id_exp
                break
                
        if id_a_eliminar: del self.carpetas_abiertas[id_a_eliminar]
        self.tabs.removeTab(index)
        widget.deleteLater()

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
