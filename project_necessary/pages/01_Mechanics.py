import streamlit as st
import numpy as np
import plotly.graph_objects as go

# заголовок окна и разметку задаёт main.py — здесь вызывать нельзя

st.title("Физическая лаборатория: Волны и колебания")

# Создаем вкладки
tab1, tab2, tab3 = st.tabs(["Нитяной маятник", "Волны в струне", "Пружинный маятник"])

# --- ВКЛАДКА 1: НИТЯНОЙ МАЯТНИК ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.header("Параметры")
        L_nit = st.slider("Длина нити (м)", 1.0, 5.0, 3.0, key="L_n")
        angle_max = st.slider("Угол отклонения (°)", 1, 20, 10, key="A_n")
        g_val = st.selectbox("Гравитация", [9.81, 1.62, 3.71], 
                            format_func=lambda x: {9.81:"Земля", 1.62:"Луна", 3.71:"Марс"}[x],
                            key="grav_select")

        theta0 = np.radians(angle_max)

        # Школьная формула Гюйгенса верна только для малых колебаний: в ней
        # sin(угол) заменён самим углом, и период тогда не зависит от амплитуды.
        T_small = 2 * np.pi * np.sqrt(L_nit / g_val)

        # Настоящий период: T = 4 sqrt(L/g) * K(sin(угол/2)), где K — полный
        # эллиптический интеграл. Берём его численно, без сторонних библиотек.
        phi = np.linspace(0, np.pi / 2, 2001)
        k_ell = np.sin(theta0 / 2)
        K_ell = np.trapezoid(1 / np.sqrt(1 - (k_ell * np.sin(phi)) ** 2), phi)
        T_nit = 4 * np.sqrt(L_nit / g_val) * K_ell
        slow_percent = 100 * (T_nit - T_small) / T_small

        st.metric("Период колебаний T", f"{T_nit:.2f} с",
                  help="Точный период с учётом амплитуды")
        st.metric("Частота ν", f"{1 / T_nit:.2f} Гц")
        st.caption(f"Формула малых колебаний даёт {T_small:.2f} с — настоящий период "
                   f"на {slow_percent:.2f}% больше.")

        if angle_max > 15:
            st.warning(f"Угол {angle_max}° — уже не мал. Настоящий период больше школьного "
                       f"на {slow_percent:.2f}%: реальный маятник качается медленнее.")
        else:
            st.success(f"Угол {angle_max}° мал: расхождение со школьной формулой "
                       f"всего {slow_percent:.2f}%.")

    with col2:
        # Один полный цикл: считаем углы честно, решая уравнение маятника
        #     theta'' = -(g / L) * sin(theta)
        # Методом Рунге-Кутты 4-го порядка. При углах до 20° синусоида малых
        # колебаний уже заметно расходится с этим движением.
        n_frames = 60
        steps_per_frame = 40
        dt = T_nit / (n_frames * steps_per_frame)
        theta, omega = theta0, 0.0
        theta_vals = [theta]

        def a(th):
            """Угловое ускорение маятника в точке th."""
            return -(g_val / L_nit) * np.sin(th)

        for _ in range(n_frames - 1):
            for _ in range(steps_per_frame):
                k1t, k1o = omega, a(theta)
                k2t, k2o = omega + dt / 2 * k1o, a(theta + dt / 2 * k1t)
                k3t, k3o = omega + dt / 2 * k2o, a(theta + dt / 2 * k2t)
                k4t, k4o = omega + dt * k3o, a(theta + dt * k3t)
                theta += dt / 6 * (k1t + 2 * k2t + 2 * k3t + k4t)
                omega += dt / 6 * (k1o + 2 * k2o + 2 * k3o + k4o)
            theta_vals.append(theta)
        theta_vals = np.array(theta_vals)
        t_steps = np.linspace(0, T_nit, n_frames)

        x_pts = L_nit * np.sin(theta_vals)
        y_pts = -L_nit * np.cos(theta_vals)

        fig1 = go.Figure()

        # 1. СТАТИЧНЫЕ ОБЪЕКТЫ (Штатив)
        fig1.add_shape(type="rect", x0=-1.2, y0=-5.5, x1=-1.0, y1=0.2, fillcolor="silver", line=dict(color="white"))
        fig1.add_shape(type="rect", x0=-1.8, y0=-5.8, x1=-0.4, y1=-5.5, fillcolor="#333", line=dict(color="white"))
        fig1.add_shape(type="rect", x0=-1.1, y0=0, x1=2.5, y1=0.1, fillcolor="gray", line=dict(color="white"))

        # 2. ТРАССЫ (То, что будет меняться)
        # Нитяной маятник
        fig1.add_trace(go.Scatter(x=[0, x_pts[0]], y=[0, y_pts[0]], mode="lines+markers",
                                 line=dict(color="silver", width=3),
                                 marker=dict(size=[0, 20], color=["white", "red"]),
                                 name="Нитяной"))
        
        # 3. АНИМАЦИЯ
        # В кадре столько же объектов, сколько трасс на графике, иначе анимация
        # не запускается: Plotly сопоставляет их по порядку.
        frames1 = [go.Frame(data=[
            go.Scatter(x=[0, x_pts[i]], y=[0, y_pts[i]])
        ], name=str(i)) for i in range(len(t_steps))]
        
        fig1.frames = frames1
        frame_duration=(T_nit*1000)/len(t_steps)
        fig1.update_layout(
            xaxis=dict(range=[-4, 5], visible=False), 
            yaxis=dict(range=[-6, 1], visible=False),
            template="plotly_dark", height=500,
            updatemenus=[dict(
                type="buttons",
                buttons=[dict(
                    label="ЗАПУСК",
                    method="animate",
                    args=[None,{
                        "frame": {"duration":frame_duration, "redraw": False},
                        "fromcurrent": True,
                        "transition":{"duration":frame_duration, "easing":"linear"}
                        }])])])
        
        st.plotly_chart(fig1, width="stretch", key="p_chart")
    m1, m2, m3,m4 = st.columns(4)
    with m1:
        st.info("🕒 **Период (T)**")
        st.write("Время одного полного колебания (T)")
        st.latex(r"T = \frac{t}{N}")
        st.caption("Единица измерения: Секунды (с)")
        st.write("**Переменные:**")
        st.write(" t - общее время, с")
        st.write(" N - количество полных колебаний, безразмерная величина")
    with m2:
        st.success("🔄 **Частота (ν)**")
        st.write("Число колебаний в секунду(ν)")
        st.latex(r"ν = \frac{1}{T}")
        st.caption("Единица измерения: Герцы (Гц)")
        st.write("**Переменные:**")
        st.write(r" T - период колебаний")
    with m3:
        st.warning("📏 **Длина волны (λ)**")
        st.write("Расстояние между соседними (гребнями или впадинами) волны")
        st.latex(r"\lambda = v \cdot T")
        st.caption("Единица измерения: Метры (м)")
        st.write("**Переменные:**")
        st.write(r" λ - длина волны (расстояние между соседними гребнями), м")
        st.write(r" v - скорость распространения волны, м/с")
        st.write(r" T - период колебаний, с")
    with m4:
        st.info("🧵 **Период математического маятника (T)**")
        st.write("Время одного полного колебания маятника.")
        st.latex(r"T = 2\pi \sqrt{\frac{L}{g}}")
        st.caption("Единица измерения: Секунды (с)")
        st.write("**Переменные:**")
        st.write(r" T - период колебаний, с")
        st.write(r" l - длина нити, м")
        st.write(r" g - ускорение свободного падения, м/с² (приблизительно 9.81 м/с² на Земле)")
        st.write(r" π - математическая константа (приблизительно 3.14159): отношение длины окружности к её диаметру")
