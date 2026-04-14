import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Оптика: Финал", layout="wide")
st.title("🔦 Оптический симулятор: Преломление и ПВО")

# --- 1. НАСТРОЙКИ ---
with st.sidebar:
    st.header("⚙️ Параметры")
    n1 = st.slider("n1 (Верх)", 1.0, 2.5, 1.5)
    n2 = st.slider("n2 (Низ)", 1.0, 2.5, 1.0)
    
    # Выбор стороны и четверти
    side = st.radio("Сторона источника:", ["Слева", "Справа"])
    vert = st.radio("Вертикаль:", ["Сверху", "Снизу"])
    angle_deg = st.slider("Угол падения α (0-90°)", 0, 90, 30)

# Определяем физические коэффициенты и направление
start_n, end_n = (n1, n2) if vert == "Сверху" else (n2, n1)
y_dir = 1 if vert == "Сверху" else -1
x_side = -1 if side == "Слева" else 1

# --- 2. ВЫЧИСЛЕНИЯ ---
alpha_rad = np.radians(angle_deg)
sin_beta = (start_n * np.sin(alpha_rad)) / end_n

if sin_beta > 1.0:
    total_reflection = True
    beta_rad = alpha_rad
    beam_label, beam_color = "ПВО", "red"
else:
    total_reflection = False
    beta_rad = np.arcsin(sin_beta)
    beam_label, beam_color = "Преломление", "#00ff9d"

# --- 3. КООРДИНАТЫ ---
# Падающий луч
x_inc = [x_side * np.sin(alpha_rad), 0]
y_inc = [y_dir * np.cos(alpha_rad), 0]

# Выходящий луч
if total_reflection:
    # ПОЛНОЕ ОТРАЖЕНИЕ: 
    # y_refr остается с тем же знаком, что и y_dir (та же среда)
    # x_refr меняет знак (отскакивает в другую сторону)
    # beta_rad при ПВО равен alpha_rad (угол падения = углу отражения)
    x_refr = [0, -x_side * np.sin(alpha_rad)] 
    y_refr = [0, y_dir * np.cos(alpha_rad)]
else:
    # ПРЕЛОМЛЕНИЕ:
    # Уходит в противоположную среду (-y_dir) 
    # И в противоположную сторону по горизонтали (-x_side)
    x_refr = [0, -x_side * np.sin(beta_rad)]
    y_refr = [0, -y_dir * np.cos(beta_rad)]

# --- 4. ОТРИСОВКА ---
def get_arc_path(start_deg, end_deg, radius=0.3):
    # Нормализация, чтобы дуга всегда была короткой (не более 180 градусов)
    diff = (end_deg - start_deg + 180) % 360 - 180
    end_deg = start_deg + diff
    
    t = np.linspace(np.radians(start_deg), np.radians(end_deg), 30)
    x = radius * np.cos(t)
    y = radius * np.sin(t)
    
    path = f"M {x[0]},{y[0]}"
    for xi, yi in zip(x[1:], y[1:]):
        path += f" L {xi},{yi}"
    return path




# --- 3. ВИЗУАЛИЗАЦИЯ PLOTLY ---
fig = go.Figure()

# --- 1. РАСЧЕТ БЕТА (СИНХРОННО ДЛЯ ГРАФИКА И МАТЕМАТИКИ) ---
# --- 1. РАСЧЕТ БЕТА (ГРАДУСЫ) ---
# --- 1. РАСЧЕТ УГЛА БЕТА (ДЛЯ ДУГИ) ---
if not total_reflection:
    if round(angle_deg, 1) == 90.0:
        beta_deg = 90.0
    else:
        n_in = n1 if vert == "Сверху" else n2
        n_out = n2 if vert == "Сверху" else n1
        sin_beta_val = (n_in * np.sin(np.radians(angle_deg))) / n_out
        beta_deg = np.degrees(np.arcsin(np.clip(sin_beta_val, -1.0, 1.0)))

# --- 2. КООРДИНАТЫ ЛУЧЕЙ (СТРОГО ОДИН РАЗ) ---
if round(angle_deg, 1) == 90.0:
    x_refr = [0, -x_side * np.sin(alpha_rad)] 
    y_refr = [0, -y_dir * np.cos(alpha_rad)]
    beam_label, beam_color = "Прямой проход", "#00ff9d"
elif total_reflection:
    x_refr = [0, -x_side * np.sin(alpha_rad)] 
    y_refr = [0, y_dir * np.cos(alpha_rad)]
    beam_label, beam_color = "ПВО", "red"
else:
    # Здесь используем бету
    x_refr = [0, -x_side * np.sin(np.radians(beta_deg))]
    y_refr = [0, -y_dir * np.cos(np.radians(beta_deg))]
    beam_label, beam_color = "Преломление", "#00ff9d"

