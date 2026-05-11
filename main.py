import sys
import traceback

try:
    from PyQt6.QtWidgets import QApplication
    import main_window

    if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = main_window.MainWindow()
        window.show()
        sys.exit(app.exec())

except Exception as e:
    print("¡Ocurrió un error al arrancar el programa!\n")
    traceback.print_exc()  # Esto imprime el error exacto
    input("\nPresiona la tecla ENTER para cerrar esta ventana...")
