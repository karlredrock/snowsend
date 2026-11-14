# SnowSend — LocalSend para Mac OS X 10.6 Snow Leopard

Cliente del **protocolo LocalSend v2** escrito en Python 2.6/2.7 con la
librería estándar de Snow Leopard, empaquetado como aplicación nativa
**`SnowSend.app`** (doble clic, sin Terminal).

**SnowSend** es un proyecto independiente: implementa el protocolo
LocalSend desde cero para que un Mac con Snow Leopard pueda intercambiar
archivos con móviles y ordenadores modernos que usan la app oficial.
No está afiliado, patrocinado ni respaldado por el proyecto LocalSend.

```
┌─────────────────────────────┐        HTTP plano :53317        ┌──────────────────────────────┐
│  Mac Snow Leopard (10.6)    │  ◄───────────────────────────►  │  Móvil / Mac moderno        │
│  SnowSend.app               │     multicast UDP 224.0.0.167   │  App oficial LocalSend       │
│  /usr/bin/python (2.6/2.7)  │     descubrimiento + archivos   │  Encryption: OFF             │
│  Tkinter + BaseHTTPServer   │                                 │  (ver §3, imprescindible)    │
└─────────────────────────────┘                                 └──────────────────────────────┘
```

> **Por qué HTTP plano:** Snow Leopard no soporta de forma fiable
> TLS 1.2/1.3 moderno ni el certificado autofirmado con *fingerprint
> pinning* que usa LocalSend por defecto (HTTPS). Por eso este cliente
> habla **HTTP sin cifrar en el puerto 53317**. Úsalo solo en tu red
> local de confianza.

**Versión:** 1.7 (`2.0.7-10.6`) · **Licencia:** MIT (ver §10) ·
**Estado:** proyecto personal, asistido por IA (§9) ·
**Idiomas:** English, Español, Français, Deutsch, Português (§5)

*Documentation in English: [`README.md`](README.md).*

---

## 1. Contenido de este proyecto

| Archivo | Para qué sirve |
|---|---|
| `snowsend.py` | Código fuente completo (GUI Tkinter + servidor HTTP + descubrimiento multicast + cliente de envío). Compatible Python 2.6/2.7 y Python 3. |
| `build_app.sh` | Script que genera `SnowSend.app` (Info.plist, launcher, icono). |
| `SnowSend.app/` | **La aplicación lista para copiar al Snow Leopard** y abrir con doble clic. |
| `SnowSend.zip` | El mismo `.app` comprimido en ZIP (recomendado para transferirlo, ver §2). |
| `tests/` | Pruebas automáticas (se ejecutan con Python 3 en cualquier máquina). |
| `README.md` | Versión en inglés de este documento. |
| `README.es.md` | Este archivo. |
| `LICENSE` | Licencia MIT del proyecto. También se copia dentro del paquete como `Contents/Resources/LICENSE.txt`. |

Estructura del paquete (clásica de Mac OS X 10.6):

```
SnowSend.app/
└── Contents/
    ├── Info.plist          CFBundleExecutable=launcher, LSMinimumSystemVersion=10.6
    ├── PkgInfo             APPL????
    ├── MacOS/
    │   └── launcher        script /bin/sh ejecutable (chmod +x)
    └── Resources/
        ├── snowsend.py
        ├── LICENSE.txt     licencia MIT del proyecto
        └── AppIcon.icns    icono (512×512 máx.)
```

El `launcher` resuelve su propia ruta con `dirname "$0"`, redirige
`stdout`/`stderr` a `~/Library/Logs/SnowSend.log` (para que al
hacer doble clic **no** se abra una ventana de Terminal) y ejecuta:

```sh
exec /usr/bin/python "$RESOURCES_DIR/snowsend.py"
```

Sin dependencias externas: nada de `pip`, `requests`, `flask`,
`PyInstaller` ni `py2app`. Solo `Tkinter`, `socket`, `struct`, `json`,
`threading`, `BaseHTTPServer`, `urllib2`, `hashlib`, `uuid`,
`mimetypes`, `os` y `sys`, todo incluido en Snow Leopard.

---

## 2. Cómo pasar `SnowSend.app` al Mac con Snow Leopard

`SnowSend.app` es en realidad una **carpeta** (paquete de Finder).
Algunos métodos de copia la “aplanan” o pierden el permiso de
ejecución del `launcher`. La forma más segura es llevarla **en ZIP**.

### Opción A — ZIP en USB (recomendada)

1. En el Mac moderno (o en este proyecto) comprime la app:
   ```sh
   zip -r SnowSend.zip SnowSend.app
   ```
   Ya tienes `SnowSend.zip` generado junto a este README.
2. Copia `SnowSend.zip` a una memoria USB **FAT32** (Snow Leopard
   no escribe en NTFS ni en exFAT de forma nativa).
3. En el Snow Leopard, abre el USB, haz doble clic en `SnowSend.zip`:
   **Utilidad de Archivos** (incluida en 10.6) lo descomprime solo.
4. Arrastra `SnowSend.app` a **Aplicaciones** (`/Applications`).
5. Doble clic en `SnowSend.app`. Aparece la ventana de SnowSend.

> Si tras copiarla el doble clic no hace nada (p. ej. la copiaste
> desde Windows y se perdió el permiso `+x`), abre Terminal en el
> Snow Leopard y ejecuta una sola vez:
> ```sh
> chmod +x /Applications/SnowSend.app/Contents/MacOS/launcher
> ```

### Opción B — Red local (SMB / FTP / SSH)