# --- 2. ДУГА АЛЬФА (α) ---
base_angle_alpha = 90 if vert == "Сверху" else 270
arc_end_alpha = base_angle_alpha - (x_side * angle_deg) if vert == "Сверху" else base_angle_alpha + (x_side * angle_deg)

if round(angle_deg, 1) == 90:
    q = 0.1
    # Квадрат альфы (в своей среде)
    fig.add_shape(type="path", path=f"M {x_side*q},0 L {x_side*q},{y_dir*q} L 0,{y_dir*q}", line=dict(color="orange", width=2))
else:
    fig.add_shape(type="path", path=get_arc_path(base_angle_alpha, arc_end_alpha, radius=0.3), line=dict(color="orange", width=2))

# Аннотация Альфа: привязана к падающему лучу (y_inc)


# --- 3. ДУГА БЕТА (β) ---
if not total_reflection:
    # Используем координаты твоего преломленного луча [1] - конец линии
    b_start = 270 if y_refr[1] < 0 else 90
    b_end = np.degrees(np.arctan2(y_refr[1], x_refr[1]))

    if round(angle_deg, 1) == 90.0:
        q = 0.1
        # Квадрат беты (в противоположной среде)
        fig.add_shape(type="path", path=f"M {x_refr[1]*q},0 L {x_refr[1]*q},{y_refr[1]*q} L 0,{y_refr[1]*q}", line=dict(color="#00ff9d", width=2))
        bx, by = x_refr[1] * 0.4, y_refr[1] * 0.5
    else:
        # Дуга преломления
        fig.add_shape(type="path", path=get_arc_path(b_start, b_end, radius=0.3), line=dict(color="#00ff9d", width=2))
        # Центр дуги
        mid_t = np.radians((b_start + b_end) / 2)
        bx, by = 0.45 * np.cos(mid_t), 0.45 * np.sin(mid_t)

    # Аннотация Бета: привязана к преломленному лучу (y_refr)




# --- ФИНАЛЬНЫЙ БЛОК БЕТА ДЛЯ 90 ГРАДУСОВ ---
if not total_reflection:
    # 1. Определяем старт и конец дуги по твоему лучу
    # (Используем твои x_refr[1] и y_refr[1])
    b_start = 270 if y_refr[1] < 0 else 90
    b_end = np.degrees(np.arctan2(y_refr[1], x_refr[1]))

    if round(angle_deg, 1) == 90.0:
        q = 0.1
        # Квадрат рисуем строго по координатам ВЫХОДА луча
        fig.add_shape(type="path", 
                      path=f"M {x_refr[1]*q},0 L {x_refr[1]*q},{y_refr[1]*q} L 0,{y_refr[1]*q}", 
                      line=dict(color="#00ff9d", width=2))
        
        # Аннотация β: жестко привязана к y_refr[1]
        # Если луч ушел вниз — буква внизу, если вверх — вверху. С альфой не столкнется.
        bx, by = x_refr[1] * 0.4, y_refr[1] * 0.5
    else:
        # Стандартная дуга для всех остальных углов
        fig.add_shape(type="path", 
                      path=get_arc_path(b_start, b_end, radius=0.3), 
                      line=dict(color="#00ff9d", width=2))
        
        # Центр дуги для буквы β (чтобы была рядом с зеленой линией)
        mid_t = np.radians((b_start + b_end) / 2)
        bx, by = 0.45 * np.cos(mid_t), 0.45 * np.sin(mid_t)

    # Отрисовка самой буквы










# --- 4. ОСИ И ЛИНИИ ---
fig.add_trace(go.Scatter(x=[-1.5, 1.5], y=[0, 0], mode='lines', line=dict(dash="dash", color="gray", width=2), showlegend=False))
fig.add_trace(go.Scatter(x=[0, 0], y=[-1, 1], mode='lines', line=dict(color="gray", width=2), showlegend=False))

fig.add_annotation(x=-1.2, y=0.5, text=f"Среда 1 (n={n1})", showarrow=False, font=dict(color="lightblue"))
fig.add_annotation(x=-1.2, y=-0.5, text=f"Среда 2 (n={n2})", showarrow=False, font=dict(color="lightyellow"))

# Отрисовка лучей
fig.add_trace(go.Scatter(x=x_inc, y=y_inc, mode='lines', name="Падающий луч", line=dict(color="yellow", width=4)))
fig.add_trace(go.Scatter(x=x_refr, y=y_refr, mode='lines', name=beam_label, line=dict(color=beam_color, width=4)))

