# SnowSend — LocalSend para Mac OS X 10.6 Snow Leopard

Cliente del **protocolo LocalSend v2** escrito en Python 2.6/2.7, con
interfaz Cocoa nativa a través del PyObjC incluido en Snow Leopard y el
resto basado en la librería estándar. Se empaqueta como **`SnowSend.app`**
(doble clic, sin Terminal).

**SnowSend** es un proyecto independiente: implementa el protocolo
LocalSend desde cero para que un Mac con Snow Leopard pueda intercambiar
archivos con móviles y ordenadores modernos que usan la app oficial.
No está afiliado, patrocinado ni respaldado por el proyecto LocalSend.

```
┌─────────────────────────────┐        HTTP plano :53317        ┌──────────────────────────────┐
│  Mac Snow Leopard (10.6)    │  ◄───────────────────────────►  │  Móvil / Mac moderno        │
│  SnowSend.app               │     multicast UDP 224.0.0.167   │  App oficial LocalSend       │
│  /usr/bin/pythonw (2.6/2.7) │     descubrimiento + archivos   │  Encryption: OFF             │
│  AppKit + BaseHTTPServer    │                                 │  (ver §3, imprescindible)    │
└─────────────────────────────┘                                 └──────────────────────────────┘
```

> **Por qué HTTP plano:** Snow Leopard no soporta de forma fiable
> TLS 1.2/1.3 moderno ni el certificado autofirmado con *fingerprint
> pinning* que usa LocalSend por defecto (HTTPS). Por eso este cliente
> habla **HTTP sin cifrar en el puerto 53317**. Úsalo solo en tu red
> local de confianza.

**Versión:** 1.4.1 (`2.0.3-10.6`) · **Licencia:** MIT (ver §10) ·
**Estado:** proyecto personal, asistido por IA (§9)