- **SMB:** en el Mac moderno comparte una carpeta (Compartir →
  Compartir archivos SMB) y en el Snow Leopard ve el servidor en
  Finder → Red. Copia el ZIP (no la carpeta suelta) y descomprime
  como arriba.
- **FTP / SFTP:** cualquier servidor FTP/SFTP accesible desde 10.6
  sirve; descarga el ZIP y descomprime.
- **CD/DVD o correo:** también funciona con el ZIP. No uses servicios
  web modernos que exijan TLS 1.2+ o navegadores actuales, porque el
  navegador de Snow Leopard (Safari 5) no los soporta.

### Opción C — Ya estás en el Snow Leopard

Si tienes los archivos en el propio Mac, basta con:

```sh
chmod +x build_app.sh
./build_app.sh
```

y abrir `SnowSend.app`.

---

## 3. ⚠️ Ajuste imprescindible en el móvil / Mac moderno: desactivar el cifrado

La app oficial de LocalSend cifra por defecto con HTTPS (TLS con
certificado autofirmado). Snow Leopard **no puede** hablar ese TLS.
Si no desactivas el cifrado, el Snow Leopard nunca aparecerá en la
lista del móvil (o viceversa) y el envío fallará.

Haz esto **en cada dispositivo moderno** que quieras usar con el
Snow Leopard:

### En el móvil (Android / iPhone)

1. Abre **LocalSend**.
2. Ve a **Ajustes (⚙️) → Cifrado / Encryption**.
3. Pon **Cifrado: Desactivado / Encryption: Off**.
4. Deja el puerto en **53317** (es el predeterminado).

### En el ordenador moderno (Windows / macOS / Linux)

1. Abre **LocalSend**.
2. **Ajustes → Cifrado / Encryption → Desactivado / Off**.
3. Puerto **53317**.

Después, en la lista de dispositivos del móvil/Mac moderno debe
aparecer el Snow Leopard con protocolo **`http`** (no `https`).
Si sigue sin aparecer, pulsa **“Anunciar / Refrescar”** en el
Snow Leopard y espera 5–10 segundos; ambos equipos deben estar en
el **mismo Wi-Fi / misma red local**, sin aislamiento de clientes
(ver §6).

> Al desactivar el cifrado, los archivos viajan **sin cifrar** por
> tu Wi-Fi local. Es aceptable en una red doméstica de confianza,
> pero no lo uses en Wi-Fi públicas.

---

## 4. Uso diario

### Al abrir la app

- Ventana sin barra de menús: **todo está dentro de la ventana**.
  - **Nombre de este Mac (alias)**: editable con el campo y el botón
    *Aplicar* (se guarda y se re-anuncia).
  - **Carpeta de descarga**: se muestra abajo del nombre; el botón
    *Cambiar…* abre el selector de carpetas.
  - **Tabla de dispositivos** en tiempo real (nombre, modelo, dirección).
    Doble clic sobre uno para enviarle archivos.
  - **Botones de idioma** en la parte inferior (ver §5).
  - **Registro** con todo lo que pasa (envíos, recepciones, errores).

### Recibir archivos

No hay que hacer nada: el servidor HTTP escucha en el **53317** y
**acepta automáticamente** las solicitudes (no hay diálogo de
“Aceptar/Rechazar” en esta versión ligera). Cada archivo se guarda
en la carpeta de descarga, verificando su **SHA-256**; si el
checksum no coincide, el archivo se descarta y se registra el error.
Si ya existe un archivo con el mismo nombre, se guarda como
`nombre (1).ext`, `nombre (2).ext`, etc.

### Enviar archivos

SnowSend funciona como la app oficial: **primero preparas la lista de archivos
y se queda ahí hasta que la vacíes.**

1. Pulsa **Añadir archivo…** (puedes seleccionar varios a la vez) o **Pegar
   portapapeles**. Los archivos se añaden a **Archivos para enviar**; todavía
   no se envía nada.
2. Repite las veces que quieras: puedes mandar todo a un dispositivo y luego
   la misma lista a otro.
3. Selecciona el dispositivo en la tabla y pulsa **Enviar al dispositivo**.
4. Acepta el aviso en el otro dispositivo en menos de 60 s (lo ves en
   *Actividad*).
5. ¿Te arrepientes a mitad? **Cancelar envío** lo aborta: se deja de enviar,
   se cierra la conexión (el receptor descarta el archivo incompleto) y se
   envía `POST /api/localsend/v2/cancel` para limpiar la sesión allí.
6. La lista **no** se vacía al enviar: usa **Quitar** (admite selección
   múltiple) o **Vaciar lista** cuando termines.

Notas:

- **Pegar portapapeles** toma el texto del portapapeles y lo añade como
  `clipboard-AAAAMMDD-HHMMSS.txt` (UTF-8) en tu carpeta temporal, igual que la
  función de texto de la app oficial. Las imágenes aún no están soportadas.
- Los archivos se leen del disco en tramos de 256 KB: cancelar funciona incluso
  a mitad de un archivo grande y nunca se carga el archivo entero en memoria.
- La lista solo vive mientras la app está abierta; no se guarda en disco.

### Pantallas pequeñas (MacBook Air de 11", 1366 × 768)

