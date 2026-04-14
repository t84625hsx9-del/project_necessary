import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Лаборатория: Волны и колебания", layout="wide")

st.title("🧲 Физическая лаборатория: Волны и колебания")

# Создаем вкладки
tab1, tab2, tab3 = st.tabs(["🧵 Нитяной маятник", "🌊 Волны в струне", "🌀 Пружинный маятник"])

# --- ВКЛАДКА 1: НИТЯНОЙ МАЯТНИК ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.header("⚙️ Параметры")
        L_nit = st.slider("Длина нити (м)", 1.0, 5.0, 3.0, key="L_n")
        angle_max = st.slider("Угол отклонения (°)", 5, 60, 30, key="A_n")
        g_val = st.selectbox("Гравитация", [9.81, 1.62, 3.71], 
                             format_func=lambda x: {9.81:"Земля", 1.62:"Луна", 3.71:"Марс"}[x])
        
        T_nit = 2 * np.pi * np.sqrt(L_nit / g_val)
        st.metric("Период колебаний T", f"{T_nit:.2f} с")
        st.metric("Частота ν", f"{1/T_nit:.2f} Гц")

    with col2:
        t_steps = np.linspace(0, T_nit, 60)
        theta_vals = np.radians(angle_max) * np.cos(2 * np.pi * t_steps / T_nit)
        x_pts = L_nit * np.sin(theta_vals)
        y_pts = -L_nit * np.cos(theta_vals)

        fig1 = go.Figure()
        # Штатив
        fig1.add_shape(type="rect", x0=-1.2, y0=-5.5, x1=-1.0, y1=0.2, fillcolor="silver", line=dict(color="white"))
        fig1.add_shape(type="rect", x0=-1.8, y0=-5.8, x1=-0.4, y1=-5.5, fillcolor="#333", line=dict(color="white"))
        fig1.add_shape(type="rect", x0=-1.1, y0=0, x1=0.8, y1=0.1, fillcolor="gray", line=dict(color="white"))

        # След
        fig1.add_trace(go.Scatter(x=x_pts, y=y_pts, mode="lines", 
                                 line=dict(color="rgba(255,255,255,0.1)", dash="dot"), showlegend=False))
        # Стержень и шарик
        fig1.add_trace(go.Scatter(x=[0, x_pts[0]], y=[0, y_pts[0]], mode="lines+markers",
                                 line=dict(color="silver", width=5),
                                 marker=dict(size=[0, 25], color=["white", "red"], line=dict(width=2, color="white")),
                                 showlegend=False))

        frames1 = [go.Frame(data=[go.Scatter(), 
                                 go.Scatter(x=[0, x_pts[i]], y=[0, y_pts[i]], 
                                            marker=dict(size=[0, 25]))], name=str(i)) for i in range(len(t_steps))]
        fig1.frames = frames1
        fig1.update_layout(xaxis=dict(range=[-4, 4], visible=False), yaxis=dict(range=[-6, 1], visible=False),
                          template="plotly_dark", height=500,
                          updatemenus=[dict(type="buttons", buttons=[dict(label="▶ КАЧАТЬ", method="animate", args=[None, {"frame":{"duration": 30}}])])])
        st.plotly_chart(fig1, use_container_width=True, key="p_chart")

# Размести это под st.plotly_chart в tab1
st.write("---")
c1, c2, c3 = st.columns(3)
with c1:
    st.latex(r"T = 2\pi\sqrt{\frac{L}{g}}")
    st.caption("Формула Гюйгенса для периода")
with c2:
    st.latex(r"\nu = \frac{1}{2\pi}\sqrt{\frac{g}{L}}")
    st.caption("Частота колебаний")
with c3:
    st.latex(r"E = \frac{mv^2}{2} + mgh")
    st.caption("Закон сохранения энергии")


