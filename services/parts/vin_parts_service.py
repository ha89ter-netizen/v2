import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VehicleContext:
    make: str
    model: str
    year: str = ""
    engine: str = ""
    vin: str = ""
    display_name: str = ""


SUPPORTED_VEHICLES = {
    "toyota_sequoia_2018": {
        "display": "Toyota Sequoia 2018",
        "prefix": "TOY-SEQ18",
        "aliases": ("toyota sequoia 2018", "тойота секвойя 2018", "sequoia 2018"),
    },
    "toyota_camry_70": {
        "display": "Toyota Camry 70",
        "prefix": "TOY-CAM70",
        "aliases": ("toyota camry 70", "toyota camry xv70", "камри 70", "camry 70"),
    },
    "hyundai_elantra": {
        "display": "Hyundai Elantra",
        "prefix": "HYU-ELA",
        "aliases": ("hyundai elantra", "хендай элантра", "hyundai elantra 2020"),
    },
    "kia_sportage": {
        "display": "Kia Sportage",
        "prefix": "KIA-SPO",
        "aliases": ("kia sportage", "киа спортейдж"),
    },
    "bmw_g30": {
        "display": "BMW G30",
        "prefix": "BMW-G30",
        "aliases": ("bmw g30", "bmw 5 g30", "bmw 520", "bmw 530", "бмв g30"),
    },
    "lada_granta": {"display": "Lada Granta", "prefix": "LAD-GRA", "aliases": ("lada granta", "лада гранта", "granta")},
    "lada_vesta": {"display": "Lada Vesta", "prefix": "LAD-VES", "aliases": ("lada vesta", "лада веста", "vesta")},
    "lada_niva_travel": {"display": "Lada Niva Travel", "prefix": "LAD-NTR", "aliases": ("lada niva travel", "нива тревел", "niva travel")},
    "lada_niva_legend": {"display": "Lada Niva Legend", "prefix": "LAD-NLG", "aliases": ("lada niva legend", "нива легенд", "niva legend")},
    "lada_largus": {"display": "Lada Largus", "prefix": "LAD-LAR", "aliases": ("lada largus", "лада ларгус", "largus")},
    "haval_jolion": {"display": "Haval Jolion", "prefix": "HAV-JOL", "aliases": ("haval jolion", "хавал джолион", "jolion")},
    "haval_h6": {"display": "Haval H6", "prefix": "HAV-H6", "aliases": ("haval h6", "хавал h6")},
    "haval_m6": {"display": "Haval M6", "prefix": "HAV-M6", "aliases": ("haval m6", "хавал m6")},
    "haval_dargo": {"display": "Haval Dargo", "prefix": "HAV-DAR", "aliases": ("haval dargo", "хавал дарго", "dargo")},
    "haval_f7": {"display": "Haval F7", "prefix": "HAV-F7", "aliases": ("haval f7", "хавал f7")},
    "chery_tiggo_4_pro": {"display": "Chery Tiggo 4 Pro", "prefix": "CHR-T4P", "aliases": ("chery tiggo 4 pro", "тигго 4 про", "tiggo 4 pro")},
    "chery_tiggo_7_pro_max": {"display": "Chery Tiggo 7 Pro Max", "prefix": "CHR-T7M", "aliases": ("chery tiggo 7 pro max", "tiggo 7 pro max", "тигго 7 про макс")},
    "chery_tiggo_8_pro_max": {"display": "Chery Tiggo 8 Pro Max", "prefix": "CHR-T8M", "aliases": ("chery tiggo 8 pro max", "tiggo 8 pro max", "тигго 8 про макс")},
    "chery_arrizo_8": {"display": "Chery Arrizo 8", "prefix": "CHR-AR8", "aliases": ("chery arrizo 8", "arrizo 8", "арризо 8")},
    "chery_tiggo_9": {"display": "Chery Tiggo 9", "prefix": "CHR-T9", "aliases": ("chery tiggo 9", "tiggo 9", "тигго 9")},
    "geely_coolray": {"display": "Geely Coolray", "prefix": "GEE-CLR", "aliases": ("geely coolray", "джили кулрей", "coolray")},
    "geely_atlas_pro": {"display": "Geely Atlas Pro", "prefix": "GEE-ATL", "aliases": ("geely atlas pro", "джили атлас", "atlas pro")},
    "geely_monjaro": {"display": "Geely Monjaro", "prefix": "GEE-MON", "aliases": ("geely monjaro", "джили монжаро", "monjaro")},
    "geely_tugella": {"display": "Geely Tugella", "prefix": "GEE-TUG", "aliases": ("geely tugella", "джили тугелла", "tugella")},
    "geely_emgrand": {"display": "Geely Emgrand", "prefix": "GEE-EMG", "aliases": ("geely emgrand", "джили эмгранд", "emgrand")},
    "changan_cs35_plus": {"display": "Changan CS35 Plus", "prefix": "CHA-C35", "aliases": ("changan cs35 plus", "чанган cs35", "cs35 plus")},
    "changan_cs55_plus": {"display": "Changan CS55 Plus", "prefix": "CHA-C55", "aliases": ("changan cs55 plus", "чанган cs55", "cs55 plus")},
    "changan_uni_k": {"display": "Changan Uni-K", "prefix": "CHA-UNK", "aliases": ("changan uni k", "changan uni-k", "уни к", "uni k")},
    "changan_uni_v": {"display": "Changan Uni-V", "prefix": "CHA-UNV", "aliases": ("changan uni v", "changan uni-v", "уни в", "uni v")},
    "changan_alsvin": {"display": "Changan Alsvin", "prefix": "CHA-ALS", "aliases": ("changan alsvin", "чанган алсвин", "alsvin")},
    "hyundai_solaris": {"display": "Hyundai Solaris", "prefix": "HYU-SOL", "aliases": ("hyundai solaris", "хендай солярис", "solaris")},
    "hyundai_creta": {"display": "Hyundai Creta", "prefix": "HYU-CRE", "aliases": ("hyundai creta", "хендай крета", "creta")},
    "hyundai_tucson": {"display": "Hyundai Tucson", "prefix": "HYU-TUC", "aliases": ("hyundai tucson", "хендай туссан", "tucson")},
    "hyundai_sonata": {"display": "Hyundai Sonata", "prefix": "HYU-SON", "aliases": ("hyundai sonata", "хендай соната", "sonata")},
    "hyundai_santa_fe": {"display": "Hyundai Santa Fe", "prefix": "HYU-SFE", "aliases": ("hyundai santa fe", "хендай санта фе", "santa fe")},
    "kia_rio": {"display": "Kia Rio", "prefix": "KIA-RIO", "aliases": ("kia rio", "киа рио", "rio")},
    "kia_seltos": {"display": "Kia Seltos", "prefix": "KIA-SEL", "aliases": ("kia seltos", "киа селтос", "seltos")},
    "kia_k5": {"display": "Kia K5", "prefix": "KIA-K5", "aliases": ("kia k5", "киа k5")},
    "kia_cerato": {"display": "Kia Cerato", "prefix": "KIA-CER", "aliases": ("kia cerato", "киа церато", "cerato")},
    "kia_sorento": {"display": "Kia Sorento", "prefix": "KIA-SOR", "aliases": ("kia sorento", "киа соренто", "sorento")},
    "toyota_rav4": {"display": "Toyota RAV4", "prefix": "TOY-RAV", "aliases": ("toyota rav4", "toyota rav 4", "тойота рав4", "rav4")},
    "toyota_land_cruiser_prado": {"display": "Toyota Land Cruiser Prado", "prefix": "TOY-PRD", "aliases": ("toyota prado", "land cruiser prado", "прадо")},
    "toyota_corolla": {"display": "Toyota Corolla", "prefix": "TOY-COR", "aliases": ("toyota corolla", "тойота королла", "corolla")},
    "toyota_highlander": {"display": "Toyota Highlander", "prefix": "TOY-HIG", "aliases": ("toyota highlander", "тойота хайлендер", "highlander")},
    "toyota_land_cruiser_300": {"display": "Toyota Land Cruiser 300", "prefix": "TOY-LC3", "aliases": ("land cruiser 300", "toyota lc300", "lc 300", "крузак 300")},
    "renault_duster": {"display": "Renault Duster", "prefix": "REN-DUS", "aliases": ("renault duster", "рено дастер", "duster")},
    "renault_logan": {"display": "Renault Logan", "prefix": "REN-LOG", "aliases": ("renault logan", "рено логан", "logan")},
    "volkswagen_polo": {"display": "Volkswagen Polo", "prefix": "VW-POLO", "aliases": ("volkswagen polo", "vw polo", "фольксваген поло", "polo")},
    "skoda_rapid": {"display": "Skoda Rapid", "prefix": "SKO-RAP", "aliases": ("skoda rapid", "шкода рапид", "rapid")},
    "mazda_cx5": {"display": "Mazda CX-5", "prefix": "MAZ-CX5", "aliases": ("mazda cx5", "mazda cx-5", "мазда сх5", "cx5", "cx 5")},
    "chevrolet_cobalt": {"display": "Chevrolet Cobalt", "prefix": "CHE-COB", "aliases": ("chevrolet cobalt", "шевроле кобальт", "cobalt")},
    "chevrolet_nexia": {"display": "Chevrolet Nexia", "prefix": "CHE-NEX", "aliases": ("chevrolet nexia", "ravon nexia", "шевроле нексия", "nexia")},
    "nissan_qashqai": {"display": "Nissan Qashqai", "prefix": "NIS-QAS", "aliases": ("nissan qashqai", "ниссан кашкай", "qashqai")},
    "mitsubishi_outlander": {"display": "Mitsubishi Outlander", "prefix": "MIT-OUT", "aliases": ("mitsubishi outlander", "митсубиси аутлендер", "outlander")},
    "lexus_rx": {"display": "Lexus RX", "prefix": "LEX-RX", "aliases": ("lexus rx", "лексус rx", "lexus rx 350", "rx 350")},
    "toyota_camry_50": {"display": "Toyota Camry 50", "prefix": "TOY-CAM50", "aliases": ("toyota camry 50", "toyota camry xv50", "камри 50", "camry 50")},
    "toyota_camry_40": {"display": "Toyota Camry 40", "prefix": "TOY-CAM40", "aliases": ("toyota camry 40", "toyota camry xv40", "камри 40", "camry 40")},
    "toyota_land_cruiser_200": {"display": "Toyota Land Cruiser 200", "prefix": "TOY-LC2", "aliases": ("land cruiser 200", "toyota lc200", "lc 200", "крузак 200")},
    "toyota_fortuner": {"display": "Toyota Fortuner", "prefix": "TOY-FOR", "aliases": ("toyota fortuner", "тойота фортунер", "fortuner")},
    "toyota_alphard": {"display": "Toyota Alphard", "prefix": "TOY-ALP", "aliases": ("toyota alphard", "тойота альфард", "alphard")},
    "lexus_lx": {"display": "Lexus LX", "prefix": "LEX-LX", "aliases": ("lexus lx", "лексус lx", "lexus lx 570", "lx 570")},
    "lexus_gx": {"display": "Lexus GX", "prefix": "LEX-GX", "aliases": ("lexus gx", "лексус gx", "lexus gx 460", "gx 460")},
    "lexus_es": {"display": "Lexus ES", "prefix": "LEX-ES", "aliases": ("lexus es", "лексус es", "lexus es 250", "es 250")},
    "lexus_nx": {"display": "Lexus NX", "prefix": "LEX-NX", "aliases": ("lexus nx", "лексус nx", "lexus nx 200", "nx 200")},
    "nissan_x_trail": {"display": "Nissan X-Trail", "prefix": "NIS-XTR", "aliases": ("nissan x trail", "nissan x-trail", "ниссан икстрейл", "x trail", "x-trail")},
    "nissan_teana": {"display": "Nissan Teana", "prefix": "NIS-TEA", "aliases": ("nissan teana", "ниссан теана", "teana")},
    "nissan_juke": {"display": "Nissan Juke", "prefix": "NIS-JUK", "aliases": ("nissan juke", "ниссан жук", "juke")},
    "nissan_almera": {"display": "Nissan Almera", "prefix": "NIS-ALM", "aliases": ("nissan almera", "ниссан альмера", "almera")},
    "hyundai_accent": {"display": "Hyundai Accent", "prefix": "HYU-ACC", "aliases": ("hyundai accent", "хендай акцент", "accent")},
    "hyundai_palisade": {"display": "Hyundai Palisade", "prefix": "HYU-PAL", "aliases": ("hyundai palisade", "хендай палисад", "palisade")},
    "hyundai_i30": {"display": "Hyundai i30", "prefix": "HYU-I30", "aliases": ("hyundai i30", "хендай i30", "i30")},
    "kia_optima": {"display": "Kia Optima", "prefix": "KIA-OPT", "aliases": ("kia optima", "киа оптима", "optima")},
    "kia_ceed": {"display": "Kia Ceed", "prefix": "KIA-CEE", "aliases": ("kia ceed", "kia cee d", "киа сид", "ceed")},
    "kia_soul": {"display": "Kia Soul", "prefix": "KIA-SOU", "aliases": ("kia soul", "киа соул", "soul")},
    "kia_mohave": {"display": "Kia Mohave", "prefix": "KIA-MOH", "aliases": ("kia mohave", "киа мохав", "mohave")},
    "volkswagen_tiguan": {"display": "Volkswagen Tiguan", "prefix": "VW-TIG", "aliases": ("volkswagen tiguan", "vw tiguan", "фольксваген тигуан", "tiguan")},
    "volkswagen_jetta": {"display": "Volkswagen Jetta", "prefix": "VW-JET", "aliases": ("volkswagen jetta", "vw jetta", "фольксваген джетта", "jetta")},
    "volkswagen_passat": {"display": "Volkswagen Passat", "prefix": "VW-PAS", "aliases": ("volkswagen passat", "vw passat", "фольксваген пассат", "passat")},
    "skoda_octavia": {"display": "Skoda Octavia", "prefix": "SKO-OCT", "aliases": ("skoda octavia", "шкода октавия", "octavia")},
    "skoda_kodiaq": {"display": "Skoda Kodiaq", "prefix": "SKO-KOD", "aliases": ("skoda kodiaq", "шкода кодиак", "kodiaq")},
    "renault_sandero": {"display": "Renault Sandero", "prefix": "REN-SAN", "aliases": ("renault sandero", "рено сандеро", "sandero")},
    "renault_arkana": {"display": "Renault Arkana", "prefix": "REN-ARK", "aliases": ("renault arkana", "рено аркана", "arkana")},
    "chevrolet_lacetti": {"display": "Chevrolet Lacetti", "prefix": "CHE-LAC", "aliases": ("chevrolet lacetti", "шевроле лачетти", "lacetti")},
    "chevrolet_spark": {"display": "Chevrolet Spark", "prefix": "CHE-SPA", "aliases": ("chevrolet spark", "шевроле спарк", "spark")},
    "chevrolet_onix": {"display": "Chevrolet Onix", "prefix": "CHE-ONX", "aliases": ("chevrolet onix", "шевроле оникс", "onix")},
    "chevrolet_malibu": {"display": "Chevrolet Malibu", "prefix": "CHE-MAL", "aliases": ("chevrolet malibu", "шевроле малибу", "malibu")},
    "chevrolet_captiva": {"display": "Chevrolet Captiva", "prefix": "CHE-CAP", "aliases": ("chevrolet captiva", "шевроле каптива", "captiva")},
    "daewoo_matiz": {"display": "Daewoo Matiz", "prefix": "DAE-MAT", "aliases": ("daewoo matiz", "дэу матиз", "ravon matiz", "matiz")},
    "honda_cr_v": {"display": "Honda CR-V", "prefix": "HON-CRV", "aliases": ("honda cr v", "honda cr-v", "хонда срв", "cr v", "cr-v")},
    "honda_accord": {"display": "Honda Accord", "prefix": "HON-ACC", "aliases": ("honda accord", "хонда аккорд", "accord")},
    "honda_civic": {"display": "Honda Civic", "prefix": "HON-CIV", "aliases": ("honda civic", "хонда цивик", "civic")},
    "mazda_6": {"display": "Mazda 6", "prefix": "MAZ-6", "aliases": ("mazda 6", "mazda6", "мазда 6")},
    "mazda_cx9": {"display": "Mazda CX-9", "prefix": "MAZ-CX9", "aliases": ("mazda cx9", "mazda cx-9", "мазда сх9", "cx9", "cx 9")},
    "mitsubishi_pajero_sport": {"display": "Mitsubishi Pajero Sport", "prefix": "MIT-PAJ", "aliases": ("mitsubishi pajero sport", "митсубиси паджеро спорт", "pajero sport")},
    "subaru_forester": {"display": "Subaru Forester", "prefix": "SUB-FOR", "aliases": ("subaru forester", "субару форестер", "forester")},
    "bmw_f10": {"display": "BMW F10", "prefix": "BMW-F10", "aliases": ("bmw f10", "bmw 5 f10", "bmw 520 f10", "бмв f10")},
    "bmw_x5": {"display": "BMW X5", "prefix": "BMW-X5", "aliases": ("bmw x5", "бмв x5", "bmw x5 f15", "bmw x5 g05")},
    "mercedes_w212": {"display": "Mercedes-Benz E-Class W212", "prefix": "MER-W212", "aliases": ("mercedes w212", "mercedes e class w212", "мерседес w212", "e class w212")},
    "mercedes_w213": {"display": "Mercedes-Benz E-Class W213", "prefix": "MER-W213", "aliases": ("mercedes w213", "mercedes e class w213", "мерседес w213", "e class w213")},
    "audi_q7": {"display": "Audi Q7", "prefix": "AUD-Q7", "aliases": ("audi q7", "ауди q7", "q7")},
}


