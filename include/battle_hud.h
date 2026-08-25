#ifndef BATTLE_HUD_H
#define BATTLE_HUD_H

#include "bn_vector.h"
#include "bn_optional.h"
#include "bn_sprite_ptr.h"
#include "bn_regular_bg_ptr.h"
#include "bn_sprite_text_generator.h"

#include "battle_animator.h"
#include "battle_scene.h"

namespace gubbio {

// Rendering della schermata di combattimento (layout della Sezione 14B.3 GDD).
//
//   +-------------------------------------------------------------+
//   | fondale d'assedio: Monte Ingino, nebbia                     |
//   |  [NEMICI x:40-90]                     [PARTY x:150-200]     |
//   +-------------------------------------------------------------+
//   | HUD 48px:  [MENU COMANDI 80px] | [STATO PARTY 160px]        |
//   +-------------------------------------------------------------+
//
// Il pannello HUD e' dipinto nelle righe 112-159 del fondale invece che su un layer separato:
// la scena e' statica e questo risparmia un BG hardware per il futuro parallasse.
//
// --- LE DUE CADENZE (Passo 21 del piano) ------------------------------------------------------
//
// `update()` fa due lavori con due ritmi diversi, e tenerli distinti e' il punto del passo:
//
//   * `_tick_animations()` gira A OGNI FRAME. E' il moto: l'animatore, il flash, l'affondo, e
//     l'avanzamento del cursore del registro degli eventi. Non alloca nulla.
//   * `_refresh()` gira SOLO al cambio di `_signature()`. E' la composizione: testi, barre,
//     gettoni della timeline, cursore bersaglio. Ogni sua riga puo' toccare l'allocatore dei
//     tile OBJ, ed e' per questo che non deve girare a ogni frame.
//
// --- DA DOVE VENGONO GLI HP DISEGNATI ---------------------------------------------------------
//
// NON dal modello. Quando il round e' in riproduzione (stato PLAY_ROUND_ANIMATIONS) il modello
// contiene gia' l'esito FINALE del round: disegnarlo farebbe scendere la barra prima
// dell'animazione che dovrebbe causarla — il difetto che il Passo 20 esiste per chiudere. Le
// barre sono quindi alimentate da `hp_after` dell'ULTIMO EVENTO GIA' RIPRODOTTO (`_hp_mostrati`),
// e da `_hp_inizio_round` per chi in quel round non e' ancora stato toccato.
class BattleHud
{
public:
    BattleHud();

    // Costruisce sprite e testi dallo stato corrente. Chiamare a ogni frame: internamente
    // ridisegna solo quando lo stato osservabile cambia.
    void update(const BattleSceneManager& battle);

private:
    static constexpr int UNIT_COUNT = PARTY_SIZE + MAX_ENEMIES_PER_ENCOUNTER;

    // I testi non stanno piu' in un vettore solo. Rigenerare tutto a ogni cambio di firma
    // significava fino a 40 allocazioni di tile in un frame su un tetto di 128 item
    // (BN_CFG_SPRITE_TILES_MAX_ITEMS) condiviso con l'etichetta del nome area
    // dell'esplorazione: qui ogni gruppo ha la propria sotto-firma e si rigenera da solo.
    static constexpr int MAX_MENU_SPRITES   = 24;   // 4 righe di comando, con boost
    static constexpr int MAX_NAME_SPRITES   = 24;   // 3 nomi abbreviati, col marcatore
    static constexpr int MAX_NUMBER_SPRITES = 4;    // gli HP correnti di UN Cero

    bn::regular_bg_ptr _background;
    bn::sprite_text_generator _text_generator;
    BattleAnimator _animator;

    bn::vector<bn::sprite_ptr, PARTY_SIZE> _hero_sprites;
    bn::vector<bn::sprite_ptr, MAX_ENEMIES_PER_ENCOUNTER> _enemy_sprites;
    bn::vector<bn::sprite_ptr, PARTY_SIZE * 2> _bars;      // HP e Fervore per ogni Cero
    bn::optional<bn::sprite_ptr> _cursor;
    bn::vector<bn::sprite_ptr, UNIT_COUNT> _timeline;

    bn::vector<bn::sprite_ptr, MAX_MENU_SPRITES> _menu_texts;
    bn::vector<bn::sprite_ptr, MAX_NAME_SPRITES> _name_texts;
    bn::vector<bn::sprite_ptr, MAX_NUMBER_SPRITES> _hp_texts[PARTY_SIZE];

    int _last_signature;
    int _last_menu_signature;
    int _last_name_signature;
    int _last_intro_progress;
    int _last_event_cursor;

    // Cache di cio' che e' gia' su schermo: un `set_item` che non cambia nulla e' comunque una
    // release e una create sull'allocatore dei tile.
    int _bar_frames[PARTY_SIZE * 2];
    int _timeline_frames[UNIT_COUNT];
    int _hp_numbers[PARTY_SIZE];

    // Gli HP come li vede il GIOCATORE, non come li sa il modello. Indice: gli eroi occupano
    // 0..PARTY_SIZE-1, i nemici seguono (vedi `_unit_index`).
    int _hp_mostrati[UNIT_COUNT];
    int _hp_inizio_round[UNIT_COUNT];

    // Chi e' gia' caduto AGLI OCCHI DEL GIOCATORE. Non coincide con "HP a zero": fra il colpo
    // che azzera gli HP e la fine dell'animazione di sconfitta l'unita' deve restare in campo,
    // altrimenti sparisce nell'istante in cui comincia la posa che la mostra cadere.
    bool _abbattuto[UNIT_COUNT];

    bool _units_built;
    bool _fade_globale_azzerato;

    void _build_units(const BattleSceneManager& battle);
    void _tick_animations(const BattleSceneManager& battle);
    void _refresh(const BattleSceneManager& battle);
    void _refresh_menu(const BattleSceneManager& battle);
    void _refresh_status(const BattleSceneManager& battle);
    void _refresh_timeline(const BattleSceneManager& battle);
    void _refresh_cursor(const BattleSceneManager& battle);
    void _apply_intro_fade(const BattleSceneManager& battle);

    // Ricalcola `_hp_mostrati` scorrendo gli eventi gia' riprodotti. Costa quanto il cursore, e
    // viene chiamata solo quando il cursore si muove.
    void _aggiorna_hp_riprodotti(const BattleSceneManager& battle);
    [[nodiscard]] AnimSubject _soggetto(const BattleSceneManager& battle, bool is_enemy, int slot) const;

    [[nodiscard]] static int _unit_index(bool is_enemy, int slot)
    {
        return is_enemy ? PARTY_SIZE + slot : slot;
    }

    [[nodiscard]] int _signature(const BattleSceneManager& battle) const;
};

} // namespace gubbio

#endif // BATTLE_HUD_H
