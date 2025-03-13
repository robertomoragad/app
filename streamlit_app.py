# file: streamlit_app.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------
# 1) Generar Iniciativa (c‡lculo sinttico)
# -----------------------
def generar_iniciativa(tipo, costo_fijo_cat, costo_var_cat, ingreso_speed, impacto_cat, total_meses=29):
    """
    Genera curvas de costos e ingresos sintticas y su BN Acumulado:
      - tipo: 'clasico' o 'disruptivo'
      - costo_fijo_cat: 'bajo', 'medio', 'alto'
      - costo_var_cat: 'pico1', 'pico2', etc. (simplificado)
      - ingreso_speed: 'rapido', 'medio', 'lento'
      - impacto_cat: 'bajo', 'medio', 'alto'
    Retorna un dict con BN_acum y BN_mensual, etc.
    """
    meses = np.arange(total_meses)
    
    # COSTOS FIJOS: segœn la categor’a
    map_cf = {
        'bajo': 1.0,
        'medio': 2.0,
        'alto': 3.0
    }
    base_cf = map_cf.get(costo_fijo_cat, 2.0)
    
    # Ajuste adicional si el tipo es disruptivo (ej: 10% menos de costo fijo)
    # Puedes cambiar la l—gica que desees
    if tipo == 'disruptivo':
        base_cf *= 0.9
    
    costos_fijos = np.full(total_meses, base_cf*2.0)
    
    # COSTOS VARIABLES: un par de curvas gaussianas sencillas
    def gauss(x, center, amplitude, width=2.0):
        return amplitude * np.exp(-0.5*((x - center)/width)**2)
    
    if costo_var_cat == 'pico1':
        wave = gauss(meses, center=5, amplitude=3.0, width=2.0)
        costos_variables = wave
    else:
        # 'pico2'
        wave1 = gauss(meses, center=4, amplitude=2.5, width=2.0)
        wave2 = gauss(meses, center=12, amplitude=3.5, width=2.0)
        costos_variables = wave1 + wave2
    
    # Ajuste para tipo disruptivo (por ejemplo, 15% menos costos variables)
    if tipo == 'disruptivo':
        costos_variables *= 0.85
    
    # INGRESOS + AHORROS: segun la velocidad (rapido, medio, lento)
    speed_map = {
        'rapido': (6, 14),
        'medio': (10, 20),
        'lento': (12, 24)
    }
    start_i, peak_i = speed_map.get(ingreso_speed, (10, 20))
    
    map_impact = {
        'bajo': 0.8,
        'medio': 1.0,
        'alto': 1.2
    }
    impact_factor = map_impact.get(impacto_cat, 1.0)
    
    # Si es disruptivo, mayor impacto
    if tipo == 'disruptivo':
        impact_factor *= 1.3
    
    ingresos = np.zeros(total_meses)
    peak_val = 12.0 * impact_factor
    
    def p_poly(t):
        return t**2
    
    for i in range(total_meses):
        if i >= start_i:
            t = i - start_i
            if i <= peak_i:
                ingresos[i] = peak_val * (p_poly(t) / p_poly(peak_i - start_i + 1)) 
            else:
                ingresos[i] = peak_val
    
    # BENEFICIO NETO MENSUAL
    bn_mensual = ingresos - (costos_fijos + costos_variables)
    # ACUMULADO
    bn_acum = np.cumsum(bn_mensual)
    
    return {
        'tipo': tipo,
        'costos_fijos': costos_fijos,
        'costos_variables': costos_variables,
        'ingresos': ingresos,
        'bn_mensual': bn_mensual,
        'bn_acum': bn_acum
    }

