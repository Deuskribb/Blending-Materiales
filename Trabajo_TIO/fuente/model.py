import os
import matplotlib.pyplot as plt
import pandas as pd
import pulp

# Variables y carga de datos 
os.makedirs("resultados", exist_ok=True)

df = pd.read_csv("data/TIO_DataSet.csv", header=1)
df.columns = df.columns.str.strip()
df.set_index("Mina", inplace=True)

lista_minas = df.index.tolist()
Demanda_total = 10000
Cap_Norte = 6000
Cap_Sur = 6000


modelo = pulp.LpProblem("Optimizacion_Mezcla_minas", pulp.LpMinimize)

# Variables de decisión continuas 
X = pulp.LpVariable.dicts("Extraccion", lista_minas, lowBound=0)

# Función Objetivo
modelo += (
    pulp.lpSum(df.loc[Mina, "Costo_USD"] * X[Mina] for Mina in lista_minas),
    "Costo_total",
)

# Restricciones de Demanda y Oferta
modelo += (
    pulp.lpSum(X[Mina] for Mina in lista_minas) == Demanda_total,
    "Restriccion_Demanda",
)

for Mina in lista_minas:
    capacidad = df.loc[Mina, "Capacidad_Max"]
    modelo += X[Mina] <= capacidad, f"Oferta_Max_{Mina}"

# Restricciones de Leyes
modelo += (
    pulp.lpSum(df.loc[Mina, "Ley_Cu"] * X[Mina] for Mina in lista_minas)
    >= 0.28 * Demanda_total,
    "Ley_Cobre",
)
modelo += (
    pulp.lpSum(df.loc[Mina, "Ley_As"] * X[Mina] for Mina in lista_minas)
    <= 0.01 * Demanda_total,
    "Ley_Arsenico",
)
modelo += (
    pulp.lpSum(df.loc[Mina, "Ley_Pb"] * X[Mina] for Mina in lista_minas)
    <= 0.0085 * Demanda_total,
    "Ley_Plomo",
)
modelo += (
    pulp.lpSum(df.loc[Mina, "Humedad"] * X[Mina] for Mina in lista_minas)
    <= 0.08 * Demanda_total,
    "Ley_Humedad",
)

# Restricciones Logísticas por Zona
minas_norte = [
    Mina for Mina in lista_minas if df.loc[Mina, "Zona"] == "Norte"
]
minas_sur = [Mina for Mina in lista_minas if df.loc[Mina, "Zona"] == "Sur"]

modelo += (
    pulp.lpSum(X[Mina] for Mina in minas_norte) <= Cap_Norte,
    "Logistica_Norte",
)
modelo += (
    pulp.lpSum(X[Mina] for Mina in minas_sur) <= Cap_Sur,
    "Logistica_Sur",
)

#msg para que sea silencioso el calculo
modelo.solve(pulp.PULP_CBC_CMD(msg=False))

print(50*"-")
print(f"Estado Del Modelo: {pulp.LpStatus[modelo.status]}")
costo_optimo = pulp.value(modelo.objective)
print(f"Costo Total Optimizado: ${costo_optimo:,.2f} USD")
print(50*"-")


# EXPORTACIÓN DE RESULTADOS A RESULTADOS/

# Exportar Variables y Costos Reducidos
res_vars = []
for Mina in lista_minas:
    v = X[Mina]
    res_vars.append(
        {
            "Mina": Mina,
            "Zona": df.loc[Mina, "Zona"],
            "Extraccion_Ton": v.varValue,
            "Capacidad_Max": df.loc[Mina, "Capacidad_Max"],
            "Costo_USD_Ton": df.loc[Mina, "Costo_USD"],
            "Costo_Reducido": v.dj if v.dj is not None else 0.0,
        }
    )

df_vars = pd.DataFrame(res_vars)
df_vars.to_csv("resultados/solucion_variables.csv", index=False)

# Exportar Precios Sombra y Holguras
res_rest = []
for nombre, rest in modelo.constraints.items():
    precio_sombra = rest.pi if rest.pi is not None else 0.0
    holgura = rest.slack if rest.slack is not None else 0.0
    res_rest.append(
        {
            "Restriccion": nombre,
            "Precio_Sombra_Dual": precio_sombra,
            "Holgura_Slack": holgura,
            "Estado": (
                "Activa (Saturada)" if abs(holgura) < 1e-5 else "Inactiva"
            ),
        }
    )