La ventana **se ajusta sola a tu pantalla** en vez de suponer un monitor grande.
Al arrancar, SnowSend mide la pantalla; si el tamaño natural no cabe, primero
encoge el registro de actividad, luego la tabla de dispositivos y luego la lista
de archivos. Los **botones de idioma y la línea de estado van anclados al borde
inferior** (Tk `side=bottom`) **antes que nada**, así que siempre se ven y nunca
son lo que se recorta. La ventana se centra en horizontal, se mantiene dentro
del área útil (descontando barra de menús y barra de título) y se reajusta cada
vez que cambias de idioma, porque los textos cambian de ancho.

Medidas reales: pantalla 1366 × 768 → ventana de unos **700 × 658**; pantalla
1024 × 600 → **700 × 490** con registro de 3 líneas. No se esconde nada y no
hace falta barra de desplazamiento.

### Cerrar

Cierra la ventana. Si algo falla al arrancar, mira el registro:

```
~/Library/Logs/SnowSend.log
```

---

## 5. Idiomas

Toda la interfaz — ventana, menús, botones, diálogos, barra de estado **y
todos los mensajes del registro** — está traducida a cinco idiomas:

| Código | Idioma | Notas |
|---|---|---|
| `en` | English | idioma por defecto si no hay coincidencia |
| `es` | Español | |
| `fr` | Français | |
| `de` | Deutsch | |
| `pt` | Português | |

- Al arrancar por primera vez, SnowSend lee el idioma del sistema
  (`AppleLocale`, `LANG`, `LC_ALL`) y elige el que coincida; si no hay
  coincidencia, usa inglés.
- Se cambia en caliente con los **cinco botones de la parte inferior de la
  ventana** (`English | Español | Français | Deutsch | Português`). Cambian al
  instante los textos de la ventana, las cabeceras de la tabla, la barra de
  estado y todos los mensajes nuevos del registro, y la elección se guarda en
  `~/.snowsend_config.json`.
- Desde la terminal: `python snowsend.py --lang de`.

Las traducciones viven en un único diccionario `STRINGS` al principio de
`snowsend.py`, con una entrada por clave. Añadir un idioma es copiar una
columna y traducirla: el test `tests/test_i18n.py` falla si falta una clave
en algún idioma o si una traducción pierde sus marcadores `%s`.

## 6. Protocolo implementado (LocalSend v2)

Referencia: <https://github.com/localsend/protocol>

- **Descubrimiento:** anuncio UDP multicast a `224.0.0.167:53317`
  con JSON `{alias, version:"2.0", deviceModel:"Mac OS X 10.6",
  deviceType:"desktop", fingerprint, port:53317, protocol:"http",
  download:false, announce:true}`. Al recibir un anuncio con
  `announce:true` se responde con `POST /register` al remitente
  (y también se acepta la respuesta multicast con `announce:false`).
  El *fingerprint* es una cadena aleatoria persistente guardada en
  `~/.localsend_10_6_fingerprint` (en modo HTTP la especificación
  define el fingerprint como aleatorio, no como hash de certificado).
- **Servidor HTTP** (base `/api/localsend/v2`):
  - `GET  /info` → información del dispositivo.
  - `POST /register` → registro mutuo de descubrimiento.
  - `POST /prepare-upload` → recibe `{info, files:{id:{fileName,size,fileType,sha256}}}`,
    devuelve `{sessionId, files:{id:token}}` (formato v2.2; también
    se acepta el formato antiguo en lista al recibir).
  - `POST /upload?sessionId=…&fileId=…&token=…` → cuerpo binario del
    archivo; verifica SHA-256 y responde `422` si no coincide.
  - `POST /cancel?sessionId=…` → cancela una sesión.
- **Cliente HTTP:** `prepare-upload` → `upload` por archivo, con
  reintento automático en HTTP plano si el destino anunció HTTPS
  (caso en que el usuario olvidó desactivar el cifrado).
- **Respaldo sin multicast:** botón *Escanear red* (`GET /info` a
  cada IP del `/24`).

**Limitaciones conocidas (asumidas para 10.6):**

- Solo HTTP plano (ver §3). Sin PIN, sin transferencia inversa
  (*download API*), sin WebRTC ni relay.
- Recepción con **aceptación automática** (sin diálogo de confirmación).
- Envío lee cada archivo en memoria para el `POST` (archivos muy
  grandes, de varios GB, pueden tardar / usar mucha RAM en un Mac
  antiguo; para uso normal es correcto).

---

## 7. Solución de problemas

| Síntoma | Qué revisar |
|---|---|
| El Snow Leopard no aparece en el móvil | ¿Cifrado desactivado en el móvil? (§3) ¿Mismo Wi-Fi? ¿Puerto 53317 en ambos? Pulsa *Anunciar / Refrescar* y *Escanear red*. |
| El móvil no aparece en el Snow Leopard | ¿Cifrado desactivado en el móvil? Algunos routers/Android bloquean multicast: usa **Escanear red**. |
| “Error en prepare-upload” al enviar | El destino probablemente sigue en HTTPS. Desactiva Encryption allí y reintenta. Mira el registro en ambos equipos. |
| El registro dice “El dispositivo NO acepta HTTP plano por el puerto 53317” | El iPhone/iPad tiene **Encryption activado**: su servidor solo habla HTTPS y Snow Leopard no soporta TLS moderno. Desactívalo (§3), cierra y abre LocalSend en el móvil, y pulsa *Reanunciar*. |
| Se queda en “Esperando aceptacion en …” | Hay que tocar **Aceptar** en el aviso del iPhone dentro de los 60 s. Si no aparece, el móvil tiene el cifrado activado o está en otra red. |
| “Respuesta no JSON (status …)” con cuerpo crudo | Es el cuerpo exacto que devolvió el móvil; pégalo si pides ayuda. Con cifrado desactivado no debería aparecer. |
| La app no abre al hacer doble clic | Revisa `~/Library/Logs/SnowSend.log`. Si copiaste la carpeta sin ZIP, re-aplica `chmod +x …/Contents/MacOS/launcher` (§2). |
| Puerto 53317 ocupado | Cierra otra copia de LocalSend o cambia el puerto con `--port` en modo headless (ver §7). |
| Firewall | En el Mac moderno permite LocalSend en el firewall; en el Snow Leopard, *Preferencias del Sistema → Seguridad → Firewall* debe permitir conexiones entrantes para `python`. |
| Archivos llegan pero con checksum incorrecto | No debería pasar (se verifica SHA-256). Revisa el registro; el archivo corrupto se elimina automáticamente. |

