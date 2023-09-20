import os
import csv
import json
import urllib.request
from pathlib import Path
from sanitization import to_normalized_sample_name
from sanitization import sample_name_to_s3_subpath
from sanitization import is_true, is_na, read_k

def to_key_csv(row, ks):
    not_applicable = [k for k in ks if is_na(row, k)]
    if len(not_applicable) == len(ks): return 'N/A'
    # Return list of values where key is 'yes' or 'true'
    bool_list = [k for k in ks if is_true(row, k)]
    if len(bool_list) == 0: return 'None'
    return ', '.join(bool_list)

def format_field(meta, k, default=''):
    v = meta.get(k, default) or default
    return f'**{k}**: {v}  '

def format_field_if(meta, k):
    if meta[k] == '': return ''
    return f'''
{format_field(meta, k)}'''

def format_row(meta):
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

### Attribution {attribution}

### Sample Identifiers  
{serialized_ids}'''

# TODO: confirm
# ### Imaging  
# {format_field(meta, 'Imaging Assay Type')}
# {format_field(meta, 'Fixative Type')}

def parse_row(row, sample_name, citation):
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
        'Please cite the publication and underlying data as': citation,
#Identifiers
        'Identifiers': {
            'Sample Name': sample_name 
        }
    }

def parse_csv(in_csv):
    # Exported from Excel with BOM
    with open(in_csv, 'r', encoding='utf-8-sig') as inf:
        reader = csv.DictReader(inf)
        for row in reader:
            yield row

def parse_metas(in_csv, citation):
    out_metas = dict()
    for row in parse_csv(in_csv):

        # Sanitize sample name and convert to s3 subpath
        sample_name = to_normalized_sample_name(row)
        s3_subpath = sample_name_to_s3_subpath(sample_name)

        # Ensure there exists minerva title
        minerva_title = read_k(row, 'Minerva Title')
        minerva_title = minerva_title if minerva_title else s3_subpath 

        meta_md = format_row(parse_row(row, sample_name, citation))
        out_metas[s3_subpath] = {
            'meta_md': meta_md,
            'minerva_title': minerva_title
        }

    return out_metas

def edit_exhibit(full_url, minerva_title, description, orig, ex):
    # Parse json at full_url
    with urllib.request.urlopen(full_url) as url:
        data = json.loads(url.read().decode('utf-8'))

        # Backup copy of original data
        out_dir = full_url.split('/')[-2]
        out_dir = os.path.join(orig, full_url.split('/')[-2])
        original_out = os.path.join(out_dir, ex)
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        with open(original_out, 'w') as outfile:
            json.dump(data, outfile, indent=4)

    data['Name'] = minerva_title
    data['Header'] = description 
    data['FirstViewport'] = {
        'Pan': [0.5, 0.5],
        'Zoom': 1.0
    }
    # Return new exhibit
    return data


def main(in_list, in_csv, output_dir, orig, s3_prefix, citation):
    metas = parse_metas(in_csv, citation)

    sample_names = []
    ex = 'exhibit.json'

    with open(in_list, 'r') as inf:
        for line in inf:
            full_url = line.strip()
            # Ensure path ends with exhibit.json
            if not full_url.endswith(ex):
                continue
            if not full_url.startswith('http'):
                continue
            sample_name = full_url.split('/')[-2]
            # Ignore any sample names not in metas
            if sample_name not in metas: continue
            
            # append sample name to list of sample names
            sample_names.append(sample_name)
            # add full url to metas dictionary
            metas[sample_name]['full_url'] = full_url 

    # Ensure metas.keys intersects with sample names
    meta_keys = set(sample_names) & set(metas.keys())
    meta_keys = [k for k in meta_keys if 'full_url' in metas[k]]

    # Ensure each metas.keys matches s3 prefix
    meta_keys = [k for k in meta_keys if s3_prefix in metas[k]['full_url']]

    # Edit all exhibit.json files
    for key in meta_keys:
        full_url = metas[key]['full_url']
        minerva_title = metas[key]['minerva_title']
        description = metas[key]['meta_md']

        # Create new exhibit json
        new_exhibit = edit_exhibit(full_url, minerva_title, description, orig, ex)
        key_output_dir = os.path.join(output_dir, key)
        key_output = os.path.join(key_output_dir, ex)

        # Create new directory, key_output_dir
        Path(key_output_dir).mkdir(parents=True, exist_ok=True)

        with open(key_output, 'w') as outfile:
            json.dump(new_exhibit, outfile, indent=4)

        out_sample = full_url.split('/')[-2]
        print(f'aws s3 cp --acl public-read {key_output} s3://{s3_prefix}/{out_sample}/{ex}', flush=True)


# Modify parameters as needed
if __name__ == "__main__":
    s3_prefix = 'www.cycif.org/110-Komen_BRCA'
    citation = 'Gray GK, Li CM-C, Rosenbluth JM, et al.,  Developmental Cell, 2022. DOI: 10.1016/j.devcel.2022.05.003.'
    in_list = os.path.join(os.path.dirname(__file__), "inputs", "links.txt")
    in_csv = os.path.join(os.path.dirname(__file__), "inputs", "source.csv")
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    orig = os.path.join(os.path.dirname(__file__), "originals")
    main(in_list, in_csv, output_dir, orig, s3_prefix, citation)