# Разместим это под st.plotly_chart в tab1
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.latex(r"T = 2\pi\sqrt{\frac{L}{g}}")
        st.caption("Формула Гюйгенса для периода")
    with c2:
        st.latex(r"\nu = \frac{1}{2\pi}\sqrt{\frac{g}{L}}")
        st.caption("Частота колебаний")


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
    # Один период волны: за это время картинка сдвигается ровно на длину волны
    # и повторяется, поэтому анимация зацикливается без рывка. (Раньше здесь
    # стоял период маятника с первой вкладки — волна зависела от длины нити.)
    #
    # Анимация идёт в реальном времени: один период на экране длится ровно
    # период волны. Поэтому частая волна бежит быстрее редкой, а длинная — быстрее
    # короткой при той же частоте, как и положено при v = λ·ν. Раньше кадр всегда
    # длился 30 мс, и на экране любая волна двигалась одинаково.
    # Показываем не один период, а столько, чтобы прокрутка длилась около четырёх
    # секунд: на 5 Гц один период — это 0.2 с, и анимация кончилась бы, не успев
    # начаться. Периодов берём целое число, поэтому картинка возвращается в
    # исходную и прокрутку можно запускать снова без рывка.
    wave_periods = max(1, round(4.0 / period_w))
    wave_run_s = wave_periods * period_w
    # Кадров столько, чтобы кадр не оказался короче 16 мс: чаще экран всё равно
    # не обновляется, а лишние кадры только утяжелили бы страницу.
    n_wave_frames = int(np.clip(wave_run_s * 1000 / 16, 24, 240))
    wave_frame_ms = wave_run_s * 1000 / n_wave_frames
    t_w = np.linspace(0, wave_run_s, n_wave_frames, endpoint=False)
    
    fig2 = go.Figure()
    
    # Рисуем саму волну
    # Формула: y = A * sin(k*x - omega*t), где omega = 2*pi*nu
    def get_wave_y(t_val):
        return np.sin(k_wave * (x_w - v_wave * t_val))

    fig2.add_trace(go.Scatter(x=x_w, y=get_wave_y(0), mode="lines", 
                             line=dict(color="cyan", width=4), name="Волна"))

    # Анимация. В кадре передаём только y: x во всех кадрах один и тот же, он уже
    # есть у самой трассы. И округляем до четырёх знаков — на глаз это не видно,
    # а страница весит втрое меньше и ползунки отзываются быстрее.
    fig2.frames = [go.Frame(data=[go.Scatter(y=np.round(get_wave_y(t), 4))]) for t in t_w]
    
    fig2.update_layout(
        template="plotly_dark", height=400,
        xaxis=dict(title="Расстояние (м)", range=[0, 10]),
        yaxis=dict(range=[-1.5, 1.5], visible=False),
        updatemenus=[dict(type="buttons", buttons=[dict(
            label="▶ ПУСК", method="animate",
            args=[None, {"frame": {"duration": wave_frame_ms, "redraw": False},
                         "fromcurrent": True,
                         "transition": {"duration": 0}}])])]
    )
    st.plotly_chart(fig2, width="stretch", key="wave_chart")

    # 3. Справочная формула
    st.write("---")
    st.latex(r"v = \lambda \cdot \nu = \frac{\lambda}{T}")
    st.write(r"v - скорость волны, м/с")
    st.write(r"λ - длина волны (расстояние между соседними гребнями), м")
    st.write(r"ν - частота волны(количество колебаний за 1 секунду), Гц ")
    st.write(r"T - период(время 1 полного колебания), c")
    st.info(f"**Анализ:** При длине волны {lambda_w:.2f} м и частоте {wave_freq:.2f} Гц "
            f"волна пробегает {v_wave:.2f} метра за одну секунду. Анимация идёт "
            f"в реальном времени, поэтому это видно на глаз: гребень пересекает "
            f"весь рисунок (10 м) за {10 / v_wave:.1f} с.")



