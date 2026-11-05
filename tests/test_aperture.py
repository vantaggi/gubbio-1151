"""Porte e finestre al loro posto, edifici al loro posto (Cioti, 5 nov 2026: «verifica il posizionamento delle
porte e delle finestre sugli edifici, si vedono alcune sovrapposte»; prompt dei giri in
/mnt/project-files/fedelta/PROMPT_VERIFICA_MAPPA.md).

1. Ogni pittore di un'apertura (porta, porta del morto, bottega, finestra, ingresso, portale acceso) o di una cosa
   appesa alla facciata (stendardo, fiaccola, tenda, lanterna, botte, sacco, cassa, lance) lascia il rettangolo che
   ha dipinto in Quadro.ingombri; i portali e le finestre dei monumenti (gli archi bui della loro Tela) si
   aggiungono con il nome del monumento. Due rettangoli non si toccano, salvo le coppie che fanno un pezzo solo:
   l'ingresso con la sua lanterna e la sua tenda, e il portale del monumento che l'ingresso accende.
2. Fra due monumenti veri della stessa area la direzione nel gioco (nord in alto) e' quella di OpenStreetMap
   (lat/lon del censimento) entro 60 gradi, salvo le eccezioni scritte qui sotto con il loro perche'.
"""
import math
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import genera_mondo as G  # noqa: E402
import mondo_dati as M  # noqa: E402
import pittore_citta as PC  # noqa: E402

DELL_INGRESSO = {"lanterna", "tenda"}

# Le coppie di monumenti che stanno di proposito in un'altra direzione da quella vera.
ECCEZIONI = {
    # Il Duomo e il Ducale si fronteggiano sulla stradina: nel vero il Duomo sta a sud-est del Ducale. Il Duomo e'
    # disegnato sopra la stradina perche' la sua facciata si veda di fronte (regola del nord in alto: le facciate
    # dei monumenti si disegnano verso il basso); il Ducale sta sotto e si vede dall'alto col cortile.
    frozenset(("duomo", "ducale")): "la facciata del Duomo si vede di fronte",
    # San Francesco nel vero sta a sud-ovest della Loggia; nel gioco sta a sud (sbaglia di 60 gradi): a ovest della
    # Loggia ci sono i giardini, che prendono tutta la meta' sinistra della piazza. Da rivedere se si rifa' l'area
    # (registro /mnt/project-files/fedelta/GIRI_MAPPA.md).
    frozenset(("loggia_tiratori", "san_francesco")): "i giardini a ovest prendono il posto",
}
SOGLIA = 60


_QUADRI = {}


def quadri():
    if not _QUADRI:
        mondo = G.mondo_del_repo()
        G.TIENI_QUADRI = _QUADRI
        try:
            for n, t in G.sorgenti_del_repo():
                a = G.leggi_area(n, t)
                G.prepara_area(a, mondo)
                if G.area_di_citta(a):
                    G._disegna_area(a, {k: mondo[k] for k in G._MONDO_DEL_DISEGNO if k in mondo})
        finally:
            G.TIENI_QUADRI = None
    return _QUADRI


def tocca(a, b):
    return not (a[3] < b[1] or b[3] < a[1] or a[4] < b[2] or b[4] < a[2])


def area_di(r):
    return (r[3] - r[1] + 1) * (r[4] - r[2] + 1)


def intersezione(a, b):
    return max(0, min(a[3], b[3]) - max(a[1], b[1]) + 1) * max(0, min(a[4], b[4]) - max(a[2], b[2]) + 1)


def sovrapposti(ingombri):
    """Le coppie di ingombri che si toccano e non fanno un pezzo solo."""
    ingressi = [r for r in ingombri if r[0].startswith("ingresso")]
    # il portale di un monumento acceso da un ingresso: quasi tutto dentro il vano luminoso
    accesi = {i for i, r in enumerate(ingombri) if r[0].startswith("vano:") and
              any(intersezione(r, s) >= 0.5 * area_di(r) for s in ingressi)}
    fuori = []
    for i in range(len(ingombri)):
        for j in range(i + 1, len(ingombri)):
            a, b = ingombri[i], ingombri[j]
            if not tocca(a, b):
                continue
            tipi = {a[0].split(":")[0], b[0].split(":")[0]}
            if tipi <= DELL_INGRESSO | {"ingresso", "ingresso_laterale"} and tipi & {"ingresso", "ingresso_laterale"}:
                continue
            if tipi <= DELL_INGRESSO:
                continue                     # la tenda e la lanterna dello stesso ingresso
            if "vano" in tipi and (i in accesi or j in accesi) and tipi - {"vano"} <= DELL_INGRESSO | {"ingresso"}:
                continue
            fuori.append((a[:5], b[:5]))
    return fuori


