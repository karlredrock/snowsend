#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SnowSend - Cliente LocalSend (Protocolo v2) para Mac OS X 10.6 Snow Leopard
=================================================================================
- Python 2.6 / 2.7 ( /usr/bin/python en Snow Leopard ) y Python 3 (para pruebas
  en un Mac moderno). Solo libreria estandar: Tkinter, socket, struct, json,
  threading, BaseHTTPServer, urllib2, hashlib, uuid, mimetypes, os, sys.
- HTTP plano (sin TLS) en el puerto 53317. Snow Leopard no soporta TLS 1.2/1.3
  moderno de forma fiable, por eso en el dispositivo moderno hay que desactivar
  Encryption (ver README.md).
- SnowSend es un proyecto independiente, escrito desde cero en Python, que
  implementa el protocolo LocalSend v2.2 para interoperar con las apps
  oficiales. No esta afiliado ni respaldado por el proyecto LocalSend.
  Licencia MIT (ver LICENSE).
- Descubrimiento multicast UDP 224.0.0.167:53317.
- Servidor: GET /info, POST /register, POST /prepare-upload, POST /upload,
  POST /cancel  (ruta base /api/localsend/v2/...)
- Cliente: secuencia prepare-upload -> upload.
- GUI Tkinter (Aqua/X11 en 10.6).

Uso:
  python snowsend.py                  # GUI
  python snowsend.py --headless       # sin GUI (servidor + descubrimiento)
  python snowsend.py --headless --alias MiMac --port 53317 \
             --download-dir ~/Downloads

