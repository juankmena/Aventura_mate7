# Aventura Matemática 7° - Control de usuarios + audio configurable

## Cómo ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usuarios de prueba locales

Si no configurás secretos, la app trae estos usuarios:

- admin / admin123
- cata / mate123
- estudiante / practica123

## Configurar usuarios en Streamlit Cloud

En Streamlit Cloud:

App > Settings > Secrets

Pegá algo como:

```toml
[users.admin]
name = "Administrador"
password = "cambiar123"
role = "admin"

[users.cata]
name = "Catalina"
password = "mate123"
role = "student"
```

## Audio

La app incluye:

- Efectos de sonido ON/OFF
- Volumen de efectos
- Modo aula / sin audio
- Música de fondo opcional
- Volumen de música

Importante: en iPad/Safari la música de fondo puede requerir tocar Play manualmente por restricciones del navegador.

## Assets esperados

Reemplazá los archivos dentro de `assets/` por tus audios reales en formato `.mp3`.

- acierto_1.mp3
- acierto_2.mp3
- acierto_3.mp3
- acierto_4.mp3
- desacierto_1.mp3
- desacierto_2.mp3
- desacierto_3.mp3
- insignia_1.mp3
- insignia_2.mp3
- insignia_3.mp3
- insignia_4.mp3
- insignia_5.mp3
- insignia_6.mp3
- musica_fondo.mp3