class PorteEFinestre(unittest.TestCase):
    def test_nessuna_apertura_sovrapposta_in_nessuna_area(self):
        q = quadri()
        self.assertGreater(len(q), 10)
        errori = []
        for aid, quadro in sorted(q.items()):
            if quadro is None:
                continue
            for a, b in sovrapposti(quadro.ingombri):
                errori.append(f"{aid}: {a} tocca {b}")
        self.assertEqual(errori, [], "\n".join(errori[:30]))

    def test_gli_ingombri_ci_sono_davvero(self):
        tipi = {r[0].split(":")[0] for quadro in quadri().values() if quadro for r in quadro.ingombri}
        for t in ("porta", "finestra", "bottega", "porta_del_morto", "stendardo", "ingresso", "lanterna", "vano"):
            self.assertIn(t, tipi)

    def test_negativa_una_finestra_sulla_porta_si_trova(self):
        q = PC.Quadro(4, 6)
        PC._porta(q, 8, 40, 10, 28, 1)
        PC._finestra(q, 10, 10, 6, 7, 1, True)
        self.assertEqual(len(sovrapposti(q.ingombri)), 1)
        # e la lanterna dell'ingresso non conta
        q = PC.Quadro(4, 6)
        PC.dipingi_ingresso_frontale(q, 4, 20, 40)
        self.assertEqual(sovrapposti(q.ingombri), [])

    def test_le_finestre_di_una_casa_stretta_non_si_accavallano(self):
        # la casa che prima metteva tre finestre con le imposte in 24 pixel, attaccate alla porta
        for larga in range(2, 7):
            for fh in (2, 3, 4, 5):
                for n in range(30):
                    q = PC.Quadro(larga + 2, 8)
                    casa = PC.Casa(1, larga, 6, fh, n, morto=0.5)
                    PC.dipingi_casa(q, casa, larga + 2)
                    PC.vita_delle_case(q, [casa], "via_dei_consoli", 3)
                    self.assertEqual(sovrapposti(q.ingombri), [], (larga, fh, n))


APPESI_INTERNI = ("scaffale_a_muro", "camino", "ruota_a_muro", "stemma", "torcia", "chiarina", "rastrelliera_chiavi",
                  "disegni_appesi")


def ingombri_della_stanza(fare):
    """I rettangoli delle finestre (la cornice, senza la lama di luce sul pavimento) e delle cose appese al muro di
    fondo di una stanza (tools/pittore_interni.py): si avvolgono per il tempo della prova e poi si rimettono."""
    import pittore_interni as PI
    rec, pila = [], []
    vecchi = {n: getattr(PI, n) for n in APPESI_INTERNI}
    p, finestra = PI.Tela.p, PI.Stanza.finestra

    def punto(self, x, y, c):
        p(self, x, y, c)
        if pila:
            pila[-1].append((x, y))

    def avvolto(nome, f):
        def g(*a, **k):
            pila.append([])
            try:
                return f(*a, **k)
            finally:
                pts = pila.pop()
                if pts:
                    rec.append((nome, min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts),
                                max(y for _, y in pts)))
        return g

    def f_finestra(self, cx, larga=1, notte=False):
        x, y = self.px(cx, 0)
        w = larga * PI.CELLA - 6
        rec.append(("finestra", x + 2, y + 9, x + 3 + w, y + 32))
        return finestra(self, cx, larga, notte)
    try:
        PI.Tela.p, PI.Stanza.finestra = punto, f_finestra
        for n, f in vecchi.items():
            setattr(PI, n, avvolto(n, f))
        fare()
    finally:
        PI.Tela.p, PI.Stanza.finestra = p, finestra
        for n, f in vecchi.items():
            setattr(PI, n, f)
    return rec


class PareteDegliInterni(unittest.TestCase):
    def test_finestre_e_cose_appese_non_si_toccano(self):
        import pittore_interni as PI
        errori = []
        for nome, stanza in sorted(PI.STANZE.items()):
            for variante in ("giorno", "notte"):
                rec = ingombri_della_stanza(lambda: stanza(variante))
                self.assertTrue(rec, nome)
                for i, a in enumerate(rec):
                    for b in rec[i + 1:]:
                        if tocca(a, b):
                            errori.append(f"{nome} ({variante}): {a} tocca {b}")
        self.assertEqual(errori, [], "\n".join(errori))


class DisposizioneNelleAree(unittest.TestCase):
    def test_i_monumenti_stanno_nella_direzione_vera(self):
        mondo = G.mondo_del_repo()
        cen = mondo["censimento"]
        errori, viste = [], 0
        for n, t in G.sorgenti_del_repo():
            a = G.leggi_area(n, t)
            G.prepara_area(a, mondo)
            if not G.area_di_citta(a):
                continue
            ed = a.get("edifici", {})
            veri = sorted(k for k in ed if k in cen and M.punto(cen[k]) and cen[k].get("ruolo") != "storia_v2")
            for i, p in enumerate(veri):
                for q in veri[i + 1:]:
                    if frozenset((p, q)) in ECCEZIONI:
                        continue
                    (x0, y0, w0, h0), (x1, y1, w1, h1) = ed[p], ed[q]
                    gx, gy = (x1 + w1 / 2) - (x0 + w0 / 2), (y0 + h0 / 2) - (y1 + h1 / 2)
                    (la0, lo0), (la1, lo1) = M.punto(cen[p]), M.punto(cen[q])
                    rx, ry = (lo1 - lo0) * math.cos(math.radians(la0)), la1 - la0
                    d = abs((math.degrees(math.atan2(gx, gy) - math.atan2(rx, ry)) + 180) % 360 - 180)
                    viste += 1
                    if d > SOGLIA:
                        errori.append(f"{a['id']}: {p} -> {q} sbaglia di {d:.0f} gradi")
        self.assertGreater(viste, 5)
        self.assertEqual(errori, [], "\n".join(errori))


if __name__ == "__main__":
    unittest.main()
