"""
ESP32 Serial → HTTPS Forwarder
pip install pyserial requests
"""
import re, time, sys
import serial, requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PORT = "COM23"      # <-- set your ESP32-C6 port
BAUD = 115200
SER_TIMEOUT = 0.2
HTTP_TIMEOUT = 12
LINE_RE = re.compile(r'(?:\[SERIALFWD\])?(http://script\.google\.com\S+)', re.I)

def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=SER_TIMEOUT)
    except serial.SerialException as e:
        print(f"[ERROR] {e}"); sys.exit(1)

    print(f"[INFO] Listening on {PORT} @ {BAUD}")
    sess = requests.Session()
    buf = b""

    while True:
        try:
            chunk = ser.read(512)
            if chunk: buf += chunk
            else: 
                time.sleep(0.02); continue

            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode("utf-8", "ignore").strip()
                m = LINE_RE.search(text)
                if not m: 
                    continue

                url_http = m.group(1)
                url_https = url_http.replace("http://", "https://", 1)
                print(f"[FORWARD] {url_https}")

                try:
                    r = sess.get(url_https, timeout=HTTP_TIMEOUT, allow_redirects=True, verify=False)
                    print(f"[RESP] {r.status_code} | {r.text[:120]!r}")
                except requests.RequestException as e:
                    print(f"[HTTP ERROR] {e}")

        except KeyboardInterrupt:
            print("\n[EXIT] Interrupted"); break
        except Exception as e:
            print(f"[ERROR] {e}"); time.sleep(0.3)

if __name__ == "__main__":
    main()
