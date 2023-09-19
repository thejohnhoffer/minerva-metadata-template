import os
import csv

CITATION = 'Gray GK, Li CM-C, Rosenbluth JM, et al.,  Developmental Cell, 2022. DOI: 10.1016/j.devcel.2022.05.003.'
KEY_MAP = {
    'Drinks Per Week': 'Drinks Per Week Current Age',
    'Sample Name': 'Sampe Name',
    'BRCA1-mutant': 'BRCA1',
    'BRCA2-mutant': 'BRCA2',
}

def read_k(row, k):
    v = row[KEY_MAP.get(k,k)]
    # Check for "don't know" in the column
    if v.find('don\'t know') != -1:
        return ''
    return v

def is_na(row, k):
    v = read_k(row, k)
    return v == 'N/A'

def is_true(row, k):
    v = read_k(row, k)
    if v == 'Yes' or v == 'yes':
        return True
    if v == 'True' or v == 'true':
        return True
    return False

def to_key_csv(row, ks):
    not_applicable = [k for k in ks if is_na(row, k)]
    if len(not_applicable) == len(ks): return 'N/A'
    # Return list of values where key is 'yes' or 'true'
    bool_list = [k for k in ks if is_true(row, k)]
    if len(bool_list) == 0: return 'None'
    return ', '.join(bool_list)

def format_field(meta, k, default=''):
    v = meta.get(k, default) or default
    return f'**{k}**: {v}'

def format_field_if(meta, k):
    if meta[k] == '': return ''
    return f'''
{format_field(meta, k)}'''

def format_row(meta):
    print(list(meta.keys()))
    identifiers = meta['Identifiers']
    formated_ids = [format_field(identifiers, i) for i in identifiers.keys()]
    serialized_ids = '\n'.join(formated_ids)
    biopsy_results = format_field_if(meta, 'Biopsy Results')
    breast_cancer_age = format_field_if(meta, 'Age Diagnosed with Breast Cancer')
    attribution = format_field_if(meta, 'Please cite the publication and underlying data as')
    return f'''# Metadata about this sample  

### Diagnosis {biopsy_results}
{format_field(meta, 'Tested for Genetic Risk', 'Unknown')}
{format_field(meta, 'Genetic Features', 'Unknown')}
{format_field(meta, 'Breast Cancer', 'Unknown')}{breast_cancer_age}

### Demographics  
{format_field(meta, 'Species', 'Unknown')}
{format_field(meta, 'Race', 'Unknown')}
{format_field(meta, 'Hispanic', 'Unknown')}
{format_field(meta, 'Ashkenazi Jewish', 'Unknown')}
{format_field(meta, 'Age at Donation', 'Unknown')}
{format_field(meta, 'Age at First Period', 'Unknown')}
{format_field(meta, 'Relative with Breast/Ovarian Cancer', 'Unknown')}

### Clinical history
{format_field(meta, 'Breast Biopsy', 'Unknown')}
{format_field(meta, 'History of Other Cancers', 'Unknown')}
{format_field(meta, 'Hysterectomy or Ovary Removal', 'Unknown')}
{format_field(meta, 'Hormone Replacement Therapy', 'Unknown')}
{format_field(meta, 'Live Births', 'Unknown')}
{format_field(meta, 'Menstrual Status', 'Unknown')}
{format_field(meta, 'Years Smoking', 'Unknown')}
{format_field(meta, 'Currently Smoke', 'Unknown')}
{format_field(meta, 'Cigarettes Per Day', 'Unknown')}
{format_field(meta, 'Years Drinking', 'Unknown')}
{format_field(meta, 'Currently Drink', 'Unknown')}
{format_field(meta, 'Drinks Per Week', 'Unknown')}

### Imaging  
{format_field(meta, 'Imaging Assay Type')}
{format_field(meta, 'Fixative Type')}

### Attribution {attribution}

### Sample Identifiers  
{serialized_ids}'''

def parse_row(row):
    return {
#Diagnosis
        'Biopsy Results': read_k(row, 'Biopsy Results'),
        'Tested for Genetic Risk': read_k(row, 'Tested for Genetic Risk'),
        'Genetic Features': to_key_csv(row, ['BRCA1-mutant', 'BRCA2-mutant']),
        'Breast Cancer': read_k(row, 'Breast Cancer'),
        'Age Diagnosed with Breast Cancer': read_k(row, 'Age Diagnosed with Breast Cancer'),
#Demographics
        'Species': 'Human',
        'Race': read_k(row, 'Race'),
        'Hispanic': read_k(row, 'Hispanic'),
        'Ashkenazi Jewish': read_k(row, 'Ashkenazi Jewish'),
        'Age at Donation': read_k(row, 'Age at Donation'),
        'Age at First Period': read_k(row, 'Age at First Period'),
        'Relative with Breast/Ovarian Cancer': read_k(row, 'Relative with Breast/Ovarian Cancer'),
#Clinical history
        'Breast Biopsy': read_k(row, 'Breast Biopsy'),
        'History of Other Cancers': read_k(row, 'History of Other Cancers'),
        'Hysterectomy or Ovary Removal': read_k(row, 'Hysterectomy or Ovary Removal'),
        'Hormone Replacement Therapy': read_k(row, 'Hormone Replacement Therapy'),
        'Live Births': read_k(row, 'Live Births'),
        'Menstrual Status': read_k(row, 'Menstrual Status'),
        'Years Smoking': read_k(row, 'Years Smoking'),
        'Currently Smoke': read_k(row, 'Currently Smoke'),
        'Cigarettes Per Day': read_k(row, 'Cigarettes Per Day'),
        'Years Drinking': read_k(row, 'Years Drinking'),
        'Currently Drink': read_k(row, 'Currently Drink'),
        'Drinks Per Week': read_k(row, 'Drinks Per Week'),
#Imaging
        'Imaging Assay Type': 't-CyCIF',
        'Fixative Type': 'FFPE',
#Attribution
        'Please cite the publication and underlying data as': CITATION,
#Identifiers
        'Identifiers': {
            'Sample Name': read_k(row, 'Sample Name')
        }
    }

def parse_csv(in_csv):
    with open(in_csv, 'r', encoding='utf-8-sig') as inf:
        reader = csv.DictReader(inf)
        for row in reader:
            yield row

def parse_metas(in_csv):
    out_metas = dict()
    for row in parse_csv(in_csv):
        k = 'Sample Name'
        sample_name = read_k(row, k) 
        minerva_title = read_k(row, 'Minerva Title')
        meta_md = format_row(parse_row(row))
        out_metas[sample_name] = {
            'meta_md': meta_md,
            'minerva_title': minerva_title
        }

    return out_metas

def main(in_list, in_csv):
    metas = parse_metas(in_csv)
    with open(in_list, 'r') as inf:
        for line in inf:
            full_url = line.strip()
            # Ensure path ends with exhibit.json
            if not full_url.endswith('exhibit.json'):
                continue
            if not full_url.startswith('http'):
                continue
            sample_name = full_url.split('/')[-2]

    for meta in metas.values():
        print(meta['meta_md'])

if __name__ == "__main__":
    in_list = os.path.join(os.path.dirname(__file__), "inputs", "links.txt")
    in_csv = os.path.join(os.path.dirname(__file__), "inputs", "komen.csv")
    main(in_list, in_csv)
