import base64
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

import streamlit as st

st.set_page_config(page_title="Aventura Matemática 7°", page_icon="🧠", layout="centered")
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"

AUDIOS_ACIERTO = [f"acierto_{i}.mp3" for i in range(1, 5)]
AUDIOS_DESACIERTO = [f"desacierto_{i}.mp3" for i in range(1, 4)]
AUDIOS_INSIGNIAS = {
    "primeros_50": "insignia_1.mp3",
    "constancia": "insignia_2.mp3",
    "racha_3": "insignia_3.mp3",
    "racha_5": "insignia_4.mp3",
    "diez_ejercicios": "insignia_5.mp3",
    "detector_refuerzo": "insignia_6.mp3",
}

USUARIOS_RESPALDO = {
    "admin": {"name": "Administrador", "password": "admin123", "role": "admin"},
    "cata": {"name": "Catalina", "password": "mate123", "role": "student"},
    "estudiante": {"name": "Estudiante", "password": "practica123", "role": "student"},
}


def cargar_usuarios():
    try:
        if "users" in st.secrets:
            return dict(st.secrets["users"])
    except Exception:
        pass
    return USUARIOS_RESPALDO


def verificar_usuario(username, password):
    usuarios = cargar_usuarios()
    username = username.strip().lower()
    if username not in usuarios:
        return None
    datos = dict(usuarios[username])
    if password == str(datos.get("password", "")):
        return {"username": username, "name": str(datos.get("name", username)), "role": str(datos.get("role", "student"))}
    return None


def login():
    st.title("🔐 Aventura Matemática")
    st.caption("Acceso restringido para estudiantes autorizados.")
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        entrar = st.form_submit_button("Entrar")
    if entrar:
        usuario = verificar_usuario(username, password)
        if usuario:
            st.session_state.auth = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    with st.expander("Usuarios de prueba local"):
        st.write("admin / admin123")
        st.write("cata / mate123")
        st.write("estudiante / practica123")


def requerir_login():
    if "auth" not in st.session_state or not st.session_state.auth:
        login()
        st.stop()


def cerrar_sesion():
    for clave in list(st.session_state.keys()):
        del st.session_state[clave]
    st.rerun()


def reproducir_audio(nombre_archivo):
    ruta = ASSETS_DIR / nombre_archivo
    if not ruta.exists() or ruta.stat().st_size == 0:
        return
    try:
        audio_b64 = base64.b64encode(ruta.read_bytes()).decode()
        st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    except Exception:
        pass


def inicializar_estado():
    valores = {
        "puntaje": 0,
        "racha": 0,
        "ejercicio_actual": None,
        "respuesta_enviada": False,
        "feedback": "",
        "tema_actual": None,
        "historial": [],
        "errores_por_tema": {},
        "insignias_desbloqueadas": [],
        "audio_pendiente": None,
        "modo_examen_preguntas": [],
        "modo_examen_indice": 0,
        "modo_examen_aciertos": 0,
        "modo_examen_inicio": None,
    }
    for k, v in valores.items():
        if k not in st.session_state:
            st.session_state[k] = v


@dataclass
class Ejercicio:
    pregunta: str
    respuesta_correcta: Any
    opciones: List[Any]
    explicacion: str
    tipo: str
    dificultad: str = "Básica"


def formatear_conjunto(elementos):
    return "{" + ", ".join(str(x) for x in elementos) + "}"


