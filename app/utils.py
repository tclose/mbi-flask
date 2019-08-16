import re

xnat_id_re = re.compile(
    r'([a-zA-Z]{3}[0-9]{3,})_([a-zA-Z0-9]+)_([a-zA-Z]{2,}[0-9a-zA-Z]+)')
