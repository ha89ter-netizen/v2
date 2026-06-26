from dataclasses import dataclass
from typing import Optional, Protocol

from services.parts.vin_parts_service import SUPPORTED_VEHICLES, VehicleContext, vehicle_catalog_key


@dataclass(frozen=True)
class PartOption:
    part_key: str
    part_name_ru: str
    part_name_en: str
    brand: str
    part_number: str
    classification: str
    price_kzt: int
    note: str = ""


class PartsProvider(Protocol):
    async def find_options(self, vehicle: VehicleContext, part_key: str) -> list[PartOption]:
        ...


def _option(part_key, ru, en, brand, number, classification, price, note="") -> PartOption:
    return PartOption(part_key, ru, en, brand, number, classification, price, note)


BASE_PARTS = {
    "ignition_coil": ("катушка зажигания", "ignition coil", "Denso", 38000, "Masuma", 17000),
    "spark_plug": ("свеча зажигания", "spark plug", "NGK", 18000, "Patron", 6500),
    "injector": ("форсунка", "fuel injector", "Denso", 62000, "SAT", 26000),
    "brake_pads": ("тормозные колодки", "brake pads", "Advics", 32000, "LYNXauto", 15000),
    "brake_disc": ("тормозной диск", "brake rotor", "Bosch", 48000, "Trialli", 21000),
    "shock_absorber": ("амортизатор", "shock absorber", "KYB", 52000, "AMD", 24000),
    "ball_joint": ("шаровая опора", "ball joint", "CTR", 26000, "Febest", 12000),
    "headlight": ("фара", "headlight", "TYC", 85000, "Depo", 42000),
    "fuel_pump": ("бензонасос", "fuel pump", "Denso", 68000, "Krauf", 29000),
    "battery": ("аккумулятор", "battery", "Varta", 62000, "Mutlu", 36000),
    "oxygen_sensor": ("датчик кислорода", "oxygen sensor", "Denso", 45000, "SAT", 18000),
}

VEHICLE_OEM_PREFIX = {
    key: (meta["display"], meta["prefix"])
    for key, meta in SUPPORTED_VEHICLES.items()
}
VEHICLE_OEM_PREFIX["generic"] = ("Generic", "GEN")


class MockPartsProvider:
    async def find_options(self, vehicle: VehicleContext, part_key: str) -> list[PartOption]:
        key = vehicle_catalog_key(vehicle)
        vehicle_label, prefix = VEHICLE_OEM_PREFIX.get(key, VEHICLE_OEM_PREFIX["generic"])
        ru, en, trusted_brand, trusted_price, cheap_brand, cheap_price = BASE_PARTS.get(
            part_key,
            ("неизвестная деталь", "unknown part", "Aftermarket", 30000, "NoName", 12000),
        )
        price_multiplier = {
            "toyota_sequoia_2018": 1.35,
            "toyota_camry_70": 1.0,
            "hyundai_elantra": 0.9,
            "kia_sportage": 0.95,
            "bmw_g30": 1.65,
            "generic": 1.0,
        }.get(key, 1.0)
        oem_price = int(trusted_price * price_multiplier * 1.65)
        trusted_price = int(trusted_price * price_multiplier)
        cheap_price = int(cheap_price * price_multiplier)
        part_code = part_key.upper().replace("_", "-")

        return [
            _option(part_key, ru, en, "OEM", f"{prefix}-{part_code}-OEM", "original_oem", oem_price, vehicle_label),
            _option(part_key, ru, en, trusted_brand, f"{prefix}-{part_code}-A1", "trusted_aftermarket", trusted_price, "качественный аналог"),
            _option(part_key, ru, en, cheap_brand, f"{prefix}-{part_code}-B1", "cheap_aftermarket", cheap_price, "дешёвый аналог"),
        ]


async def lookup_parts(vehicle: VehicleContext, part_key: str, provider: Optional[PartsProvider] = None) -> list[PartOption]:
    provider = provider or MockPartsProvider()
    return await provider.find_options(vehicle, part_key)
