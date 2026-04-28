# Aventura Matemática 7° - Control de usuarios

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usuarios de prueba local

- admin / admin123
- cata / mate123
- estudiante / practica123

## Streamlit Cloud

En Streamlit Cloud, configurá usuarios en:

**App > Settings > Secrets**

Plantilla:

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

## Audios

Reemplazá los archivos de la carpeta `assets/` por tus grabaciones `.mp3`.

Nombres esperados:

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
