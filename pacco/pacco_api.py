class PaccoAPIV1:
    def download(self, registry, *settings):
        print("Downloading {} with the following settings...".format(registry))
        for s in settings:
            print("{}".format(s))


Pacco = PaccoAPIV1
