// Banco di prova: fa girare una ROM GBA in libmgba senza finestra, preme tasti da un copione e salva
// schermate. Copione (una riga per comando):
//   aspetta N            N frame senza tasti
//   tieni TASTI N        tiene premuti i TASTI (A,B,SELECT,START,DESTRA,SINISTRA,SU,GIU,R,L uniti da +) per N frame
//   premi TASTI          un tocco: 2 frame premuti, 8 rilasciati
//   foto NOME            salva NOME.ppm (240x160)
//   tieni_foto TASTI N K NOME  tiene i TASTI per N frame e fa una foto ogni K: NOME_000.ppm ...
//   foto_ogni K N NOME   N frame, una foto ogni K: NOME_000.ppm ...
//   finche TESTO M       avanza fino a quando il log del gioco contiene TESTO (al massimo M frame)
//   foto_al_log TESTO NOME M  come finche, poi una foto
//   foto_ai_log TESTO FINE M  una foto ogni volta che una riga del log contiene TESTO (nome = la riga),
//                        fino alla riga che contiene FINE (al massimo M frame)
//   premi_finche TASTI TESTO M  un tocco di TASTI ogni 20 frame finche' il log contiene TESTO (al massimo M
//                        frame); trovato, non tocca piu' niente (i dialoghi e la battaglia fino a un menu)
//   caso SEME N          il giocatore scimmia (docs/caccia_ai_crash.md): N frame di tasti a caso col SEME
//                        (croce tenuta, corsa, A a raffica, B, Start, Select, L/R), mai A+B+Select+Start; alla
//                        fine la riga "CASO finito". Dice "!! bloccato" se il gioco tace per 20 000 frame.
// Il log del gioco (bn::core::log) va su stderr, con gli errori di mGBA ("MGBA ..."). Alla riga
// "ASSERT scattato" (include/limiti.h) il banco lascia passare 30 frame, salva assert.ppm (la schermata
// d'errore di Butano, col messaggio) e si ferma.
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static struct mCore* core;
static color_t* buf;
static unsigned W, H;
static char ultimo[4096];
static int trovato;
static const char* cerca;
static long frame_n;
static const char* cattura;
static char da_fotografare[512];
static long crollato = -1;            // il frame dell'assert, -1 nessuno
static long ultimo_log;               // il frame dell'ultima riga del gioco

static void logga(struct mLogger* l, int cat, enum mLogLevel lv, const char* f, va_list a)
{
    (void) l;
    int debug = !strcmp(mLogCategoryName(cat), "GBA Debug");
    if(!debug && !(lv & (mLOG_ERROR | mLOG_FATAL | mLOG_GAME_ERROR)))
        return;
    vsnprintf(ultimo, sizeof ultimo, f, a);
    if(debug)
        fprintf(stderr, "[%ld] %s\n", frame_n, ultimo);
    else
        fprintf(stderr, "[%ld] MGBA %s: %s\n", frame_n, mLogCategoryName(cat), ultimo);
    ultimo_log = frame_n;
    if(crollato < 0 && strstr(ultimo, "ASSERT scattato"))
        crollato = frame_n;
    if(cerca && strstr(ultimo, cerca))
        trovato = 1;
    if(cattura && strstr(ultimo, cattura))
    {
        int j = 0;
        for(const char* c = ultimo; *c && j < 500; ++c)
            da_fotografare[j++] = (*c == ' ' || *c == '/') ? '_' : *c;
        da_fotografare[j] = 0;
    }
}

static struct mLogger logger = { .log = logga };

static void foto(const char* nome)
{
    char p[1024];
    snprintf(p, sizeof p, "%s.ppm", nome);
    FILE* f = fopen(p, "wb");
    fprintf(f, "P6\n%u %u\n255\n", W, H);
    for(unsigned i = 0; i < W * H; ++i)
    {
        uint32_t c = buf[i];
        unsigned char rgb[3] = { c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF };
        fwrite(rgb, 1, 3, f);
    }
    fclose(f);
}

static int tasti(const char* s)
{
    static const char* nomi[] = { "A", "B", "SELECT", "START", "DESTRA", "SINISTRA", "SU", "GIU", "R", "L" };
    int k = 0;
    char c[256];
    snprintf(c, sizeof c, "%s", s);
    for(char* t = strtok(c, "+"); t; t = strtok(NULL, "+"))
        for(int i = 0; i < 10; ++i)
            if(!strcmp(t, nomi[i]))
                k |= 1 << i;
    return k;
}

static void corri(int k, int n)
{
    core->setKeys(core, k);
    for(int i = 0; i < n; ++i, ++frame_n)
    {
        core->runFrame(core);
        if(da_fotografare[0]) { foto(da_fotografare); da_fotografare[0] = 0; }
        if(crollato >= 0 && frame_n - crollato >= 30)
        {
            foto("assert");
            fprintf(stderr, "[%ld] !! fermo all'assert, foto in assert.ppm\n", frame_n);
            core->deinit(core);
            exit(0);
        }
    }
}

// xorshift32: lo stesso SEME da' gli stessi tasti, quindi un crash trovato si rifa' uguale
static uint32_t caso_stato;
static uint32_t caso(uint32_t n)
{
    caso_stato ^= caso_stato << 13;
    caso_stato ^= caso_stato >> 17;
    caso_stato ^= caso_stato << 5;
    return caso_stato % n;
}