---

## 8. Para desarrolladores / pruebas

Verificar sintaxis (válido en Python 2.7 y en Python 3):

```sh
python3 -m py_compile snowsend.py   # en un Mac moderno
/usr/bin/python -m py_compile snowsend.py   # en Snow Leopard
```

Modo sin GUI (útil para pruebas o para dejarlo corriendo en un
Mac viejo sin pantalla):

```sh
python snowsend.py --headless --alias MiMac --port 53317 --download-dir ~/Downloads
```

Reconstruir el paquete (opcionalmente con tu propio icono:
coloca un `icon.png` de hasta 512×512 junto a `build_app.sh`
antes de compilar; en el Mac se convertirá con `sips`/`iconutil`
a `AppIcon.icns`, y si no hay icono se genera uno placeholder):

```sh
chmod +x build_app.sh
./build_app.sh
```

Antes de publicar una versión, comprueba que el paquete quedó completo:
`Info.plist` con `CFBundleName=SnowSend`, `Contents/MacOS/launcher`
ejecutable y `Contents/Resources/` con `snowsend.py`, `LICENSE.txt` y
`AppIcon.icns`.

Pruebas automáticas incluidas en `tests/` (se ejecutan con Python 3 en
cualquier máquina; no hacen falta el Mac ni el móvil):

```sh
python3 tests/test_server_regression.py     # /info, /register, chunked,
                                            # Content-Length, 100-continue,
                                            # 422 por SHA, multicast
python3 tests/test_send_fake_iphone.py      # envio a un "iPhone falso" (modo normal)
MODE=chunked python3 tests/test_send_fake_iphone.py   # respuesta chunked/gzip/close
python3 tests/test_register_and_diagnose.py # registro HTTP-first + diagnostico
python3 tests/test_i18n.py                  # completitud de las 5 traducciones
python3 tests/test_gui_stub.py              # GUI, cola y portapapeles en 5 idiomas
python3 tests/test_cancel.py                # cancelar a mitad y entre archivos
```

---

## 9. Seguridad

- Este cliente habla **HTTP sin cifrar** por necesidad de
  compatibilidad con 10.6. Úsalo **solo en tu LAN de confianza**.
- Acepta archivos automáticamente: revisa periódicamente la
  carpeta de descarga y no aceptes archivos de redes desconocidas.
- El SHA-256 se verifica en recepción, pero sin TLS no hay
  autenticación del remitente: cualquier equipo de tu red podría
  enviarte un archivo. Es el mismo modelo de confianza que el
  propio LocalSend en modo sin cifrado.

---

## 10. Proyecto realizado con ayuda de IA

Este proyecto se desarrolló en **colaboración con un asistente de IA**
(agente de Arena.ai), en un proceso iterativo de escribir, probar y
corregir: el código, el empaquetado y esta documentación se generaron
y revisaron con esa ayuda, partiendo de las indicaciones, pruebas en
hardware real (un Mac con Snow Leopard y un iPhone) y correcciones del
autor del proyecto.

Qué significa esto en la práctica:

- **Revisa el código antes de confiar en él.** Se ha probado (recepción
  y envío reales, tests de regresión en el propio repositorio), pero
  ningún software está libre de errores y este no tiene auditoría de
  seguridad formal.
- **Se entrega “tal cual”, sin garantía** (ver la licencia, §10).
- **No sustituye a la app oficial.** SnowSend existe porque la app
  oficial ya no se ejecuta en Snow Leopard; no pretende ser un reemplazo
  en sistemas modernos.
- Las decisiones de diseño, la elección de licencia y la
  responsabilidad sobre lo publicado son del autor del proyecto.

---

## 11. Licencia y parámetros legales

### Licencia elegida: MIT

El proyecto se publica bajo **licencia MIT** (archivo [`LICENSE`](LICENSE),
también incluido en `SnowSend.app/Contents/Resources/LICENSE.txt`).

MIT permite usar, copiar, modificar, fusionar, publicar, distribuir,
sublicenciar y vender el software, con dos condiciones:

1. Conservar el aviso de copyright y la licencia en las copias o
   partes sustanciales del software.
2. No hay garantía: el software se entrega “AS IS”. El autor no responde
   de daños o pérdidas de datos.

**Por qué MIT y no otra:**

| Licencia | Cuándo conviene | Situación de SnowSend |
|---|---|---|
| **MIT** (elegida) | Quieres que cualquiera pueda usar, modificar y redistribuir con la mínima fricción, también en productos cerrados o comerciales. | Es lo que mejor encaja: es un *port* de utilidad para hardware antiguo, sin interés en forzar la apertura de derivados. |
| Apache-2.0 | Igual que MIT pero con **concesión explícita de patentes** y cláusula de marcas; es la que usa la app oficial LocalSend. | Alternativa válida si te preocupan las patentes o si quieres alinearte con el ecosistema LocalSend. Cambiarla es sustituir un archivo. |
| GPL-3.0 | Quieres obligar a que cualquier versión modificada siga siendo libre y abierta. | **No recomendada aquí**: impide mezclarla con código de licencias incompatibles y añade obligaciones (entrega de fuentes) a quien redistribuya el `.app`. |

