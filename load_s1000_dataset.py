from datasets import Dataset, DatasetDict


label_list = ['O','I-Species','B-Species']

def load_file(tsv):
    with open(tsv) as f:
        raw = f.readlines()
    tokens = [line.split('\t')[0] for line in raw]
    labels = [ label_list.index(line.split('\t')[1].strip())
              if len(line.split('\t'))==2  else -1
              for line in raw]
    res_tokens = []
    res_labels = []
    sample_tokens = []
    sample_labels = []

    for token, label in zip(tokens, labels):
        if label ==-1:
            res_tokens.append(sample_tokens)
            res_labels.append(sample_labels)
            sample_tokens = []
            sample_labels = []
        else:
            sample_tokens.append(token)
            sample_labels.append(label)

    return Dataset.from_dict({"tokens": res_tokens, "labels": res_labels})

def create_s1000_dataset(datadir='./'):
    files = ['train.tsv', 'dev.tsv', 'test.tsv']
    data = DatasetDict()
    if not datadir.endswith('/'):
        datadir+="/"
    for file in files:
        data[file.split(".")[0]] = load_file(datadir+file)
    return data