def _clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def vehicle_from_car_row(row) -> Optional[VehicleContext]:
    if not row:
        return None
    _, vin, brand, model, year, mileage, engine, transmission, fuel, nickname = row
    display = " ".join(part for part in [brand, model, year] if part).strip()
    if nickname:
        display = f"{nickname} ({display})" if display else nickname
    return VehicleContext(
        make=_clean(brand),
        model=_clean(model),
        year=_clean(year),
        engine=_clean(engine),
        vin=_clean(vin),
        display_name=display or _clean(brand),
    )


def vehicle_from_text(text: str) -> VehicleContext:
    value = _clean(text)
    vin_match = re.search(r"\b(?:VIN[:\s-]*)?([A-Z0-9]{17})\b", value, flags=re.I)
    vin = vin_match.group(1).upper() if vin_match else ""
    value = re.sub(r"\(?\b(?:VIN[:\s-]*)?[A-Z0-9]{17}\b\)?", "", value, flags=re.I).strip()
    value = value.split("—", 1)[0].strip()
    if not value and vin:
        return VehicleContext(make="", model="", vin=vin, display_name=f"VIN: {vin}")
    if "(" in value and ")" in value:
        value = value[value.find("(") + 1:value.rfind(")")].strip()

    tokens = value.split()
    year = ""
    for token in reversed(tokens):
        if token.isdigit() and len(token) == 4:
            year = token
            tokens.remove(token)
            break
    make = tokens[0] if tokens else value
    model = " ".join(tokens[1:]) if len(tokens) > 1 else ""
    return VehicleContext(make=make, model=model, year=year, vin=vin, display_name=value or text)


def vehicle_catalog_key(vehicle: VehicleContext) -> str:
    text = f"{vehicle.make} {vehicle.model} {vehicle.year} {vehicle.engine} {vehicle.display_name}".lower()
    normalized = re.sub(r"[^a-zа-яё0-9]+", " ", text).strip()
    for key, meta in SUPPORTED_VEHICLES.items():
        for alias in meta["aliases"]:
            alias_key = re.sub(r"[^a-zа-яё0-9]+", " ", alias.lower()).strip()
            if alias_key and alias_key in normalized:
                return key
    return "generic"