### Puntos legales revisados

1. **¿Se copió código de LocalSend? No.** Todo `snowsend.py` es código
   original escrito para este proyecto; no hay código Dart de LocalSend
   ni de terceros traducido ni portado. Por eso **no hereda** la licencia
   Apache-2.0 de la app oficial: se puede licenciar libremente (MIT).
2. **El repositorio del protocolo (`localsend/protocol`) no declara
   licencia** (no tiene archivo `LICENSE`; GitHub lo reporta como “sin
   licencia”). Por eso aquí **no se reproduce su texto**: se usa solo como
   referencia funcional para lograr interoperabilidad, y los endpoints,
   campos JSON y puertos se han reescrito con redacción propia. La
   interoperabilidad en sí (hablar el mismo protocolo en la red) no está
   restringida por derechos de autor.
3. **La app oficial es Apache-2.0.** No se ha reutilizado su código, así
   que no hay obligaciones de `NOTICE` ni de atribución obligatoria; aun
   así, se le da crédito expresamente en §11 por cortesía y honestidad.
4. **Proyectos GPL-3.0** (por ejemplo `theanazerka/unlocalsend`):
   se consultaron solo **observaciones públicas de comportamiento** (que
   iOS envía los cuerpos en `chunked`), nunca su código. Copiar código
   GPL-3.0 habría obligado a liberar SnowSend bajo GPL-3.0; **no se ha
   hecho**.
5. **Marcas.** “LocalSend”, su logotipo y el nombre del proyecto son de
   sus autores. Por eso la app se llama **SnowSend**: se evita cualquier
   confusión o uso indebido de marca. Las menciones del tipo
   “compatible con LocalSend” son uso descriptivo/nominativo (indicar
   con qué es compatible), no una reivindicación de la marca. **SnowSend
   no está afiliado ni respaldado por LocalSend.**
6. **Apple.** macOS, Mac OS X, Snow Leopard, Aqua, Finder e `iconutil`
   son marcas de Apple Inc. SnowSend no está afiliado a Apple.
7. **Python y Tk.** El paquete **no redistribuye** Python: usa el
   `/usr/bin/python` que ya viene con el sistema. Python es software de
   la Python Software Foundation (licencia PSF) y Tk/Tcl tiene su propia
   licencia permisiva; al no incluirse binarios en el ZIP, no se añaden
   obligaciones de redistribución.
8. **Contenido del `.app`**: incluye el aviso de copyright y la licencia
   dentro del paquete (`Contents/Resources/LICENSE.txt`), que es lo que
   MIT exige al distribuir el binario.
9. **Sin telemetría ni red externa.** SnowSend no envía datos a ningún
   servidor ni recoge información del usuario; solo abre sockets en la
   red local (UDP 53317 para descubrimiento, TCP 53317 para HTTP).
   Ojo: el modo HTTP plano transporta los archivos **sin cifrar** por tu
   red local (§8).
10. **Exención de responsabilidad.** Software de utilidad, sin garantía,
    pensado para redes locales de confianza y para uso personal. Si lo
    redistribuyes, mantén el archivo `LICENSE` y el aviso de copyright.

> **Si quieres otro titular de derechos**, cambia la línea
> `Copyright (c) 2026 SnowSend contributors` de `LICENSE` por tu nombre
> (o el de tu organización) y la misma línea en
> `Contents/Resources/LICENSE.txt` tras reconstruir con `./build_app.sh`.
> Si prefieres Apache-2.0, basta con sustituir el contenido de `LICENSE`
> por el texto oficial de Apache License 2.0 y añadir un `NOTICE`.

---

## 12. Agradecimientos

Sin estos proyectos, SnowSend no existiría. Gracias a:

- **[LocalSend](https://github.com/localsend/localsend)** (Tien Nam Do y
  colaboradores, licencia Apache-2.0) — la app de código abierto que
  inspiró todo esto y con la que SnowSend es compatible. Aquí empezó la
  idea de “AirDrop sin nube”.
