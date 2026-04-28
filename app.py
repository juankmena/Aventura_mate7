
import base64
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

import streamlit as st


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Aventura Matemática 7°",
    page_icon="🧠",
    layout="centered",
)

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"

AUDIOS_ACIERTO = [
    "acierto_1.mp3",
    "acierto_2.mp3",
    "acierto_3.mp3",
    "acierto_4.mp3",
]

AUDIOS_DESACIERTO = [
    "desacierto_1.mp3",
    "desacierto_2.mp3",
    "desacierto_3.mp3",
]

AUDIOS_INSIGNIAS = {
    "primeros_50": "insignia_1.mp3",
    "constancia": "insignia_2.mp3",
    "racha_3": "insignia_3.mp3",
    "racha_5": "insignia_4.mp3",
    "diez_ejercicios": "insignia_5.mp3",
    "detector_refuerzo": "insignia_6.mp3",
}

MUSICA_FONDO = "musica_fondo.mp3"


# =========================================================
# USUARIOS
# =========================================================

USUARIOS_RESPALDO = {
    "admin": {"name": "Administrador", "password": "admin123", "role": "admin"},
    "cata": {"name": "Catalina", "password": "mate123", "role": "student"},
    "estudiante": {"name": "Estudiante", "password": "practica123", "role": "student"},
}


def cargar_usuarios() -> Dict[str, Dict[str, str]]:
    try:
        if "users" in st.secrets:
            return dict(st.secrets["users"])
    except Exception:
        pass
    return USUARIOS_RESPALDO


def verificar_usuario(username: str, password: str):
    usuarios = cargar_usuarios()
    username = username.strip().lower()

    if username not in usuarios:
        return None

    datos = dict(usuarios[username])
    if password == str(datos.get("password", "")):
        return {
            "username": username,
            "name": str(datos.get("name", username)),
            "role": str(datos.get("role", "student")),
        }
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
            st.session_state.audio_pendiente = None
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    with st.expander("ℹ️ Nota para el administrador"):
        st.write(
            "Los usuarios se configuran desde Streamlit Secrets. "
            "Si no hay Secrets configurados, se usan usuarios de respaldo para pruebas."
        )


def requerir_login():
    if "auth" not in st.session_state or not st.session_state.auth:
        login()
        st.stop()


def cerrar_sesion():
    for clave in list(st.session_state.keys()):
        del st.session_state[clave]
    st.rerun()


# =========================================================
# AUDIO
# =========================================================

def audio_a_base64(nombre_archivo: str):
    ruta = ASSETS_DIR / nombre_archivo
    if not ruta.exists() or ruta.stat().st_size == 0:
        return None
    try:
        return base64.b64encode(ruta.read_bytes()).decode()
    except Exception:
        return None


def reproducir_audio(nombre_archivo: str):
    """
    Reproduce audio de evento si:
    - sonido_activo está encendido
    - modo_silencioso está apagado
    - el archivo existe en assets
    """
    if st.session_state.get("modo_silencioso", False):
        return
    if not st.session_state.get("sonido_activo", True):
        return

    audio_base64 = audio_a_base64(nombre_archivo)
    if not audio_base64:
        return

    volumen = float(st.session_state.get("volumen_audio", 70)) / 100

    st.markdown(
        f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        <script>
        const audios = window.parent.document.querySelectorAll('audio');
        if (audios.length > 0) {{
            const audio = audios[audios.length - 1];
            audio.volume = {volumen};
        }}
        </script>
        """,
        unsafe_allow_html=True,
    )


def mostrar_musica_fondo():
    """
    Muestra un reproductor de música de fondo.
    Por restricciones de navegadores, especialmente iPad/Safari,
    la música normalmente debe iniciarse manualmente con Play.
    """
    if st.session_state.get("modo_silencioso", False):
        st.info("🔇 Modo aula activo: música y efectos desactivados.")
        return

    if not st.session_state.get("musica_activa", False):
        return

    audio_base64 = audio_a_base64(MUSICA_FONDO)
    if not audio_base64:
        st.caption("🎵 Música activada, pero falta assets/musica_fondo.mp3")
        return

    volumen = float(st.session_state.get("volumen_musica", 35)) / 100
    st.markdown(
        f"""
        <div style="padding: 0.75rem; border-radius: 0.75rem; border: 1px solid #ddd; margin-bottom: 1rem;">
            <strong>🎵 Música de fondo</strong><br>
            <audio controls loop style="width: 100%; margin-top: 0.5rem;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            <script>
            const audios = window.parent.document.querySelectorAll('audio');
            if (audios.length > 0) {{
                const audio = audios[audios.length - 1];
                audio.volume = {volumen};
            }}
            </script>
            <small>En iPad puede ser necesario tocar Play manualmente.</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# ESTADO
# =========================================================

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
        "sonido_activo": True,
        "modo_silencioso": False,
        "volumen_audio": 70,
        "musica_activa": False,
        "volumen_musica": 35,
        "modo_examen_preguntas": [],
        "modo_examen_indice": 0,
        "modo_examen_aciertos": 0,
        "modo_examen_inicio": None,
    }
    for clave, valor in valores.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor


