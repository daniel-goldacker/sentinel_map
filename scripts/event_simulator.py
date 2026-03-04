import argparse
import random
import time
from typing import Sequence

import requests


DEFAULT_IPS: Sequence[str] = (
    "8.8.8.8",
    "1.1.1.1",
    "9.9.9.9",
    "208.67.222.222",
    "31.13.71.36",
    "81.2.69.142",
    "91.198.174.192",
    "103.21.244.0",
    "185.199.108.153",
    "45.33.32.156",
    "52.95.110.1",
    "201.17.128.1",
    "200.160.2.3",
    "177.54.145.10",
    "189.126.10.10",
    "5.255.255.5",
    "77.88.8.8",
    "114.114.114.114",
    "180.76.76.76",
    "202.108.22.5",
    "61.135.169.121",
    "101.226.4.6",
    "168.126.63.1",
    "129.250.35.250",
    "133.130.103.1",
    "202.12.27.33",
    "14.139.34.1",
    "49.207.0.1",
    "103.86.96.100",
    "180.183.0.1",
    "203.50.2.71",
    "139.130.4.5",
    "196.25.1.1",
    "41.203.64.1",
    "197.211.61.1",
    "154.70.154.1",
    "80.67.169.40",
    "62.210.0.1",
    "46.182.19.48",
    "212.102.33.61",
    "193.0.14.129",
    "130.89.148.14",
    "94.140.14.14",
    "176.103.130.130",
    "79.171.16.1",
    "23.236.62.147",
    "104.244.42.129",
    "151.101.1.69",
)

DEFAULT_PATHS: Sequence[str] = (
    "/.env",
    "/wp-admin",
    "/phpmyadmin",
    "/admin",
    "/config.php",
    "/login",
    "/api/v1/login",
    "/api/v1/auth",
    "/api/v1/users",
    "/graphql",
    "/server-status",
    "/actuator/health",
    "/.git/config",
    "/backup.zip",
    "/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/cgi-bin/luci",
)

DEFAULT_TYPES: Sequence[str] = (
    "varredura",
    "forca_bruta",
    "crawler",
    "credencial_reutilizada",
    "sql_injection",
    "xss",
    "exploit_rce",
    "ddos",
    "botnet",
    "phishing",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulador de eventos para SentinelMap")
    parser.add_argument("--url", default="http://localhost:8000/event", help="Endpoint de ingestao")
    parser.add_argument("--interval", type=float, default=0.08, help="Intervalo entre eventos (segundos)")
    parser.add_argument("--count", type=int, default=0, help="Quantidade total de eventos (0 = infinito)")
    parser.add_argument("--timeout", type=float, default=2.0, help="Timeout HTTP por envio")
    return parser.parse_args()


def build_event() -> dict[str, str]:
    return {
        "ip": random.choice(DEFAULT_IPS),
        "type": random.choice(DEFAULT_TYPES),
        "path": random.choice(DEFAULT_PATHS),
        "ua": "sentinelmap-simulator/1.0",
    }


def main() -> None:
    args = parse_args()

    sent = 0
    while True:
        if args.count > 0 and sent >= args.count:
            print(f"Concluido: {sent} eventos enviados.")
            break

        event = build_event()

        try:
            response = requests.post(args.url, json=event, timeout=args.timeout)
            ok = response.status_code == 200
            status = "OK" if ok else f"HTTP {response.status_code}"
            print(f"[{sent + 1}] {status} | {event['type']} | {event['ip']} | {event['path']}")
        except requests.RequestException as exc:
            print(f"[{sent + 1}] FAIL | {exc}")

        sent += 1
        time.sleep(max(0.01, args.interval))


if __name__ == "__main__":
    main()
