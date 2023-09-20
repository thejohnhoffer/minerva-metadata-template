# Intended key name: key in source.csv
KEY_NORMALIZE = {
    'Drinks Per Week': 'Drinks Per Week Current Age',
    'Sample Name': 'Sampe Name',
    'BRCA1-mutant': 'BRCA1',
    'BRCA2-mutant': 'BRCA2',
}
# Sample in source.csv: Input sample name
SAMPLE_NORMALIZE = {
    'CCK17-M': 'CK17-M',
}
# Input sample subpath: s3:// sample subpath
STORY_NORMALIZE = {
    'CK19_BCC': 'Ck19_BCC',
    'CK22': 'Ck22'
}

def to_normalized_sample_name(row):
    k = 'Sample Name'
    return SAMPLE_NORMALIZE.get(read_k(row, k), read_k(row, k))

def sample_name_to_s3_subpath(sample_name):
    s3_subpath = sample_name.replace('-', '_')
    return STORY_NORMALIZE.get(s3_subpath, s3_subpath)

def read_k(row, k):
    v = row[KEY_NORMALIZE.get(k,k)]
    # Check for "don't know" in the column
    if v.find('don\'t know') != -1:
        return ''
    return v

def is_na(row, k):
    v = read_k(row, k)
    return v == 'N/A'

def is_true(row, k):
    v = read_k(row, k)
    if v == 'Yes' or v == 'yes': return True
    if v == 'True' or v == 'true': return True
    return False