# --- ВКЛАДКА 3: ПРУЖИННЫЙ МАЯТНИК ---
with tab3:
    col3, col4 = st.columns([1, 2])
    with col3:
        m_p = st.slider("Масса (кг)", 0.5, 5.0, 1.0, key="m_p")
        k_p = st.slider("Жесткость (Н/м)", 10, 100, 40, key="k_p")
        amplitude = st.slider(
            "Амплитуда A (м)", 0.1, 1.0, 0.3, key="amp_p",
            help="Насколько груз отходит от положения равновесия — то есть на сколько ты "
                 "оттянул его вниз, прежде чем отпустить. Вверх он потом поднимется "
                 "ровно на столько же, поэтому полный размах равен 2·A. "
                 "На период амплитуда не влияет: T = 2π√(m/k), амплитуды в формуле нет."
        )

        g_spring = 9.81
        spring_free = 1.0                       # длина пружины без груза
        # Груз висит там, где сила упругости уравновешивает вес: k*x = m*g.
        # Поэтому тяжёлый груз или мягкая пружина — и груз висит ниже.
        stretch = m_p * g_spring / k_p
        y_equilibrium = -(spring_free + stretch)
        T_p = 2 * np.pi * np.sqrt(m_p / k_p)

        st.metric("Период T", f"{T_p:.2f} с")
        st.metric("Растяжение x", f"{stretch:.2f} м",
                  help="Насколько пружина вытянулась под весом груза, пока он висит неподвижно")
        st.latex(r"k \cdot x = m \cdot g \;\Rightarrow\; x = \frac{m g}{k}")

    def spring_func(y_end):
        """Витки пружины от точки подвеса до груза: чем длиннее, тем витки реже."""
        num_coils = 10
        y_points = np.linspace(0, y_end, num_coils * 12)
        amplitude_x = 0.1
        if y_end != 0:
            x_points = amplitude_x * np.sign(y_end) * np.sin(2 * np.pi * num_coils * (y_points / y_end))
        else:
            x_points = np.zeros_like(y_points)
        return x_points, y_points

    with col4:
        # Кадров всегда одинаково — 60 на полный цикл, иначе при коротком периоде
        # (лёгкий груз на жёсткой пружине) их выходило меньше десятка и движение
        # получалось рваным. endpoint=False — чтобы последний кадр не повторял
        # первый и анимация зацикливалась без залипания.
        num_frames = 60
        t_p = np.linspace(0, T_p, num_frames, endpoint=False)
        frame_duration = (T_p / num_frames) * 1000
        # Минус перед амплитудой: в первом кадре груз в нижней точке — ровно так,
        # как описано в подсказке к ползунку («оттянул вниз и отпустил»).
        y_p = y_equilibrium - amplitude * np.cos((2 * np.pi / T_p) * t_p)
        fig3 = go.Figure()
        fig3.add_shape(type="rect", x0=-0.5, y0=0, x1=0.5, y1=0.1, fillcolor="gray")
        sx, sy = spring_func(y_p[0])
        fig3.add_trace(go.Scatter(x=sx, y=sy, mode="lines", line=dict(color="silver", width=2), showlegend=False))
        fig3.add_trace(go.Scatter(x=[0], y=[y_p[0]], mode="markers", marker=dict(symbol="square", size=40, color="blue"), showlegend=False))

        fig3.frames = [go.Frame(data=[go.Scatter(x=spring_func(y_p[i])[0], y=spring_func(y_p[i])[1]),
                                     go.Scatter(x=[0], y=[y_p[i]])]) for i in range(len(t_p))]
        # Рамка рисунка постоянная — рассчитана на самый длинный случай (тяжёлый
        # груз на мягкой пружине). Если подгонять её под текущую пружину, кадр
        # растягивается вместе с ней, и растяжение на глаз почти не заметно.
        max_stretch = 5.0 * g_spring / 10.0        # предельные значения ползунков массы и жёсткости
        y_low = -(spring_free + max_stretch + 1.0) - 0.3
        fig3.update_layout(
            xaxis=dict(range=[-1, 1], visible=False), 
            yaxis=dict(range=[y_low, 0.5], visible=False),
            template="plotly_dark", height=500,
            updatemenus=[dict(
                type="buttons",
                buttons=[dict(
                    label="ЗАПУСК",
                    method="animate",
                    args=[None,{
                        "frame": {"duration":frame_duration, "redraw": False},
                        "fromcurrent": True,
                        "transition":{"duration":0},
                        }])])])
        st.plotly_chart(fig3, width="stretch", key="spring_chart")

    st.divider()
    st.subheader("📚 Справочные материалы")

    s_col1, s_col2 = st.columns(2)

    with s_col1:
        with st.expander("📏 Растяжение x — насколько вытянулась пружина", expanded=True):
            st.write("""
            Повесили груз — пружина вытянулась и остановилась там, где сила упругости
            сравнялась с весом груза. Это и есть **растяжение x**, оно же — положение
            равновесия, вокруг которого потом идут колебания.
            """)
            st.latex(r"k \cdot x = m \cdot g \quad\Rightarrow\quad x = \frac{m g}{k}")
            st.write(f"""
            **Как читать формулу сейчас:**
            - **m — масса груза**, {m_p} кг;
            - **g — ускорение свободного падения**, 9.81 м/с². Вместе m·g — это
              **вес груза**, сейчас {m_p * g_spring:.1f} Н;
            - **k — жёсткость пружины**, {k_p} Н/м;
            - **x — растяжение**: {m_p * g_spring:.1f} Н ÷ {k_p} Н/м = **{stretch:.2f} м**.

            Тяжелее груз или мягче пружина — растяжение больше, груз висит ниже.
            """)

    with s_col2:
        with st.expander("↕️ Амплитуда A — насколько качается груз", expanded=True):
            st.write(f"""
            **Амплитуда A** — это насколько груз отходит от положения равновесия,
            то есть на сколько ты оттянул его вниз, прежде чем отпустить. Вверх он
            поднимется ровно на столько же.

            Сейчас A = **{amplitude:.2f} м**, поэтому груз ходит от
            **{spring_free + stretch - amplitude:.2f} м** до
            **{spring_free + stretch + amplitude:.2f} м** под точкой подвеса,
            а полный размах равен 2·A = **{2 * amplitude:.2f} м**.

            Важное: **на период амплитуда не влияет**. Оттянешь сильнее — груз пойдёт
            быстрее и пройдёт больший путь, но вернётся ровно через то же время.
            """)
            if amplitude > stretch:
                st.warning(f"Сейчас амплитуда ({amplitude:.2f} м) больше растяжения "
                           f"({stretch:.2f} м): в верхней точке пружина уже не растянута, "
                           f"а сжата. В школьных задачах обычно разбирают случай, когда "
                           f"пружина всё время растянута.")

    s_col3, s_col4 = st.columns(2)

    with s_col3:
        with st.expander("🔩 Жёсткость k — свойство самой пружины", expanded=True):
            st.write(f"""
            **Жёсткость k** показывает, какая сила нужна, чтобы растянуть пружину
            на один метр. Измеряется в ньютонах на метр (Н/м).

            Сейчас k = **{k_p} Н/м**: чтобы растянуть эту пружину на метр, надо тянуть
            с силой {k_p} Н. Жёсткая пружина (100 Н/м) почти не поддаётся, мягкая
            (10 Н/м) тянется легко.

            Жёсткость от груза не зависит — она такая, какой сделана пружина.
            А вот растяжение x зависит и от неё, и от груза.
            """)

    with s_col4:
        with st.expander("🕒 Период T — время одного колебания", expanded=True):
            st.latex(r"T = 2\pi \sqrt{\frac{m}{k}}")
            st.write(f"""
            **Переменные:**
            - **T — период**, время одного полного колебания, с. Сейчас **{T_p:.2f} с**;
            - **m — масса груза**, кг;
            - **k — жёсткость пружины**, Н/м;
            - **π** — 3.14159…

            Тяжёлый груз качается медленно, жёсткая пружина — быстро. Ни амплитуда,
            ни сила тяжести в формулу не входят: на Луне период был бы тот же самый,
            только пружина вытянулась бы меньше.
            """)
    



