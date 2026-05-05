import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# PARÁMETROS DEFAULT 
# Sector (distribución discreta empirica)
PROB_CERCANO  = 0.35   # 1-2 cuadras
PROB_INTERMEDIO = 0.40 # 2-3 cuadras
PROB_LEJANO   = 0.25   # 3-5 cuadras

# Parada en cartel (distribución Bernoulli)
PROB_PARADA_CARTEL = 0.45

# Parada cartel: demora Normal(media=60s, desvio=20s)
MEDIA_CARTEL_SEG  = 60.0
DESVIO_CARTEL_SEG = 20.0

# Bloqueo de cuadra (sólo sectores cercano y lejano)
PROB_BLOQUEO = 0.40
FACTOR_BLOQUEO = 1.80  # +80%

# Tiempo por cuadra: Uniforme(30, 45) segundos
T_CUADRA_MIN = 30.0
T_CUADRA_MAX = 45.0

# Parada extra: 60/250 jornadas → probabilidad
PROB_PARADA_EXTRA = 60 / 250
# Demora extra: Exponencial(media=80s)
MEDIA_EXTRA_SEG = 80.0


def sector_cuadras(rnd):
    """Devuelve (nombre_sector, cuadras_min, cuadras_max) según rnd uniforme."""
    acum_cercano    = PROB_CERCANO
    acum_intermedio = PROB_CERCANO + PROB_INTERMEDIO
    if rnd < acum_cercano:
        return "Cercano", 1, 2
    elif rnd < acum_intermedio:
        return "Intermedio", 2, 3
    else:
        return "Lejano", 3, 5


