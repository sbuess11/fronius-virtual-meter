import json
import os
import time
from pyModbusTCP.server import ModbusServer, DataBank

OPTIONS_PATH = "/data/options.json"


def load_options():
    bind_port = 1502
    dummy_power_w = 1000

    if os.path.exists(OPTIONS_PATH):
        with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            bind_port = int(data.get("bind_port", bind_port))
            dummy_power_w = int(data.get("dummy_power_w", dummy_power_w))

    return bind_port, dummy_power_w


def to_u16(value: int) -> int:
    if value < 0:
        return (1 << 16) + value
    return value & 0xFFFF


def str_to_regs(text: str, reg_count: int):
    text = (text or "")[: reg_count * 2]
    text = text.ljust(reg_count * 2, " ")
    regs = []
    for i in range(0, len(text), 2):
        regs.append((ord(text[i]) << 8) + ord(text[i + 1]))
    return regs


def set_regs(start_1_based: int, values):
    DataBank.set_holding_registers(start_1_based - 40001, list(values))


def write_static_identity():
    set_regs(40001, [0x5375, 0x6E53])  # 'SunS'
    set_regs(40003, [1, 65])

    set_regs(40005, str_to_regs("Fronius", 16))
    set_regs(40021, str_to_regs("Smart Meter IP", 16))
    set_regs(40037, str_to_regs("HA-VirtualMeter", 8))
    set_regs(40045, str_to_regs("00000001", 16))
    set_regs(40061, str_to_regs("HAVM0001", 16))
    set_regs(40077, [240])

    set_regs(40079, [203, 105])


def write_measurements(power_w: int):
    l1 = int(round(power_w / 3.0))
    l2 = int(round(power_w / 3.0))
    l3 = power_w - l1 - l2

    set_regs(40125, [to_u16(power_w)])
    set_regs(40126, [to_u16(l1)])
    set_regs(40127, [to_u16(l2)])
    set_regs(40128, [to_u16(l3)])

    set_regs(40083, [to_u16(power_w)])
    set_regs(40084, [0])

    now_wh = int(time.time() // 10)
    import_wh = now_wh if power_w >= 0 else 0
    export_wh = now_wh if power_w < 0 else 0

    set_regs(40129, [import_wh & 0xFFFF])
    set_regs(40130, [export_wh & 0xFFFF])


def main():
    bind_port, dummy_power_w = load_options()

    print("=== Fronius Virtual Meter starting ===")
    print(f"Port: {bind_port}")
    print(f"Dummy power: {dummy_power_w} W")

    write_static_identity()
    write_measurements(dummy_power_w)

    server = ModbusServer(host="0.0.0.0", port=bind_port, no_block=True)
    server.start()

    print("Modbus TCP server is running")

    try:
        while True:
            _, dummy_power_w = load_options()
            write_measurements(dummy_power_w)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


if __name__ == "__main__":
    main()
