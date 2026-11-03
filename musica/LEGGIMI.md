# Musica di Gubbio 1151 (F7)

Tutto originale e generato: le partiture sono testi in questa cartella, gli strumenti sono
sintetizzati da `tools/genera_audio.py` (nessun campione registrato), l'uscita va in `audio/`.

```
musica/*.brano + musica/temi.comuni ──> tools/genera_audio.py --scrivi ──> audio/*.xm, audio/*.wav
```

`audio/` non si tocca a mano: `tests/test_audio.py` controlla che sia aggiornata. Per ascoltare
sul PC: `python tools/genera_audio.py --ascolto CARTELLA` (serve ffmpeg con libopenmpt; in
alternativa si apre `audio/*.xm` con OpenMPT o direttamente in mGBA dentro la ROM).

## Scelte musicali

- **Un filo solo**: il *Tema di Gubbio* (re dorico, 8 battute, in `temi.comuni`) torna nel titolo,
  nella basilica (cantato come una lauda, con organum a una quinta sotto), nel prologo, nella terza
  alba e alla fine della canzone dei titoli. Chi gioca lo riconosce senza saperlo.
- **Modi medievali** invece di maggiore e minore: dorico per Gubbio, misolidio per la vita dei
  quartieri e la salita, eolio per la battaglia, frigio per il Bottaccione e Corrado.
- **Strumenti dell'Umbria del XII secolo, sintetizzati**: liuto, arpa, flauto dolce, ciaramella,
  viella, coro, corno, bordone (ghironda/cornamusa), campane, tamburo, grancassa, sonagli, incudine.
- **Forme del tempo**: saltarello in 6/8 per la città, lauda per la basilica, ballata in 3/4 per la
  canzone di Flaviano. Nessun Inno dei Ceri (regola delle cutscene).
- **Cutscene a misura**: i brani di C1-C4 durano quanto la regia (il test lo controlla).

## Brani

| Brano (`bn::music_items::`) | Dove | Durata | Anello |
| :-- | :-- | --: | :-- |
| `titolo` | schermata del titolo (il Campanone apre) | 67 s | sì, dal Tema |
| `citta` | esplorazione dei quartieri, di giorno | 38 s | sì |
| `notte` | la città di notte / fase NOTTE | 64 s | sì |
| `stradoni` | salita al Monte Ingino | 60 s | sì |
| `basilica` | dentro la basilica di Sant'Ubaldo | 64 s | sì |
| `bottaccione` | gola del Bottaccione e Condotto | 51 s | sì |
| `battaglia` | battaglie normali | 29 s | sì, dopo l'attacco |
| `corrado` | duello con Corrado | 27 s | sì, dopo l'attacco |
| `vittoria` | fine battaglia vinta | 8 s | no |
| `sconfitta` | battaglia persa | 12 s | no |
| `presentazione` | cartiglio delle presentazioni C3 | 4 s | no |
| `prologo` | cutscene C1 | 55 s | (sì) |
| `undici_bandiere` | cutscene C2 | 16 s | (sì) |
| `pastorale` | cutscene C2P | 2,7 s | no |
| `terza_alba` | cutscene C4, poi riparte dal Tema per i titoli | 27 s | sì, dal Tema |
| `canzone_di_flaviano` | titoli di coda: «la canzone nuova» promessa da Flaviano e Giuliana | 58 s | sì |

## Effetti (`bn::sound_items::`)

`cursore`, `conferma`, `annulla`, `testo` (avanzamento del dialogo), `colpo`, `fuoco` (Antonio),
`fede` (Ubaldo), `cura`, `scudo` (Corrado), `svanisce` (nemico sconfitto), `livello`, `salva`,
`campanone` (rintocco singolo, 2,8 s).

## Come si aggancia nel gioco (lavoro del thread del gioco, sul PC)

1. Il Makefile ha già `AUDIO := audio`: Butano passa `audio/` a mmutil e genera
   `bn_music_items.h` e `bn_sound_items.h`.
2. Musica: `bn::music_items::citta.play(bn::fixed(0.6));` (anello per default);
   jingle: `bn::music_items::vittoria.play(bn::fixed(0.7), false);`; stop con `bn::music::stop()`.
   Effetti: `bn::sound_items::conferma.play();`.
3. Punti di aggancio proposti: titolo → `titolo`; esplorazione → brano per area
   (quartieri `citta`, fase NOTTE `notte`, stradoni `stradoni`, basilica `basilica`, Bottaccione
   `bottaccione`); `scena_battaglia` → `battaglia` o `corrado`, poi `vittoria`/`sconfitta`;
   `regia` → il brano della cutscene all'inizio (la regia può portare il nome del brano);
   menù e testo → effetti. Cambiare brano solo se è diverso da quello che suona (niente ripartenze
   passando da un'area all'altra dello stesso quartiere).
4. Prova: suono in mGBA, ROM < 1 MB in più (audio/ pesa ~800 KB prima della conversione), zero
   heap invariato (maxmod usa memoria statica di Butano).

## Formato delle partiture (`*.brano`)

```
titolo: Gubbio 1151 - Notte
bpm: 60                    # tempo (con velocita' 6: bpm = semiminime al minuto se 4 righe = 1/4)
battuta: 16                # righe per battuta: le stanghette | vengono controllate
anello: no                 # facoltativo: i jingle non tornano da capo
durata_attesa: 28          # facoltativo: per i brani delle cutscene
canale arpa arpa 150       # canale NOME STRUMENTO [pan 0-255]
def giro: A3:2 E4:2 ...    # frase riusabile, si cita con $giro (o $giro+12 trasposta)
ordine: INTRO *A B         # '*' = da dove riparte l'anello

[A] 128                    # sezione di 128 righe (max 256); "[A] 80 /16" cambia la battuta
arpa: !34 $giro            # ogni riga deve sommare esattamente le righe della sezione
eco: = voci >2 !16         # copia di un altro canale: trasposizione (+N/-N), ritardo (>righe), volume
```

Gettoni: `D4:8` nota e durata in righe (la durata resta finché non cambia), `D4:8!40` col volume
(0-64), `!40` volume per le note seguenti, `r:4` pausa (spegne gli strumenti tenuti; pizzicati e
percussioni suonano fino in fondo), `^` stacca, `~:16` lascia suonare, `x`/`X` colpo di percussione
(normale/accento), `( ... )*4` ripeti, `T90` cambio di tempo, `|` stanghetta. `#` dopo uno spazio
apre un commento (`F#4` è una nota).
