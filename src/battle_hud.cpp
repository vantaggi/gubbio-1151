#include "battle_hud.h"

#include "bn_string.h"
#include "bn_display.h"

#include "bn_regular_bg_items_battle_bg.h"
#include "bn_sprite_items_ubaldo.h"
#include "bn_sprite_items_giorgio.h"
#include "bn_sprite_items_antonio.h"
#include "bn_sprite_items_enemy_fante.h"
#include "bn_sprite_items_enemy_balestriere.h"
#include "bn_sprite_items_enemy_corrado.h"
#include "bn_sprite_items_hud_bar.h"
#include "bn_sprite_items_target_cursor.h"
#include "bn_sprite_items_timeline_icons.h"
#include "scene_fade.h"

#include "font_gubbio.h"

namespace gubbio {

namespace {

// Coordinate della Sezione 14B.3 GDD, convertite dal sistema a origine in alto a sinistra
// (0-239 / 0-159) a quello centrato di Butano (-120..119 / -80..79).
[[nodiscard]] constexpr int sx(int screen_x) { return screen_x - 120; }
[[nodiscard]] constexpr int sy(int screen_y) { return screen_y - 80; }

// Party a destra (x 150-200), schieramento nemico a sinistra (x 40-90).
constexpr int HERO_X[PARTY_SIZE]  = {196, 162, 218};   // Ubaldo, Giorgio, Antonio
constexpr int HERO_Y[PARTY_SIZE]  = { 86,  94,  94};   // i piedi poggiano sulla fascia di terreno
// Formazione 3x2 (Sez. 12 GDD): prima riga in avanguardia, seconda in retrovia.
constexpr int ENEMY_X[MAX_ENEMIES_PER_ENCOUNTER] = {60, 94, 44, 78, 112, 28};
constexpr int ENEMY_Y[MAX_ENEMIES_PER_ENCOUNTER] = {96, 96, 78, 78,  78, 96};

// Timeline degli ordini in alto a destra (Sez. 20A GDD, pilastro 1).
constexpr int TIMELINE_X = 228;
constexpr int TIMELINE_Y = 12;
constexpr int TIMELINE_STEP = 15;

// I fotogrammi delle barre non sono piu' scritti a mano qui: vengono dalla tabella generata
// insieme ai .bmp (battle_anim_table.h). E' la duplicazione dichiarata nella Sessione 05 —
// le stesse costanti ricopiate in questo file e in tools/preview_battle_screen.py — che il
// Passo 19 ha chiuso alla sorgente.
constexpr int BAR_FRAMES = HUD_BAR_FRAMES;
constexpr int BAR_FERVOR_OFFSET = HUD_BAR_FERVOR_OFFSET;

// Riquadro del menu comandi: 80px a sinistra dell'HUD (Sezione 14B.3 GDD).
constexpr int MENU_X = 8;
constexpr int MENU_Y = 118;
constexpr int MENU_LINE = 10;

// Riquadro di stato del party: i restanti 160px.
constexpr int STATUS_X = 84;
constexpr int STATUS_Y = 118;
constexpr int STATUS_LINE = 12;
constexpr int NUMBERS_X = 133;   // solo HP correnti: la frazione la dice la barra
constexpr int BAR_HP_X = 157;
constexpr int BAR_FER_X = 193;

// Nomi abbreviati: la fascia di stato e' larga 157px e deve ospitare nome, HP e due barre.
constexpr const char* HERO_SHORT_NAME[PARTY_SIZE] = {"Ubaldo", "Giorgio", "Antonio"};

// Gli indici del party sono anche gli indici degli attori animati: `_soggetto()` costruisce un
// AnimActor direttamente dallo slot dell'eroe, e la timeline pesca il proprio gettone dallo
// stesso numero. Se i due elenchi divergessero, Sant'Ubaldo attaccherebbe con la posa di San
// Giorgio e il gettone mostrerebbe il terzo.
static_assert(PARTY_UBALDO  == int(AnimActor::UBALDO) &&
              PARTY_GIORGIO == int(AnimActor::GIORGIO) &&
              PARTY_ANTONIO == int(AnimActor::ANTONIO),
              "l'ordine del party e quello degli attori animati non coincidono piu': pose e "
              "gettoni della timeline finirebbero sull'eroe sbagliato");
static_assert(TIMELINE_ICON_COUNT == ANIM_ACTOR_COUNT,
              "il foglio dei gettoni non ha un fotogramma per attore: la timeline pescherebbe "
              "un indice fuori dal foglio");

[[nodiscard]] const char* command_label(MenuCommand command)
{
    switch(command)
    {
        case MenuCommand::ATTACK: return "Attacca";
        case MenuCommand::SKILL:  return "Abilità";
        case MenuCommand::ITEM:   return "Oggetti";
        case MenuCommand::FLEE:   return "Fuga";
        default:                  return "";
    }
}

// UN SOLO punto in cui il nome di un nemico diventa la sua identita' grafica. Prima erano due
// (lo sprite e il gettone della timeline) e con l'animatore sarebbero diventati tre: tre elenchi
// di nomi da tenere allineati a mano, cioe' il modo piu' facile per far comparire un Balestriere
// che si muove come un Fante.
[[nodiscard]] AnimActor anim_actor_for(const BattleUnit& unit, int slot)
{
    if(! unit.is_enemy)
    {
        return AnimActor(slot);
    }

    if(unit.name == bn::string_view("Corrado di Spoleto"))
    {
        return AnimActor::ENEMY_CORRADO;
    }

    return unit.name == bn::string_view("Balestriere Pesante") ? AnimActor::ENEMY_BALESTRIERE
                                                               : AnimActor::ENEMY_FANTE;
}

[[nodiscard]] const bn::sprite_item& sprite_item_for(AnimActor kind)
{
    switch(kind)
    {
        case AnimActor::UBALDO:            return bn::sprite_items::ubaldo;
        case AnimActor::GIORGIO:           return bn::sprite_items::giorgio;
        case AnimActor::ANTONIO:           return bn::sprite_items::antonio;
        case AnimActor::ENEMY_BALESTRIERE: return bn::sprite_items::enemy_balestriere;
        case AnimActor::ENEMY_CORRADO:     return bn::sprite_items::enemy_corrado;
        default:                           break;
    }

    // Il Fante e' anche il ripiego: e' l'unico nemico che ogni incontro puo' contenere, quindi
    // un attore ignoto si vede come un Fante invece di lasciare il campo vuoto.
    return bn::sprite_items::enemy_fante;
}

[[nodiscard]] int bar_frame(int current, int maximum)
{
    if(maximum <= 0)
    {
        return 0;
    }

    const int frame = (current * (BAR_FRAMES - 1)) / maximum;
    return frame < 0 ? 0 : (frame > BAR_FRAMES - 1 ? BAR_FRAMES - 1 : frame);
}

} // namespace

BattleHud::BattleHud() :
    _background(bn::regular_bg_items::battle_bg.create_bg(0, 0)),
    _text_generator(FONT_GUBBIO),
    _last_signature(0),
    _last_menu_signature(-1),
    // -2 e non -1: la sotto-firma dei nomi E' l'indice dell'eroe attivo, che vale -1 fuori
    // dalle fasi di input. Con -1 la prima schermata di battaglia sarebbe nata senza nomi.
    _last_name_signature(-2),
    _last_intro_progress(-1),
    _last_event_cursor(-1),
    _units_built(false),
    _fade_globale_azzerato(false)
{
    _text_generator.set_left_alignment();
    _text_generator.set_bg_priority(0);

    for(int i = 0; i < PARTY_SIZE * 2; ++i)
    {
        _bar_frames[i] = -1;
    }

    for(int i = 0; i < UNIT_COUNT; ++i)
    {
        _timeline_frames[i] = -1;
        _hp_mostrati[i] = 0;
        _hp_inizio_round[i] = 0;
        _abbattuto[i] = false;
    }

    for(int i = 0; i < PARTY_SIZE; ++i)
    {
        _hp_numbers[i] = -1;
    }
}

void BattleHud::update(const BattleSceneManager& battle)
{
    if(! _units_built)
    {
        _build_units(battle);
        _units_built = true;
        _last_signature = _signature(battle) - 1;
    }

    _apply_intro_fade(battle);

    // L'ORDINE FRA LE DUE CADENZE NON E' LIBERO. `_tick_animations()` e' cio' che aggiorna
    // `_hp_mostrati`, e `_signature()` legge proprio quelli: invertendo, la firma descriverebbe
    // il fotogramma precedente e le barre resterebbero indietro di un frame per tutto il round.
    _tick_animations(battle);

    if(const int signature = _signature(battle); signature != _last_signature)
    {
        _last_signature = signature;
        _refresh(battle);
    }
}

// La scena emerge dal nero: e' lo stato INTRO_FADE_IN della Sez. 20B GDD, che finora
// transitava in un solo frame senza che si vedesse nulla.
void BattleHud::_apply_intro_fade(const BattleSceneManager& battle)
{
    const int progress = battle.intro_progress();

    if(progress == _last_intro_progress)
    {
        return;
    }

    _last_intro_progress = progress;

    // La dissolvenza passa dalle primitive di `scene_fade` (Passo 5): la FSM resta padrona del
    // tempo — l'avanzamento e' ancora `intro_progress()` — ma il tocco alle palette globali
    // avviene in un punto solo, lo stesso che le scene azzerano uscendo.
    scene_fade::apply(scene_fade::OPAQUE - progress);
}

// --- PRIMA CADENZA: ogni frame -----------------------------------------------------------------
//
// Qui non si alloca nulla e non si crea nessuno sprite. Si muove cio' che esiste gia'.
void BattleHud::_tick_animations(const BattleSceneManager& battle)
{
    const bool in_riproduzione = battle.state() == BattleState::PLAY_ROUND_ANIMATIONS;

    // PRIMA DI QUALUNQUE FLASH: il fade globale degli sprite va azzerato, perche' il banco delle
    // palette di Butano applica il fade globale e quello per-palette IN SEQUENZA sugli stessi
    // colori. Un residuo del primo non verrebbe sostituito dal flash bianco: si sommerebbe.
    // Non lo si azzera a ogni frame perche' cancellerebbe la dissolvenza d'ingresso, che usa
    // esattamente lo stesso registro per i 32 frame dello stato INTRO_FADE_IN.
    if(in_riproduzione && ! _fade_globale_azzerato)
    {
        _animator.begin_round();
        _fade_globale_azzerato = true;
    }

    if(! in_riproduzione)
    {
        // Fuori dalla riproduzione il modello E' cio' che si vede, e il round successivo parte
        // da qui: `_hp_inizio_round` e' il valore da cui le barre scenderanno colpo per colpo.
        //
        // PERCHE' QUESTA ISTANTANEA E' PRESA IN TEMPO. Lo stato EXECUTE_ROUND_ACTIONS occupa un
        // frame in cui il round NON e' ancora stato risolto: `_handle_command_input` si limita a
        // impostare lo stato, e la risoluzione avviene all'`update()` successivo. L'HUD vede
        // quindi sempre almeno un frame con gli HP di INIZIO round, ed e' quello che qui viene
        // congelato. Se un domani EXECUTE risolvesse il round nello stesso frame in cui vi si
        // entra, l'istantanea conterrebbe gia' l'esito e le barre tornerebbero a scendere prima
        // del colpo.
        _animator.end();
        _fade_globale_azzerato = false;
        _last_event_cursor = -1;

        for(int hero = 0; hero < PARTY_SIZE; ++hero)
        {
            const BattleUnit& unit = battle.party()[hero];
            _hp_mostrati[hero] = unit.current_hp;
            _hp_inizio_round[hero] = unit.current_hp;
            _abbattuto[hero] = ! unit.is_alive();
        }

        for(int slot = 0, count = battle.enemies().size(); slot < count; ++slot)
        {
            const BattleUnit& unit = battle.enemies()[slot];
            const int indice = _unit_index(true, slot);
            _hp_mostrati[indice] = unit.current_hp;
            _hp_inizio_round[indice] = unit.current_hp;
            _abbattuto[indice] = ! unit.is_alive();
        }

        return;
    }

    if(const int cursore = battle.event_cursor(); cursore != _last_event_cursor)
    {
        _last_event_cursor = cursore;
        _aggiorna_hp_riprodotti(battle);

        if(cursore < battle.events().size())
        {
            const BattleEvent& evento = battle.events()[cursore];
            _animator.begin(evento,
                            _soggetto(battle, evento.actor_is_enemy, evento.actor_slot),
                            _soggetto(battle, evento.target_is_enemy, evento.target_slot));
        }
        else
        {
            _animator.end();
        }
    }

    // Il fast-forward NON e' reimplementato qui: e' gia' della FSM, che con A o B tenuti consuma
    // quattro frame di registro per frame di gioco. L'animatore si limita a rispettarlo, cosi'
    // le pose si comprimono insieme al temporizzatore invece di scorrere a velocita' diversa.
    _animator.tick(passo_riproduzione());
}

// Gli HP come li ha visti il giocatore: si riparte da quelli d'inizio round e si applicano SOLO
// gli eventi gia' riprodotti, cioe' quelli prima del cursore. L'evento sul cursore e' quello in
// corso e non ha ancora "colpito": e' la ragione per cui un caduto resta visibile per tutta la
// sua animazione di sconfitta e sparisce solo quando quella finisce.
void BattleHud::_aggiorna_hp_riprodotti(const BattleSceneManager& battle)
{
    for(int i = 0; i < UNIT_COUNT; ++i)
    {
        _hp_mostrati[i] = _hp_inizio_round[i];

        // NON `false`: chi era gia' a terra all'inizio del round deve restarci. Azzerando la
        // bandiera per tutti, un nemico ucciso al round 1 sarebbe RIAPPARSO in campo per tutta
        // la riproduzione del round 2, per poi sparire di nuovo alla fine.
        _abbattuto[i] = _hp_inizio_round[i] <= 0;
    }

    const auto& eventi = battle.events();
    const int fine = battle.event_cursor() < eventi.size() ? battle.event_cursor() : eventi.size();

    for(int i = 0; i < fine; ++i)
    {
        const BattleEvent& evento = eventi[i];
        const int indice = _unit_index(evento.target_is_enemy, evento.target_slot);

        if(indice < 0 || indice >= UNIT_COUNT)
        {
            continue;
        }

        _hp_mostrati[indice] = evento.hp_after;

        if(evento.kind == EventKind::DEFEAT)
        {
            _abbattuto[indice] = true;
        }
    }
}

AnimSubject BattleHud::_soggetto(const BattleSceneManager& battle, bool is_enemy, int slot) const
{
    if(is_enemy)
    {
        const int reale = (slot >= 0 && slot < _enemy_sprites.size()) ? slot : 0;
        const AnimActor kind = anim_actor_for(battle.enemies()[reale], reale);
        return AnimSubject{_enemy_sprites[reale], &sprite_item_for(kind), kind,
                           sx(ENEMY_X[reale]), sy(ENEMY_Y[reale])};
    }

    const int reale = (slot >= 0 && slot < PARTY_SIZE) ? slot : 0;
    const AnimActor kind = AnimActor(reale);
    return AnimSubject{_hero_sprites[reale], &sprite_item_for(kind), kind,
                       sx(HERO_X[reale]), sy(HERO_Y[reale])};
}

void BattleHud::_build_units(const BattleSceneManager& battle)
{
    _hero_sprites.push_back(bn::sprite_items::ubaldo.create_sprite(
        sx(HERO_X[PARTY_UBALDO]), sy(HERO_Y[PARTY_UBALDO])));
    _hero_sprites.push_back(bn::sprite_items::giorgio.create_sprite(
        sx(HERO_X[PARTY_GIORGIO]), sy(HERO_Y[PARTY_GIORGIO])));
    _hero_sprites.push_back(bn::sprite_items::antonio.create_sprite(
        sx(HERO_X[PARTY_ANTONIO]), sy(HERO_Y[PARTY_ANTONIO])));

    for(int slot = 0, count = battle.enemies().size(); slot < count; ++slot)
    {
        const AnimActor kind = anim_actor_for(battle.enemies()[slot], slot);
        _enemy_sprites.push_back(sprite_item_for(kind).create_sprite(
            sx(ENEMY_X[slot]), sy(ENEMY_Y[slot])));
    }

    // Due barre per Cero: HP e Fervore, allineate alle righe di stato.
    for(int hero = 0; hero < PARTY_SIZE; ++hero)
    {
        const int y = sy(STATUS_Y + hero * STATUS_LINE + 3);
        _bars.push_back(bn::sprite_items::hud_bar.create_sprite(sx(BAR_HP_X + 16), y));
        _bars.push_back(bn::sprite_items::hud_bar.create_sprite(sx(BAR_FER_X + 16), y));
    }

    _cursor = bn::sprite_items::target_cursor.create_sprite(0, 0);
}

// --- SECONDA CADENZA: solo al cambio di firma --------------------------------------------------
//
// Ogni riga di qui sotto puo' toccare l'allocatore dei tile OBJ. Nessuno dei quattro blocchi
// rigenera cio' che non e' cambiato: la regola e' la stessa del dialogo (dialogue_view.h), e la
// ragione e' la stessa — il tetto vero non sono i tile ma le 128 allocazioni di
// BN_CFG_SPRITE_TILES_MAX_ITEMS, condivise con il resto del gioco.
void BattleHud::_refresh(const BattleSceneManager& battle)
{
    // --- Sprite delle unita': i caduti spariscono dal campo, ma solo dopo la loro animazione ---
    for(int hero = 0; hero < PARTY_SIZE; ++hero)
    {
        _hero_sprites[hero].set_visible(! _abbattuto[hero]);
    }

    for(int slot = 0, count = _enemy_sprites.size(); slot < count; ++slot)
    {
        _enemy_sprites[slot].set_visible(! _abbattuto[_unit_index(true, slot)]);
    }

    _refresh_menu(battle);
    _refresh_status(battle);
    _refresh_timeline(battle);
    _refresh_cursor(battle);
}

// Menu comandi (riquadro sinistro, 80px). Cambia solo con l'eroe attivo, il comando e il Boost:
// durante la riproduzione delle animazioni, che e' quando la firma cambia piu' spesso, questo
// blocco non tocca l'allocatore nemmeno una volta.
void BattleHud::_refresh_menu(const BattleSceneManager& battle)
{
    const int active_hero = battle.active_hero_index();
    const int firma = (active_hero + 1) * 64 + int(battle.selected_command()) * 8 +
                      battle.boost_level();

    if(firma == _last_menu_signature)
    {
        return;
    }

    _last_menu_signature = firma;
    _menu_texts.clear();

    for(int i = 0; i < int(MenuCommand::COUNT); ++i)
    {
        const bool selected = active_hero >= 0 && i == int(battle.selected_command());
        bn::string<20> line;
        bn::ostringstream stream(line);
        stream << (selected ? "> " : "  ") << command_label(MenuCommand(i));

        if(selected && battle.boost_level() > 0)
        {
            stream << (battle.boost_level() == BOOST_MAX_LEVEL ? " MAX" : " x");

            if(battle.boost_level() != BOOST_MAX_LEVEL)
            {
                stream << battle.boost_level();
            }
        }

        _text_generator.generate(sx(MENU_X), sy(MENU_Y + i * MENU_LINE), line, _menu_texts);
    }
}

// Stato del party (riquadro destro, 160px). Tre gruppi con tre ritmi diversi: i nomi cambiano
// solo quando cambia l'eroe attivo, i numeri solo quando cambiano gli HP di QUEL Cero, e le
// barre solo quando cambia il loro fotogramma.
void BattleHud::_refresh_status(const BattleSceneManager& battle)
{
    const int active_hero = battle.active_hero_index();

    if(active_hero != _last_name_signature)
    {
        _last_name_signature = active_hero;
        _name_texts.clear();

        for(int hero = 0; hero < PARTY_SIZE; ++hero)
        {
            bn::string<20> line;
            bn::ostringstream stream(line);
            stream << (hero == active_hero ? ">" : " ") << HERO_SHORT_NAME[hero];
            _text_generator.generate(sx(STATUS_X), sy(STATUS_Y + hero * STATUS_LINE), line,
                                     _name_texts);
        }
    }

    for(int hero = 0; hero < PARTY_SIZE; ++hero)
    {
        const BattleUnit& unit = battle.party()[hero];
        const int hp = _hp_mostrati[hero];

        if(hp != _hp_numbers[hero])
        {
            _hp_numbers[hero] = hp;
            _hp_texts[hero].clear();

            bn::string<12> numbers;
            bn::ostringstream numbers_stream(numbers);
            numbers_stream << hp;
            _text_generator.generate(sx(NUMBERS_X), sy(STATUS_Y + hero * STATUS_LINE), numbers,
                                     _hp_texts[hero]);
        }

        // La barra HP segue cio' che si e' visto accadere; quella del Fervore segue il modello,
        // perche' il registro degli eventi porta gli HP del bersaglio e non il suo Fervore. Il
        // giorno in cui BattleEvent guadagnasse un `fervor_after`, questa riga cambia da sola.
        const int frame_hp = bar_frame(hp, unit.max_hp);
        const int frame_fervore = BAR_FERVOR_OFFSET + bar_frame(unit.current_fervor, unit.max_fervor);

        if(frame_hp != _bar_frames[hero * 2])
        {
            _bar_frames[hero * 2] = frame_hp;
            _bars[hero * 2].set_item(bn::sprite_items::hud_bar, frame_hp);
        }

        if(frame_fervore != _bar_frames[hero * 2 + 1])
        {
            _bar_frames[hero * 2 + 1] = frame_fervore;
            _bars[hero * 2 + 1].set_item(bn::sprite_items::hud_bar, frame_fervore);
        }
    }
}

void BattleHud::_refresh_timeline(const BattleSceneManager& battle)
{
    BattleSceneManager::OrderQueue order;
    battle.predicted_order(order);

    while(_timeline.size() > order.size())
    {
        _timeline.pop_back();
    }

    for(int i = 0; i < order.size(); ++i)
    {
        const UnitRef ref = order[i];
        const BattleUnit& unit = ref.is_enemy ? battle.enemies()[ref.slot] : battle.party()[ref.slot];
        const int frame = int(anim_actor_for(unit, ref.slot));
        const int y = sy(TIMELINE_Y + i * TIMELINE_STEP);

        if(i < _timeline.size())
        {
            // `set_item` e' una release piu' una create sull'allocatore: si chiama solo se il
            // gettone e' davvero cambiato, altrimenti nove allocazioni a ogni cambio di firma.
            if(frame != _timeline_frames[i])
            {
                _timeline_frames[i] = frame;
                _timeline[i].set_item(bn::sprite_items::timeline_icons, frame);
            }

            _timeline[i].set_position(sx(TIMELINE_X), y);
        }
        else
        {
            _timeline_frames[i] = frame;
            _timeline.push_back(bn::sprite_items::timeline_icons.create_sprite(
                sx(TIMELINE_X), y, frame));
        }
    }
}

void BattleHud::_refresh_cursor(const BattleSceneManager& battle)
{
    const UnitRef target = battle.selected_target();
    const bool show_cursor = battle.active_hero_index() >= 0 && target.is_enemy &&
                             target.slot < _enemy_sprites.size() &&
                             ! _abbattuto[_unit_index(true, target.slot)];

    if(_cursor)
    {
        _cursor->set_visible(show_cursor);

        if(show_cursor)
        {
            _cursor->set_position(sx(ENEMY_X[target.slot]), sy(ENEMY_Y[target.slot] - 28));
        }
    }
}

// L'INVARIANTE DELLA FIRMA. Da scrivere per iscritto perche' e' gia' stato un difetto ad alta
// gravita': nella Sessione 07D la firma ignorava `is_enemy` del bersaglio, e passando da Muro
// della Fede (alleato, slot 0) a Giudizio della Verga (nemico, slot 0) cambiava il LATO del
// bersaglio ma non il suo indice. La firma non cambiava, `_refresh()` non girava, e il cursore
// bersaglio restava nascosto — al primo scontro del gioco.
//
// La regola generale che ne discende: la firma deve contenere OGNI COSA CHE SI DISEGNA. Se un
// giorno l'HUD mostrera' un dato nuovo, quel dato entra qui nello stesso momento, non dopo.
// I campi, uno per riga qui sotto:
//
//   1. stato della FSM;
//   2. numero del round;
//   3. indice dell'eroe attivo (e' il marcatore ">" del menu e dei nomi);
//   4. comando selezionato;
//   5. indice di abilita' selezionata — non e' ancora disegnato da nessuna parte, ed e' qui
//      apposta: il tasto L lo fa scorrere gia' oggi, quindi il giorno in cui il nome
//      dell'abilita' comparira' nel menu la firma lo sta gia' seguendo;
//   6. livello di Boost;
//   7. LATO del bersaglio (`is_enemy`) — il campo della Sessione 07D;
//   8. slot del bersaglio;
//   9. cursore del registro degli eventi: e' cio' che fa avanzare le barre durante la
//      riproduzione, perche' gli HP mostrati sono funzione di quanti eventi sono gia' passati;
//  10. HP MOSTRATI e stato di abbattimento di tutte le unita' (non gli HP del modello: vedi la
//      nota in cima a battle_hud.h);
//  11. Fervore e barriera dei tre Ceri;
//  12. scudo e turni di BREAK di tutti i nemici.
//
// Il miscelamento e' polinomiale e non una somma: due termini che si scambiano di valore — due
// nemici che finiscono con gli HP scambiati — darebbero la stessa somma e nessun ridisegno.
// I conti si fanno su `uint32_t` perche' il trabocco di un intero con segno e' comportamento
// indefinito, e il valore si tronca a 31 bit solo alla fine.
int BattleHud::_signature(const BattleSceneManager& battle) const
{
    uint32_t firma = 2166136261u;

    const auto mescola = [&firma](int valore)
    {
        firma = firma * 16777619u + uint32_t(valore + 1);
    };

    mescola(int(battle.state()));
    mescola(battle.round_number());
    mescola(battle.active_hero_index());
    mescola(int(battle.selected_command()));
    mescola(battle.selected_skill_index());
    mescola(battle.boost_level());
    mescola(battle.selected_target().is_enemy ? 1 : 0);
    mescola(battle.selected_target().slot);
    mescola(battle.event_cursor());

    for(int i = 0; i < UNIT_COUNT; ++i)
    {
        mescola(_hp_mostrati[i]);
        mescola(_abbattuto[i] ? 1 : 0);
    }

    for(const BattleUnit& hero : battle.party())
    {
        mescola(hero.current_fervor);
        mescola(hero.barrier_hp);
    }

    for(const BattleUnit& enemy : battle.enemies())
    {
        mescola(enemy.current_shield);
        mescola(enemy.break_turns);
    }

    return int(firma & 0x7FFFFFFFu);
}

} // namespace gubbio