# =========================================================
# MODELO
# =========================================================

@dataclass
class Ejercicio:
    pregunta: str
    respuesta_correcta: Any
    opciones: List[Any]
    explicacion: str
    tipo: str
    dificultad: str = "Básica"


# =========================================================
# UTILIDADES
# =========================================================

def formatear_conjunto(elementos):
    return "{" + ", ".join(str(x) for x in elementos) + "}"


def es_primo(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def reiniciar_ejercicio():
    st.session_state.ejercicio_actual = None
    st.session_state.respuesta_enviada = False
    st.session_state.feedback = ""


def registrar_historial(ejercicio: Ejercicio, respuesta_usuario, correcta: bool):
    st.session_state.historial.append(
        {
            "usuario": st.session_state.usuario["username"],
            "tema": ejercicio.tipo,
            "pregunta": ejercicio.pregunta,
            "respuesta_usuario": respuesta_usuario,
            "respuesta_correcta": ejercicio.respuesta_correcta,
            "correcta": correcta,
        }
    )

    if not correcta:
        st.session_state.errores_por_tema[ejercicio.tipo] = (
            st.session_state.errores_por_tema.get(ejercicio.tipo, 0) + 1
        )


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


def evaluar_respuesta(respuesta_usuario, ejercicio: Ejercicio):
    correcta = str(respuesta_usuario).strip() == str(ejercicio.respuesta_correcta).strip()

    if correcta:
        st.session_state.puntaje += 10
        st.session_state.racha += 1
        st.session_state.feedback = random.choice([
            "✅ ¡Correcto! Muy bien.",
            "🌟 ¡Excelente! Vas ganando confianza.",
            "🏆 ¡Buenísimo! Sigue así.",
            "🔥 ¡Respuesta correcta! Buena racha.",
        ])
    else:
        st.session_state.racha = 0
        st.session_state.feedback = (
            f"❌ Casi. La respuesta correcta es: {ejercicio.respuesta_correcta}"
        )

    registrar_historial(ejercicio, respuesta_usuario, correcta)

    nuevas = obtener_nuevas_insignias()
    if nuevas:
        codigo_insignia, _ = nuevas[0]
        st.session_state.audio_pendiente = AUDIOS_INSIGNIAS.get(codigo_insignia)
    elif correcta:
        st.session_state.audio_pendiente = random.choice(AUDIOS_ACIERTO)
    else:
        st.session_state.audio_pendiente = random.choice(AUDIOS_DESACIERTO)

    st.session_state.respuesta_enviada = True
    return correcta


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
    desbloqueadas = set(st.session_state.insignias_desbloqueadas)
    return [texto for codigo, texto in catalogo.items() if codigo in desbloqueadas]


# =========================================================
# GENERADORES DE EJERCICIOS
# =========================================================

def ejercicio_naturales():
    return Ejercicio(
        pregunta="¿Cuál símbolo representa el conjunto de los números naturales?",
        respuesta_correcta="ℕ",
        opciones=["ℕ", "ℤ", "∅", "⊂"],
        explicacion="El conjunto de los números naturales se representa usualmente con el símbolo ℕ.",
        tipo="Conjuntos",
        dificultad="Básica",
    )


def ejercicio_extension_comprension():
    limite = random.randint(4, 9)
    respuesta = formatear_conjunto(list(range(1, limite)))
    opciones = [
        respuesta,
        formatear_conjunto(list(range(1, limite + 1))),
        formatear_conjunto(list(range(0, limite))),
        formatear_conjunto(list(range(2, limite))),
    ]
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=f"Representa por extensión el conjunto: A = {{x ∈ ℕ | 1 ≤ x < {limite}}}",
        respuesta_correcta=respuesta,
        opciones=opciones,
        explicacion="La condición indica números naturales desde 1 hasta el número anterior al límite dado.",
        tipo="Notación de conjuntos",
        dificultad="Media",
    )


