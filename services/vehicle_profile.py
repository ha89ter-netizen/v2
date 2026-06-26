import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class VehicleProfile:
    brand: str
    model: str = ""
    year: str = ""
    mileage: Optional[int] = None
    engine: str = ""
    transmission: str = ""
    fuel: str = ""
    nickname: str = ""


def _parse_mileage(value: str) -> Optional[int]:
    match = re.search(r"(\d[\d\s]{2,})\s*(км|km)?", value.lower())
    if not match:
        return None
    return int(match.group(1).replace(" ", ""))


def parse_vehicle_profile(text: str) -> VehicleProfile:
    parts = [part.strip() for part in text.split("|")]
    base = parts[0] if parts else text.strip()
    tokens = base.split()
    year = ""
    if tokens and tokens[-1].isdigit() and len(tokens[-1]) == 4:
        year = tokens.pop()

    brand = tokens[0] if tokens else base
    model = " ".join(tokens[1:]) if len(tokens) > 1 else ""

    profile = VehicleProfile(brand=brand, model=model, year=year)
    extra = [part for part in parts[1:] if part]
    if extra:
        profile.mileage = _parse_mileage(extra[0])
    if len(extra) > 1:
        profile.engine = extra[1]
    if len(extra) > 2:
        profile.transmission = extra[2]
    if len(extra) > 3:
        profile.fuel = extra[3]
    if len(extra) > 4:
        profile.nickname = extra[4]
    return profile


def format_vehicle_profile(row) -> str:
    if not row:
        return "Авто не указано"

    _, vin, brand, model, year, mileage, engine, transmission, fuel, nickname = row
    name = " ".join(part for part in [brand, model, year] if part).strip()
    if nickname:
        name = f"{nickname} ({name})" if name else nickname

    details = []
    if vin:
        details.append(f"VIN: {vin}")
    if mileage:
        details.append(f"пробег {mileage} км")
    if engine:
        details.append(f"двигатель {engine}")
    if transmission:
        details.append(f"коробка {transmission}")
    if fuel:
        details.append(f"топливо {fuel}")

    return f"{name} — {', '.join(details)}" if details else name