def simular(n_dias,
            prob_cercano, prob_intermedio, prob_lejano,
            prob_cartel, media_cartel, desvio_cartel,
            prob_bloqueo, factor_bloqueo,
            t_cuadra_min, t_cuadra_max,
            prob_extra, media_extra,
            fila_inicio):
    """
    Ejecuta la simulación de N días en memoria con 2 filas.
    Devuelve:
    - vector_estado : lista de dicts con las filas [fila_inicio .. fila_inicio+200] y fila N
    - estadísticas  : dict con los KPIs pedidos
    """
    # Acumuladores globales
    tiempo_total_acum   = 0.0
    tiempo_max          = -np.inf
    tiempo_min          =  np.inf
    cnt_cartel_y_extra  = 0   # KPI 2: paró cartel Y hubo extra
    cnt_sin_cartel_sin_extra = 0  # KPI 3: sin cartel Y sin extra
    # Variables propias (extra)
    cnt_bloqueo         = 0   # Cuántas veces hubo bloqueo
    cnt_cercano         = 0   # Cuántas veces fue a sector cercano
    cnt_intermedio      = 0   # Cuántas veces fue a sector intermedio
    cnt_lejano          = 0   # Cuántas veces fue a sector lejano
    tiempo_sector       = {"Cercano": 0.0, "Intermedio": 0.0, "Lejano": 0.0}

    # Acumulados del vector de estado
    tiempo_acum_parcial = 0.0

    vector_estado = []
    fila_fin_rango = fila_inicio + 200

    fila_prev = None  # "fila anterior" en memoria (2 filas)

    for i in range(1, n_dias + 1):
        # ── RNDs y variables de la fila ──
        rnd_sector  = np.random.rand()
        rnd_cartel  = np.random.rand()
        rnd_bloqueo = np.random.rand()
        rnd_extra   = np.random.rand()

        # 1. Sector
        nombre_sector, c_min, c_max = sector_cuadras_local(
            rnd_sector, prob_cercano, prob_intermedio, prob_lejano)
        n_cuadras = np.random.randint(c_min, c_max + 1)  # cuadras reales recorridas

        # 2. Tiempo de circulación cuadra a cuadra
        t_circulacion = 0.0
        hubo_bloqueo_fila = False
        aplica_bloqueo = nombre_sector in ("Cercano", "Lejano")
        for _ in range(n_cuadras):
            t_cuadra = np.random.uniform(t_cuadra_min, t_cuadra_max)
            if aplica_bloqueo and rnd_bloqueo < prob_bloqueo:
                t_cuadra *= factor_bloqueo
                hubo_bloqueo_fila = True
            t_circulacion += t_cuadra

        # 3. Parada cartel
        parada_cartel = rnd_cartel < prob_cartel
        if parada_cartel:
            t_cartel = max(0.0, np.random.normal(media_cartel, desvio_cartel))
        else:
            t_cartel = 0.0

        # 4. Parada extra
        parada_extra = rnd_extra < prob_extra
        if parada_extra:
            t_extra = np.random.exponential(media_extra)
        else:
            t_extra = 0.0

        # 5. Tiempo total de la jornada
        t_total = t_circulacion + t_cartel + t_extra

        # ── Acumuladores ──
        tiempo_total_acum  += t_total
        tiempo_acum_parcial += t_total
        if t_total > tiempo_max:
            tiempo_max = t_total
        if t_total < tiempo_min:
            tiempo_min = t_total

        if parada_cartel and parada_extra:
            cnt_cartel_y_extra += 1
        if (not parada_cartel) and (not parada_extra):
            cnt_sin_cartel_sin_extra += 1
        if hubo_bloqueo_fila:
            cnt_bloqueo += 1

        if nombre_sector == "Cercano":
            cnt_cercano += 1
            tiempo_sector["Cercano"] += t_total
        elif nombre_sector == "Intermedio":
            cnt_intermedio += 1
            tiempo_sector["Intermedio"] += t_total
        else:
            cnt_lejano += 1
            tiempo_sector["Lejano"] += t_total

        # Construir fila (sólo si está en el rango de visualización o es la última)
        en_rango = fila_inicio <= i <= fila_fin_rango
        es_ultima = i == n_dias

        if en_rango or es_ultima:
            fila = {
                "Jornada":          i,
                "RND_Sector":       round(rnd_sector, 4),
                "Sector":           nombre_sector,
                "Cuadras":          n_cuadras,
                "RND_Bloqueo":      round(rnd_bloqueo, 4),
                "Bloqueo":          "Sí" if hubo_bloqueo_fila else "No",
                "T_Circulacion(s)": round(t_circulacion, 2),
                "RND_Cartel":       round(rnd_cartel, 4),
                "Parada_Cartel":    "Sí" if parada_cartel else "No",
                "T_Cartel(s)":      round(t_cartel, 2),
                "RND_Extra":        round(rnd_extra, 4),
                "Parada_Extra":     "Sí" if parada_extra else "No",
                "T_Extra(s)":       round(t_extra, 2),
                "T_Total(s)":       round(t_total, 2),
                "T_Acum(s)":        round(tiempo_acum_parcial, 2),
                "T_Prom_Acum(s)":   round(tiempo_acum_parcial / i, 2),
            }
            vector_estado.append((i, fila))

        fila_prev = {
            "i": i,
            "t_total": t_total,
            "sector": nombre_sector,
        }


    # KPIs
    estadisticas = {
        "t_promedio":             round(tiempo_total_acum / n_dias, 2),
        "pct_cartel_y_extra":     round(cnt_cartel_y_extra / n_dias * 100, 2),
        "cnt_sin_cartel_sin_extra": cnt_sin_cartel_sin_extra,
        "tiempo_max":             round(tiempo_max, 2),
        "tiempo_min":             round(tiempo_min, 2),
        # Extras propios
        "pct_bloqueo":            round(cnt_bloqueo / n_dias * 100, 2),
        "t_prom_cercano":         round(tiempo_sector["Cercano"] / cnt_cercano, 2) if cnt_cercano else 0,
        "t_prom_lejano":          round(tiempo_sector["Lejano"]  / cnt_lejano,  2) if cnt_lejano  else 0,
        "pct_sector_cercano":     round(cnt_cercano    / n_dias * 100, 2),
        "pct_sector_intermedio":  round(cnt_intermedio / n_dias * 100, 2),
        "pct_sector_lejano":      round(cnt_lejano     / n_dias * 100, 2),
    }

    # Separar filas del rango y la última
    filas_rango = [f for (idx, f) in vector_estado if fila_inicio <= idx <= fila_fin_rango]
    ultima_fila = [f for (idx, f) in vector_estado if idx == n_dias]

    return filas_rango, ultima_fila[0] if ultima_fila else None, estadisticas


def sector_cuadras_local(rnd, p_cercano, p_intermedio, p_lejano):
    acum1 = p_cercano
    acum2 = p_cercano + p_intermedio
    if rnd < acum1:
        return "Cercano", 1, 2
    elif rnd < acum2:
        return "Intermedio", 2, 3
    else:
        return "Lejano", 3, 5