static void scimmia(uint32_t seme, long n)
{
    enum { A = 1, B = 2, SELECT = 4, START = 8, DESTRA = 16, SINISTRA = 32, SU = 64, GIU = 128, R = 256, L = 512 };
    static const int croce[8] = { DESTRA, SINISTRA, SU, GIU, SU | DESTRA, SU | SINISTRA, GIU | DESTRA, GIU | SINISTRA };
    caso_stato = seme ? seme * 2654435761u : 1;
    long fine = frame_n + n;
    ultimo_log = frame_n;
    while(frame_n < fine)
    {
        uint32_t r = caso(100);
        if(r < 50)                                      // camminare (diagonale una volta su 3), a volte di corsa
        {
            int k = croce[caso(3) ? caso(4) : 4 + caso(4)];
            corri(k | (caso(10) < 3 ? B : 0), 8 + caso(90));
        }
        else if(r < 76)                                 // A a raffica: dialoghi, cartelli, menu, battaglia
        {
            for(int i = 1 + caso(6); i > 0; --i) { corri(A, 2); corri(0, 6); }
        }
        else if(r < 82)                                 // una freccia e A: scegliere una voce dei menu
        {
            corri(croce[caso(4)], 2); corri(0, 4); corri(A, 2); corri(0, 6);
        }
        else if(r < 88) { corri(B, 2); corri(0, 8); }
        else if(r < 91) { corri(START, 2); corri(0, 10); }
        else if(r < 93) { corri(SELECT, 2); corri(0, 10); }
        else if(r < 94) { corri(L, 4); corri(L | SELECT, 2); corri(0, 10); }   // il pannello di debug
        else if(r < 96) { corri(caso(2) ? L : R, 2); corri(0, 8); }
        else corri(0, 10 + caso(50));
        if(frame_n - ultimo_log > 20000)
        {
            fprintf(stderr, "[%ld] !! bloccato: il gioco non scrive nel log da %ld frame\n", frame_n, frame_n - ultimo_log);
            ultimo_log = frame_n;
        }
    }
    fprintf(stderr, "[%ld] CASO finito seme %u frame %ld\n", frame_n, seme, n);
}

int main(int argc, char** argv)
{
    if(argc < 3) { fprintf(stderr, "uso: banco ROM COPIONE\n"); return 2; }
    mLogSetDefaultLogger(&logger);
    core = mCoreFind(argv[1]);
    core->init(core);
    mCoreInitConfig(core, NULL);
    core->desiredVideoDimensions(core, &W, &H);
    buf = malloc(W * H * BYTES_PER_PIXEL);
    core->setVideoBuffer(core, buf, W);
    if(!mCoreLoadFile(core, argv[1])) { fprintf(stderr, "ROM non caricata\n"); return 1; }
    core->reset(core);
    FILE* s = fopen(argv[2], "r");
    char riga[1024];
    while(fgets(riga, sizeof riga, s))
    {
        char cmd[64] = "", a[512] = "", b[512] = "", c[512] = "";
        int n = sscanf(riga, "%63s %511s %511s %511s", cmd, a, b, c);
        if(n < 1 || cmd[0] == '#') continue;
        if(!strcmp(cmd, "aspetta")) corri(0, atoi(a));
        else if(!strcmp(cmd, "tieni")) corri(tasti(a), atoi(b));
        else if(!strcmp(cmd, "caso")) scimmia((uint32_t) strtoul(a, NULL, 10), atol(b));
        else if(!strcmp(cmd, "premi")) { corri(tasti(a), 2); corri(0, 8); }
        else if(!strcmp(cmd, "foto")) foto(a);
        else if(!strcmp(cmd, "tieni_foto"))
        {
            char d[512] = "";
            sscanf(riga, "%*s %*s %*s %*s %511s", d);
            int k = atoi(c), tot = atoi(b);
            char p[600];
            for(int i = 0; i < tot; ++i)
            {
                corri(tasti(a), 1);
                if(i % k == 0) { snprintf(p, sizeof p, "%s_%03d", d, i / k); foto(p); }
            }
        }
        else if(!strcmp(cmd, "foto_ogni"))
        {
            int k = atoi(a), tot = atoi(b);
            char p[600];
            for(int i = 0; i < tot; ++i)
            {
                corri(0, 1);
                if(i % k == 0) { snprintf(p, sizeof p, "%s_%03d", c, i / k); foto(p); }
            }
        }
        else if(!strcmp(cmd, "foto_ai_log"))
        {
            cattura = a; cerca = b; trovato = 0;
            for(int i = 0; i < atoi(c) && !trovato; ++i) corri(0, 1);
            cattura = NULL; cerca = NULL;
        }
        else if(!strcmp(cmd, "premi_finche"))
        {
            int k = tasti(a), m = atoi(c);
            cerca = b; trovato = 0;
            for(int i = 0; i < m && !trovato; ++i) corri(i % 20 < 2 ? k : 0, 1);
            if(!trovato) fprintf(stderr, "!! non trovato: %s\n", b);
            cerca = NULL;
            corri(0, 1);
        }
        else if(!strcmp(cmd, "finche") || !strcmp(cmd, "foto_al_log"))
        {
            int foto_dopo = !strcmp(cmd, "foto_al_log");
            int m = atoi(foto_dopo ? c : b);
            cerca = a; trovato = 0;
            for(int i = 0; i < m && !trovato; ++i) corri(0, 1);
            if(!trovato) fprintf(stderr, "!! non trovato: %s\n", a);
            if(foto_dopo) foto(b);
            cerca = NULL;
        }
    }
    core->deinit(core);
    return 0;
}