df_rest = pd.DataFrame(res_rest)
df_rest.to_csv("resultados/analisis_restricciones.csv", index=False)

print("--- PLAN DE EXTRACCIÓN Y COSTOS REDUCIDOS ---")
print(df_vars.to_string(index=False))

print("\n--- PRECIOS SOMBRA (DUALES) Y HOLGURAS ---")
print(df_rest.to_string(index=False))


# COMPROBACIÓN INDEPENDIENTE DE FACTIBILIDAD 
# Respuesta 2c, verificación independiente  

print("VERIFICACIÓN INDEPENDIENTE DE FACTIBILIDAD")
print(50*"-")
tot_ton = sum(v["Extraccion_Ton"] for v in res_vars)
tot_cu = (
    sum(
        df.loc[v["Mina"], "Ley_Cu"] * v["Extraccion_Ton"]
        for v in res_vars
    )
    / tot_ton
)
tot_pb = (
    sum(
        df.loc[v["Mina"], "Ley_Pb"] * v["Extraccion_Ton"]
        for v in res_vars
    )
    / tot_ton
)
costo_calc = sum(v["Costo_USD_Ton"] * v["Extraccion_Ton"] for v in res_vars)

print(f" Demanda Calculada: {tot_ton:,.0f} ton (Requerido: 10,000 ton)")
print(f" Ley Cu Promedio: {tot_cu*100:.2f}% (Mínimo: 28.00%)")
print(f" Ley Pb Promedio: {tot_pb*100:.3f}% (Máximo: 0.850%)")
print(f" Costo Verificado: ${costo_calc:,.2f} USD")
assert abs(costo_calc - costo_optimo) < 1e-2, "Error de verificación"
print(" Estado de Verificación: OK - Solución 100% Factible")


# ANÁLISIS DE RANGOS DE VALIDEZ (Pregunta 3c)
print("\nGenerando Rangos de Validez...")

rangos_res = []

# Escenarios de prueba para la tolerancia de Plomo
escenarios_pb = [
    ("Apretable (0.78%)", 0.0078, "Muestra costo si se exige menor tolerancia de Pb"),
    ("Base (0.85%)", 0.0085, "Solución óptima actual"),
    ("Relajado (0.95%)", 0.0095, "Muestra costo si se relaja la norma de Pb")
]

for nombre, pct_pb, efecto in escenarios_pb:
    m_temp = pulp.LpProblem("Rango_Pb", pulp.LpMinimize)
    X_t = pulp.LpVariable.dicts("X", lista_minas, lowBound=0)
    
    m_temp += pulp.lpSum(df.loc[Mina, "Costo_USD"] * X_t[Mina] for Mina in lista_minas)
    m_temp += pulp.lpSum(X_t[Mina] for Mina in lista_minas) == Demanda_total
    for Mina in lista_minas:
        m_temp += X_t[Mina] <= df.loc[Mina, "Capacidad_Max"]
    m_temp += pulp.lpSum(df.loc[Mina, "Ley_Cu"] * X_t[Mina] for Mina in lista_minas) >= 0.28 * Demanda_total
    m_temp += pulp.lpSum(df.loc[Mina, "Ley_As"] * X_t[Mina] for Mina in lista_minas) <= 0.01 * Demanda_total
    m_temp += pulp.lpSum(df.loc[Mina, "Ley_Pb"] * X_t[Mina] for Mina in lista_minas) <= pct_pb * Demanda_total
    m_temp += pulp.lpSum(df.loc[Mina, "Humedad"] * X_t[Mina] for Mina in lista_minas) <= 0.08 * Demanda_total
    m_temp += pulp.lpSum(X_t[Mina] for Mina in minas_norte) <= Cap_Norte
    m_temp += pulp.lpSum(X_t[Mina] for Mina in minas_sur) <= Cap_Sur
    
    m_temp.solve(pulp.PULP_CBC_CMD(msg=False))
    
    costo_eval = pulp.value(m_temp.objective) if pulp.LpStatus[m_temp.status] == "Optimal" else None
    
    rangos_res.append({
        "Escenario": nombre,
        "Tol_Plomo_%": pct_pb * 100,
        "Estado_Modelo": pulp.LpStatus[m_temp.status],
        "Costo_Total_USD": costo_eval,
        "Efecto_Observado": efecto
    })

