from iob_core import iob_core


class iob_edge_detect(iob_core):
    def __init__(self, *args, **kwargs):
        self.set_default_attribute("version", "0.1")
        self.set_default_attribute("generate_hw", False)

        self.create_instance(
            "iob_reg_r",
            "iob_reg_r_inst",
        )

        super().__init__(*args, **kwargs)
