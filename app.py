import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import streamlit as st

st.set_page_config(page_title="Aventura Matemática 7°", page_icon="🧠", layout="centered")

# Estilo visual simple y amigable para iPad
st.markdown("""
<style>
    .main .block-container {max-width: 900px; padding-top: 1.5rem;}
    div.stButton > button {border-radius: 14px; font-weight: 700; min-height: 3rem;}
    .card {padding: 1rem; border-radius: 18px; background: #f7f7fb; border: 1px solid #eee;}
    .big {font-size: 1.35rem; font-weight: 800;}
    .ok {background:#e9fff1; padding:1rem; border-radius:16px; border:1px solid #b7f5cd;}
    .bad {background:#fff0f0; padding:1rem; border-radius:16px; border:1px solid #ffc7c7;}
</style>
""", unsafe_allow_html=True)

@dataclass
class Ejercicio:
    pregunta: str
    respuesta_correcta: Any
    opciones: List[Any]
    explicacion: str
    tipo: str
    dificultad: str = "Básica"


def init_state():
    defaults = {
        "puntaje": 0,
        "racha": 0,
        "tema_actual": None,
        "ejercicio_actual": None,
        "respuesta_enviada": False,
        "feedback_ok": None,
        "historial": [],
        "errores_por_tema": {},
        "audio_activo": True,
        "examen": [],
        "examen_i": 0,
        "examen_ok": 0,
        "examen_inicio": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def conj(xs):
    return "{" + ", ".join(map(str, xs)) + "}"

def nuevo_ejercicio(tema):
    st.session_state.ejercicio_actual = random.choice(GENERADORES[tema])()
    st.session_state.respuesta_enviada = False
    st.session_state.feedback_ok = None

def registrar(ej, resp, ok):
    st.session_state.historial.append({"tema": ej.tipo, "pregunta": ej.pregunta, "respuesta": resp, "correcta": ej.respuesta_correcta, "ok": ok})
    if not ok:
        st.session_state.errores_por_tema[ej.tipo] = st.session_state.errores_por_tema.get(ej.tipo, 0) + 1

def evaluar(resp, ej):
    ok = str(resp).strip() == str(ej.respuesta_correcta).strip()
    if ok:
        st.session_state.puntaje += 10
        st.session_state.racha += 1
    else:
        st.session_state.racha = 0
    registrar(ej, resp, ok)
    st.session_state.respuesta_enviada = True
    st.session_state.feedback_ok = ok

def nivel():
    p = st.session_state.puntaje
    if p < 50: return "🌱 Explorador/a", p / 50
    if p < 120: return "📘 Aprendiz", (p-50) / 70
    if p < 220: return "🧩 Estratega", (p-120) / 100
    if p < 350: return "⚔️ Maestro/a de enteros", (p-220) / 130
    return "🏆 Leyenda matemática", 1.0

# Generadores: ajustados a las observaciones del temario.
def naturales():
    return Ejercicio("¿Cuál símbolo representa el conjunto de los números naturales?", "ℕ", ["ℕ", "ℤ", "∅", "⊂"], "ℕ representa los números naturales.", "Números naturales")

def extension_comprension():
    n = random.randint(4, 10)
    ans = conj(range(1, n))
    opts = [ans, conj(range(1, n+1)), conj(range(0, n)), conj(range(2, n))]
    random.shuffle(opts)
    return Ejercicio(f"Representa por extensión: A = {{x ∈ ℕ | 1 ≤ x < {n}}}", ans, opts, "Se listan los naturales desde 1 hasta el anterior al límite.", "Notación de conjuntos", "Media")

def multiplos_divisores_primos():
    tipo = random.choice(["múltiplos", "divisores", "primos", "pares", "impares"])
    if tipo == "múltiplos":
        k = random.randint(2, 5); lim = random.randint(18, 30)
        ans = conj([x for x in range(1, lim+1) if x % k == 0])
        preg = f"Sea A = {{x ∈ ℕ | x es múltiplo de {k} y x ≤ {lim}}}. Escríbelo por extensión."
    elif tipo == "divisores":
        k = random.choice([12, 18, 24, 30, 36])
        ans = conj([x for x in range(1, k+1) if k % x == 0])
        preg = f"Sea A = {{x ∈ ℕ | x es divisor de {k}}}. Escríbelo por extensión."
    elif tipo == "primos":
        lim = random.choice([10, 15, 20])
        primos = [x for x in range(2, lim+1) if all(x%d for d in range(2, int(x**0.5)+1))]
        ans = conj(primos); preg = f"Sea A = {{x ∈ ℕ | x es primo y x ≤ {lim}}}. Escríbelo por extensión."
    elif tipo == "pares":
        lim = random.choice([10, 12, 14, 16])
        ans = conj([x for x in range(1, lim+1) if x%2==0]); preg = f"Sea A = {{x ∈ ℕ | x es par y x ≤ {lim}}}. Escríbelo por extensión."
    else:
        lim = random.choice([9, 11, 13, 15])
        ans = conj([x for x in range(1, lim+1) if x%2!=0]); preg = f"Sea A = {{x ∈ ℕ | x es impar y x ≤ {lim}}}. Escríbelo por extensión."
    opts = [ans, conj([]), conj(range(1, min(8, len(ans))+1)), "Ninguna de las anteriores"]
    opts = list(dict.fromkeys(opts)); random.shuffle(opts)
    return Ejercicio(preg, ans, opts, "Este ejercicio refuerza múltiplos, divisores, primos, pares o impares.", "Conjuntos con conceptos de primaria", "Media")

def operaciones_conjuntos():
    U = set(range(1, 11)); A=set(random.sample(list(U),5)); B=set(random.sample(list(U),5))
    op=random.choice(["∪","∩","-","complemento"])
    if op=="∪": res=sorted(A|B); preg=f"A={conj(sorted(A))}, B={conj(sorted(B))}. Calcula A ∪ B."; exp="Unión: elementos en A, en B o en ambos."
    elif op=="∩": res=sorted(A&B); preg=f"A={conj(sorted(A))}, B={conj(sorted(B))}. Calcula A ∩ B."; exp="Intersección: elementos comunes."
    elif op=="-": res=sorted(A-B); preg=f"A={conj(sorted(A))}, B={conj(sorted(B))}. Calcula A - B."; exp="Diferencia: elementos de A que no están en B."
    else: res=sorted(U-A); preg=f"U={conj(sorted(U))}, A={conj(sorted(A))}. Calcula el complemento de A."; exp="Complemento: elementos del universo que no están en A."
    ans=conj(res); opts=[ans, conj(sorted(B-A)), conj(sorted(A&B)), conj(sorted(U-A))]
    opts=list(dict.fromkeys(opts))
    while len(opts)<4: opts.append(conj(sorted(random.sample(list(U), random.randint(1,5)))))
    random.shuffle(opts)
    return Ejercicio(preg, ans, opts[:4], exp, "Operaciones entre conjuntos", "Media")

def pertenencia_inclusion():
    A=set(random.sample(range(1,10),5))
    if random.random()<0.5:
        e=random.choice(list(A)) if random.random()<0.6 else random.randint(10,15)
        ans="∈" if e in A else "∉"
        preg=f"Completa: {e} ___ A, donde A={conj(sorted(A))}"
        exp="Pertenencia relaciona elemento con conjunto."
    else:
        B=set(random.sample(list(A),3)) if random.random()<0.6 else set(random.sample(range(10,16),3))
        ans="⊂" if B.issubset(A) else "⊄"
        preg=f"Completa: B ___ A, donde A={conj(sorted(A))} y B={conj(sorted(B))}"
        exp="Inclusión relaciona conjunto con conjunto."
    return Ejercicio(preg, ans, ["∈","∉","⊂","⊄"], exp, "Pertenencia e inclusión")

def valor_opuesto_comparacion():
    kind=random.choice(["valor","opuesto","comparar"])
    if kind=="valor":
        n=random.randint(-15,15); ans=abs(n); opts=list(set([ans,-ans,n,random.randint(0,15)])); preg=f"Calcula |{n}|"; exp="Valor absoluto: distancia al cero."
    elif kind=="opuesto":
        n=random.choice([x for x in range(-15,16) if x]); ans=-n; opts=list(set([ans,n,abs(n),-abs(n)])); preg=f"¿Cuál es el opuesto de {n}?"; exp="El opuesto tiene signo contrario."
    else:
        a=random.randint(-12,12); b=random.randint(-12,12)
        while a==b: b=random.randint(-12,12)
        ans=">" if a>b else "<"; opts=[">","<","≥","≤"]; preg=f"Completa: {a} ___ {b}"; exp="En la recta numérica, el mayor está más a la derecha."
    while len(opts)<4: opts.append(random.randint(-15,15))
    random.shuffle(opts)
    return Ejercicio(preg, ans, opts[:4], exp, "Números enteros")

def operaciones_enteros():
    a=random.randint(-12,12); b=random.choice([x for x in range(-12,13) if x])
    op=random.choice(["+","-","×","÷"])
    if op=="+": ans=a+b; exp="Suma/resta: se puede pensar en ganancias y deudas."
    elif op=="-": ans=a-b; exp="Suma/resta: se puede pensar en ganancias y deudas."
    elif op=="×": ans=a*b; exp="Multiplicación: aplica ley de signos."
    else:
        ans=random.randint(-10,10); a=ans*b; exp="División: aplica ley de signos."
    opts=list(set([ans,-ans,ans+1,ans-1,a+b]));
    while len(opts)<4: opts.append(random.randint(-50,50))
    random.shuffle(opts)
    return Ejercicio(f"Resuelve: {a} {op} {b}", ans, opts[:4], exp, "Operaciones con enteros", "Media")

def combinadas():
    a=random.randint(-8,8); b=random.randint(-8,8); c=random.choice([x for x in range(-6,7) if x])
    ans=abs(a)+b*c
    opts=list(set([ans,-ans,abs(a)+b+c,abs(a)-b*c]))
    while len(opts)<4: opts.append(random.randint(-70,70))
    random.shuffle(opts)
    return Ejercicio(f"Resuelve: |{a}| + ({b}) × ({c})", ans, opts[:4], "Orden: valor absoluto, multiplicación y suma.", "Operaciones combinadas", "Alta")

def potencias():
    if random.random()<0.5:
        base=random.choice([-5,-4,-3,-2,2,3,4,5]); expn=random.randint(2,4); ans=base**expn
        opts=list(set([ans, -(abs(base)**expn), abs(base)**expn, base*expn]))
        preg=f"Calcula: ({base})^{expn}"; exp="Base negativa entre paréntesis: el signo depende de si el exponente es par o impar."
    else:
        base=random.randint(2,5); m=random.randint(2,5); n=random.randint(1,4)
        if random.random()<0.5:
            ans=f"{base}^{m+n}"; preg=f"Simplifica: {base}^{m} × {base}^{n}"; opts=[ans,f"{base}^{m*n}",f"{base}^{m-n}",f"{base*m}^{n}"]; exp="Igual base multiplicando: se suman exponentes."
        else:
            if m<=n: m,n=n+2,m
            ans=f"{base}^{m-n}"; preg=f"Simplifica: {base}^{m} ÷ {base}^{n}"; opts=[ans,f"{base}^{m+n}",f"{base}^{m*n}",f"{base-n}^{m}"]; exp="Igual base dividiendo: se restan exponentes."
    while len(opts)<4: opts.append(random.randint(-125,125))
    random.shuffle(opts)
    return Ejercicio(preg, ans, opts[:4], exp, "Potencias", "Alta")

GENERADORES: Dict[str, List[Callable[[], Ejercicio]]] = {
    "🧩 Conjuntos": [naturales, extension_comprension, multiplos_divisores_primos, operaciones_conjuntos, pertenencia_inclusion],
    "🧭 Enteros": [valor_opuesto_comparacion],
    "⚔️ Operaciones": [operaciones_enteros, combinadas],
    "🔥 Potencias": [potencias],
}
TODOS=[g for L in GENERADORES.values() for g in L]

st.title("🧠 Aventura Matemática 7°")
st.caption("Práctica amigable para conjuntos, enteros, operaciones combinadas y potencias")

niv, prog = nivel()
with st.sidebar:
    st.header("🎮 Panel")
    st.metric("Puntaje", st.session_state.puntaje)
    st.metric("Racha", st.session_state.racha)
    st.write(f"**{niv}**")
    st.progress(min(max(prog,0),1))
    st.session_state.audio_activo = st.toggle("Sonido de acierto", value=st.session_state.audio_activo)
    modo=st.radio("Modo", ["Práctica por tema", "Modo examen", "Guía rápida", "Reporte"])
    if st.button("🔄 Reiniciar avance"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if modo=="Práctica por tema":
    tema=st.selectbox("Elige un tema", list(GENERADORES.keys()))
    if st.session_state.tema_actual != tema:
        st.session_state.tema_actual=tema
        nuevo_ejercicio(tema)
    if st.session_state.ejercicio_actual is None:
        nuevo_ejercicio(tema)
    ej=st.session_state.ejercicio_actual
    st.markdown(f"<div class='card'><div class='big'>{ej.pregunta}</div><br>Tema: {ej.tipo} · Dificultad: {ej.dificultad}</div>", unsafe_allow_html=True)
    resp=st.radio("Selecciona una respuesta:", ej.opciones, key=f"resp_{tema}_{ej.pregunta}")
    c1,c2=st.columns(2)
    with c1:
        if st.button("✅ Revisar", use_container_width=True) and not st.session_state.respuesta_enviada:
            evaluar(resp, ej); st.rerun()
    with c2:
        if st.button("➡️ Nuevo ejercicio", use_container_width=True):
            nuevo_ejercicio(tema); st.rerun()
    if st.session_state.respuesta_enviada:
        if st.session_state.feedback_ok:
            st.markdown("<div class='ok'>🎉 ¡Correcto! +10 puntos</div>", unsafe_allow_html=True)
            st.balloons()
            if st.session_state.audio_activo:
                try: st.audio("assets/acierto.wav", autoplay=True)
                except TypeError: st.audio("assets/acierto.wav")
        else:
            st.markdown(f"<div class='bad'>❌ No es correcto. Respuesta correcta: <b>{ej.respuesta_correcta}</b></div>", unsafe_allow_html=True)
        st.write("💡", ej.explicacion)

elif modo=="Modo examen":
    st.subheader("📝 Modo examen")
    n=st.slider("Cantidad de preguntas", 5, 20, 10)
    if st.button("🚀 Iniciar examen"):
        st.session_state.examen=[random.choice(TODOS)() for _ in range(n)]
        st.session_state.examen_i=0; st.session_state.examen_ok=0; st.session_state.examen_inicio=time.time(); st.rerun()
    if st.session_state.examen:
        i=st.session_state.examen_i
        if i < len(st.session_state.examen):
            ej=st.session_state.examen[i]
            st.progress(i/len(st.session_state.examen))
            st.markdown(f"### Pregunta {i+1}/{len(st.session_state.examen)}")
            st.write(ej.pregunta)
            resp=st.radio("Respuesta:", ej.opciones, key=f"exam_{i}_{ej.pregunta}")
            if st.button("Responder"):
                ok=str(resp)==str(ej.respuesta_correcta)
                if ok: st.session_state.examen_ok += 1
                registrar(ej, resp, ok)
                st.session_state.examen_i += 1
                st.rerun()
        else:
            total=len(st.session_state.examen); ok=st.session_state.examen_ok; nota=round(ok/total*100,1)
            st.success("Examen finalizado")
            st.metric("Resultado", f"{nota}%")
            st.write(f"Aciertos: {ok}/{total}")
            st.write(f"Tiempo: {int(time.time()-st.session_state.examen_inicio)} segundos")

elif modo=="Guía rápida":
    st.subheader("📘 Guía rápida")
    st.write("Conjuntos: extensión, comprensión, unión, intersección, diferencia, complemento, pertenencia e inclusión.")
    st.write("Enteros: recta numérica, comparación, valor absoluto y opuesto.")
    st.write("Operaciones: suma/resta como ganancias y deudas; multiplicación/división con ley de signos.")
    st.write("Potencias: concepto, signo de base negativa y propiedades con igual base.")

else:
    st.subheader("📊 Reporte")
    total=len(st.session_state.historial); ok=sum(x["ok"] for x in st.session_state.historial)
    st.metric("Ejercicios", total); st.metric("Aciertos", ok); st.metric("Porcentaje", f"{round(ok/total*100,1) if total else 0}%")
    st.write("### Errores por tema")
    if st.session_state.errores_por_tema:
        for t,c in sorted(st.session_state.errores_por_tema.items(), key=lambda x:x[1], reverse=True): st.write(f"- {t}: {c}")
    else: st.write("Sin errores registrados.")