def ejercicio_operacion_conjuntos():
    universo = set(range(1, 11))
    A = set(random.sample(list(universo), 5))
    B = set(random.sample(list(universo), 5))
    operacion = random.choice(["∪", "∩", "-"])

    if operacion == "∪":
        resultado = sorted(A | B)
        explicacion = "La unión reúne todos los elementos que están en A, en B o en ambos."
    elif operacion == "∩":
        resultado = sorted(A & B)
        explicacion = "La intersección contiene solo los elementos comunes a ambos conjuntos."
    else:
        resultado = sorted(A - B)
        explicacion = "La diferencia A - B contiene los elementos que están en A pero no en B."

    respuesta = formatear_conjunto(resultado)
    distractores = [
        formatear_conjunto(sorted(B - A)),
        formatear_conjunto(sorted(A & B)) if operacion != "∩" else formatear_conjunto(sorted(A | B)),
        formatear_conjunto(sorted(universo - A)),
    ]
    opciones = list(dict.fromkeys(distractores + [respuesta]))
    while len(opciones) < 4:
        opciones.append(formatear_conjunto(sorted(random.sample(list(universo), random.randint(1, 5)))))
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=f"Dados A = {formatear_conjunto(sorted(A))} y B = {formatear_conjunto(sorted(B))}, calcula A {operacion} B.",
        respuesta_correcta=respuesta,
        opciones=opciones[:4],
        explicacion=explicacion,
        tipo="Operaciones con conjuntos",
        dificultad="Media",
    )


def ejercicio_complemento():
    U = set(range(1, 11))
    A = set(random.sample(list(U), random.randint(3, 6)))
    respuesta = formatear_conjunto(sorted(U - A))
    opciones = [
        respuesta,
        formatear_conjunto(sorted(A)),
        formatear_conjunto(sorted(U)),
        formatear_conjunto(sorted(random.sample(list(U), 5))),
    ]
    opciones = list(dict.fromkeys(opciones))
    while len(opciones) < 4:
        opciones.append(formatear_conjunto(sorted(random.sample(list(U), random.randint(1, 6)))))
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=f"Si U = {formatear_conjunto(sorted(U))} y A = {formatear_conjunto(sorted(A))}, calcula el complemento de A.",
        respuesta_correcta=respuesta,
        opciones=opciones[:4],
        explicacion="El complemento de A contiene los elementos del universo que no están en A.",
        tipo="Operaciones con conjuntos",
        dificultad="Media",
    )


def ejercicio_pertenencia_inclusion():
    A = set(random.sample(range(1, 10), 5))
    elemento = random.choice(list(A)) if random.random() > 0.4 else random.randint(10, 15)
    respuesta = "∈" if elemento in A else "∉"

    return Ejercicio(
        pregunta=f"Completa la relación correcta: {elemento} ___ A, donde A = {formatear_conjunto(sorted(A))}",
        respuesta_correcta=respuesta,
        opciones=["∈", "∉", "⊂", "⊄"],
        explicacion="Se usa ∈ cuando un elemento pertenece a un conjunto; se usa ∉ cuando no pertenece.",
        tipo="Pertenencia e inclusión",
        dificultad="Básica",
    )