#  INTERFAZ GRÁFICA
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TP3 – Simulación Parqueando (Montecarlo)")
        self.root.geometry("1280x780")
        self.root.resizable(True, True)

        # Variables de parámetros
        self.n_dias_var       = tk.IntVar(value=1000)
        self.semilla_var      = tk.IntVar(value=42)
        self.fila_inicio_var  = tk.IntVar(value=1)

        self.prob_cercano_var    = tk.DoubleVar(value=PROB_CERCANO)
        self.prob_intermedio_var = tk.DoubleVar(value=PROB_INTERMEDIO)
        self.prob_lejano_var     = tk.DoubleVar(value=PROB_LEJANO)

        self.prob_cartel_var     = tk.DoubleVar(value=PROB_PARADA_CARTEL)
        self.media_cartel_var    = tk.DoubleVar(value=MEDIA_CARTEL_SEG)
        self.desvio_cartel_var   = tk.DoubleVar(value=DESVIO_CARTEL_SEG)

        self.prob_bloqueo_var    = tk.DoubleVar(value=PROB_BLOQUEO)
        self.factor_bloqueo_var  = tk.DoubleVar(value=FACTOR_BLOQUEO)

        self.t_cuadra_min_var    = tk.DoubleVar(value=T_CUADRA_MIN)
        self.t_cuadra_max_var    = tk.DoubleVar(value=T_CUADRA_MAX)

        self.prob_extra_var      = tk.DoubleVar(value=round(PROB_PARADA_EXTRA, 4))
        self.media_extra_var     = tk.DoubleVar(value=MEDIA_EXTRA_SEG)

        # Variables de resultados
        self.t_prom_var          = tk.StringVar(value="–")
        self.pct_cartel_extra_var= tk.StringVar(value="–")
        self.cnt_sin_var         = tk.StringVar(value="–")
        self.t_max_var           = tk.StringVar(value="–")
        self.t_min_var           = tk.StringVar(value="–")
        self.pct_bloqueo_var     = tk.StringVar(value="–")
        self.t_prom_cercano_var  = tk.StringVar(value="–")
        self.t_prom_lejano_var   = tk.StringVar(value="–")
        self.pct_sec_cercano_var = tk.StringVar(value="–")
        self.pct_sec_inter_var   = tk.StringVar(value="–")
        self.pct_sec_lejano_var  = tk.StringVar(value="–")

        self.df_resultado = None

        # Notebook principal
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.nb = nb

        self.tab_config    = ttk.Frame(nb)
        self.tab_tabla     = ttk.Frame(nb)
        self.tab_kpi       = ttk.Frame(nb)
        self.tab_graficos  = ttk.Frame(nb)

        nb.add(self.tab_config,   text="⚙ Configuración")
        nb.add(self.tab_tabla,    text="📋 Tabla de Simulación")
        nb.add(self.tab_kpi,      text="📊 Resultados / KPIs")
        nb.add(self.tab_graficos, text="📈 Gráficos")

        self._build_config_tab()
        self._build_tabla_tab()
        self._build_kpi_tab()
        self._build_graficos_tab()


    # TAB CONFIGURACIÓN 
    def _build_config_tab(self):
        tab = self.tab_config

        # Parámetros generales
        gen = ttk.LabelFrame(tab, text="Parámetros Generales")
        gen.pack(fill="x", padx=10, pady=6)

        params_gen = [
            ("N (jornadas a simular):",       self.n_dias_var),
            ("Semilla aleatoria:",             self.semilla_var),
            ("Fila de inicio visualización:", self.fila_inicio_var),
        ]
        for r, (lbl, var) in enumerate(params_gen):
            ttk.Label(gen, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=3)
            ttk.Entry(gen, textvariable=var, width=12).grid(row=r, column=1, padx=6, pady=3)

        # Sectores
        sec = ttk.LabelFrame(tab, text="Probabilidades de Sector  (deben sumar 1.0)")
        sec.pack(fill="x", padx=10, pady=6)
        params_sec = [
            ("P(Sector Cercano  1-2 cuadras):",    self.prob_cercano_var),
            ("P(Sector Intermedio 2-3 cuadras):",  self.prob_intermedio_var),
            ("P(Sector Lejano  3-5 cuadras):",     self.prob_lejano_var),
        ]
        for r, (lbl, var) in enumerate(params_sec):
            ttk.Label(sec, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=3)
            ttk.Entry(sec, textvariable=var, width=12).grid(row=r, column=1, padx=6, pady=3)

        # Cartel
        car = ttk.LabelFrame(tab, text="Parada en Cartel Informativo  [Normal]")
        car.pack(fill="x", padx=10, pady=6)
        params_car = [
            ("P(Parada en cartel):",           self.prob_cartel_var),
            ("Media demora cartel (seg):",      self.media_cartel_var),
            ("Desviación demora cartel (seg):", self.desvio_cartel_var),
        ]
        for r, (lbl, var) in enumerate(params_car):
            ttk.Label(car, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=3)
            ttk.Entry(car, textvariable=var, width=12).grid(row=r, column=1, padx=6, pady=3)

        # Bloqueo + Circulación
        blq = ttk.LabelFrame(tab, text="Bloqueo de Cuadra y Circulación  [Uniforme]")
        blq.pack(fill="x", padx=10, pady=6)
        params_blq = [
            ("P(Bloqueo) – solo Cercano/Lejano:", self.prob_bloqueo_var),
            ("Factor de aumento por bloqueo:",     self.factor_bloqueo_var),
            ("T_cuadra mínimo (seg):",              self.t_cuadra_min_var),
            ("T_cuadra máximo (seg):",              self.t_cuadra_max_var),
        ]
        for r, (lbl, var) in enumerate(params_blq):
            ttk.Label(blq, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=3)
            ttk.Entry(blq, textvariable=var, width=12).grid(row=r, column=1, padx=6, pady=3)

        # Parada extra
        ext = ttk.LabelFrame(tab, text="Parada Extra en Pago/Validación  [Exponencial]")
        ext.pack(fill="x", padx=10, pady=6)
        params_ext = [
            ("P(Parada extra) – e.g. 60/250 = 0.24:", self.prob_extra_var),
            ("Media demora extra (seg):",               self.media_extra_var),
        ]
        for r, (lbl, var) in enumerate(params_ext):
            ttk.Label(ext, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=3)
            ttk.Entry(ext, textvariable=var, width=12).grid(row=r, column=1, padx=6, pady=3)

        # Botones
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="▶  Ejecutar Simulación",
                command=self.ejecutar).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="↺  Restablecer Defaults",
                command=self.restablecer).pack(side="left", padx=6)


    # TAB TABLA 
    def _build_tabla_tab(self):
        tab = self.tab_tabla
        frame = ttk.Frame(tab)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(frame)
        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")

        self.tree.tag_configure("ultima", background="#fffacd")
        self.tree.tag_configure("sep",    background="#d0d0d0")

    def _cargar_tabla(self, filas_rango, ultima_fila):
        tree = self.tree
        for item in tree.get_children():
            tree.delete(item)

        if not filas_rango and ultima_fila is None:
            return

        cols = list(filas_rango[0].keys()) if filas_rango else list(ultima_fila.keys())
        tree["columns"] = cols
        tree["show"] = "headings"
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110, anchor="center")

        for fila in filas_rango:
            tree.insert("", "end", values=list(fila.values()))

        if ultima_fila and (not filas_rango or filas_rango[-1]["Jornada"] != ultima_fila["Jornada"]):
            tree.insert("", "end", values=["..."] * len(cols), tags=("sep",))
            tree.insert("", "end", values=list(ultima_fila.values()), tags=("ultima",))


    # TAB KPIs 
    def _build_kpi_tab(self):
        tab = self.tab_kpi

        requeridos = ttk.LabelFrame(tab, text="KPIs Requeridos por la Consigna")
        requeridos.pack(fill="x", padx=10, pady=8)

        kpis_req = [
            ("1. Tiempo promedio de estacionamiento (seg):", self.t_prom_var),
            ("2. % Jornadas con parada cartel Y parada extra:", self.pct_cartel_extra_var),
            ("3. Jornadas SIN parada cartel NI parada extra:", self.cnt_sin_var),
            ("4. Tiempo MÁXIMO de estacionamiento (seg):", self.t_max_var),
            ("5. Tiempo MÍNIMO de estacionamiento (seg):", self.t_min_var),
        ]
        for r, (lbl, var) in enumerate(kpis_req):
            ttk.Label(requeridos, text=lbl, width=50, anchor="w").grid(
                row=r, column=0, sticky="w", padx=8, pady=4)
            ttk.Label(requeridos, textvariable=var, font=("", 10, "bold"),
                    foreground="#005580").grid(row=r, column=1, padx=8, pady=4, sticky="w")

        extras = ttk.LabelFrame(tab, text="KPIs Adicionales (propuestos por el grupo)")
        extras.pack(fill="x", padx=10, pady=8)

        kpis_ext = [
            ("6. % Jornadas con bloqueo de cuadra:", self.pct_bloqueo_var),
            ("7. Tiempo promedio sector Cercano (seg):", self.t_prom_cercano_var),
            ("8. Tiempo promedio sector Lejano (seg):", self.t_prom_lejano_var),
            ("   % Jornadas en sector Cercano:", self.pct_sec_cercano_var),
            ("   % Jornadas en sector Intermedio:", self.pct_sec_inter_var),
            ("   % Jornadas en sector Lejano:", self.pct_sec_lejano_var),
        ]
        for r, (lbl, var) in enumerate(kpis_ext):
            ttk.Label(extras, text=lbl, width=50, anchor="w").grid(
                row=r, column=0, sticky="w", padx=8, pady=4)
            ttk.Label(extras, textvariable=var, font=("", 10, "bold"),
                    foreground="#005500").grid(row=r, column=1, padx=8, pady=4, sticky="w")


    # TAB GRÁFICOS 
    def _build_graficos_tab(self):
        tab = self.tab_graficos
        self.fig, self.axs = plt.subplots(1, 3, figsize=(14, 5))
        self.canvas_graf = FigureCanvasTkAgg(self.fig, master=tab)
        self.canvas_graf.get_tk_widget().pack(fill="both", expand=True)
        self.fig.tight_layout(pad=3)

    def _actualizar_graficos(self, estadisticas):
        for ax in self.axs:
            ax.clear()

        # Gráfico 1: distribución de sectores
        sectores = ["Cercano", "Intermedio", "Lejano"]
        pcts = [estadisticas["pct_sector_cercano"],
                estadisticas["pct_sector_intermedio"],
                estadisticas["pct_sector_lejano"]]
        self.axs[0].bar(sectores, pcts, color=["#4c9be8", "#f0a500", "#e85454"])
        self.axs[0].set_title("Distribución de Sectores (%)")
        self.axs[0].set_ylabel("%")
        self.axs[0].set_ylim(0, 60)
        for i, v in enumerate(pcts):
            self.axs[0].text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9)

        # Gráfico 2: descomposición del tiempo (pastel)
        df = self.df_resultado
        if df is not None:
            labels2 = ["Circulación", "Cartel", "Extra"]
            vals2 = [
                df["T_Circulacion(s)"].mean(),
                df["T_Cartel(s)"].mean(),
                df["T_Extra(s)"].mean(),
            ]
            self.axs[1].pie(vals2, labels=labels2, autopct="%1.1f%%",
                            colors=["#4c9be8", "#f0a500", "#e85454"],
                            startangle=90)
            self.axs[1].set_title("Composición Promedio del Tiempo Total")

        # Gráfico 3: % eventos clave
        eventos = ["Parada\nCartel", "Parada\nExtra", "Bloqueo\nCuadra",
                "Cartel\n+ Extra"]
        vals3 = [
            self.prob_cartel_var.get() * 100,
            self.prob_extra_var.get() * 100,
            estadisticas["pct_bloqueo"],
            estadisticas["pct_cartel_y_extra"],
        ]
        self.axs[2].bar(eventos, vals3, color=["#4c9be8", "#f0a500", "#e85454", "#9b4ce8"])
        self.axs[2].set_title("% de Ocurrencia de Eventos")
        self.axs[2].set_ylabel("%")
        for i, v in enumerate(vals3):
            self.axs[2].text(i, v + 0.3, f"{v:.1f}%", ha="center", fontsize=8)

        self.fig.tight_layout(pad=3)
        self.canvas_graf.draw()


    # LÓGICA DE EJECUCIÓN 
    def ejecutar(self):
        n      = self.n_dias_var.get()
        semilla = self.semilla_var.get()
        fila_i  = self.fila_inicio_var.get()

        # Validaciones básicas
        p_c = self.prob_cercano_var.get()
        p_i = self.prob_intermedio_var.get()
        p_l = self.prob_lejano_var.get()
        if abs(p_c + p_i + p_l - 1.0) > 0.001:
            messagebox.showwarning("Error", "Las probabilidades de sector deben sumar 1.0")
            return
        if fila_i < 1 or fila_i > n:
            messagebox.showwarning("Error", f"Fila de inicio debe estar entre 1 y {n}")
            return
        if n < 1:
            messagebox.showwarning("Error", "N debe ser al menos 1")
            return

        np.random.seed(semilla)

        filas_rango, ultima_fila, stats = simular(
            n_dias          = n,
            prob_cercano    = p_c,
            prob_intermedio = p_i,
            prob_lejano     = p_l,
            prob_cartel     = self.prob_cartel_var.get(),
            media_cartel    = self.media_cartel_var.get(),
            desvio_cartel   = self.desvio_cartel_var.get(),
            prob_bloqueo    = self.prob_bloqueo_var.get(),
            factor_bloqueo  = self.factor_bloqueo_var.get(),
            t_cuadra_min    = self.t_cuadra_min_var.get(),
            t_cuadra_max    = self.t_cuadra_max_var.get(),
            prob_extra      = self.prob_extra_var.get(),
            media_extra     = self.media_extra_var.get(),
            fila_inicio     = fila_i,
        )

        # Guardar para gráficos
        if filas_rango:
            self.df_resultado = pd.DataFrame(filas_rango)
        elif ultima_fila:
            self.df_resultado = pd.DataFrame([ultima_fila])

        # Cargar tabla
        self._cargar_tabla(filas_rango, ultima_fila)

        # Actualizar KPIs
        self.t_prom_var.set(f"{stats['t_promedio']} seg  ({stats['t_promedio']/60:.2f} min)")
        self.pct_cartel_extra_var.set(f"{stats['pct_cartel_y_extra']} %")
        self.cnt_sin_var.set(f"{stats['cnt_sin_cartel_sin_extra']} jornadas")
        self.t_max_var.set(f"{stats['tiempo_max']} seg  ({stats['tiempo_max']/60:.2f} min)")
        self.t_min_var.set(f"{stats['tiempo_min']} seg  ({stats['tiempo_min']/60:.2f} min)")
        self.pct_bloqueo_var.set(f"{stats['pct_bloqueo']} %")
        self.t_prom_cercano_var.set(f"{stats['t_prom_cercano']} seg")
        self.t_prom_lejano_var.set(f"{stats['t_prom_lejano']} seg")
        self.pct_sec_cercano_var.set(f"{stats['pct_sector_cercano']} %")
        self.pct_sec_inter_var.set(f"{stats['pct_sector_intermedio']} %")
        self.pct_sec_lejano_var.set(f"{stats['pct_sector_lejano']} %")

        # Gráficos
        self._actualizar_graficos(stats)

        # Ir a la tabla
        self.nb.select(self.tab_tabla)
        messagebox.showinfo("Simulación completada",
                            f"Se simularon {n:,} jornadas.\n"
                            f"Se muestran jornadas {fila_i} a {min(fila_i+200, n)} "
                            f"y la jornada N = {n}.")

    def restablecer(self):
        self.n_dias_var.set(1000)
        self.semilla_var.set(42)
        self.fila_inicio_var.set(1)
        self.prob_cercano_var.set(PROB_CERCANO)
        self.prob_intermedio_var.set(PROB_INTERMEDIO)
        self.prob_lejano_var.set(PROB_LEJANO)
        self.prob_cartel_var.set(PROB_PARADA_CARTEL)
        self.media_cartel_var.set(MEDIA_CARTEL_SEG)
        self.desvio_cartel_var.set(DESVIO_CARTEL_SEG)
        self.prob_bloqueo_var.set(PROB_BLOQUEO)
        self.factor_bloqueo_var.set(FACTOR_BLOQUEO)
        self.t_cuadra_min_var.set(T_CUADRA_MIN)
        self.t_cuadra_max_var.set(T_CUADRA_MAX)
        self.prob_extra_var.set(round(PROB_PARADA_EXTRA, 4))
        self.media_extra_var.set(MEDIA_EXTRA_SEG)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()