# ---------------------------------------------------------
# Streamlit App
# ---------------------------------------------------------
def main():
    st.title("Prototipo para Priorizar un Portafolio de Iniciativas (Cl‡sico vs Disruptivo)")
    
    # 1) Par‡metros globales
    st.subheader("Configuraci—n Inicial")
    
    num_iniciativas = st.number_input("Nœmero de iniciativas en Backlog", min_value=1, max_value=100, value=10)
    horizon_mes = st.number_input("Mes para evaluar BNA (ej: 24)", min_value=1, max_value=50, value=24)
    
    # 2) Construir un backlog sinttico
    st.markdown("Generaremos un backlog sinttico segœn tus selecciones para cada iniciativa.")
    df_backlog = []
    
    for i in range(num_iniciativas):
        # Simulamos si es 'clasico' o 'disruptivo'
        tipo_opt = st.selectbox(f"Iniciativa {i+1} - Tipo", ['clasico','disruptivo'], key=f"tipo_{i}")
        cf_opt = st.selectbox(f"Iniciativa {i+1} - Costos Fijos", ['bajo','medio','alto'], key=f"cf_{i}")
        cv_opt = st.selectbox(f"Iniciativa {i+1} - Costos Variables", ['pico1','pico2'], key=f"cv_{i}")
        ing_opt = st.selectbox(f"Iniciativa {i+1} - Ingresos/Ahorros Speed", ['rapido','medio','lento'], key=f"ing_{i}")
        imp_opt = st.selectbox(f"Iniciativa {i+1} - Impacto", ['bajo','medio','alto'], key=f"imp_{i}")
        
        # Generar la iniciativa
        data = generar_iniciativa(tipo_opt, cf_opt, cv_opt, ing_opt, imp_opt, total_meses=29)
        bn24 = data['bn_acum'][horizon_mes] if horizon_mes < 29 else data['bn_acum'][-1]
        
        df_backlog.append({
            'id': i,
            'tipo': tipo_opt,
            'cf': cf_opt,
            'cv': cv_opt,
            'ing': ing_opt,
            'imp': imp_opt,
            'BN_at_mesX': bn24,
            'data': data
        })
    
    # 3) Mostramos backlog
    st.subheader("Backlog Actual (vista simplificada)")
    backlog_table = pd.DataFrame([{
        'ID': p['id'],
        'Tipo': p['tipo'],
        'CF': p['cf'],
        'CV': p['cv'],
        'Ingr-Speed': p['ing'],
        'Impacto': p['imp'],
        f'BNA @ mes{horizon_mes}': round(p['BN_at_mesX'],2)
    } for p in df_backlog])
    st.dataframe(backlog_table)
    
    # 4) Seleccionar cu‡ntos proyectos se van a "ejecutar"
    st.subheader("Selecci—n y Prioridad")
    num_ejecutar = st.slider("Nœmero de proyectos a ejecutar (priorizamos por BNA@mesX)", 
                             min_value=1, max_value=num_iniciativas, value=min(num_iniciativas,5))
    
    # 5) Ordenar por BN_at_mesX y elegir top n
    df_sorted = sorted(df_backlog, key=lambda x: x['BN_at_mesX'], reverse=True)
    chosen = df_sorted[:num_ejecutar]
    
    st.write(f"Seleccionamos los {num_ejecutar} proyectos con mayor BNA al mes {horizon_mes}.")
    
    chosen_table = pd.DataFrame([{
        'ID': p['id'],
        'Tipo': p['tipo'],
        'CF': p['cf'],
        'CV': p['cv'],
        'Ingr-Speed': p['ing'],
        'Impacto': p['imp'],
        f'BNA @ mes{horizon_mes}': round(p['BN_at_mesX'],2)
    } for p in chosen])
    st.dataframe(chosen_table)
    
    # 6) Curva agregada de BNA
    st.subheader("Curva Agregada de las Iniciativas Seleccionadas")
    total_meses = 29
    curve_sum = np.zeros(total_meses)
    
    for proj in chosen:
        curve_sum += proj['data']['bn_acum']
    
    # BN al mes horizon
    final_bnX = curve_sum[horizon_mes] if horizon_mes < total_meses else curve_sum[-1]
    st.write(f"Beneficio Neto Acumulado combinado al mes {horizon_mes}: **{final_bnX:.2f}**")
    
    # Plot
    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(np.arange(total_meses), curve_sum, label='BNA Agregado', color='blue')
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_title('Curva Global de Monetizaci—n (BNA)')
    ax.set_xlabel('Mes')
    ax.set_ylabel('Beneficio Neto Acumulado (Unidades)')
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)

if __name__ == "__main__":
    main()