def ejercicio_inclusion_subconjunto():
    A = set(random.sample(range(1, 10), 5))
    B = set(random.sample(list(A), 3)) if random.random() > 0.35 else set(random.sample(range(10, 16), 3))
    respuesta = "⊂" if B.issubset(A) else "⊄"

    return Ejercicio(
        pregunta=f"Completa la relación correcta: B ___ A, donde A = {formatear_conjunto(sorted(A))} y B = {formatear_conjunto(sorted(B))}",
        respuesta_correcta=respuesta,
        opciones=["∈", "∉", "⊂", "⊄"],
        explicacion="La inclusión compara conjuntos. B ⊂ A cuando todos los elementos de B están dentro de A.",
        tipo="Pertenencia e inclusión",
        dificultad="Media",
    )


def ejercicio_pares_impares():
    n = random.randint(1, 40)
    respuesta = "par" if n % 2 == 0 else "impar"

    return Ejercicio(
        pregunta=f"El número {n} es...",
        respuesta_correcta=respuesta,
        opciones=["par", "impar", "primo", "compuesto"],
        explicacion="Un número par es divisible entre 2; si no lo es, es impar.",
        tipo="Pares e impares",
        dificultad="Básica",
    )


def ejercicio_primos_compuestos():
    n = random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 17, 19, 21, 25])
    respuesta = "primo" if es_primo(n) else "compuesto"

    return Ejercicio(
        pregunta=f"El número {n} es...",
        respuesta_correcta=respuesta,
        opciones=["primo", "compuesto", "par", "impar"],
        explicacion="Un número primo tiene exactamente dos divisores positivos: 1 y él mismo.",
        tipo="Primos y compuestos",
        dificultad="Básica",
    )


def ejercicio_multiplos_divisores():
    a = random.randint(2, 9)
    b = a * random.randint(2, 6) if random.random() > 0.5 else random.randint(10, 50)
    respuesta = "sí" if b % a == 0 else "no"

    return Ejercicio(
        pregunta=f"¿{b} es múltiplo de {a}?",
        respuesta_correcta=respuesta,
        opciones=["sí", "no", "solo si es par", "no se puede saber"],
        explicacion=f"Un número es múltiplo de {a} si al dividirlo entre {a} el residuo es cero.",
        tipo="Múltiplos y divisores",
        dificultad="Media",
    )


def ejercicio_valor_absoluto():
    n = random.randint(-15, 15)
    respuesta = abs(n)
    opciones = list(dict.fromkeys([respuesta, -respuesta, n, random.randint(0, 15)]))
    while len(opciones) < 4:
        opciones.append(random.randint(0, 15))
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=f"Calcula el valor absoluto: |{n}|",
        respuesta_correcta=respuesta,
        opciones=opciones[:4],
        explicacion="El valor absoluto representa la distancia del número al cero en la recta numérica.",
        tipo="Números enteros",
        dificultad="Básica",
    )


def ejercicio_opuesto():
    n = random.choice([x for x in range(-15, 16) if x != 0])
    respuesta = -n
    opciones = list(dict.fromkeys([respuesta, n, abs(n), -abs(n)]))
    while len(opciones) < 4:
        opciones.append(random.randint(-15, 15))
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=f"¿Cuál es el número opuesto de {n}?",
        respuesta_correcta=respuesta,
        opciones=opciones[:4],
        explicacion="El opuesto de un número tiene el mismo valor absoluto, pero signo contrario.",
        tipo="Números enteros",
        dificultad="Básica",
    )


def ejercicio_comparacion_enteros():
    a = random.randint(-12, 12)
    b = random.randint(-12, 12)
    while a == b:
        b = random.randint(-12, 12)
    respuesta = ">" if a > b else "<"

    return Ejercicio(
        pregunta=f"Completa con el símbolo correcto: {a} ___ {b}",
        respuesta_correcta=respuesta,
        opciones=[">", "<", "≥", "≤"],
        explicacion="En la recta numérica, el número que está más a la derecha es mayor.",
        tipo="Números enteros",
        dificultad="Básica",
    )