Referencia del protocolo: https://github.com/localsend/protocol (v2.2)
"""

from __future__ import print_function, with_statement

import gzip
import hashlib
import json
import mimetypes
import os
import socket
import struct
import sys
import threading
import time
import uuid
import zlib

# ---------------------------------------------------------------------------
# Compatibilidad Python 2 / Python 3
# ---------------------------------------------------------------------------

try:
    unicode
except NameError:
    unicode = str

try:
    import Queue as queue_module
except ImportError:
    import queue as queue_module

try:
    import Tkinter as tk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    HAS_TKINTER = True
except ImportError:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
        HAS_TKINTER = True
    except ImportError:
        HAS_TKINTER = False
        tk = None
        filedialog = None
        messagebox = None

try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn

try:
    import urllib2
    from urlparse import urlparse, parse_qs
    from urllib import quote as url_quote
except ImportError:
    import urllib.request as urllib2
    import urllib.error
    from urllib.parse import urlparse, parse_qs, quote as url_quote

try:
    import httplib
except ImportError:
    import http.client as httplib

try:
    from StringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

# ---------------------------------------------------------------------------
# Constantes del protocolo
# ---------------------------------------------------------------------------

MULTICAST_IP = "224.0.0.167"
PORT = 53317
PROTOCOL_VERSION = "2.0"
DEVICE_MODEL = "Mac OS X 10.6"
DEVICE_TYPE = "desktop"
PROTOCOL = "http"
API_BASE = "/api/localsend/v2"


# ---------------------------------------------------------------------------
# Utilidades de bytes / texto (Py2: str es bytes, Py3: bytes != str)
# ---------------------------------------------------------------------------

def to_bytes(s):
    if isinstance(s, bytes):
        return s
    return s.encode("utf-8")


def to_text(b):
    if isinstance(b, unicode):
        return b
    try:
        return b.decode("utf-8")
    except Exception:
        try:
            return b.decode("utf-8", "ignore")
        except Exception:
            return str(b)


def sha256_of_file(path):
    h = hashlib.sha256()
    f = open(path, "rb")
    try:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    finally:
        f.close()
    return h.hexdigest()


def sanitize_filename(name):
    name = str(name).replace("\\", "/")
    name = name.split("/")[-1]
    name = name.strip()
    if not name or name == "." or name == "..":
        name = "archivo_recibido"
    return name


def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = "%s (%d)%s" % (base, i, ext)
        if not os.path.exists(candidate):
            return candidate
        i += 1


def default_alias():
    try:
        name = socket.gethostname()
    except Exception:
        name = "SnowLeopard"
    if not name:
        name = "SnowLeopard"
    name = name.split(".")[0]
    return name or "SnowLeopard"


def load_or_create_fingerprint():
    """Fingerprint persistente (en modo HTTP es una cadena aleatoria, segun
    la especificacion: SHA-256 del certificado si hay HTTPS, si no, aleatorio).
    Se guarda en ~/.snowsend_fingerprint para no auto-descubrirnos.
    (Si existe el archivo antiguo ~/.localsend_10_6_fingerprint se reutiliza
    su valor, para seguir siendo el mismo dispositivo tras el renombrado.)"""
    home = os.path.expanduser("~")
    path = os.path.join(home, ".snowsend_fingerprint")
    legacy_path = os.path.join(home, ".localsend_10_6_fingerprint")
    if not os.path.exists(path) and os.path.exists(legacy_path):
        try:
            lf = open(legacy_path, "r")
            try:
                legacy_fp = lf.read().strip()
            finally:
                lf.close()
            if legacy_fp:
                wf = open(path, "w")
                try:
                    wf.write(legacy_fp)
                finally:
                    wf.close()
        except Exception:
            pass
    try:
        f = open(path, "r")
        try:
            fp = f.read().strip()
        finally:
            f.close()
        if fp:
            return fp
    except Exception:
        pass
    raw = uuid.uuid4().hex + str(time.time()) + default_alias()
    fp = hashlib.sha256(to_bytes(raw)).hexdigest()
    try:
        f = open(path, "w")
        try:
            f.write(fp)
        finally:
            f.close()
    except Exception:
        pass
    return fp


# ---------------------------------------------------------------------------
# Estado global de la aplicacion
# ---------------------------------------------------------------------------

class AppState(object):
    def __init__(self, alias, download_dir):
        self.alias = alias
        self.download_dir = download_dir
        self.port = PORT
        self.fingerprint = load_or_create_fingerprint()
        self.devices = {}          # fingerprint -> dict(dispositivo)
        self.devices_lock = threading.Lock()
        self.sessions = {}         # sessionId -> dict(sesion)
        self.sessions_lock = threading.Lock()
        self.log_queue = queue_module.Queue()
        self.device_queue = queue_module.Queue()
        self.stop_event = threading.Event()
        self.discovery_sock = None
        self._last_device_count = -1

    def log(self, msg):
        try:
            ts = time.strftime("%H:%M:%S")
        except Exception:
            ts = ""
        line = "[%s] %s" % (ts, msg)
        try:
            print(line)
        except Exception:
            pass
        try:
            self.log_queue.put(line)
        except Exception:
            pass

    def add_device(self, info, ip):
        if not info or not isinstance(info, dict):
            return
        fp = info.get("fingerprint") or (str(info.get("alias") or "desconocido") + "@" + str(ip))
        if fp == self.fingerprint:
            return
        alias = info.get("alias") or "Desconocido"
        try:
            port = int(info.get("port") or PORT)
        except Exception:
            port = PORT
        protocol = info.get("protocol") or "http"
        device = {
            "alias": alias,
            "version": info.get("version") or PROTOCOL_VERSION,
            "deviceModel": info.get("deviceModel") or "",
            "deviceType": info.get("deviceType") or "",
            "fingerprint": fp,
            "port": port,
            "protocol": protocol,
            "download": info.get("download", False),
            "ip": ip,
            "last_seen": time.time(),
        }
        is_new = False
        with self.devices_lock:
            if fp not in self.devices:
                is_new = True
            self.devices[fp] = device
        if is_new:
            self.log("Dispositivo detectado: %s (%s) %s://%s:%s" % (
                alias, device.get("deviceModel") or device.get("deviceType") or "",
                protocol, ip, port))
        try:
            self.device_queue.put(device)
        except Exception:
            pass


def build_info(state):
    return {
        "alias": state.alias,
        "version": PROTOCOL_VERSION,
        "deviceModel": DEVICE_MODEL,
        "deviceType": DEVICE_TYPE,
        "fingerprint": state.fingerprint,
        "port": getattr(state, "port", PORT) or PORT,
        "protocol": PROTOCOL,
        "download": False,
    }


# ---------------------------------------------------------------------------
# Cliente HTTP (httplib/http.client directo, con urllib2 como respaldo)
# ---------------------------------------------------------------------------
# El iPhone (Swift/Network.framework) puede responder con
# Transfer-Encoding: chunked, gzip o sin Content-Length, y el
# urllib2/httplib de Python 2.6 de Snow Leopard a veces devuelve el
# cuerpo con el framing chunked sin decodificar, gzip sin descomprimir
# o un cuerpo vacio en 204, lo que provocaba el error:
#   "No JSON object could be decoded"
# Por eso se usa httplib directamente, se registra status/headers/
# cuerpo crudo en caso de error y se intenta decodificar de varias
# formas (gzip/deflate, chunked manual, BOM, extraccion {..}).

def _try_decompress(body, encoding):
    if not body:
        return body
    enc = (encoding or "").lower()
    is_gzip = body[:2] == b"\x1f\x8b"
    if enc == "gzip" or is_gzip:
        try:
            f = gzip.GzipFile(fileobj=BytesIO(body))
            try:
                return f.read()
            finally:
                f.close()
        except Exception:
            pass
    if enc == "deflate":
        try:
            return zlib.decompress(body)
        except Exception:
            try:
                return zlib.decompress(body, -15)
            except Exception:
                pass
    return body


def _try_chunked_decode(body):
    """Decodifica framing chunked a mano si el cuerpo lo trae crudo
    (p. ej. b"a3\\r\\n{...}\\r\\n0\\r\\n\\r\\n"). Devuelve None si no
    parece chunked."""
    if not body or b"\r\n" not in body:
        return None
    # La primera linea debe ser un tamano hex (opcionalmente ;ext)
    first_line = body.split(b"\r\n", 1)[0].strip()
    try:
        int(first_line.split(b";")[0].strip(), 16)
    except Exception:
        return None
    out = b""
    pos = 0
    data = body
    while True:
        eol = data.find(b"\r\n", pos)
        if eol < 0:
            return None
        size_line = data[pos:eol].strip().split(b";")[0].strip()
        try:
            size = int(size_line, 16)
        except Exception:
            return None
        pos = eol + 2
        if size == 0:
            break
        if pos + size > len(data):
            return None
        out += data[pos:pos + size]
        pos += size
        # CRLF tras cada chunk
        if data[pos:pos + 2] == b"\r\n":
            pos += 2
        elif data[pos:pos + 1] == b"\n":
            pos += 1
    return out


def _parse_json_body(body, status, headers, url):
    if body is None:
        body = b""
    if not body or not body.strip():
        return {}
    encoding = headers.get("content-encoding") or headers.get("Content-Encoding") or ""
    body = _try_decompress(body, encoding)
    text = to_text(body)
    # BOM UTF-8
    if text.startswith("\ufeff"):
        text = text[1:]
    text_stripped = text.strip()
    if not text_stripped:
        return {}
    try:
        return json.loads(text_stripped)
    except Exception:
        pass
    # Chunked crudo sin decodificar por httplib (Python 2.6)
    decoded = _try_chunked_decode(body)
    if decoded is not None:
        try:
            return json.loads(to_text(_try_decompress(decoded, encoding)).strip())
        except Exception:
            pass
    # Extraer el primer objeto JSON {..} del cuerpo (por si viene
    # envuelto en HTML, framing u otro texto)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass
    # Fallo: incluir el cuerpo crudo para diagnosticar en el registro
    raw_repr = repr(body[:1000])
    raise ValueError("Respuesta no JSON (status %s, url %s, headers %s, body=%s)" % (
        status, url, headers, raw_repr))


def _http_request(method, url, body_bytes, headers, timeout):
    parsed = urlparse(url)
    scheme = (parsed.scheme or "http").lower()
    host = parsed.hostname
    if not host:
        raise ValueError("URL sin host: %s" % url)
    port = parsed.port or (443 if scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path = path + "?" + parsed.query
    conn = None
    if scheme == "https":
        try:
            import ssl
            if hasattr(ssl, "_create_unverified_context"):
                context = ssl._create_unverified_context()
                conn = httplib.HTTPSConnection(host, port, timeout=timeout, context=context)
        except Exception:
            conn = None
        if conn is None:
            conn = httplib.HTTPSConnection(host, port, timeout=timeout)
    else:
        conn = httplib.HTTPConnection(host, port, timeout=timeout)
    try:
        conn.request(method, path, body=body_bytes, headers=headers)
        resp = conn.getresponse()
        status = resp.status
        resp_headers = {}
        try:
            for k, v in resp.getheaders():
                resp_headers[k.lower()] = v
        except Exception:
            pass
        raw_body = b""
        try:
            raw_body = resp.read()
        except Exception as e:
            # httplib.IncompleteRead trae .partial con lo recibido
            partial = getattr(e, "partial", None)
            if partial is not None:
                raw_body = partial
            else:
                raise
        return status, resp_headers, raw_body
    finally:
        try:
            conn.close()
        except Exception:
            pass


def http_get_json(url, timeout=5):
    status, headers, body = _http_request("GET", url, None, {"Accept": "application/json"}, timeout)
    if status == 204:
        return {}
    if status >= 400:
        raise Exception("HTTP %s en GET %s: %s" % (status, url, repr(body[:500])))
    return _parse_json_body(body, status, headers, url)


def http_post_json(url, body_dict, timeout=10):
    data = to_bytes(json.dumps(body_dict))
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    status, resp_headers, body = _http_request("POST", url, data, headers, timeout)
    if status == 204:
        return {}
    if status >= 400:
        raise Exception("HTTP %s en POST %s: %s" % (status, url, repr(body[:1000])))
    return _parse_json_body(body, status, resp_headers, url)


def http_post_file(url, filepath, timeout=120):
    f = open(filepath, "rb")
    try:
        data = f.read()
    finally:
        f.close()
    headers = {"Content-Type": "application/octet-stream", "Accept": "application/json"}
    status, resp_headers, body = _http_request("POST", url, data, headers, timeout)
    if status >= 400:
        raise Exception("HTTP %s en upload %s: %s" % (status, url, repr(body[:1000])))
    return body


# ---------------------------------------------------------------------------
# Descubrimiento multicast UDP
# ---------------------------------------------------------------------------
# NOTA macOS/BSD (Snow Leopard): enlazar el socket a la direccion multicast
# 224.0.0.167 o a 127.0.0.1 hace que sendto() falle con
# "[Errno 49] Can't assign requested address" (EADDRNOTAVAIL), aunque en
# Linux parezca funcionar. Hay que enlazar a INADDR_ANY / a la IP local
# real (p. ej. 192.168.1.x), fijar IP_MULTICAST_IF con esa IP y unirse
# al grupo con (multicast_ip, local_ip). Ver StackOverflow 19798254.

def get_local_ip():
    """IP local que usaria la ruta hacia el grupo multicast (sin enviar
    ningun paquete: un connect() UDP solo fija la ruta)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((MULTICAST_IP, PORT))
            ip = s.getsockname()[0]
            if ip and ip != "0.0.0.0" and not ip.startswith("127."):
                return ip
        finally:
            s.close()
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and ip != "0.0.0.0" and not ip.startswith("127."):
                return ip
        finally:
            s.close()
    except Exception:
        pass
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return "0.0.0.0"


