#include "folla_vista.h"

#include "bn_sprite_shape_size.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_tile.h"

#include "esplorazione.h"
#include "mondo_logica.h"

namespace gubbio
{

namespace
{
    using namespace folla;

    constexpr int ALTEZZA_PASSANTE = 31;      // 16x32, i piedi sull'ultima riga
    constexpr int ALTEZZA_ANIMALE = 15;       // 16x16, le zampe sull'ultima riga
    constexpr int DAVANTI = 14;               // pixel: chi ha il giocatore davanti si ferma
    constexpr int SPAVENTO = 22;              // pixel: le galline e gli altri animali scappano
    constexpr int VOLO = 36;                  // pixel: i piccioni volano via
    constexpr int FRAME_VOLO = 48;
    constexpr int FRAME_ASSENZA = 420;        // quanto restano via i piccioni
    constexpr int FRAME_BECCO = 20;           // gli animali fermi: becchettano o muovono la coda

    int distanza(int ax, int ay, int bx, int by)
    {
        int dx = ax - bx;
        int dy = ay - by;
        return (dx < 0 ? -dx : dx) + (dy < 0 ? -dy : dy);
    }

    int lunghezza_di(const Corrente& c)
    {
        int l = 0;

        for(int k = 1; k < c.punti; ++k)
        {
            const Punto& a = GUBBIO_VOCE(PUNTO, c.primo + k - 1);
            const Punto& b = GUBBIO_VOCE(PUNTO, c.primo + k);
            int dx = int(b.tx) - int(a.tx);
            int dy = int(b.ty) - int(a.ty);
            l += ((dx < 0 ? -dx : dx) + (dy < 0 ? -dy : dy)) * mondo::TILE_PX;
        }

        return l;
    }

    // Il punto a 's' pixel dal primo punto, e la direzione del tratto (dx, dy in -1..1).
    void punto_a(const Corrente& c, int s, int& x, int& y, int& dx, int& dy)
    {
        for(int k = 1; k < c.punti; ++k)
        {
            const Punto& a = GUBBIO_VOCE(PUNTO, c.primo + k - 1);
            const Punto& b = GUBBIO_VOCE(PUNTO, c.primo + k);
            int ax = mondo::piedi_x(a.tx);
            int ay = mondo::piedi_y(a.ty);
            int bx = mondo::piedi_x(b.tx);
            int by = mondo::piedi_y(b.ty);
            int l = (bx > ax ? bx - ax : ax - bx) + (by > ay ? by - ay : ay - by);
            dx = bx > ax ? 1 : (bx < ax ? -1 : 0);
            dy = by > ay ? 1 : (by < ay ? -1 : 0);

            if(s <= l || k == c.punti - 1)
            {
                int t = s < l ? s : l;
                x = ax + dx * t;
                y = ay + dy * t;
                return;
            }

            s -= l;
        }

        const Punto& p = GUBBIO_VOCE(PUNTO, c.primo);
        x = mondo::piedi_x(p.tx);
        y = mondo::piedi_y(p.ty);
        dx = dy = 0;
    }
}

void Folla::_carica(Viandante& v, int fotogramma)
{
    if(v.caricato == fotogramma)
    {
        return;
    }

    v.caricato = uint8_t(fotogramma);
    const Corrente& c = GUBBIO_VOCE(CORRENTE, v.corrente);
    bn::sprite_tiles_ptr tiles = v.sprite.tiles();
    bn::span<bn::tile> vram = *tiles.vram();

    if(c.animale)
    {
        for(int t = 0; t < 4; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(GUBBIO_VOCE(FIGURA_ANIMALE, c.figura), fotogramma * 32 + t * 8 + r);
            }
        }
    }
    else
    {
        for(int t = 0; t < 8; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(GUBBIO_VOCE(FIGURA_PASSANTE, c.figura), fotogramma * 64 + t * 8 + r);
            }
        }
    }
}

void Folla::prepara(int area, int fase, const Esplorazione& esplorazione, const bn::sprite_palette_ptr& gente)
{
    _v.clear();

    for(int k = 0; k < CORRENTI; ++k)
    {
        const Corrente& c = GUBBIO_VOCE(CORRENTE, k);

        if(c.area != area || !((c.fasi >> fase) & 1))
        {
            continue;
        }

        int lunghezza = lunghezza_di(c);

        for(int q = 0; q < c.quanti && !_v.full(); ++q)
        {
            int tile = c.animale ? 4 : 8;
            bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(tile, bn::bpp_mode::BPP_4);
            bn::sprite_ptr sprite = bn::sprite_ptr::create(
                0, 0, c.animale ? bn::sprite_shape_size(16, 16) : bn::sprite_shape_size(16, 32), bn::move(tiles), gente);
            Viandante v{ bn::move(sprite), lunghezza, lunghezza * q / c.quanti + (c.animale ? q * 5 : 0) % (lunghezza + 1),
                         (q % 2) ? -1 : 1, 0, 0, 0, 0, 0, 0, uint8_t(k), 255, 0, uint8_t(_v.size()) };
            _v.push_back(bn::move(v));
        }
    }

    aggiorna(esplorazione, -1000, -1000, 0);       // tutti al loro posto prima del primo frame
}

