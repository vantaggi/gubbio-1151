// Banco di prova: fa girare una ROM GBA in libmgba senza finestra, preme tasti da un copione e salva
// schermate. Copione (una riga per comando):
//   aspetta N            N frame senza tasti
//   tieni TASTI N        tiene premuti i TASTI (A,B,SELECT,START,DESTRA,SINISTRA,SU,GIU,R,L uniti da +) per N frame
//   premi TASTI          un tocco: 2 frame premuti, 8 rilasciati
//   foto NOME            salva NOME.ppm (240x160)
//   foto_ogni K N NOME   N frame, una foto ogni K: NOME_000.ppm ...
//   finche TESTO M       avanza fino a quando il log del gioco contiene TESTO (al massimo M frame)
//   foto_al_log TESTO NOME M  come finche, poi una foto
//   foto_ai_log TESTO FINE M  una foto ogni volta che una riga del log contiene TESTO (nome = la riga),
//                        fino alla riga che contiene FINE (al massimo M frame)
// Il log del gioco (bn::core::log) va su stderr.
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

static void logga(struct mLogger* l, int cat, enum mLogLevel lv, const char* f, va_list a)
{
    (void) l;
    if(strcmp(mLogCategoryName(cat), "GBA Debug") && !(lv & (mLOG_ERROR | mLOG_FATAL)))
        return;
    vsnprintf(ultimo, sizeof ultimo, f, a);
    fprintf(stderr, "[%ld] %s\n", frame_n, ultimo);
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
    }
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
        else if(!strcmp(cmd, "premi")) { corri(tasti(a), 2); corri(0, 8); }
        else if(!strcmp(cmd, "foto")) foto(a);
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