# Справочник
# --- СТИЛИЗОВАННЫЙ СПРАВОЧНИК ---
# --- СТИЛИЗОВАННЫЙ СПРАВОЧНИК ---
st.write("---")
st.header("📊 Физические характеристики")




# Второй ряд (Связь с Оптикой)
st.write("### 🔦 Связь с Оптикой")
col_opt1, col_opt2 = st.columns([2, 1])

with col_opt1:
    # Строка сырая (r), иначе Python принял бы \nu за перенос строки и формула
    # развалилась бы прямо на экране.
    st.markdown(r"""
    В оптике эти же законы определяют природу света.
    При переходе луча из одной среды в другую (преломлении):
    1.  **Частота ($\nu$)** остается **неизменной** (поэтому цвет не меняется).
    2.  **Скорость ($v$)** и **Длина волны ($\lambda$)** — **уменьшаются** в более плотной среде.
    """)
    st.latex(r"n = \frac{c}{v} = \frac{\lambda_{vac}}{\lambda_{med}}")

with col_opt2:
    st.metric("Скорость света (c)", "300 000 км/с", help="В вакууме")

st.info("💡 **Интересный факт:** Частота — это единственная характеристика, которая 'помнит' источник колебаний, независимо от того, через какие линзы или среды проходит свет.")

