void Folla::aggiorna(const Esplorazione& esplorazione, int px, int py, int frame)
{
    for(Viandante& v : _v)
    {
        const Corrente& c = GUBBIO_VOCE(CORRENTE, v.corrente);
        bool piccione = c.animale && c.figura == ANIMALE_PICCIONE;

        // il piccione in volo: su e di lato, poi via per un po'; torna dove si era alzato
        if(v.volo > 0)
        {
            --v.volo;
            v.vy -= 2;
            v.vx += v.verso * 2;
            _carica(v, 1);
            v.sprite.set_visible(v.volo > 0);

            if(v.volo == 0)
            {
                v.volo = -FRAME_ASSENZA - v.indice * 31;
            }

            esplorazione.colloca_sulla_mappa(v.sprite, v.x + v.vx, v.y + v.vy, ALTEZZA_ANIMALE);
            continue;
        }

        if(v.volo < 0)
        {
            if(++v.volo == 0)
            {
                v.vx = v.vy = 0;
                v.sprite.set_visible(true);
            }

            continue;
        }

        int dx = 0;
        int dy = 0;
        punto_a(c, v.s, v.x, v.y, dx, dy);
        int vicino = distanza(px, py, v.x, v.y);
        bool muove = false;

        if(piccione && vicino < VOLO)
        {
            v.volo = FRAME_VOLO;
            v.verso = px < v.x ? 1 : -1;
            v.sprite.set_horizontal_flip(v.verso < 0);
            continue;
        }

        if(v.pausa > 0)
        {
            --v.pausa;

            if(c.sparisce)
            {
                v.sprite.set_visible(v.pausa == 0);
            }
        }
        else if(c.animale && vicino < SPAVENTO)
        {
            // scappa: dalla parte opposta al giocatore, il doppio piu' svelto
            int ax, ay, adx, ady;
            punto_a(c, v.s + v.verso, ax, ay, adx, ady);

            if(distanza(px, py, ax, ay) < vicino)
            {
                v.verso = -v.verso;
            }

            muove = true;
        }
        else if(!c.animale && vicino < DAVANTI)
        {
            // il giocatore gli sta davanti: aspetta
        }
        else
        {
            muove = frame % c.lentezza == 0;
        }

        if(muove)
        {
            v.s += v.verso;
            ++v.passi;

            if(v.s <= 0 || v.s >= v.lunghezza)
            {
                v.s = v.s <= 0 ? 0 : v.lunghezza;
                v.verso = -v.verso;
                v.pausa = (c.animale ? 40 : 70) + (v.indice * 53 + frame) % 110;

                if(c.sparisce)
                {
                    v.sprite.set_visible(false);
                }
            }

            punto_a(c, v.s, v.x, v.y, dx, dy);
        }

        // la direzione di chi cammina e' quella del tratto, nel verso in cui va
        dx *= v.verso;
        dy *= v.verso;

        if(c.animale)
        {
            if(dx)
            {
                v.sprite.set_horizontal_flip(dx < 0);
            }

            // in cammino un passo ogni 6 pixel; fermi becchettano
            int f = muove ? (v.passi / 6) % 2 : (v.pausa > 0 ? ((frame + v.indice * 7) / FRAME_BECCO) % 2 : 0);
            _carica(v, f);
            esplorazione.colloca_sulla_mappa(v.sprite, v.x, v.y, ALTEZZA_ANIMALE);
        }
        else
        {
            int direzione = dx ? DIREZIONE_DESTRA : (dy < 0 ? DIREZIONE_SU : DIREZIONE_GIU);
            v.sprite.set_horizontal_flip(dx < 0);
            int f = muove || (v.pausa == 0 && vicino >= DAVANTI) ? (v.passi / PIXEL_PER_PASSO) % FOTOGRAMMI_PASSO : 0;
            _carica(v, direzione * FOTOGRAMMI_PASSO + f);
            esplorazione.colloca_sulla_mappa(v.sprite, v.x, v.y, ALTEZZA_PASSANTE);
        }

        // chi e' piu' in basso sullo schermo sta davanti a chi e' piu' in alto
        v.sprite.set_z_order(2000 - v.y / 2);
    }
}

}
