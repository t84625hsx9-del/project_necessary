import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Термодинамика: Поршень", layout="wide")
st.title("🌡️ Анимация цилиндра с газом")

# --- Настройки в сайдбаре ---
with st.sidebar:
    st.header("Управление")
    temp = st.slider("Температура (K)", 100, 1000, 300)
    vol = st.slider("Объем цилиндра (V)", 0.5, 2.0, 1.0)
    n = 1.0  # количество вещества
    R = 8.31
    pressure = (n * R * temp) / vol

# --- Создание визуализации (Цилиндр + График) ---
fig = go.Figure()

# 1. Рисуем корпус цилиндра (стенки)
fig.add_shape(type="rect", x0=0.4, y0=0, x1=0.6, y1=2.2, 
              line=dict(color="White", width=3))

# 2. Рисуем ПОРШЕНЬ (двигается в зависимости от vol)
# Цвет меняется от температуры (от синего к красному)
color_val = f"rgb({min(255, temp/4)}, 50, {max(0, 255-temp/4)})"

fig.add_shape(type="rect", x0=0.4, y0=vol, x1=0.6, y1=vol+0.1, 
              fillcolor=color_val, line=dict(color="LightGray"))

# 3. Добавляем "молекулы" внутри (случайные точки)
# Чем меньше объем, тем плотнее точки
np.random.seed(42)
num_particles = 30
px = np.random.uniform(0.42, 0.58, num_particles)
py = np.random.uniform(0.05, vol - 0.05, num_particles)

fig.add_trace(go.Scatter(x=px, y=py, mode='markers', 
                         marker=dict(size=6, color=color_val, opacity=0.6),
                         name="Молекулы газа"))

# Настройки осей для цилиндра
fig.update_layout(
    title=f"Состояние газа (P ≈ {pressure:.0f} Па)",
    xaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(range=[0, 2.5], title="Высота поршня (Объем)"),
    template="plotly_dark",
    height=600,
    showlegend=False
)

# --- Вывод в Streamlit ---
col1, col2 = st.columns([1, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("PV-диаграмма")
    # Маленький график процесса для наглядности
    v_axis = np.linspace(0.4, 2.5, 100)
    p_axis = (n * R * temp) / v_axis
    
    fig_pv = go.Figure()
    fig_pv.add_trace(go.Scatter(x=v_axis, y=p_axis, name="Изотерма", line=dict(dash='dash')))
    # Точка текущего состояния
    fig_pv.add_trace(go.Scatter(x=[vol], y=[pressure], mode='markers+text', 
                                 marker=dict(size=15, color='red'),
                                 text=["Текущее состояние"], textposition="top right"))
    
    fig_pv.update_layout(template="plotly_dark", height=400, xaxis_title="V", yaxis_title="P")
    st.plotly_chart(fig_pv, use_container_width=True)
    
    st.metric("Давление (P)", f"{pressure:.1f} Па")

