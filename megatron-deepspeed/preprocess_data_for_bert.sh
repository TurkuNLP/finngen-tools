## Fetch and sample data
#mkdir -p data/owt2
#wget https://a3s.fi/openwebtext2/2020-01.jsonl -P data/owt2
#head -n 100000 data/owt2/2020-01.jsonl > tiny-owt2-sample.jsonl



module load cray-python
source ../venv/bin/activate
CPUS=8 # What is the max one can use on a login node?
python tools/preprocess_data.py \
       --input tiny-owt2-sample.jsonl \
       --workers $CPUS \
       --output-prefix bert-data_2 \
       --vocab bert-base-cased-tokenizer/vocab.txt \
       --dataset-impl mmap \
       --tokenizer-type BertWordPieceCase \
       --split-sentences

## If on a node with network connection, e.g. Puhti or Mahti, can be run with srun:
# CPUS=40
# srun --account project_462000119 --cpus-per-task $CPUS --mem=50G --partition standard \
#     python tools/preprocess_data.py \
#        --input tiny-owt2-sample.jsonl \
#        --workers $CPUS \
#        --output-prefix bert-data_2 \
#        --vocab bert-base-cased-tokenizer/vocab.txt \
#        --dataset-impl mmap \
#        --tokenizer-type BertWordPieceCase \
#        --split-sentences

