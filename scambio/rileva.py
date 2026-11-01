#!/usr/bin/env python3
"""Rilievo della Gubbio reale per la mappa topologica del gioco.

Va lanciato su una macchina che raggiunge overpass-api.de e api.opentopodata.org
(in cloud sono bloccati). Solo libreria standard.

    python rileva.py [cartella_uscita]

Scrive in cartella_uscita (default: cartella dello script):
  rilievo.json  strade con nome (geometria), porte, piazze, mura, corsi d'acqua, cime,
                e la quota del terreno (DEM EU-DEM 25 m) su monumenti, strade e cime.
Stampa a fine giro un riepilogo; incollare il riepilogo nel thread basta, ma il file e' meglio.
"""
import json, math, os, sys, time, urllib.parse, urllib.request

UA = "gubbio-1151-mappa/1.0 (gioco amatoriale; contatto: vantaggi su GitHub)"
OVERPASS = "https://overpass-api.de/api/interpreter"
TOPO = "https://api.opentopodata.org/v1/{ds}"
CENTRO = (43.344, 12.562, 43.366, 12.594)   # sud, ovest, nord, est: centro storico + Bottaccione + Ingino
LARGO = (43.30, 12.48, 43.42, 12.68)        # per le cime attorno

# Ancore dei monumenti (da f3/censimento.csv; basilica corretta col terzo giro).
ANCORE = {
    "consoli": (43.353421, 12.578262), "pretorio": (43.353033, 12.579304),
    "piazza_grande": (43.353213, 12.57897), "ranghiasci": (43.353442, 12.579003),
    "case_consoli": (43.354353, 12.57675), "fontana_matti": (43.354419, 12.576765),
    "bargello": (43.354436, 12.57663), "san_domenico": (43.354557, 12.574557),
    "capitano_popolo": (43.356377, 12.575773), "ponte_san_martino": (43.354748, 12.57601),
    "porta_metauro": (43.356554, 12.576066), "teatro_romano": (43.351844, 12.572537),
    "san_francesco": (43.351557, 12.576707), "loggia_tiratori": (43.352105, 12.577544),
    "santa_maria_laici": (43.352418, 12.57723), "san_pietro": (43.349047, 12.580716),
    "porta_san_pietro": (43.348823, 12.579596), "sant_agostino": (43.349513, 12.584352),
    "porta_romana": (43.349755, 12.583834), "san_marziale": (43.35094, 12.5834),
    "santa_maria_nuova": (43.350343, 12.583113), "duomo": (43.353651, 12.580159),
    "ducale": (43.353977, 12.579606), "canonici": (43.352929, 12.580349),
    "mura_rocca": (43.359299, 12.585932), "basilica": (43.356367, 12.584993),
    "gola_bottaccione": (43.361652, 12.580337), "acquedotto": (43.36128, 12.581492),
    "sant_ambrogio": (43.358794, 12.576479),
}


def get(url, params=None, data=None, tentativi=5):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    corpo = urllib.parse.urlencode(data).encode() if data else None
    for i in range(tentativi):
        try:
            req = urllib.request.Request(url, data=corpo, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # 429/502/504 di Overpass e opentopodata capitano
            attesa = 3 * 2 ** i
            print(f"  errore {e}; ritento fra {attesa}s", file=sys.stderr)
            time.sleep(attesa)
    raise SystemExit(f"FALLITO: {url}")


def overpass(q):
    return get(OVERPASS, data={"data": "[out:json][timeout:120];" + q})["elements"]


def bb(b):
    return f"({b[0]},{b[1]},{b[2]},{b[3]})"


def geom(el):
    if "geometry" in el:
        return [[round(p["lat"], 6), round(p["lon"], 6)] for p in el["geometry"] if p]
    if "lat" in el:
        return [[round(el["lat"], 6), round(el["lon"], 6)]]
    if "center" in el:
        return [[round(el["center"]["lat"], 6), round(el["center"]["lon"], 6)]]
    return []


def metri(a, b):
    dy = (b[0] - a[0]) * 111320
    dx = (b[1] - a[1]) * 111320 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)


def campiona(punti, passo=35):
    """Un punto ogni ~passo metri lungo la polilinea, estremi compresi."""
    if len(punti) < 2:
        return list(punti)
    out, acc = [punti[0]], 0.0
    for a, b in zip(punti, punti[1:]):
        acc += metri(a, b)
        if acc >= passo:
            out.append(b)
            acc = 0.0
    if out[-1] != punti[-1]:
        out.append(punti[-1])
    return out