def ejercicio_operaciones_enteros():
    a = random.randint(-12, 12)
    b = random.choice([x for x in range(-12, 13) if x != 0])
    operacion = random.choice(["+", "-", "×", "÷"])

    if operacion == "+":
        respuesta = a + b
    elif operacion == "-":
        respuesta = a - b
    elif operacion == "×":
        respuesta = a * b
    else:
        respuesta = random.randint(-10, 10)
        a = respuesta * b

    opciones = list(dict.fromkeys([respuesta, -respuesta, respuesta + 1, respuesta - 1]))
    while len(opciones) < 4:
        opciones.append(random.randint(-30, 30))
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=f"Resuelve: {a} {operacion} {b}",
        respuesta_correcta=respuesta,
        opciones=opciones[:4],
        explicacion="En suma/resta podés pensar en ganancias y deudas. En multiplicación/división aplicá ley de signos.",
        tipo="Operaciones con enteros",
        dificultad="Media",
    )


def ejercicio_operacion_combinada():
    a = random.randint(-8, 8)
    b = random.randint(-8, 8)
    c = random.choice([x for x in range(-6, 7) if x != 0])
    respuesta = abs(a) + b * c

    opciones = list(dict.fromkeys([respuesta, -respuesta, abs(a) + b + c, abs(a) - b * c]))
    while len(opciones) < 4:
        opciones.append(random.randint(-60, 60))
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=f"Resuelve la operación combinada: |{a}| + ({b}) × ({c})",
        respuesta_correcta=respuesta,
        opciones=opciones[:4],
        explicacion="Primero se resuelve el valor absoluto, luego la multiplicación y finalmente la suma.",
        tipo="Operaciones combinadas",
        dificultad="Alta",
    )


def ejercicio_potencia():
    base = random.randint(-5, 5)
    if base == 0:
        base = 2
    exponente = random.randint(2, 4)
    respuesta = base ** exponente

    opciones = list(dict.fromkeys([respuesta, -(abs(base) ** exponente), abs(base) ** exponente, base * exponente]))
    while len(opciones) < 4:
        opciones.append(random.randint(-125, 125))
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=f"Calcula la potencia: ({base})^{exponente}",
        respuesta_correcta=respuesta,
        opciones=opciones[:4],
        explicacion="Cuando la base negativa está entre paréntesis, el signo depende de si el exponente es par o impar.",
        tipo="Potencias",
        dificultad="Media",
    )


def ejercicio_propiedades_potencias():
    base = random.randint(2, 5)
    m = random.randint(2, 5)
    n = random.randint(1, 4)
    tipo = random.choice(["multiplicacion", "division"])

    if tipo == "multiplicacion":
        respuesta = f"{base}^{m+n}"
        pregunta = f"Simplifica usando propiedades de potencias: {base}^{m} × {base}^{n}"
        explicacion = "Cuando se multiplican potencias de igual base, se conserva la base y se suman los exponentes."
        distractores = [f"{base}^{m*n}", f"{base}^{m-n}", f"{base*m}^{n}"]
    else:
        if m <= n:
            m, n = n + 2, m
        respuesta = f"{base}^{m-n}"
        pregunta = f"Simplifica usando propiedades de potencias: {base}^{m} ÷ {base}^{n}"
        explicacion = "Cuando se dividen potencias de igual base, se conserva la base y se restan los exponentes."
        distractores = [f"{base}^{m+n}", f"{base}^{m*n}", f"{base-n}^{m}"]

    opciones = distractores + [respuesta]
    random.shuffle(opciones)

    return Ejercicio(
        pregunta=pregunta,
        respuesta_correcta=respuesta,
        opciones=opciones,
        explicacion=explicacion,
        tipo="Propiedades de potencias",
        dificultad="Alta",
    )