def es_primo(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def opciones(*items):
    salida = list(dict.fromkeys(items))
    while len(salida) < 4:
        salida.append(random.randint(-50, 50))
    random.shuffle(salida)
    return salida[:4]


def reiniciar_ejercicio():
    st.session_state.ejercicio_actual = None
    st.session_state.respuesta_enviada = False
    st.session_state.feedback = ""


def registrar_historial(ejercicio, respuesta_usuario, correcta):
    st.session_state.historial.append({
        "usuario": st.session_state.usuario["username"],
        "tema": ejercicio.tipo,
        "pregunta": ejercicio.pregunta,
        "respuesta_usuario": respuesta_usuario,
        "respuesta_correcta": ejercicio.respuesta_correcta,
        "correcta": correcta,
    })
    if not correcta:
        st.session_state.errores_por_tema[ejercicio.tipo] = st.session_state.errores_por_tema.get(ejercicio.tipo, 0) + 1


def obtener_nuevas_insignias():
    candidatas = []
    if st.session_state.puntaje >= 50:
        candidatas.append(("primeros_50", "🌱 Primeros 50 puntos"))
    if st.session_state.puntaje >= 150:
        candidatas.append(("constancia", "📘 Constancia"))
    if st.session_state.racha >= 3:
        candidatas.append(("racha_3", "🔥 Racha x3"))
    if st.session_state.racha >= 5:
        candidatas.append(("racha_5", "⚡ Racha x5"))
    if len(st.session_state.historial) >= 10:
        candidatas.append(("diez_ejercicios", "🧠 10 ejercicios practicados"))
    if len(st.session_state.errores_por_tema) >= 3:
        candidatas.append(("detector_refuerzo", "🔎 Detector de temas por reforzar"))
    nuevas = []
    for codigo, texto in candidatas:
        if codigo not in st.session_state.insignias_desbloqueadas:
            st.session_state.insignias_desbloqueadas.append(codigo)
            nuevas.append((codigo, texto))
    return nuevas


def evaluar_respuesta(respuesta_usuario, ejercicio):
    correcta = str(respuesta_usuario).strip() == str(ejercicio.respuesta_correcta).strip()
    if correcta:
        st.session_state.puntaje += 10
        st.session_state.racha += 1
        st.session_state.feedback = random.choice(["✅ ¡Correcto!", "🌟 ¡Excelente!", "🏆 ¡Buenísimo!", "🔥 ¡Respuesta correcta!"])
    else:
        st.session_state.racha = 0
        st.session_state.feedback = f"❌ Casi. La respuesta correcta es: {ejercicio.respuesta_correcta}"
    registrar_historial(ejercicio, respuesta_usuario, correcta)
    nuevas = obtener_nuevas_insignias()
    if nuevas:
        st.session_state.audio_pendiente = AUDIOS_INSIGNIAS.get(nuevas[0][0])
    elif correcta:
        st.session_state.audio_pendiente = random.choice(AUDIOS_ACIERTO)
    else:
        st.session_state.audio_pendiente = random.choice(AUDIOS_DESACIERTO)
    st.session_state.respuesta_enviada = True


def obtener_nivel(puntaje):
    if puntaje < 50:
        return "Nivel 1: Explorador/a", "🌱"
    if puntaje < 120:
        return "Nivel 2: Aprendiz", "📘"
    if puntaje < 220:
        return "Nivel 3: Estratega", "🧩"
    if puntaje < 350:
        return "Nivel 4: Maestro/a de enteros", "⚔️"
    return "Nivel 5: Leyenda matemática", "🏆"


def insignias():
    catalogo = {
        "primeros_50": "🌱 Primeros 50 puntos",
        "constancia": "📘 Constancia",
        "racha_3": "🔥 Racha x3",
        "racha_5": "⚡ Racha x5",
        "diez_ejercicios": "🧠 10 ejercicios practicados",
        "detector_refuerzo": "🔎 Detector de temas por reforzar",
    }
    return [texto for codigo, texto in catalogo.items() if codigo in set(st.session_state.insignias_desbloqueadas)]


# Generadores

def ejercicio_naturales():
    return Ejercicio("¿Cuál símbolo representa el conjunto de los números naturales?", "ℕ", ["ℕ", "ℤ", "∅", "⊂"], "Los naturales se representan con ℕ.", "Conjuntos")


def ejercicio_extension_comprension():
    limite = random.randint(4, 9)
    resp = formatear_conjunto(range(1, limite))
    ops = [resp, formatear_conjunto(range(1, limite + 1)), formatear_conjunto(range(0, limite)), formatear_conjunto(range(2, limite))]
    random.shuffle(ops)
    return Ejercicio(f"Representa por extensión: A = {{x ∈ ℕ | 1 ≤ x < {limite}}}", resp, ops, "Se listan los naturales desde 1 hasta el número anterior al límite.", "Notación de conjuntos", "Media")


def ejercicio_operacion_conjuntos():
    U = set(range(1, 11)); A = set(random.sample(list(U), 5)); B = set(random.sample(list(U), 5)); op = random.choice(["∪", "∩", "-"])
    if op == "∪":
        res, exp = sorted(A | B), "La unión reúne elementos de A, B o ambos."
    elif op == "∩":
        res, exp = sorted(A & B), "La intersección contiene los comunes."
    else:
        res, exp = sorted(A - B), "La diferencia A-B contiene los de A que no están en B."
    resp = formatear_conjunto(res)
    ops = [resp, formatear_conjunto(sorted(B - A)), formatear_conjunto(sorted(A & B)), formatear_conjunto(sorted(U - A))]
    random.shuffle(ops)
    return Ejercicio(f"A = {formatear_conjunto(sorted(A))}, B = {formatear_conjunto(sorted(B))}. Calcula A {op} B.", resp, ops[:4], exp, "Operaciones con conjuntos", "Media")


def ejercicio_complemento():
    U = set(range(1, 11)); A = set(random.sample(list(U), random.randint(3, 6))); resp = formatear_conjunto(sorted(U - A))
    ops = [resp, formatear_conjunto(sorted(A)), formatear_conjunto(sorted(U)), formatear_conjunto(sorted(random.sample(list(U), 5)))]
    random.shuffle(ops)
    return Ejercicio(f"Si U = {formatear_conjunto(sorted(U))} y A = {formatear_conjunto(sorted(A))}, calcula el complemento de A.", resp, ops, "El complemento son los elementos del universo que no están en A.", "Operaciones con conjuntos", "Media")


def ejercicio_pertenencia_inclusion():
    A = set(random.sample(range(1, 10), 5)); e = random.choice(list(A)) if random.random() > .4 else random.randint(10, 15); resp = "∈" if e in A else "∉"
    return Ejercicio(f"Completa: {e} ___ A, donde A = {formatear_conjunto(sorted(A))}", resp, ["∈", "∉", "⊂", "⊄"], "∈ se usa cuando un elemento pertenece a un conjunto.", "Pertenencia e inclusión")


def ejercicio_inclusion_subconjunto():
    A = set(random.sample(range(1, 10), 5)); B = set(random.sample(list(A), 3)) if random.random() > .35 else set(random.sample(range(10, 16), 3)); resp = "⊂" if B.issubset(A) else "⊄"
    return Ejercicio(f"Completa: B ___ A, donde A = {formatear_conjunto(sorted(A))} y B = {formatear_conjunto(sorted(B))}", resp, ["∈", "∉", "⊂", "⊄"], "La inclusión compara conjunto con conjunto.", "Pertenencia e inclusión", "Media")


def ejercicio_pares_impares():
    n = random.randint(1, 40); resp = "par" if n % 2 == 0 else "impar"
    return Ejercicio(f"El número {n} es...", resp, ["par", "impar", "primo", "compuesto"], "Un par es divisible entre 2; si no, es impar.", "Pares e impares")


def ejercicio_primos_compuestos():
    n = random.choice([2,3,4,5,6,7,8,9,10,11,12,13,15,17,19,21,25]); resp = "primo" if es_primo(n) else "compuesto"
    return Ejercicio(f"El número {n} es...", resp, ["primo", "compuesto", "par", "impar"], "Un primo tiene exactamente dos divisores positivos: 1 y él mismo.", "Primos y compuestos")


def ejercicio_multiplos_divisores():
    a = random.randint(2, 9); b = a * random.randint(2, 6) if random.random() > .5 else random.randint(10, 50); resp = "sí" if b % a == 0 else "no"
    return Ejercicio(f"¿{b} es múltiplo de {a}?", resp, ["sí", "no", "solo si es par", "no se puede saber"], f"Es múltiplo si al dividir entre {a} el residuo es cero.", "Múltiplos y divisores", "Media")


def ejercicio_valor_absoluto():
    n = random.randint(-15, 15); resp = abs(n)
    return Ejercicio(f"Calcula |{n}|", resp, opciones(resp, -resp, n, abs(n)+1), "El valor absoluto es la distancia al cero.", "Números enteros")


def ejercicio_opuesto():
    n = random.choice([x for x in range(-15, 16) if x != 0]); resp = -n
    return Ejercicio(f"¿Cuál es el opuesto de {n}?", resp, opciones(resp, n, abs(n), -abs(n)), "El opuesto cambia el signo.", "Números enteros")


def ejercicio_comparacion_enteros():
    a = random.randint(-12, 12); b = random.randint(-12, 12)
    while a == b: b = random.randint(-12, 12)
    resp = ">" if a > b else "<"
    return Ejercicio(f"Completa: {a} ___ {b}", resp, [">", "<", "≥", "≤"], "En la recta numérica, el de la derecha es mayor.", "Números enteros")


def ejercicio_operaciones_enteros():
    a = random.randint(-12, 12); b = random.choice([x for x in range(-12, 13) if x != 0]); op = random.choice(["+", "-", "×", "÷"])
    if op == "+": resp = a + b
    elif op == "-": resp = a - b
    elif op == "×": resp = a * b
    else:
        resp = random.randint(-10, 10); a = resp * b
    return Ejercicio(f"Resuelve: {a} {op} {b}", resp, opciones(resp, -resp, resp+1, resp-1), "Suma/resta: ganancias y deudas. Multiplicación/división: ley de signos.", "Operaciones con enteros", "Media")


def ejercicio_operacion_combinada():
    a = random.randint(-8, 8); b = random.randint(-8, 8); c = random.choice([x for x in range(-6, 7) if x != 0]); resp = abs(a) + b * c
    return Ejercicio(f"Resuelve: |{a}| + ({b}) × ({c})", resp, opciones(resp, -resp, abs(a)+b+c, abs(a)-b*c), "Primero valor absoluto, luego multiplicación y finalmente suma.", "Operaciones combinadas", "Alta")


def ejercicio_potencia():
    base = random.randint(-5,5) or 2; exp = random.randint(2,4); resp = base ** exp
    return Ejercicio(f"Calcula: ({base})^{exp}", resp, opciones(resp, -(abs(base)**exp), abs(base)**exp, base*exp), "Con base negativa entre paréntesis, el signo depende de si el exponente es par o impar.", "Potencias", "Media")


def ejercicio_propiedades_potencias():
    base = random.randint(2,5); m = random.randint(2,5); n = random.randint(1,4); mult = random.random() > .5
    if mult:
        resp = f"{base}^{m+n}"; pregunta = f"Simplifica: {base}^{m} × {base}^{n}"; exp = "Igual base multiplicando: se suman exponentes."; dist = [f"{base}^{m*n}", f"{base}^{m-n}", f"{base*m}^{n}"]
    else:
        if m <= n: m, n = n+2, m
        resp = f"{base}^{m-n}"; pregunta = f"Simplifica: {base}^{m} ÷ {base}^{n}"; exp = "Igual base dividiendo: se restan exponentes."; dist = [f"{base}^{m+n}", f"{base}^{m*n}", f"{base-n}^{m}"]
    ops = dist + [resp]; random.shuffle(ops)
    return Ejercicio(pregunta, resp, ops, exp, "Propiedades de potencias", "Alta")


GENERADORES: Dict[str, List[Callable[[], Ejercicio]]] = {
    "🧩 Conjuntos": [ejercicio_naturales, ejercicio_extension_comprension, ejercicio_operacion_conjuntos, ejercicio_complemento, ejercicio_pertenencia_inclusion, ejercicio_inclusion_subconjunto, ejercicio_pares_impares, ejercicio_primos_compuestos, ejercicio_multiplos_divisores],
    "🧭 Números enteros": [ejercicio_valor_absoluto, ejercicio_opuesto, ejercicio_comparacion_enteros],
    "⚔️ Operaciones con enteros": [ejercicio_operaciones_enteros, ejercicio_operacion_combinada],
    "🔥 Potencias": [ejercicio_potencia, ejercicio_propiedades_potencias],
}
TODOS_GENERADORES = [g for lista in GENERADORES.values() for g in lista]


# Interfaz
requerir_login()
inicializar_estado()
if st.session_state.audio_pendiente:
    reproducir_audio(st.session_state.audio_pendiente)
    st.session_state.audio_pendiente = None

usuario = st.session_state.usuario
st.title("🧠 Aventura Matemática 7°")
st.caption("Práctica interactiva con control de usuarios.")
nivel, icono_nivel = obtener_nivel(st.session_state.puntaje)

with st.sidebar:
    st.header("🎮 Panel")
    st.write(f"👤 **{usuario['name']}**")
    st.caption(f"Usuario: {usuario['username']} | Rol: {usuario['role']}")
    if st.button("🚪 Cerrar sesión"):
        cerrar_sesion()
    st.divider()
    st.metric("Puntaje", st.session_state.puntaje)
    st.metric("Racha", st.session_state.racha)
    st.write(f"{icono_nivel} **{nivel}**")
    st.progress(min((st.session_state.puntaje % 100) / 100, 1.0))
    st.divider()
    modo = st.radio("Modo", ["Práctica por tema", "Modo examen", "Guía rápida", "Reporte", "Administración"], index=0)
    if modo == "Administración" and usuario["role"] != "admin":
        modo = "Reporte"; st.warning("Administración solo para usuarios admin.")
    st.divider()
    st.write("🏅 **Insignias**")
    for b in insignias(): st.write(b)
    if not insignias(): st.caption("Todavía no hay insignias.")
    st.divider()
    if st.button("🔄 Reiniciar mi avance"):
        usuario_actual, auth_actual = st.session_state.usuario, st.session_state.auth
        for clave in list(st.session_state.keys()): del st.session_state[clave]
        st.session_state.auth, st.session_state.usuario = auth_actual, usuario_actual
        inicializar_estado(); st.rerun()

if modo == "Práctica por tema":
    st.subheader("🎯 Práctica por tema")
    tema = st.selectbox("Elige un tema", list(GENERADORES.keys()))
    if st.session_state.tema_actual != tema:
        st.session_state.tema_actual = tema
        st.session_state.ejercicio_actual = random.choice(GENERADORES[tema])()
        st.session_state.respuesta_enviada = False
        st.session_state.feedback = ""
    if st.session_state.ejercicio_actual is None:
        st.session_state.ejercicio_actual = random.choice(GENERADORES[tema])()
    ejercicio = st.session_state.ejercicio_actual
    c1, c2 = st.columns(2)
    c1.info(f"Tema: {ejercicio.tipo}")
    c2.warning(f"Dificultad: {ejercicio.dificultad}")
    st.markdown(f"### {ejercicio.pregunta}")
    respuesta = st.radio("Selecciona una respuesta:", ejercicio.opciones, key=f"respuesta_{tema}_{ejercicio.pregunta}")
    b1, b2 = st.columns(2)
    if b1.button("✅ Revisar") and not st.session_state.respuesta_enviada:
        evaluar_respuesta(respuesta, ejercicio); st.rerun()
    if b2.button("➡️ Nuevo ejercicio"):
        reiniciar_ejercicio(); st.session_state.ejercicio_actual = random.choice(GENERADORES[tema])(); st.rerun()
    if st.session_state.respuesta_enviada:
        if st.session_state.feedback.startswith(("✅", "🌟", "🏆", "🔥")): st.success(st.session_state.feedback)
        else: st.error(st.session_state.feedback)
        st.write("💡", ejercicio.explicacion)
        if st.session_state.racha >= 3: st.balloons()

elif modo == "Modo examen":
    st.subheader("📝 Modo examen")
    cantidad = st.slider("Cantidad de preguntas", 5, 20, 10)
    if st.button("🚀 Iniciar examen"):
        st.session_state.modo_examen_preguntas = [random.choice(TODOS_GENERADORES)() for _ in range(cantidad)]
        st.session_state.modo_examen_indice = 0; st.session_state.modo_examen_aciertos = 0; st.session_state.modo_examen_inicio = time.time(); st.rerun()
    if st.session_state.modo_examen_preguntas:
        i = st.session_state.modo_examen_indice; preguntas = st.session_state.modo_examen_preguntas
        if i < len(preguntas):
            ejercicio = preguntas[i]
            st.progress(i / len(preguntas)); st.markdown(f"### Pregunta {i+1} de {len(preguntas)}")
            st.info(f"Tema: {ejercicio.tipo} | Dificultad: {ejercicio.dificultad}")
            st.markdown(f"**{ejercicio.pregunta}**")
            respuesta = st.radio("Respuesta:", ejercicio.opciones, key=f"examen_{i}_{ejercicio.pregunta}")
            if st.button("Responder"):
                correcta = str(respuesta).strip() == str(ejercicio.respuesta_correcta).strip()
                if correcta:
                    st.session_state.modo_examen_aciertos += 1; st.session_state.audio_pendiente = random.choice(AUDIOS_ACIERTO)
                else:
                    st.session_state.audio_pendiente = random.choice(AUDIOS_DESACIERTO)
                registrar_historial(ejercicio, respuesta, correcta)
                nuevas = obtener_nuevas_insignias()
                if nuevas: st.session_state.audio_pendiente = AUDIOS_INSIGNIAS.get(nuevas[0][0])
                st.session_state.modo_examen_indice += 1; st.rerun()
        else:
            tiempo = int(time.time() - st.session_state.modo_examen_inicio)
            aciertos = st.session_state.modo_examen_aciertos; total = len(preguntas); nota = round((aciertos / total) * 100, 1)
            st.success("🎉 Examen finalizado"); st.metric("Aciertos", f"{aciertos}/{total}"); st.metric("Resultado", f"{nota}%"); st.metric("Tiempo", f"{tiempo} segundos")
            if nota >= 85: st.balloons(); st.write("🏆 Excelente dominio.")
            elif nota >= 70: st.write("💪 Buen resultado. Conviene reforzar errores.")
            else: st.write("📘 Recomendación: practicar por tema antes de repetir.")
            if st.button("Reiniciar modo examen"):
                st.session_state.modo_examen_preguntas = []; st.session_state.modo_examen_indice = 0; st.session_state.modo_examen_aciertos = 0; st.session_state.modo_examen_inicio = None; st.rerun()

elif modo == "Guía rápida":
    st.subheader("📘 Guía rápida")
    with st.expander("🧩 Conjuntos", expanded=True):
        st.markdown("""- Extensión: se listan elementos.
- Comprensión: se describe una condición.
- Unión, intersección, diferencia y complemento.
- Pertenencia e inclusión.
- Múltiplos, divisores, primos, compuestos, pares e impares.""")
    with st.expander("🧭 Enteros"):
        st.markdown("""- Enteros: negativos, cero y positivos.
- Valor absoluto: distancia al cero.
- Opuesto: mismo valor absoluto, signo contrario.""")
    with st.expander("⚔️ Operaciones"):
        st.markdown("""- Suma/resta: ganancias y deudas.
- Multiplicación/división: ley de signos.
- Operaciones combinadas: paréntesis, valor absoluto, multiplicación/división y suma/resta.""")
    with st.expander("🔥 Potencias"):
        st.markdown("""- Potencia: multiplicación repetida.
- Base negativa entre paréntesis: depende del exponente.
- Igual base: multiplicando se suman exponentes; dividiendo se restan.""")

elif modo == "Reporte":
    st.subheader("📊 Mi reporte")
    total = len(st.session_state.historial); correctas = sum(1 for x in st.session_state.historial if x["correcta"]); porcentaje = round((correctas / total) * 100, 1) if total else 0
    c1, c2, c3 = st.columns(3); c1.metric("Ejercicios", total); c2.metric("Correctas", correctas); c3.metric("Porcentaje", f"{porcentaje}%")
    st.divider(); st.write("### Temas con más errores")
    if st.session_state.errores_por_tema:
        for tema_error, cantidad_error in sorted(st.session_state.errores_por_tema.items(), key=lambda x: x[1], reverse=True): st.write(f"- **{tema_error}:** {cantidad_error} error(es)")
    else: st.success("Todavía no hay errores registrados.")
    st.divider(); st.write("### Últimos ejercicios")
    if st.session_state.historial:
        for item in st.session_state.historial[-5:][::-1]:
            st.write(f"{'✅' if item['correcta'] else '❌'} **{item['tema']}** — {item['pregunta']}")
            if not item["correcta"]: st.caption(f"Tu respuesta: {item['respuesta_usuario']} | Correcta: {item['respuesta_correcta']}")
    else: st.caption("Aún no hay ejercicios practicados.")

else:
    st.subheader("🛠️ Administración")
    st.info("Los usuarios se cambian en Streamlit Cloud > App > Settings > Secrets.")
    for username, datos in cargar_usuarios().items():
        st.write(f"- **{username}** — {datos.get('name', username)} — rol: `{datos.get('role', 'student')}`")
    st.divider(); st.write("### Plantilla para Secrets")
    st.code('''[users.admin]
name = "Administrador"
password = "cambiar123"
role = "admin"

[users.cata]
name = "Catalina"
password = "mate123"
role = "student"

[users.estudiante]
name = "Estudiante"
password = "practica123"
role = "student"''', language="toml")

st.divider()
st.caption("Aventura Matemática 7° | Versión con control de usuarios.")