def quote(punti):
    """Quote DEM per una lista di [lat, lon]; 100 punti per chiamata, 1 chiamata al secondo."""
    ris = []
    for ds in ("eudem25m", "srtm30m"):
        ris = []
        ok = True
        for i in range(0, len(punti), 100):
            blocco = punti[i:i + 100]
            locs = "|".join(f"{p[0]},{p[1]}" for p in blocco)
            r = get(TOPO.format(ds=ds), params={"locations": locs})
            if r.get("status") != "OK":
                ok = False
                break
            ris += [None if x["elevation"] is None else round(x["elevation"], 1) for x in r["results"]]
            time.sleep(1.1)
        if ok:
            return ds, ris
    return None, [None] * len(punti)


def main():
    uscita = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    os.makedirs(uscita, exist_ok=True)
    print("1/3 Overpass: strade, porte, piazze, mura, acque...")
    els = overpass(
        f'(way["highway"]["name"]{bb(CENTRO)};'
        f'way["highway"~"steps|footway|path|track|pedestrian"]{bb(CENTRO)};'
        f'nwr["historic"="city_gate"]{bb(CENTRO)};'
        f'nwr["barrier"="city_wall"]{bb(CENTRO)};'
        f'nwr["historic"="citywalls"]{bb(CENTRO)};'
        f'nwr["place"="square"]{bb(CENTRO)};'
        f'way["highway"="pedestrian"]["area"="yes"]{bb(CENTRO)};'
        f'way["waterway"]{bb(CENTRO)};'
        f'node["aerialway"="station"]{bb(CENTRO)};'
        f'way["aerialway"]{bb(CENTRO)};'
        f');out geom;')
    time.sleep(2)
    print("2/3 Overpass: cime e passi attorno...")
    cime = overpass(f'(node["natural"~"peak|saddle"]["name"]{bb(LARGO)};'
                    f'node["mountain_pass"="yes"]["name"]{bb(LARGO)};);out;')
    elementi = []
    for el in els + cime:
        t = el.get("tags", {})
        elementi.append({"osm": f'{el["type"]}/{el["id"]}', "nome": t.get("name"),
                         "tag": {k: v for k, v in t.items() if k in (
                             "highway", "historic", "barrier", "place", "waterway", "natural",
                             "ele", "incline", "steps", "aerialway", "tunnel", "bridge", "alt_name",
                             "old_name", "area", "surface")},
                         "geom": geom(el)})
    print(f"   {len(elementi)} elementi")

    print("3/3 Quote DEM...")
    punti, chi = [], []
    for k, p in ANCORE.items():
        punti.append(list(p)); chi.append(("ancora", k, 0))
    for i, e in enumerate(elementi):
        t = e["tag"]
        if e["nome"] and ("highway" in t or "historic" in t or "place" in t or "natural" in t):
            for j, p in enumerate(campiona(e["geom"])):
                punti.append(p); chi.append(("elemento", i, j))
    vista, uniq = {}, []
    for p in punti:
        key = (round(p[0], 5), round(p[1], 5))
        if key not in vista:
            vista[key] = len(uniq); uniq.append(list(key))
    print(f"   {len(uniq)} punti unici")
    ds, q = quote(uniq)
    quota_ancore, profili = {}, {}
    for p, (tipo, a, j) in zip(punti, chi):
        z = q[vista[(round(p[0], 5), round(p[1], 5))]]
        if tipo == "ancora":
            quota_ancore[a] = z
        else:
            profili.setdefault(a, []).append([p[0], p[1], z])
    for i, prof in profili.items():
        elementi[i]["profilo"] = prof

    out = {"_leggimi": "Rilievo OSM + DEM per la mappa topologica di Gubbio 1151. Geometrie [lat, lon]; "
                       "profilo = [lat, lon, quota m s.l.m.] ogni ~35 m. Dati OSM (c) OpenStreetMap contributors, ODbL.",
           "dem": ds, "quando": time.strftime("%Y-%m-%d %H:%M"), "quota_ancore": quota_ancore,
           "elementi": elementi}
    f = os.path.join(uscita, "rilievo.json")
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"\nScritto {f} ({os.path.getsize(f)//1024} KB), DEM={ds}")
    print("Quote delle ancore (m s.l.m.):")
    for k, z in sorted(quota_ancore.items(), key=lambda kv: (kv[1] is None, kv[1])):
        print(f"  {k:20s} {z}")
    nomi = sorted({e['nome'] for e in elementi if e['nome'] and 'highway' in e['tag']})
    print(f"Strade con nome: {len(nomi)}")
    print("Cime:", ", ".join(f"{e['nome']} {e['tag'].get('ele','?')}" for e in elementi if 'natural' in e['tag']))


if __name__ == "__main__":
    main()
