# Megatron DeepSpeed on Lumi
## Setupping a working environment for Microsoft/Megatron-DeepSpeed
### Modules
module load cray-python
### Initialize venv
```
python -m venv --system-site-packages venv
source venv/bin/activate
 ```
### Install torch, transformers, deepspeed, etc.

```
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch --extra-index-url https://download.pytorch.org/whl/rocm5.1.1
python -m pip install numpy datasets evaluate accelerate sklearn nltk
python -m pip install --upgrade git+https://github.com/huggingface/transformers
python -m pip install deepspeed
```
### Install apex (on compute node)
```
git clone https://github.com/ROCmSoftwarePlatform/apex
srun --account=project_462000119 --cpus-per-task=20 --partition=pilot --gres=gpu:mi250:1 --time=2:00:00 --pty bash
```
```
module load cray-python
source venv/bin/activate
cd apex
python setup.py install --cpp_ext --cuda_ext
exit
```
### Clone Megatron
```
git clone https://github.com/microsoft/Megatron-DeepSpeed
cd Megatron-DeepSpeed
```
## Setup things for GPT
### Download tokenizer files
```
mkdir gpt2
wget https://huggingface.co/gpt2/resolve/main/{vocab.json,merges.txt} -P gpt2
```
### Download data, truncate
```
mkdir -p data/owt2
wget https://a3s.fi/openwebtext2/2020-01.jsonl -P data/owt2
head -n 100000 data/owt2/2020-01.jsonl > tiny-owt2-sample.jsonl
```

### Preprocess for GPT
```
python Megatron-DeepSpeed/tools/preprocess_data.py 
    --input tiny-owt2-sample.jsonl 
    --tokenizer-type GPT2BPETokenizer 
    --vocab-file gpt2/vocab.json 
    --merge-file gpt2/merges.txt 
    --output-prefix tiny-owt2-sample
```

### Preprocess for BERT
```
python tools/preprocess_data.py \
       --input tiny-owt2-sample.jsonl \
       --workers 8 \
       --output-prefix bert-data_2 \
       --vocab bert-base-cased-tokenizer/vocab.txt \
       --dataset-impl mmap \
       --tokenizer-type BertWordPieceCase \
       --split-sentences
```

### Launch training
```
# BERT
sbatch launch_bert_training.sh
or 
bash pretrain_bert_srun.sh

# GPT
sbatch launch_gpt_training.sh
bash pretrain_gpt_srun.sh

# T5
sbatch launch_t5_training.sh
TODO: bash pretrain_t5_srun.sh 

```
### NOTES:
* BERT-pretraining on Microsoft/Megatron-DeepSpeed fails if --checkpoint-activations is on
* BERT doesn't support DeepSpeed Pipelinen Parallel
* T5 requires a following change 
```
file: megatron/model/t5_model.py: 137

-        decoder_output, encoder_output = lm_output
+        decoder_output, encoder_output, *moe_losses = lm_output

```
* T5 not yet properly tested to run on LUMI, but latest error message on Lumi also appeared on Puhti and was solved by above change.