def _setup_multicast_socket(sock, local_ip):
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass
    try:
        reuseport = getattr(socket, "SO_REUSEPORT", None)
        if reuseport is not None:
            sock.setsockopt(socket.SOL_SOCKET, reuseport, 1)
    except Exception:
        pass
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
    except Exception:
        pass
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    except Exception:
        pass
    # Interfaz de salida multicast = IP local real (clave en macOS).
    try:
        mc_if = getattr(socket, "IP_MULTICAST_IF", None)
        if mc_if is not None and local_ip and local_ip != "0.0.0.0":
            sock.setsockopt(socket.IPPROTO_IP, mc_if, socket.inet_aton(local_ip))
    except Exception:
        pass
    try:
        iface = local_ip if (local_ip and local_ip != "0.0.0.0") else "0.0.0.0"
        mreq = struct.pack("4s4s", socket.inet_aton(MULTICAST_IP), socket.inet_aton(iface))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except Exception:
        pass


def _send_via_temp_socket(state, payload):
    """Envio de respaldo con un socket temporal enlazado a la IP local.
    En macOS el socket de recepcion a veces no puede enviar si quedo
    enlazado de otra forma; este camino suele funcionar."""
    local_ip = get_local_ip()
    tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        _setup_multicast_socket(tmp, local_ip)
        try:
            tmp.bind((local_ip, 0))
        except Exception:
            try:
                tmp.bind(("", 0))
            except Exception:
                pass
        tmp.sendto(payload, (MULTICAST_IP, PORT))
        return True
    except Exception as e:
        state.log("Error enviando anuncio multicast (respaldo): %s" % e)
        return False
    finally:
        try:
            tmp.close()
        except Exception:
            pass


def _send_announcement(state, sock):
    info = build_info(state)
    info["announce"] = True
    payload = to_bytes(json.dumps(info))
    # La implementacion oficial anuncia 3 veces; enviamos 3 paquetes.
    for _i in range(3):
        try:
            sock.sendto(payload, (MULTICAST_IP, PORT))
        except Exception as e:
            # Errno 49 en macOS si el socket no esta bien enlazado:
            # reintentar una vez con socket temporal y no spamear el log.
            if _send_via_temp_socket(state, payload):
                state.log("Anuncio multicast enviado (via socket temporal, IP local %s)" % get_local_ip())
            else:
                state.log("Error enviando anuncio multicast: %s" % e)
            return
        time.sleep(0.1)


def announce_once(state):
    sock = getattr(state, "discovery_sock", None)
    if sock is not None:
        _send_announcement(state, sock)
        return
    local_ip = get_local_ip()
    tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        _setup_multicast_socket(tmp, local_ip)
        try:
            tmp.bind((local_ip, 0))
        except Exception:
            try:
                tmp.bind(("", 0))
            except Exception:
                pass
        _send_announcement(state, tmp)
    finally:
        try:
            tmp.close()
        except Exception:
            pass


