from dataclasses import dataclass
from urllib.parse import quote_plus

from services.parts.oem_lookup import PartOption
from services.parts.vin_parts_service import VehicleContext
from services.i18n import is_english


@dataclass(frozen=True)
class SearchLink:
    title: str
    query: str
    url: str


def _vehicle_query(vehicle: VehicleContext) -> str:
    return " ".join(part for part in [vehicle.make, vehicle.model, vehicle.year, vehicle.engine] if part).strip()


def build_search_links(vehicle: VehicleContext, option: PartOption, language_code: str = "") -> list[SearchLink]:
    vehicle_text = _vehicle_query(vehicle)
    queries = [
        f"{vehicle_text} {option.part_name_en} OEM {option.part_number}",
        f"{vehicle_text} {option.part_name_en} {option.brand}",
        f"{vehicle_text} {option.part_name_ru} купить Казахстан",
        f"{option.part_number} купить Казахстан",
    ]
    titles = (
        ["OEM original search", "Brand/analog search", "Search in Kazakhstan", "Search by part number"]
        if is_english(language_code)
        else ["OEM оригинал", "Бренд / аналог", "Купить в Казахстане", "Поиск по номеру"]
    )
    return [
        SearchLink(title, query, f"https://www.google.com/search?q={quote_plus(query)}")
        for title, query in zip(titles, queries)
    ]
