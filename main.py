import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkcalendar import DateEntry
import sqlite3
import babel.numbers

from ttkthemes import ThemedTk

class GestionDineroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Dinero")

        # Configuración para centrar y escalar la ventana
        root.update_idletasks()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.geometry(f"{width}x{height}+0+0")

        # Variables para almacenar la entrada del usuario
        self.descripcion_var = tk.StringVar()
        self.dinero_var = tk.DoubleVar()
        self.fecha_var = tk.StringVar()
        self.tipo_var = tk.StringVar(value="Ingreso")  # Valor predeterminado: Ingreso

        # Crear la base de datos y la tabla de transacciones
        self.conn = sqlite3.connect("gestion_dinero.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT, 
                descripcion TEXT,
                dinero REAL,
                fecha TEXT
            )
        ''')
        self.conn.commit()

        # Frame principal para centrar widgets
        frame_principal = ttk.Frame(root, padding="20")
        frame_principal.pack(expand=True, fill="both", padx=10, pady=10)

        # Frame para widgets a la izquierda
        frame_izquierda = ttk.Frame(frame_principal)
        frame_izquierda.pack(side="left", padx=10, pady=10)

        tk.Label(frame_izquierda, text="Tipo:").pack(side="top", padx=10, pady=10)
        ttk.Combobox(frame_izquierda, textvariable=self.tipo_var, values=["Ingreso", "Gasto"]).pack(side="top", padx=10, pady=10)

        tk.Label(frame_izquierda, text="Descripción:").pack(side="top", padx=10, pady=10)
        tk.Entry(frame_izquierda, textvariable=self.descripcion_var).pack(side="top", padx=10, pady=10)

        tk.Label(frame_izquierda, text="Dinero:").pack(side="top", padx=10, pady=10)
        tk.Entry(frame_izquierda, textvariable=self.dinero_var).pack(side="top", padx=10, pady=10)

        tk.Label(frame_izquierda, text="Fecha:").pack(side="top", padx=10, pady=10)
        DateEntry(frame_izquierda, textvariable=self.fecha_var, date_pattern='yyyy-mm-dd').pack(side="top", padx=10, pady=10)

        ttk.Button(frame_izquierda, text="Agregar Transacción", command=self.agregar_transaccion).pack(side="top", padx=10, pady=10)
        ttk.Button(frame_izquierda, text="Eliminar Seleccionado", command=self.eliminar_seleccionado).pack(side="top", padx=10, pady=10)

        # Lista para mostrar historial de transacciones a la derecha
        self.tree = ttk.Treeview(frame_principal, columns=("ID", "Tipo", "Descripción", "Dinero", "Fecha"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.heading("Dinero", text="Dinero")  
        self.tree.heading("Fecha", text="Fecha")
        self.tree.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Etiqueta para mostrar el balance total
        self.balance_total_label = tk.Label(frame_principal, text="")
        self.balance_total_label.pack(side="top", padx=10, pady=10)  # Mover la etiqueta de balance total a la parte superior

        # Etiqueta para mostrar el balance del mes
        self.balance_mes_label = tk.Label(frame_principal, text="")
        self.balance_mes_label.pack(side="top", padx=10, pady=10)  # Mover la etiqueta de balance del mes a la parte superior

        # Botones para filtrar por mes y borrar filtros
        tk.Label(frame_principal, text="Mes:").pack(side="top", padx=10, pady=10)
        self.meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.mes_var = tk.StringVar(value=self.meses[0])
        ttk.Combobox(frame_principal, textvariable=self.mes_var, values=self.meses).pack(side="top", padx=10, pady=10)
        ttk.Button(frame_principal, text="Filtrar por Mes", command=self.filtrar_por_mes).pack(side="top", padx=10, pady=10)
        ttk.Button(frame_principal, text="Borrar Filtros", command=self.borrar_filtros).pack(side="top", padx=10, pady=10)

        # Cargar historial de transacciones al iniciar la aplicación
        self.cargar_historial()

        # Añadir un evento para redimensionar
        root.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        # Redimensionar la lista de transacciones al cambiar el tamaño de la ventana
        self.tree.column("#0", width=event.width - 20)  # Ajustar ancho de la primera columna

    def agregar_transaccion(self):
        tipo = self.tipo_var.get()
        descripcion = self.descripcion_var.get()
        dinero = self.dinero_var.get()
        fecha = self.fecha_var.get()

        if tipo and descripcion and dinero and fecha:
            self.cursor.execute('''
                INSERT INTO transacciones (tipo, descripcion, dinero, fecha)
                VALUES (?, ?, ?, ?)
            ''', (tipo, descripcion, dinero, fecha))
            self.conn.commit()

            # Limpiar las entradas después de agregar una transacción
            self.tipo_var.set("Ingreso")
            self.descripcion_var.set("")
            self.dinero_var.set("")
            self.fecha_var.set("")

            # Actualizar la lista de transacciones y el balance
            self.cargar_historial()

    def cargar_historial(self):
        # Limpiar la lista antes de cargar datos nuevos
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Consultar las transacciones y cargar en la lista
        self.cursor.execute('SELECT * FROM transacciones ORDER BY id DESC')
        transacciones = self.cursor.fetchall()

        for transaccion in transacciones:
            self.tree.insert("", "end", values=transaccion)

        # Actualizar el balance total después de cargar el historial
        self.actualizar_balance_total()

    def eliminar_seleccionado(self):
        selected_item = self.tree.selection()
        if selected_item:
            # Obtener el ID de la transacción seleccionada
            transaccion_id = self.tree.item(selected_item, 'values')[0]
            # Eliminar la transacción de la base de datos
            self.cursor.execute('DELETE FROM transacciones WHERE id = ?', (transaccion_id,))
            self.conn.commit()
            # Actualizar la lista de transacciones y el balance
            self.cargar_historial()

    def actualizar_balance_total(self):
        # Calcular el balance total
        self.cursor.execute('SELECT SUM(CASE WHEN tipo="Ingreso" THEN dinero ELSE -dinero END) AS balance FROM transacciones')
        balance_total = self.cursor.fetchone()[0] or 0.0

        # Mostrar el balance total en la etiqueta correspondiente
        self.balance_total_label.config(text=f"Balance Total: {balance_total:.2f}€")

        # Actualizar el balance del mes después de cargar el historial
        self.actualizar_balance_mes()

    def actualizar_balance_mes(self):
        # Obtener el mes seleccionado
        mes_seleccionado = self.mes_var.get()

        if mes_seleccionado:
            # Obtener el número del mes seleccionado
            numero_mes = self.meses.index(mes_seleccionado) + 1
            numero_mes = str(numero_mes).zfill(2)  # Rellenar con ceros a la izquierda si es necesario

            # Calcular el balance del mes
            self.cursor.execute('SELECT SUM(CASE WHEN tipo="Ingreso" THEN dinero ELSE -dinero END) AS balance_mes FROM transacciones WHERE strftime("%m", fecha) = ?', (str(numero_mes),))
            balance_mes = self.cursor.fetchone()[0] or 0.0

            # Mostrar el balance del mes en la etiqueta correspondiente
            self.balance_mes_label.config(text=f"Balance del Mes ({mes_seleccionado}): {balance_mes:.2f}€")
 
    def filtrar_por_mes(self):
        mes_seleccionado = self.mes_var.get()
        if mes_seleccionado:
            # Obtener el número del mes seleccionado
            numero_mes = self.meses.index(mes_seleccionado) + 1
            numero_mes = str(numero_mes).zfill(2)  # Rellenar con ceros a la izquierda si es necesario
            # Filtrar las transacciones por mes
            self.cursor.execute('SELECT * FROM transacciones WHERE strftime("%m", fecha) = ? ORDER BY id DESC', (str(numero_mes),))
            transacciones = self.cursor.fetchall()

            # Limpiar la lista antes de cargar datos nuevos
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Cargar las transacciones filtradas en la lista
            for transaccion in transacciones:
                self.tree.insert("", "end", values=transaccion)

            # Actualizar el balance del mes después de cargar el historial filtrado
            self.actualizar_balance_mes()

        # Actualizar el balance total después de cargar el historial filtrado
        self.actualizar_balance_total()

    def borrar_filtros(self):
        # Limpiar la lista antes de cargar todos los datos
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Cargar todas las transacciones
        self.cargar_historial()

if __name__ == "__main__":
    root = ThemedTk(theme="scidblue") 
    app = GestionDineroApp(root)

    root.mainloop()
