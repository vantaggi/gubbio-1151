# Lezioni imparate

Ogni volta che qualcosa si è dovuto rifare, o si è scoperto tardi, qui c'è una voce: cosa è successo,
quanto è costato, perché, che cosa si doveva decidere prima e la regola che ne esce. Ogni regola è già
entrata in una fase di [PERCORSO_DA_ZERO.md](PERCORSO_DA_ZERO.md), così il prossimo gioco non ripaga lo
stesso errore. Il modello di una voce è in [modelli/LEZIONE.md](modelli/LEZIONE.md).

I costi sono misurati sulla storia del repo (righe e file toccati dal commit del rifacimento) o, dove
manca una misura, stimati e scritti come stima. Nessuna voce racconta la trama.

**Le cinque che pesano di più**, nell'ordine in cui le avremmo evitate:
[L01](#l01--le-scelte-di-fondazione-prese-dopo-il-prototipo) (fondazioni),
[L02](#l02--lorientamento-della-mappa-cambiato-dopo-la-prima-prova) (orientamento),
[L04](#l04--lo-standard-grafico-arrivato-a-metà-produzione) (standard grafico),
[L03](#l03--la-storia-scritta-prima-della-sua-struttura) (struttura della storia),
[L06](#l06--i-limiti-dellhardware-scoperti-dai-crash) (limiti dell'hardware).

---

## L01 · Le scelte di fondazione prese dopo il prototipo

**Cosa è successo.** Il prototipo (agosto 2026, 24 sessioni) è stato buttato il 1 novembre e si è
ripartiti da zero. La grafica nasceva da foto prese dal web, che in un repo pubblico non si possono
tenere; il repo non aveva licenza; rilascio e ambito non erano mai stati decisi; la toolchain non era
bloccata.

**Quanto è costato.** Tutto il prototipo come prodotto: di lui sono sopravvissuti solo idee, test e
lezioni. La cronologia è stata riscritta per togliere i derivati delle foto.

**Perché.** Si è partiti dal codice e dal GDD senza fissare prima le cinque scelte che cambiano tutto il
piano: cosa vuol dire rilascio, da dove viene la grafica, che repo, che licenza, quanto è grande la v1.

**Cosa si doveva decidere prima.** Le decisioni D002, D004, D005, D007, D008 e D020, il primo giorno,
prima di una sola riga di codice. Lo stesso per la scelta del ramo: sviluppare su un ramo orfano
parallelo (D005) ha poi chiesto un passaggio a parte per farlo diventare `main` (D006).

**Regola nuova.** Fase 0 del percorso: nessun codice né asset finché la scheda di avvio non ha una
risposta a ogni domanda di fondazione. Il nuovo gioco nasce su `main` in un repo suo.

**Dove vive ora.** [modelli/SCHEDA_AVVIO.md](modelli/SCHEDA_AVVIO.md), fase 0 del percorso.

## L02 · L'orientamento della mappa cambiato dopo la prima prova

**Cosa è successo.** La città era ruotata con l'ovest in alto (D060), per vedere di fronte le facciate
che guardano a est. Alla prima prova (4 nov) Cioti non capiva il giro della città e ha chiesto il nord in
alto (D061). Si sono ruotate tutte le aree, le facciate, la mappa del menù, i varchi, i test e i
documenti; sette thread sono stati fermati e avvisati perché non rifacessero parti da ruotare.

**Quanto è costato.** Il solo commit della rotazione: 31 file, 13.842 righe aggiunte e 13.414 tolte, più
i ritocchi successivi (spawn, chiostro, portali, Loggia coricata) e una giornata di coordinamento. La
città approvata il 2 nov è rimasta nel tag `citta-v1` come storia.

**Perché.** L'orientamento è stato scelto per un vincolo di disegno (le facciate a est), non per chi
gioca, e la prima volta che Cioti ha *camminato* nella città era il giorno 4, con la città già dipinta.

**Cosa si doveva decidere prima.** Orientamento e convenzione di vista (D042, D061) andavano provati con
una città grezza navigabile (blocchi colorati, nomi delle aree, varchi) prima di dipingere, e giudicati
camminando, non guardando un'immagine.

**Regola nuova.** L'orientamento è una decisione di fondazione del mondo: si decide con un «greybox»
giocabile e la prova di chi gioca. Per le città della serie: nord in alto salvo motivo forte, il lato
vero di ogni facciata sta nei dati e il disegno la gira verso il basso.

**Dove vive ora.** Fase 4 (greybox) del percorso; `facciata_lato_reale` in `mondo/monumenti.json`.

## L03 · La storia scritta prima della sua struttura

**Cosa è successo.** Il copione v1 è stato scritto in scene dalla scaletta del GDD e messo subito nel
motore (D070). Il 3 nov Cioti ha chiesto più sfaccettature: si è scritto un prompt strutturato, una
Bibbia della storia, e il copione è stato rifatto in v2 (D071) con scelte, varianti e indizi che il
motore v1 non sapeva gestire.

**Quanto è costato.** Copione: 26 file, 6.155 righe aggiunte e 3.942 tolte; motore della storia rifatto
(scelte, varianti per bandiera, 64 bandiere nuove, formato di salvataggio v3); quest, edifici e NPC
rivisti; poi una revisione completa e un grafo per ritrovare i buchi.

**Perché.** La struttura (tema, scelte, segreti, quanti finali, chi sa cosa) è venuta dopo le scene, e
il motore è stato scritto per la struttura sbagliata.

**Cosa si doveva decidere prima.** Il prompt della storia e la Bibbia (D071), il grafo della trama (D072)
e la regola di rispetto per le persone vere (D074) prima di scrivere una battuta; il motore dopo aver
saputo che tipo di scelte servono.

**Regola nuova.** Ordine fisso: ricerca → prompt della storia → Bibbia approvata → scaletta → grafo a 0
errori → copione → motore. Il prompt di Gubbio (parte C di `storia/PROMPT_STORIA.md` nei file del
progetto) è il modello da adattare.

**Dove vive ora.** Fase 3 del percorso; `tools/grafo_trama.py` e `tests/test_grafo_trama.py`.

## L04 · Lo standard grafico arrivato a metà produzione

**Cosa è successo.** La Guida di stile (12 scelte, D040) fissava palette, luce, contorni e misure, ma non
*come* si dipinge un edificio, una figura o un interno (D053). Ogni thread ha dipinto a modo suo. Il
4 nov, dopo che sagome, edifici, cutscene e menù erano già fatti, è nato lo standard con regole siglate
(D054) e si è rifatto tutto con loop di 10 giri per ambito (D055).

**Quanto è costato.** Il 4 nov conta 218 commit, in gran parte per portare allo standard fondali
(8.701 righe aggiunte e 3.334 tolte nel solo primo pezzo), cutscene, menù, figure della città e
Bottaccione. Stima: un giorno pieno di lavoro parallelo di 5-6 thread.

**Perché.** La guida diceva cosa, non come; mancava un pezzo campione approvato per ogni tipo di
grafica, e mancava un custode visivo che confrontasse il lavoro dei thread.

**Cosa si doveva decidere prima.** Lo standard di esecuzione (D054) insieme alla Guida, con un pezzo
campione per tipo (figura, edificio, suolo, interno, oggetto, riquadro, cutscene) e il custode visivo
(D107) dal primo giorno di produzione.

**Regola nuova.** La fase di stile finisce solo quando ci sono la Guida in dati, lo standard con le
regole misurabili sotto test, e un pezzo campione per tipo approvato da chi gioca. Il loop di 10 giri
si fa sul campione, non dopo su tutto.

**Dove vive ora.** Fase 4 del percorso; `STANDARD_GRAFICO.md` nei file del progetto (`stile_dati/`),
`tests/test_fondali_standard.py`, `tools/controlla_cutscene.py`.

## L05 · Sagome, animazioni e porte giudicate solo a gioco fatto

**Cosa è successo.** Il 4 nov Cioti ha giudicato brutte le sagome e le animazioni di battaglia e ha
notato che le cutscene non mostravano mai i protagonisti; alla prima prova le porte degli edifici non si
trovavano. Tutto rifatto (D058, D056).

**Quanto è costato.** Un generatore di sagome nuovo, 10 giri sulle animazioni, cutscene C3 e C4 rifatte,
un pezzo intero sugli ingressi leggibili (stima: mezza giornata di due thread).

**Perché.** Queste cose si giudicano solo nel gioco, in movimento, e la prima ROM che Cioti ha giocato
davvero è arrivata il giorno 4.

**Cosa si doveva decidere prima.** Una «fetta verticale» presto: un'area, una porta, un dialogo, una
battaglia, una cutscene con i protagonisti, al livello finale, giocata da Cioti prima della produzione
in serie (D026, D055).

**Regola nuova.** Fase 6 del percorso: fetta verticale giocata e approvata come cancello. Senza ok, niente
produzione in serie.

**Dove vive ora.** Fase 6 del percorso.

## L06 · I limiti dell'hardware scoperti dai crash

**Cosa è successo.** Il 5 nov due crash veri giocando: «No more sprite sort layers» (Butano ne ha 16, lo
z dai piedi ne usava uno per sprite) e «no more available colors» (palette degli sprite a 256 su 256 in
una battaglia partita dalla città). Prima ancora il lag vicino agli animali e al cambio d'area, e l'erba
del Teatro che sforava i 1.024 tile di un'area.

**Quanto è costato.** Due correzioni urgenti con ROM nuove, prove nuove in mGBA, contatori di palette,
un thread dedicato alla caccia ai crash (D032). Ogni crash ha interrotto una prova di Cioti.

**Perché.** I budget della console (sprite, palette, tile per area, strati di ordinamento, VRAM, EWRAM,
CPU per frame) non erano scritti da nessuna parte né misurati nelle prove. Un errore di Butano a schermo
non finisce nel log, quindi i test verdi non lo vedevano.

**Cosa si doveva decidere prima.** Una tabella dei budget con un contatore per ognuno nel pannello di
debug e una prova di stress per area e per passaggio scena (D030), prima di riempire le aree.

**Regola nuova.** Ogni limite dell'hardware ha un numero scritto, un contatore e una prova mGBA che
misura il picco con margine; ogni nuova scena registra il suo picco.

**Dove vive ora.** Fase 5 del percorso; `-DGUBBIO_PALETTE`, `-DGUBBIO_PRESTAZIONI`, prove `palette_*` in
`tests/mgba/prove.json`.

## L07 · La toolchain solo sul PC

**Cosa è successo.** Fino al 4 nov si credeva che il cloud non potesse compilare la ROM (D022): build e
prove passavano tutte dal PC di Cioti con Remote Control. Quando il PC era spento il gioco non si
compilava; quando una sessione finiva un pezzo restava ferma («Come mai tutto è fermo?», 2 nov); a PC
spento è rimasto lavoro non salvato. Dal 4 nov la ROM si compila in cloud con il mirror di Docker
(D023).

**Quanto è costato.** Stima: due giorni di lavoro serializzato su una sola macchina, più i lavori
lasciati a metà e ricostruiti.

**Perché.** Non si è provato il primo giorno se il cloud potesse fare la build (Docker Hub rispondeva
429, ma un mirror esisteva).

**Cosa si doveva decidere prima.** Il giorno 0 una build completa e una prova mGBA senza schermo in
cloud, con l'immagine bloccata per digest (D020, D021, D023). Il PC di chi gioca serve solo a giocare.

**Regola nuova.** Criterio d'uscita della fase 0: ROM compilata in cloud, in CI e sul PC con lo stesso
digest, e una prova in mGBA che passa in cloud. Ogni sessione salva il WIP su un ramo prima di fermarsi.

**Dove vive ora.** Fase 0 del percorso; `toolchain.lock`, `build.sh`, `tools/banco.sh`.

## L08 · Le regole del codice GBA arrivate dopo il codice

**Cosa è successo.** Il 5 nov Cioti ha dato le regole di sviluppo GBA (D029): niente float, niente
`std::`, tabelle `constexpr`, niente divisioni nel ciclo di ogni frame. Il codice esistente è stato
corretto e sono nati i controlli automatici.

**Quanto è costato.** 25 file, 1.315 righe aggiunte; divisioni tolte dalla folla (probabile causa del
lag), tre strumenti di controllo nuovi.

**Perché.** Le regole erano in parte nel prototipo (`AGENTS.md`) ma non tradotte in controlli
automatici fin dal primo commit.

**Cosa si doveva decidere prima.** Regole di codice e i loro controlli (D028, D029) nella fase delle
fondamenta tecniche, prima del primo sistema di gioco.

**Regola nuova.** Il modello di repo di ogni gioco parte con `docs/regole_sviluppo_gba.md`,
`controlla_regole_gba.py`, `controlla_divisioni.py`, `controlla_struct.py` e `-Werror` già attivi.

**Dove vive ora.** Fase 5 del percorso; [GENERICO_E_SPECIFICO.md](GENERICO_E_SPECIFICO.md).

## L09 · Le schermate per chi gioca pensate tardi

**Cosa è successo.** Il 4 nov Cioti ha chiesto: «Abbiamo ragionato su tutto?» Mancavano il menù (obiettivi,
mappa, oggetti, negozio, opzioni), gli aiuti e gli edifici esplorabili: il gioco aveva solo una pausa
con «Salva» e un solo interno. Sono stati progettati e costruiti in un giorno (D096, D066).

**Quanto è costato.** Due thread interi (menù e interni), salvataggio portato alla versione 4, 12 pezzi
di lavoro nuovi nel piano.

**Perché.** Il piano partiva dai sistemi tecnici (mondo, battaglia, storia) e non da una lista di cosa
deve vedere e poter fare chi gioca.

**Cosa si doveva decidere prima.** L'inventario completo delle schermate e delle azioni del giocatore,
con mockup, nella fase di design (D096), prima di fare il piano dei pezzi.

**Regola nuova.** Fase 2 del percorso: lista di controllo «cosa serve a chi gioca» (dove sono, dove
vado, cosa devo fare, cosa ho, come salvo, come leggo una mossa, dove si entra) chiusa prima del piano.

**Dove vive ora.** Fase 2 del percorso; [modelli/SCHEDA_AVVIO.md](modelli/SCHEDA_AVVIO.md), sezione 4.

## L10 · Le battute degli NPC che non dicevano niente

**Cosa è successo.** Il 5 nov, dopo una prova lunga, Cioti ha trovato «frasi senza senso» negli NPC di
contorno, mentre le battute degli amici andavano bene. Gli NPC uscivano senza nome e con aforismi e
riferimenti non spiegati (D079). Riscritte tutte (D080).

**Quanto è costato.** 11 file, 9.152 righe aggiunte e 8.633 tolte (testi e tabelle generate).

**Perché.** Non c'era una guida di scrittura per gli NPC: si sono scritte battute «d'atmosfera» invece di
battute concrete.

**Cosa si doveva decidere prima.** Una guida di scrittura degli NPC (D080) e la revisione dei testi
(D081) prima di scrivere il primo NPC.

**Regola nuova.** Ogni NPC ha nome a schermo; ogni battuta dice cosa fa, vede o teme chi parla; nessun
riferimento che il giocatore non può ancora conoscere. Si fa leggere un campione a chi gioca prima di
scriverne cento.

**Dove vive ora.** Fase 3 del percorso; `tests/test_redazione.py`.

## L11 · La schermata delle mosse incomprensibile

**Cosa è successo.** La scelta delle mosse in battaglia era un elenco di nomi (D094): non si capivano
effetto, danno e costo. Rifatta il 5 nov con una scheda e l'anteprima sul bersaglio (D095).

**Quanto è costato.** Un thread per una sera: nuova logica constexpr, nuove prove della vista.

**Perché.** La schermata è stata disegnata dal lato del motore («quali comandi esistono») e non dal lato
di chi sceglie («cosa devo sapere per scegliere»).

**Cosa si doveva decidere prima.** Per ogni schermata di scelta, la lista delle informazioni che servono
per scegliere e due o tre giochi del genere come riferimento, nella fase di design (D095).

**Regola nuova.** Nessuna schermata di scelta senza la sua scheda «cosa deve sapere chi gioca» e un
mockup approvato.

**Dove vive ora.** Fase 2 del percorso.

## L12 · La prima prova di chi gioca arrivata il quarto giorno

**Cosa è successo.** La prima volta che Cioti ha girato davvero per la città è stata il 4 nov sera. In
mezz'ora sono usciti: il protagonista che compariva nell'intro, il compagno che non seguiva, porte
introvabili, lag, orientamento da cambiare. I test erano verdi.

**Quanto è costato.** Tutto quello che le lezioni L02, L05 e L06 raccontano è stato scoperto qui.

**Perché.** Le ROM di fase c'erano, ma non c'era un appuntamento fisso per giocarle; gli oracoli
guardavano i log e non lo schermo (D026).

**Cosa si doveva decidere prima.** Una prova di chi gioca a cadenza fissa (a ogni fase, almeno una al
giorno quando si produce), con una sola ROM da provare (D031) e una breve lista di cosa guardare.

**Regola nuova.** Ogni fase del percorso chiude con una prova giocata; i problemi trovati diventano prove
automatiche prima di essere corretti.

**Dove vive ora.** Tutte le fasi del percorso (riga «prova giocata»).

## L13 · Nomi cambiati e copie rimaste indietro

**Cosa è successo.** I nomi di gioco degli amici sono cambiati più volte e il 4 nov la regola del «San»
per i protagonisti (D075). Copie del copione e documenti fuori dal repo sono rimasti con i nomi vecchi;
Cioti lo ha notato («i documenti e i JSON sono allineati?»).

**Quanto è costato.** Un thread intero di allineamento, un test nuovo esteso a docs e dati.

**Perché.** C'erano più copie della stessa informazione e nessun controllo che fossero uguali.

**Cosa si doveva decidere prima.** Una sola fonte per ogni dato (D076), nel repo; le copie si generano;
il test dei nomi esiste dal primo nome.

**Regola nuova.** Mai copie a mano: se serve una copia fuori dal repo, si rigenera e porta scritto da dove
viene. Test dei nomi ritirati dal primo giorno.

**Dove vive ora.** Fase 5 del percorso; `tests/test_nomi_coerenti.py`.

## L14 · La suite di test lenta

**Cosa è successo.** A inizio novembre la suite completa durava più di 7 minuti; ogni piccola modifica la
rifaceva tutta e frenava i thread. Il 4 nov è nato il giro corto (D027).

**Quanto è costato.** Stima: un'ora di attesa al giorno per thread prima del giro corto.

**Perché.** I test sono cresciuti senza un modo per lanciare solo quelli toccati.

**Cosa si doveva decidere prima.** Il giro corto e il parallelo come parte del modello di repo (D027).

**Regola nuova.** `tools/prove.py` è nel modello; un test sopra i 15 secondi si divide o va nella sola
CI.

**Dove vive ora.** Fase 5 del percorso; `docs/prove.md`.

## L15 · Lavori paralleli che si pestavano i piedi

**Cosa è successo.** Più thread hanno lavorato insieme sulla città mentre se ne decideva la rotazione
(Cioti, 4 nov: «non avrebbe senso rifare delle parti se poi viene ruotata la mappa»); thread fermi a
fine pezzo senza coda; il grafo delle dipendenze è arrivato solo il 3 nov (D106).

**Quanto è costato.** Stima: diversi pezzi fatti due volte e mezze giornate di thread fermi.

**Perché.** Si sono aperti thread paralleli prima di chiudere le decisioni che toccavano tutti, e senza
dire quali file erano di chi.

**Cosa si doveva decidere prima.** Il piano a grafo con risorse esclusive (D106), i custodi (D107), e la
regola che una decisione di fondazione aperta blocca i thread che ne dipendono (D105).

**Regola nuova.** Prima di aprire thread paralleli: decisioni di fondazione chiuse, ogni thread con il
suo brief (contratto, file di sua proprietà, custodi, criterio d'uscita, coda successiva).

**Dove vive ora.** Fase 7 del percorso; [modelli/BRIEF_THREAD.md](modelli/BRIEF_THREAD.md).

## L16 · La città vera raccolta dopo il contratto del mondo

**Cosa è successo.** Il contratto del mondo del prototipo (D062) aveva dieci differenze dalla città vera
(direzioni delle vie, ordine dei quartieri, quote). Il 1-2 nov si è fatto il censimento dei monumenti e
della rete stradale e il grafo delle aree è stato rifatto dai dati OSM (D063).

**Quanto è costato.** Due rifacimenti del grafo delle aree in due giorni (35 e poi 41 varchi), griglie
rigenerate.

**Perché.** Il mondo è stato disegnato prima di raccogliere i dati veri; in più il cloud non raggiunge
OpenStreetMap e Commons, quindi le query vanno fatte sul PC.

**Cosa si doveva decidere prima.** Censimento (monumenti con misure, rete stradale, quote, foto di
riferimento con licenze, simboli) prima del contratto del mondo (D063, D067).

**Regola nuova.** Fase 1 del percorso: il contratto del mondo si scrive dai dati raccolti, e chi conosce
la città conferma i punti dubbi prima del disegno.

**Dove vive ora.** Fase 1 del percorso; `tools/mondo_dati.py`, `mondo/grafo.json`.

## L17 · Scala del personaggio e scala degli edifici decise separate

**Cosa è successo.** Con il fattore di compressione unico le porte venivano alte 4 pixel; poi le porte
sono state portate a 26-28 pixel per far passare il protagonista 16x32, e le facciate a 5 tile.

**Quanto è costato.** Facciate e portali di tutti i monumenti rifatti una volta (pezzo dei fondali).

**Perché.** La scala degli edifici e quella del personaggio sono state scelte in due momenti diversi.

**Cosa si doveva decidere prima.** Proporzioni del personaggio (D046) e scala del mondo insieme, provate
con la figura accanto a una porta e a una facciata.

**Regola nuova.** La tavola delle proporzioni ha sempre il personaggio davanti a una porta, una casa e il
monumento più alto.

**Dove vive ora.** Fase 4 del percorso; regola M1 dello standard grafico.

## L18 · Copie di lavoro e modifiche perse

**Cosa è successo.** Mockup e copioni copiati in `/mnt/project-files/` sono diventati vecchi rispetto al
repo (per esempio il mockup delle cutscene C5-C7 superato dal codice); una volta un `git checkout HEAD --`
ha cancellato modifiche non salvate; a PC spento è rimasto lavoro non committato.

**Quanto è costato.** Lavoro rifatto a mano, confusione su quale fosse la versione buona (D076).

**Perché.** Non era scritto quale copia facesse fede, e il WIP non si salvava prima di fermarsi.

**Cosa si doveva decidere prima.** Il repo è l'unica fonte (D076); i file del progetto servono solo per
cose che non stanno nel repo (foto di riferimento, audio da ascoltare, pagine per chi gioca).

**Regola nuova.** Ogni file fuori dal repo dice in testa da dove viene; prima di fermarsi si committa il
WIP su un ramo di lavoro; mai `checkout` su file con modifiche non salvate.

**Dove vive ora.** Fase 7 del percorso.

## L19 · Il metodo nato a fine progetto

**Cosa è successo.** Il registro delle decisioni, le lezioni e il percorso da zero sono stati scritti il
6 nov ricostruendo la storia da memoria, chat e commit (D108). Molte decisioni erano sparse in decine di
file e messaggi.

**Quanto è costato.** Un thread intero di ricostruzione; qualche data e qualche costo sono stime.

**Perché.** Non c'era un posto unico dove scrivere una decisione nel momento in cui la si prende.

**Cosa si doveva decidere prima.** Aprire `docs/metodo/` il primo giorno (D108), con la regola di
aggiornamento e il test.

**Regola nuova.** Il metodo è il primo file del repo di ogni gioco nuovo: si copia dal gioco precedente e
si aggiorna a ogni decisione o rifacimento.

**Dove vive ora.** [README.md](README.md), regola di aggiornamento; `tests/test_metodo.py`.
