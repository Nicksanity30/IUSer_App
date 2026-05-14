import sys
import traceback

try:
    from PyQt6.QtWidgets import QApplication
    # Importamos tu archivo de la ventana principal
    import main_window

    if __name__ == "__main__":
        print("Iniciando aplicación IUSer...")
        app = QApplication(sys.argv)
        
        # Instanciamos la clase que está en main_window.py
        window = main_window.MainWindow()
        window.show()
        
        print("Ventana cargada con éxito.")
        sys.exit(app.exec())

except Exception as e:
    print("\n" + "="*40)
    print("¡CRASH DETECTADO!")
    print("="*40)
    traceback.print_exc()  # Esto nos dirá exactamente en qué línea falló
    input("\nPresiona la tecla ENTER para cerrar esta ventana...")