> **In English (short version).** SnowSend is a small, dependency-free
> Python 2.6/2.7 client of the **LocalSend protocol v2** that runs on
> **Mac OS X 10.6 Snow Leopard** (where the official Flutter app no
> longer works). It speaks **plain HTTP on port 53317** (Snow Leopard
> can't do modern TLS), discovers devices over multicast UDP
> 224.0.0.167, receives *and* sends files, and ships as a
> double-clickable `SnowSend.app`. Turn **Encryption = OFF** in the
> official LocalSend app on the other device. Not affiliated with
> LocalSend or Apple. MIT licensed. Full docs in Spanish below.

---

## 0. Empezar en 30 segundos

```sh
git clone https://github.com/TU_USUARIO/snowsend.git
cd snowsend
chmod +x build_app.sh && ./build_app.sh   # crea SnowSend.app
```

Después copia `SnowSend.app` (o su ZIP) al Mac con Snow Leopard.
Si el release no incluye `SnowSend.zip`, descarga el ZIP de código fuente
y ejecuta `sh build_app.sh` para generar el paquete en el Mac.

---

## 1. Contenido de este proyecto

| Archivo | Para qué sirve |
|---|---|
| `snowsend.py` | Código fuente (barra de menús nativa AppKit/PyObjC + servidor HTTP + descubrimiento multicast + cliente de envío). Compatible con Python 2.6/2.7 y Python 3 (modo headless). |
| `build_app.sh` | Script que genera `SnowSend.app` (Info.plist, launcher, icono). |
| `SnowSend.app/` | **La aplicación lista para copiar al Snow Leopard** y abrir con doble clic. |
| `SnowSend.zip` | El mismo `.app` comprimido en ZIP (recomendado para transferirlo, ver §2). |
| `README.md` | Este archivo. |
| `LICENSE` | Licencia MIT del proyecto. También se copia dentro del paquete como `Contents/Resources/LICENSE.txt`. |

Estructura del paquete (clásica de Mac OS X 10.6):

```
SnowSend.app/
└── Contents/
    ├── Info.plist          LSUIElement=true (sin Dock), LSMinimumSystemVersion=10.6
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
hacer doble clic **no** se abra una ventana de Terminal) y prefiere
`/usr/bin/pythonw`, el intérprete GUI de Snow Leopard para Cocoa. Solo
usa `/usr/bin/python` como alternativa si `pythonw` no está disponible:

```sh
if [ -x /usr/bin/pythonw ]; then
  PYTHON_BIN=/usr/bin/pythonw
else
  PYTHON_BIN=/usr/bin/python
fi
exec "$PYTHON_BIN" -u "$RESOURCES_DIR/snowsend.py"
```

Sin dependencias externas: nada de `pip`, `requests`, `flask`,
`PyInstaller` ni `py2app`. La interfaz usa únicamente **AppKit y Foundation
(PyObjC incluido por Apple en Snow Leopard)**; la red usa módulos de la
librería estándar de Python (`socket`, `struct`, `json`, `threading`,
`BaseHTTPServer`, `urllib2`, `hashlib`, `uuid`, `mimetypes`, `os`, `sys`).

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
5. Doble clic en `SnowSend.app`. Aparece **SnowSend** en la barra de menús; no abre ventana ni muestra icono en el Dock.

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

### Barra de menús

Al abrir SnowSend aparece el texto **“SnowSend (n)”** en la barra superior,
donde `n` es el número de dispositivos detectados; la app no crea una
ventana y no aparece en el Dock. Haz clic en el título para ver el estado
del servidor HTTP, el alias del equipo y la lista de dispositivos.

- Haz clic en un dispositivo para seleccionarlo (queda marcado).
- Pulsa **Enviar archivo...** y elige un archivo en el panel nativo de Cocoa.
- **Anunciar / Refrescar** vuelve a publicar el equipo por multicast;
  **Escanear red** es un respaldo para routers que bloquean multicast.
- El alias se toma del nombre del equipo. Los mensajes y errores se guardan
  en `~/Library/Logs/SnowSend.log`.

### Recibir archivos

No hay que hacer nada: el servidor HTTP escucha en el **53317** y
**acepta automáticamente** las solicitudes (no hay diálogo de
“Aceptar/Rechazar” en esta versión ligera). Cada archivo se guarda
en la carpeta de descarga, verificando su **SHA-256**; si el
checksum no coincide, el archivo se descarta y se registra el error.
Si ya existe un archivo con el mismo nombre, se guarda como
`nombre (1).ext`, `nombre (2).ext`, etc.

### Enviar archivos

1. Espera a que el dispositivo destino aparezca en el menú
   (o pulsa **Anunciar / Refrescar**; si tu router bloquea el
   multicast, pulsa **Escanear red**, que pregunta por HTTP a cada
   IP del `/24` local).
2. Haz clic en el nombre del dispositivo para seleccionarlo.
3. Abre de nuevo el menú, pulsa **Enviar archivo...** y elige un archivo
   en el panel de selección nativo de Cocoa (`NSOpenPanel`). La transferencia
   corre en segundo plano para no bloquear la barra de menús.
4. El cliente hace la secuencia del protocolo v2:
   `POST /prepare-upload` (metadatos + SHA-256) → el receptor
   devuelve `sessionId` + token por archivo → `POST /upload`
   con el contenido binario del archivo.
5. El progreso y la confirmación quedan en el registro de
   `~/Library/Logs/SnowSend.log`.

### Cerrar

Elige **Salir** en el menú de SnowSend para detener limpiamente el servidor
y el receptor multicast. Si algo falla al arrancar, mira el registro:

```
~/Library/Logs/SnowSend.log
```

---

## 5. Protocolo implementado (LocalSend v2)

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

## 6. Solución de problemas

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

## 7. Para desarrolladores / pruebas

Verificar sintaxis (válido en Python 2.7 y en Python 3):

```sh
python3 -m py_compile snowsend.py   # en un Mac moderno
/usr/bin/python -m py_compile snowsend.py   # en Snow Leopard
```

Modo headless (sin barra de menús; útil para pruebas o para dejarlo
corriendo en un Mac viejo sin pantalla):

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
`Info.plist` con `CFBundleName=SnowSend` y `LSUIElement=true`,
`Contents/MacOS/launcher` ejecutable y `Contents/Resources/` con
`snowsend.py`, `LICENSE.txt` y `AppIcon.icns`.

Pruebas automáticas incluidas en `tests/` (se ejecutan con Python 3 en
cualquier máquina; no hacen falta el Mac ni el móvil):

```sh
python3 tests/test_server_regression.py     # /info, /register, chunked,
                                            # Content-Length, 100-continue,
                                            # 422 por SHA, multicast
python3 tests/test_send_fake_iphone.py      # envio a un "iPhone falso" (modo normal)
MODE=chunked python3 tests/test_send_fake_iphone.py   # respuesta chunked/gzip/close
python3 tests/test_register_and_diagnose.py # registro HTTP-first + diagnostico
```

---

## 8. Seguridad

- Este cliente habla **HTTP sin cifrar** por necesidad de
  compatibilidad con 10.6. Úsalo **solo en tu LAN de confianza**.
- Acepta archivos automáticamente: revisa periódicamente la
  carpeta de descarga y no aceptes archivos de redes desconocidas.
- El SHA-256 se verifica en recepción, pero sin TLS no hay
  autenticación del remitente: cualquier equipo de tu red podría
  enviarte un archivo. Es el mismo modelo de confianza que el
  propio LocalSend en modo sin cifrado.

---

## 9. Proyecto realizado con ayuda de IA

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

## 10. Licencia y parámetros legales

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

## 11. Agradecimientos

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
- **Proyecto Python** y sus bibliotecas estándar (`BaseHTTPServer`,
  `httplib`, `socket`, `json`, `hashlib`, `threading`), mantenidas por la
  Python Software Foundation y la comunidad.
- **Apple / PyObjC** — `AppKit`, `Foundation`, `NSStatusBar` y `NSOpenPanel`
  para una interfaz Cocoa nativa sin dependencias instalables.
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

## 12. Historial de cambios

### v1.4.1 — Corrección del arranque Cocoa

- El launcher usa primero `/usr/bin/pythonw`, requerido por algunas
  aplicaciones GUI de Cocoa en Snow Leopard, y activa el logging sin búfer.
- Si AppKit/PyObjC no está disponible, el arranque normal informa el error
  en el registro en vez de quedarse ejecutando en modo headless sin interfaz.

### v1.4 (2.0.3-10.6) — Interfaz nativa de barra de menús

1. Se reemplaza la ventana Tkinter por un elemento `NSStatusItem` de AppKit;
   el menú muestra estado del servidor, alias y dispositivos detectados.
2. Se selecciona un dispositivo en el menú y **Enviar archivo...** abre un
   `NSOpenPanel` Cocoa nativo. El envío continúa en un hilo de fondo.
3. El paquete configura `LSUIElement=true` para ocultar el Dock y el botón
   **Salir** detiene el servidor HTTP y el receptor multicast limpiamente.
4. No se añaden dependencias: la interfaz usa el PyObjC incluido en
   Snow Leopard y el transporte sigue usando la biblioteca estándar.

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
