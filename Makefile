#---------------------------------------------------------------------------------------------------------------------
# TARGET is the name of the output.
# BUILD is the directory where object files & intermediate files will be placed.
# LIBBUTANO is the main directory of butano library (https://github.com/GValiente/butano).
#
# NOTA (Sessione 02b): questo Makefile e' stato allineato alla convenzione attuale di Butano.
# La versione precedente usava `BUTANO_PATH` + `include $(BUTANO_PATH)/butano.mak`, ma il
# butano.mak odierno risolve i propri sotto-makefile tramite `LIBBUTANOABS`, che va esportato
# dal progetto: senza di esso il build fallisce con "No rule to make target '/butano_dka.mak'".
# `BUTANO_PATH` resta accettato come override d'ambiente per non rompere setup esistenti.
#---------------------------------------------------------------------------------------------------------------------
TARGET          :=  gubbio1151
BUILD           :=  build
PYTHON          :=  python
# `common` e' la libreria di supporto degli esempi Butano: fornisce i font sprite usati dal
# tabulato di collaudo in main.cpp. Da rimuovere quando l'HUD definitivo avra' i propri asset.
SOURCES         :=  src ../butano/common/src
INCLUDES        :=  include ../butano/common/include
DATA            :=
GRAPHICS        :=  graphics ../butano/common/graphics
AUDIO           :=  audio
AUDIOBACKEND    :=  maxmod
AUDIOTOOL       :=
DMGAUDIO        :=  dmg_audio
DMGAUDIOBACKEND :=  default
ROMTITLE        :=  GUBBIO1151
ROMCODE         :=  GU11
USERFLAGS       :=
USERCXXFLAGS    :=  -Wdouble-promotion -Wfloat-conversion -Werror=double-promotion -Werror=float-conversion
USERASFLAGS     :=
USERLDFLAGS     :=
USERLIBDIRS     :=
USERLIBS        :=
DEFAULTLIBS     :=
STACKTRACE      :=
USERBUILD       :=
EXTTOOL         :=

# Se BUTANO_PATH non e' definito nelle variabili di sistema, usa il default relativo.
ifndef BUTANO_PATH
    LIBBUTANO   :=  ../butano/butano
else
    LIBBUTANO   :=  $(BUTANO_PATH)
endif

#---------------------------------------------------------------------------------------------------------------------
# Export absolute butano path:
#---------------------------------------------------------------------------------------------------------------------
ifndef LIBBUTANOABS
    export LIBBUTANOABS :=  $(realpath $(LIBBUTANO))
endif

#---------------------------------------------------------------------------------------------------------------------
# Include main makefile:
#---------------------------------------------------------------------------------------------------------------------
include $(LIBBUTANOABS)/butano.mak
