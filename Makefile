#---------------------------------------------------------------------------------------------------
# Gubbio 1151. Si compila con `bash build.sh`, che controlla prima la toolchain (toolchain.lock).
# Butano e' il submodule in butano/; LIBBUTANOABS va esportato perche' butano.mak lo usa per
# trovare i propri sotto-makefile.
#---------------------------------------------------------------------------------------------------
TARGET          :=  gubbio1151
BUILD           :=  build
PYTHON          ?=  python
# graphics/ e' generata da stile/genera_bmp.py: non si modifica a mano.
SOURCES         :=  src
INCLUDES        :=  include
DATA            :=
GRAPHICS        :=  graphics
AUDIO           :=  audio
AUDIOBACKEND    :=  maxmod
AUDIOTOOL       :=
DMGAUDIO        :=
DMGAUDIOBACKEND :=  default
ROMTITLE        :=  GUBBIO1151
ROMCODE         :=  GU11
USERFLAGS       :=
# Il GBA non ha FPU: ogni promozione a double e' una routine software. Errore, non avviso.
# -Werror: zero avvisi, sempre (revisione a loop, 4 nov 2026: erano 69, tutti tolti). Vale anche per le ROM
# delle prove (tools/prove_mgba.py), che passano di qui.
# Gli autotest dei testi e del formattatore girano a tempo di compilazione (src/autotest_testi.cpp):
# la prova su tutto int16 supera il limite predefinito di operazioni constexpr di gcc.
# Strati di ordinamento degli sprite: ogni coppia (priorita' del fondale, z) e' uno strato, e sulla mappa lo z viene
# dai piedi (Esplorazione::z_sulla_mappa), quindi quasi ogni sprite ne ha uno suo. Il predefinito di Butano (16)
# finiva in Sant'Andrea con la folla e la fila ("No more sprite sort layers available", 5 nov 2026): con 128,
# quanti gli sprite, non si puo' piu' finire.
USERCXXFLAGS    :=  -DBN_CFG_SPRITES_MAX_SORT_LAYERS=128 \
                    -Werror -Wdouble-promotion -Wfloat-conversion -Werror=double-promotion -Werror=float-conversion \
                    -fconstexpr-ops-limit=1073741824
USERASFLAGS     :=
USERLDFLAGS     :=
USERLIBDIRS     :=
USERLIBS        :=
DEFAULTLIBS     :=
STACKTRACE      :=
USERBUILD       :=
EXTTOOL         :=

LIBBUTANO       :=  butano/butano

ifndef LIBBUTANOABS
    export LIBBUTANOABS :=  $(realpath $(LIBBUTANO))
endif

include $(LIBBUTANOABS)/butano.mak
