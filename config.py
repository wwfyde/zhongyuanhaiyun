import yaml
from yaml import FullLoader

with open('etc/config.yaml') as f:
    config = yaml.load(f, Loader=FullLoader)