import streamlit as st
import numpy as np
import plotly.graph_objects as go

# заголовок окна и разметку задаёт main.py — здесь вызывать нельзя
st.title("Лаборатория магнетизма и электродинамики")


def smooth_polyline(points, per_segment=40):
    """Сглаживает ломаную сплайном Катмулла-Рома: кривая проходит через все
    опорные точки, но без углов на стыках."""
    pts = np.asarray(points, dtype=float)
    ext = np.vstack([pts[0] + (pts[0] - pts[1]), pts, pts[-1] + (pts[-1] - pts[-2])])
    pieces = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        t = np.linspace(0, 1, per_segment, endpoint=False)[:, None]
        pieces.append(0.5 * ((2 * p1) + (-p0 + p2) * t
                             + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                             + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    pieces.append(pts[-1][None, :])
    curve = np.vstack(pieces)
    return curve[:, 0], curve[:, 1]


def trace_field_line(field, start, step, max_steps, bounds, sinks=(), sink_radius=0.2):
    """Ведёт силовую линию вдоль поля методом Рунге-Кутты 2-го порядка.

    field(x, y) возвращает (Bx, By). Точки идут строго по направлению поля,
    поэтому порядок точек в линии — это и есть направление B.
    Линия обрывается, когда упирается в «сток» (южный полюс), выходит за кадр
    или замыкается сама на себя.
    """
    x_min, x_max, y_min, y_max = bounds
    x, y = start
    xs, ys = [x], [y]
    for _ in range(max_steps):
        bx, by = field(x, y)
        norm = (bx * bx + by * by) ** 0.5
        if norm < 1e-12:
            break
        # середина шага — вторая точка схемы Рунге-Кутты
        bx, by = field(x + step * bx / norm * 0.5, y + step * by / norm * 0.5)
        norm = (bx * bx + by * by) ** 0.5
        if norm < 1e-12:
            break
        x += step * bx / norm
        y += step * by / norm
        xs.append(x)
        ys.append(y)
        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            break
        for sx, sy in sinks:
            if (x - sx) ** 2 + (y - sy) ** 2 < sink_radius ** 2:
                return xs, ys
        if len(xs) > 30 and (x - start[0]) ** 2 + (y - start[1]) ** 2 < (step * 1.5) ** 2:
            return xs, ys          # линия замкнулась
    return xs, ys

# Создаем под-вкладки внутри модуля для удобства
mag_tabs = st.tabs(["Взаимодействие магнитов", "✋ Правила левой и правой руки", "Правило Ленца"])

# =====================================================================
# БЛОК 1: ПОЛОСОВЫЕ МАГНИТЫ (ФИЗИЧЕСКИ КОРРЕКТНЫЕ ЛИНИИ ПОЛЯ)
# =====================================================================
with mag_tabs[0]:
    st.subheader("1. Полосовые магниты: Направление линий поля (от N к S)")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Управление полюсами")
        
        # Переключатели полярности
        m1_pos = st.radio("Магнит 1 (Слева):", ["N — S (Север справа)", "S — N (Юг справа)"], key="m1_polar")
        m2_pos = st.radio("Магнит 2 (Справа):", ["S — N (Юг слева)", "N — S (Север слева)"], key="m2_polar")
        
        distance = st.slider("Расстояние", 1.8, 4.5, 2.8, step=0.1, key="mag_dist_slider")
        
        # Определяем точные координаты центров и краев полюсов
        # Магнит 1 закреплен слева (центр в x = -1.0)
        x1_center = -1.0
        if m1_pos == "N — S (Север справа)":
            m1_N_x, m1_S_x = 0.0, -2.0  # Координаты торцов N и S
            m1_right_is_N = True
        else:
            m1_S_x, m1_N_x = 0.0, -2.0
            m1_right_is_N = False
            
        # Магнит 2 сдвигается слайдером (центр в x = distance + 1.0)
        x2_center = distance + 1.0
        if m2_pos == "S — N (Юг слева)":
            m2_S_x, m2_N_x = distance, distance + 2.0
            m2_left_is_S = True
        else:
            m2_N_x, m2_S_x = distance, distance + 2.0
            m2_left_is_S = False

        # Определение режима для вывода текста
        if m1_right_is_N == m2_left_is_S:
            st.success("🟢 **Режим: Притяжение**")
            mode = "Притяжение"
        else:
            st.warning("🟠 **Режим: Отталкивание**")
            mode = "Отталкивание"
        
    with c2:
        fig1 = go.Figure()
        h = 0.4  # Высота брусков магнитов
        
        # --- ОТРИСОВКА КОРПУСА МАГНИТА 1 (СЛЕВА) ---
        if m1_right_is_N:
            fig1.add_shape(type="rect", x0=-2.0, y0=-h/2, x1=-1.0, y1=h/2, fillcolor="red", line=dict(color="white"))
            fig1.add_annotation(x=-1.5, y=0, text="<b>S</b>", showarrow=False, font=dict(color="white", size=16))
            fig1.add_shape(type="rect", x0=-1.0, y0=-h/2, x1=0.0, y1=h/2, fillcolor="blue", line=dict(color="white"))
            fig1.add_annotation(x=-0.5, y=0, text="<b>N</b>", showarrow=False, font=dict(color="white", size=16))
        else:
            fig1.add_shape(type="rect", x0=-2.0, y0=-h/2, x1=-1.0, y1=h/2, fillcolor="blue", line=dict(color="white"))
            fig1.add_annotation(x=-1.5, y=0, text="<b>N</b>", showarrow=False, font=dict(color="white", size=16))
            fig1.add_shape(type="rect", x0=-1.0, y0=-h/2, x1=0.0, y1=h/2, fillcolor="red", line=dict(color="white"))
            fig1.add_annotation(x=-0.5, y=0, text="<b>S</b>", showarrow=False, font=dict(color="white", size=16))
            
        # --- ОТРИСОВКА КОРПУСА МАГНИТА 2 (СПРАВА) ---
        if m2_left_is_S:
            fig1.add_shape(type="rect", x0=distance, y0=-h/2, x1=distance+1.0, y1=h/2, fillcolor="red", line=dict(color="white"))
            fig1.add_annotation(x=distance+0.5, y=0, text="<b>S</b>", showarrow=False, font=dict(color="white", size=16))
            fig1.add_shape(type="rect", x0=distance+1.0, y0=-h/2, x1=distance+2.0, y1=h/2, fillcolor="blue", line=dict(color="white"))
            fig1.add_annotation(x=distance+1.5, y=0, text="<b>N</b>", showarrow=False, font=dict(color="white", size=16))
        else:
            fig1.add_shape(type="rect", x0=distance, y0=-h/2, x1=distance+1.0, y1=h/2, fillcolor="blue", line=dict(color="white"))
            fig1.add_annotation(x=distance+0.5, y=0, text="<b>N</b>", showarrow=False, font=dict(color="white", size=16))
            fig1.add_shape(type="rect", x0=distance+1.0, y0=-h/2, x1=distance+2.0, y1=h/2, fillcolor="red", line=dict(color="white"))
            fig1.add_annotation(x=distance+1.5, y=0, text="<b>S</b>", showarrow=False, font=dict(color="white", size=16))

        # --- ГЕНЕРАЦИЯ ЛИНИЙ: СТРОГО ИЗ N В S ---
        if mode == "Притяжение":
            start_x = m1_N_x if m1_right_is_N else m2_N_x
            end_x = m2_S_x if m2_left_is_S else m1_S_x
            
            y_offsets = [0.0, 0.15, 0.3, -0.15, -0.3]
            arrow_dir = "▶" if start_x < end_x else "◀"
            for idx, yo in enumerate(y_offsets):
                x_line = np.linspace(start_x, end_x, 50)
                y_line = yo * (1 + 0.4 * np.sin(np.pi * (x_line - start_x) / (end_x - start_x)))

                fig1.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines", line=dict(color="cyan", width=2, dash="dash"), showlegend=False))

                # Стрелку каждой линии сдвигаем вдоль неё на свою долю пути и
                # сажаем точно на линию: раньше все пять стояли на одной
                # вертикали и слипались в сплошное пятно.
                frac = 0.34 + 0.08 * idx
                x_arrow = start_x + (end_x - start_x) * frac
                y_arrow = yo * (1 + 0.4 * np.sin(np.pi * frac))
                fig1.add_annotation(x=x_arrow, y=y_arrow, text=arrow_dir, showarrow=False,
                                    font=dict(color="cyan", size=12))
        
        else:
            # Режим ОТТАЛКИВАНИЯ
            x_mid = distance / 2
            y_offsets = [0.1, 0.25, -0.1, -0.25]
            
            # 1. Линии у ближних полюсов
            for idx, yo in enumerate(y_offsets):
                # доля пути своя у каждой линии — иначе стрелки встают стопкой
                frac = 0.30 + 0.12 * idx
                x_arr_l = x_mid * frac
                x_arr_r = distance - x_mid * frac
                y_arr = yo + np.sign(yo) * 1.5 * frac ** 3
                if m1_right_is_N:
                    x_l = np.linspace(0.0, x_mid - 0.1, 30)
                    y_l = yo + (np.sign(yo) * 1.5 * (x_l / x_mid)**3)
                    fig1.add_trace(go.Scatter(x=x_l, y=y_l, mode="lines", line=dict(color="cyan", width=2, dash="dash"), showlegend=False))
                    fig1.add_annotation(x=x_arr_l, y=y_arr, text="▶", showarrow=False, font=dict(color="cyan", size=12))
                    
                    x_r = np.linspace(x_mid + 0.1, distance, 30)
                    y_r = yo + (np.sign(yo) * 1.5 * ((distance - x_r) / x_mid)**3)
                    fig1.add_trace(go.Scatter(x=x_r, y=y_r, mode="lines", line=dict(color="cyan", width=2, dash="dash"), showlegend=False))
                    fig1.add_annotation(x=x_arr_r, y=y_arr, text="◀", showarrow=False, font=dict(color="cyan", size=12))
                else:
                    x_l = np.linspace(0.0, x_mid - 0.1, 30)
                    y_l = yo + (np.sign(yo) * 1.5 * (x_l / x_mid)**3)
                    fig1.add_trace(go.Scatter(x=x_l, y=y_l, mode="lines", line=dict(color="cyan", width=2, dash="dash"), showlegend=False))
                    fig1.add_annotation(x=x_arr_l, y=y_arr, text="◀", showarrow=False, font=dict(color="cyan", size=12))
                    
                    x_r = np.linspace(x_mid + 0.1, distance, 30)
                    y_r = yo + (np.sign(yo) * 1.5 * ((distance - x_r) / x_mid)**3)
                    fig1.add_trace(go.Scatter(x=x_r, y=y_r, mode="lines", line=dict(color="cyan", width=2, dash="dash"), showlegend=False))
                    fig1.add_annotation(x=x_arr_r, y=y_arr, text="▶", showarrow=False, font=dict(color="cyan", size=12))

            # 2. Линии у внешних краев
            for edge_start, edge_end, arrow in [(-2.0, 0.0, "▶"), (distance+2.0, distance, "◀")]:
                if (edge_start == -2.0 and not m1_right_is_N) or (edge_start == distance+2.0 and m2_left_is_S):
                    for loop_h in [0.6, 1.0]:
                        x_loop = np.linspace(edge_start, edge_end, 40)
                        y_loop = loop_h * np.sin(np.pi * (x_loop - edge_start) / (edge_end - edge_start))
                        fig1.add_trace(go.Scatter(x=x_loop, y=y_loop, mode="lines", line=dict(color="cyan", width=1.5, dash="dash"), showlegend=False))
                        fig1.add_trace(go.Scatter(x=x_loop, y=-y_loop, mode="lines", line=dict(color="cyan", width=1.5, dash="dash"), showlegend=False))
                        fig1.add_annotation(x=(edge_start+edge_end)/2, y=loop_h, text=arrow, showarrow=False, font=dict(color="cyan", size=10))
                        fig1.add_annotation(x=(edge_start+edge_end)/2, y=-loop_h, text=arrow, showarrow=False, font=dict(color="cyan", size=10))
            
            st.write("***Примечание: линии выглядят неполными, но все линии магнитного поля всегда выходят из северного полюса***")

        # Настройки отображения осей и вывод графика
        fig1.update_layout(
            template="plotly_dark", height=420,
            xaxis=dict(range=[-3.0, 7.0], visible=False, fixedrange=True),
            yaxis=dict(range=[-1.8, 1.8], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig1, width="stretch", key="physical_direction_magnets")



# =====================================================================
# БЛОК 2: ПРАВИЛА ЛЕВОЙ И ПРАВОЙ РУКИ
# =====================================================================
with mag_tabs[1]:
    st.subheader("2. Интерактивный тренажер правил рук")
    
    hand_mode = st.selectbox("Что изучаем?", ["Правило ЛЕВОЙ руки (Сила Ампера)",
                                              "Правило ПРАВОЙ руки (Магнитное поле прямого проводника с током)",
                                              "Правило ПРАВОЙ руки (Соленоид — катушка с током)"])
    
    c3, c4 = st.columns([1, 1.5])
    
    with c3:
        if "ЛЕВОЙ" in hand_mode:
            st.markdown("### 🫲 Правило левой руки")
            st.write("**Если расположить левую руку так, чтобы линии магнитного поля входили в ладонь, а четыре вытянутых пальца показывали направление тока, то отогнутый на 90° большой палец покажет направление силы Ампера**.")
            st.write("Используется для определения направления **Силы Ампера ($F_A$)**, действующей на проводник с током в магнитном поле.")
            
            # Интерактивные селекторы
            b_dir = st.radio("Направление магнитного поля (B):", ["Сверху вниз (N сверху, S снизу)", "Снизу вверх (S сверху, N снизу)"])
            i_dir = st.radio("Направление тока в проводнике (I):", ["Вправо", "Влево"])
            
            # Логика правила левой руки:
            # Поле входит в ладонь, 4 пальца по току, большой отогнутый палец показывает Силу.
            if (b_dir.startswith("Сверху") and i_dir == "Вправо") or (b_dir.startswith("Снизу") and i_dir == "Влево"):
                force_res = "ОТ ВАС (вглубь экрана ⊗)"
                force_arrow = "⊗"
            else:
                force_res = "НА ВАС (из экрана ⊙)"
                force_arrow = "⊙"
                
            st.success(f"⚖️ **Результат:** Сила Ампера направлена: {force_res}")
            
        elif "оленоид" in hand_mode:
            st.markdown("### 🫱 Правило правой руки для соленоида")
            st.write("**Если обхватить соленоид правой рукой так, чтобы четыре пальца смотрели по направлению тока в витках, то отогнутый большой палец укажет направление линий поля внутри катушки — то есть на её северный полюс**.")
            st.info("У соленоида руки как бы меняются ролями по сравнению с прямым проводом: там большой палец был током, а согнутые пальцы — полем. Здесь наоборот: пальцы — ток, большой палец — поле.")

            sol_dir = st.radio(
                "Ток на ближней к нам стороне витков:",
                ["Течёт вверх", "Течёт вниз"],
                key="solenoid_current"
            )

            # Та же геометрия, что во вкладке Ленца: ближняя к зрителю сторона витка —
            # правая. Ток вверх на ней означает поле внутри катушки налево.
            sol_up = sol_dir.startswith("Течёт вверх")
            sol_b_dir = -1 if sol_up else 1          # +1 — поле внутри смотрит вправо
            sol_north = "слева" if sol_b_dir < 0 else "справа"
            sol_south = "справа" if sol_b_dir < 0 else "слева"

            st.success(f"🧲 **Результат:** поле внутри катушки направлено "
                       f"**{'влево' if sol_b_dir < 0 else 'вправо'}**, значит "
                       f"**северный полюс {sol_north}**, южный — {sol_south}.")
            st.caption("Снаружи катушка ведёт себя точно как полосовой магнит: "
                       "линии выходят из северного полюса и входят в южный.")

        else:
            st.markdown("### 🫱 Правило правой руки (буравчика)")
            st.write("**Если обхватить проводник правой рукой, направив отогнутый большой палец по направлению тока, то согнутые пальцы покажут направление силовых линий магнитного поля**.")
            st.write("Используется для определения направления **Магнитных линий ($B$)** вокруг прямого проводника с током.")
            
            i_dir = st.radio("Направление тока в проводнике (I):", ["Вверх", "Вниз"])
            
            # Логика правила правой руки:
            # Большой палец по току, 4 согнутых пальца показывают направление линий поля.
            if i_dir == "Вверх":
                field_res = "**Справа от провода — от нас ⊗, слева — на нас ⊙.** Если смотреть на провод сверху, то есть вдоль тока на себя, линии идут против часовой стрелки."
            else:
                field_res = "**Справа от провода — на нас ⊙, слева — от нас ⊗.** Если смотреть на провод сверху, линии идут по часовой стрелке."
                
            st.success(f"🔄 **Результат:** Магнитные линии закручены: {field_res}")
    with c4:
        # Визуализация правил рук через простую 2D схему векторных стрелок
        fig2 = go.Figure()
        
        if "ЛЕВОЙ" in hand_mode:
            # Рисуем полюса магнитов, создающих поле B
            # Верхний полюс
            v_color = "blue" if b_dir.startswith("Сверху") else "red"
            v_text = "<b>N</b>" if b_dir.startswith("Сверху") else "<b>S</b>"
            fig2.add_shape(type="rect", x0=-1.5, y0=1.0, x1=1.5, y1=1.4, fillcolor=v_color, line=dict(color="white"))
            fig2.add_annotation(x=0, y=1.2, text=v_text, showarrow=False, font=dict(color="white", size=14))
            
            # Нижний полюс
            n_color = "red" if b_dir.startswith("Сверху") else "blue"
            n_text = "<b>S</b>" if b_dir.startswith("Сверху") else "<b>N</b>"
            fig2.add_shape(type="rect", x0=-1.5, y0=-1.4, x1=1.5, y1=-1.0, fillcolor=n_color, line=dict(color="white"))
            fig2.add_annotation(x=0, y=-1.2, text=n_text, showarrow=False, font=dict(color="white", size=14))
            
            # Стрелки магнитного поля B
            y_b = np.linspace(0.8, -0.8, 5) if b_dir.startswith("Сверху") else np.linspace(-0.8, 0.8, 5)
            for yb in y_b:
                fig2.add_annotation(x=-1.0, y=yb, text="↓" if b_dir.startswith("Сверху") else "↑", showarrow=False, font=dict(color="cyan", size=20))
                fig2.add_annotation(x=1.0, y=yb, text="↓" if b_dir.startswith("Сверху") else "↑", showarrow=False, font=dict(color="cyan", size=20))
            # подпись поля уводим выше проводника: на самой оси её наполовину
            # закрывала серая полоса провода
            fig2.add_annotation(x=1.45, y=0.5, text="<b>B</b>", showarrow=False, font=dict(color="cyan", size=16))

            # Проводник с током I (горизонтальная линия)
            fig2.add_shape(type="line", x0=-2.0, y0=0, x1=2.0, y1=0, line=dict(color="silver", width=6))
            i_arrow = "▶ ▶ ▶" if i_dir == "Вправо" else "◀ ◀ ◀"
            fig2.add_annotation(x=0, y=0.15, text=f"{i_arrow} <b>I (Ток)</b>", showarrow=False, font=dict(color="silver", size=14))
                        # Сила Ампера по центру
            # F с индексом A, а не «F_A»: подчёркивание — это запись из кода,
            # в учебнике сила Ампера пишется буквой F с маленькой A внизу
            fig2.add_annotation(x=0, y=-0.35, text=f"{force_arrow} F<sub>A</sub>", showarrow=False,
                                font=dict(color="orange", size=20))
            
        elif "оленоид" in hand_mode:
            # --- катушка: витки нарисованы как кольца, ближняя сторона светлее ---
            coil_rx, coil_ry = 0.17, 0.85
            coil_xs = np.linspace(-1.05, 1.05, 6)

            for cx in coil_xs:                      # дальние половинки витков
                t_far = np.linspace(np.pi, 2 * np.pi, 40)
                fig2.add_trace(go.Scatter(x=cx + coil_rx * np.sin(t_far), y=coil_ry * np.cos(t_far),
                                          mode="lines", line=dict(color="dimgray", width=2),
                                          showlegend=False))

            # --- поле внутри катушки: длинная стрелка вдоль оси ---
            fig2.add_annotation(x=1.25 * sol_b_dir, y=0, ax=-1.25 * sol_b_dir, ay=0,
                                xref="x", yref="y", axref="x", ayref="y",
                                showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=3,
                                arrowcolor="cyan")
            fig2.add_annotation(x=0, y=0.22, text="<b>B внутри</b>", showarrow=False,
                                font=dict(color="cyan", size=13))

            for cx in coil_xs:                      # ближние половинки — поверх поля
                t_near = np.linspace(0, np.pi, 40)
                fig2.add_trace(go.Scatter(x=cx + coil_rx * np.sin(t_near), y=coil_ry * np.cos(t_near),
                                          mode="lines", line=dict(color="silver", width=4),
                                          showlegend=False))
                # стрелка тока на ближней стороне витка
                y0, y1 = (0.35, 0.75) if sol_up else (0.75, 0.35)
                fig2.add_annotation(x=cx + coil_rx * 0.8, y=y1, ax=cx + coil_rx * 0.8, ay=y0,
                                    xref="x", yref="y", axref="x", ayref="y",
                                    showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=2.5,
                                    arrowcolor="darkorange")
            fig2.add_annotation(x=1.55, y=0.62, text="<b>I</b>", showarrow=False,
                                font=dict(color="darkorange", size=14))

            # --- полюса катушки ---
            north_x = -1.45 if sol_b_dir < 0 else 1.45
            south_x = -north_x
            fig2.add_annotation(x=north_x, y=0, text="<b>N</b>", showarrow=False,
                                font=dict(color="royalblue", size=20))
            fig2.add_annotation(x=south_x, y=0, text="<b>S</b>", showarrow=False,
                                font=dict(color="crimson", size=20))

            # --- линии поля снаружи: из N в S, как у полосового магнита ---
            for side_sign in (1, -1):
                knots = [
                    (-1.15, side_sign * 0.06),
                    (-1.8, side_sign * 0.55),
                    (-1.0, side_sign * 1.25),
                    (0.0, side_sign * 1.45),
                    (1.0, side_sign * 1.25),
                    (1.8, side_sign * 0.55),
                    (1.15, side_sign * 0.06),
                ]
                if sol_b_dir > 0:                   # север справа — линии идут в другую сторону
                    knots = knots[::-1]
                x_out, y_out = smooth_polyline(knots)
                fig2.add_trace(go.Scatter(x=x_out, y=y_out, mode="lines",
                                          line=dict(color="seagreen", width=1.4), showlegend=False))
                for frac in (0.25, 0.6):
                    i = int(len(x_out) * frac)
                    fig2.add_annotation(x=x_out[i], y=y_out[i], ax=x_out[i - 3], ay=y_out[i - 3],
                                        xref="x", yref="y", axref="x", ayref="y",
                                        showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=1.5,
                                        arrowcolor="seagreen")

            fig2.add_annotation(x=0, y=-1.28, text="ближняя к нам сторона витков — правая",
                                showarrow=False, font=dict(color="silver", size=10))

        else: 
            # Визуализация правила правой руки
            # Проводник с током (вертикальный столб)
            fig2.add_shape(type="rect", x0=-0.1, y0=-1.5, x1=0.1, y1=1.5, fillcolor="silver", line=dict(color="white"))
            i_tip, i_tail = (1.3, -1.3) if i_dir == "Вверх" else (-1.3, 1.3)
            fig2.add_annotation(x=0.0, y=i_tip, ax=0.0, ay=i_tail,
                                xref="x", yref="y", axref="x", ayref="y",
                                showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=4,
                                arrowcolor="darkorange")
            fig2.add_annotation(x=0.32, y=1.1, text="<b>I</b>", showarrow=False,
                                font=dict(color="darkorange", size=15))
            
            # Магнитные кольца поля вокруг проводника (вид сбоку в разрезе)
            # Слева от проводника
            left_sym = "⊙" if i_dir == "Вверх" else "⊗"
            fig2.add_annotation(x=-1.0, y=0, text=f"{left_sym} B", showarrow=False,
                                font=dict(color="cyan", size=20))
            
            # Справа от проводника
            right_sym = "⊗" if i_dir == "Вверх" else "⊙"
            fig2.add_annotation(x=1.0, y=0, text=f"{right_sym} B", showarrow=False,
                                font=dict(color="cyan", size=20))
            
        # Добавим подписи для школьников
        st.info("ℹ️ Обозначения: ⊙ — вектор направлен на нас (из экрана), ⊗ — вектор направлен от нас (внутрь экрана).")

        fig2.update_layout(
            template="plotly_dark", height=400,
            xaxis=dict(range=[-2.5, 2.5], visible=False, fixedrange=True),
            yaxis=dict(range=[-1.6, 1.6], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        
        st.plotly_chart(fig2, width="stretch", key="hand_rules")
        if "ЛЕВОЙ" in hand_mode:
            st.write("**Примечание:** левая рука отвечает на вопрос про силу: есть внешнее поле и есть ток в проводнике — куда его потянет. "
                     "А поле вокруг самого проводника ищут правой рукой, это другая задача.")
        elif "оленоид" in hand_mode:
            st.write("**Можно ли тут левой рукой?** Нет. Полюса катушки определяет только правая рука: "
                     "связь «ток → его поле» всегда правая, левая дала бы зеркальный, то есть неверный ответ. "
                     "Левая рука нужна соленоиду в другой задаче — когда он сам попал во внешнее магнитное поле "
                     "и надо понять, куда его потянет: тогда на каждый виток действует сила Ампера, и её ищут левой рукой.")
        else:
            st.write("**Примечание:** правило работает в обе стороны, и всегда правой рукой. "
                     "Известен ток — согнутые пальцы дают линии поля. Известны линии поля — согни пальцы по линиям, "
                     "и отогнутый большой палец покажет направление тока. "
                     "Менять правую руку на левую нельзя: она даст зеркальное, то есть противоположное направление.")
    
with mag_tabs[2]:
    c5, c6 = st.columns([1, 1.5])

    with c5:
        st.header('3. Правило Ленца (связь магнита и индукционного тока)')
        st.markdown("""
        **Правило Ленца:** 
        Индукционный ток всегда имеет такое направление, что его собственное магнитное поле противодействует тому изменению, которое его вызвало.
        * **Приближение:** Контур создаёт *встречное* поле **отталкивание**.
        * **Удаление:** Контур создаёт *попутное* поле **притяжение**.
        """)

        magnet_pole = st.radio(
            "Полюс магнита, направленный к кольцу:",
            ['Северный (N) — Синий', 'Южный (S) — Красный'],
            key="lenz_pole_selection"
        )

        last_magnet = st.radio(
            "Действия с магнитом:",
            ['Вдвигаем магнит в кольцо', 'Выдвигаем магнит из кольца', 'Магнит неподвижен'],
            key="lenz_action_selection"
        )

        mag_dist_max = 3.5
        mag_distance = st.slider(
            "Расстояние от магнита до кольца:", 
            min_value=1.0, max_value=mag_dist_max, value=2.8, step=0.1,
            key="lenz_range_slider"
        )

        mag_zoom = st.slider(
            "Масштаб рисунка:",
            min_value=0.5, max_value=2.5, value=1.0, step=0.1,
            key="lenz_zoom_slider",
            help="1.0 — вся сцена целиком; больше — ближе к кольцу, меньше — дальше"
        )

        # =====================================================================
        # ФИЗИКА: ОДИН РАСЧЁТ НА ВСЮ ВКЛАДКУ
        # Ток и поле кольца выводятся из одной величины b_ind_dir, поэтому
        # разойтись между собой они больше не могут.
        # =====================================================================
        is_N_forward = (magnet_pole == 'Северный (N) — Синий')
        magnet_moves = (last_magnet != 'Магнит неподвижен')
        approaching = (last_magnet == 'Вдвигаем магнит в кольцо')
        ring_rx, ring_ry = 0.22, 1.1          # полуоси кольца на рисунке сбоку

        # Поле магнита в том месте, где стоит кольцо (+1 — вправо, -1 — влево).
        # Кольцо справа от магнита: линии выходят из N и входят в S.
        b_ext_dir = 1 if is_N_forward else -1

        # Правило Ленца: приближаем — поток растёт, кольцо отвечает встречным
        # полем; удаляем — поток убывает, кольцо отвечает попутным. Стоит на
        # месте — поток не меняется, тока нет совсем, и поля у кольца тоже нет.
        b_ind_dir = (-b_ext_dir if approaching else b_ext_dir) if magnet_moves else 0

        # =====================================================================
        # ВЕЛИЧИНА ТОКА. Ток пропорционален скорости изменения потока: I ~ |dФ/dt|.
        # Скорость магнита в симуляторе одна и та же, поэтому всё решает то, как
        # круто меняется поток по пути, то есть расстояние до кольца.
        # Поток магнита сквозь кольцо радиуса R с расстояния d по оси (магнит
        # считаем диполем): Ф(d) = m R² / (2 (R² + d²)^1.5), отсюда
        #     |dФ/dd| = 1.5 m R² d / (R² + d²)^2.5
        # Постоянные (момент магнита, сопротивление кольца) в симуляторе роли не
        # играют — важно лишь, во сколько раз ток больше или меньше. Число нигде
        # не показывается: величина видна по яркости и толщине стрелок.
        # =====================================================================
        def flux_slope(dist):
            """Насколько быстро меняется поток, если сдвинуть магнит на единицу длины."""
            return 1.5 * ring_ry ** 2 * dist / (ring_ry ** 2 + dist ** 2) ** 2.5

        # считаем от середины магнита: поле создаёт весь магнит, и в расчёте он
        # заменяется диполем, который сидит в середине, — поэтому к расстоянию до
        # торца добавляем половину его длины
        dipole_dist = mag_distance + 1.0
        current_raw = flux_slope(dipole_dist) if magnet_moves else 0.0
        current_top = flux_slope(1.0 + 1.0)          # магнит вплотную — самый сильный ток
        # доля от наибольшего возможного тока; корень — чтобы слабый ток всё же
        # был виден на рисунке, а не сливался с фоном
        current_level = (current_raw / current_top) ** (1 / 3) if magnet_moves else 0.0

        # Правило буравчика. Смотрим на кольцо со стороны магнита: если поле
        # кольца направлено на наблюдателя (влево, b_ind_dir < 0) — ток идёт
        # против часовой стрелки.
        current_ccw = (b_ind_dir < 0)

        # На виде сбоку ближняя к зрителю половина кольца — правая.
        # Ток против часовой (взгляд со стороны магнита) — на ближней стенке вверх.
        near_wall_up = current_ccw
        far_wall_up = not current_ccw

        st.divider()
        if not magnet_moves:
            st.info("⚪ **Тока нет** — поток сквозь кольцо не меняется, и кольцу нечем"
                    " действовать на магнит")
        elif approaching:
            st.warning("🟠 **Кольцо отталкивает магнит** — мешает потоку усиливаться")
        else:
            st.success("🟢 **Кольцо притягивает магнит** — мешает потоку слабеть")

        pole_word = "N" if is_N_forward else "S"
        ext_word = "вправо, от магнита" if b_ext_dir > 0 else "влево, к магниту"
        flux_word = "усиливается" if approaching else "слабеет"
        ind_word = "влево" if b_ind_dir < 0 else "вправо"
        turn_word = "против часовой стрелки" if current_ccw else "по часовой стрелке"
        move_word = "приближается" if approaching else "удаляется"

        if not magnet_moves:
            st.markdown(f"""
            **Ход рассуждения:**
            1. К кольцу обращён полюс **{pole_word}** → поле магнита сквозь кольцо идёт **{ext_word}**.
            2. Магнит стоит на месте → поток сквозь кольцо **не меняется**.
            3. Нет изменения потока — нет ЭДС индукции, значит **тока в кольце нет**.
            4. Раз тока нет, то нет и собственного поля кольца: отталкивать или
               притягивать магнит нечем.

            Само по себе магнитное поле ток не создаёт. Ток появляется только от
            **изменения** потока — начни двигать магнит, и он сразу возникнет.
            """)
        else:
            st.markdown(f"""
            **Ход рассуждения:**
            1. К кольцу обращён полюс **{pole_word}** → поле магнита сквозь кольцо идёт **{ext_word}**.
            2. Магнит {move_word} → поток сквозь кольцо в эту же сторону **{flux_word}**.
            3. Кольцо противодействует → его собственное поле внутри направлено **{ind_word}**.
            4. По правилу буравчика ток течёт **{turn_word}**, если смотреть на кольцо со стороны магнита.
            """)

            strength_word = ("слабый" if current_level < 0.35
                             else "заметный" if current_level < 0.65 else "сильный")
            st.caption("Чем ближе магнит к кольцу, тем сильнее ток: рядом с магнитом поле "
                       "меняется резче, поэтому при том же движении поток меняется быстрее. "
                       "Сила тока видна по яркости и толщине стрелок.")

    with c6:
        fig3 = go.Figure()

        # Геометрия сцены
        magnet_right_edge = -mag_distance
        magnet_left_edge = magnet_right_edge - 2.0
        magnet_center_x = (magnet_left_edge + magnet_right_edge) / 2
        w_half = 1.0

        # =====================================================================
        # 1. ДАЛЬНЯЯ (от зрителя) ПОЛОВИНА КОЛЬЦА — левая дуга, темнее и тоньше
        # =====================================================================
        t_far = np.linspace(np.pi, 2 * np.pi, 60)
        fig3.add_trace(go.Scatter(x=ring_rx * np.sin(t_far), y=ring_ry * np.cos(t_far),
                                  mode="lines", line=dict(color="dimgray", width=3), showlegend=False))

        # =====================================================================
        # 2. КОРПУС МАГНИТА
        # =====================================================================
        left_color = "crimson" if is_N_forward else "royalblue"
        left_text = "<b>S</b>" if is_N_forward else "<b>N</b>"
        right_color = "royalblue" if is_N_forward else "crimson"
        right_text = "<b>N</b>" if is_N_forward else "<b>S</b>"

        fig3.add_shape(type="rect", x0=magnet_left_edge, y0=-0.35, x1=magnet_center_x, y1=0.35,
                       fillcolor=left_color, line=dict(color="white", width=1))
        fig3.add_annotation(x=(magnet_left_edge + magnet_center_x) / 2, y=0, text=left_text,
                            showarrow=False, font=dict(color="white", size=14))

        fig3.add_shape(type="rect", x0=magnet_center_x, y0=-0.35, x1=magnet_right_edge, y1=0.35,
                       fillcolor=right_color, line=dict(color="white", width=1))
        fig3.add_annotation(x=(magnet_center_x + magnet_right_edge) / 2, y=0, text=right_text,
                            showarrow=False, font=dict(color="white", size=14))

        if magnet_moves:
            # Скорость магнита: вправо при вдвигании, влево при выдвигании
            v_len, v_dir = 1.0, (1 if approaching else -1)
            fig3.add_annotation(x=magnet_center_x + v_dir * v_len, y=0.62,
                                ax=magnet_center_x - v_dir * v_len, ay=0.62,
                                xref="x", yref="y", axref="x", ayref="y",
                                text="<b>v</b>", font=dict(color="lightgray", size=14),
                                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=3,
                                arrowcolor="lightgray")

            # Сила, с которой кольцо действует на магнит: всегда против скорости,
            # а величиной идёт за током — нет тока, нет и силы
            f_len = 0.35 + 0.75 * current_level
            f_dir = -1 if approaching else 1
            fig3.add_annotation(x=magnet_center_x + f_dir * f_len, y=-0.62,
                                ax=magnet_center_x - f_dir * f_len, ay=-0.62,
                                xref="x", yref="y", axref="x", ayref="y",
                                text="<b>F</b>", font=dict(color="tomato", size=14),
                                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=3,
                                arrowcolor="tomato")
        else:
            fig3.add_annotation(x=magnet_center_x, y=0.62, text="магнит неподвижен",
                                showarrow=False, font=dict(color="lightgray", size=12),
                                )

        # =====================================================================
        # 3. ЛИНИИ ПОЛЯ МАГНИТА — замкнутые петли строго от N к S
        # Форма школьная: петля выходит из северного торца, огибает магнит и
        # возвращается в южный. Концы попадают точно в торцы, изломов нет.
        # =====================================================================
        if is_N_forward:
            pole_N_x, pole_S_x = magnet_right_edge, magnet_left_edge
            pole_sign = 1
        else:
            pole_N_x, pole_S_x = magnet_left_edge, magnet_right_edge
            pole_sign = -1

        def draw_field_line(x_line, y_line, color, width, arrow_fracs):
            """Рисует линию, предварительно разложив точки равномерно по длине."""
            seg = np.hypot(np.diff(x_line), np.diff(y_line))
            arc = np.concatenate(([0.0], np.cumsum(seg)))
            even = np.linspace(0, arc[-1], 240)
            x_line = np.interp(even, arc, x_line)
            y_line = np.interp(even, arc, y_line)

            fig3.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines",
                                      line=dict(color=color, width=width), showlegend=False))
            for frac in arrow_fracs:
                i = int(len(x_line) * frac)
                if i < 4 or i >= len(x_line):
                    continue
                fig3.add_annotation(x=x_line[i], y=y_line[i], ax=x_line[i - 3], ay=y_line[i - 3],
                                    xref="x", yref="y", axref="x", ayref="y",
                                    showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=1.5,
                                    arrowcolor=color)

        # Размер самой внешней петли (той, что прошивает кольцо) считаем сразу:
        # по нему строится третья линия, чтобы она оказалась ровно посередине
        # между второй и внешней — тогда четыре линии идут равномерно.
        pierce_h, pierce_edge, pierce_over = 1.75, 0.02, 0.80
        t_p = np.linspace(0, np.pi, 400)

        lo, hi = 0.0, 50.0
        for _ in range(50):
            ext_p = (lo + hi) / 2
            if (w_half * np.cos(t_p) + ext_p * np.sin(2 * t_p)).max() < mag_dist_max + 1.0 + pierce_over:
                lo = ext_p
            else:
                hi = ext_p
        ext_p = (lo + hi) / 2

        second_line = {"h": 1.00, "ext": 0.90, "y_edge": 0.10}
        line_configs = [
            {"h": 0.50, "ext": 0.35, "y_edge": 0.18},   # ближняя к магниту петля
            second_line,                                 # вторая
            {"h": (second_line["h"] + pierce_h) / 2,     # третья — среднее второй и внешней
             "ext": (second_line["ext"] + ext_p) / 2,
             "y_edge": (second_line["y_edge"] + pierce_edge) / 2},
        ]

        for side_sign in (1, -1):
            for cfg in line_configs:
                t = np.linspace(0, np.pi, 300)
                # cos(t) ведёт кривую от торца N к торцу S, sin(2t) выпускает её
                # наружу за оба торца — концы садятся точно на полюса
                x_line = magnet_center_x + pole_sign * (w_half * np.cos(t) + cfg["ext"] * np.sin(2 * t))
                y_line = side_sign * (cfg["y_edge"] + (cfg["h"] - cfg["y_edge"]) * np.sin(t))
                draw_field_line(x_line, y_line, "seagreen", 1.3, (0.3, 0.7))

        # =====================================================================
        # ЛИНИЯ, ПРОШИВАЮЩАЯ КОЛЬЦО: тот же гладкий овал, что и остальные линии,
        # и так же симметричный относительно границы полюсов. Её размер, как и у
        # остальных, от кольца не зависит: поле магнита не знает, где стоит кольцо,
        # и меняться от этого не может. Вылет посчитан один раз по самому дальнему
        # положению магнита — тогда петля перелетает плоскость кольца при любом
        # положении слайдера, а высота, на которой она проходит сквозь кольцо,
        # получается сама: ближе магнит — линия идёт у самой оси, дальше — выше.
        # =====================================================================
        for side_sign in (1, -1):
            x_line = magnet_center_x + w_half * np.cos(t_p) + ext_p * np.sin(2 * t_p)
            y_line = side_sign * (pierce_edge + (pierce_h - pierce_edge) * np.sin(t_p))
            if not is_N_forward:
                x_line, y_line = x_line[::-1], y_line[::-1]      # ход всегда от N к S
            draw_field_line(x_line, y_line, "seagreen", 1.4, (0.25, 0.55, 0.85))

        fig3.add_annotation(x=magnet_left_edge - 1.25, y=0.22, text="<b>B магнита</b>", showarrow=False,
                            font=dict(color="seagreen", size=12))
        # =====================================================================
        # 4. СОБСТВЕННОЕ ПОЛЕ КОЛЬЦА B_инд
        # Внутри кольца пустота (в отличие от корпуса магнита), поэтому линии поля
        # рисуем замкнутыми целиком: каждая проходит СКВОЗЬ кольцо вдоль его оси,
        # выходит наружу, огибает проводник и возвращается. Стрелка на внутреннем
        # участке и показывает, куда направлено поле кольца. Форма петель подобрана
        # под кадр, а направление обхода — строго из расчёта (b_ind_dir).
        # =====================================================================
        ring_loop_configs = [
            {"wide": 0.70, "tall": 0.30},   # проходит у самой стенки кольца
            {"wide": 1.12, "tall": 0.62},   # средняя
            {"wide": 1.45, "tall": 0.94},   # самая широкая, идёт близко к оси
        ]

        # Чем сильнее ток, тем ярче поле кольца и тем толще стрелки тока.
        # Нижняя граница яркости нужна, чтобы слабый ток всё же было видно.
        ring_alpha = 0.35 + 0.65 * current_level
        ring_color = f"rgba(255,0,255,{ring_alpha:.2f})"

        def draw_ring_loop(x_line, y_line):
            """Замкнутая петля B_инд со стрелками одинаковой длины."""
            seg = np.hypot(np.diff(x_line), np.diff(y_line))
            arc = np.concatenate(([0.0], np.cumsum(seg)))
            even = np.linspace(0, arc[-1], 240)
            x_even = np.interp(even, arc, x_line)
            y_even = np.interp(even, arc, y_line)
            fig3.add_trace(go.Scatter(x=x_even, y=y_even, mode="lines",
                                      line=dict(color=ring_color, width=1.5), showlegend=False))
            tail = max(2, int(240 * 0.22 / arc[-1]))          # хвост стрелки ≈ 0.22 сцены
            for frac, width in ((0.25, 1.6), (0.5, 3.0), (0.75, 1.6)):   # 0.5 — участок внутри кольца
                i = int(240 * frac)
                fig3.add_annotation(x=x_even[i], y=y_even[i],
                                    ax=x_even[i - tail], ay=y_even[i - tail],
                                    xref="x", yref="y", axref="x", ayref="y",
                                    showarrow=True, arrowhead=3, arrowsize=0.8, arrowwidth=width,
                                    arrowcolor=ring_color)

        if magnet_moves:
            for side_sign in (1, -1):
                for cfg in ring_loop_configs:
                    s = np.linspace(0, 2 * np.pi, 400)
                    # s = 0 — снаружи кольца, s = pi — внутри него; знак b_ind_dir
                    # разворачивает обход, поэтому внутри кольца линия всегда идёт по полю
                    x_line = -b_ind_dir * cfg["wide"] * np.sin(s)
                    y_line = side_sign * (ring_ry + cfg["tall"] * np.cos(s))
                    draw_ring_loop(x_line, y_line)

            fig3.add_annotation(x=1.85, y=-0.62, text="<b>B инд</b>", showarrow=False,
                                font=dict(color=ring_color, size=13))
        else:
            fig3.add_annotation(x=1.85, y=-0.62, text="поля кольца нет", showarrow=False,
                                font=dict(color="dimgray", size=12),
                                )
        # =====================================================================
        # 5. БЛИЖНЯЯ К ЗРИТЕЛЮ ПОЛОВИНА КОЛЬЦА — правая дуга, поверх всего
        # =====================================================================
        t_near = np.linspace(0, np.pi, 60)
        fig3.add_trace(go.Scatter(x=ring_rx * np.sin(t_near), y=ring_ry * np.cos(t_near),
                                  mode="lines", line=dict(color="silver", width=6), showlegend=False))

        # Ток: яркая стрелка на ближней стенке, бледная — на дальней.
        # Яркость и толщина обеих идут за величиной тока.
        near_color = f"rgba(255,140,0,{0.35 + 0.65 * current_level:.2f})"
        far_color = f"rgba(205,133,63,{0.3 + 0.6 * current_level:.2f})"
        if magnet_moves:
            near_y0, near_y1 = (0.35, 0.85) if near_wall_up else (0.85, 0.35)
            fig3.add_annotation(x=ring_rx * 0.78, y=near_y1, ax=ring_rx * 0.78, ay=near_y0,
                                xref="x", yref="y", axref="x", ayref="y",
                                showarrow=True, arrowhead=3, arrowsize=1.2,
                                arrowwidth=2.0 + 2.5 * current_level, arrowcolor=near_color)
            far_y0, far_y1 = (0.35, 0.85) if far_wall_up else (0.85, 0.35)
            fig3.add_annotation(x=-ring_rx * 0.78, y=far_y1, ax=-ring_rx * 0.78, ay=far_y0,
                                xref="x", yref="y", axref="x", ayref="y",
                                showarrow=True, arrowhead=3, arrowsize=1,
                                arrowwidth=1.2 + 1.6 * current_level, arrowcolor=far_color)
            fig3.add_annotation(x=0.85, y=0.68, text="<b>I инд</b>",
                                showarrow=False, font=dict(color=near_color, size=13),
                                )
        else:
            fig3.add_annotation(x=0.85, y=0.68, text="<b>тока нет</b>", showarrow=False,
                                font=dict(color="dimgray", size=13))

        # Какая сторона кольца ближе к зрителю — подписано прямо на рисунке.
        # Подпись стоит сбоку от своей дуги и соединена с ней выноской: ближняя
        # стенка — правая, дальняя — левая. Высота выбрана по середине кольца:
        # петли поля идут выше и ниже, а эта полоса свободна, и текст не ложится
        # поверх линий.
        # Обе подписи ставим справа от кольца: слева стоит магнит, и при близком
        # его положении подпись ложилась прямо на корпус. Выноска дальней стенки
        # проходит сквозь кольцо — это и читается как «стенка за ним».
        fig3.add_annotation(x=0.30, y=0.18, ax=1.62, ay=0.42,
                            xref="x", yref="y", axref="x", ayref="y",
                            text="ближняя", showarrow=True, arrowhead=2,
                            arrowsize=1, arrowwidth=1, arrowcolor="silver",
                            font=dict(color="silver", size=10))
        fig3.add_annotation(x=-0.30, y=-0.18, ax=1.62, ay=-0.42,
                            xref="x", yref="y", axref="x", ayref="y",
                            text="дальняя", showarrow=True, arrowhead=2,
                            arrowsize=1, arrowwidth=1, arrowcolor="dimgray",
                            font=dict(color="dimgray", size=10))

        # =====================================================================
        # КАДР. Размер сцены меняется: чем дальше магнит, тем длиннее его петли,
        # поэтому границы считаем по тому, что реально нарисовано, — тогда ничего
        # не обрезается. Слайдер масштаба приближает картинку к кольцу.
        # Сами оси остаются скрытыми: рамок и цифр зритель не видит.
        # =====================================================================
        drawn_x = [np.asarray(tr.x, dtype=float) for tr in fig3.data]
        drawn_y = [np.asarray(tr.y, dtype=float) for tr in fig3.data]
        for sh in fig3.layout.shapes:
            drawn_x.append(np.array([sh.x0, sh.x1], dtype=float))
            drawn_y.append(np.array([sh.y0, sh.y1], dtype=float))
        for ann in fig3.layout.annotations:
            drawn_x.append(np.array([ann.x], dtype=float))
            drawn_y.append(np.array([ann.y], dtype=float))
            if ann.axref == "x" and ann.ax is not None:
                drawn_x.append(np.array([ann.ax], dtype=float))
            if ann.ayref == "y" and ann.ay is not None:
                drawn_y.append(np.array([ann.ay], dtype=float))

        # Поля, чтобы подписи не липли к краю. По горизонтали шире: у боковых
        # подписей кольца («ближняя», «дальняя») кадр считается по точке, а не по
        # ширине текста, и узкого поля им не хватало — слово обрезалось краем.
        pad_x, pad_y = 1.15, 0.5
        all_x, all_y = np.concatenate(drawn_x), np.concatenate(drawn_y)
        x_lo, x_hi = all_x.min() - pad_x, all_x.max() + pad_x
        y_lo, y_hi = all_y.min() - pad_y, all_y.max() + pad_y
        # Не мельчим картинку без нужды: пока всё влезает, кадр держим прежнего
        # размера, и масштаб при движении магнита не скачет. Расширяем, только
        # когда петли магнита перестают помещаться.
        min_w, min_h = 11.0, 5.2
        if x_hi - x_lo < min_w:
            mid = (x_lo + x_hi) / 2
            x_lo, x_hi = mid - min_w / 2, mid + min_w / 2
        if y_hi - y_lo < min_h:
            mid = (y_lo + y_hi) / 2
            y_lo, y_hi = mid - min_h / 2, mid + min_h / 2

        cx, cy = (x_lo + x_hi) / 2, (y_lo + y_hi) / 2
        cx += -cx * (1 - 1 / mag_zoom)              # приближаемся — уходим к кольцу (оно в x = 0)
        half_w, half_h = (x_hi - x_lo) / 2 / mag_zoom, (y_hi - y_lo) / 2 / mag_zoom

        fig3.update_layout(
            template="plotly_dark", height=430,
            xaxis=dict(range=[cx - half_w, cx + half_w], visible=False, fixedrange=True),
            yaxis=dict(range=[cy - half_h, cy + half_h], visible=False, fixedrange=True,
                       scaleanchor="x", scaleratio=1),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig3, width="stretch", key="lenz_side_view")

        # =====================================================================
        # 6. ВТОРОЙ РАКУРС: КОЛЬЦО АНФАС СО СТОРОНЫ МАГНИТА
        # Здесь направление читается строго и без двусмысленности.
        # =====================================================================
        f_col1, f_col2 = st.columns([1, 1.2])

        with f_col1:
            fig4 = go.Figure()
            ring_r = 1.0
            t_ring = np.linspace(0, 2 * np.pi, 180)
            fig4.add_trace(go.Scatter(
                x=ring_r * np.cos(t_ring),
                y=ring_r * np.sin(t_ring),
                mode="lines",
                line=dict(color="silver", width=6),
                showlegend=False
            ))

            # Магнит стоит — тока нет, и показывать на этом виде нечего:
            # остаётся пустое кольцо и пометка, что тока нет.
            if magnet_moves:
                for ang_deg in (30, 120, 210, 300):
                    t0 = np.radians(ang_deg)
                    x0, y0 = ring_r * np.cos(t0), ring_r * np.sin(t0)

                    if current_ccw:
                        dx, dy = -np.sin(t0), np.cos(t0)
                    else:
                        dx, dy = np.sin(t0), -np.cos(t0)

                    fig4.add_annotation(
                        x=x0 + dx * 0.28, y=y0 + dy * 0.28,
                        ax=x0 - dx * 0.28, ay=y0 - dy * 0.28,
                        xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True,
                        arrowhead=3,
                        arrowsize=1.2,
                        arrowwidth=2.0 + 2.5 * current_level,
                        arrowcolor=near_color
                    )

                fig4.add_annotation(x=0, y=0.2, text="⊙" if current_ccw else "⊗", showarrow=False,
                                    font=dict(color=ring_color, size=36))
                fig4.add_annotation(x=0, y=-0.35, text="<b>B инд</b>", showarrow=False,
                                    font=dict(color=ring_color, size=13))
                fig4.add_annotation(x=0, y=-1.45,
                                    text="<b>I инд</b>: " + ("против часовой" if current_ccw else "по часовой"),
                                    showarrow=False, font=dict(color=near_color, size=13))
            else:
                fig4.add_annotation(x=0, y=-1.45, text="<b>тока нет:</b> магнит неподвижен",
                                    showarrow=False, font=dict(color="dimgray", size=13))

            fig4.add_annotation(x=0, y=1.45, text="смотрим со стороны магнита",
                                showarrow=False, font=dict(color="lightgray", size=11))

            fig4.update_layout(
                template="plotly_dark", height=260,
                xaxis=dict(range=[-1.7, 1.7], visible=False, fixedrange=True),
                yaxis=dict(range=[-1.7, 1.7], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig4, width="stretch", key="lenz_front_view")

        with f_col2:
            st.caption("**Смотрим на кольцо со стороны магнита.**")
            if not magnet_moves:
                st.markdown("""
                Магнит стоит на месте — поток сквозь кольцо не меняется, тока нет,
                и показывать здесь нечего. Начни двигать магнит — ток появится, а его
                направление будет зависеть от того, вдвигаем мы магнит или выдвигаем.
                """)
            else:
                st.markdown(f"""
                В этой проекции:
                - ток идёт **{turn_word}**;
                - поле индукционного тока направлено **{"на наблюдателя ⊙" if current_ccw else "от наблюдателя ⊗"}**;
                - это как раз и означает, что кольцо создаёт поле, противодействующее изменению потока.

                Поэтому при **приближении** магнита поле кольца направлено **навстречу** внешнему полю,
                а при **удалении** — **в ту же сторону**, что и внешнее поле.
                """)
                st.caption("⊙ — поле направлено на наблюдателя, ⊗ — от наблюдателя.")

        st.write("*Примечание*: линии магнитного поля у магнита заходят в южный полюс, даже уходя в кольцо")

    n_col, n2_col=st.columns([1,1])
    with n_col:
        with st.expander("❓ Что такое индукционный ток?", expanded=True):
            st.markdown("""
                            **Индукционный ток** отличается от постоянного тем, что он возникает только при **изменении** магнитного поля в замкнутом контуре. 
                            * **Пример:** приближение или отдаление магнита от металлического кольца.
                            * **Важно:** если магнит неподвижен — тока в кольце нет.
                            """)
    with n2_col:
        with st.expander("🧲 Что такое магнитное поле?", expanded=True):
            st.markdown(r"""
                **Магнитное поле** — это особый вид материи, который существует вокруг движущихся электрических зарядов (токов) и постоянных магнитов. Оно осуществляет магнитное взаимодействие между ними.
                * Поле графически изображают с помощью **силовых линий**.
                * Направление этих линий всегда строго **от Северного полюса (N) к Южному (S)**.
                * **Магнитный поток ($\Phi$)** — это величина, которая показывает, сколько таких силовых линий пронзает площадь замкнутого контура (например, нашего кольца).
                """)


    