# --- ВКЛАДКА 2: БЕГУЩАЯ ВОЛНА ---
# --- ВКЛАДКА 2: БЕГУЩАЯ ВОЛНА ---
with tab2:
    st.subheader("🌊 Физика волны: Скорость, Частота, Длина")
    
    # 1. Настройки параметров
    c1, c2, c3 = st.columns(3)
    with c1:
        # Длина волны (расстояние между гребнями)
        lambda_w = st.slider("Длина волны λ (м)", 1.0, 5.0, 2.0, key="lam_s")
    with c2:
        # Частота (Гц)
        wave_freq = st.slider("Частота ν (Гц)", 0.5, 5.0, 1.0, key="freq_s")
    
    # Расчет зависимых величин
    v_wave = lambda_w * wave_freq  # Скорость волны
    period_w = 1 / wave_freq        # Период
    k_wave = 2 * np.pi / lambda_w  # Волновое число

    with c3:
        # Вывод скорости как в Оптике (красивая метрика)
        st.metric("Скорость волны (v)", f"{v_wave:.2f} м/с")

    # 2. Визуализация
    x_w = np.linspace(0, 10, 300)
    # Скорость анимации зависит от реальной физической скорости v_wave
    t_steps = np.linspace(0, 2, 60) 
    
    fig2 = go.Figure()
    
    # Рисуем саму волну
    # Формула: y = A * sin(k*x - omega*t), где omega = 2*pi*nu
    def get_wave_y(t_val):
        return np.sin(k_wave * (x_w - v_wave * t_val))

    fig2.add_trace(go.Scatter(x=x_w, y=get_wave_y(0), mode="lines", 
                             line=dict(color="cyan", width=4), name="Волна"))

    # Анимация
    fig2.frames = [go.Frame(data=[go.Scatter(x=x_w, y=get_wave_y(t))]) for t in t_steps]
    
    fig2.update_layout(
        template="plotly_dark", height=400,
        xaxis=dict(title="Расстояние (м)", range=[0, 10]),
        yaxis=dict(range=[-1.5, 1.5], visible=False),
        updatemenus=[dict(type="buttons", buttons=[dict(label="▶ ПУСК", method="animate", args=[None, {"frame":{"duration": 30}}])])]
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 3. Справочная формула (как просил)
    st.write("---")
    st.latex(r"v = \lambda \cdot \nu = \frac{\lambda}{T}")
    st.info(f"**Анализ:** При длине волны {lambda_w} м и частоте {wave_freq} Гц, волна пробегает {v_wave} метров за одну секунду.")



# --- ВКЛАДКА 3: ПРУЖИННЫЙ МАЯТНИК ---
with tab3:
    col3, col4 = st.columns([1, 2])
    with col3:
        m_p = st.slider("Масса (кг)", 0.5, 5.0, 1.0, key="m_p")
        k_p = st.slider("Жесткость (Н/м)", 10, 100, 40, key="k_p")
        T_p = 2 * np.pi * np.sqrt(m_p / k_p)
        st.metric("Период T", f"{T_p:.2f} с")

    def spring_func(y_end):
        y = np.linspace(0, y_end, 100)
        x = 0.1 * np.sin(2 * np.pi * 12 * y / (y_end if y_end != 0 else 1))
        return x, y

    with col4:
        t_p = np.linspace(0, T_p, 60)
        y_p = -1.5 + 0.7 * np.cos((2*np.pi/T_p) * t_p)
        fig3 = go.Figure()
        fig3.add_shape(type="rect", x0=-0.5, y0=0, x1=0.5, y1=0.1, fillcolor="gray")
        sx, sy = spring_func(y_p[0])
        fig3.add_trace(go.Scatter(x=sx, y=sy, mode="lines", line=dict(color="silver", width=2), showlegend=False))
        fig3.add_trace(go.Scatter(x=[0], y=[y_p[0]], mode="markers", marker=dict(symbol="square", size=40, color="blue"), showlegend=False))
        
        fig3.frames = [go.Frame(data=[go.Scatter(x=spring_func(y_p[i])[0], y=spring_func(y_p[i])[1]), 
                                     go.Scatter(x=[0], y=[y_p[i]])]) for i in range(len(t_p))]
        fig3.update_layout(xaxis=dict(range=[-1, 1], visible=False), yaxis=dict(range=[-3, 0.5], visible=False),
                          template="plotly_dark", height=500,
                          updatemenus=[dict(type="buttons", buttons=[dict(label="▶ СТАРТ", method="animate", args=[None, {"frame":{"duration": 30}}])])])
        st.plotly_chart(fig3, use_container_width=True)
        
    st.write("---")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.latex(r"T = 2\pi\sqrt{\frac{m}{k}}")
        st.caption("Период колебаний")
    with p2:
        st.latex(r"\omega = \sqrt{\frac{k}{m}}")
        st.caption("Циклическая частота")
    with p3:
        st.latex(r"F = -k \cdot x")
        st.caption("Закон Гука")



# Справочник
# --- СТИЛИЗОВАННЫЙ СПРАВОЧНИК ---
st.write("---")
st.header("📊 Физические характеристики")

# Первый ряд метрик (основные показатели)
m1, m2, m3 = st.columns(3)

with m1:
    st.info("🕒 **Период (T)**")
    st.write("Время одного полного цикла")
    st.latex(r"T = \frac{t}{n}")
    st.caption("Единица измерения: Секунды (с)")

with m2:
    st.success("🔄 **Частота (ν)**")
    st.write("Число колебаний в секунду")
    st.latex(r"\nu = \frac{1}{T}")
    st.caption("Единица измерения: Герцы (Гц)")

with m3:
    st.warning("📏 **Длина волны (λ)**")
    st.write("Расстояние между гребнями")
    st.latex(r"\lambda = v \cdot T")
    st.caption("Единица измерения: Метры (м)")

# Второй ряд (Связь с Оптикой)
st.write("### 🔦 Связь с Оптикой")
col_opt1, col_opt2 = st.columns([2, 1])

with col_opt1:
    st.markdown(f"""
    В оптике эти же законы определяют природу света. 
    При переходе луча из одной среды в другую (преломлении):
    1.  **Частота ($\nu$)** остается **неизменной** (поэтому цвет не меняется).
    2.  **Скорость ($v$)** и **Длина волны ($\lambda$)** — **уменьшаются** в более плотной среде.
    """)
    st.latex(r"n = \frac{c}{v} = \frac{\lambda_{vac}}{\lambda_{med}}")

with col_opt2:
    st.metric("Скорость света (c)", "300 000 км/с", help="В вакууме")

st.info("💡 **Интересный факт:** Частота — это единственная характеристика, которая 'помнит' источник колебаний, независимо от того, через какие линзы или среды проходит свет.")

















