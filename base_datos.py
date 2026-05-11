import sqlite3
import os

CARPETA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(CARPETA_ACTUAL, "iuser_database.db")

def conectar():
    return sqlite3.connect(RUTA_DB)

def iniciar_db():
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS expedientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caratula TEXT, nro_exp TEXT, juzgado TEXT, responsable TEXT,
        act_nom TEXT, act_cuit TEXT, act_dom TEXT, act_loc TEXT, act_tel TEXT, act_mail TEXT,
        dem_nom TEXT, dem_cuit TEXT, dem_dom TEXT, dem_loc TEXT, dem_tel TEXT, dem_mail TEXT,
        monto_reclamo TEXT, fecha_inicio TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        id_exp INTEGER, fecha TEXT, hora TEXT, titulo TEXT, contenido TEXT, 
        origen TEXT DEFAULT 'Otros', resaltado INTEGER DEFAULT 0,
        FOREIGN KEY(id_exp) REFERENCES expedientes(id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, hora TEXT, descripcion TEXT, completada INTEGER DEFAULT 0,
        id_exp INTEGER)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS plantillas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT, contenido TEXT)''')

    # === NUEVA TABLA: PERFIL DEL USUARIO (Para comercialización) ===
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT, matricula TEXT, telefono TEXT, email TEXT,
        domicilio TEXT, usar_membrete INTEGER DEFAULT 1,
        posicion TEXT DEFAULT 'Derecha')''')

    # Cargamos las plantillas por defecto si está vacío
    cursor.execute("SELECT count(*) FROM plantillas")
    if cursor.fetchone()[0] == 0:
        plantillas_base = [
            ("Mero Trámite / Acompaña Oficio", "<p align='right'><b>SEÑOR JUEZ:</b></p><p align='justify'>..., abogado apoderado por la parte actora, manteniendo el domicilio legal constituido en autos, a V.S. respetuosamente digo:</p><p align='justify'>Que por la presente vengo a acompañar oficio debidamente diligenciado, solicitando se agregue a sus antecedentes.</p><p align='center'><b>PROVEER DE CONFORMIDAD,<br>SERÁ JUSTICIA.</b></p>"),
            ("Solicita Pronto Despacho", "<p align='right'><b>SEÑOR JUEZ:</b></p><p align='justify'>..., por la representación invocada, a V.S. respetuosamente digo:</p><p align='justify'>Que habiendo transcurrido con creces los plazos procesales legales desde la última presentación de esta parte sin que se haya dictado resolución, vengo por la presente a solicitar PRONTO DESPACHO sobre lo peticionado oportunamente.</p><p align='center'><b>SERÁ JUSTICIA.</b></p>"),
            ("Constituye Domicilio Electrónico", "<p align='right'><b>SEÑOR JUEZ:</b></p><p align='justify'>Que vengo por la presente a constituir domicilio electrónico en la casilla <b>[CASILLA_AQUI]</b>, solicitando se tenga presente para futuras notificaciones.</p><p align='center'><b>SERÁ JUSTICIA.</b></p>")
        ]
        cursor.executemany("INSERT INTO plantillas (titulo, contenido) VALUES (?, ?)", plantillas_base)

    # Creamos un usuario en blanco por defecto si no existe
    cursor.execute("SELECT count(*) FROM usuario")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuario (nombre, matricula, telefono, email, domicilio, usar_membrete, posicion) VALUES ('', '', '', '', '', 1, 'Derecha')")

    # Intentos de actualización para tablas viejas
    try: cursor.execute("ALTER TABLE movimientos ADD COLUMN origen TEXT DEFAULT 'Otros'")
    except sqlite3.OperationalError: pass 
    try: cursor.execute("ALTER TABLE movimientos ADD COLUMN resaltado INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass 
    try: cursor.execute("ALTER TABLE tareas ADD COLUMN completada INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass 
    try: cursor.execute("ALTER TABLE tareas ADD COLUMN id_exp INTEGER")
    except sqlite3.OperationalError: pass 
    try: cursor.execute("ALTER TABLE expedientes ADD COLUMN monto_reclamo TEXT")
    except sqlite3.OperationalError: pass 
    try: cursor.execute("ALTER TABLE expedientes ADD COLUMN fecha_inicio TEXT")
    except sqlite3.OperationalError: pass 

    conn.commit()
    conn.close()

iniciar_db()
