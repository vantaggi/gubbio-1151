#ifndef GUBBIO_TESTO_AUTOTEST_H
#define GUBBIO_TESTO_AUTOTEST_H

#include "testo.h"

// Autotest esaustivo dei testi: disegna ogni TestoId, nel suo contesto, a ogni lunghezza di
// rivelazione della macchina da scrivere, e ricontrolla ogni tabella di tools/genera_testi.py.
// E' constexpr: src/autotest_testi.cpp lo esegue a tempo di compilazione (la ROM non compila se
// fallisce) e la schermata di prova lo riesegue sul GBA per stampare il conteggio.
namespace gubbio::testo
{

enum class ErroreAutotest : int
{
    NESSUNO,
    RIGHE_FUORI_CONTESTO,      // piu' righe di quante il contesto ne ammetta
    RIGA_TROPPO_LARGA,         // larghezza oltre il contesto
    RIGHE_NON_CONTIGUE,        // i glifi delle righe non si susseguono
    GLIFI_NON_TORNANO,         // la somma dei glifi delle righe non e' quella del testo
    BYTE_NON_CRESCENTE,        // i passi della macchina da scrivere tornano indietro nel testo
    BYTE_NON_CONFINE,          // un passo cade in mezzo a un carattere UTF-8
    CODICE_DIVERSO,            // il glifo non e' il carattere che sta a quel byte
    X_SBAGLIATA,               // x del glifo diversa dalla somma degli avanzamenti
    LARGHEZZA_SBAGLIATA,       // larghezza della riga diversa da quella dei glifi
    TAGLIO_SBAGLIATO,          // punto di taglio diverso dal primo glifo che tocca lo sprite
    PIXEL_IN_SPRITE_SPENTO,    // un pixel cade in uno sprite che a quel passo e' ancora spento
    PIXEL_FUORI_CONTESTO,      // un pixel esce dalla larghezza del contesto
};

struct EsitoAutotest
{
    int passi = 0;      // (testo, lunghezza di rivelazione) disegnati
    int pixel = 0;      // pixel accesi in tutti i passi
    ErroreAutotest errore = ErroreAutotest::NESSUNO;
    int testo = -1;
    int riga = -1;
    int passo = -1;
};

// Codice del carattere UTF-8 che comincia a 'byte', o -1 se non e' un inizio di carattere valido.
constexpr int decodifica_utf8(const char* s, int lunghezza, int byte)
{
    if(byte < 0 || byte >= lunghezza)
    {
        return -1;
    }

    int b0 = (unsigned char)(s[byte]);
    int continuazioni = 0;
    int codice = 0;

    if(b0 < 0x80)
    {
        return b0;
    }
    else if((b0 & 0xE0) == 0xC0)
    {
        continuazioni = 1;
        codice = b0 & 0x1F;
    }
    else if((b0 & 0xF0) == 0xE0)
    {
        continuazioni = 2;
        codice = b0 & 0x0F;
    }
    else if((b0 & 0xF8) == 0xF0)
    {
        continuazioni = 3;
        codice = b0 & 0x07;
    }
    else
    {
        return -1;   // byte di continuazione 10xxxxxx: non e' un confine di carattere
    }

    for(int i = 1; i <= continuazioni; ++i)
    {
        if(byte + i >= lunghezza)
        {
            return -1;
        }

        int b = (unsigned char)(s[byte + i]);

        if((b & 0xC0) != 0x80)
        {
            return -1;
        }

        codice = (codice << 6) | (b & 0x3F);
    }

    return codice;
}

constexpr EsitoAutotest autotest_testi()
{
    EsitoAutotest esito;

    auto fallisci = [&esito](ErroreAutotest e, int t, int r, int p) {
        esito.errore = e;
        esito.testo = t;
        esito.riga = r;
        esito.passo = p;
        return esito;
    };

    for(int t = 0; t < testi::TESTI_CONTEGGIO; ++t)
    {
        const Testo& testo = dati(TestoId(t));
        int larghezza_max = larghezza_contesto(testo.contesto);
        int sprite_max = sprite_per_riga(testo.contesto);

        if(testo.righe < 1 || testo.righe > righe_contesto(testo.contesto))
        {
            return fallisci(ErroreAutotest::RIGHE_FUORI_CONTESTO, t, -1, -1);
        }

        // Tabelle: righe contigue, byte UTF-8, x e larghezze, punti di taglio.
        int prossimo = testo.primo_glifo;
        int byte_precedente = -1;

        for(int r = 0; r < testo.righe; ++r)
        {
            int ir = indice_riga(testo, r);
            const Riga& rg = riga(ir);

            if(rg.primo_glifo != prossimo || rg.glifi < 1)
            {
                return fallisci(ErroreAutotest::RIGHE_NON_CONTIGUE, t, r, -1);
            }

            if(rg.larghezza > larghezza_max)
            {
                return fallisci(ErroreAutotest::RIGA_TROPPO_LARGA, t, r, -1);
            }

            int x = 0;

            for(int g = 0; g < rg.glifi; ++g)
            {
                int ig = rg.primo_glifo + g;
                const stile::Glifo& gl = glifo(glifo_font(ig));
                int b = byte_glifo(ig);

                if(b <= byte_precedente)
                {
                    return fallisci(ErroreAutotest::BYTE_NON_CRESCENTE, t, r, g);
                }

                int codice = decodifica_utf8(testo.utf8, testo.byte, b);

                if(codice < 0)
                {
                    return fallisci(ErroreAutotest::BYTE_NON_CONFINE, t, r, g);
                }

                if(char32_t(codice) != gl.codice)
                {
                    return fallisci(ErroreAutotest::CODICE_DIVERSO, t, r, g);
                }

                if(x_glifo(ig) != x)
                {
                    return fallisci(ErroreAutotest::X_SBAGLIATA, t, r, g);
                }

                byte_precedente = b;
                x += gl.larghezza + stile::FONT_SPAZIATURA;
            }

            if(rg.larghezza != x - stile::FONT_SPAZIATURA)
            {
                return fallisci(ErroreAutotest::LARGHEZZA_SBAGLIATA, t, r, -1);
            }

            for(int k = 0; k < testi::SPRITE_PER_RIGA; ++k)
            {
                int atteso = rg.glifi;

                for(int g = rg.glifi - 1; g >= 0; --g)
                {
                    int ig = rg.primo_glifo + g;

                    if(x_glifo(ig) + glifo(glifo_font(ig)).larghezza > k * testi::LARGHEZZA_SPRITE)
                    {
                        atteso = g;
                    }
                }

                if(taglio(ir, k) != atteso)
                {
                    return fallisci(ErroreAutotest::TAGLIO_SBAGLIATO, t, r, k);
                }
            }

            prossimo += rg.glifi;
        }

        if(prossimo - testo.primo_glifo != testo.glifi)
        {
            return fallisci(ErroreAutotest::GLIFI_NON_TORNANO, t, -1, -1);
        }

        // Disegno a ogni lunghezza di rivelazione: il passo n aggiunge il glifo n-1 a quanto gia'
        // disegnato, con gli sprite accesi come li vedrebbe la vista a quel passo.
        int r = 0;
        int nella_riga = 0;

        for(int n = 1; n <= testo.glifi; ++n)
        {
            int ir = indice_riga(testo, r);

            while(nella_riga == riga(ir).glifi)
            {
                ++r;
                nella_riga = 0;
                ir = indice_riga(testo, r);
            }

            int ig = riga(ir).primo_glifo + nella_riga;
            ++nella_riga;

            int accesi = sprite_accesi(ir, nella_riga);
            bool fuori_contesto = false;
            bool in_sprite_spento = false;

            per_ogni_pixel(glifo(glifo_font(ig)), x_glifo(ig), [&](int px, int) {
                ++esito.pixel;

                if(px >= larghezza_max || px / testi::LARGHEZZA_SPRITE >= sprite_max)
                {
                    fuori_contesto = true;
                }
                else if(px / testi::LARGHEZZA_SPRITE >= accesi)
                {
                    in_sprite_spento = true;
                }
            });

            if(fuori_contesto)
            {
                return fallisci(ErroreAutotest::PIXEL_FUORI_CONTESTO, t, r, n);
            }

            if(in_sprite_spento)
            {
                return fallisci(ErroreAutotest::PIXEL_IN_SPRITE_SPENTO, t, r, n);
            }

            ++esito.passi;
        }
    }

    return esito;
}

}

#endif
