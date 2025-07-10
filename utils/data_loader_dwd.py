import requests
import zipfile
import io
import pandas as pd
from datetime import datetime, timedelta
import yaml
import os 
from joblib import Memory

# Cache-Verzeichnis fuer joblib
memory = Memory("cache/joblib", verbose=0)

def load_yaml_config(path):
    with open(path, "r") as file:
        return yaml.safe_load(file)
    

#Mapping von internen Namen auf DWD Stationen
LOCATION_MAP = {
    "Aachen-Orsbach": "15000",
    "Ahaus": "07374",
    "Alfeld": "07367",
    "Angermuende": "00164",
    "Arkona": "00183",
    "Augsburg": "00232",
    "Bamberg": "00282",
    "Belm": "00342",
    "Berlin Brandenburg": "00427",
    "Berlin-Tegel": "00430",
    "Berus": "00460",
    "Boizenburg": "00591",
    "Boltenhagen": "00596",
    "Braunschweig": "00662",
    "Bremen": "00691",
    "Bremerhaven": "00701",
    "Bremervoerde": "00704",
    "Chemnitz": "00853",
    "Chieming": "00856",
    "Cottbus": "00880",
    "Cuxhaven": "00891",
    "Deuselbach": "00953",
    "Diepholz": "00963",
    "Doberlug-Kirchhain": "01001",
    "Dresden-Klotzsche": "01048",
    "Doernick": "06163",
    "Duesseldorf": "01078",
    "Eisenach": "07368",
    "Emden": "05839",
    "Fehmarn": "05516",
    "Feldberg/Mecklenburg": "07351",
    "Feldberg/Schwarzwald": "01346",
    "Fichtelberg": "01358",
    "Freiburg": "01443",
    "Freudenstadt": "01468",
    "Friesoythe-Altenoythe": "01503",
    "Fuerstenzell": "05856",
    "Gardelegen": "01544",
    "Garmisch-Partenkirchen": "01550",
    "Genthin": "01605",
    "Gera-Leumnitz": "01612",
    "Gießen/Wettenberg": "01639",
    "Greifswald": "01757",
    "Goerlitz": "01684",
    "Goettingen": "01691",
    "Hamburg-Fuhlsbuettel": "01975",
    "Hannover": "02014",
    "Harzgerode": "02044",
    "Helgoland": "02115",
    "Hersfeld": "02171",
    "Hof": "02261",
    "Hohenpeißenberg": "02290",
    "Kahler Asten": "02483",
    "Kaisersbach-Cronhuette": "02485",
    "Kempten": "02559",
    "Kleiner Feldberg/Taunus": "02601",
    "Klippeneck": "02638",
    "Konstanz": "02712",
    "Koeln/Bonn": "02667",
    "Lahr": "02812",
    "Lautertal-Oberlauter": "00867",
    "Leck": "02907",
    "Leinefelde": "02925",
    "Leipzig/Halle": "02932",
    "Lindenberg": "03015",
    "Lippspringe": "03028",
    "List auf Sylt": "03032",
    "Luebeck-Blankensee": "03086",
    "Luedenscheid": "03098",
    "Luegde-Paenbruch": "06197",
    "Magdeburg": "03126",
    "Mannheim": "05906",
    "Marienberg": "03167",
    "Meiningen": "03231",
    "Meßstetten-Appental": "03268",
    "Michelstadt-Vielbrunn": "03287",
    "Muehldorf": "03366",
    "Muenster/Osnabrueck": "01766",
    "Norderney": "03631",
    "Nuerburg-Barweiler": "03660",
    "Nuernberg": "03668",
    "Oberstdorf": "03730",
    "Oschatz": "03811",
    "Potsdam": "03987",
    "Regensburg": "04104",
    "Rheinstetten": "04177",
    "Rostock-Warnemuende": "04271",
    "Saarbruecken-Ensheim": "04336",
    "Sankt Peter-Ording": "04393",
    "Schleswig": "04466",
    "Soltau": "04745",
    "Straubing": "04911",
    "Stuttgart (Schnarrenberg)": "04928",
    "Trier-Petrisberg": "05100",
    "Trollenhagen": "05109",
    "Ueckermuende": "05142",
    "Waldmuenchen": "07370",
    "Weiden": "05397",
    "Weihenstephan-Duernast": "05404",
    "Weinbiet": "05426",
    "Werl": "05480",
    "Wiesenburg": "05546",
    "Wittenberg": "05629",
    "Wuerzburg": "05705",
    "Zinnwald-Georgenfeld": "05779",
    "Zugspitze": "05792",
    "Oehringen": "03761",
}
DATE_MAP = {
    "00164": ("20200101", "20240910"),
    "00183": ("20200101", "20241231"),
    "00232": ("20200101", "20241231"),
    "00282": ("20200101", "20241231"),
    "00342": ("20200101", "20241231"),
    "00427": ("20200101", "20241231"),
    "00430": ("20200101", "20210505"),
    "00460": ("20200101", "20241231"),
    "00591": ("20200101", "20241231"),
    "00596": ("20200101", "20241231"),
    "00662": ("20200101", "20241231"),
    "00691": ("20200101", "20241231"),
    "00701": ("20200101", "20241231"),
    "00704": ("20200101", "20241231"),
    "00853": ("20200101", "20241231"),
    "00856": ("20200101", "20241231"),
    "00867": ("20200101", "20241231"),
    "00880": ("20200101", "20241231"),
    "00891": ("20200101", "20240902"),
    "00953": ("20200101", "20241231"),
    "00963": ("20200101", "20241231"),
    "01001": ("20200101", "20240919"),
    "01048": ("20200101", "20241231"),
    "01078": ("20200101", "20241231"),
    "01346": ("20200101", "20241231"),
    "01358": ("20200101", "20241231"),
    "01443": ("20200101", "20241231"),
    "01468": ("20200101", "20241231"),
    "01503": ("20200101", "20241231"),
    "01544": ("20200101", "20240918"),
    "01550": ("20200101", "20241231"),
    "01605": ("20200101", "20241231"),
    "01612": ("20200101", "20241231"),
    "01639": ("20200101", "20241231"),
    "01684": ("20200101", "20241231"),
    "01691": ("20200101", "20241231"),
    "01757": ("20200101", "20241120"),
    "01766": ("20200101", "20241231"),
    "01975": ("20200101", "20241231"),
    "02014": ("20200101", "20241231"),
    "02044": ("20200101", "20240911"),
    "02115": ("20200101", "20241231"),
    "02171": ("20200101", "20241231"),
    "02261": ("20200101", "20241231"),
    "02290": ("20200101", "20241231"),
    "02483": ("20200101", "20241231"),
    "02485": ("20200101", "20240412"),
    "02559": ("20200101", "20241231"),
    "02601": ("20200101", "20241231"),
    "02638": ("20200101", "20241231"),
    "02667": ("20200101", "20241231"),
    "02712": ("20200101", "20241231"),
    "02812": ("20200101", "20241029"),
    "02907": ("20200101", "20241231"),
    "02925": ("20200101", "20241231"),
    "02932": ("20200101", "20241231"),
    "03015": ("20200101", "20241231"),
    "03028": ("20200101", "20241231"),
    "03032": ("20200101", "20241231"),
    "03086": ("20200101", "20241130"),
    "03098": ("20200101", "20241231"),
    "03126": ("20200101", "20241211"),
    "03167": ("20200101", "20241231"),
    "03231": ("20200101", "20241231"),
    "03268": ("20200101", "20240819"),
    "03287": ("20200101", "20241231"),
    "03366": ("20200101", "20241231"),
    "03631": ("20200101", "20241231"),
    "03660": ("20200101", "20241231"),
    "03668": ("20200101", "20241231"),
    "03730": ("20200101", "20241231"),
    "03761": ("20200101", "20241231"),
    "03811": ("20200101", "20240529"),
    "03987": ("20200101", "20241231"),
    "04104": ("20200101", "20241231"),
    "04177": ("20200101", "20241231"),
    "04271": ("20200101", "20241231"),
    "04336": ("20200101", "20241231"),
    "04393": ("20200101", "20241231"),
    "04466": ("20200101", "20241231"),
    "04745": ("20200101", "20241231"),
    "04911": ("20200101", "20241231"),
    "04928": ("20200101", "20241231"),
    "05100": ("20200101", "20241231"),
    "05109": ("20200101", "20241001"),
    "05142": ("20200101", "20241231"),
    "05397": ("20200101", "20241231"),
    "05404": ("20200101", "20241231"),
    "05426": ("20200101", "20241231"),
    "05480": ("20200101", "20241231"),
    "05516": ("20200101", "20240821"),
    "05546": ("20200101", "20240411"),
    "05629": ("20200101", "20241231"),
    "05705": ("20200101", "20241231"),
    "05779": ("20200101", "20241231"),
    "05792": ("20200101", "20241231"),
    "05839": ("20200101", "20241231"),
    "05856": ("20200101", "20241231"),
    "05906": ("20200101", "20241231"),
    "06163": ("20200101", "20241231"),
    "06197": ("20200101", "20241231"),
    "07351": ("20200101", "20240926"),
    "07367": ("20200101", "20240827"),
    "07368": ("20200101", "20240612"),
    "07370": ("20200101", "20241231"),
    "07374": ("20200101", "20241231"),
    "15000": ("20200101", "20241231"),
}

