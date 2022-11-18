# Megatron DeepSpeed on Lumi
This directory is for sharing setups and keep on track what's working with our experiments on Lumi and especially with my personal efforts for getting T5-Megatron working.

## Important notes:
* BERT-pretraining on Microsoft/Megatron-DeepSpeed fails if --checkpoint-activations is on
* BERT doesn't support DeepSpeed Pipeline Parallel
* T5 has a bug that needs to be fixed with the following: 

```
file: megatron/model/t5_model.py: 137

-        decoder_output, encoder_output = lm_output
+        decoder_output, encoder_output, *moe_losses = lm_output

```


## Setup
### Create a virtual environment 

setup-venv-lumi.sh takes care of installing required packages including apex for rocm. 
Installation requires a GPU, so change the account from slurm variables. 
Default installation name for venv is "venv", you may alter it to your liking. 

```
bash setup-venv-lumi.sh

```

### Clone Megatron
```
git clone https://github.com/microsoft/Megatron-DeepSpeed
cd Megatron-DeepSpeed
```
## Setup things for GPT
### Download tokenizer files

Default gpt-tokenizer for example. Any BPE-tokenizer should work.

```
mkdir gpt2
wget https://huggingface.co/gpt2/resolve/main/{vocab.json,merges.txt} -P gpt2
```
### Download example data and sample
Any .jsonl-formatted data with `text`-column should work directly
```
mkdir -p data/owt2
wget https://a3s.fi/openwebtext2/2020-01.jsonl -P data/owt2
head -n 100000 data/owt2/2020-01.jsonl > tiny-owt2-sample.jsonl
```

### Preprocess for GPT
```
python Megatron-DeepSpeed/tools/preprocess_data.py \
    --input tiny-owt2-sample.jsonl \
    --tokenizer-type GPT2BPETokenizer \
    --vocab-file gpt2/vocab.json \
    --merge-file gpt2/merges.txt \
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

# GPT
sbatch launch_gpt_training.sh
```
# T5
### Running t5:

```
# If you haven't yet done this, clone the repo. 
git clone https://github.com/microsoft/Megatron-DeepSpeed
cd Megatron-DeepSpeed

# Else
cd /path/to/Megatron-DeepSpeed

# If you havent yet patched t5_model.py, this line does the trick
perl -p -i -e "s/decoder_output, encoder_output = lm_output/decoder_output, encoder_output, *moe_losses = lm_output/g" megatron/model/t5_model.py 

# Download and edit below scripts to your needs and matching your account 
wget https://raw.githubusercontent.com/TurkuNLP/finngen-tools/main/megatron-deepspeed/launch_t5_training.sh
wget https://raw.githubusercontent.com/TurkuNLP/finngen-tools/main/megatron-deepspeed/pretrain_t5_lumi.sh


sbatch launch_t5_training_lumi.sh

```