# Modello: una decisione

Una riga nella tabella della sezione giusta di `DECISIONI.md`, con il primo ID libero:

```
| D123 | 2026-11-06 | Ambito | Cosa si è deciso, in una frase che si capisce da sola | Chi | G | valida |
```

- **Ambito**: una parola (Rilascio, Toolchain, Stile, Mondo, Storia, Battaglia, Menù, Processo...).
- **Chi**: `Cioti`, `Claude` (su delega), `Claude, ok Cioti` (proposta approvata).
- **Tipo**: `G` vale per ogni gioco della serie, `S` solo per questo gioco, `G+S` regola generica con
  valori di questo gioco.
- **Stato**: `valida`, `in corso`, `da rivedere`, `superata da Dnnn`.
- Niente barre verticali dentro le celle, niente dettagli di trama.

Quando una decisione nuova ne sostituisce una vecchia:
1. la vecchia passa a `superata da D123`;
2. si scrive la lezione in `LEZIONI.md` (modello in [LEZIONE.md](LEZIONE.md)) che cita le due decisioni;
3. `python3 tools/controlla_metodo.py` deve dire 0 errori.
