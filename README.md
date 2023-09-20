## Using meta.py

This script and example `inputs` have embeded metadata for the following paper:

```
Gray GK, Li CM-C, Rosenbluth JM, et al.,  Developmental Cell, 2022. DOI: 10.1016/j.devcel.2022.05.003.
```

When running `meta.py`, the following is attempted:

- Reads all `exhibit.json` files from `links.txt`
- Uses custom corrections in `sanitization.py` (modify per dataset)
- Caches the original `exhibit.json` files to `originals` directory
- When possible, adds matching metadata by 'Sample Name' in source.csv
- Writes modified `exhibit.json` files to `outputs` directory
- Prints all commands needed for AWS upload

Generate the neeeded commands:

```
python3 meta.py | tee commands.sh
```

Make copy of `originals` directory. Run `bash commands.sh` to overwrite AWS `exhibit.json` files with added metadata. 
