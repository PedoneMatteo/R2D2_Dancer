# Video demo

Questa cartella contiene i video dimostrativi del progetto.

## File attesi

| File                  | Contenuto                                                |
|-----------------------|----------------------------------------------------------|
| `r2d2_dancer.gif`     | R2D2 che balla sul posto (modalita `r2d2_dancer.launch`) |
| `r2d2_walker.gif`     | R2D2 che cammina in cerchio (modalita `r2d2_walker.launch`) |

## Come registrare i video

### Metodo 1: Peek (consigliato per GIF)

```bash
sudo apt install peek
peek
```

1. Avvia il launch (dancer o walker)
2. Apri Peek e posiziona la finestra su RViz
3. Premi **Registra** e lascia girare 5-10 secondi
4. Salva il file nella cartella `video/`

### Metodo 2: OBS Studio (per video mp4/webm)

```bash
sudo apt install obs-studio
obs
```

### Metodo 3: Da terminale con `ffmpeg` (screen capture)

```bash
# Registra una finestra per 10 secondi
ffmpeg -f x11grab -video_size 800x600 -i :0.0+100,100 -t 10 video/r2d2_dancer.mp4

# Converti in GIF animata
ffmpeg -i video/r2d2_dancer.mp4 -filter_complex "fps=10,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse" video/r2d2_dancer.gif
```

### Metodo 4: RViz screencast (ROS2)

```bash
# Installa il plugin screencast per RViz
sudo apt install ros-humble-rviz2-screencast

# Aggiungi il pannello "Screencast" in RViz dal menu Panels > Add New Panel
# Premi il pulsante Record per avviare/fermare la registrazione
```

> **Nota:** I file video/gif verranno ignorati da `.gitignore` se troppo grandi.
> Le GIF sono consigliate perche GitHub le riproduce automaticamente nel README.