- **[LocalSend Protocol v2.2](https://github.com/localsend/protocol)**
  (organización LocalSend) — la especificación de descubrimiento
  multicast, `register`, `prepare-upload`, `upload`, `cancel` e `info`
  que se ha implementado. Referencia funcional, no texto copiado.
- **[hermes-localsend](https://github.com/tylerbrevard/hermes-localsend)**
  (tylerbrevard, licencia MIT) — implementación del protocolo v2.2 solo
  con la librería estándar de Python; sus notas públicas sobre el
  `Transfer-Encoding: chunked` de iOS fueron clave para arreglar la
  recepción de archivos desde el iPhone.
- **[unlocalsend](https://github.com/theanazerka/unlocalsend)**
  (theanazerka, licencia GPL-3.0) — cliente de LocalSend para iOS
  antiguo, útil para entender cómo se comporta el lado iOS. Solo se
  tomaron ideas de comportamiento; **no se copió código**.
- **Proyecto Python** y sus bibliotecas estándar (`Tkinter`,
  `BaseHTTPServer`, `httplib`, `socket`, `json`, `hashlib`, `threading`),
  mantenidas por la Python Software Foundation y la comunidad.
- **Tcl/Tk** — el toolkit detrás de la interfaz, incluido en Mac OS X.
- **Apple** — por Mac OS X 10.6 Snow Leopard y su intérprete de Python
  preinstalado, que hacen posible que este Mac siga siendo útil.
- Al **autor del proyecto**, por probar en hardware real, reportar los
  fallos exactos (multicast `Errno 49`, `422` de checksum, `prepare-upload`
  sin JSON) y validar cada versión.
- **Asistente de IA de Arena.ai** — por escribir, depurar y documentar
  junto al autor; ver §9.

---

*SnowSend es un proyecto independiente y no oficial, sin relación con
LocalSend, Apple Inc. ni con los autores de los proyectos citados.
“LocalSend” es un nombre del proyecto LocalSend; “macOS”, “Mac OS X” y
“Snow Leopard” son marcas de Apple Inc.*

---

## 13. Historial de cambios

### v1.7 (2.0.7-10.6) — La ventana cabe en pantallas de 11"

1. **La barra inferior (botones de idioma y texto de estado) ya no se pierde en
   pantallas pequeñas.** La ventana medía 800 × 740 fijos; un MacBook Air de 11"
   es 1366 × 768, y tras la barra de menús y la de título solo quedan ~658 px, así
   que el pie se salía de la pantalla. Ahora el pie se empaqueta con
   `side=bottom` **primero**, de modo que Tk le reserva su espacio y lo que falte
   se le resta al registro de actividad.
2. **`fit_to_screen()`**: al arrancar (y cada vez que cambias de idioma) la
   ventana mide `winfo_screenwidth/height` y, si el tamaño natural no cabe,
   encoge el registro, luego la tabla de dispositivos y luego la lista de
   archivos —hasta un mínimo de 3 líneas— antes de limitar la ventana al área
   útil. Se centra en horizontal y nunca es mayor que la pantalla; el `minsize`
   sale de esos mismos números, así que la ventana no puede quedar fuera.
3. **Diseño compacto**: ventana 800 × 740 → ~700 × 658, márgenes 14/12 → 12/10,
   tabla de dispositivos 7 → 5 filas, registro 8 → 5 líneas, lista de archivos
   5 → 4 filas. La misma información con ~90 px menos de alto.
4. **La frase larga de "desactiva Encryption" ya no se duplica ni se sale del
   pie**: ahora hay una versión corta (`HTTP :53317 - Encryption OFF en el otro
   dispositivo`) con `wraplength` que sigue el ancho de la ventana.
5. **Comprobaciones nuevas** en `tests/test_gui_stub.py` (78 en total): el Tk
   falso modela `winfo_screenwidth/height`, `winfo_reqheight`, `geometry` y
   `minsize`, así que las pruebas verifican que la ventana cabe en 1366 × 768
   **y** en 1024 × 600, que el pie se empaqueta desde abajo, que el registro baja
   a 3 líneas y no menos, y que el texto corto del pie existe en los 5 idiomas.
6. Versión 1.7 (`2.0.7-10.6`).

### v1.6 (2.0.6-10.6) — Cola de archivos, portapapeles y cancelar

1. **Arreglado el `\u2026` que salía en algunos botones.** Esas etiquetas
   estaban escritas como cadenas normales (de bytes) con escapes `\uXXXX`, y
   **Python 2 no interpreta esos escapes en cadenas de bytes**, así que en Snow
   Leopard el botón mostraba literalmente `\u2026`. Ahora las 478 entradas del
   catálogo son literales unicode `u"…"`, con lo que acentos y puntos suspensivos
   se ven bien en Python 2.6/2.7.
2. **Los archivos se encolan en vez de enviarse al instante**, como en el
   LocalSend real: *Añadir archivo…* (selección múltiple) y *Pegar
   portapapeles* llenan la lista **Archivos para enviar**, que **no** se vacía
   tras enviar, de modo que el mismo lote se puede mandar a otro dispositivo o
   repetir tras un fallo. Solo *Quitar* (selección múltiple) y *Vaciar lista*
   la vacían.
3. **Cancelar una transferencia en curso**: el botón *Cancelar envío* detiene la
   subida, cierra el socket (el receptor descarta el archivo incompleto) y envía
   `POST /api/localsend/v2/cancel` para limpiar la sesión.
4. **Las subidas se envían por tramos de 256 KB** (`http_post_file`) en vez de
   leer el archivo entero en memoria: los archivos grandes ya no son un
   problema de memoria y la cancelación puede cortar a mitad de archivo.
5. **Pegar portapapeles** envía el texto del portapapeles como archivo
   `clipboard-AAAAMMDD-HHMMSS.txt`, igual que la función de texto de la app
   oficial.
6. **Pruebas nuevas:** `tests/test_cancel.py` (10 comprobaciones: cancelar antes
   de empezar, a mitad de archivo, entre archivos, petición `/cancel`, envío
   normal completo) y `tests/test_gui_stub.py` sube a 61 (cola de archivos, no
   duplicar, quitar/vaciar, pegar portapapeles con UTF-8, aviso de portapapeles
   vacío).
7. Versión 1.6 (`2.0.6-10.6`).

### v1.5 (2.0.5-10.6) — Cambio de idioma arreglado, fuera la barra de menús

1. **Se elimina la barra de menús.** En Tk 8.5/Aqua de Snow Leopard no se puede
   reetiquetar la barra de menús global sin romperla: Tk añade su propio menú de
   aplicación, los índices se desplazan y aparecían **menús duplicados y una
   entrada con caracteres basura** (`Ú/2026`). Todo vuelve a estar dentro de la
   ventana, como antes.
2. **El cambio de idioma ahora sí funciona**, y con un control visible en vez
   de un menú: cinco botones de radio en la parte inferior de la ventana. Al
   pulsarlos se llama directamente a `change_language()`, que retraduce todos
   los widgets, las cabeceras de la tabla, la barra de estado y el pie, escribe
   el cambio en el registro, actualiza la lista de dispositivos sin perderla y
   guarda la elección en `~/.snowsend_config.json`.
3. **Se eliminan los diálogos de Preferencias y Acerca de** (sus controles —
   nombre, idioma, carpeta de descarga — están en la ventana principal), que
   eran los últimos sitios donde una traducción obsoleta podía quedarse.
4. **Se quitan 16 claves de traducción muertas** del catálogo (entradas de menú
   y de diálogo que ya no existen); el catálogo queda en 97 claves × 5 idiomas,
   verificado por `tests/test_i18n.py`.
5. **`tests/test_gui_stub.py` sube a 47 comprobaciones**: ahora pulsa cada uno
   de los cinco botones de idioma y verifica que cambian los textos de los
   botones, las cabeceras, la barra de estado y la configuración guardada —
   exactamente la regresión reportada.
6. Versión 1.5 (`2.0.5-10.6`).

### v1.4 (2.0.4-10.6) — Cinco idiomas, interfaz estilo Mac, documentación en inglés

1. **La interfaz habla cinco idiomas**: inglés, español, francés, alemán y
   portugués. No solo la ventana: menús, botones, diálogos, barra de estado y
   **todos los mensajes del registro** pasan por un catálogo único `STRINGS` y
   la función `T()`. El idioma se detecta del sistema al arrancar, se puede
   cambiar en caliente desde el menú **Idioma** o en
   **Preferencias → Idioma**, se recuerda en `~/.snowsend_config.json` y se
   puede forzar con `--lang en|es|fr|de|pt`.
2. **Rediseño como app de Mac OS X**: barra de menús global (Acerca de,
   Preferencias… ⌘,, Salir, Dispositivo, Ventana, Idioma), cabecera con el
   nombre de la app y el estado del servidor, **tabla de dispositivos**
   (nombre / modelo / dirección) en lugar de una lista simple, panel de
   actividad monoespaciado con color para errores y avisos, y barra de estado
   con listo, número de dispositivos e idioma. Doble clic en un dispositivo
   para enviar. Usa `ttk` (tema nativo Aqua) si está disponible y cae a los
   widgets clásicos de Tk si no.
3. **Ventana de Preferencias** para cambiar el nombre del Mac, el idioma y la
   carpeta de descarga, todo persistente entre arranques.
4. **README principal en inglés**; la versión española queda como
   `README.es.md` (este archivo).
5. **Pruebas nuevas:** `tests/test_i18n.py` (17 comprobaciones: completitud de
   los cinco idiomas, paridad de marcadores `%s`, `T()`, detección del idioma
   del sistema, configuración persistente) y `tests/test_gui_stub.py` (35
   comprobaciones: la ventana se construye en los cinco idiomas sin pantalla,
   tabla de dispositivos, avisos, Preferencias/Acerca de, cierre).
6. Versión 1.4 (`2.0.4-10.6`) en `Info.plist`, `VERSION` y `APP_VERSION`.

### v1.3 (2.0.3-10.6) — Renombrado a SnowSend, licencia y créditos

1. **La app se llama ahora `SnowSend.app`** (antes `LocalSend.app`).
   Cambian el nombre visible en Finder, el título de la ventana
   (`SnowSend - Snow Leopard`), el `CFBundleName`/`CFBundleIdentifier`
   (`org.snowsend.SnowSend`) y el archivo de código, que pasa a
   `snowsend.py`. En el terminal:
   `Contents/Resources/snowsend.py`.
2. **Nuevo registro en `~/Library/Logs/SnowSend.log`**
   (antes `LocalSend10_6.log`). Si vas a reportar un fallo, es ese
   archivo el que hay que mirar.
3. **El fingerprint se conserva.** Se guarda en `~/.snowsend_fingerprint`
   y, si existe el antiguo `~/.localsend_10_6_fingerprint`, se migra
   automáticamente para seguir siendo el mismo equipo en la lista de los
   móviles (no hay que volver a aceptar el dispositivo).
4. **Licencia MIT** (`LICENSE`, incluida también dentro del paquete como
   `Contents/Resources/LICENSE.txt`) y **§10 con el análisis legal**:
   código original sin copiar de LocalSend, sin reproducir el texto del
   protocolo, sin código GPL-3.0, y aviso de marca (SnowSend no está
   afiliado a LocalSend ni a Apple).
5. **§9: el proyecto se declara como realizado con ayuda de IA** y
   **§11: agradecimientos** a LocalSend, al protocolo v2.2,
   hermes-localsend, unlocalsend, Python, Tcl/Tk y Apple.
6. El nombre “LocalSend” ya solo se usa para indicar **compatibilidad**
   con el protocolo y con la app oficial (uso descriptivo), no como
   nombre del producto.

### v1.2 (2.0.2-10.6) — Envío del Mac al iPhone (prepare-upload)

**Síntoma:** al enviar desde la Mac, el registro mostraba
`Preparando envio a … (https://192.168.1.76:53317)`,
`Fallo con https (…SSL23_GET_SERVER_HELLO:unknown protocol), reintentando con http plano…`
y terminaba con `Error en prepare-upload: No JSON object could be decoded`.

1. **El cliente ya no intenta TLS primero.** Snow Leopard no puede
   negociar TLS moderno, así que el envío empieza siempre por
   **HTTP plano** (`http://IP:53317`) y solo usa el protocolo anunciado
   como respaldo. El registro ahora dice
   `Preparando envio a … (http://192.168.1.76:53317)` y desaparece el
   error de `SSL23_GET_SERVER_HELLO`.

2. **Cliente HTTP reescrito con `httplib`/`http.client` directo.** El
   `urllib2` de Python 2.6 devolvía cuerpos que no podía interpretar
   (respuestas `chunked`, `gzip`, sin `Content-Length` o cerradas por el
   iPhone), y `json.loads()` fallaba con *No JSON object could be
   decoded*. Ahora se leen estado + cabeceras + cuerpo crudo y el JSON
   se extrae con varios intentos: descompresión gzip/deflate,
   decodificación `chunked` manual, BOM UTF-8 y extracción del primer
   objeto `{...}` del cuerpo. Si aun así no es JSON, el registro muestra
   **el cuerpo crudo y las cabeceras** en lugar de un mensaje opaco.

3. **Espera de 60 s para aceptar en el iPhone.** Antes eran 15 s: si no
   tocabas «Aceptar» a tiempo, la conexión se cortaba y el error
   parecía otra cosa. El registro avisa:
   `Esperando aceptacion en … (acepta en el iPhone si aparece el aviso)`.

4. **Diagnóstico automático del receptor cuando el envío falla.** Se
   consulta `GET /api/localsend/v2/info` por HTTP plano y, si el
   dispositivo no contesta (basura binaria, cuerpo vacío, conexión
   cerrada), se avisa sin rodeos:

   ```
   >>> El dispositivo NO acepta HTTP plano por el puerto 53317.
   >>> En el iPhone abre LocalSend > Ajustes (engranaje) y pon Encryption en OFF,
   >>> cierra y vuelve a abrir LocalSend, luego pulsa 'Reanunciar' aqui.
   ```

   Ese es el caso más frecuente: **si el iPhone tiene el cifrado
   activado, su servidor solo habla HTTPS y la Mac nunca podrá
   enviarle** (Snow Leopard no soporta TLS 1.2). Desactivar
   *Encryption* en el iPhone es obligatorio en ambos sentidos.

5. **Registro al iPhone por HTTP primero.** `register_callback` prueba
   `http` antes que el protocolo anunciado, así que el Mac aparece en la
   lista del iPhone sin errores de TLS en el registro.

6. Los errores con bytes binarios (por ejemplo la alerta TLS del iPhone)
   se muestran escapados (`\x15\x03…`) y nunca rompen la interfaz.

Si vienes de la v1.1, **sustituye la app por esta v1.2**.

### v1.1 (2.0.1-10.6) — Correcciones iPhone + macOS detectadas en uso real

1. **Recepción desde iPhone fallaba con `422 checksum SHA256 no coincide`**
   (archivo de 4 bytes, `prepare-upload` 200 pero `upload` 422).
   Causa: iOS LocalSend envía `prepare-upload` y `upload` con
   `Transfer-Encoding: chunked` y **sin** `Content-Length`. El receptor
   solo leía `Content-Length`, así que el cuerpo llegaba como 0 bytes,
   el archivo quedaba vacío y el SHA-256 no coincidía.
   Corrección: decodificación `chunked` completa (tamaños hex, trailers,
   streaming a disco con SHA-256 al vuelo) tanto para JSON como para
   archivos, más respuesta explícita a `Expect: 100-continue`
   (`protocol_version = HTTP/1.1` + `handle_expect_100()`), sin la cual
   cliente y servidor quedan en deadlock. Ahora en el registro se ve:
   `upload: … Transfer-Encoding=chunked` y `Archivo recibido: … (4 bytes)`.

2. **`[Errno 49] Can't assign requested address` al anunciar multicast**
   (lista de dispositivos vacía en el Mac, aunque el iPhone sí lo
   encontraba por escaneo HTTP).
   Causa: en macOS/BSD enlazar el socket UDP a `224.0.0.167` (o a
   `127.0.0.1`) hace que `sendto()` falle con EADDRNOTAVAIL, aunque en
   Linux funcione. Corrección: enlazar a `INADDR_ANY` (`""`), fijar
   `IP_MULTICAST_IF` con la IP local real (p. ej. `192.168.1.x`,
   obtenida con `connect()` UDP), unirse al grupo con
   `(224.0.0.167, IP_local)` y, si el socket principal no puede enviar,
   reintentar con un socket temporal enlazado a la IP local. En el
   registro ahora aparece: `Descubrimiento multicast activo en
   224.0.0.167:53317 (IP local 192.168.1.x)`.

3. **`SSL routines:SSL23_GET_SERVER_HELLO:unknown protocol` al registrarse**
   en el iPhone. Causa: el iPhone anuncia `protocol:https` aunque el
   cifrado esté desactivado; el cliente intentaba TLS contra un
   servidor HTTP plano. Corrección: `register_callback` prueba el
   protocolo anunciado y, si falla, reintenta con `http` (y luego
   `https`), actualizando el protocolo guardado del dispositivo.

Si vienes de la v1.0, **sustituye la app por esta v1.1**
(no hay que cambiar nada más; la carpeta de descarga y el alias se
conservan).

---
