#!/bin/bash
#BSUB -J CafeFilterLinks
#BSUB -q gpua100
#BSUB -gpu "num=1:mode=exclusive_process"
#BSUB -R "rusage[mem=32GB]"
#BSUB -R "span[hosts=1]"
#BSUB -n 4
#BSUB -W 24:00
#BSUB -o Output_%J.out
#BSUB -e Output_%J.err
#BSUB -B
#BSUB -N
##BSUB -u s243970@dtu.dk

# Start Ollama server in the background
~/bin/ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
sleep 10

# Pull the model
~/bin/ollama pull qwen2.5:14b

# Activate virtual environment
source venv/bin/activate

# Run link filtering
python3 -u filter_links.py

# Shut down Ollama
kill $OLLAMA_PID
