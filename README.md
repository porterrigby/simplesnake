# SimpleSnake
A Clembench game for evaluating LLMs on 2D text-based spatial reasoning tasks.

### Installation
SimpleSnake requires that [Clemcore](https://github.com/clp-research/clemcore) and [Clembench](https://github.com/clp-research/clembench) are already installed and functioning on your system.

After verifying Clembench is correctly installed, clone the repository into your local clembench 
directory alongside existing games.
```bash
git clone https://github.com/porterrigby/simplesnake.git $CLEMBENCH_HOME/simplesnake
```
---

### Usage
SimpleSnake contains three separate game variations. To run the vanilla version, execute:

```bash
clem run -g simplesnake -m <model-to-evaluate-on>
```

To run a variation of SimpleSnake that implements obstacles, run:
```bash
clem run -g simplesnake_withobstacles -m <model-to-evaluate-on>
```

A variation of the game that focuses on up-front planning instead of incremental moves can also be run using:
```bash
clem run -g simplesnake_withplanning -m <model-to-evaluate-on>
```
---

### Transcription and Evaluation
Games played by models within Clembench can be transcribed and evaluated into *html* files using ```clem transcribe```
and ```clem eval``` respectively. The resulting files are saved under ```results/```.

