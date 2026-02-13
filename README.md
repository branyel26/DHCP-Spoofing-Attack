# DHCP Spoofing Attack (Man-in-the-Middle)

> 📚 **Asignatura:** Seguridad de Redes  
> 👨‍🏫 **Profesor:** Jonathan Rondón  
> 🏫 **Instituto Tecnológico de Las Américas (ITLA)**  
> 👤 **Autor:** Branyel Pérez

⚠️ **USO EXCLUSIVO EN ENTORNOS DE LABORATORIO CONTROLADOS.** El uso indebido de estas herramientas fuera de ambientes autorizados es ilegal y contrario a la ética profesional.

---

## Tabla de Contenidos

1. [Descripción del Ataque](#descripción-del-ataque)
2. [Topología de Red](#topología-de-red)
3. [Especificaciones Técnicas](#especificaciones-técnicas)
4. [Requisitos](#requisitos)
5. [Guía de Ejecución](#guía-de-ejecución)
6. [Verificación del Ataque](#verificación-del-ataque)
7. [Análisis Técnico](#análisis-técnico)

---

## Descripción del Ataque

Este ataque combina dos técnicas para lograr una posición de **Man-in-the-Middle (MitM)** en la red:

### Fase 1: DHCP Starvation
El script `agotador.py` inunda el servidor DHCP legítimo con solicitudes falsas hasta agotar su pool de direcciones IP disponibles.

### Fase 2: DHCP Rogue Server
Una vez saturado el servidor legítimo, `rogue.py` levanta un servidor DHCP malicioso que responde a las solicitudes de los clientes, asignándoles una IP pero configurando la **dirección del atacante como Gateway**, interceptando así todo el tráfico saliente.

### Objetivo Final
Posicionar al atacante como puerta de enlace de la víctima, permitiendo interceptar, analizar o modificar todo el tráfico de red.

---

## Topología de Red

![Topología de Red](Topologia.png)

---

## Especificaciones Técnicas

### Direccionamiento

| Segmento | Red | Máscara |
|----------|-----|---------|
| LAN Sede A | 10.14.89.0/25 | 255.255.255.128 |
| LAN Sede B | 10.14.89.128/25 | 255.255.255.128 |
| VLAN 30 (RRHH) | 10.14.89.192/27 | 255.255.255.224 |
| VLAN 40 (Contabilidad) | 10.14.89.224/27 | 255.255.255.224 |
| Backbone Serial | 10.0.0.0/30, 10.0.0.4/30, 10.0.0.8/30 | 255.255.255.252 |

### Actores del Laboratorio

| Rol | Equipo | Dirección IP | Observaciones |
|-----|--------|--------------|---------------|
| Atacante | Kali Linux | 10.14.89.4 | eth0 → SW1 (e0/3), Modo Dynamic Desirable |
| Víctima | PC1 | 10.14.89.2 → 10.14.89.20 | VLAN 10 (Ventas) |
| Gateway Legítimo | Router R1 | 10.14.89.1 | Servidor DHCP original |

### Parámetros del Ataque DHCP Rogue

| Parámetro | Valor |
|-----------|-------|
| IP del Servidor Rogue | 10.14.89.4 |
| IP Ofrecida a Víctima | 10.14.89.20 |
| Gateway Spoofed | 10.14.89.4 (Atacante) |
| DNS Ofrecido | 8.8.8.8 |
| Subnet Mask | 255.255.255.192 (/26) |

### Infraestructura

- **Routing:** OSPF Área 0 entre R1, R2 y R3
- **Switching Sede B:** SW2, SW3, SW4 en topología triangular
- **Protocolos L2:** EtherChannel + PVST+

---

## Requisitos

### Software
- Python 3.x
- Scapy

### Instalación de Dependencias
```bash
pip install scapy
```

### Permisos
- Privilegios de superusuario (root)

---

## Guía de Ejecución

### Paso 1: Identificar la Interfaz de Red
```bash
ip addr show
```

### Paso 2: Ejecutar DHCP Starvation (Agotar el pool legítimo)
```bash
sudo python3 agotador.py -i eth0
```

Este script envía solicitudes DHCP DISCOVER de forma continua para saturar el servidor DHCP de R1.

**Nota:** Ejecutar hasta observar que el pool está agotado. Presionar `Ctrl+C` para detener.

### Paso 3: Levantar el Servidor DHCP Rogue
```bash
sudo python3 rogue.py -i eth0 --my-ip 10.14.89.4 --victim-ip 10.14.89.20
```

### Parámetros del Script Rogue

| Parámetro | Descripción | Valor |
|-----------|-------------|-------|
| `-i`, `--iface` | Interfaz de red | **Requerido** |
| `--my-ip` | IP del atacante (será el gateway falso) | **Requerido** |
| `--victim-ip` | IP a asignar a la víctima | 10.14.89.20 |

### Ejemplo de Salida
```
[22:15:30] ROGUE: ESCUCHANDO EN eth0 (IP Falsa: 10.14.89.20)
[22:15:35] ROGUE: DISCOVER de aa:bb:cc:dd:ee:ff -> ATACANDO
[22:15:35] ROGUE: REQUEST recibido -> ENVIANDO ACK (VICTIMA CAYÓ)
```

---

## Verificación del Ataque

### En la Máquina Víctima
```bash
ip route show
# o
route -n
```

### Resultado Esperado
La víctima tendrá configurado como gateway la IP del atacante:
```
default via 10.14.89.4 dev eth0
```

### En el Router R1
```
R1# show ip dhcp binding
```
El pool estará lleno con MACs aleatorias del ataque Starvation.

---

## Análisis Técnico

### Flujo del Ataque

```
┌─────────────┐     DISCOVER     ┌─────────────┐
│   Víctima   │ ───────────────► │  Broadcast  │
└─────────────┘                  └─────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                                       ▼
            ┌─────────────┐                         ┌─────────────┐
            │  R1 (DHCP)  │ ← Pool Agotado          │   Atacante  │
            │   LEGÍTIMO  │   No responde           │    ROGUE    │
            └─────────────┘                         └─────────────┘
                                                           │
                                                     OFFER/ACK
                                                    Gateway: 10.14.89.4
                                                           │
                                                           ▼
                                                    ┌─────────────┐
                                                    │   Víctima   │
                                                    │ MitM Active │
                                                    └─────────────┘
```

### Estructura del Paquete DHCP OFFER/ACK Malicioso

```
DHCP Options:
├── Message Type: OFFER / ACK
├── Server Identifier: 10.14.89.4 (Atacante)
├── Subnet Mask: 255.255.255.192
├── Router (Gateway): 10.14.89.4 (Atacante) ← Clave del MitM
├── Lease Time: 3600
└── DNS Server: 8.8.8.8
```

### Indicadores de Compromiso (IoC)

- Servidor DHCP no autorizado en la red
- Gateway diferente al configurado legítimamente
- Alto volumen de DHCP DISCOVER desde MACs `02:xx`
- Respuestas DHCP desde IP no autorizada

---

## Evidencias del Laboratorio

### 1. Estado Inicial - Antes del Ataque
Configuración de red de la víctima con gateway legítimo (R1).

![Antes del ataque](Antes%20del%20Ataque%20DHCP%20Spoofing.png)

### 2. Fase 1: Ejecutando DHCP Starvation (agotador.py)
Agotando el pool de direcciones IP del servidor DHCP legítimo.

![Ejecutando Agotador](Ejecutando%20Agotador%20de%20pool.png)

### 3. Fase 2: Ejecutando Servidor Rogue (rogue.py)
Servidor DHCP falso respondiendo a solicitudes de las víctimas.

![Ejecutando Rogue](Ejecutando%20Starvation%20Attack.png)

### 4. Resultado - Después del Ataque
La víctima tiene configurado el gateway del atacante (MitM exitoso).

![Después del ataque](Después%20del%20ataque%20Starvation%20Attack.png)

---

## Archivos del Repositorio

| Archivo | Descripción |
|---------|-------------|
| `agotador.py` | Script de DHCP Starvation |
| `rogue.py` | Servidor DHCP Rogue/Spoofing |
| `Topologia.png` | Diagrama de la topología de red |
| `Antes del Ataque DHCP Spoofing.png` | Estado inicial de la víctima |
| `Ejecutando Agotador de pool.png` | Fase 1: Starvation |
| `Ejecutando Starvation Attack.png` | Fase 2: Servidor Rogue |
| `Después del ataque Starvation Attack.png` | MitM exitoso |
| `README.md` | Documentación técnica |

---

## Contramedidas

- **DHCP Snooping:** Filtra respuestas DHCP de puertos no confiables
- **Port Security:** Limita MACs por puerto
- **Rate Limiting:** Limita solicitudes DHCP por puerto

---

## Referencias

- RFC 2131 - Dynamic Host Configuration Protocol
- Documentación oficial de Scapy

---

**Disclaimer:** Este material es parte de un ejercicio académico supervisado. El autor no se responsabiliza por el uso indebido de este código.
