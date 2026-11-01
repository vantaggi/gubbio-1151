#---------------------------------------------------------------------------------------------------
# Gubbio 1151. Si compila con `bash build.sh`, che controlla prima la toolchain (toolchain.lock).
# Butano e' il submodule in butano/; LIBBUTANOABS va esportato perche' butano.mak lo usa per
# trovare i propri sotto-makefile.
#---------------------------------------------------------------------------------------------------
TARGET          :=  gubbio1151
BUILD           :=  build
PYTHON          ?=  python
# Il font della schermata di prova viene dalla libreria `common` di Butano (zlib).
# graphics/ e' generata da stile/genera_bmp.py: non si modifica a mano.
SOURCES         :=  src
INCLUDES        :=  include butano/common/include
DATA            :=
GRAPHICS        :=  graphics butano/common/graphics
AUDIO           :=
AUDIOBACKEND    :=  maxmod
AUDIOTOOL       :=
DMGAUDIO        :=
DMGAUDIOBACKEND :=  default
ROMTITLE        :=  GUBBIO1151
ROMCODE         :=  GU11
USERFLAGS       :=
# Il GBA non ha FPU: ogni promozione a double e' una routine software. Errore, non avviso.
# Gli autotest dei testi e del formattatore girano a tempo di compilazione (src/autotest_testi.cpp):
# la prova su tutto int16 supera il limite predefinito di operazioni constexpr di gcc.
USERCXXFLAGS    :=  -Wdouble-promotion -Wfloat-conversion -Werror=double-promotion -Werror=float-conversion \
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