GENERADORES: Dict[str, List[Callable[[], Ejercicio]]] = {
    "🧩 Conjuntos": [
        ejercicio_naturales,
        ejercicio_extension_comprension,
        ejercicio_operacion_conjuntos,
        ejercicio_complemento,
        ejercicio_pertenencia_inclusion,
        ejercicio_inclusion_subconjunto,
        ejercicio_pares_impares,
        ejercicio_primos_compuestos,
        ejercicio_multiplos_divisores,
    ],
    "🧭 Números enteros": [
        ejercicio_valor_absoluto,
        ejercicio_opuesto,
        ejercicio_comparacion_enteros,
    ],
    "⚔️ Operaciones con enteros": [
        ejercicio_operaciones_enteros,
        ejercicio_operacion_combinada,
    ],
    "🔥 Potencias": [
        ejercicio_potencia,
        ejercicio_propiedades_potencias,
    ],
}

TODOS_GENERADORES = [g for lista in GENERADORES.values() for g in lista]


# =========================================================
# APP
# =========================================================

requerir_login()
inicializar_estado()

if st.session_state.audio_pendiente:
    reproducir_audio(st.session_state.audio_pendiente)
    st.session_state.audio_pendiente = None

usuario = st.session_state.usuario

st.title("🧠 Aventura Matemática 7°")
st.caption("Práctica interactiva con control de usuarios y audio configurable.")

mostrar_musica_fondo()