@memory.cache
def _parse_zip_content(content, station_id):
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        txt = next(n for n in z.namelist() if n.endswith(".txt"))
        df = pd.read_csv(z.open(txt), sep=';', encoding='latin1', na_values='-999', dtype=str)

    df['STATIONS_ID'] = df['STATIONS_ID'].str.strip().str.zfill(5)
    df['MESS_DATUM'] = pd.to_datetime(df['MESS_DATUM'], format='%Y%m%d%H%M')
    df = df[df['STATIONS_ID'] == station_id]

    return df

def _load_monthly_weather_df(station_id, url, local_zip_path):

    # Pruefe ob ZIP-Datei lokal vorhanden ist (Dateicache)
    if os.path.exists(local_zip_path):
        with open(local_zip_path, "rb") as f:
            content = f.read()
    else:
        print(f"⬇️ Lade ZIP von URL: {url}")
        resp = requests.get(url)
        resp.raise_for_status()
        content = resp.content
        os.makedirs(os.path.dirname(local_zip_path), exist_ok=True)
        with open(local_zip_path, "wb") as f:
            f.write(content)

    # Hier: Parsen cache'n – somit wird die ZIP nur einmal entpackt und geparst
    df = _parse_zip_content(content, station_id)

    return df


def load_weather_data(location, date, typ):
    target_date = pd.to_datetime(date).date()
    year, month = target_date.year, target_date.month

    station_id = LOCATION_MAP.get(location)
    if not station_id:
        raise ValueError(f"❌ Kein Mapping fuer Standort '{location}' gefunden.")

    start_str, end_str = DATE_MAP.get(station_id, (None, None))
    if not start_str:
        raise ValueError(f"❌ Kein gueltiger Zeitraum fuer Station-ID {station_id} hinterlegt.")

    if typ == "pv":
        data_type = "solar"
        code = "SOLAR"
        key = "GS_10"
        out = "pv"
    elif typ == "wind":
        data_type = "wind"
        code = "wind"
        key = "FF_10"
        out = "wind"
    else:
        raise ValueError(f"Unbekannter Typ '{typ}'")

    # URL & ZIP-Pfad muus ggf. angepasst werden 
    url = f"https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/{data_type}/recent/10minutenwerte_{code}_{station_id}_akt.zip"
    local_zip_path = os.path.join("cache", f"{station_id}_{data_type}_{year}_{month:02d}.zip")

    # Hole Monats-DataFrame aus persistentem Cache
    df = _load_monthly_weather_df(station_id, url, local_zip_path)

    # Filtere nur den angeforderten Tag
    df = df[df['MESS_DATUM'].dt.date == target_date]

    if df.empty:
        raise ValueError(f"⚠️ Keine Daten fuer '{location}' am {target_date} ({key}).")

    # Erzeuge Ergebnis
    result = [
        {"datetime": row["MESS_DATUM"].to_pydatetime(), out: float(row[key]) if pd.notna(row[key]) else None}
        for _, row in df.iterrows()
    ]

    return result
