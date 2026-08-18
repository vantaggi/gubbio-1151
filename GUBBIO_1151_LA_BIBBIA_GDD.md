# GUBBIO 1151: LA GUERRA DELLE UNDICI CITTÀ
# LA BIBBIA DI DESIGN & TECHNICAL SPECIFICATION (MASTER DOCUMENT)
> **Piattaforma:** Game Boy Advance (GBA 32-bit ARM7TDMI)  
> **Engine:** Butano Engine (C++20) / devkitARM  
> **Genere:** Turn-based Tactical Dark Fantasy RPG  
> **Target Cartuccia:** 32MB Flash ROM + 256Kbit FRAM Non-Volatile Save  
> **Riferimento Storico:** L'assedio delle 11 Città Confederate contro Gubbio (Maggio 1151) e la mistica dei Tre Ceri  

---

## INDICE GENERALE DEI CONTENUTI (TOC)
1. [Visione Generale del Progetto](#1-visione-generale-del-progetto)
2. [I Protagonisti: L'Ordine dei Tre Ceri](#2-i-protagonisti-lordine-dei-tre-ceri)
3. [Gli Antagonisti: La Coalizione delle 11 Città](#3-gli-antagonisti-la-coalizione-delle-11-città)
4. [Trama Narrativa in Quattro Atti](#4-trama-narrativa-in-quattro-atti)
5. [Specifiche Tecniche GBA (Butano Engine)](#5-specifiche-tecniche-gba-butano-engine)
6. [Hardware e Flash della Cartuccia](#6-hardware-e-flash-della-cartuccia)
7. [Storytelling Completo & Sceneggiatura di Gioco](#7-storytelling-completo--sceneggiatura-di-gioco)
8. [Enciclopedia delle Reference Reali: Gubbio Medievale, Simboli, Folclore & Toponomastica](#8-enciclopedia-delle-reference-reali-gubbio-medievale-simboli-folclore--toponomastica)
9. [Correzione Araldica Rigorosa: Stemmi dei Quartieri e Simboli Civici](#9-correzione-araldica-rigorosa-stemmi-dei-quartieri-e-simboli-civici-di-gubbio)
10. [Guida Dettagliata agli Asset Visivi (Reference Art Sheet GBA)](#10-guida-dettagliata-agli-asset-visivi-reference-art-sheet-per-gba)
11. [Struttura Narrativa Sistematica (I 7 Passi del Story Design)](#11-struttura-narrativa-sistematica-i-7-passi-del-story-design)
12. [Architettura del Combat System (GBA / Butano Engine)](#12-architettura-del-combat-system-gba--butano-engine)
13. [Bilanciamento Matematico & Progressione (Modello Golden Sun / Fire Emblem)](#13-bilanciamento-matematico--progressione-modello-golden-sun--fire-emblem)
14. [Layout delle Scene & Specifiche delle Tilemap (GBA / 240x160)](#14-layout-delle-scene--specifiche-delle-tilemap-gba--240x160)
15. [Guida alla Ricostruzione Spaziale, Planimetrie Reali & Proporzioni Tilemap](#15-guida-alla-ricostruzione-spaziale-planimetrie-reali--proporzioni-tilemap)
16. [L'Arte dei Campanari & Il Suono del Campanone (Pilastro Diegetico & Auditivo)](#16-larte-dei-campanari--il-suono-del-campanone-pilastro-diegetico--auditivo)
17. [Altre Eccellenze Iconiche: Balestrieri, Sbandieratori, Tavole Eugubine & Folclore](#17-altre-eccellenze-iconiche-di-gubbio-balestrieri-sbandieratori-tavole-eugubine--folclore-mistico)
18. [Pipeline Tecnica Audio: Campionamento del Campanone & Integrazione Maxmod](#18-pipeline-tecnica-audio-campionamento-del-campanone--integrazione-maxmodbutano)
19. [Struttura del Repository & Architettura Software (Butano Engine C++20)](#19-struttura-del-repository--architettura-software-butano-engine-c20)
20. [Architettura della Battle Loop (Ispirata a Golden Sun & Octopath Traveler)](#20-architettura-della-battle-loop-ispirata-a-golden-sun--octopath-traveler)
21. [Implementazione Tilemap & Matrice di Collisione: Piazza Grande & Palazzo dei Consoli](#21-implementazione-tilemap--matrice-di-collisione-piazza-grande--palazzo-dei-consoli)
22. [Implementazione Dungeon: La Gola del Bottaccione & Il Condotto Pensile](#22-implementazione-dungeon-la-gola-del-bottaccione--il-condotto-pensile)
23. [Specifiche degli Sprite Sheet & Tabella delle Animazioni (Tre Ceri)](#23-specifiche-degli-sprite-sheet--tabella-delle-animazioni-tre-ceri)
24. [Sistema di Salvataggio Non-Volatile su FRAM (256 Kbit / SRAM GBA)](#24-sistema-di-salvataggio-non-volatile-su-fram-256-kbit--sram-gba)
25. [UI/UX, Font Proporzionale & Motore Dialoghi (Text Box Typewriter)](#25-uiux-font-proporzionale--motore-dialoghi-text-box-typewriter)
26. [Intelligenza Artificiale & Script delle Boss Fight](#26-intelligenza-artificiale--script-delle-boss-fight)
27. [Asset Pipeline & Automazione Build (Python & Claude Code Workflow)](#27-asset-pipeline--automazione-build-python--claude-code-workflow)
28. [Art Direction, Guida Estetica & Palette Shading per GBA](#28-art-direction-guida-estetica--palette-shading-per-gba)
29. [Durata del Gioco, Pacing dei Contenuti & Progressione Ore](#29-durata-del-gioco-pacing-dei-contenuti--progressione-ore)
30. [Setup Automatico del Progetto: Bash Initializer Script](#30-setup-automatico-del-progetto-bash-initializer-script)
31. [Database Completo degli NPC, Dialoghi Ramificati & Quest Secondarie](#31-database-completo-degli-npc-dialoghi-ramificati--quest-secondarie-i-4-quartieri)
32. [Icona del Gioco, Header Cartuccia & Metadati GBA](#32-icona-del-gioco-header-cartuccia--metadati-gba)
33. [Caricamento, Schermata dei Titoli & Menu di Sistema](#33-caricamento-schermata-dei-titoli--menu-di-sistema)
34. [Regia delle Cinematiche & Sequenze Animate](#34-regia-delle-cinematiche--sequenze-animate)
35. [Effetti Visivi, Particellari & Shader GBA (H-Blank Interrupts)](#35-effetti-visivi-particellari--shader-gba-h-blank-interrupts)
36. [Sound Design Completo & Sound Effects Table (SFX Matrix)](#36-sound-design-completo--sound-effects-table-sfx-matrix)
37. [Titoli di Coda & Epilogo Interattivo (La Vetrata della Vittoria)](#37-titoli-di-coda--epilogo-interattivo-la-vetrata-della-vittoria)
38. [Topografia Urbana & World Flow del Centro Storico (Dalle Mappe Reali)](#38-topografia-urbana--world-flow-del-centro-storico-dalle-mappe-reali)
39. [Mappa Tattica Regionale dell'Umbria & Le Tre Direttrici della Coalizione](#39-mappa-tattica-regionale-dellumbria--le-tre-direttrici-della-coalizione-1151)

---

## 1. VISIONE GENERALE DEL PROGETTO
*Gubbio 1151* è un gioco di ruolo tattico a turni per Game Boy Advance ispirato agli eventi storici raffigurati sulle vetrate della Basilica di Sant'Ubaldo sul Monte Ingino (l'assedio del 1151 da parte della coalizione di 11 città confederate guidate da Perugia).  
Il progetto rilegge il contesto storico attraverso una lente **Dark Fantasy medievale stilizzata**, elevando i Santi Patroni dei Tre Ceri a campioni mistici e trasformando i signori feudali della coalizione in signori della guerra araldici e mostruosi.

---

## 2. I PROTAGONISTI: L'ORDINE DEI TRE CERI

Il party è composto da 3 eroi fissi interconnessi da sinergie tattiche e un sistema di combattimento basato su **Fervore / Devozione** e barre d'azione.

### 1. Sant'Ubaldo (Il Vescovo Patriarca / High Hierophant)
* **Archetipo:** Chierico di Supporto / Controller Mistico
* **Arma:** *Verga Pastorale del Giudizio* (Ferro battuto e argento benedetto)
* **Ruolo in Combattimento:** Buffer, scudi divini, purificazione debuff e manipolazione dei turni.
* **Abilità Chiave:**
  * `Muro della Fede`: Barriera sacra che assorbe danni fisici e respinge proiettili d'assedio.
  * `Giudizio della Verga`: Colpo sacro a bersaglio singolo con la *Verga Pastorale del Giudizio*. **Aggiunta in Sessione 04:** era l'unica abilità offensiva di elemento Fede del party, e senza di essa la debolezza a Luce/Fede di nemici come il Balestriere Pesante non era sfruttabile da nessuno — la loro barra di Punti Scudo risultava irrompibile.
  * `Preghiera dei Tre Giorni`: Purifica gli status alterati dell'intero party e ripristina Fervore per 3 turni.
  * `Vigore della Rocca` *(Abilità Suprema)*: Potenzia la difesa del gruppo e rende tutti gli attacchi fisici di Giorgio intrisi di danno sacro radiante.

### 2. San Giorgio (Il Paladino della Lancia d'Oro)
* **Archetipo:** Vanguard / Tank / Single-Target Finisher (Cero dei Muratori/Commercianti)
* **Arma:** *Lancia da Giostra Benedetta & Scudo del Santo Cavaliere*
* **Ruolo in Combattimento:** Assorbe i colpi diretti (Taunt/Guardia), spezza le formazioni pesanti e infligge enormi danni perforanti ai boss corazzati e a cavallo.
* **Abilità Chiave:**
  * `Fendente del Drago`: Attacco in affondo che ignora il 50% dell'armatura nemica.
  * `Bastione Azzurro`: Intercetta gli attacchi mirati a Sant'Ubaldo o Sant'Antonio, convertendo i danni parati in punti Fervore.
  * `Carica del Destriero Celeste` *(Abilità Suprema)*: Carica travolgente che atterra tutti i nemici in prima linea.

### 3. Sant'Antonio Abate (L'Arcanista delle Fiamme Nere)
* **Archetipo:** Piromante Ermetico / DPS Magico ad Area (Cero dei Contadini)
* **Arma:** *Grimorio dell'Eremita & Bastone a Tau Fiammeggiante*
* **Ruolo in Combattimento:** Controllo delle masse, debuff delle resistenze nemiche e ustioni prolungate su macchine belliche e battaglioni.
* **Abilità Chiave:**
  * `Fuoco di Sant'Antonio`: Colpo magico di fuoco concentrato che applica status *Ustione Alchemica* cumulabile.
  * `Ceneri del Solstizio`: Incantesimo ad area che brucia le corazze nemiche, riducendone la difesa del 30%.
  * `Inferno del Porco Mistico` *(Abilità Suprema)*: Evocazione di fiamme ancestrali che inceneriscono l'intero campo di battaglia nemico.

---

## 3. GLI ANTAGONISTI: LA COALIZIONE DELLE 11 CITTÀ

La coalizione nemica è strutturata in una gerarchia di luogotenenti e signori feudali:

1. **Monaldo da Perugia (Il Tiranno del Grifo di Sangue - Boss Finale):** Sovrano della coalizione. Combatte impugnando uno spadone a due mani con anima d'ombra ed evoca avatar del Grifo di Perugia in più fasi di combattimento.
2. **Corrado di Spoleto (Il Colosso delle Forge):** Boss con corazza d'acciaio spessa e martello d'assedio. Immune ai danni da taglio finché Sant'Antonio non surriscalda le sue piastre.
3. **Valerio di Cagli (L'Alchimista della Flaminia):** Assassino e maestro di miasmi tossici che infetta i pozzi e schiera balestrieri con dardi avvelenati.
4. **I Signori di Foligno e Todi (I Gemelli della Tempesta):** Duo boss con attacchi combinati di vento e frecce fulminanti ad altissima velocità.
5. **I Conti di Nocera, Gualdo Tadino, Fossato, Assisi, Bettona, Spello:** Luogotenenti a capo delle linee di rifornimento e delle macchine d'assedio sparse nelle valli eugubine.

---

## 4. TRAMA NARRATIVA IN QUATTRO ATTI

### Atto I: Il Sigillo Spezzato e la Corona di Spine
* **Location:** Città di Gubbio (Piazza Grande, Quartieri di San Martino e San Giuliano, Monte Ingino).
* **Eventi:** La coalizione delle 11 città schiera le proprie armate attorno alla conca eugubina. I messaggeri nemici consegnano l'ultimatum a Palazzo dei Consoli. Il Vescovo Ubaldo ordina tre giorni di digiuno e preghiera sul Monte Ingino, risvegliando il potere spirituale dei Tre Ceri in Giorgio e Antonio.

### Atto II: La Guerra nell'Ombra
* **Location:** Gola del Bottaccione, Acquedotto Medievale, Valli di San Girolamo.
* **Eventi:** Con le porte sigillate, il party sfrutta gli antichi cunicoli della Gola del Bottaccione per compiere sabotaggi dietro le linee nemiche. Vengono distrutte le riserve di pece di Cagli e sabotati i primi trabucchi di Nocera e Fossato.

### Atto III: L'Eclissi delle Mura
* **Location:** Le Mura Urbiche, Porta Romana, Porta San Pietro.
* **Eventi:** La coalizione lancia l'assalto frontale con torri mobili e catapulte pesanti. Il gameplay alterna scontri tattici a turni e gestione della difesa delle porte, respingendo le cariche dei cavalieri di Spoleto e Foligno.

### Atto IV: La Notte del Giudizio (La Sortita)
* **Location:** Il Grande Accampamento Nemico nella Piana Eugubina.
* **Eventi:** All'alba del terzo giorno, avvolti dalla nebbia mattutina, i tre eroi guidano la carica decisiva nel cuore del campo di Monaldo da Perugia. Scontro finale epico a più fasi contro il Grifo Araldico e liberazione definitiva di Gubbio.

---

## 5. SPECIFICHE TECNICHE GBA (BUTANO ENGINE)

* **Risoluzione:** 240 × 160 pixel a 60 FPS.
* **Modalità Grafica:** Mode 0 / Mode 1 (BGs tilemap a layer multipli per parallasse durante l'esplorazione + scrolling dinamico durante le battaglie).
* **Audio Engine:** Maxmod GBA (Tracce chiptune orchestrali in formato `.xm` / `.it`).
* **Struttura Dati Personaggi (C++20):**

```cpp
#ifndef HERO_DATA_H
#define HERO_DATA_H

#include "bn_string_view.h"

struct HeroStats {
    bn::string_view name;
    int max_hp;
    int max_fervor;
    int physical_atk;
    int physical_def;
    int magic_resist;
    int faith_power;
    int flame_power;
    int speed;
};

constexpr HeroStats HEROES[] = {
    {"Sant'Ubaldo",   240, 180, 25, 45, 72, 95, 10, 30},
    {"San Giorgio",   380, 120, 90, 80, 40, 25,  0, 42},
    {"Sant'Antonio",  210, 210, 18, 28, 56, 20, 95, 38}
};

#endif
```

> **Nota di revisione (Sessione 02):** due valori di questa tabella sono stati fissati in fase di
> implementazione del Battle Engine.
> * `magic_resist` non era censita: e' derivata applicando alla Difesa Fisica il rapporto
>   Resistenza/Difesa della curva di crescita della Sezione 13B (Ubaldo 26/16, Giorgio 14/28,
>   Antonio 24/12).
> * Il Fervore massimo di San Giorgio e' passato da **70 a 120**. A 70 non poteva pagare il Boost
>   MAX della Sezione 20A (100 Fervore assoluti + 20 dell'abilita' firma), quindi la sua Mossa
>   Suprema `Carica del Destriero Celeste` era strutturalmente irraggiungibile. A 120 la attiva
>   consumando esattamente l'intera barra, coerentemente con la Sezione 12A. Resta il pool piu'
>   basso dei tre Ceri: la sua identita' di Cero meno mistico e' preservata dal tasso di accumulo,
>   non dal tetto.

---

## 6. HARDWARE E FLASH DELLA CARTUCCIA
* **Cartuccia Target:** Scheda GBA custom 32MB Flash ROM + 256Kbit FRAM (Non-Volatile Save).
* **Hardware di Scrittura:** GBxCart RW v1.4 / Joey Jr.
* **Flasher Utility:** FlashGBX (Linux/macOS/Windows).
* **Target Binary:** `gubbio1151.gba`.


---

## 7. STORYTELLING COMPLETO & SCENEGGIATURA DI GIOCO

### PROLOGO: L'OMBRA DELLE UNDICI CORONE
* **Cutscene d'apertura (Pixel Art Cinemagrafica):**
  Una mappa dell'Umbria medievale viene consumata lentamente dall'inchiostro nero. Undici stendardi si piantano sui valichi dell'Appennino. Al centro, la bandiera purpurea del Grifo di Perugia domina la scena.
* **Narrazione:**
  *Nel maggio del 1151, l'invidia e la sete di dominio spezzarono la pace dei colli. Undici città confederate cinsero d'assedio la roccaforte di Gubbio. Senza vie di fuga e con le scorte ridotte al lumicino, la città sembrò destinata a cadere nell'oblio. Ma dalle pietre del Monte Ingino non sorse la resa, bensì il fuoco mistico della Fede.*

---

### ATTO I: IL DIGIUNO DEL MONTE INGINO
* **Scena 1: L'Arringa a Piazza Grande**
  * Il gioco inizia sui camminamenti di Palazzo dei Consoli.
  * Il Podestà e i capitani delle milizie sono nel panico: le sentinelle avvistano le avanguardie nemiche da San Martino a Porta Romana.
  * Un araldo perugino varca le mura portando un ultimatum empio: la consegna immediata delle chiavi della città e l'assoggettamento totale al tiranno Monaldo da Perugia.
  * **Intervento di Ubaldo:** Il Vescovo Ubaldo non cede alle armi profane. Si frappone all'araldo, stringendo la verga pastorale: *"Gubbio non si prostra agli idoli di ferro. Prima che parli la spada, parlerà il cielo."*
* **Scena 2: L'Ascesa al Monte Ingino**
  * *Gameplay:* Il primo dungeon tutorial. Ubaldo guida il giovane cavaliere Giorgio e l'eremita Antonio lungo i tornanti dell'Ingino per raggiungere l'Eremo della Rocca.
  * *Nemici:* Falchi predatori corrotti e spie umbre infiltrate tra i sentieri.
* **Scena 3: Il Risveglio dei Tre Ceri (Cutscene / Boss Tutorial)**
  * All'interno della Basilica, Ubaldo officia il rito del digiuno sacro di tre giorni.
  * Tre pilastri di legno e luce ancestrale prendono vita dall'altare: i **Tre Ceri Mistici**.
  * Giorgio riceve l'armatura benedetta e la Lancia Radiante del Cero dei Muratori. Antonio viene avvolto dalle fiamme dell'Eremita, custode del Cero della Terra.
  * Primo scontro di prova contro gli *Spettri del Dubbio* evocati dal tormento dell'assedio per sbloccare le sinergie del party.

---

### ATTO II: LA GUERRA NELL'OMBRA
* **Scena 1: I Cunicoli del Bottaccione**
  * Con le porte principali barricate, il party sfrutta gli antichi condotti dell'acquedotto medievale nella Gola del Bottaccione per compiere una sortita notturna dietro le linee di accerchiamento.
  * *Atmosfera:* Dungeon labirintico, roccia scura, torce fioche e trappole alchemiche.
* **Scena 2: Sabotaggio alle Fornaci di Cagli e Nocera**
  * **Boss 1: Valerio di Cagli (L'Alchimista dei Miasmi)**
    * Trovato mentre avvelena il torrente Camignano con estratti di pece nera.
    * *Scontro:* Valerio combatte a distanza con nubi tossiche. Ubaldo deve mantenere attiva la purificazione mentre Giorgio e Antonio sfondano i suoi alambicchi magici.
  * La distruzione delle riserve di pece blocca il rifornimento dei trabucchi nemici.
* **Scena 3: L'Incontro con Corrado di Spoleto**
  * Al passo di Scheggia, il Colosso di Spoleto guida la scorta dei mangani da guerra.
  * **Boss 2: Corrado di Spoleto (Il Titano d'Acciaio)**
    * Una montagna vivente d'armatura.
    * *Meccanica di battaglia:* I fendenti di Giorgio rimbalzano. Antonio deve surriscaldare le giunture con *Fuoco di Sant'Antonio*, rendendole vulnerabili al colpo d'affondo finale di Giorgio.

---

### ATTO III: L'ASSEDIO ALLE MURA
* **Scena 1: L'Assalto delle Undici Bandiere**
  * La coalizione, infuriata per i sabotaggi, lancia l'offensiva generale contro Porta Romana e Porta San Pietro.
  * Il cielo sopra Gubbio si oscura per la pioggia di dardi infuocati.
* **Scena 2: La Difesa delle Porte (Battle Hub & Wave Survival)**
  * Il giocatore deve difendere la breccia sulle mura da ondate continue di fanti pesanti, scale d'assedio e battaglioni mercenari.
  * **Boss 3: I Gemelli di Foligno e Todi (Tempesta & Saetta)**
    * Uno controlla archi lunghi con raffiche fulminee, l'altro scaglia trombe d'aria che respingono il party.
    * *Scontro:* Necessita del *Muro della Fede* di Ubaldo per schermare i fulmini e consentire a Giorgio di raggiungere l'arciere in corpo a corpo.
* **Scena 3: L'Oracolo della Visione**
  * Le mura reggono a stento; le riserve d'acqua e grano sono finite.
  * All'interno del Duomo, mentre i cittadini invocano la salvezza, Sant'Ubaldo cade in trance mistica: ha la visione esatta del punto debole del campo perugino, protetto da un patto sacrilego con l'araldica oscura del Grifo.

---

### ATTO IV: LA NOTTE DEL GIUDIZIO (LA SORTITA)
* **Scena 1: La Carica nella Nebbia**
  * All'alba del terzo giorno dopo la visione, una fitta coltre di nebbia scende dal Bottaccione coprendo l'intera piana.
  * I tre campioni, alla testa di un drappello di miliziani eugubini, compiono una sortita a sorpresa nel cuore dell'accampamento confederato.
* **Scena 2: Dungeon Finale - L'Accampamento del Grifo**
  * Il campo di Monaldo è una cittadella di tende nere e trincee fortificate.
  * Il party sconfigge le guardie scelte delle ultime città confederate (Assisi, Bettona, Spello, Fossato).
* **Scena 3: Battaglia Finale - Monaldo da Perugia & L'Avatar del Grifo**
  * **Fase 1: Monaldo Tiranno di Ferro.** Scontro contro il generale in armatura completa e spadone a due mani intriso d'ombra.
  * **Fase 2: La Metamorfosi del Grifo di Sangue.** Sconfitto sul piano umano, Monaldo sacrifica il sangue della coalizione per tramutarsi nella gigantesca aberrazione alata del Grifo Araldico.
  * *Meccaniche Fase 2:* Il Grifo vola fuori portata; Antonio brucia le sue ali d'ombra facendolo precipitare al suolo, permettendo a Ubaldo di infrangere la barriera demoniaca e a Giorgio di trafiggere il cuore della bestia con la Lancia d'Oro dei Ceri.

---

### EPILOGO: LA GLORIA SULLE VETRATE
* Il Grifo cade in cenere. Gli stendardi delle 11 città si infrangono nella polvere e i superstiti fuggono in rotta disordinata.
* La nebbia si dirada rivelando Gubbio intatta, baciata dalla luce del sole sul Monte Ingino.
* **Scena Finale:** I tre eroi risalgono a Palazzo dei Consoli tra le campane a festa e la folla in trionfo.
* L'immagine finale passa dalla pixel art fluida 32-bit alla stilizzazione geometrica e luminosa delle **vetrate colorate della Basilica**, immortalandone la leggenda nei secoli.


---

## 8. ENCICLOPEDIA DELLE REFERENCE REALI: GUBBIO MEDIEVALE, SIMBOLI, FOLCLORE & TOPONOMASTICA

Questo capitolo raccoglie tutti gli elementi storici, urbanistici, araldici e folcloristici reali da trasformare in meccaniche di gioco, mappe, oggetti, equipaggiamenti e dialoghi.

---

### A. GEOGRAFIA REALE, MONTAGNE E TOPONOMASTICA DEI LIVELLI

1. **Il Monte Ingino (908 m s.l.m.):**
   * *Ruolo nel gioco:* Il monte sacro, sede dell'Eremo e della Rocca. I tornanti (gli "Stradoni") costituiscono il percorso dell'ascesa spirituale e della Corsa finale.
   * *Punti di riferimento:* La Basilica di Sant'Ubaldo in vetta, la Rocca Medievale (il Cassero), la sorgente di San Girolamo.
2. **Il Monte Foce (o Monte Calvo) & Monte D'Ansciano:**
   * I massicci che stringono la conca a nord e a ovest. Usati nel gioco come punti di appostamento dei trabucchi delle truppe di Spoleto e Cagli.
3. **La Gola del Bottaccione:**
   * *La Valle dei Misteri:* Tagliata dal torrente **Camignano** tra l'Ingino e il Foce.
   * *Archivio della Terra (Livello K-T / Iridio):* Geologicamente nota per lo strato di argilla scura (estinzione dei dinosauri). Nel gioco viene reinterpretata come una *vena di roccia alchemica oscura* sfruttata da Valerio di Cagli per le sue armi.
   * *L'Acquedotto Medievale (Il Condotto):* Lo stretto ponte-canale in pietra sospeso sul dirupo, utilizzato dal party come sentiero stealth per scavalcare le linee nemiche.
   * *Eremo di Sant'Ambrogio:* Luogo mistico nascosto nella gola per riposo, salvataggio e recupero MP/Fervore.
4. **La Rete delle Porte Urbiche (Le 6 Porte di Gubbio):**
   * **Porta Romana (Porta Sant'Agostino):** Accesso est, sotto l'attacco dei cavalieri di Spoleto e Foligno.
   * **Porta San Pietro (Porta Vittoria):** A sud, punto focale del grande assedio delle macchine perugine.
   * **Porta San Martino:** A nord, a ridosso del quartiere medievale più ripido.
   * **Porta Trasmondana (San Donato):** Ingresso verso le balze montane.
   * **Porta San Nicolò:** Verso la pianura.
   * **Porta Metauro / Marmorea:** Collegamento strategico verso la via Flaminia.
5. **Piazza Grande e il Complesso Consolare:**
   * *Piazza Pensile:* Monumentale piazza sospesa su arconi trecenteschi. Nel gioco funge da Hub Centrale e bastione del Governo Cittadino.
   * *Palazzo dei Consoli:* La sede del Podestà e dei Consoli di Giustizia. In cima svetta la torre campanaria con il **Campanone**.
   * *Palazzo Pretorio:* Il comando militare e deposito delle armi.
   * *Fontana dei Matti (Fontana del Bargello):* Fontana ottagonale davanti al Palazzo del Bargello. Meccanica: bere tre sorsi d'acqua conferisce la "Patente da Matto" (buff temporaneo: +50% Velocità, -20% Difesa, immune alla paura).

---

### B. QUARTIERI STORICI, STEMMI E COLORI

I 4 Quartieri storici di Gubbio sono le 4 fazioni cittadine che offrono supporto logistico e potenziamenti agli eroi:

| Quartiere | Stemma & Araldica Reale | Colori Sociali | Bonus / Ruolo nel Gioco |
| :--- | :--- | :--- | :--- |
| **San Martino** | Corona d'oro reale su campo vermiglio | **Rosso & Oro** | Forgia le armature pesanti e le armi di San Giorgio. Quartiere dei ferraioli e artigiani. |
| **Sant'Andrea** | Croce di Sant'Andrea bianca su campo verde | **Verde & Bianco** | Gilda degli erboristi e speziali; fornisce pozioni, bende e tinture medicamentose. |
| **San Pietro** | Chiavi pontificie incrociate con tiara | **Azzurro & Giallo** | Ordine dei chierici; accresce la barra di Fervore e le magie sacre di Sant'Ubaldo. |
| **San Giuliano** | Ramo d'olivo e stella d'oro su campo azzurro | **Blu Notte & Argento** | Fornisce intelligence, spie dei vicoli e mappe delle gallerie segrete. |

---

### C. LA SIMBOLOGIA DEI TRE CERI & USI TRADIZIONALI

I Tre Ceri non sono solo statue, ma l'anima del sistema di combattimento e dell'equipaggiamento sacro:

1. **Colori & Corporazioni:**
   * **Sant'Ubaldo:** *Camicia Gialla*, fazzoletto rosso, pantaloni bianchi. Simbolo: la **Mitra Vescovile**. Corporazione: *Muratori & Scalpellini*.
   * **San Giorgio:** *Camicia Azzurra*, fazzoletto rosso, pantaloni bianchi. Simbolo: l'**Elmo e la Spada**. Corporazione: *Commercianti, Merciari e Falegnami*.
   * **Sant'Antonio Abate:** *Camicia Nera*, fazzoletto rosso, pantaloni bianchi. Simbolo: la **Fiamma e il Porcellino**. Corporazione: *Contadini, Bestionari e Zappatori*.

2. **Oggetti Sacri e Rituali Trasformati in Oggetti Chiave:**
   * **Le Brocche di Ceramica Mastro Giorgio (Brocca dell'Alzata):**
     * Vasi in maiolica a lustro dorato e rubino.
     * *Meccanica:* All'inizio delle battaglie boss, Giorgio o Ubaldo compiono il rito del "Lancio della Brocca". I cocci frantumati a terra infondono l'effetto *Fervore Collettivo* raddoppiando l'attacco per i primi 3 turni.
   * **Il Batticero (La Barella di Legno):**
     * Struttura a croce in olmo e quercia dove poggiano i Ceri.
     * Nel gioco è una reliquia d'assedio montabile su un carro da guerra per sfondare le barricate perugine.
   * **Il Suono del Campanone:**
     * Il mastodontico bronzo sulla torre di Palazzo dei Consoli suonato dai maestri campanari "a doppi".
     * *Meccanica ad Evento:* Quando il Campanone rintocca durante le battaglie di difesa delle mura, azzera i cooldown del party e infligge status *Stordimento Sonoro* ai nemici.
   * **Il Fazzoletto Ceraiolo:**
     * Fazzoletto triangolare rosso vivo con spilla del Santo. Equipaggiabile come accessorio (+15 Fervore, protezione dai colpi critici).

---

### D. BESTIARIO FOLCLORISTICO E DELLA TRADIZIONE UMBRA

1. **Il Lupo d'Agobbio (Dungeon di Santa Maria della Vittoria):**
   * Una bestia mannara primordiale che infesta i boschi fuori Porta Metauro prima di essere pacificata da una preghiera di Sant'Ubaldo. Una volta redento, diventa una convocazione evocabile in battaglia.
2. **Lo Spettro del Bargello:**
   * Guardiano spettrale delle carceri del Palazzo del Bargello, dotato di balestra a tre frecce.
3. **I Cavalieri del Grifo di Sangue (Perugia):**
   * Cavalieri corazzati su destrieri bardati di rosso e nero, armati di lance pesanti e scudi recanti il Grifo d'Argento rampante.
4. **I Guerrieri della Roccia di Spoleto:**
   * Fanti muniti di scudi torre e mazze ferrate pesanti battute nelle ferriere della Valnerina.
5. **Gli Assassini della Gola di Cagli:**
   * Arcieri nascosti tra le forre rocciose che scoccano dardi impregnati di veleno di vipera dell'Appennino.

---

### E. GASTRONOMIA E CONSUMABILI COME ITEMS DI GIOCO

Nel gioco, il cibo tradizionale eugubino sostituisce le classiche pozioni RPG:

* **Crescia di Pasqua al Formaggio:** Ripristina 100 HP e conferisce status *Sazietà Fortificata* (+10% Difesa per 5 turni).
* **Crescia sotto la Cenere (con Foglietti e Friccò):** Ripristina tutti gli HP a un alleato caduto.
* **Baccalà alla Ceraiola (con prugne e uvetta):** Piatto tradizionale del 15 maggio. Rigenera completamente la barra del Fervore / MP di tutto il gruppo.
* **Biscotti all'Anice di Sant'Ubaldo:** Consumabile rapido che rimuove Veleno, Confusione e Silenzio.
* **Vino Rosso delle Colline Eugubine (Orvietano / Sagrantino d'importazione):** Aumenta l'Attacco del 40% ma riduce la Precisione del 15%.


---

## 9. CORREZIONE ARALDICA RIGOROSA: STEMMI DEI QUARTIERI E SIMBOLI CIVICI DI GUBBIO

> **Nota di Precisione Storica:**  
> A Gubbio la tradizione araldica dei **Quattro Quartieri storici** deriva dalle ricerche documentarie trecentesche (approfondite negli studi di Cece, Luongo e Biscarini per l'imbandieramento storico e per il *Torneo dei Quartieri*).

### 1. Stemma Civico del Comune di Gubbio
* **Blasonatura:** *Di rosso, al monte di cinque cime alla tedesca d'argento, caricato in capo del lambello (rastrello) a sei pendenti di rosso con cinque gigli d'oro in campo azzurro (Capo d'Angiò / fazione Guelfa).*
* **Elemento Identitario:** Il monte a cinque cime d'argento rappresenta la conformazione scoscesa del Monte Ingino e delle alture circostanti.

---

### 2. Gli Stemmi Reali dei Quattro Quartieri Storici

| Quartiere | Stemma & Figura Araldica Documentata | Campo / Colori Dominanti | Simbolo / Impresa Tradizionale |
| :--- | :--- | :--- | :--- |
| **Sant'Andrea** | **Palme incrociate** (Croce decussata) | Campo **Rosso** (Figura in Argento/Bianco) | Quartiere orientale, via Flaminia e Porta Romana. |
| **San Giuliano** | **Il Falcone** | Campo **Rosso** (Figura in Argento/Bianco) | Quartiere centrale e nobiliare. |
| **San Martino** | **La Corona** (regia a fioroni) | Campo **Rosso** (Figura in Argento/Bianco) | Quartiere dei fabbri e dei vicoli alti. |
| **San Pietro** | **La Rosa** (a 5 petali, fogliata e gambuta) | Campo **Rosso** (Figura in Argento/Bianco) | Quartiere meridionale, baluardo verso la pianura. |

---

### 3. I Colori Reali della Festa dei Ceri (Non confondere con i Quartieri!)
La Festa dei Ceri ha una propria codifica cromatica e corporativa autonoma rispetto ai quartieri:
* **Sant'Ubaldo (Muratori & Scalpellini):** Camicia Gialla, pantaloni bianchi, fazzoletto e fascia rossa.
* **San Giorgio (Commercianti, Falegnami & Merciari):** Camicia Azzurra, pantaloni bianchi, fazzoletto e fascia rossa.
* **Sant'Antonio (Contadini, Bestionari & Zappatori):** Camicia Nera, pantaloni bianchi, fazzoletto e fascia rossa.

---

## 10. GUIDA DETTAGLIATA AGLI ASSET VISIVI (REFERENCE ART SHEET PER GBA)

Per consentire la produzione o generazione precisa degli sprite e dei background in pixel art 32-bit (risoluzione base GBA $240 \times 160$ px):

```
+-----------------------------------------------------------------------------+
|                             ASSET VISIVI GBA                                |
|                                                                             |
|  [ BACKGROUNDS (Mode 0/1) ]        [ SPRITES (16x16 / 32x32) ]              |
|  - Piazza Grande (Arconi + Torre)   - Sant'Ubaldo (Veste oro/pastorale)     |
|  - Gola del Bottaccione (Acquedotto)- San Giorgio (Armatura azzurra/lancia) |
|  - Monte Ingino (Stradoni e Basilica) San Antonio (Saio nero/fiamme)        |
|  - Mura Urbiche (Porta Romana/Pietro) Boss: Grifo di Perugia (64x64 alato) |
+-----------------------------------------------------------------------------+
```

### Reference 1: Piazza Grande e Palazzo dei Consoli
* **Elementi Architettonici Indispensabili:** 
  * La piazza pensile sollevata sul vuoto con la pavimentazione in mattoni rossi disposti a spina di pesce.
  * La facciata gotica in pietra calcarea chiara del **Palazzo dei Consoli**, la loggia panoramica, la scalinata a ventaglio e la torretta con la campana (il *Campanone*).
  * Sul lato opposto: il profilo più sobrio del **Palazzo Pretorio**.
  * Di fronte: la ringhiera in ferro battuto che affaccia sulla vallata sottostante (effetto profondità a strati).

### Reference 2: La Gola del Bottaccione & L'Acquedotto Pensile
* **Palette Colori:** Grigio calcareo scuro, muschio verde umido, acqua limpida del torrente Camignano sul fondo e la fascia bruna/nerastra della roccia (livello K-T).
* **Architettura:** Il sottile ponte dell'acquedotto medievale ("Il Condotto") a campate ad arco che corre lungo la parete rocciosa a strapiombo.

### Reference 3: Monte Ingino & Stradoni
* **Composizione:** Sentiero sterrato a tornanti che sale a zig-zag tra pini e lecci secolari.
* In alto: il profilo della **Basilica di Sant'Ubaldo** con il chiostro e la torre della Rocca sovrastante.

### Reference 4: Gli Sprite dei Protagonisti & Boss
* **Sant'Ubaldo:** Pivot 16x32 pixel. Mantello liturgico giallo e oro, mitra vescovile d'argento, verga pastorale metallica con punta che scintilla di luce bianca.
* **San Giorgio:** Pivot 32x32 pixel (con armatura). Piastre metalliche con riflessi celesti, gualdrappa azzurra, elmo con pennacchio e lunga lancia dorata.
* **Sant'Antonio:** Pivot 16x32 pixel. Saio scuro con cappuccio, bastone a tau di legno nodoso, fiamme animate rosse e nere attorno alle mani; un piccolo cinghiale mistico a terra al suo fianco durante l'idle.
* **Monaldo / Grifo di Perugia (Boss 64x64):** Gigantesca chimera alata con testa e ali d'aquila e corpo di leone, con piume cremisi scure e occhi infuocati.


---

## 11. STRUTTURA NARRATIVA SISTEMATICA (I 7 PASSI DEL STORY DESIGN)

Questa sezione sviluppa nel dettaglio l'architettura narrativa del gioco seguendo i 7 passi del design narrativo per RPG.

---

### PASSO 1: PREMESSA E CONFLITTO CENTRALE (LOGLINE)
* **Logline:**  
  *Nel maggio 1151, Gubbio è cinta d'assedio da una coalizione di undici città guidata dalla tirannia di Perugia; tre campioni spirituali, incarnando la mistica dei Tre Ceri (Fede, Valore e Fuoco), devono superare il dubbio interiore, sabotare le macchine belliche e guidare una disperata sortita all'alba per spezzare il patto oscuro del Grifo di Sangue.*
* **Posta in gioco:**  
  La distruzione totale della città di pietra, la cancellazione dell'identità civica eugubina e l'assoggettamento feudale all'araldica demoniaca perugina.

---

### PASSO 2: WORLDBUILDING E REGOLE DEL MONDO
* **Tono:** Dark Fantasy Medievale Storico. Realismo architettonico/araldico unito a misticismo liturgico ed ermetico (luce sacra, piromanzia arcaica, araldica bestiale corrotta).
* **Le Due Forze in Campo:**
  * **La Devozione Eugubina (La Pietra e la Fede):** Il potere non deriva dalla magia profana, ma dalla devozione civica e spirituale, catalizzata dalla Basilica sul Monte Ingino e dai Tre Ceri.
  * **Il Patto del Grifo (La Corruzione Feudale):** Monaldo da Perugia ha stipulato un patto araldico che dona ai signori delle 11 città corazze animate, miasmi alchemici e tempeste elementali, al prezzo di sacrificare il sangue dei propri soldati.
* **Regole del Sistema Mistico:**
  * La magia di Ubaldo richiede **Fervore**, che si accumula proteggendo gli alleati e compiendo atti di fede comunitaria.
  * Il fuoco di Antonio necessita di combustibile spirituale e catalizzatori naturali (pece, legni benedetti, sacrifici materiali).
  * Il vigore marziale di Giorgio consuma energia fisica proporzionale al peso dell'armatura e richiede benedizioni per infliggere danni magici.

---

### PASSO 3: ARCO DEI PERSONAGGI E CONFLITTI INTERNI

#### 1. Sant'Ubaldo (Il Vescovo / High Hierophant)
* **Obiettivo Esterno:** Mantenere in vita il popolo di Gubbio e spezzare l'assedio delle 11 città senza cedere alla violenza d'odio.
* **Conflitto Interno (La Prova della Fede):** La tentazione di usare la forza militare bruta anziché la guida spirituale; il peso morale di vedere i propri cittadini soffrire la fame durante i tre giorni di digiuno.
* **Arco Evolutivo:** Passa dal ruolo di anziano pastore protettivo a guida carismatica assoluta, capace di compiere il miracolo della sortita nella nebbia.

#### 2. San Giorgio (Il Cavaliere / Vanguard)
* **Obiettivo Esterno:** Abbattere in duello i generali nemici (Corrado di Spoleto, i Gemelli, Monaldo).
* **Conflitto Interno (L'Orgoglio Marziale):** Il desiderio di gloria personale e l'impazienza giovanile che rischiano di farlo cadere nelle imboscate nemiche.
* **Arco Evolutivo:** Impara che la lancia non serve a conquistare fama, ma a fare da scudo vivente per chi non può difendersi, consacrandosi come vero campione del Cero.

#### 3. Sant'Antonio Abate (L'Eremita / Piromante)
* **Obiettivo Esterno:** Distruggere le macchine d'assedio e purificare i miasmi tossici che avvelenano le acque di Gubbio.
* **Conflitto Interno (L'Isolamento):** Il distacco eremitico dal mondo cittadino e la sfiducia nella natura umana.
* **Arco Evolutivo:** Riconnette il suo fuoco ermetico con la comunità dei lavoratori della terra, trasformando una fiamma solitaria in un baluardo di purificazione collettiva.

#### 4. Monaldo da Perugia (L'Antagonista Principale)
* **Obiettivo Esterno:** Conquistare Gubbio, sottomettere l'Appennino e offrire le anime della città all'Avatar del Grifo.
* **Motivazione:** L'ossessione per il dominio assoluto e la convinzione che la pietà sia una debolezza da estirpare dal feudalesimo umbro.

---

### PASSO 4: STRUTTURA DETTAGLIATA IN QUATTRO ATTI E BEAT SHEET

```
[ ATTO I: La Chiamata ] ──> [ ATTO II: Il Sabotaggio ] ──> [ ATTO III: La Breccia ] ──> [ ATTO IV: Il Trionfo ]
  - Ultimatum a Consoli       - Acquedotto Bottaccione       - Bombardamento Mura         - Sortita Nebbiosa
  - Digiuno Monte Ingino       - Valerio di Cagli (Veleno)   - Gemelli Tempesta           - Scontro Monaldo
  - Risveglio dei 3 Ceri      - Corrado Spoleto (Ferro)     - Visione Mistica nel Duomo  - Metamorfosi Grifo
```

* **Atto I (Incidente Scatenante):**
  * *Beat 1:* L'araldo perugino irrompe a Palazzo dei Consoli; rifiuto di Ubaldo.
  * *Beat 2:* Salita sul Monte Ingino braccati da spie e ricognitori.
  * *Beat 3:* Il Rito dei 3 Giorni: risveglio delle armi dei Ceri nella Basilica.
* **Atto II (Escalation & Ostacoli):**
  * *Beat 4:* Fuga notturna lungo l'Acquedotto pensile del Bottaccione.
  * *Beat 5:* Scontro con Valerio di Cagli; distruzione dei barili di pece nera.
  * *Beat 6:* Duello al passo con Corrado di Spoleto; fusione delle corazze corrotte.
* **Atto III (Il Punto di Crisi):**
  * *Beat 7:* Inizio del bombardamento su Porta Romana e Porta San Pietro.
  * *Beat 8:* Battaglia a ondate sulle mura; scontro con i Gemelli di Foligno e Todi.
  * *Beat 9 (Crisi Totale):* Esaurimento delle risorse idriche e alimentari; Sant'Ubaldo entra in preghiera estatica e svela il punto cieco nel campo nemico.
* **Atto IV (Climax & Risoluzione):**
  * *Beat 10:* Discesa nella piana sotto il velo della nebbia mattutina.
  * *Beat 11:* Infiltrazione e distruzione del comando perugino.
  * *Beat 12 (Climax):* Duello finale contro Monaldo (Forma Umana -> Grifo di Sangue).
  * *Beat 13:* Vittoria e trasfigurazione nella vetrata eterna della Basilica.

---

### PASSO 5: INTEGRAZIONE LUDONARRATIVA (MECCANICHE CHE RACCONTANO LA STORIA)

1. **Il Sistema di Fervore Dinamico:**
   * La barra di magia non si ripristina con pozioni standard ma con azioni di supporto reciproco (es. Giorgio che para un colpo per Antonio aumenta il Fervore di Ubaldo).
2. **Il Morale della Città:**
   * La riuscita delle quest secondarie nei 4 Quartieri (San Martino, Sant'Andrea, San Pietro, San Giuliano) aumenta la barra di resistenza delle Porte Urbiche durante l'Atto III.
3. **Le Reliquie della Tradizione:**
   * Lanciare la Brocca all'inizio della battaglia boss sacrifica un oggetto consumabile per dare un buff di velocità e attacco al party, rispecchiando l'esplosione di energia dell'Alzata dei Ceri.

---

### PASSO 6: COPIONE DEI DIALOGHI CHIAVE (GBA TEXT BOX FORMAT)

```
[BOX 1: Palazzo dei Consoli - Ultimatum]
ARALDO DI PERUGIA:
"Aprite le porte e consegnate le chiavi del Cassero. 
Monaldo non concederà una seconda alba."

SANT'UBALDO:
"Gubbio non piega la schiena davanti al ferro corrotto. 
Riferisci al tuo padrone che la pietra di questo monte 
è saldata con la fede, non con la paura."

[BOX 2: Basilica di Sant'Ubaldo - Risveglio dei Ceri]
SAN GIORGIO:
"Padre... la città trema sotto i colpi dei mangani. 
Cosa possono tre uomini contro undici eserciti?"

SANT'ANTONIO:
"La fiamma più piccola consuma la foresta più fitta, 
ragazzo. Stringi quella lancia e taci."

[BOX 3: Scontro Finale - Monaldo da Perugia]
MONALDO:
"Avete osato marciare nella nebbia per morire nel fango! 
Il Grifo divorerà le vostre ossa e le vostre preghiere!"

SANT'UBALDO:
"Oggi non muore Gubbio, Monaldo. Oggi cade l'orgoglio 
che ha insanguinato i colli dell'Umbria!"
```

---

### PASSO 7: RITMO E PACING DEL GAMEPLAY

| Sezione | Tensione | Tipo di Gameplay | Atmosfera Sonora |
| :--- | :--- | :--- | :--- |
| **Piazza Grande (Inizio)** | Media (Panico civico) | Esplorazione, Dialoghi NPC, Preparazione | Rintocchi cupi di campana |
| **Monte Ingino (Salita)** | Medio-Bassa | Dungeon esplorativo, combattimenti base | Vento montano e flauto |
| **Basilica (Rito Ceri)** | Alta (Solenne) | Cutscene mistica, Boss tutorial | Coro sacro chiptune |
| **Gola del Bottaccione** | Medio-Alta | Stealth, trappole, dungeon labirintico | Suoni d'acqua e archi bassi |
| **Boss Valerio / Corrado** | Altissima | Boss Fight tattica (sinergie obbligate) | Battaglia orchestrale GBA |
| **Difesa delle Porte** | Massima (Urgenza) | Survival a turni / Difesa posizionale | Rullanti di guerra e ottoni |
| **Sortita nella Nebbia** | Tensione Sospesa | Dungeon finale lineare, assalti a sorpresa | Melodia tetra con crescendo |
| **Monaldo / Grifo** | Picco Assoluto | Multi-stage Epic Boss Fight | Traccia finale polifonica completa |
| **Epilogo Trionfale** | Risoluzione | Cutscene finale e titoli di coda | Inno festoso e Campanone a doppi |


---

## 12. ARCHITETTURA DEL COMBAT SYSTEM (GBA / BUTANO ENGINE)

Il sistema di combattimento adotta una vista laterale (Side-View Turn-Based con sprite animati stile *Golden Sun / Final Fantasy VI*) basata sulla gestione dinamica del **Fervore**, posizionamento su griglia 3x2 e sinergie obbligate tra i Tre Ceri.

```
+-------------------------------------------------------------+
| [NEMICI: Formazione 3x2]        [PARTY DEI TRE CERI]        |
|  (Retrovia)    (Avanguardia)     (Avanguardia) (Retrovia)   |
|  [Arciere]     [Fante Scudo]     [San Giorgio] [S. Ubaldo]  |
|  [Alchimista]  [Cavaliere]                     [S. Antonio] |
+-------------------------------------------------------------+
```

---

### A. IL SISTEMA FERVORE (DEVOTION SYSTEM)

Nel gioco non esistono i canonici punti mana (MP) ricaricabili con pozioni universali. L'energia mistica è regolata dalla barra **Fervore** ($0 - 100$), individuale per ciascun Cero:

> **Chiarimento sulla scala (Sessione 02):** la scala $0-100$ è la **lettura normalizzata** della
> barra, ossia quella che l'HUD della Sezione 14B.3 disegna come `[F: 45%]`. Il *pool assoluto* è
> invece diverso per ogni Cero ed è quello censito nella Sezione 5 (Ubaldo 180, Giorgio 120,
> Antonio 210), perché i costi di Boost della Sezione 20A ($25 / 50 / 100$) sono valori assoluti.
> In codice la conversione è `BattleUnit::fervor_percent()`; l'invariante "ogni Cero deve poter
> pagare il Boost MAX" è verificato a compile time dalle `static_assert` in `battle_scene.h`.
>
> **Fervore all'ingresso in battaglia:** le percentuali del mockup HUD della Sezione 14B.3
> (Ubaldo $80\%$, Giorgio $45\%$, Antonio $20\%$) sono promosse da esempio grafico a **dato
> canonico di inizializzazione**: i Ceri non entrano in campo a barra piena. In assoluto:
> Ubaldo $144/180$, Giorgio $54/120$, Antonio $42/210$. Conseguenza tattica voluta — solo
> Sant'Ubaldo può aprire lo scontro con una Mossa Suprema; San Giorgio deve guadagnarsi la sua
> incassando 5 colpi ($+15$ ciascuno) e Sant'Antonio accumulando tick di Ustione ($+10$).
>
> **NOTA DI REVISIONE (2026-08-18, Sessione 11) — HP e Fervore SI TRASPORTANO fra le scene.**
> Le percentuali qui sopra restano valide, ma solo come **stato di una partita nuova**: non
> sono più l'inizializzatore di ogni scontro. Dalla seconda battaglia in poi ogni Cero entra in
> campo con gli HP e il Fervore con cui ha finito la precedente, trasportati da `GameState`
> (`include/game_state.h`) e destinati al salvataggio su FRAM.
> La prova che questa è la lettura corretta del documento sta **nella Sezione 6**, che assegna
> all'*Eremo di Sant'Ambrogio* «riposo, salvataggio e recupero MP/Fervore»: un luogo che
> ripristina il Fervore non ha alcuna funzione se il Fervore si ripristinasse da solo all'inizio
> di ogni combattimento. Conseguenze aperte, da decidere quando i luoghi esisteranno: quanto
> esattamente ripristini l'Eremo, e se la vittoria curi qualcosa (oggi **non cura nulla**, per
> non rendere invisibile il trasporto appena introdotto).

* **Accumulo di Fervore:**
  * **San Giorgio (Parata & Contrattacco):** Ricevere colpi fisici o attivare *Bastione Azzurro* per assorbire danni diretti a Ubaldo o Antonio genera $+15$ Fervore per colpo.
  * **Sant'Ubaldo (Fede & Supporto):** Applicare scudi, benedizioni o curare alleati con HP bassi genera $+20$ Fervore.
  * **Sant'Antonio (Combustione):** Ogni turno in cui un nemico subisce danni passivi da *Ustione Alchemica* genera $+10$ Fervore.
* **Consumo di Fervore:**
  * Le abilità standard richiedono $15 - 35$ Fervore.
  * Le **Mosse Supreme dei Tre Ceri** richiedono $100$ Fervore e consumano l'intera barra, innescando cutscene con scaling Mode 7/Affine.

---

### B. FORMULE DI CALCOLO DANNI & MITIGAZIONE

Tutti i calcoli sono ottimizzati per operazioni su interi a 32-bit (senza virgola mobile pesante su processore ARM7TDMI):

1. **Danno Fisico Diretto (San Giorgio / Fanti nemici):**
   $$	ext{DannoFisico} = \left[ (	ext{Atk} 	imes 2) - 	ext{DefNemica} 
ight] 	imes 	ext{ModificatoreAbilità} 	imes 	ext{RNG}(0.9, 1.1)$$
   * *Se $	ext{DefNemica} \ge (	ext{Atk} 	imes 2)$, il danno minimo garantito è pari a $1$.*

2. **Danno Magico / Fuoco (Sant'Antonio):**
   $$	ext{DannoFuoco} = \left[ (	ext{PotereFiamma} 	imes 2.5) - (	ext{ResistenzaMagica} 	imes 0.5) 
ight] 	imes 	ext{MoltiplicatoreUstione}$$
   * *Status Ustione Alchemica:* Infligge a fine turno un danno **assoluto** pari al $25\%$ del Potere Mistico di chi la applica, per 3 turni e cumulabile fino a 3 cariche. Il valore per carica è fissato al momento dell'applicazione.

> **Nota di revisione (Sessione 04):** questa voce prescriveva in origine *"il $10\%$ degli HP massimi
> del nemico"*. Con 3 cariche erano il $30\%$ degli HP massimi per round, una quota che azzera per
> costruzione il dimensionamento delle riserve di HP della Sezione 13D: nel collaudo su emulatore
> Corrado di Spoleto (1520 HP, mini-boss al $400\%$ di San Giorgio) moriva in **4 round**, con
> 456 danni/round dalla sola Ustione contro i ~139 di tutto il resto del party. Con il danno
> assoluto lo stesso scontro supera i 7 round e le riserve di HP tornano a contare.

3. **Valore di Assorbimento Scudo (Sant'Ubaldo):**
   $$	ext{HPScudo} = (	ext{PotereFede} 	imes 1.8) + (	ext{LivelloEroe} 	imes 12)$$

---

### C. COMBO DEI TRE CERI (TRI-SYNERGY ATTACKS)

Quando due o tre eroi agiscono nello stesso round con Fervore $\ge 50$, possono concatenare abilità combinate:

| Nome Combo | Eroi Coinvolti | Effetto Tattico |
| :--- | :--- | :--- |
| **Lancia Incandescente** | Giorgio + Antonio | Antonio infonde la lancia di Giorgio con fiamme sacre. Ignora la corazza del nemico e applica Ustione ad area sulla colonna posteriore. |
| **Egida della Purificazione** | Ubaldo + Giorgio | Ubaldo riflette i raggi di luce sullo scudo di Giorgio; acceca tutti i nemici (-50% Precisione per 2 turni) e devia il 100% dei proiettili. |
| **Giudizio del Monte Ingino** | Ubaldo + Antonio | Tempesta di fuoco sacro: converte tutti i debuff del party in danni radianti ad area contro l'intero schieramento nemico. |
| **Alzata Trionfale (Tri-Combo)** | Ubaldo + Giorgio + Antonio | Richiede 100 Fervore su tutti i membri. I Tre Ceri si manifestano in campo azzerando le difese dei boss e infliggendo colossali danni a 3 elementi (Fisico, Sacro, Fuoco). |

---

### D. STATI ALTERATI (STATUS EFFECTS)

* **Ustione Alchemica (Antonio):** Danno passivo da fuoco a inizio turno. Riduce del $20\%$ l'efficacia delle cure ricevute dal bersaglio.
* **Spezzacorazza (Giorgio):** Riduce la Difesa Fisica del bersaglio del $40\%$ per 2 turni.
* **Benedizione Liturgica (Ubaldo):** Rende il bersaglio immune a veleno e miasmi e rigenera il $5\%$ di HP a turno.
* **Terrore Feudale (Monaldo/Nemici):** Blocca l'accumulo di Fervore del personaggio affetto per 2 turni.
* **Stordimento da Campanone (Gubbio Event):** Il bersaglio salta il turno successivo e subisce colpi critici garantiti.

---

### E. IMPLEMENTAZIONE CODICE C++ (BUTANO ENGINE HEADER)

```cpp
// battle_engine.h - Strutture e Logica Combattimento per GBA
#ifndef BATTLE_ENGINE_H
#define BATTLE_ENGINE_H

#include "bn_core.h"
#include "bn_vector.h"
#include "bn_random.h"

enum class StatusEffect { NONE, ALCHEMICAL_BURN, ARMOR_BROKEN, BLESSED, TERRIFIED, STUNNED };
enum class ElementType { PHYSICAL, FAITH_HOLY, FLAME, VOID_SHADOW };

struct BattleUnit {
    bn::string_view name;
    int max_hp;
    int current_hp;
    int max_fervor;
    int current_fervor;
    int attack;
    int defense;
    int magic_power;
    int speed;
    StatusEffect current_status;
    int status_turns;
    bool is_enemy;

    [[nodiscard]] bool is_alive() const { return current_hp > 0; }

    void take_damage(int amount) {
        current_hp -= amount;
        if(current_hp < 0) current_hp = 0;
    }

    void add_fervor(int amount) {
        current_fervor += amount;
        if(current_fervor > max_fervor) current_fervor = max_fervor;
    }
};

class BattleSystem {
public:
    static int calculate_damage(const BattleUnit& attacker, const BattleUnit& target, int skill_power, ElementType element) {
        int base_dmg = 0;
        if(element == ElementType::PHYSICAL) {
            base_dmg = (attacker.attack * 2) - target.defense;
        } else if(element == ElementType::FLAME || element == ElementType::FAITH_HOLY) {
            base_dmg = (attacker.magic_power * 2) - (target.defense / 2);
        }
        if(base_dmg < 1) base_dmg = 1;
        return (base_dmg * skill_power) / 100;
    }
};

#endif
```


---

## 13. BILANCIAMENTO MATEMATICO & PROGRESSIONE (MODELLO GOLDEN SUN / FIRE EMBLEM)

Per garantire un bilanciamento collaudato senza dover testare i valori numerici da zero, l'architettura matematica adotta il sistema di crescita a progressione lineare di *Golden Sun* combinato con il triangolo delle debolezze tattiche di *Fire Emblem: The Sacred Stones*.

---

### A. TRIANGOLO DELLE AFFINITÀ E MOLTIPLICATORI ELEMENTALI

```
       [ FEDE / LUCE ] (Sant'Ubaldo)
         ▲         │
         │         ▼
   (Forte su)   [ OMBRA / CORRUZIONE ] (Coalizione Monaldo)
         │         │
         │         ▼
       [ FUOCO / PIROMANZIA ] (Sant'Antonio)
         ▲         │
         │         ▼
       [ ACCIAIO / FANTERIA ] (San Giorgio / Soldati)
```

* **Moltiplicatori di Efficacia:**
  * **Vantaggio Diretto (Debolezza):** $	imes 1.5$ Danno inflitto $+ 10\%$ Probabilità Colpo Critico.
  * **Neutro:** $	imes 1.0$ Danno.
  * **Svantaggio (Resistenza):** $	imes 0.5$ Danno inflitto.

---

### B. CURVA DI CRESCITA DEL PARTY (LIVELLI 1 - 20)

Progressione per livello basata su numeri interi (ottimizzata per registri ARM a 32-bit):

| Statistica | San Giorgio (Paladino Tank) | Sant'Ubaldo (Chierico Fede) | Sant'Antonio (Mago Fuoco) |
| :--- | :--- | :--- | :--- |
| **HP Base (Liv. 1)** | $120	ext{ HP}$ | $90	ext{ HP}$ | $75	ext{ HP}$ |
| **Incremento HP / Liv.** | $+22	ext{ HP}$ | $+14	ext{ HP}$ | $+11	ext{ HP}$ |
| **Attacco Fisico Base** | $32 \ (+5/	ext{liv})$ | $14 \ (+2/	ext{liv})$ | $10 \ (+1/	ext{liv})$ |
| **Difesa Fisica Base** | $28 \ (+4/	ext{liv})$ | $16 \ (+2/	ext{liv})$ | $12 \ (+1/	ext{liv})$ |
| **Potere Mistico Base** | $8 \ (+1/	ext{liv})$ | $30 \ (+5/	ext{liv})$ | $34 \ (+6/	ext{liv})$ |
| **Resistenza Mistica Base** | $14 \ (+2/	ext{liv})$ | $26 \ (+4/	ext{liv})$ | $24 \ (+4/	ext{liv})$ |
| **Velocità / Iniziativa Base** | $12 \ (+2/	ext{liv})$ | $16 \ (+2/	ext{liv})$ | $18 \ (+3/	ext{liv})$ |

---

### C. FORMULE DI CALCOLO DANNI STANDARDIZZATE

1. **Attacco Fisico Diretto (San Giorgio / Nemici Standard):**
   $$	ext{Danno} = \max\left(1, \left\lfloor rac{(	ext{Atk} 	imes 2) - 	ext{DefNemico}}{2} 
ight
floor 	imes 	ext{ModificatoreSkill}
ight)$$

2. **Abilità Mistica (Sant'Antonio / Sant'Ubaldo):**
   $$	ext{DannoMagico} = \max\left(1, \left[ 	ext{DannoBaseSkill} + \left\lfloor rac{	ext{PotereMistico} - 	ext{ResistenzaNemico}}{2} 
ight
floor 
ight] 	imes 	ext{MoltiplicatoreElementale}
ight)$$

---

### D. STATISTICHE DI RIFERIMENTO DEI NEMICI E PACING DEI BOSS

| Categoria Nemico | HP Rispetto al Party | Azioni / Turno | Comportamento IA | Esempio |
| :--- | :--- | :--- | :--- | :--- |
| **Mob Comune** | $60\%$ di San Giorgio | 1 | Attacca il bersaglio con meno Difesa | Fanti di Perugia, Spie di Cagli |
| **Nemico d'Elite** | $120\%$ di San Giorgio | 1 | Applica debuff o scudi al turno 1 | Cavalieri del Grifo, Balestrieri Pesanti |
| **Mini-Boss (Luogotenente)** | $400\%$ di San Giorgio | 2 | Schema alternato (Attacco pesante + Buff) | Corrado di Spoleto, Valerio di Cagli |
| **Boss Finale (Fase 1 Umana)** | $600\%$ di San Giorgio | 2 | Attacchi ad area e contrattacco | Monaldo Tiranno di Ferro |
| **Boss Finale (Fase 2 Grifo)** | $1000\%$ di San Giorgio | 3 | Volo fuori portata, tempesta d'ombra | Avatar del Grifo di Sangue |

---

### E. HEADER C++ DELLA PROGRESSIONE STATISTICHE (BUTANO ENGINE)

```cpp
// stat_growth.h - Calcolo statistiche e progressione party
#ifndef STAT_GROWTH_H
#define STAT_GROWTH_H

struct GrowthRates {
    int hp_gain;
    int atk_gain;
    int def_gain;
    int mag_gain;
    int res_gain;
    int spd_gain;
};

struct UnitBase {
    int base_hp;
    int base_atk;
    int base_def;
    int base_mag;
    int base_res;
    int base_spd;
    GrowthRates growth;
};

constexpr UnitBase PARTY_GROWTH[3] = {
    // San Giorgio (Tank / Paladino)
    {120, 32, 28,  8, 14, 12, {22, 5, 4, 1, 2, 2}},
    // Sant'Ubaldo (Chierico Fede / Supporto)
    { 90, 14, 16, 30, 26, 16, {14, 2, 2, 5, 4, 2}},
    // Sant'Antonio (Mago Fuoco / DPS Area)
    { 75, 10, 12, 34, 24, 18, {11, 1, 1, 6, 4, 3}}
};

inline void compute_stats_for_level(int hero_id, int level, int& out_hp, int& out_atk, int& out_def, int& out_mag, int& out_res, int& out_spd) {
    const auto& base = PARTY_GROWTH[hero_id];
    int l = level - 1;
    out_hp  = base.base_hp  + (base.growth.hp_gain * l);
    out_atk = base.base_atk + (base.growth.atk_gain * l);
    out_def = base.base_def + (base.growth.def_gain * l);
    out_mag = base.base_mag + (base.growth.mag_gain * l);
    out_res = base.base_res + (base.growth.res_gain * l);
    out_spd = base.base_spd + (base.growth.spd_gain * l);
}

#endif
```


---

## 14. LAYOUT DELLE SCENE & SPECIFICHE DELLE TILEMAP (GBA / 240x160)

Questa sezione definisce la gestione dei layer grafici, le dimensioni in tile e la mappatura della memoria video (VRAM) per il rendering a 60 FPS con Butano Engine in **Mode 0** (4 sfondi a tilemap indipendenti).

---

### A. ASSEGNAZIONE DEI LAYER HARDWARE GBA (MODE 0)

| Layer Hardware | Priorità | Tipologia | Risoluzione / Formato | Funzione nel Gioco |
| :--- | :--- | :--- | :--- | :--- |
| **BG0** | 0 (Top) | Text / HUD | $32 \times 32$ tile ($256 \times 256$ px) | Finestra dialoghi, barre HP/Fervore, menu di comando |
| **BG1** | 1 | Foreground / Collisioni | $64 \times 64$ o $32 \times 32$ tile | Tetti, merli, archi superiori (passaggio sotto) |
| **BG2** | 2 | Main Ground | $64 \times 64$ o $32 \times 32$ tile | Terreno calpestabile, facciate, ostacoli base |
| **BG3** | 3 (Bottom) | Parallasse / Cielo | $32 \times 32$ tile ($256 \times 256$ px) | Profilo Monte Ingino, vallata eugubina, nebbia |
| **OBJ (Sprites)**| Intermedio | Sprite Engine | OAM (128 sprite max) | Eroi, nemici, NPC, proiettili, effetti particellari |

---

### B. LAYOUT DELLE 3 MAPPE CARDINE

#### 1. Mappa Hub: Piazza Grande & Palazzo dei Consoli
* **Dimensioni Totali:** $512 \times 320$ pixel ($64 \times 40$ tile da $8 \times 8$ px).
* **Struttura dei Livelli:**
  * *Piano Superiore (Piazza Pensile):* Pavimentazione a mattoni rossi a spina di pesce, Palazzo dei Consoli a nord-ovest, Palazzo Pretorio a sud-est.
  * *Ringhiera Panoramica (Sud):* Affaccio sul vuoto; layer BG3 scorre a $1/4$ della velocità per mostrare la piana eugubina e gli accampamenti nemici lontani.
  * *Piano Inferiore (Arconi di Sostruzione):* Raggiungibile da scalinate laterali; zona d'ombra con depositi di grano e postazioni di difesa.
* **Punti di Trigger:** Portone dei Consoli (Ingresso Sala di Guerra), Fontana del Bargello (Accesso quartiere San Martino), Uscita Est verso Porta Romana.

#### 2. Mappa Dungeon: La Gola del Bottaccione & Il Condotto
* **Dimensioni Totali:** $256 \times 1024$ pixel ($32 \times 128$ tile a scorrimento prettamente verticale/obliquo).
* **Struttura dei Livelli:**
  * *BG3:* Parete rocciosa calcarea scura con fenditure e vene di roccia K-T.
  * *BG2:* Il camminamento stretto dell'Acquedotto Medievale (larghezza: 2 tile = 16 px, caduta laterale punita con riposizionamento e danno).
  * *BG1:* Archi in pietra e cascate d'acqua del Camignano che coprono visivamente il party per sezioni stealth.

#### 3. Schermata di Combattimento (Battle Screen Layout)
* **Risoluzione:** Fissa $240 \times 160$ px.
* **Suddivisione Spaziale:**

```
+-------------------------------------------------------------+
| [BG3: Sfondo d'Assedio - Monte Ingino / Nebbia]            |
|                                                             |
|  [NEMICI: 3x2]                   [PARTY CERI]               |
|   (x: 40-90, y: 50-100)           (x: 150-200, y: 50-100)   |
|   - 1-3 Mostri / Boss 64x64       - Ubaldo, Giorgio, Antonio|
+-------------------------------------------------------------+
| [BG0: HUD Inferiore - Altezza 48px (y: 112 - 160)]          |
|  [MENU COMANDI: 80px]  [STATO PARTY: 160px]                 |
|  > Attacca  | Abilità   |  S. Giorgio: 120/120 HP  [F: 45%] |
|    Oggetti  | Fuga      |  S. Ubaldo:   90/90  HP  [F: 80%] |
|                         |  S. Antonio:  75/75  HP  [F: 20%] |
+-------------------------------------------------------------+
```

---

### C. GESTIONE DELLA VRAM & PALETTE (GBA 15-BIT COLOR)

* **Allocazione Palette Sfondi (BG):**
  * *Palette 0-3:* Terreni e pietre calcaree di Gubbio (grigi caldi, ocra, mattone cotto).
  * *Palette 4-7:* Vegetazione dell'Ingino e legno dei Ceri (verdi bosco, marroni quercia).
  * *Palette 8-11:* Cielo, nebbia mattutina e fiamme alchemiche.
  * *Palette 12-15:* HUD, font e bordi dei box di testo (fondo nero semitrasparente, testo bianco/oro).
* **Allocazione Palette Sprite (OBJ):**
  * *Palette 0 (Sant'Ubaldo):* Giallo ocra, oro, bianco liturgico, argento mitra.
  * *Palette 1 (San Giorgio):* Azzurro cavaliere, metallo piastre, oro lancia, rosso fazzoletto.
  * *Palette 2 (Sant'Antonio):* Nero saio, arancio/rosso fuoco, cuoio scuro bastone.
  * *Palette 3-7:* Nemici comuni, soldati perugini e bestie araldiche.


---

## 15. GUIDA ALLA RICOSTRUZIONE SPAZIALE, PLANIMETRIE REALI & PROPORZIONI TILEMAP

Questa sezione fornisce i parametri geometrici, le coordinate relative e i rapporti di scala per trasporre la pianta reale di Gubbio e i suoi monumenti storici in una mappa a griglia ortogonale 16-bit per GBA (Tile $8 \times 8$ px e Sprite $16 \times 16$ px).

---

### A. RAPPORTO DI SCALA PLANIMETRICA (METRI -> PIXEL GBA)

* **Fattore di Conversione:** $1\text{ Tile } (8 \times 8\text{ px}) = 1.5\text{ metri reali}$.
* **Personaggio Standard ($16 \times 32$ px):** $1.75\text{ m reale} \approx 2\text{ tile di larghezza} \times 4\text{ tile di altezza}$.
* **Prospettiva Adottata:** *High-Angle Top-Down a 3/4* (stile classico *Golden Sun / Chrono Trigger*), con facciate proiettate verso l'alto di $1.2\times$ per enfatizzare l'imponenza gotica.

---

### B. PROPORZIONI E DIMENSIONI DEI MONUMENTI CARDINE

```
+-----------------------------------------------------------------------------+
| PALAZZO DEI CONSOLI (GBA Mode 0 Grid)                                      |
|                                                                             |
|  [Torre Campanaria con Campanone] -> Alt. 60m (40 Tile / 320 px)            |
|  [Loggetta Panoramica e Merli]    -> Larg. 33m (22 Tile / 176 px)           |
|  [Facciata Principale in Calcare] -> Finestre gotiche bifore                |
|  [Scalinata a Ventaglio]          -> Prof. 6m (4 Tile / 32 px)              |
|                                                                             |
| =========================================================================== |
| PIAZZA GRANDE (Piazza Pensile)    -> 130m x 40m (86 x 26 Tile / 688x208 px) |
| =========================================================================== |
|                                                                             |
|  [Arconi Inferiori di Sostruzione]-> Visibili dalla balza inferiore         |
|  [Palazzo Pretorio (Fronteggiante)]-> Alt. 30m (20 Tile / 160 px)           |
+-----------------------------------------------------------------------------+
```

> **NOTA DI REVISIONE (2026-08-18, Sessione 15) — LA CITTA' E' QUELLA CHE SI RICONOSCE.**
> Decisione del committente, presa dopo il rilievo che segue.
>
> **Quasi nessuno dei monumenti che rendono Gubbio riconoscibile esisteva nel 1151.** Il
> **Palazzo dei Consoli** — l'edificio simbolo, attorno a cui questa Bibbia costruisce l'hub —
> e' del **1332-1349**, su progetto di Angelo da Orvieto: posteriore di quasi due secoli
> all'assedio. Con esso e' posteriore **Piazza Grande**, che esiste *perche'* esiste quel
> palazzo. Il **Palazzo Ducale** e' quattrocentesco. La **Basilica di Sant'Ubaldo** custodisce un
> santo che nel 1151 e' **vivo**, ed e' il protagonista del gioco. Di tutti i trenta monumenti
> della pianta ufficiale, il **Teatro Romano** e' fra i pochissimi che nel 1151 c'erano gia'.
>
> **Si riproducono comunque tutti, senza correzioni cronologiche.** La ragione e' esplicita: il
> valore che si persegue e' che **un eugubino riconosca la propria citta'**, e una Gubbio
> romanica filologicamente corretta non la riconoscerebbe nessuno — oltre a essere
> archeologicamente poco documentata. Il gioco e' un dark fantasy con un Grifo demoniaco, non un
> simulatore storico: l'anacronismo e' una scelta, ed e' questa.
>
> Conseguenza operativa: `docs/riferimenti/FONTI.md` censisce i trenta monumenti con una colonna
> "nel 1151", che resta **informativa e non vincolante**. Nessuna sessione futura deve "correggere"
> la mappa rimuovendo cio' che e' posteriore.
>
> **La scala e' 1,5 metri per tile.** Non e' una convenzione nuova: e' quella che questa tabella
> gia' usa, verificata su cinque monumenti su sei (Consoli 33 m/22 tile, Piazza 130 m/86 tile,
> Pretorio 25 m/16, Fontana 4,5 m/3, Basilica 50 m/34). L'unica eccezione e' il ponte
> dell'acquedotto, 1,2 m rappresentato con 2 tile perche' sotto quella soglia non sarebbe
> percorribile. Ne segue che **Piazza Grande come oggi implementata (64x40 tile = 96 x 60 m) non
> e' in scala**: e' un quarto piu' corta e mezza volta piu' profonda della piazza vera. La scelta
> fra fedelta' (86x26) e giocabilita' (64x40) e' aperta e spetta al committente.

| Monumento Reale | Dimensioni Reali (m) | Dimensioni GBA (Tile $8\times8$) | Dettagli Architettonici Distintivi |
| :--- | :--- | :--- | :--- |
| **Palazzo dei Consoli** | $33\text{m largh.} \times 60\text{m alt.}$ | $22 \times 40\text{ tile } (176 \times 320\text{ px})$ | Facciata gotica in pietra chiara, portale a tutto sesto, scalinata semicircolare e torretta del Campanone sporgente. |
| **Piazza Grande** | $130\text{m lungh.} \times 40\text{m largh.}$ | $86 \times 26\text{ tile } (688 \times 208\text{ px})$ | Pavimentazione a spina di pesce rossa, ringhiera sud su vuoto con parallasse della piana. |
| **Palazzo Pretorio** | $25\text{m largh.} \times 30\text{m alt.}$ | $16 \times 20\text{ tile } (128 \times 160\text{ px})$ | Profilo massiccio, pietra scura a vista, finestre simmetriche austere. |
| **Fontana dei Matti (Bargello)** | $4.5\text{m diametro}$ | $3 \times 3\text{ tile } (24 \times 24\text{ px})$ | Bacino ottagonale in pietra calcarea, cannelle centrali con acqua animata a 3 frame. |
| **Acquedotto del Bottaccione** | Lunghezza totale $1.5\text{km}$ | Segmento $32 \times 128\text{ tile}$ | Ponte pensile mono-corsia largo $1.2\text{m}$ ($2\text{ tile}$ / $16\text{ px}$) a strapiombo sul torrente. |
| **Basilica di Sant'Ubaldo** | $50\text{m lungh.} \times 22\text{m largh.}$ | $34 \times 15\text{ tile } (272 \times 120\text{ px})$ | Navata unica, chiostro interno con porticato e scalinata d'accesso al Monte Ingino. |

---

### C. MATRICE DELLE COORDINATE TOPOGRAFICHE URBANE

Disposizione spaziale relativa della mappa urbana principale (World Grid $256 \times 256$ tile):

```
       [ MONTE INGINO - Basilica & Rocca ] (X: 128, Y: 10)
                     ▲
                     │  (Stradoni / Tornanti)
                     │
 [ GOLA DEL BOTTACCIONE ] (X: 40, Y: 60)
         ▲
         │ (Acquedotto)
         │
 [ QUARTIERE SAN MARTINO ] ── [ PIAZZA GRANDE & CONSOLI ] ── [ QUARTIERE SANT'ANDREA ]
 (X: 50, Y: 110 - Corona)      (X: 128, Y: 110 - Hub)          (X: 200, Y: 110 - Palme)
         │                               │                               │
         ▼                               ▼                               ▼
 [ PORTA SAN MARTINO ]         [ PALAZZO PRETORIO ]            [ PORTA ROMANA ]
 (X: 40, Y: 150)               (X: 128, Y: 140)                (X: 220, Y: 150)
                                         │
                                         ▼
                               [ QUARTIERE SAN PIETRO ]
                               (X: 128, Y: 180 - Rosa)
                                         │
                                         ▼
                               [ PORTA SAN PIETRO ]
                               (X: 128, Y: 220 - Assedio)
```

---

### D. WORKFLOW DI TRASPOSIZIONE DALLE FOTO REALI ALLE TILEMAP

Per convertire fedelmente foto e planimetrie reali in asset GBA compatibili con Butano:

1. **Rilievo Fotografico & Prospettico:**
   * Foto ortogonali frontali per le facciate (Palazzo dei Consoli, Bargello, Duomo).
   * Planimetrie catastali/satellitari per il tracciato delle mura e delle 6 porte.
2. **Scalatura su Griglia $8 \times 8$ px:**
   * Importazione della planimetria su *Aseprite* o *Tiled* su layer a griglia fissa $8 \times 8$ px.
   * Applicazione della palette indexed GBA (16 colori per subtile, con limitazione di max 4 palette BG attive per blocco).
3. **Generazione Collision Matrix (Mask):**
   * Creazione automatica dell'array di collisione binario in C++ ($0 = \text{Calpestabile}$, $1 = \text{Muro/Ostacolo}$, $2 = \text{Trigger Passaggio Livello}$, $3 = \text{Balcone Panoramico/Salto}$).


---

## 16. L'ARTE DEI CAMPANARI & IL SUONO DEL CAMPANONE (PILASTRO DIEGETICO & AUDITIVO)

Il **Campanone di Palazzo dei Consoli** e la sua *sonata a doppi* (eseguita dai maestri campanari a corpo libero in cima alla torretta) sono il motore emotivo, narrativo e sonoro di tutto il gioco.  
Non è un minigioco separato: è un **evento diegetico integrato** i cui rintocchi reali scandiscono l'esplorazione, sbloccano passaggi ed esplodono come shockwave acustica nei momenti cruciali della battaglia.

---

### A. IL SUONO DEL BRONZO COME PILASTRO NARRATIVO & GAMEPLAY

```
+-----------------------------------------------------------------------------+
|              IL CAMPANONE: EVENTI DIEGETICI & TRIGGER ACUSTICI               |
|                                                                             |
|  [Esplorazione Hub] --------> Rintocchi all'Alba e al Tramonto              |
|  [Fase d'Allarme / Assedio] -> 'Doppio d'Assedio' (Aumenta Fervore Party)   |
|  [Fronte delle Mura] -------> Shockwave Acustica: Stordisce l'Avanguardia   |
|  [Sortita all'Alba] --------> 'Sonata Solenne': Dissipa la Nebbia Oscura    |
+-----------------------------------------------------------------------------+
```

1. **Risonanza Dinamica sulle Mura (Atto III):**
   * Quando i campanari salgono sulla gabbia e lanciano il bronzo *"a bicchiere"*, la campana suona a doppi dall'alto della città pensile.
   * L'onda d'urto del Campanone attraversa le vallate:
     * **Effetto Alleati:** Genera $+30$ Fervore immediato a tutto il party e annulla i cooldown delle abilità supreme.
     * **Effetto Nemici:** Infligge lo status *Stordimento Acustico* alle truppe nemiche (salto del turno e rottura degli scudi d'assedio).
2. **Lo Svegliarino e la Guida nella Nebbia (Atto IV):**
   * Durante la carica notturna nella fitta nebbia della piana eugubina, il rintocco profondo e cadenzato del Campanone fa da *faro acustico*, impedendo al party di perdersi e dissipando l'illusione di disorientamento creata da Monaldo da Perugia.

---

### B. AUDIO DESIGN NATURALE PER GBA (MAXMOD SOUND ENGINE)

* **Campione Reale PCM:** Il timbro reale del Campanone (oltre 20 quintali di bronzo fuso) è campionato direttamente in PCM a 8-bit sui canali DirectSound del GBA. Il suo rimbombo metallico, caratterizzato da un decadimento lungo e risonanze basse, vibra sopra le tracce tracker `.xm`.
* **Codifica delle Tre Sonate Tradizionali:**
  * **Il Doppio d'Assedio:** Battuta serrata a rotazione continua che accompagna le sequenze di combattimento sulle porte urbiche.
  * **La Sonata Solenne dei Ceri:** Armonia a festa che risuona durante il risveglio delle armi mistiche e nella vittoria finale.
  * **Il Rintocco Solitario (Svegliarino):** Tocco singolo e maestoso che segna il cambio di fase temporale tra il giorno e la notte.


---

## 17. ALTRE ECCELLENZE ICONICHE DI GUBBIO: BALESTRIERI, SBANDIERATORI, TAVOLE EUGUBINE & FOLCLORE MISTICO

Questo capitolo integra nel GDD altri quattro pilastri dell'identità storica ed etno-culturale di Gubbio, traducendoli in classi ausiliarie, reliquie mistiche e meccaniche di combattimento.

---

### A. I BALESTRIERI DI GUBBIO (LA SOCIETÀ DEI BALESTRIERI & IL PALIO DELLA BALESTRA)
* **Contesto Reale:** La tradizione plurisecolare del tiro con la balestra all'italiana antica da banco (*Tasso*), celebrata storicamente nel Palio della Balestra contro Sansepolcro.
* **Integrazione nel Gioco:**
  * **Unità Alleata / Classe Speciale:** *I Balestrieri del Monte*.
  * **Meccanica "Tiro al Tasso":** Durante le fasi di difesa delle porte urbiche (Atto III), il giocatore può attivare un minigioco di mira per centrare con precisione millimetrica i comandanti nemici nelle retrovie, ignorando la prima linea di scudi.
  * **Arma Chiave Equipaggiabile:** *Balestra Antica da Posta* (Danno perforante elevato con tempo di caricamento di 1 turno).

---

### B. IL GRUPPO SBANDIERATORI DI GUBBIO (L'ARTE DEL MANEGGIO DELLA BANDIERA)
* **Contesto Reale:** Celebri in tutto il mondo per l'eleganza dei lanci acrobatici, i costumi d'epoca rigorosi e le figure geometriche aeree.
* **Integrazione nel Gioco:**
  * **Ruolo Tattico (Aura Buff & Supporto):** Gli alfieri sbandieratori accompagnano i tre eroi sul campo.
  * **Abilità "Lancio di Bandiera / Figura dei Ceri":** Lanciare la bandiera verso l'alto deflette le frecce nemiche per 1 round e concede a tutto il party un bonus del $+25\%$ alla Schivata e all'Iniziativa.
  * **Oggetto Sacro:** *Vessillo del Comune di Gubbio* (Aumenta il guadagno di Fervore del party a ogni colpo andato a segno).

---

### C. LE TAVOLE EUGUBINE (LE TAVOLE IGUVINE IN BRONZO)
* **Contesto Reale:** Sette tavole bronzee scritte in caratteri umbri ed etruschi (III-I sec. a.C.), il più importante documento epigrafico dell'antichità italica, contenenti rituali sacri, purificazioni e preghiere alla divinità *Jove Grabovio*.
* **Integrazione nel Gioco:**
  * **Le Reliquie Ancestrali (Tavole di Bronzo I - VII):** Sette frammenti incisi nascosti nei dungeon (Bottaccione, Rocca, cripte di San Pietro e Duomo).
  * **Meccanica "Liturgia Umbra Ancestrale":** Decifrare le tavole conferisce a Sant'Ubaldo e Sant'Antonio incantesimi primordiali di purificazione e benedizione della terra contro le aberrazioni del Grifo.
  * **Abilità Segreta sbloccata:** *Rito di Grabovio* (Evoca una barriera di bronzo runico che riflette le magie d'ombra nemiche).

---

### D. L'ALBERO DI NATALE DI GUBBIO (L'ALBERO PIÙ GRANDE DEL MONDO)
* **Contesto Reale:** La maestosa sagoma luminosa disegnata con centinaia di sorgenti di luce sulle pendici del Monte Ingino.
* **Integrazione nel Gioco (Reinterpretazione Dark Fantasy):**
  * **"Il Faro dell'Ingino / La Rete delle Luci":** Durante l'Atto IV, quando la nebbia cala sulla piana, i cittadini accendono falò e fiaccole lungo tutto il profilo del monte, tracciando la sagoma piramidale luminosa.
  * **Effetto Gameplay:** La luce dell'Ingino dirada la nebbia magica di Monaldo, impedendo ai nemici di colpire alle spalle e raddoppiando il danno delle magie di fuoco e luce.

---

### E. LA CERAMICA A LUSTRO ORO E RUBINO (MASTRO GIORGIO ANDREOLI)
* **Contesto Reale:** La celebre tecnica rinascimentale dei lustri metallici iridescenti a riflessi rossi e dorati.
* **Integrazione nel Gioco:**
  * **Materiale di Crafting Unico:** *Polvere di Lustro Rubino*.
  * Usata per forgiare la punta della *Lancia di San Giorgio* e potenziare gli anelli del party per ottenere riflessi elementali contro gli incantesimi avversari.


---

## 18. PIPELINE TECNICA AUDIO: CAMPIONAMENTO DEL CAMPANONE & INTEGRAZIONE MAXMOD/BUTANO

Questa sezione specifica la procedura di acquisizione, filtraggio e integrazione del suono autentico del Campanone di Palazzo dei Consoli all'interno della cartuccia Game Boy Advance a 32-bit.

---

### A. FONTI AUDIO & REGISTRAZIONI REALI DI RIFERIMENTO

* **Archivio Ufficiale della Compagnia dei Campanari di Gubbio:**
  * Documentazione ufficiale delle sonate codificate (*campanari.it*).
  * Sonate di riferimento: *Il Doppio Solenne del 15 Maggio*, *La Sonata d'Assedio* e *Lo Svegliarino mattutino*.
* **Tracce Audio Isolabili:**
  * Campione 1: Singolo rintocco isolato con attacco percussivo e riverbero lungo del bronzo.
  * Campione 2: Loop ritmico della rotazione completa a doppi ("a bicchiere").

---

### B. PROCESSO DI CONVERSIONE PCM PER GBA (BUTANO ENGINE)

Per garantire la massima fedeltà acustica sui canali DirectSound senza esaurire la memoria della ROM:

1. **Specifiche di Campionamento:**
   * **Formato File:** `.wav` non compresso (PCM).
   * **Canali:** Mono (1 canale).
   * **Profondità Bit:** $8\text{-bit Signed PCM}$.
   * **Sample Rate Ottimale:** $16.000\text{ Hz}$ o $21.055\text{ Hz}$ (compromesso perfetto per mantenere il corpo delle basse frequenze con un peso di soli $\approx 32\text{ KB}$ per 2 secondi di audio).

2. **Organizzazione dei File nel Repository:**

```
gubbio1151_gba/
├── audio/
│   ├── sound_effects/
│   │   ├── campanone_hit.wav       # Singolo rintocco profondo (PCM 8-bit, 16kHz)
│   │   ├── campanone_doppio.wav    # Sequenza a doppi per battaglie e cutscene
│   │   └── brocca_break.wav        # Frantumazione ceramica Mastro Giorgio
│   └── music/
│       ├── gubbio_piazza_hub.xm    # Traccia tracker chiptune orchestrale
│       └── siege_eleven_cities.xm  # Battaglia contro Perugia e coalizione
```

3. **Integrazione nel Codice C++20 (Butano Engine):**

```cpp
// campanone_audio.h - Gestione trigger sonoro del Campanone
#ifndef CAMPANONE_AUDIO_H
#define CAMPANONE_AUDIO_H

#include "bn_sound_items.h"
#include "bn_sound.h"

class CampanoneAudio {
public:
    // Riproduce il singolo tocco maestoso con volume pieno
    static void play_strike() {
        bn::sound_items::campanone_hit.play(1.0);
    }

    // Riproduce la sequenza d'assedio/allarme a doppi
    static void play_siege_double() {
        bn::sound_items::campanone_doppio.play(1.0);
    }
};

#endif
```


---

## 20. ARCHITETTURA DELLA BATTLE LOOP (ISPIRATA A GOLDEN SUN & OCTOPATH TRAVELER)

Per garantire un loop di combattimento tattico, dinamico e visivamente spettacolare, il sistema fonde la presentazione e fluidità a turni di **Golden Sun** con la meccanica di rottura guardia e amplificazione turni (**Shield Break & Boost / Fervore**) di **Octopath Traveler**.

---

### A. I 3 PILASTRI DELLA BATTLE LOOP

1. **Timeline & Order Queue (Modello FFX / Golden Sun):**
   * L'ordine di azione del round è visibile in alto a destra tramite piccole icone degli eroi e dei nemici, determinate dalla statistica *Velocità* e da eventuali modificatori di priorità delle abilità.
2. **Sistema "Scudo dei Signori Feudali" (Shield Break):**
   * Ogni nemico o boss possiede una barra di **Corazza/Punti Scudo** ($1 - 6$).
   * Colpire il punto debole (es. Fuoco di Antonio sui cavalieri corazzati, Luce di Ubaldo sui non-morti/ombre) sottrae $1$ Punto Scudo.
   * Quando lo Scudo scende a $0$, il nemico entra in stato **BREAK**: salta il turno corrente + il successivo e la sua Difesa Fisica/Mistica viene dimezzata.
3. **Fervor Boost (Spend to Supercharge):**
   * Durante la selezione del comando, spendere cariche di **Fervore** moltiplica l'efficacia dell'azione:
     * *Boost x1 (25 Fervore):* $+50\%$ Danno / Scudo raddoppiato.
     * *Boost x2 (50 Fervore):* Attacco a doppio colpo (toglie 2 Punti Scudo) o applica buff a tutta la colonna.
     * *Boost MAX (100 Fervore):* Attiva l'Abilità Suprema del Cero con animazione a schermo intero.

---

### B. LA MACCHINA A STATI DELLA BATTAGLIA (FINITE STATE MACHINE)

```
 [ INIZIO BATTAGLIA ] ──> Calcolo Iniziativa & Display Formazioni
           │
           ▼
 ┌───> [ STATO 1: INPUT_HERO_1 (San Giorgio) ] ──> Seleziona Attacco/Skill/Boost
 │         │
 │         ▼
 ├───> [ STATO 2: INPUT_HERO_2 (Sant'Ubaldo) ] ──> Seleziona Buffer/Cure/Boost
 │         │
 │         ▼
 ├───> [ STATO 3: INPUT_HERO_3 (Sant'Antonio) ] ─> Seleziona Magia Fuoco/Debuff
 │         │
 │         ▼
 │     [ STATO 4: EXECUTE_TURN_QUEUE ]
 │         ├─ Esecuzione azioni in ordine di Velocità
 │         ├─ Animazioni colpi, particellari e scaling Mode 7
 │         ├─ Calcolo danni, status 'Break' e tick Ustione Alchemica
 │         └─ Trigger sonoro del Campanone in caso di evento speciale
 │         │
 │         ▼
 └───  [ STATO 5: CHECK_WIN_LOSE ]
           ├─ Nemici sconfitti ──> [ STATO 6: VICTORY_FANFARE & REWARDS ]
           ├─ Party esausto    ──> [ STATO 7: GAME_OVER ]
           └─ Nemici vivi      ──> Ritorno a STATO 1 per il nuovo round
```

---

### C. IMPLEMENTAZIONE IN C++20 (BUTANO ENGINE: `battle_scene.h`)

```cpp
// battle_scene.h - Macchina a stati della Battle Loop
#ifndef BATTLE_SCENE_H
#define BATTLE_SCENE_H

#include "bn_core.h"
#include "bn_vector.h"
#include "bn_keypad.h"
#include "battle_engine.h"
#include "campanone_audio.h"

enum class BattleState {
    INTRO_FADE_IN,
    SELECT_COMMAND_GIORGIO,
    SELECT_COMMAND_UBALDO,
    SELECT_COMMAND_ANTONIO,
    EXECUTE_ROUND_ACTIONS,
    CHECK_ROUND_OUTCOME,
    VICTORY,
    DEFEAT
};

struct QueuedAction {
    BattleUnit* actor;
    BattleUnit* target;
    int skill_id;
    int fervor_boost_level; // 0 = standard, 1 = 25%, 2 = 50%, 3 = MAX
    int calculated_speed;
};

class BattleSceneManager {
private:
    BattleState _current_state;
    bn::vector<BattleUnit, 3> _party;
    bn::vector<BattleUnit, 6> _enemies;
    bn::vector<QueuedAction, 9> _action_queue;
    int _selected_menu_index;

public:
    BattleSceneManager() : 
        _current_state(BattleState::INTRO_FADE_IN),
        _selected_menu_index(0) {}

    void init_battle(int encounter_id) {
        // Carica party e nemici in base al dungeon/boss
        _current_state = BattleState::SELECT_COMMAND_GIORGIO;
    }

    void update() {
        switch(_current_state) {
            case BattleState::SELECT_COMMAND_GIORGIO:
                handle_command_input(0, BattleState::SELECT_COMMAND_UBALDO);
                break;

            case BattleState::SELECT_COMMAND_UBALDO:
                handle_command_input(1, BattleState::SELECT_COMMAND_ANTONIO);
                break;

            case BattleState::SELECT_COMMAND_ANTONIO:
                handle_command_input(2, BattleState::EXECUTE_ROUND_ACTIONS);
                break;

            case BattleState::EXECUTE_ROUND_ACTIONS:
                execute_all_queued_actions();
                _current_state = BattleState::CHECK_ROUND_OUTCOME;
                break;

            case BattleState::CHECK_ROUND_OUTCOME:
                if(all_enemies_dead()) {
                    _current_state = BattleState::VICTORY;
                } else if(all_heroes_dead()) {
                    _current_state = BattleState::DEFEAT;
                } else {
                    // Nuovo round
                    _action_queue.clear();
                    _current_state = BattleState::SELECT_COMMAND_GIORGIO;
                }
                break;

            case BattleState::VICTORY:
                // Fanfara, ricompense, loot e ritorno alla mappa
                break;

            case BattleState::DEFEAT:
                // Schermata Game Over
                break;

            default:
                break;
        }
    }

private:
    void handle_command_input(int hero_idx, BattleState next_state) {
        // Navigazione comandi D-Pad
        if(bn::keypad::up_pressed()) _selected_menu_index = (_selected_menu_index - 1 + 4) % 4;
        if(bn::keypad::down_pressed()) _selected_menu_index = (_selected_menu_index + 1) % 4;

        // Tasto R: Attiva/Incrementa Boost Fervore
        if(bn::keypad::r_pressed()) {
            // Aggiunge moltiplicatore consumando Fervore
        }

        // Tasto A: Conferma azione
        if(bn::keypad::a_pressed()) {
            // Aggiunge l'azione pianificata alla coda
            _current_state = next_state;
            _selected_menu_index = 0;
        }

        // Tasto B: Torna indietro al personaggio precedente
        if(bn::keypad::b_pressed() && hero_idx > 0) {
            _current_state = static_cast<BattleState>(static_cast<int>(_current_state) - 1);
        }
    }

    void execute_all_queued_actions() {
        // Ordina la coda per velocità
        // Esegue animazioni colpi, applica danni e riduce barre Scudo
    }

    bool all_enemies_dead() const {
        for(const auto& enemy : _enemies) {
            if(enemy.is_alive()) return false;
        }
        return true;
    }

    bool all_heroes_dead() const {
        for(const auto& hero : _party) {
            if(hero.is_alive()) return false;
        }
        return true;
    }
};

#endif
```


---

## 21. IMPLEMENTAZIONE TILEMAP & MATRICE DI COLLISIONE: PIAZZA GRANDE & PALAZZO DEI CONSOLI

Questa sezione definisce la matrice binaria delle collisioni per l'Hub principale di Piazza Grande, specificando i layer di rendering (BG Mode 0), i trigger di transizione e l'integrazione del parser in C++20 con Butano Engine.

---

### A. SPECIFICHE DIMENSIONALI DELLA TILEMAP

* **Dimensioni Totali:** $64 \times 40\text{ tile}$ ($512 \times 320\text{ pixel}$).
* **Dimensione Singola Tile:** $8 \times 8\text{ pixel}$.
* **Layer Grafici:**
  * **BG2 (Main Ground):** Pavimentazione a spina di pesce in cotto rosso, scalinata semicircolare dei Consoli, parapetto in ferro a sud.
  * **BG1 (Foreground):** Sporti della loggetta panoramica, merlatura gotica e arcate sotto cui il player può camminare.
  * **BG3 (Parallasse 1/4 vel.):** Panorama della pianura eugubina e sagome dei trabucchi nemici in lontananza.

---

### B. LEGENDA DEI TRIGGER E DELLA MASCHERA DI COLLISIONE

La matrice usa valori a 8-bit per determinare calpestabilità ed eventi di transizione:

```
+-----------------------------------------------------------------------------+
| VALORE | TIPO / STATO       | COMPORTAMENTO NEL GAME LOOP                   |
+--------+--------------------+-----------------------------------------------+
|   0    | CALPESTABILE       | Movimento libero del personaggio a terra      |
|   1    | SOLIDO (MURO)      | Collisione rigida (blocco del movimento)      |
|   2    | PARAPETTO / RINGH. | Blocco collisione ma visuale aperta su BG3    |
|   3    | TRIGGER: CONSOLI   | Ingresso alla Sala dell'Arengo / Comando      |
|   4    | TRIGGER: BARGELLO  | Transizione verso Quartiere San Martino       |
|   5    | TRIGGER: ROMANA    | Transizione verso Porta Romana (Fronte Est)   |
|   6    | FONTANA DEI MATTI  | Interazione (Pressione Tasto A: 'Patente')    |

> **NOTA DI REVISIONE (2026-08-18, Sessione 18d) — LA FONTANA NON E' IN PIAZZA GRANDE.**
> Correzione del committente, che conosce la citta': la **Fontana dei Matti (Fontana del
> Bargello)** si trova in **Largo del Bargello, lungo la salita di via dei Consoli**, davanti al
> Palazzo del Bargello — **non** dentro Piazza Grande. Questa legenda la elencava fra i tile
> della piazza, e il codice l'aveva ereditata: era in griglia alle celle (23-24, 24-25).
>
> Rimossa da `piazza_grande_collision.h`, con una `static_assert` che impedisce di rimetterla.
> Il valore di tile 6 resta definito per l'area **`MapId::LARGO_BARGELLO`**, dichiarata e non
> ancora autorata, dove staranno fontana e Palazzo del Bargello — e dove portera' il varco
> occidentale della piazza, che oggi apre provvisoriamente una battaglia.
>
> Vale la pena notare **come e' emerso**: nessuna verifica automatica poteva trovarlo, perche' il
> gioco funzionava benissimo con la fontana nel posto sbagliato. Serviva qualcuno che conoscesse
> Gubbio e guardasse lo schermo.
+-----------------------------------------------------------------------------+
```

---

### C. SCHEMA DELLA GRIGLIA SPAZIALE (64x40 TILE)

```
      0                                32                              63
   0  +----------------------------------------------------------------+
      |1111111111111111111111111111111111111111111111111111111111111111|
      |1111111111111111111111111111111111111111111111111111111111111111|
      |11111 [ PALAZZO DEI CONSOLI ] 11111111 [ PALAZZO PRETORIO ] 1111|
      |11111        (Y: 2-18)        11111111       (Y: 2-16)      1111|
      |1111111111111113311111111111111111111111111111111111111111111111|  <-- Y: 18 (Ingresso Consoli: 3)
      |444                                                           55|  <-- X: 0-2 (Bargello: 4), X: 61-63 (Romana: 5)
  20  |444     000000000000000000000000000000000000000000000000000   55|
      |        000000000000000000000000000000000000000000000000000     |
      |        00000000000 [66] 000000000000000000000000000000000      |  <-- Fontana dei Matti (6)
      |        00000000000 [66] 000000000000000000000000000000000      |
  30  |        000000000000000000000000000000000000000000000000000     |
      |        000000000000000000000000000000000000000000000000000     |
      |2222222222222222222222222222222222222222222222222222222222222222|  <-- Y: 38-39 (Ringhiera Sud: 2)
  39  |2222222222222222222222222222222222222222222222222222222222222222|
      +----------------------------------------------------------------+
```

---

### D. PARSER DELLE COLLISIONI IN C++20 (`scene_piazza_grande.h`)

> **NOTA DI REVISIONE (2026-08-18, Sessione 11).** Lo pseudocodice qui sotto resta a titolo
> illustrativo, ma l'implementazione reale — `include/piazza_grande_collision.h`,
> `include/overworld_player.h`, `include/scene_exploration.h` — se ne discosta su **tre punti**,
> per ragioni verificate:
>
> 1. **La hitbox e' 12x8 ancorata AI PIEDI, non il bounding box 16x16 centrato.** Con un riquadro
>    alto 16 centrato sullo sprite, per posare il centro sul portone dei Consoli (y=18) il bordo
>    superiore ricade su y=17, che la griglia restituisce come muro: **il portone sarebbe
>    letteralmente irraggiungibile**. Un personaggio visto dall'alto collide con i piedi.
> 2. **Il movimento e' provato ad ASSI SEPARATI** (prima X, poi Y) e non con un unico test sul
>    punto d'arrivo diagonale: con il test unico, camminare in diagonale contro un muro blocca
>    anche la componente libera e il personaggio si incolla all'ostacolo.
> 3. **Si campiona l'INTERVALLO di tile coperto, non i quattro angoli.** Con celle da 8 px e una
>    scatola da 12x8, un ostacolo largo un tile puo' stare interamente fra i quattro angoli e non
>    essere visto.
>
> Inoltre la firma `get_tile_type(const uint8_t*, int pixel_x, int pixel_y)` qui stampata e
> quella implementata `get_tile_type(int tile_x, int tile_y)` hanno, omettendo il puntatore, lo
> **stesso numero di argomenti dello stesso tipo ma unita' diverse** — un chiamante che segue
> questo documento sbaglierebbe di un fattore 8 senza errore di compilazione. Per questo la
> variante in pixel si chiama ora `get_tile_type_px()`: l'unita' e' nel nome. La scena
> dell'esplorazione e' `ExplorationScene`, parametrizzata da `MapId` e non una classe per mappa;
> `scene_piazza_grande.h` non esiste.

```cpp
// scene_piazza_grande.h - Gestione collisioni e transizioni Piazza Grande
#ifndef SCENE_PIAZZA_GRANDE_H
#define SCENE_PIAZZA_GRANDE_H

#include "bn_core.h"
#include "bn_fixed_point.h"
#include "campanone_audio.h"

namespace piazza_map {
    constexpr int MAP_WIDTH_TILES = 64;
    constexpr int MAP_HEIGHT_TILES = 40;
    constexpr int TILE_SIZE = 8;

    // Macro per calcolare il tipo di tile alle coordinate in pixel (X, Y)
    inline uint8_t get_tile_type(const uint8_t* collision_grid, int pixel_x, int pixel_y) {
        int tile_x = pixel_x / TILE_SIZE;
        int tile_y = pixel_y / TILE_SIZE;

        if(tile_x < 0 || tile_x >= MAP_WIDTH_TILES || tile_y < 0 || tile_y >= MAP_HEIGHT_TILES) {
            return 1; // Fuori mappa = solido
        }
        return collision_grid[tile_y * MAP_WIDTH_TILES + tile_x];
    }
}

class PiazzaScene {
private:
    int _player_x;
    int _player_y;
    bool _has_mad_patent;

public:
    PiazzaScene() : _player_x(256), _player_y(200), _has_mad_patent(false) {}

    bool can_move_to(const uint8_t* collision_grid, int target_x, int target_y) {
        // Verifica il bounding box del player (16x16 pixel centrato)
        uint8_t top_left     = piazza_map::get_tile_type(collision_grid, target_x - 7, target_y - 7);
        uint8_t top_right    = piazza_map::get_tile_type(collision_grid, target_x + 7, target_y - 7);
        uint8_t bottom_left  = piazza_map::get_tile_type(collision_grid, target_x - 7, target_y + 7);
        uint8_t bottom_right = piazza_map::get_tile_type(collision_grid, target_x + 7, target_y + 7);

        // Se un angolo interseca un solido (1) o la ringhiera (2), il movimento è bloccato
        if(top_left == 1 || top_left == 2 || top_right == 1 || top_right == 2 ||
           bottom_left == 1 || bottom_left == 2 || bottom_right == 1 || bottom_right == 2) {
            return false;
        }
        return true;
    }

    void handle_tile_events(uint8_t tile_type) {
        switch(tile_type) {
            case 3: // Ingresso Palazzo dei Consoli
                CampanoneAudio::play_strike();
                // Transizione scena Sala Consiliare
                break;
            case 4: // Verso San Martino / Bargello
                // Carica mappa Quartiere San Martino
                break;
            case 5: // Verso Porta Romana
                // Carica mappa Fronte Est / Assedio
                break;
            case 6: // Fontana dei Matti
                _has_mad_patent = true; // Buff Velocità attivo
                break;
            default:
                break;
        }
    }
};

#endif
```


---

## 22. IMPLEMENTAZIONE DUNGEON: LA GOLA DEL BOTTACCIONE & IL CONDOTTO PENSILE

Questa sezione definisce la matrice di collisione, i pericoli ambientali e le meccaniche stealth per il secondo dungeon principale: la discesa sotterranea lungo l'acquedotto medievale sospeso.

---

### A. SPECIFICHE TECNICHE DELLA MAPPA
* **Dimensioni Totali:** $32 \times 128\text{ tile}$ ($256 \times 1024\text{ pixel}$ a scorrimento prettamente verticale).
* **Layer Grafici (Mode 0):**
  * **BG3:** Parete del canyon calcareo con strato scuro K-T (Iridio).
  * **BG2:** Ponte pensile in pietra dell'Acquedotto ($2\text{ tile}$ di larghezza = $16\text{ px}$) e passerelle in legno.
  * **BG1:** Cascate d'acqua animate e archi di contrafforte sotto cui nascondersi.
* **Pericolo Ambientale (Miasmi di Cagli):**
  * Zone contrassegnate con nebbia verde: il party subisce $5\text{ HP}$ di danno ogni 3 secondi se non protetto dalla *Benedizione Liturgica* di Sant'Ubaldo.

---

### B. MATRICE DELLE COLLISIONI DEL BOTTACCIONE (`bottaccione_map.h`)

```cpp
// bottaccione_map.h - Matrice e pericoli della Gola del Bottaccione
#ifndef BOTTACCIONE_MAP_H
#define BOTTACCIONE_MAP_H

#include "bn_core.h"

namespace bottaccione {
    constexpr int WIDTH = 32;
    constexpr int HEIGHT = 128;

    enum TileType : uint8_t {
        VOID_FALL     = 0, // Strapiombo (caduta: -15 HP e respawn a inizio ponte)
        STONE_BRIDGE  = 1, // Calpestabile sicuro
        WOOD_PLANK    = 2, // Legno fragile (crolla dopo 2 secondi di sosta)
        TOXIC_MIASMA  = 3, // Zona velenosa di Valerio di Cagli
        STEALTH_ARCH  = 4, // Nascondiglio (invisibile alle ronde nemiche)
        BOSS_TRIGGER  = 5  // Ingresso arena Boss Valerio di Cagli
    };
}

#endif
```

---

## 23. SPECIFICHE DEGLI SPRITE SHEET & TABELLA DELLE ANIMAZIONI (TRE CERI)

Per garantire animazioni fluide a 60 FPS stile *Golden Sun*, ogni personaggio dispone di una tabella di animazione standardizzata a 4 direzioni (Overworld) e pose di battaglia (Side-View).

---

### A. FORMATO FILE GRAFICI & LAYOUT SHEET

* **Formato:** File `.png` indicizzato a 16 colori (Palette 0 trasparente).
* **Dimensioni Frame:**
  * **San Giorgio:** $32 \times 32\text{ px}$ (inclusa lancia e scudo).
  * **Sant'Ubaldo:** $16 \times 32\text{ px}$ (inclusa mitra e pastorale).
  * **Sant'Antonio:** $16 \times 32\text{ px}$ (incluso bastone a tau e cinghiale di supporto).

```
+-----------------------------------------------------------------------------+
|               LAYOUT SPRITE SHEET OVERWORLD (4 FRAME WALK CYCLE)            |
|                                                                             |
|  [Frame 0: Giù-1]   [Frame 1: Giù-2]   [Frame 2: Giù-3]   [Frame 3: Giù-4]  |
|  [Frame 4: Su-1]    [Frame 5: Su-2]    [Frame 6: Su-3]    [Frame 7: Su-4]   |
|  [Frame 8: Sin-1]   [Frame 9: Sin-2]   [Frame 10: Sin-3]  [Frame 11: Sin-4] |
|  [Frame 12: Des-1]  [Frame 13: Des-2]  [Frame 14: Des-3]  [Frame 15: Des-4] |
+-----------------------------------------------------------------------------+
```

---

### B. TABELLA POSE DI BATTAGLIA (SIDE-VIEW BATTLE SHEET)

| ID Posa | Nome Animazione | Numero Frame | Descrizione Visiva |
| :--- | :--- | :--- | :--- |
| **0** | `IDLE_STANCE` | 4 frame loop | Respiro e oscillazione arma a 8 FPS |
| **1** | `MELEE_ATTACK` | 6 frame | Scatto in avanti, affondo lancia (Giorgio) o colpo pastorale |
| **2** | `CAST_SPELL` | 5 frame | Sollevamento reliquia con alone di luce/fuoco attorno alle mani |
| **3** | `TAKE_HIT` | 2 frame | Rinculo all'indietro e lampeggio bianco della palette |
| **4** | `GUARD_SHIELD` | 3 frame loop | San Giorgio piazza lo scudo a terra con scintille azzurre |
| **5** | `VICTORY_CHEER` | 4 frame loop | Sollevamento del fazzoletto ceraiolo al cielo |

---

### C. IMPLEMENTAZIONE CONTROLLER ANIMAZIONI (`hero_animator.h`)

```cpp
// hero_animator.h - Gestione animazioni sprite con Butano Engine
#ifndef HERO_ANIMATOR_H
#define HERO_ANIMATOR_H

#include "bn_sprite_ptr.h"
#include "bn_sprite_animate_actions.h"
#include "bn_sprite_items_hero_giorgio.h"

class HeroAnimator {
private:
    bn::sprite_ptr _sprite;
    bn::sprite_animate_action<4> _walk_action;
    bool _is_moving;

public:
    HeroAnimator(bn::fixed x, bn::fixed y) :
        _sprite(bn::sprite_items::hero_giorgio.create_sprite(x, y)),
        _walk_action(bn::create_sprite_animate_action_forever(
            _sprite, 8, bn::sprite_items::hero_giorgio.tiles_item(), 0, 1, 2, 3)),
        _is_moving(false) {}

    void set_direction(int direction_id, bool moving) {
        _is_moving = moving;
        int base_tile = direction_id * 4;

        if(_is_moving) {
            _walk_action = bn::create_sprite_animate_action_forever(
                _sprite, 8, bn::sprite_items::hero_giorgio.tiles_item(),
                base_tile, base_tile + 1, base_tile + 2, base_tile + 3);
        } else {
            _walk_action = bn::create_sprite_animate_action_forever(
                _sprite, 8, bn::sprite_items::hero_giorgio.tiles_item(),
                base_tile, base_tile, base_tile, base_tile);
        }
    }

    void update() {
        if(_is_moving) {
            _walk_action.update();
        }
    }

    void set_position(bn::fixed x, bn::fixed y) {
        _sprite.set_position(x, y);
    }
};

#endif
```


---

## 24. SISTEMA DI SALVATAGGIO NON-VOLATILE SU FRAM (256 Kbit / SRAM GBA)

Per garantire la persistenza dei dati senza l'uso di batterie tampone deperibili, il salvataggio è strutturato su chip FRAM da 32 KB (256 Kbit) con allocazione a dimensione fissa, dual-slot (Slot 1 / Slot 2) e calcolo di checksum CRC32 per la protezione da corruzione.

---

### A. STRUTTURA DATI SERIALIZZABILE (`save_data.h`)

```cpp
#ifndef SAVE_DATA_H
#define SAVE_DATA_H

#include "bn_core.h"
#include "bn_sram.h"

struct HeroSaveState {
    uint16_t current_hp;
    uint16_t current_fervor;
    uint8_t  level;
    uint8_t  equipped_weapon_id;
    uint8_t  equipped_armor_id;
    uint8_t  equipped_relic_id;
};

struct SaveData {
    char     magic_header[4];     // "G1151"
    uint32_t save_timestamp;      // Tempo totale di gioco in secondi
    uint8_t  current_act;         // Atto I, II, III o IV
    uint8_t  current_map_id;      // 0: Piazza Grande, 1: Bottaccione, 2: Mura, 3: Piana
    int16_t  player_pos_x;        // Coordinate su mappa
    int16_t  player_pos_y;
    HeroSaveState party[3];       // Ubaldo, Giorgio, Antonio
    uint8_t  inventory_items[32]; // ID e conteggio consumabili
    uint32_t story_flags;         // Maschera di bit per quest e dialoghi
    uint8_t  quartieri_reputation[4]; // San Martino, Sant'Andrea, San Pietro, San Giuliano
    uint32_t checksum;            // CRC32 calcolato sul payload
};

class SaveSystem {
public:
    static constexpr int SAVE_SLOT_SIZE = sizeof(SaveData);

    static bool write_save(int slot_index, const SaveData& data) {
        int sram_offset = slot_index * SAVE_SLOT_SIZE;
        bn::sram::write_offset(data, sram_offset);
        return true;
    }

    static bool read_save(int slot_index, SaveData& out_data) {
        int sram_offset = slot_index * SAVE_SLOT_SIZE;
        bn::sram::read_offset(out_data, sram_offset);
        
        // Verifica del Magic Header
        if(out_data.magic_header[0] != 'G' || out_data.magic_header[1] != '1') {
            return false;
        }
        return true;
    }
};

#endif
```

---

## 25. UI/UX, FONT PROPORZIONALE & MOTORE DIALOGHI (TEXT BOX TYPEWRITER)

Il sistema visuale sfrutta il layer hardware **BG0** (Priorità 0) per visualizzare una text box a 8-bit con sfondo semitrasparente scuro e bordi decorati con i motivi geometrici delle formelle di Palazzo dei Consoli.

---

### A. SPECIFICHE DEL MOTORE DI TESTO
* **Font Compatto a 8 px:** Set di caratteri proporzionale ottimizzato per la risoluzione $240 	imes 160$ px (fino a 28 caratteri per riga, massimo 3 righe per box).

> **NOTA DI REVISIONE (2026-08-18, Sessione 12) — IL FONT ITALIANO ESISTE.**
> Questa sezione dava per scontato un set di caratteri adeguato all'italiano. Non lo era: il font
> usato fino alla Sessione 11, `common_variable_8x8_sprite_font` di Butano, mappa 16 caratteri non
> ASCII e sono **tutti spagnoli** (`Á É Í Ó Ú Ü Ñ á é í ó ú ü ñ ¡ ¿`) — **nessun accento grave
> italiano**. Un carattere non mappato non e' un errore di compilazione: e' un `BN_ERROR` a
> runtime, cioe' il gioco che si ferma davanti al giocatore alla prima battuta con "città".
>
> **Decisione: font 8x8 proprio del progetto**, `graphics/font_gubbio.bmp` + `include/font_gubbio.h`,
> generato da `tools/make_font.py`. Contiene i 94 glifi ASCII di Butano piu' le **12 lettere
> accentate italiane** (`à è é ì ò ù À È É Ì Ò Ù`). Le misure che hanno determinato la forma:
> * le **minuscole** avevano gia' lo spazio (3 righe libere sopra `a`, `o`, `u`; 2 sopra `e`),
>   quindi sono **derivate senza ridisegnare nulla**; sulla `i` l'accento prende il posto del
>   puntino, come vuole la tipografia;
> * le **maiuscole** occupavano tutte e 8 le righe, quindi si toglie la riga la cui rimozione si
>   nota di meno — per `A I O U` esiste una riga duplicata e la compressione e' esatta, per `E` il
>   costo misurato e' di 2 pixel — e l'accento e' un trattino di 3 px sulla riga liberata.
>   La compressione piu' aggressiva (a 6 righe) e' stata **provata e scartata**: accanto alle
>   altre maiuscole la lettera appariva rimpicciolita.
>
> Conseguenze applicate: il Battle HUD usa lo stesso font (il menu comandi dice ora **"Abilità"**),
> la libreria `../butano/common` e' stata **rimossa dal `Makefile`** perche' serviva solo al font,
> e `tools/preview_battle_screen.py` rende con il medesimo font della ROM. Un test della suite
> verifica che **ogni carattere delle stringhe dei sorgenti esista nel font**.
>
> Resta valido il resto della sezione: 8 px di altezza, fino a 28 caratteri per riga, 3 righe.
>
> **NOTA DI REVISIONE (2026-08-18, Sessione 13) — il motore di testo esiste ed e' eseguito.**
> `include/dialogue_box.h` (stato e macchina da scrivere) e `include/dialogue_view.h` (cornice e
> sprite) sono implementati e collaudati su emulatore. Due precisazioni che questa sezione rendeva
> ambigue:
> * **"BG0 visualizza la text box" va letto cosi': la CORNICE sta su BG0, il TESTO sta sugli
>   sprite.** In Butano il testo e' fatto di sprite (OAM) e non di tile di background: alla
>   lettera la frase non e' realizzabile. Misurato: tre righe di prosa italiana costano **15
>   sprite e 120 tile OBJ**; il tetto che si tocca per primo non sono i tile (1024) ma le 128
>   allocazioni distinte di `BN_CFG_SPRITE_TILES_MAX_ITEMS`.
> * **Righe per battuta: 3, non 2.** Questa sezione dice "massimo 3 righe per box", mentre la
>   struttura `DialogueNode` della Sez. 31C ne prevede due (`text_line_1`, `text_line_2`).
>   Si adotta il 3 di questa sezione, che e' quella che descrive il motore; la 31C andra'
>   allineata quando si scriveranno le tabelle del copione (Passo 17).
>
> Le coordinate della finestra **non sono fissate in alcun punto del GDD**: sono state scelte
> nell'implementazione (testo a x=14, prima riga y=118, interlinea 13 px) riusando la fascia bassa
> gia' quotata per l'HUD di battaglia (y 112-160, Sez. 14B.1).
* **Effetto Macchina da Scrivere (Typewriter):** 1 carattere ogni 2 frame hardware (30 caratteri al secondo), con possibilità di skip istantaneo premendo il tasto $B$.
* **Speaker Indicator & Bip Vocale Chiptune:** Pitch audio modulato in base a chi parla (grave/solenne per Sant'Ubaldo, squillante per San Giorgio, cupo/roco per Sant'Antonio, metallico/minaccioso per Monaldo).

---

### B. IMPLEMENTAZIONE DIALOGUE MANAGER (`dialogue_box.h`)

```cpp
#ifndef DIALOGUE_BOX_H
#define DIALOGUE_BOX_H

#include "bn_core.h"
#include "bn_string_view.h"
#include "bn_sprite_text_generator.h"
#include "bn_keypad.h"

enum class Speaker { UBALDO, GIORGIO, ANTONIO, MONALDO, CITIZEN };

class DialogueManager {
private:
    bn::string_view _current_text;
    int _visible_chars;
    int _frame_counter;
    bool _is_active;

public:
    DialogueManager() : _visible_chars(0), _frame_counter(0), _is_active(false) {}

    void show_message(Speaker speaker, bn::string_view text) {
        _current_text = text;
        _visible_chars = 0;
        _frame_counter = 0;
        _is_active = true;
    }

    void update() {
        if(!_is_active) return;

        // Skip testo con tasto B
        if(bn::keypad::b_pressed()) {
            _visible_chars = _current_text.size();
        }

        // Avanzamento carattere
        if(_visible_chars < _current_text.size()) {
            _frame_counter++;
            if(_frame_counter % 2 == 0) {
                _visible_chars++;
            }
        }

        // Chiusura con tasto A quando il testo è completo
        if(_visible_chars >= _current_text.size() && bn::keypad::a_pressed()) {
            _is_active = false;
        }
    }

    [[nodiscard]] bool is_active() const { return _is_active; }
};

#endif
```

---

## 26. INTELLIGENZA ARTIFICIALE & SCRIPT DELLE BOSS FIGHT

I boss non agiscono in modo casuale: seguono una tabella di priorità e transizioni di stato legate ai loro Punti Scudo (Shield Break) e alla percentuale di HP rimanenti.

---

### A. CORRADO DI SPOLETO (IL TITANO DELLE FORGE - ATTO II)
* **Punti Scudo Base:** 4.
* **Debolezza Meccanica:** Immune al danno da taglio finché non viene applicato lo status *Ustione Alchemica* di Sant'Antonio.
* **Routine Comportamentale:**
  * *Turno 1:* Attiva *Scudo di Forgia* (Aumenta Difesa del 50%).
  * *Turno 2:* *Martello d'Assedio* su San Giorgio (Danno fisico colossale a target singolo).
  * *Se in BREAK:* Salta il turno e la sua resistenza al fuoco scende a zero.

---

### B. VALERIO DI CAGLI (L'ALCHIMISTA DEI MIASMI - ATTO II)
* **Punti Scudo Base:** 3.
* **Routine Comportamentale:**
  * *Ciclo Tossico:* Alterna *Nube di Pece* (applica Veleno a tutto il party) e colpi a distanza con la cerbottana su Sant'Ubaldo.
  * *Fase Difensiva (<50% HP):* Evoca due balestrieri mercenari a fargli da scudo e si posiziona nella colonna posteriore.

---

### C. I GEMELLI DELLA TEMPESTA (FOLIGNO & TODI - ATTO III)
* **Punti Scudo Base:** 3 ciascuno.
* **Sinergia:**
  * Il Boss di Foligno lancia folate di vento che raddoppiano la velocità del fratello.
  * Il Boss di Todi scaglia frecce fulminee a raffica.
  * *Condizione Chiave:* Quando uno dei due viene sconfitto, il superstite assorbe l'elemento del compagno caduto ed entra in modalità *Berserk* permanente (+50% Attacco).

---

### D. MONALDO DA PERUGIA & L'AVATAR DEL GRIFO (BOSS FINALE - ATTO IV)

```
[ FASE 1: Monaldo Umano ] ──(0 HP)──> [ FASE 2: Volo del Grifo ] ──(Ali Bruciate)──> [ FASE 3: Forma Terrena ]
  - Punti Scudo: 5                      - Punti Scudo: 6 (Fuori Portata)                - Punti Scudo: 4
  - Spadone d'Ombra                     - Tempesta di Sangue                            - Ruggito dell'Ingino
  - Contrattacco Marziale               - Richiede Fuoco di Antonio                     - Danno a Tutto Campo
```

* **Fase 1 (Monaldo di Ferro):** Combatte a terra con affondi pesanti e parate reattive.
* **Fase 2 (La Metamorfosi):** Sacrifica il sangue dei luogotenenti e si trasforma nel Grifo Araldico volante, bersagliabile solo dalle magie a distanza di Antonio e Ubaldo.
* **Fase 3 (L'Impatto al Suolo):** Caduto a terra con le ali bruciate, scatena l'attacco supremo *Apocalisse dei Colli*, contrastabile solo attivando il *Muro della Fede* o l'*Alzata Trionfale dei Tre Ceri*.

---

## 27. ASSET PIPELINE & AUTOMAZIONE BUILD (PYTHON & CLAUDE CODE WORKFLOW)

Per rendere la pipeline autonoma e compilabile con Claude Code da terminale:

---

### A. SCRIPT DI CONVERSIONE TILEMAP -> MASCHERA C++ (`tools/map_exporter.py`)

Questo script legge una mappa esportata da *Tiled* (formato `.json` o `.csv`) e genera direttamente l'array statico `uint8_t` in un file header C++ per Butano:

```python
#!/usr/bin/env python3
import json
import sys

def export_map_header(json_file, output_header):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    layer = data['layers'][0] # Prende il primo layer di collisione
    width = layer['width']
    height = layer['height']
    raw_data = layer['data']

    with open(output_header, 'w') as out:
        out.write(f"// Generato automaticamente da map_exporter.py
")
        out.write(f"#ifndef COLLISION_DATA_H
#define COLLISION_DATA_H

")
        out.write(f"#include <stdint.h>

")
        out.write(f"constexpr int MAP_WIDTH = {width};
")
        out.write(f"constexpr int MAP_HEIGHT = {height};

")
        out.write(f"constexpr uint8_t COLLISION_MAP[{width * height}] = {{
    ")
        
        for i, val in enumerate(raw_data):
            out.write(f"{val}, ")
            if (i + 1) % width == 0:
                out.write("
    ")
        
        out.write("};

#endif
")
    print(f"Header {output_header} generato con successo ({width}x{height} tile).")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        export_map_header(sys.argv[1], sys.argv[2])
```

---

### B. COMANDI DI BUILD & TEST AUTOMATIZZATI

* **Compilazione Completa ROM:**
  ```bash
  make -j$(nproc)
  ```
* **Esecuzione Immediata su mGBA (con logging gdb/debug):**
  ```bash
  mgba-qt gubbio1151.gba
  ```
* **Pipelined Asset Build (Asset -> Code -> ROM):**
  ```bash
  python3 tools/map_exporter.py assets/maps/piazza.json include/piazza_collision.h && make
  ```


---

## 28. ART DIRECTION, GUIDA ESTETICA & PALETTE SHADING PER GBA

Per garantire che l'atmosfera Dark Fantasy medievale di Gubbio risulti leggibile, materica e fedele all'hardware 15-bit del Game Boy Advance ($240 \times 160$ px a 32.768 colori), l'estetica adotta standard visivi rigorosi:

---

### A. IDENTITÀ CROMATICA & ILLUMINAZIONE AMBIENTALE
* **La Pietra Calcarea Eugubina (Tone Mapping):** 
  * I muri dei palazzi storici usano una rampa cromatica a 4 toni: grigio freddo in ombra, ocra chiaro alla luce e bianco caldo per i riflessi solari.
* **Il Contrasto del Vermiglio Comunale:**
  * I 4 stemmi dei quartieri e i drappi cittadini utilizzano il rosso vivo saturo, che stacca nettamente dal grigio della pietra.
* **Effetto Giorno / Notte & Nebbia Dinamica:**
  * Sfruttamento delle *Color Effects* hardware del GBA (Alpha Blending tra Layer BG1/BG2 e BG3):
    * **Giorno (Atti I e III):** Illuminazione neutra con contrasto medio.
    * **Notte/Bottaccione (Atto II):** Filtro bluastro/antracite sui layer di sfondo, torce animate con flickering su layer sprite.
    * **Sortita all'Alba (Atto IV):** Layer BG0 o BG1 con alpha blending al 50% di bianco nebbioso semitrasparente, squarciato dalle luci dell'Albero/Faro dell'Ingino.

---

### B. PROPORZIONI SPRITE & SCALING MODE 7
* **Overworld:** Sprite da $16 \times 32$ px (Ubaldo/Antonio) e $32 \times 32$ px (Giorgio su armatura).
* **Battaglia (Side-View):** Sprite eroi a $32 \times 48$ px con animazioni fluide a 8 FPS; boss (Corrado, Gemelli, Grifo) su frame da $64 \times 64$ px con gestione affine (zoom/rotazione Mode 7 durante le abilità supreme).

---

## 29. DURATA DEL GIOCO, PACING DEI CONTENUTI & PROGRESSIONE ORE

Per una cartuccia flash ROM da 32MB, la durata è calibrata sul modello classico dei grandi RPG tattici per Game Boy Advance (*Golden Sun / Fire Emblem*):

| Fase / Capitolo | Durata Stimata | Livello Party | Obiettivo Primario / Contenuti |
| :--- | :--- | :--- | :--- |
| **Prologo & Atto I (La Chiamata)** | $\approx 1.5 - 2\text{ ore}$ | Liv. 1 - 5 | Esplorazione Piazza Grande, salita Monte Ingino, risveglio dei Tre Ceri. |
| **Atto II (Guerra nell'Ombra)** | $\approx 3.0 - 4\text{ ore}$ | Liv. 5 - 10 | Dungeon del Bottaccione, Eremo di Sant'Ambrogio, Boss Valerio e Corrado. |
| **Atto III (L'Assedio alle Mura)** | $\approx 3.5 - 4.5\text{ ore}$ | Liv. 10 - 15 | Difesa a ondate di Porta Romana/San Pietro, Boss Gemelli di Foligno/Todi. |
| **Atto IV (La Sortita & Finale)** | $\approx 2.5 - 3.5\text{ ore}$ | Liv. 15 - 20 | Accampamento nemico nella piana, Boss Finale Monaldo / Avatar del Grifo. |
| **Contenuti Extra / Post-Game** | $\approx 2.0 - 3.0\text{ ore}$ | Liv. 20 (Cap) | Cripte del Duomo, 7 Tavole Eugubine, sfide al Cassero della Rocca. |
| **DURATA TOTALE** | **$\approx 12 - 17\text{ ORE}$** | **Completo** | **Esperienza RPG narrativa densa e priva di padding artificiale.** |

---

## 30. SETUP AUTOMATICO DEL PROGETTO: BASH INITIALIZER SCRIPT

Questo script automatizza l'intera creazione dell'albero cartelle, del `Makefile`, degli script di conversione e dell'entry point C++ `main.cpp`:

```bash
#!/usr/bin/env bash
set -e

PROJECT_NAME="gubbio1151_gba"
echo "Inizializzazione progetto: $PROJECT_NAME..."

mkdir -p "$PROJECT_NAME"/{src,include,graphics,audio/sound_effects,audio/music,tools,build}

# 1. Creazione Makefile
cat << 'EOF' > "$PROJECT_NAME/Makefile"
TARGET := gubbio1151
BUILD := build
SOURCES := src
INCLUDES := include
GRAPHICS := graphics
AUDIO := audio

include $(BUTANO_PATH)/butano.mak
EOF

# 2. Creazione main.cpp
cat << 'EOF' > "$PROJECT_NAME/src/main.cpp"
#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_display.h"

int main()
{
    bn::core::init();

    while(true)
    {
        bn::core::update();
    }
}
EOF

echo "Setup completato con successo in ./$PROJECT_NAME/"
```


---

## 31. DATABASE COMPLETO DEGLI NPC, DIALOGHI RAMIFICATI & QUEST SECONDARIE (I 4 QUARTIERI)

Questa sezione censisce tutti i personaggi non giocanti (NPC) distribuiti nella città di Gubbio e nei suoi sobborghi, con i relativi alberi di dialogo (formato GBA text-box) e le quest secondarie legate alla reputazione dei 4 Quartieri.

---

### A. MATRICE DELLE MISSIONI SECONDARIE DEI 4 QUARTIERI

Il completamento delle quest dei quartieri non conferisce solo esperienza e oggetti, ma determina il livello di fortificazione e i rinforzi ausiliari durante la difesa delle mura nell'Atto III.

```
+-----------------------------------------------------------------------------+
| REPUTAZIONE DEI 4 QUARTIERI & RINFORZI DIFESA MURA (ATTO III)               |
|                                                                             |
| [San Martino]  -> Rinforza le armature dei Fanti (+20% Difesa Fisica Mura)  |
| [Sant'Andrea]  -> Gilda Speziali: Dispensa Pozioni & Antidoti ogni 3 turni  |
| [San Pietro]   -> Ordine Chierici: Ricarica Fervore continua alle Porte     |
| [San Giuliano] -> Rete Spie: Rallenta le Torri Mobili di Spoleto e Cagli    |
+-----------------------------------------------------------------------------+
```

| ID Quest | Quartiere | Nome Missione | NPC Datore | Obiettivo / Dinamica | Ricompensa |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Q-SM01** | San Martino | *Il Ferro del Monte Calvo* | **Mastro Raniero** (Fabbro) | Recuperare 3 blocchi di ferro fuso dalle fornaci occupate da Cagli. | *Corazza Rinforzata* per Giorgio (+15 Def) + Scudi Mura. |
| **Q-SA01** | Sant'Andrea | *Le Erbe del Bottaccione* | **Monna Agnese** (Speziale) | Raccogliere 4 radici di elleboro selvatico nella gola prima che i miasmi le brucino. | *Balsamo di Sant'Andrea* (Cura totale veleno) + Rifornimenti medici. |
| **Q-SP01** | San Pietro | *La Rosa d'Argento Scomparsa* | **Fra' Bernardo** (Priore) | Ritrovare il reliquiario della Rosa rubato da un infiltrato perugino nelle cripte. | *Spilla della Rosa* (+20 Fervore iniziale) + Benedizione Porta Vittoria. |
| **Q-SG01** | San Giuliano | *Occhi sui Mercatali* | **Giacomo il Gufo** (Spia) | Decifrare i segnali luminosi dei mercenari perugini accampati a sud. | *Mappa dei Cunicoli* (Scorciatoia stealth) + Trappole d'arresto. |
| **Q-CIV01**| Piazza Grande | *I Tre Sorsi del Matto* | **Mastro Tano** (Bargello) | Eseguire il rito dei tre giri attorno alla fontana rispondendo ai suoi enigmi. | *Patente da Matto* (Buff velocità + Schivata) |

---

### B. REGISTRO DETTAGLIATO DEGLI NPC & SCRIPT DEI DIALOGHI

#### 1. Area Piazza Grande & Complesso Consolare

* **NPC 1: Il Podestà Guido da Gubbio**
  * *Ruolo:* Capo del governo cittadino e snodo delle missioni principali degli Atti I e III.
  * *Dialogo (Atto I - Pre-Digiuno):*
    > **PODESTÀ GUIDO:**  
    > "Monsignore... undici stendardi circondano la conca. Le nostre milizie sono poche, e le scorte di grano a Palazzo Pretorio basteranno per una settimana. Se non troviamo un miracolo, cadremo prima dell'estate."  
    > **SANT'UBALDO:**  
    > "Non contare le lance dei perugini, Guido. Conta la fede di chi abita queste pietre. Fate sprangare le porte e ordinate alla città tre giorni di silenzio e digiuno."
  * *Dialogo (Atto III - Assedio in corso):*
    > **PODESTÀ GUIDO:**  
    > "Porta Romana sta cedendo sotto i colpi dei mangani di Foligno! Giorgio, guida i balestrieri sui camminamenti prima che aprano una breccia!"

* **NPC 2: Mastro Tano del Bargello (Custode della Fontana dei Matti)**
  * *Ruolo:* Guardiano folcloristico, abilita il rito della *Patente da Matto*.
  * *Dialogo d'ingaggio:*
    > **MASTRO TANO:**  
    > "Fermati, cavaliere! Nessuno passa davanti al Bargello senza dimostrare la follia sacra di chi ama questa terra più della propria vita! Sei pronto a compiere i tre giri e a bagnarti la fronte?"  
    > **[SCELTA: 1. Fai i tre giri / 2. Tira dritto]**  
    > *(Se 1):* *"Che l'acqua della fonte liberi il tuo braccio dalla paura! Eccoti la patente, ceraiolo!"*

---

#### 2. Quartiere San Martino (La Fazione della Corona)

* **NPC 3: Mastro Raniero (Il Maestro Ferraio)**
  * *Posizione:* Bottega d'armi nei vicoli alti di San Martino.
  * *Dialogo (Quest Q-SM01):*
    > **MASTRO RANIERO:**  
    > "Le mie fornaci sono spente, ragazzo. Le truppe di Spoleto hanno bloccato i carichi di carbone e minerale al passo. Se mi riporti il ferro sequestrato alle fornaci basse, forgerò per Giorgio un pettorale che nessun dardo potrà scalfire."

* **NPC 4: Berto il Tagliapietre**
  * *Ruolo:* NPC di lore, fornisce dettagli sulle gallerie segrete dell'acquedotto.
  * *Dialogo:*
    > **BERTO:**  
    > "Mio nonno ha scalpellato la pietra del Condotto nel Bottaccione. Diceva sempre: *'C'è una fessura dove la roccia diventa nera come la pece... lì la terra non dorme'*. Fate attenzione se scendete laggiù."

---

#### 3. Quartiere Sant'Andrea (La Fazione delle Palme)

* **NPC 5: Monna Agnese (L'Erborista della Spina)**
  * *Posizione:* Orto botanico a ridosso dell'Abbazia di Sant'Andrea.
  * *Dialogo (Quest Q-SA01):*
    > **MONNA AGNESE:**  
    > "Gli alchimisti di Cagli stanno riversando veleno nel fosso. I feriti alle porte hanno le labbra viola e le bende non bastano. Mi serve l'elleboro che cresce solo sulle rocce umide del Bottaccione, o non supereranno la notte."

* **NPC 6: Fra' Matteo il Pescatore**
  * *Ruolo:* Mercante di consumabili ittici (Baccalà e salse cerConsistency).
  * *Dialogo:*
    > **FRA' MATTEO:**  
    > "Il Camignano è torbido, ma le riserve del convento sono piene. Prendi questo baccalà con prugne: basta un boccone per restituire il fiato anche dopo cento colpi di lancia."

---

#### 4. Quartiere San Pietro (La Fazione della Rosa)

* **NPC 7: Fra' Bernardo (Il Priore di San Pietro)**
  * *Posizione:* Chiostro dell'Abbazia di San Pietro.
  * *Dialogo (Quest Q-SP01):*
    > **FRA' BERNARDO:**  
    > "Hanno profanato l'altare, Vescovo Ubaldo! Una spia infiltrata ha sottratto la Rosa d'Argento con cui benediciamo i miliziani prima della guardia notturna. Senza di essa, gli uomini tremano di fronte ai vessilli del Grifo."

* **NPC 8: Lucia la Tessitrice dei Ceri**
  * *Ruolo:* Sarta sacra; forgia gli accessori per Fervore e i Fazzoletti Ceraioli.
  * *Dialogo:*
    > **LUCIA:**  
    > "Ogni punto di filo rosso trattiene una preghiera. Tieni Giorgio, allaccia questo fazzoletto al collo: quando il colpo nemico sarà mortale, il Santo ti concederà un secondo battito."

---

#### 5. Quartiere San Giuliano (La Fazione del Falcone)

* **NPC 9: Giacomo il Gufo (Il Falconiere dei Nobili)**
  * *Posizione:* Torre d'avvistamento di Porta San Giuliano.
  * *Dialogo (Quest Q-SG01):*
    > **GIACOMO:**  
    > "I miei falchi vedono tutto dalla cima del Monte Calvo. Monaldo non attaccherà da nord: sta preparando le catapulte mobili proprio di fronte a Porta San Pietro. Se mi portate i cifrari delle staffette nemiche, saboteremo le loro ruote prima dell'alba."

* **NPC 10: Cecco il Balestriere Scelto**
  * *Ruolo:* Addestratore del party; sblocca le abilità di perforazione armature di Giorgio.
  * *Dialogo:*
    > **CECCO:**  
    > "Un cavaliere senza mira è solo un bersaglio di latta. Guarda la giuntura sotto la spallaccia: è lì che devi piantare la punta della lancia se vuoi abbattere i titani di Spoleto in un solo affondo."

---

### C. IMPLEMENTAZIONE STRUTTURE DATI NPC IN C++ (`npc_registry.h`)

```cpp
#ifndef NPC_REGISTRY_H
#define NPC_REGISTRY_H

#include "bn_string_view.h"
#include "bn_vector.h"

struct DialogueNode {
    bn::string_view speaker_name;
    bn::string_view text_line_1;
    bn::string_view text_line_2;
    uint8_t required_act;
    uint8_t quest_trigger_id; // 0 se nessun trigger
};

struct NPCData {
    uint8_t npc_id;
    bn::string_view name;
    int world_x;
    int world_y;
    uint8_t map_id;
    uint8_t default_sprite_id;
    bn::vector<DialogueNode, 4> dialogues;
};

// Esempio di inizializzazione statica per memoria ROM GBA
constexpr NPCData NPC_DATABASE[] = {
    {
        1, "Podestà Guido", 256, 180, 0, 10,
        {
            {"Podestà Guido", "Undici stendardi ci stringono,", "dobbiamo resistere a ogni costo!", 1, 0},
            {"Podestà Guido", "Porta Romana sta cedendo!", "Giorgio, corri sui camminamenti!", 3, 0}
        }
    },
    {
        2, "Mastro Raniero", 60, 120, 0, 11,
        {
            {"Mastro Raniero", "Le fornaci sono spente. Riportami", "il ferro sequestrato a valle.", 2, 1}
        }
    }
};

#endif
```


---

## 32. ICONA DEL GIOCO, HEADER CARTUCCIA & METADATI GBA

Per garantire la compatibilità con emulatori, flashcard (Everdrive, EZ-Flash) e frontend digitali (Analogue Pocket, GBA Player), vengono definiti gli asset d'identità visiva della cartuccia.

---

### A. METADATI HEADER INTERNO GBA (OFFSET 0x0A0 - 0x0BF)
* **Game Title (12 Char):** `GUBBIO 1151 ` (spaziati a 12 byte)
* **Game Code (4 Char):** `BGUB`
* **Maker Code (2 Char):** `01` (Nintendo/Homebrew Indipendente)
* **Software Version:** `0x01` (v1.0)
* **Complement Checksum:** Calcolato automaticamente da `gbafix`.

---

### B. ASSET GRAFICI DELL'ICONA & BOXART
* **Icona Cartuccia (Analogue Pocket / Everdrive .bin / Frontend):**
  * Risoluzione: $32 \times 32\text{ px}$ e $48 \times 48\text{ px}$ PNG indicizzato.
  * Soggetto: Lo scudo vermiglio con il Monte a 5 Cime e la fiamma del Cero d'Oro incastonata al centro.
* **Splash Icon (Game Select Menu):**
  * Sprite affine animato ($32 \times 32\text{ px}$): I Tre Ceri che brillano in sequenza (Giallo, Azzurro, Nero) all'avvio della ROM.

---

## 33. CARICAMENTO, SCHERMATA DEI TITOLI & MENU DI SISTEMA

---

### A. SCHERMATA D'AVVIO & INTRO ANIMATA (BOOT SEQUENCE)
1. **Logo Team / Intro Eugubina:** Sfondo nero, rintocco isolato del Campanone in PCM, compare in dissolvenza bianca il sigillo del Comune di Gubbio che si dissolve in polvere di lustro rubino.
2. **Titoli di Testa (Title Screen):**
   * **Visuale:** Sfondo Mode 0 a 3 layer (Profilo scuro del Monte Ingino + Torretta di Palazzo dei Consoli con nuvole animate in scorrimento continuo su BG3).
   * **Logo Principale:** *"GUBBIO 1151: LA GUERRA DELLE UNDICI CITTÀ"* con lettere intagliate nella pietra calcarea bordate d'oro.
   * **Scelte Menu:**
     * `NUOVA CRONACA` (Avvia Prologo Atto I)
     * `CONTINUA` (Carica Slot 1 o Slot 2 da FRAM)
     * `IMPOSTAZIONI` (Velocità Testo, Volume Musica Chiptune, Volume Campanone PCM, Modalità Colori GBA Originale / IPS)

---

### B. PAUSE & INVENTORY MENU (MENU DI GIOCO - TASTO START)

Il menu di gioco occupa l'intero schermo $240 \times 160\text{ px}$ su BG0 e BG1:

```
+-------------------------------------------------------------+
| [GUBBIO 1151 - ATTO II]                  ORO: 450 DUCATI     |
| +---------------------+  +--------------------------------+ |
| | > EQUIPAGGIAMENTO   |  | SAN GIORGIO    LV 8  HP: 274/274| |
| |   ZAINO & RELIQUIE  |  | SANT'UBALDO    LV 8  HP: 188/188| |
| |   STATO 4 QUARTIERI |  | SANT'ANTONIO   LV 8  HP: 152/152| |
| |   TAVOLE EUGUBINE   |  +--------------------------------+ |
| |   SALVA (FRAM)      |  [POSIZIONE: Gola del Bottaccione]| |
| +---------------------+  [TEMPO DI GIOCO: 04h:22m]        | |
+-------------------------------------------------------------+
```

* **Sotto-Menu 'Stato 4 Quartieri':** Visualizza i 4 scudi rossi e la barra reputazione di San Martino, Sant'Andrea, San Pietro e San Giuliano con i relativi bonus mura sbloccati.
* **Sotto-Menu 'Tavole Eugubine':** Griglia 7 slot che mostra i frammenti di bronzo rinvenuti con la trascrizione dei testi sacri in lingua iguvina e traduzione a schermo.

---

## 34. REGIA DELLE CINEMATICHE & SEQUENZE ANIMATE

Le sequenze d'intermezzo alternano due stili grafici: **Cinemagrafiche a Pixel Art Full-Screen** (dialoghi e introspezione) e **Sequenze Affine Mode 7** (combattimenti epici e momenti solenni).

---

### A. CINEMATICA 1: L'ULTIMATUM SUL LOGGIATO (ATTO I)
* **Visuale:** Inquadratura panoramica dall'alto della piazza pensile di Palazzo dei Consoli.
* **Animazione:** Le ombre delle truppe perugine avanzano sulle valli; la telecamera scorre verso l'araldo a cavallo che lancia la pergamena insanguinata ai piedi di Ubaldo.
* **Audio:** Rumore sordo di tamburi di guerra interrotto dal colpo perentorio del pastorale di Sant'Ubaldo sulla pietra.

---

### B. CINEMATICA 2: L'ALZATA DEI TRE CERI (FINE ATTO I)
* **Visuale:** Interno della Basilica di Sant'Ubaldo; altare illuminato da fasci di luce volumetrica.
* **Effetto GBA:** Rotazione affine (Mode 7) dei tre ceri poligonali stilizzati in pixel art che si ergono verticalmente mentre Giorgio e Antonio vengono avvolti dalle aure dorate e fiammeggianti.
* **Audio:** Esecuzione orchestrale chiptune dell'Inno dei Ceri che culmina con il fragore della brocca di ceramica spezzata a terra.

---

### C. CINEMATICA 3: LA SORTITA ALL'ALBA NELLA NEBBIA (ATTO IV)
* **Visuale:** Porta San Pietro che si apre cigolando; un muro di nebbia densa invade l'ingresso.
* **Animazione:** Dalla nebbia emergono i tre eroi con gli occhi illuminati dal Fervore; alle loro spalle, le centinaia di luci dell'Albero del Monte Ingino squarciano l'orizzonte.

---

## 35. EFFETTI VISIVI, PARTICELLARI & SHADER GBA (H-BLANK INTERRUPTS)

Sfruttando le capacità del controller video del GBA e gli interrupt hardware (H-Blank / V-Blank):

---

### A. EFFETTO ONDULAZIONE CALORE & ACQUA (H-BLANK REGISTER MANIPULATION)
* **Gola del Bottaccione (Acqua del Camignano):** Manipolazione del registro `REG_BG2HOFS` riga per riga tramite interrupt H-Blank per creare l'effetto realistico di rifrazione dell'acqua corrente.
* **Fiamme di Sant'Antonio:** Distorsione sinusoidale dello sfondo attorno al personaggio durante il caricamento del *Fuoco di Sant'Antonio*.

---

### B. ENGINE PARTICELLARE DEDICATO (MAX 32 PARTICELLE ATTIVE)
* **Faville di Fuoco (Antonio):** Piccole particelle $2 \times 2\text{ px}$ rosse e arancioni con traiettoria parabolica ascendente e dissolvenza di palette.
* **Lampi di Grazia Sacra (Ubaldo):** Scintille a croce bianca a 4 punte che cadono lentamente sugli alleati curati.
* **Polvere di Pietra (Giorgio):** Schegge grigie che scaturiscono all'impatto della lancia contro le corazze nemiche o al blocco perfetto dello scudo.

---

### C. TRANSIZIONI DI BATTAGLIA (BATTLE SWIRL)
* **Effetto Entrata in Battaglia:** Schermo che si frantuma a tasselli rotanti tramite zoom affine (Mode 1 / Mode 7 scaling) accompagnato da un lampo bianco a schermo intero (`REG_BLDY = 16`).

---

## 36. SOUND DESIGN COMPLETO & SOUND EFFECTS TABLE (SFX MATRIX)

Tutti i suoni sono sintetizzati tramite i 4 canali PSG hardware (DirectSound A/B + Ch1/Ch2 Square Waves + Ch3 Wave RAM + Ch4 Noise):

---

### TABELLA COMPLETA DEGLI EFFETTI SONORI (SFX REGISTRY)

| ID SFX | Nome Effetto | Canale Audio | Descrizione & Sintesi |
| :--- | :--- | :--- | :--- |
| **SFX-01** | `CAMPANONE_HIT` | DirectSound A (PCM 8-bit) | Singolo rintocco profondo del bronzo dei Consoli con riverbero lungo (2.1 sec). |
| **SFX-02** | `CAMPANONE_DOPPIO` | DirectSound A (PCM 8-bit) | Sequenza ritmica incalzante a doppi per assedi e scene solenni. |
| **SFX-03** | `BROCCA_BREAK` | DirectSound B (PCM 8-bit) | Fragore di maiolica a lustro che si spezza sulla pietra. |
| **SFX-04** | `SWORD_CLASH` | Ch4 (Noise) + Ch1 (Square) | Impatto metallico acuto di parata lancia/scudo. |
| **SFX-05** | `HOLY_SHIELD` | Ch3 (Wave RAM) | Risonanza armonica eterea per l'attivazione del *Muro della Fede*. |
| **SFX-06** | `FLAME_BURST` | Ch4 (Noise) + DirectSound B | Ruggito profondo del getto piromantico di Sant'Antonio. |
| **SFX-07** | `SHIELD_BREAK` | DirectSound B (PCM 8-bit) | Suono pesante di corazza che si frantuma (ingresso nemico in stato BREAK). |
| **SFX-08** | `FERVOR_CHARGE` | Ch1 (Square sweep-up) | Glissando ascendente rapido quando si spende Fervore con il tasto R. |
| **SFX-09** | `TEXT_BEEP_UBALDO`| Ch3 (Low Sine Wave) | Bip vocale solenne a 110 Hz per i dialoghi del Vescovo. |
| **SFX-10** | `TEXT_BEEP_GIORGIO`| Ch1 (Square Wave) | Bip vocale squillante a 440 Hz per il Cavaliere. |
| **SFX-11** | `TEXT_BEEP_ANTONIO`| Ch4 (Low filtered noise)| Bip vocale cupo e roco per l'Eremita. |
| **SFX-12** | `TEXT_BEEP_MONALDO`| Ch1 + Ch2 (Dissonant) | Bip vocale stridente e metallico per il Tiranno di Perugia. |

---

## 37. TITOLI DI CODA & EPILOGO INTERATTIVO (LA VETRATA DELLA VITTORIA)

La sequenza di chiusura trasforma il videogioco in un monumento d'arte medievale:

---

### A. LA SCENA DEL CORTEO TRIONFALE
* I tre campioni, scortati dai Balestrieri, dagli Sbandieratori e dai rappresentanti dei 4 Quartieri, risalgono la cordonata verso Piazza Grande.
* Il popolo lancia petali di rose bianche e gialle.
* In cima alla scalinata dei Consoli, il Campanone suona a festa a rotazione continua.

---

### B. TRASFORMAZIONE NELLE VETRATE ISTORIATE DELLA BASILICA
1. La grafica in pixel art 32-bit a schermo pieno inizia a comporsi di tasselli di vetro policromo delimitati da profili di piombo nero.
2. La telecamera scorre verticalmente lungo la grande **Vetrata Istoriata di Sant'Ubaldo** che raffigura:
   * *Registro Inferiore:* I soldati delle undici città in rotta e gli stendardi spezzati.
   * *Registro Mediano:* San Giorgio che abbatte il Grifo d'Ombra e Sant'Antonio che spegne i trabucchi con la fiamma mistica.
   * *Registro Superiore:* Sant'Ubaldo con le braccia aperte che benedice la città di pietra e il Monte Ingino illuminato dal sole.
3. I titoli di coda (crediti storici, musicisti tracker, programmatori Butano) scorrono sulla destra con caratteri gotici dorati.
4. Schermata finale: *"GUBBIO È SALVA. ANNO DOMINI 1151."* con salvataggio automatico del file di completamento su FRAM (sblocco modalità New Game+ e Boss Rush al Cassero).


---

## 38. TOPOGRAFIA URBANA & WORLD FLOW DEL CENTRO STORICO (DALLE MAPPE REALI)

Basandosi sulla planimetria reale del centro storico di Gubbio, il mondo di gioco è suddiviso in macro-aree ortogonali interconnesse ($512 \times 320\text{ px}$ ciascuna) distribuite lungo i dislivelli naturali della città.

```
                       [ AREA 4: MONTE INGINO ]
                      (Basilica Sant'Ubaldo & Rocca)
                                   ▲
                                   │ (Stradoni - Salita)
                                   │
                      [ AREA 3: GUBBIO ALTA ]
                  (Duomo 13, Palazzo Ducale 12)
                                   ▲
                                   │ (Scale & Vicoli ripidi)
                                   │
 [ AREA 2A: SAN MARTINO ] ── [ AREA 2B: PIAZZA GRANDE ] ── [ AREA 2C: SANT'ANDREA ]
 (San Domenico 5, Camignano)  (Consoli 11, Pretorio 14)    (Porta Romana 6, S. Agostino)
         │                               │                               │
         ▼                               ▼                               ▼
 [ AREA 1A: TEATRO ROMANO ] ─ [ AREA 1B: 40 MARTIRI ] ─── [ AREA 1C: SAN PIETRO ]
 (Fuori Mura / Avamposto)     (S. Francesco 7, Tiratori 8) (Abbazia 3, Quartiere Rosa)
```

---

### A. SPECIFICA DEI SETTORI E PUNTI D'INTERESSE

1. **Balza Inferiore (Fronte Sud & Mercatale):**
   * **Area 1A - Teatro Romano:** Monumento romano situato all'esterno della cinta muraria, utilizzato nel gioco come avamposto delle pattuglie nemiche e zona tutorial avanzata.
   * **Area 1B - Piazza 40 Martiri & Logge dei Tiratori:** Grande polo commerciale; sede di mercanti d'armi, speziali e artigiani del cuoio.
   * **Area 1C - Complesso di San Pietro:** Bastione meridionale fortificato e sede della quest della Rosa d'Argento (`Q-SP01`).
2. **Fascia Mediana (Asse Consolare & Quartieri):**
   * **Area 2A - Quartiere San Martino & San Domenico:** Fucina delle armi pesanti (Mastro Raniero) e accesso alla Gola del Bottaccione seguendo l'alveo del torrente Camignano.
   * **Area 2B - Piazza Grande:** Hub centrale pensile sollevato sugli arconi trecenteschi; accesso a Palazzo dei Consoli e Palazzo Pretorio.
   * **Area 2C - Quartiere Sant'Andrea & Porta Romana:** Polo erboristico e baluardo difensivo orientale contro le cariche di Spoleto e Foligno.
3. **Fascia Alta & Monte (Dislivello Religioso):**
   * **Area 3 - Duomo & Palazzo Ducale:** Zona delle cripte segrete e deposito sacro di una delle 7 Tavole Eugubine.
   * **Area 4 - Monte Ingino & Stradoni:** Sentiero a tornanti tra i boschi sacri fino alla Basilica di Sant'Ubaldo e al Cassero della Rocca.

---

## 39. MAPPA TATTICA REGIONALE DELL'UMBRIA & LE TRE DIRETTRICI DELLA COALIZIONE (1151)

Questa sezione codifica la mappa geografica regionale dell'Umbria medievale per la cutscene iniziale e per la schermata di monitoraggio dello stato della guerra nel menu di pausa.

```
       [ Cagli / Flaminia ] (Valerio - Veleno)
                ▲
                │  (Gole del Bottaccione)
                │
 [ Umbertide ] ──► [ GUBBIO (1151) ] ◄── [ Gualdo Tadino / Nocera ]
 (Linee Tevere)    (I Tre Ceri)           (Fossato - Trabucchi)
                        ▲
                        │  (Valle Umbra)
                        │
 [ PERUGIA ] ───────────┴─────────── [ SPOLETO ]
 (Monaldo - Grifo Finale)            (Corrado - Colosso Forge)
       │                                  │
 [ Assisi, Bettona, Spello ]       [ Foligno & Todi ]
```

---

### A. I 3 ASSI STRATEGICI DELLA COALIZIONE

1. **Asse Ovest / Sud-Ovest (L'Egemonia del Grifo):**
   * **Perugia (Capitale Nemica):** Base del Tiranno Monaldo; schiera la cavalleria pesante e i cultisti dell'araldica del Grifo d'Ombra.
   * **Umbertide & Città di Castello:** Contingenti di supporto lungo l'asta del Tevere a presidiare le vie di fuga settentrionali.
2. **Asse Est / Flaminia (L'Accerchiamento dei Passi Appenninici):**
   * **Gualdo Tadino, Fossato di Vico & Nocera Umbra:** Controllano l'accesso alla via Flaminia e riforniscono i trabucchi e le catapulte mobili posizionate sui colli.
   * **Cagli:** Avamposto dell'alchimista Valerio per contaminare le sorgenti d'acqua dolce del Bottaccione.
3. **Asse Sud / Valle Umbra (La Fanteria Corazzata):**
   * **Spoleto:** Fanti pesanti armati di magli e corazze temprate nelle fucine della Valnerina (Corrado).
   * **Foligno, Assisi, Bettona, Spello & Bevagna:** Battaglioni d'assalto rapido e arcieri coordinati dai Gemelli della Tempesta (Foligno e Todi).

---

### B. IMPLEMENTAZIONE OVERWORLD CUTSCENE (`scene_world_map.h`)

```cpp
#ifndef SCENE_WORLD_MAP_H
#define SCENE_WORLD_MAP_H

#include "bn_core.h"
#include "bn_display.h"
#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_items_umbria_map.h"
#include "campanone_audio.h"

class UmbriaWorldMapCutscene {
private:
    bn::regular_bg_ptr _map_bg;
    int _animation_timer;
    int _step;

public:
    UmbriaWorldMapCutscene() :
        _map_bg(bn::regular_bg_items::umbria_map.create_bg(0, 0)),
        _animation_timer(0),
        _step(0) {}

    void update() {
        _animation_timer++;

        // Step 1: Mappa pergamena visibile (0-60 frame)
        // Step 2: Gli 11 stendardi neri compaiono sui centri nemici (60-180 frame)
        // Step 3: Rintocco del Campanone e bagliore dorato su Gubbio (180+ frame)
        if(_animation_timer == 180) {
            CampanoneAudio::play_strike();
        }
    }
};

#endif
```