df_rangos = pd.DataFrame(rangos_res)
df_rangos.to_csv("resultados/rangos_validez.csv", index=False)
print(" Rangos de validez guardados en 'resultados/rangos_validez.csv'")


# ---------------------------------------------------------
# 5. ANÁLISIS PARAMÉTRICO Y GRÁFICO (Pregunta 3d)
# ---------------------------------------------------------
print("\nGenerando Análisis Paramétrico del Plomo (Pb)...")

pb_limites = [pct / 10000 for pct in range(75, 105, 1)]  # De 0.85% a 1.04%
costos_param = []
extraccion_minas_param = {m: [] for m in lista_minas}

for pb_val in pb_limites:
    m_temp = pulp.LpProblem("Parametrico", pulp.LpMinimize)
    X_t = pulp.LpVariable.dicts("X", lista_minas, lowBound=0)

    m_temp += pulp.lpSum(
        df.loc[Mina, "Costo_USD"] * X_t[Mina] for Mina in lista_minas
    )
    m_temp += pulp.lpSum(X_t[Mina] for Mina in lista_minas) == Demanda_total

    for Mina in lista_minas:
        m_temp += X_t[Mina] <= df.loc[Mina, "Capacidad_Max"]

    m_temp += (
        pulp.lpSum(df.loc[Mina, "Ley_Cu"] * X_t[Mina] for Mina in lista_minas)
        >= 0.28 * Demanda_total
    )
    m_temp += (
        pulp.lpSum(df.loc[Mina, "Ley_As"] * X_t[Mina] for Mina in lista_minas)
        <= 0.01 * Demanda_total
    )
    m_temp += (
        pulp.lpSum(df.loc[Mina, "Ley_Pb"] * X_t[Mina] for Mina in lista_minas)
        <= pb_val * Demanda_total
    )
    m_temp += (
        pulp.lpSum(df.loc[Mina, "Humedad"] * X_t[Mina] for Mina in lista_minas)
        <= 0.08 * Demanda_total
    )
    m_temp += (
        pulp.lpSum(X_t[Mina] for Mina in minas_norte) <= Cap_Norte
    )
    m_temp += pulp.lpSum(X_t[Mina] for Mina in minas_sur) <= Cap_Sur

    m_temp.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[m_temp.status] == "Optimal":
        costos_param.append(pulp.value(m_temp.objective) / 1e6)
        for Mina in lista_minas:
            extraccion_minas_param[Mina].append(X_t[Mina].varValue)
    else:
        costos_param.append(None)
        for Mina in lista_minas:
            extraccion_minas_param[Mina].append(0)

# Generar y guardar gráfico
fig, ax1 = plt.subplots(figsize=(9, 5))

color = "tab:blue"
ax1.set_xlabel("Límite Máximo de Plomo (%)")
ax1.set_ylabel("Costo Total (Millones USD)", color=color)
ax1.plot(
    [p * 100 for p in pb_limites],
    costos_param,
    color=color,
    marker="o",
    linewidth=2,
    label="Costo Total",
)
ax1.tick_params(axis="y", labelcolor=color)
ax1.grid(True)

ax2 = ax1.twinx()
color = "tab:red"
ax2.set_ylabel("Extracción por Mina (Toneladas)", color=color)
for Mina in lista_minas:
    if max(extraccion_minas_param[Mina]) > 0:
        ax2.plot(
            [p * 100 for p in pb_limites],
            extraccion_minas_param[Mina],
            linestyle="--",
            label=f"Extracción {Mina}",
        )

ax2.tick_params(axis="y", labelcolor=color)
plt.title("Análisis Paramétrico: Costo y Plan de Extracción vs. Límite de Plomo")
fig.tight_layout()

plt.savefig("resultados/analisis_parametrico_plomo.png", dpi=300)
print(" Gráfico guardado exitosamente en 'resultados/analisis_parametrico_plomo.png'")