fig.update_layout(
    xaxis=dict(range=[-1.5, 1.5], showgrid=False, visible=False, fixedrange=True),
    yaxis=dict(range=[-1.2, 1.2], showgrid=False, visible=False, fixedrange=True),
    template="plotly_dark", height=500, margin=dict(t=20, b=20), showlegend=True
)

# --- 5. ВЫВОД СИМУЛЯЦИИ И МАТЕМАТИКА ---
col1, col2 = st.columns([2, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True, key="optics_final_v4")

with col2:
    st.subheader("🔢 Математика")
    st.latex(r"\frac{\sin \alpha}{\sin \beta} = \frac{n_2}{n_1}")
    
    n_start = n1 if vert == "Сверху" else n2
    n_end = n2 if vert == "Сверху" else n1
    
    if n_start > n_end:
        critical_angle = np.degrees(np.arcsin(n_end / n_start))
        st.info(f"Критический угол: {critical_angle:.2f}°")
    else:
        critical_angle = 91

    # Расчет беты для метрик
    sin_beta = (n_start * np.sin(np.radians(angle_deg))) / n_end
    beta_rad_calc = np.arcsin(np.clip(sin_beta, -1.0, 1.0))
    beta_deg_calc = np.degrees(beta_rad_calc)

    if angle_deg >= critical_angle and angle_deg < 90:
        st.error("⚠️ Полное отражение")
        st.metric("Угол преломления β", "Отсутствует (ПВО)")
    elif round(angle_deg, 1) == 90.0:
        st.success("✅ Прямой проход (90°)")
        st.metric("Угол преломления β", "90.00°")
    elif round(angle_deg, 1) == 0.0:
        st.info("⚠️ Скользящий луч (0°)")
        st.metric("Угол преломления β", f"{beta_deg_calc:.2f}° (пред.)")
    else:
        st.success("✅ Преломление")
        st.metric("Угол преломления β", f"{beta_deg_calc:.2f}°")





# --- 5. ТЕОРЕТИЧЕСКИЙ БЛОК (СОВМЕЩЕНИЕ) ---
st.divider()
st.header("📚 Справочные материалы")

t_col1, t_col2 = st.columns(2)

with t_col1:
    with st.expander("🤔 Почему свет преломляется?", expanded=True):
        st.write("""
        Преломление происходит из-за **изменения скорости света** при переходе из одной среды в другую. (это пример с абсолютным показателем, а с относительным это закон Снеллуиса)
        """)
        st.latex(r"n = \frac{c}{v}")
        st.caption("Где c — скорость света в вакууме, v — в среде.")

with t_col2:
    with st.expander("📐 Основные определения", expanded=True):
        st.write("""
        - **Нормаль** — перпендикуляр к границе (толстая линия).
        - **Коэффициент (показатель) преломления** (n) — это безразмерная величина, определяющая, во сколько раз скорость света в вакууме (c) выше скорости света в данной среде. (Это абсолютный коэффицент, а относительный это тоже самое, но с другими средами, не являющимися вакуумом)
        - **Угол падения (α)** — угол МЕЖДУ лучом и нормалью.
        - **Угол преломления (β)** — угол МЕЖДУ преломлённым лучом и нормалью
        - **Оптически более плотная среда** — среда с большим значением **n**.
        - **Принцип Ферма** - (физический смысл закона Снеллуиса) путь, который потребует минимум времени для прохождения между двумя точками. Чтобы сэкономить время в среде, где скорость ниже, свет сокращает путь в ней, «прижимаясь» к нормали.                     
        """)

with st.expander("💡 Полное внутреннее отражение (ПВО)"):
    st.write("""
    Если свет идет из среды с большим **n** в среду с меньшим **n** (например, из стекла в воздух) под большим углом, он может не преломиться, а полностью отразиться назад.(так как наступает момент, когда sin(𝛽)по формуле должен стать больше 1.)
    
    **Где это используют?**
    - В **оптоволокне** (свет «прыгает» внутри кабеля, не выходя наружу).
    - В **алмазах** (именно из-за ПВО они так ярко блестят).
    """)

# --- 6. ТЕСТ (Проверка знаний) ---
st.subheader("📝 Мини-тест")
answer = st.radio("Что произойдет с лучом, если он перейдет из воздуха (n=1) в стекло (n=1.5)?", 
                 ["Угол β станет больше угла α", "Угол β станет меньше угла α", "Луч не изменит направление"])
if st.button("Проверить"):
    if answer == "Угол β станет меньше угла α":
        st.success("Правильно! В более плотной среде луч прижимается к нормали.")
    else:
        st.error("Неверно. Попробуй изменить n2 на 1.5 в симуляции и посмотри на график.")