nivel, icono_nivel = obtener_nivel(st.session_state.puntaje)
progreso_nivel = min((st.session_state.puntaje % 100) / 100, 1.0)

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
    st.progress(progreso_nivel)

    st.divider()
    st.write("🔊 **Audio**")
    st.session_state.modo_silencioso = st.toggle(
        "Modo aula / sin audio",
        value=st.session_state.modo_silencioso,
        help="Desactiva efectos y música.",
    )

    st.session_state.sonido_activo = st.toggle(
        "Efectos de sonido",
        value=st.session_state.sonido_activo,
        disabled=st.session_state.modo_silencioso,
    )

    st.session_state.volumen_audio = st.slider(
        "Volumen efectos",
        0,
        100,
        int(st.session_state.volumen_audio),
        disabled=st.session_state.modo_silencioso or not st.session_state.sonido_activo,
    )

    st.session_state.musica_activa = st.toggle(
        "Música de fondo",
        value=st.session_state.musica_activa,
        disabled=st.session_state.modo_silencioso,
        help="En iPad puede requerir tocar Play manualmente.",
    )

    st.session_state.volumen_musica = st.slider(
        "Volumen música",
        0,
        100,
        int(st.session_state.volumen_musica),
        disabled=st.session_state.modo_silencioso or not st.session_state.musica_activa,
    )

    st.divider()
    modo = st.radio(
        "Modo",
        ["Práctica por tema", "Modo examen", "Guía rápida", "Reporte", "Administración"],
        index=0,
    )

    if modo == "Administración" and usuario["role"] != "admin":
        modo = "Reporte"
        st.warning("La administración solo está disponible para usuarios admin.")

    st.divider()
    st.write("🏅 **Insignias**")
    lista_insignias = insignias()
    if lista_insignias:
        for badge in lista_insignias:
            st.write(badge)
    else:
        st.caption("Todavía no hay insignias.")

    st.divider()
    if st.button("🔄 Reiniciar mi avance"):
        usuario_actual = st.session_state.usuario
        auth_actual = st.session_state.auth
        for clave in list(st.session_state.keys()):
            del st.session_state[clave]
        st.session_state.auth = auth_actual
        st.session_state.usuario = usuario_actual
        inicializar_estado()
        st.rerun()


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
        st.session_state.respuesta_enviada = False

    ejercicio = st.session_state.ejercicio_actual

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"Tema: {ejercicio.tipo}")
    with col_b:
        st.warning(f"Dificultad: {ejercicio.dificultad}")

    st.markdown(f"### {ejercicio.pregunta}")

    respuesta = st.radio(
        "Selecciona una respuesta:",
        ejercicio.opciones,
        key=f"respuesta_{tema}_{ejercicio.pregunta}",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Revisar") and not st.session_state.respuesta_enviada:
            evaluar_respuesta(respuesta, ejercicio)
            st.rerun()

    with col2:
        if st.button("➡️ Nuevo ejercicio"):
            reiniciar_ejercicio()
            st.session_state.ejercicio_actual = random.choice(GENERADORES[tema])()
            st.rerun()

    if st.session_state.respuesta_enviada:
        if st.session_state.feedback.startswith(("✅", "🌟", "🏆", "🔥")):
            st.success(st.session_state.feedback)
        else:
            st.error(st.session_state.feedback)

        st.write("💡", ejercicio.explicacion)

        if st.session_state.racha >= 3:
            st.balloons()


elif modo == "Modo examen":
    st.subheader("📝 Modo examen")
    st.write("Este modo mezcla temas y simula una práctica sin ayudas durante la respuesta.")

    cantidad = st.slider("Cantidad de preguntas", 5, 20, 10)

    if st.button("🚀 Iniciar examen"):
        st.session_state.modo_examen_preguntas = [
            random.choice(TODOS_GENERADORES)() for _ in range(cantidad)
        ]
        st.session_state.modo_examen_indice = 0
        st.session_state.modo_examen_aciertos = 0
        st.session_state.modo_examen_inicio = time.time()
        st.rerun()

    if st.session_state.modo_examen_preguntas:
        indice = st.session_state.modo_examen_indice
        preguntas = st.session_state.modo_examen_preguntas

        if indice < len(preguntas):
            ejercicio = preguntas[indice]
            st.progress(indice / len(preguntas))
            st.markdown(f"### Pregunta {indice + 1} de {len(preguntas)}")
            st.info(f"Tema: {ejercicio.tipo} | Dificultad: {ejercicio.dificultad}")
            st.markdown(f"**{ejercicio.pregunta}**")

            respuesta = st.radio(
                "Respuesta:",
                ejercicio.opciones,
                key=f"examen_{indice}_{ejercicio.pregunta}",
            )

            if st.button("Responder"):
                correcta = str(respuesta).strip() == str(ejercicio.respuesta_correcta).strip()
                if correcta:
                    st.session_state.modo_examen_aciertos += 1
                    st.session_state.audio_pendiente = random.choice(AUDIOS_ACIERTO)
                else:
                    st.session_state.audio_pendiente = random.choice(AUDIOS_DESACIERTO)

                registrar_historial(ejercicio, respuesta, correcta)

                nuevas = obtener_nuevas_insignias()
                if nuevas:
                    codigo_insignia, _ = nuevas[0]
                    st.session_state.audio_pendiente = AUDIOS_INSIGNIAS.get(codigo_insignia)

                st.session_state.modo_examen_indice += 1
                st.rerun()
        else:
            tiempo = int(time.time() - st.session_state.modo_examen_inicio)
            aciertos = st.session_state.modo_examen_aciertos
            total = len(st.session_state.modo_examen_preguntas)
            nota = round((aciertos / total) * 100, 1)

            st.success("🎉 Examen finalizado")
            st.metric("Aciertos", f"{aciertos}/{total}")
            st.metric("Resultado", f"{nota}%")
            st.metric("Tiempo", f"{tiempo} segundos")

            if nota >= 85:
                st.balloons()
                st.write("🏆 Excelente dominio. Estás listo para subir de nivel.")
            elif nota >= 70:
                st.write("💪 Buen resultado. Conviene reforzar los errores antes del examen.")
            else:
                st.write("📘 Recomendación: vuelve a practicar por tema antes de repetir el modo examen.")

            if st.button("Reiniciar modo examen"):
                st.session_state.modo_examen_preguntas = []
                st.session_state.modo_examen_indice = 0
                st.session_state.modo_examen_aciertos = 0
                st.session_state.modo_examen_inicio = None
                st.rerun()


elif modo == "Guía rápida":
    st.subheader("📘 Guía rápida")

    with st.expander("🧩 Conjuntos", expanded=True):
        st.markdown(
            """
- **Por extensión:** se listan los elementos. Ejemplo: A = {1, 2, 3}
- **Por comprensión:** se describe la condición. Ejemplo: A = {x ∈ ℕ | x < 4}
- **Unión (∪):** elementos que están en A, en B o en ambos.
- **Intersección (∩):** elementos comunes.
- **Diferencia (-):** elementos de A que no están en B.
- **Complemento:** elementos del universo que no están en el conjunto.
- **Pertenencia (∈):** relación entre elemento y conjunto.
- **Inclusión (⊂):** relación entre conjunto y conjunto.
- **Múltiplos, divisores, primos, compuestos, pares e impares:** necesarios para describir conjuntos.
"""
        )

    with st.expander("🧭 Enteros"):
        st.markdown(
            """
- Los enteros incluyen números negativos, cero y positivos.
- El valor absoluto es la distancia al cero.
- El opuesto cambia el signo del número.
- En la recta numérica, el número más a la derecha es mayor.
"""
        )

    with st.expander("⚔️ Operaciones con enteros"):
        st.markdown(
            """
- En suma y resta se puede pensar en ganancias y deudas.
- En multiplicación y división se aplica ley de signos.
- Orden sugerido: paréntesis, valor absoluto, multiplicación/división, suma/resta.
"""
        )

    with st.expander("🔥 Potencias"):
        st.markdown(
            """
- Una potencia representa multiplicación repetida.
- Si la base negativa está entre paréntesis, el signo depende del exponente.
- Igual base multiplicando: se suman exponentes.
- Igual base dividiendo: se restan exponentes.
"""
        )


elif modo == "Reporte":
    st.subheader("📊 Mi reporte de avance")

    total = len(st.session_state.historial)
    correctas = sum(1 for item in st.session_state.historial if item["correcta"])
    porcentaje = round((correctas / total) * 100, 1) if total else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Ejercicios", total)
    col2.metric("Correctas", correctas)
    col3.metric("Porcentaje", f"{porcentaje}%")

    st.divider()
    st.write("### Temas con más errores")
    if st.session_state.errores_por_tema:
        errores_ordenados = sorted(
            st.session_state.errores_por_tema.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        for tema_error, cantidad_error in errores_ordenados:
            st.write(f"- **{tema_error}:** {cantidad_error} error(es)")
    else:
        st.success("Todavía no hay errores registrados. ¡Buen inicio!")

    st.divider()
    st.write("### Últimos ejercicios")
    if st.session_state.historial:
        for item in st.session_state.historial[-5:][::-1]:
            icono = "✅" if item["correcta"] else "❌"
            st.write(f"{icono} **{item['tema']}** — {item['pregunta']}")
            if not item["correcta"]:
                st.caption(
                    f"Tu respuesta: {item['respuesta_usuario']} | Correcta: {item['respuesta_correcta']}"
                )
    else:
        st.caption("Aún no hay ejercicios practicados.")


else:
    st.subheader("🛠️ Administración")

    st.info(
        "Este panel muestra los usuarios configurados. "
        "Para cambiarlos en Streamlit Cloud, editá App > Settings > Secrets."
    )

    usuarios = cargar_usuarios()
    for username, datos in usuarios.items():
        rol = datos.get("role", "student")
        nombre = datos.get("name", username)
        st.write(f"- **{username}** — {nombre} — rol: `{rol}`")

    st.divider()
    st.write("### Plantilla para Streamlit Secrets")
    st.code(
        """
[users.admin]
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
role = "student"
""",
        language="toml",
    )

    st.divider()
    st.write("### Archivos de audio esperados")
    st.code(
        """
assets/
  acierto_1.mp3
  acierto_2.mp3
  acierto_3.mp3
  acierto_4.mp3
  desacierto_1.mp3
  desacierto_2.mp3
  desacierto_3.mp3
  insignia_1.mp3
  insignia_2.mp3
  insignia_3.mp3
  insignia_4.mp3
  insignia_5.mp3
  insignia_6.mp3
  musica_fondo.mp3
""",
        language="text",
    )

st.divider()
st.caption("Aventura Matemática 7° | Control de usuarios + audio configurable.")
