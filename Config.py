import configparser


class Config:
    def __init__(self, config_file='config.cfg'):
        self.config = configparser.RawConfigParser()
        self.config.read(config_file)

    def read_from_config(self, section, option):
        return self.config.get(section, option)

    def get_all_section_parameters(self, section):
        return dict(self.config.items(section))

    def write_to_config(self, section, option):
        return self.config.write(section, option)
