#!/usr/bin/env python3
"""Sagome degli edifici e aree stradali del centro di Gubbio, per misurare larghezze di vie e piazze.

Va lanciato dove overpass-api.de e' raggiungibile (in cloud e' bloccato). Solo libreria standard.
    python rileva_edifici.py [cartella_uscita]
Scrive edifici.json: edifici (poligoni), aree pedonali/piazze (area:highway, highway=pedestrian area,
place=square), e tag di larghezza delle strade (width, est_width, lanes). (c) OpenStreetMap contributors, ODbL.
"""
import json, os, sys, time, urllib.parse, urllib.request

UA = "gubbio-1151-mappa/1.0 (gioco amatoriale; contatto: vantaggi su GitHub)"
OVERPASS = "https://overpass-api.de/api/interpreter"
BB = "(43.3470,12.5700,43.3580,12.5870)"   # centro murato + Teatro + Sant'Agostino


def overpass(q):
    data = urllib.parse.urlencode({"data": "[out:json][timeout:180];" + q}).encode()
    for i in range(5):
        try:
            req = urllib.request.Request(OVERPASS, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=200) as r:
                return json.loads(r.read().decode("utf-8"))["elements"]
        except Exception as e:
            print(f"  errore {e}; ritento", file=sys.stderr)
            time.sleep(4 * 2 ** i)
    raise SystemExit("FALLITO")


def geom(el):
    if "geometry" in el:
        return [[round(p["lat"], 7), round(p["lon"], 7)] for p in el["geometry"] if p]
    if el["type"] == "relation":
        out = []
        for m in el.get("members", []):
            if m.get("role") == "outer" and "geometry" in m:
                out += [[round(p["lat"], 7), round(p["lon"], 7)] for p in m["geometry"] if p]
        return out
    return []


def main():
    uscita = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    print("1/2 edifici...")
    ed = overpass(f'(way["building"]{BB};relation["building"]{BB};);out geom;')
    time.sleep(2)
    print("2/2 aree stradali e larghezze...")
    ar = overpass(f'(way["area:highway"]{BB};way["highway"]["area"="yes"]{BB};nwr["place"="square"]{BB};'
                  f'way["highway"]["width"]{BB};way["highway"]["est_width"]{BB};way["man_made"="bridge"]{BB};);out geom;')
    keep = ("building", "name", "height", "building:levels", "area:highway", "highway", "area", "place",
            "width", "est_width", "lanes", "man_made", "historic", "amenity")
    def pack(el):
        t = el.get("tags", {})
        return {"osm": f'{el["type"]}/{el["id"]}', "tag": {k: v for k, v in t.items() if k in keep}, "geom": geom(el)}
    out = {"_leggimi": "Edifici e aree stradali OSM del centro di Gubbio (c) OpenStreetMap contributors, ODbL.",
           "quando": time.strftime("%Y-%m-%d %H:%M"),
           "edifici": [pack(e) for e in ed], "aree": [pack(e) for e in ar]}
    f = os.path.join(uscita, "edifici.json")
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"Scritto {f} ({os.path.getsize(f)//1024} KB): {len(out['edifici'])} edifici, {len(out['aree'])} aree")


if __name__ == "__main__":
    main()