def register_callback(state, info, ip):
    """Cuando recibimos un anuncio con announce=true, respondemos con
    POST /api/localsend/v2/register al remitente (segun la especificacion).
    El iPhone puede anunciar protocol=https aunque el usuario haya
    desactivado el cifrado; si el handshake TLS falla con
    "unknown protocol" (el peer en realidad habla HTTP plano),
    reintentamos con http y actualizamos el protocolo del dispositivo."""
    try:
        port = int(info.get("port") or PORT)
    except Exception:
        port = PORT
    protocol = info.get("protocol") or "http"
    # Snow Leopard no puede hacer TLS moderno: probar http primero
    # siempre (el iPhone anuncia https aunque el cifrado este off).
    protocols_to_try = []
    for p in ("http", protocol, "https"):
        if p not in protocols_to_try:
            protocols_to_try.append(p)
    last_error = None
    for proto in protocols_to_try:
        url = "%s://%s:%s%s/register" % (proto, ip, port, API_BASE)
        try:
            resp = http_post_json(url, build_info(state), timeout=5)
            if isinstance(resp, dict) and resp.get("fingerprint") and resp.get("fingerprint") != state.fingerprint:
                state.add_device(resp, ip)
            elif isinstance(resp, dict):
                if proto != protocol:
                    info = dict(info)
                    info["protocol"] = proto
                state.add_device(info, ip)
            return
        except Exception as e:
            last_error = e
            continue
    state.log("No se pudo registrar en %s (%s): %s" % (info.get("alias") or ip, ip, last_error))


def discovery_loop(state):
    local_ip = get_local_ip()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    _setup_multicast_socket(sock, local_ip)
    # En macOS/BSD NO hay que enlazar a 224.0.0.167 (Errno 49 al enviar).
    # Se enlaza a INADDR_ANY ("") para recibir el grupo y poder enviar
    # desde la IP local real; si eso fallara, se prueba la IP local.
    bound = False
    bind_error = None
    for bind_addr in ("", local_ip):
        if not bind_addr and local_ip == "0.0.0.0":
            pass
        try:
            sock.bind((bind_addr, PORT))
            bound = True
            break
        except Exception as e:
            bind_error = e
            continue
    if not bound:
        state.log("Aviso: no se pudo enlazar UDP :%d (%s). Se intentara solo con anuncio." % (PORT, bind_error))
        state.discovery_sock = sock
        try:
            _send_announcement(state, sock)
        except Exception:
            pass
        return
    state.discovery_sock = sock
    sock.settimeout(1.0)
    _send_announcement(state, sock)
    state.log("Descubrimiento multicast activo en %s:%d (IP local %s)" % (MULTICAST_IP, PORT, local_ip))
    last_announce = time.time()
    while not state.stop_event.is_set():
        # Re-anuncio periodico cada 15 segundos (mantiene visible el equipo).
        if time.time() - last_announce > 15:
            try:
                _send_announcement(state, sock)
            except Exception:
                pass
            last_announce = time.time()
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except Exception:
            continue
        ip = addr[0] if addr else "?"
        try:
            info = json.loads(to_text(data))
        except Exception:
            continue
        if not isinstance(info, dict):
            continue
        if info.get("fingerprint") == state.fingerprint:
            continue
        state.add_device(info, ip)
        if info.get("announce"):
            t = threading.Thread(target=register_callback, args=(state, info, ip))
            t.daemon = True
            t.start()
    try:
        sock.close()
    except Exception:
        pass


def scan_subnet(state):
    """Respaldo cuando el multicast esta bloqueado: pregunta GET /info a
    cada IP del /24 local. Util en redes con aislamiento multicast."""
    local_ip = get_local_ip()
    if not local_ip or local_ip == "0.0.0.0":
        state.log("No se pudo determinar la IP local para escanear.")
        return
    parts = local_ip.split(".")
    if len(parts) != 4:
        state.log("IP local invalida: %s" % local_ip)
        return
    prefix = ".".join(parts[:3]) + "."
    state.log("Escaneando %s0/24 (IP local %s) en busca de dispositivos LocalSend..." % (prefix, local_ip))
    work_q = queue_module.Queue()
    for i in range(1, 255):
        ip = "%s%d" % (prefix, i)
        if ip != local_ip:
            work_q.put(ip)

    def worker():
        while True:
            try:
                ip = work_q.get_nowait()
            except queue_module.Empty:
                return
            url = "http://%s:%d%s/info" % (ip, PORT, API_BASE)
            try:
                info = http_get_json(url, timeout=1)
                if isinstance(info, dict) and info.get("fingerprint") and info.get("fingerprint") != state.fingerprint:
                    state.add_device(info, ip)
                    state.log("Escaneo: encontrado %s en %s" % (info.get("alias") or "?", ip))
            except Exception:
                pass

    threads = []
    for _i in range(20):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    state.log("Escaneo de red completado.")


