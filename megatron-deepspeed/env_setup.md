# Modules
​
module load cray-python
​
# Initialize venv
​
python -m venv --system-site-packages venv
source venv/bin/activate
​
# Install torch, transformers, deepspeed, etc.
​
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch --extra-index-url https://download.pytorch.org/whl/rocm5.1.1
python -m pip install numpy datasets evaluate accelerate sklearn nltk
python -m pip install --upgrade git+https://github.com/huggingface/transformers
python -m pip install deepspeed
​
# Install apex (on compute node)
​
git clone https://github.com/ROCmSoftwarePlatform/apex
srun --account=project_462000119 --cpus-per-task=20 --partition=pilot --gres=gpu:mi250:1 --time=2:00:00 --pty bash
module load cray-python
source venv/bin/activate
cd apex
python setup.py install --cpp_ext --cuda_ext
exit
​
# Clone Megatron
​
git clone https://github.com/microsoft/Megatron-DeepSpeed
cd Megatron-DeepSpeed
​
# Download tokenizer files
​
mkdir gpt2
wget https://huggingface.co/gpt2/resolve/main/{vocab.json,merges.txt} -P gpt2
​
# Download data, truncate
​
mkdir -p data/owt2
wget https://a3s.fi/openwebtext2/2020-01.jsonl -P data/owt2
​
head -n 100000 data/owt2/2020-01.jsonl > tiny-owt2-sample.jsonl
​
# Preprocess to Megatron format
​
python Megatron-DeepSpeed/tools/preprocess_data.py --input tiny-owt2-sample.jsonl --tokenizer-type GPT2BPETokenizer --vocab-file gpt2/vocab.json --merge-file gpt2/merges.txt --output-prefix tiny-owt2-sample
​