# ---------------------------------------------------------------------------
# Servidor HTTP (recepcion)
# ---------------------------------------------------------------------------

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class SnowSendHandler(BaseHTTPRequestHandler):
    server_version = "SnowSend/1.3"
    sys_version = ""
    # HTTP/1.1 es necesario para que BaseHTTPRequestHandler responda
    # "100 Continue" ante "Expect: 100-continue" (iOS/Dart lo envia en
    # subidas grandes). Con el valor por defecto HTTP/1.0 la condicion
    # protocol_version >= "HTTP/1.1" falla, no se llama a
    # handle_expect_100() y cliente/servidor quedan en deadlock hasta
    # timeout, con el cuerpo vacio y SHA-256 incorrecto.
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        try:
            state = self.server.state
            state.log("HTTP %s - %s" % (self.client_address[0] if self.client_address else "?", fmt % args))
        except Exception:
            pass

    def handle_expect_100(self):
        # iOS/Dart y curl envian "Expect: 100-continue" en subidas.
        # Hay que responder 100 explicitamente o el cliente espera.
        try:
            self.send_response_only(100)
        except Exception:
            try:
                self.send_response(100)
            except Exception:
                pass
        try:
            self.end_headers()
        except Exception:
            pass
        return True

    def _is_chunked(self):
        te = self.headers.get("Transfer-Encoding") or ""
        return "chunked" in te.lower()

    def _read_chunk_size(self):
        line = self.rfile.readline(65536)
        if not line:
            return None
        line = line.strip()
        if line == b"":
            return self._read_chunk_size()
        size_str = line.split(b";")[0].strip()
        try:
            return int(size_str, 16)
        except Exception:
            return None

    def _read_chunked_bytes(self):
        chunks = []
        while True:
            size = self._read_chunk_size()
            if size is None:
                break
            if size == 0:
                # trailers hasta linea vacia
                while True:
                    trailer = self.rfile.readline(65536)
                    if not trailer or trailer.strip() == b"":
                        break
                break
            remaining = size
            data = b""
            while remaining > 0:
                piece = self.rfile.read(remaining)
                if not piece:
                    break
                data += piece
                remaining -= len(piece)
            chunks.append(data)
            self.rfile.read(2)  # CRLF tras cada chunk
        return b"".join(chunks)

    def _stream_body_to_file(self, out, hasher):
        """Escribe el cuerpo HTTP a `out` calculando SHA-256 al vuelo.
        Soporta Content-Length y Transfer-Encoding: chunked (iOS).
        Devuelve el numero total de bytes recibidos."""
        total = 0
        if self._is_chunked():
            while True:
                size = self._read_chunk_size()
                if size is None:
                    break
                if size == 0:
                    while True:
                        trailer = self.rfile.readline(65536)
                        if not trailer or trailer.strip() == b"":
                            break
                    break
                remaining = size
                while remaining > 0:
                    to_read = remaining if remaining < 8192 else 8192
                    piece = self.rfile.read(to_read)
                    if not piece:
                        break
                    out.write(piece)
                    hasher.update(piece)
                    total += len(piece)
                    remaining -= len(piece)
                self.rfile.read(2)  # CRLF tras cada chunk
            return total
        length_str = self.headers.get("Content-Length") or "0"
        try:
            length = int(length_str)
        except Exception:
            length = 0
        remaining = length
        while remaining > 0:
            to_read = remaining if remaining < 8192 else 8192
            piece = self.rfile.read(to_read)
            if not piece:
                break
            out.write(piece)
            hasher.update(piece)
            total += len(piece)
            remaining -= len(piece)
        return total

    def _send_json(self, code, obj):
        body = to_bytes(json.dumps(obj))
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, code):
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _read_body(self):
        # iOS LocalSend envia prepare-upload/upload con
        # Transfer-Encoding: chunked y SIN Content-Length. Si solo se
        # lee Content-Length, el cuerpo llega como 0 bytes, el JSON
        # falla / el archivo queda vacio y el SHA-256 no coincide (422).
        if self._is_chunked():
            return self._read_chunked_bytes()
        length_str = self.headers.get("Content-Length") or "0"
        try:
            length = int(length_str)
        except Exception:
            length = 0
        if length <= 0:
            return b""
        # read(n) en el socket bufferizado puede devolver menos de n;
        # leer en bucle hasta completar.
        body = b""
        remaining = length
        while remaining > 0:
            piece = self.rfile.read(remaining)
            if not piece:
                break
            body += piece
            remaining -= len(piece)
        return body

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        state = self.server.state
        if path == API_BASE + "/info":
            self._send_json(200, build_info(state))
        elif path == "/" or path == API_BASE + "/ping":
            body = to_bytes("SnowSend - %s\n" % state.alias)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == API_BASE + "/download":
            # Transferencia inversa (download API) no implementada.
            self._send_empty(403)
        else:
            self._send_empty(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        state = self.server.state
        client_ip = self.client_address[0] if self.client_address else "?"

        if path == API_BASE + "/register":
            body = self._read_body()
            try:
                info = json.loads(to_text(body)) if body else {}
            except Exception:
                info = {}
            if isinstance(info, dict) and info.get("fingerprint") != state.fingerprint:
                state.add_device(info, client_ip)
            self._send_json(200, build_info(state))
            return

        if path == API_BASE + "/prepare-upload":
            body = self._read_body()
            try:
                payload = json.loads(to_text(body))
            except Exception as e:
                state.log("prepare-upload: JSON invalido: %s" % e)
                self._send_empty(400)
                return
            sender_info = payload.get("info") or {}
            if sender_info:
                state.add_device(sender_info, client_ip)
            files_raw = payload.get("files") or {}
            files_list = []
            if isinstance(files_raw, dict):
                for fid, fmeta in files_raw.items():
                    if isinstance(fmeta, dict):
                        if "id" not in fmeta:
                            fmeta["id"] = fid
                        files_list.append(fmeta)
                    else:
                        files_list.append({"id": fid, "fileName": str(fid)})
            elif isinstance(files_raw, list):
                files_list = files_raw
            else:
                files_list = []
            if not files_list:
                self._send_empty(204)
                return
            session_id = uuid.uuid4().hex
            tokens = {}
            session_files = {}
            for fmeta in files_list:
                fid = fmeta.get("id") or uuid.uuid4().hex
                token = uuid.uuid4().hex
                tokens[fid] = token
                session_files[fid] = {
                    "fileName": fmeta.get("fileName") or fid,
                    "size": fmeta.get("size") or 0,
                    "fileType": fmeta.get("fileType") or "application/octet-stream",
                    "sha256": fmeta.get("sha256"),
                    "token": token,
                }
            with state.sessions_lock:
                state.sessions[session_id] = {
                    "files": session_files,
                    "sender": sender_info,
                    "ip": client_ip,
                }
            state.log("Solicitud de %s: %d archivo(s) - aceptado automaticamente" % (
                sender_info.get("alias") or client_ip, len(files_list)))
            for fmeta in files_list:
                state.log("  - %s (%s bytes)" % (fmeta.get("fileName"), fmeta.get("size")))
            self._send_json(200, {"sessionId": session_id, "files": tokens})
            return

        if path == API_BASE + "/upload":
            qs = parse_qs(parsed.query)

            def qget(name):
                v = qs.get(name)
                if isinstance(v, list) and v:
                    return v[0]
                return v

            session_id = qget("sessionId")
            file_id = qget("fileId")
            token = qget("token")
            session = None
            with state.sessions_lock:
                if session_id:
                    session = state.sessions.get(session_id)
            if not session or file_id not in session.get("files", {}):
                state.log("upload: sesion o archivo no encontrado session=%s file=%s" % (session_id, file_id))
                self._send_empty(400)
                return
            fmeta = session["files"][file_id]
            if token and token != fmeta.get("token"):
                state.log("upload: token invalido para %s" % fmeta.get("fileName"))
                self._send_empty(403)
                return
            state.log("upload: %s Content-Length=%s Transfer-Encoding=%s" % (
                fmeta.get("fileName"),
                self.headers.get("Content-Length") or "-",
                self.headers.get("Transfer-Encoding") or "-"))
            try:
                if not os.path.isdir(state.download_dir):
                    os.makedirs(state.download_dir)
            except Exception as e:
                state.log("No se pudo crear la carpeta de descarga: %s" % e)
                self._send_empty(500)
                return
            safe_name = sanitize_filename(fmeta.get("fileName") or file_id)
            dest = unique_path(os.path.join(state.download_dir, safe_name))
            hasher = hashlib.sha256()
            out = None
            received = 0
            try:
                out = open(dest, "wb")
                received = self._stream_body_to_file(out, hasher)
            except Exception as e:
                state.log("Error guardando %s: %s" % (safe_name, e))
                try:
                    if out is not None:
                        out.close()
                except Exception:
                    pass
                self._send_empty(500)
                return
            try:
                if out is not None:
                    out.close()
            except Exception:
                pass
            expected = fmeta.get("sha256")
            if expected:
                actual = hasher.hexdigest()
                if actual.lower() != str(expected).lower():
                    state.log("ERROR: checksum SHA256 no coincide para %s (recibidos %d bytes, esperados %s)" % (
                        safe_name, received, fmeta.get("size")))
                    try:
                        os.remove(dest)
                    except Exception:
                        pass
                    self._send_empty(422)
                    return
            state.log("Archivo recibido: %s (%d bytes) -> %s" % (safe_name, received, dest))
            self._send_empty(200)
            return

        if path == API_BASE + "/cancel":
            try:
                self._read_body()
            except Exception:
                pass
            qs = parse_qs(parsed.query)
            session_id = None
            if qs.get("sessionId"):
                session_id = qs.get("sessionId")[0]
            if session_id:
                with state.sessions_lock:
                    if session_id in state.sessions:
                        del state.sessions[session_id]
            state.log("Sesion cancelada por el remitente")
            self._send_empty(200)
            return

        try:
            self._read_body()
        except Exception:
            pass
        self._send_empty(404)


def start_http_server(state, port):
    server = ThreadedHTTPServer(("", port), SnowSendHandler)
    server.state = state
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    state.log("Servidor HTTP iniciado en puerto %d" % port)
    return server


# ---------------------------------------------------------------------------
# Envio de archivos (cliente)
# ---------------------------------------------------------------------------

def sanitize_log(text, limit=200):
    """Evita volcar bytes binarios/control (p. ej. una alerta TLS del
    iPhone) al registro de la GUI."""
    try:
        text = to_text(text)
    except Exception:
        text = repr(text)
    out = []
    for ch in text:
        o = ord(ch)
        if o < 32 or o == 127:
            out.append("\\x%02x" % o)
        else:
            out.append(ch)
    s = "".join(out)
    if len(s) > limit:
        s = s[:limit] + "..."
    return s


def _encryption_hint(state, port):
    state.log("  >>> El dispositivo NO acepta HTTP plano por el puerto %s." % port)
    state.log("  >>> En el iPhone abre LocalSend > Ajustes (engranaje) y pon Encryption en OFF,")
    state.log("  >>> cierra y vuelve a abrir LocalSend, luego pulsa 'Reanunciar' aqui.")


def diagnose_peer(state, ip, port, alias):
    """Cuando el envio falla, sondea GET /info por HTTP plano para
    distinguir 'el receptor tiene Encryption activado (solo TLS)' de
    otros problemas. Un servidor TLS-only responde basura, vacio o
    cierra la conexion a una peticion HTTP plana."""
    url = "http://%s:%s%s/info" % (ip, port, API_BASE)
    try:
        info = http_get_json(url, timeout=8)
    except Exception as e:
        msg = sanitize_log(e, 160)
        state.log("  Diagnostico: %s no responde a HTTP plano (%s)" % (alias, msg))
        low = msg.lower()
        binario = ("\\x" in msg) or ("ssl" in low and "wrong version" in low) or ("ssl" in low and "unknown protocol" in low)
        if (binario or "empty" in low or "no json" in low or "badstatusline" in low
                or "reset" in low or "no status" in low or "10054" in low
                or "timed out" in low):
            _encryption_hint(state, port)
        else:
            state.log("  Si el aviso de transferencia no aparece en el iPhone, reinicia LocalSend alli.")
        return
    if isinstance(info, dict) and info.get("alias"):
        state.log("  Diagnostico: %s si responde /info por HTTP (alias=%s, protocol=%s)." % (
            alias, info.get("alias"), info.get("protocol")))
        state.log("  Prueba a reiniciar LocalSend en el iPhone y a aceptar el aviso de transferencia.")
    else:
        state.log("  Diagnostico: /info devolvio datos inesperados: %s" % (info,))
        _encryption_hint(state, port)


def send_files_to_device(state, device, filepaths):
    ip = device.get("ip")
    try:
        port = int(device.get("port") or PORT)
    except Exception:
        port = PORT
    announced_protocol = device.get("protocol") or "http"
    # Snow Leopard solo puede hablar HTTP plano: probar http primero
    # siempre, aunque el peer anuncie https (caso iPhone con cifrado off).
    protocol = "http"
    alias = device.get("alias") or ip
    state.log("Preparando envio a %s (http://%s:%s) - %d archivo(s)" % (
        alias, ip, port, len(filepaths)))
    files_dict = {}
    paths_by_id = {}
    for fp in filepaths:
        if not os.path.isfile(fp):
            state.log("  Omitido (no existe): %s" % fp)
            continue
        fid = uuid.uuid4().hex
        size = os.path.getsize(fp)
        state.log("  Calculando SHA256: %s (%d bytes)" % (os.path.basename(fp), size))
        try:
            sha = sha256_of_file(fp)
        except Exception as e:
            state.log("  No se pudo calcular SHA256 de %s: %s" % (fp, e))
            sha = None
        ftype = mimetypes.guess_type(fp)[0] or "application/octet-stream"
        files_dict[fid] = {
            "id": fid,
            "fileName": os.path.basename(fp),
            "size": size,
            "fileType": ftype,
            "sha256": sha,
        }
        paths_by_id[fid] = fp
    if not files_dict:
        state.log("No hay archivos validos para enviar.")
        return
    prepare_body = {"info": build_info(state), "files": files_dict}
    # 60 s de timeout: en el iPhone hay que tocar "Aceptar" y eso
    # puede tardar mas que los 15 s anteriores.
    state.log("  Esperando aceptacion en %s... (acepta en el iPhone si aparece el aviso)" % alias)
    resp = None
    protocols_to_try = []
    for p in ("http", announced_protocol, "https"):
        if p not in protocols_to_try:
            protocols_to_try.append(p)
    last_error = None
    first_error = None
    for proto in protocols_to_try:
        protocol = proto
        prepare_url = "%s://%s:%s%s/prepare-upload" % (proto, ip, port, API_BASE)
        try:
            resp = http_post_json(prepare_url, prepare_body, timeout=60)
            break
        except Exception as e:
            last_error = e
            if first_error is None:
                first_error = e
            state.log("  prepare-upload con %s fallo: %s" % (proto, sanitize_log(e, 200)))
            resp = None
            continue
    if resp is None:
        state.log("Error en prepare-upload: %s" % sanitize_log(first_error, 200))
        diagnose_peer(state, ip, port, alias)
        return
    if not resp or "sessionId" not in resp:
        state.log("Respuesta inesperada de prepare-upload (sin sessionId): %s" % (resp,))
        if not resp:
            state.log("  El receptor devolvio una respuesta vacia.")
        diagnose_peer(state, ip, port, alias)
        return
    # Recordar el protocolo que funciono para la proxima vez
    try:
        fp_dev = device.get("fingerprint")
        if fp_dev:
            with state.devices_lock:
                if fp_dev in state.devices:
                    state.devices[fp_dev]["protocol"] = protocol
    except Exception:
        pass
    session_id = resp.get("sessionId")
    tokens_raw = resp.get("files") or {}
    tokens = {}
    if isinstance(tokens_raw, dict):
        tokens = tokens_raw
    elif isinstance(tokens_raw, list):
        for item in tokens_raw:
            if isinstance(item, dict):
                fid = item.get("id")
                tokens[fid] = item.get("token") or item.get("status") or "success"
            else:
                tokens[item] = "success"
    state.log("Sesion aceptada: %s" % session_id)
    success_count = 0
    for fid, fp in paths_by_id.items():
        token = tokens.get(fid)
        if token is None:
            state.log("  %s: no autorizado por el receptor" % os.path.basename(fp))
            continue
        if isinstance(token, dict):
            token = token.get("token") or token.get("status")
        if token == "rejected":
            state.log("  %s: rechazado por el receptor" % os.path.basename(fp))
            continue
        upload_url = "%s://%s:%s%s/upload?sessionId=%s&fileId=%s&token=%s" % (
            protocol, ip, port, API_BASE,
            url_quote(str(session_id)), url_quote(str(fid)), url_quote(str(token)))
        state.log("  Enviando: %s" % os.path.basename(fp))
        try:
            http_post_file(upload_url, fp, timeout=120)
            state.log("  OK: %s" % os.path.basename(fp))
            success_count += 1
        except Exception as e:
            state.log("  Error enviando %s: %s" % (os.path.basename(fp), e))
    state.log("Envio finalizado: %d/%d archivo(s) a %s" % (success_count, len(paths_by_id), alias))


# ---------------------------------------------------------------------------
# Interfaz grafica Tkinter (compatible con Tk 8.5 de Snow Leopard)
# ---------------------------------------------------------------------------

if HAS_TKINTER:
    class SnowSendGUI(object):
        def __init__(self, state):
            self.state = state
            self.root = tk.Tk()
            self.root.title("SnowSend - Snow Leopard")
            self.root.geometry("680x560")
            try:
                self.root.minsize(560, 420)
            except Exception:
                pass
            self.device_order = []
            self.build_widgets()
            self.poll_queues()

        def build_widgets(self):
            root = self.root
            top = tk.Frame(root, padx=8, pady=6)
            top.pack(fill=tk.X)
            tk.Label(top, text="Alias:").pack(side=tk.LEFT)
            self.alias_var = tk.StringVar()
            self.alias_var.set(self.state.alias)
            tk.Entry(top, textvariable=self.alias_var, width=22).pack(side=tk.LEFT, padx=(4, 8))
            tk.Button(top, text="Aplicar", command=self.apply_alias).pack(side=tk.LEFT)
            tk.Label(top, text="Servidor: HTTP :53317 - activo", fg="green").pack(side=tk.RIGHT)

            dl_frame = tk.Frame(root, padx=8, pady=2)
            dl_frame.pack(fill=tk.X)
            tk.Label(dl_frame, text="Carpeta de descarga:").pack(side=tk.LEFT)
            self.download_label = tk.Label(dl_frame, text=self.state.download_dir)
            self.download_label.pack(side=tk.LEFT, padx=4)
            tk.Button(dl_frame, text="Cambiar...", command=self.on_change_download).pack(side=tk.RIGHT)

            tk.Label(root, text="Dispositivos detectados:", anchor=tk.W).pack(fill=tk.X, padx=8, pady=(6, 0))
            list_frame = tk.Frame(root, padx=8, pady=2)
            list_frame.pack(fill=tk.X)
            self.listbox = tk.Listbox(list_frame, height=8, width=82)
            scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
            self.listbox.config(yscrollcommand=scrollbar.set)
            self.listbox.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            btn_frame = tk.Frame(root, padx=8, pady=4)
            btn_frame.pack(fill=tk.X)
            tk.Button(btn_frame, text="Anunciar / Refrescar", command=self.on_announce).pack(side=tk.LEFT, padx=2)
            tk.Button(btn_frame, text="Escanear red", command=self.on_scan).pack(side=tk.LEFT, padx=2)
            tk.Button(btn_frame, text="Enviar Archivo...", command=self.on_send).pack(side=tk.LEFT, padx=12)
            tk.Button(btn_frame, text="Limpiar registro", command=self.on_clear_log).pack(side=tk.RIGHT, padx=2)

            tk.Label(root, text="Registro:", anchor=tk.W).pack(fill=tk.X, padx=8, pady=(4, 0))
            log_frame = tk.Frame(root, padx=8, pady=2)
            log_frame.pack(fill=tk.BOTH, expand=tk.YES)
            self.log_text = tk.Text(log_frame, height=14, width=82, wrap=tk.WORD)
            log_scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
            self.log_text.config(yscrollcommand=log_scroll.set)
            self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
            log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.log_text.config(state="disabled")

            tk.Label(root, text="HTTP plano :53317 - En el movil/Mac moderno desactiva Encryption (cifrado) en LocalSend.",
                     fg="gray").pack(fill=tk.X, padx=8, pady=4)

        def apply_alias(self):
            new_alias = self.alias_var.get().strip()
            if new_alias:
                self.state.alias = new_alias
                self.state.log("Alias cambiado a: %s" % new_alias)
                self.on_announce()

        def on_announce(self):
            self.state.log("Anunciando presencia en la red (multicast %s:%d)..." % (MULTICAST_IP, PORT))
            t = threading.Thread(target=announce_once, args=(self.state,))
            t.daemon = True
            t.start()

        def on_scan(self):
            t = threading.Thread(target=scan_subnet, args=(self.state,))
            t.daemon = True
            t.start()

        def on_clear_log(self):
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", tk.END)
            self.log_text.config(state="disabled")

        def on_change_download(self):
            folder = filedialog.askdirectory(title="Carpeta de descarga")
            if folder:
                self.state.download_dir = folder
                self.download_label.config(text=folder)
                self.state.log("Carpeta de descarga: %s" % folder)

        def on_send(self):
            sel = self.listbox.curselection()
            if not sel:
                messagebox.showwarning("SnowSend", "Selecciona primero un dispositivo de la lista.")
                return
            idx = int(sel[0])
            if idx < 0 or idx >= len(self.device_order):
                return
            fp = self.device_order[idx]
            device_copy = None
            with self.state.devices_lock:
                dev = self.state.devices.get(fp)
                if dev:
                    device_copy = dict(dev)
            if not device_copy:
                return
            filepaths = filedialog.askopenfilenames(
                title="Seleccionar archivos para enviar a %s" % (device_copy.get("alias") or ""))
            if not filepaths:
                return
            self.state.log("Envio iniciado a %s (%d archivo(s))" % (
                device_copy.get("alias"), len(filepaths)))
            t = threading.Thread(target=send_files_to_device,
                                 args=(self.state, device_copy, list(filepaths)))
            t.daemon = True
            t.start()

        def refresh_device_list(self):
            self.listbox.delete(0, tk.END)
            self.device_order = []
            with self.state.devices_lock:
                devices = list(self.state.devices.values())
            devices.sort(key=lambda d: d.get("alias", ""))
            for d in devices:
                label = "%s  -  %s  (%s://%s:%s)" % (
                    d.get("alias"),
                    d.get("deviceModel") or d.get("deviceType") or "",
                    d.get("protocol"), d.get("ip"), d.get("port"))
                self.listbox.insert(tk.END, label)
                self.device_order.append(d.get("fingerprint"))
            if len(devices) != self.state._last_device_count:
                self.state._last_device_count = len(devices)
                if devices:
                    self.state.log("Dispositivos en lista: %d" % len(devices))

        def poll_queues(self):
            try:
                while True:
                    line = self.state.log_queue.get_nowait()
                    self.log_text.config(state="normal")
                    self.log_text.insert(tk.END, line + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state="disabled")
            except queue_module.Empty:
                pass
            need_refresh = False
            try:
                while True:
                    self.state.device_queue.get_nowait()
                    need_refresh = True
            except queue_module.Empty:
                pass
            if need_refresh:
                self.refresh_device_list()
            try:
                self.root.after(400, self.poll_queues)
            except Exception:
                pass
else:
    SnowSendGUI = None


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------

def run_headless(state, port):
    state.port = port
    server = start_http_server(state, port)
    t = threading.Thread(target=discovery_loop, args=(state,))
    t.daemon = True
    t.start()
    state.log("Modo headless activo. Alias: %s" % state.alias)
    state.log("Carpeta de descarga: %s" % state.download_dir)
    state.log("Pulsa Ctrl+C para salir.")
    try:
        while not state.stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        state.log("Interrumpido por el usuario.")
    finally:
        state.stop_event.set()
        try:
            server.shutdown()
        except Exception:
            pass


def print_usage():
    print("Uso: python snowsend.py [--headless] [--alias NOMBRE] [--port 53317] [--download-dir RUTA]")


def main():
    alias = default_alias()
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    port = PORT
    headless = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--headless" or a == "--no-gui":
            headless = True
        elif a == "--alias" and i + 1 < len(args):
            alias = args[i + 1]
            i += 1
        elif a == "--port" and i + 1 < len(args):
            try:
                port = int(args[i + 1])
            except Exception:
                pass
            i += 1
        elif a == "--download-dir" and i + 1 < len(args):
            download_dir = args[i + 1]
            i += 1
        elif a == "--help" or a == "-h":
            print_usage()
            return
        i += 1

    state = AppState(alias, download_dir)

    if headless or not HAS_TKINTER:
        if not HAS_TKINTER and not headless:
            print("Tkinter no disponible, usando modo headless.")
        run_headless(state, port)
        return

    state.port = port
    gui = SnowSendGUI(state)
    server = start_http_server(state, port)
    t = threading.Thread(target=discovery_loop, args=(state,))
    t.daemon = True
    t.start()
    state.log("SnowSend iniciado - Alias: %s" % alias)
    state.log("Descubrimiento multicast: %s:%d" % (MULTICAST_IP, PORT))
    state.log("Carpeta de descarga: %s" % download_dir)
    state.log("HTTP plano en :%d - En el dispositivo moderno desactiva Encryption." % port)

    def on_close():
        state.stop_event.set()
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            gui.root.destroy()
        except Exception:
            pass

    try:
        gui.root.protocol("WM_DELETE_WINDOW", on_close)
    except Exception:
        pass
    gui.root.mainloop()


if __name__ == "__main__":
    main()
